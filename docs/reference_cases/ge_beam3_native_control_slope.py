"""Research-only accepted-state slope; uses analytic native operators, not an oracle."""
from copy import deepcopy
import numpy as np
from anysolver.linalg import factorize,MatrixClass
from anysolver._ge_beam3_native_translation import capture,assemble,bordered
from anysolver._ge_beam3_native_arc import clone_model,make_store
from anysolver._ge_beam3_native_generalized_parameter import parameter_column
from anysolver._ge_beam3_p5_seeded.core import sha


def solve_control_slope(matrix,column,free,local_control):
    """K du + F_lambda d_lambda=0, e_control^T du=1; K need not be invertible."""
    column=np.asarray(column);free=np.asarray(free)
    if (column.dtype!=np.float64 or column.ndim!=1 or not np.isfinite(column).all()
        or free.ndim!=1 or not np.issubdtype(free.dtype,np.integer) or len(free)==0
        or len(set(free))!=len(free) or np.any(free<0) or np.any(free>=len(column))
        or type(local_control) is not int or not 0<=local_control<len(free)
        or matrix.shape!=(len(column),len(column)) or not np.isfinite(matrix.data).all()):
        raise ValueError('bounded finite control-slope inputs')
    operator=bordered(matrix,column,free,local_control)
    rhs=np.zeros(len(free)+1);rhs[-1]=1.
    value=np.asarray(factorize(operator,MatrixClass.GENERAL).solve(rhs),dtype=float).reshape(-1)
    if value.shape!=rhs.shape or not np.isfinite(value).all():raise ValueError('control slope range')
    error=float(np.linalg.norm(operator@value-rhs)/max(1.,np.linalg.norm(rhs)))
    if error>1e-11:raise ValueError('control slope linear residual')
    return value,error


def accepted_slope(model,program,snapshot,parameter):
    observed=sha(snapshot);made=clone_model(model)
    _,_,free,_,_,local_control=capture(made,program)
    store=make_store(made,deepcopy(snapshot['states']),snapshot['displacements'])
    try:
        f,k,trial,physical,scale=assemble(made,store,snapshot['displacements'],program,parameter)
        residual=float(max(np.linalg.norm(f[free]),np.linalg.norm(physical[free]))/scale)
        if residual>1e-11:raise ValueError('accepted native slope origin not equilibrated')
        column=parameter_column(made,store,trial,program.distributed,nodal_moments=program.nodal_moments)['column']
        vector,error=solve_control_slope(k,column,free,local_control)
        result=dict(parameter_per_control=float(vector[-1]),linear_residual=error,origin_residual=residual,
                    direction=vector,snapshot_sha256=observed,analytic_parameter_column=True,production_qualified=False)
    finally:
        if store.has_active_trial:store.discard_trial(store.active_trial_token())
    if sha(snapshot)!=observed:raise ValueError('accepted history changed during slope replay')
    return result

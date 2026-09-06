"""P5 compatibility with real solver-owned rotation trials; research only."""

from dataclasses import dataclass

import numpy as np

from anysolver._ge_beam3_mixed_ad import Jet2, so3_exp
from anysolver._native_rotation_state import NativeRotationStateStore
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import skew
from docs.reference_cases.ge_beam3_curved_p5_compensated_mixed import CompensatedMixedBeamProbe
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array,_readonly
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import LocalForceAccuracy


SCHEMA='GE_BEAM3_P5_NATIVE_CHART_COMPATIBILITY_V1'


def _axial(matrix):
    return np.array([matrix[2,1]-matrix[1,2],matrix[0,2]-matrix[2,0],matrix[1,0]-matrix[0,1]])/2


def exp_chart_terms(vector):
    """Spatial left Exp Jacobian and its derivative, from analytic Jet2."""
    value=_array(vector,(3,),'native rotation increment')
    if np.linalg.norm(value)>=.9*np.pi: raise ValueError('native increment requires explicit cutback')
    jets=so3_exp([Jet2.variable(float(v),i,3) for i,v in enumerate(value)])
    r=np.array([[item.value for item in row] for row in jets])
    dr=np.array([[item.gradient for item in row] for row in jets])
    ddr=np.array([[item.hessian for item in row] for row in jets])
    a=np.column_stack([_axial(dr[:,:,j]@r.T) for j in range(3)])
    da=np.empty((3,3,3))
    for j in range(3):
        for k in range(3): da[:,j,k]=_axial(ddr[:,:,j,k]@r.T+dr[:,:,j]@dr[:,:,k].T)
    return a,da


def pullback(force,hessian,increments):
    force=_array(force,(18,),'spatial force');hessian=_array(hessian,(18,18),'spatial energy Hessian')
    increments=_array(increments,(3,3),'native increments')
    if np.linalg.norm(hessian-hessian.T)>1e-11*max(1.,np.linalg.norm(hessian)):
        raise ValueError('symmetric spatial energy Hessian required')
    chart=np.eye(18);spatial=hessian.copy();extra=np.zeros((18,18))
    for node,vector in enumerate(increments):
        start=6*node+3;a,da=exp_chart_terms(vector);moment=force[start:start+3]
        chart[start:start+3,start:start+3]=a
        spatial[start:start+3,start:start+3]-=.5*skew(moment)
        for k in range(3): extra[start:start+3,start+k]=da[:,:,k].T@moment
    transformed=chart.T@spatial@chart+extra
    if np.linalg.norm(transformed-transformed.T)>1e-11*max(1.,np.linalg.norm(transformed)):
        raise ValueError('native chart Hessian symmetry failed')
    return _readonly(chart.T@force),_readonly(transformed),_readonly(chart)


@dataclass(frozen=True)
class NativeChartResponse:
    schema: str
    element_id: int
    node_ids: tuple
    generation: int
    trial_serial: int
    positions: np.ndarray
    nodal_operators: np.ndarray
    increments: np.ndarray
    force: np.ndarray
    tangent: np.ndarray
    chart: np.ndarray
    spatial: object
    origins: tuple


def evaluate_native_trial(store,token,*,element_id,node_ids,reference,section,origins,order=8,line_force=None):
    """No element/material commit. The active store is authority for pose only."""
    if type(store) is not NativeRotationStateStore: raise ValueError('exact native rotation store required')
    store.validate_trial_token(token)
    if type(element_id) is not int or type(node_ids) is not tuple or len(node_ids)!=3:
        raise ValueError('explicit integer element and three-node tuple required')
    if len(set(node_ids))!=3 or any(type(i) is not int for i in node_ids):
        raise ValueError('three distinct exact integer node IDs required')
    view=store.element_view(element_id,node_ids,reference.nodal_triads[:,:,2],trial_token=token)
    for vector in view.rotation_coordinate_increment: exp_chart_terms(vector)
    if origins is None: raise ValueError('explicit fixed station origins required')
    model=CompensatedMixedBeamProbe(reference,section,position_low=np.zeros((3,3)),
                                    order=order,origins=origins,line_force=line_force)
    frames=view.trial_rotation_matrices@model.reference.nodal_triads
    length=max(np.linalg.norm(a-b) for a in reference.coordinates for b in reference.coordinates)
    response=model.solve(view.trial_coordinates,frames,
                         force_accuracy=LocalForceAccuracy(1e-12,float(length)))
    force,tangent,chart=pullback(response.residual,response.tangent,view.rotation_coordinate_increment)
    store.validate_trial_token(token)
    return NativeChartResponse(SCHEMA,element_id,node_ids,view.generation,view.trial_serial,
        _readonly(view.trial_coordinates),_readonly(view.trial_rotation_matrices),
        _readonly(view.rotation_coordinate_increment),force,tangent,chart,response,model.origins)

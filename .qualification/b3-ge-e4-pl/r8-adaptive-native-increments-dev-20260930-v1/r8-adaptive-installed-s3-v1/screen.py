from pathlib import Path
from dataclasses import asdict,replace
import hashlib,json,sys
import numpy as np
import numba,threadpoolctl
import anysolver
from anysolver import b3_ge,stiffened_shell
from anysolver._stiffened_shell_increment_control import decode_control
from test_stiffened_shell_ge_physical_fibre_linear import _definition
from test_stiffened_shell_ge_physical_fibre_finite import _yielding_definition

root=Path.cwd()
assert Path(anysolver.__file__).resolve().is_relative_to((root.parent/'r8-adaptive-installed-v1/site').resolve())
case=sys.argv[1]
assert all(p['num_threads']==1 for p in threadpoolctl.threadpool_info())
assert numba.config.DISABLE_JIT and numba.config.NUMBA_NUM_THREADS==1
if case=='s3':
    definition=_yielding_definition(False,True);targets=(.5,1.,.5)
else:
    assert case=='q4'
    definition=_definition();beams=[]
    for native in definition.beams:
        element,inertia=native.instantiate();reference=element.operator.reference
        section=b3_ge.PhysicalFibreSection(tuple(replace(fibre,
            curve=b3_ge.FlowCurve((0.,),(1e5,),1e9)) for fibre in element.section.fibres),
            element.section.background_factor)
        beams.append(b3_ge.define_beam('b3-ge',element.element_id,element.node_ids,
            reference.coordinates,reference.nodal_triads,section,inertia,
            quadrature=element.operator.order))
    definition=replace(definition,beams=tuple(beams));targets=(.5,1.)
control=stiffened_shell.AdaptiveIncrementControl(4,24)
actions=(stiffened_shell.NodalAction('beam',105,(0.,0.,1000.,0.,0.,0.)),)
owner=stiffened_shell.create_analysis(definition=definition)
status='completed';failure=None;oracle_status=None
try:
    try:
        result=owner.solve(actions,targets=targets,increment_control=control)
        attempts=result.increment_attempts
    except stiffened_shell.AdaptiveIncrementExhausted as error:
        status='nonconverged';failure=str(error);attempts=error.attempts
        result=None if owner._finite_driver is None else owner.recover()
    report={'case':case,'status':status,'failure':failure,'requested_targets':targets,
            'control':asdict(control),'default_iterations':12,'default_backtracks':8,
            'source':anysolver.__file__,'model':owner._identity,
            'attempts':[asdict(row) for row in attempts],
            'work':{key:sum(getattr(row,key) for row in attempts)
                    for key in ('evaluations','linear_solves','rejected_trials')},
            'accepted_factors':() if result is None else result.accepted_factors}
    (root/'screen.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    if result is not None:
        checkpoint=owner.checkpoint();(root/'accepted.checkpoint').write_bytes(checkpoint)
        report['equilibrium_ratio']=result.free_equilibrium_ratio
        report['constraint_max']=result.constraint_max
        report['accumulated_fibre_max']=max(v for row in result.beam_station_accumulated for v in row)
        report['last_increment_dissipation_j']=sum(sum(row.incremental_dissipation_j) for row in result.beam_fibre_energy)
        support=result.support_reactions[:owner._shell_count].reshape(-1,6)
        applied=np.array((0.,0.,1000.*result.load_factor))
        report['force_balance']=float(np.linalg.norm(support[:,:3].sum(axis=0)+applied)/np.linalg.norm(applied))
        moment=support[:,3:].sum(axis=0)+np.cross(definition.shell.coordinates_m,support[:,:3]).sum(axis=0)
        report['moment_balance']=float(np.linalg.norm(moment+np.cross(result.beam_positions[-1],applied))/(np.linalg.norm(applied)*owner._reference_length))
        restored=stiffened_shell.create_analysis(definition=definition)
        try:
            restored.restore(checkpoint)
            assert restored.checkpoint()==checkpoint
            report['restored_bytes_equal']=True
        finally:restored.close()
        if status=='completed':
            oracle=stiffened_shell.create_analysis(definition=definition)
            try:
                matched=oracle.solve(actions,targets=result.accepted_factors)
                state,inner=decode_control(checkpoint,owner._identity)
                assert state.completed and inner==oracle.checkpoint()
                assert matched.beam_fibre_energy==result.beam_fibre_energy
                report['matched_increment_oracle']='byte-identical physical checkpoint and fibre energies'
            finally:oracle.close()
    (root/'screen.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    (root/'environment.json').write_text(json.dumps({'python':sys.version,'threads':threadpoolctl.threadpool_info(),
        'jit_disabled':bool(numba.config.DISABLE_JIT)},indent=2))
    print(json.dumps({key:report[key] for key in ('case','status','failure','accepted_factors','work')}))
finally:owner.close()

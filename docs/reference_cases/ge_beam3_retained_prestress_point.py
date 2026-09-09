"""The unchanged actual preload evaluator, shared by serial and bounded tests."""
from hashlib import sha256
import json
import numpy as np
from anysolver import _ge_beam3_retained_nodal_loading as nodal
from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
from anysolver._ge_beam3_native_line_loading import LinePattern
from anysolver._ge_beam3_p5_seeded.core import canonical
from anysolver._native_paired_factor_chain_modes import solve_paired_factor_chain_modes as paired
from docs.reference_cases.ge_beam3_exact_family_partition import partition
from test_ge_beam3_native_generalized_modal import make
from test_ge_beam3_schur_line_program import save

EMPTY=DistributedPattern(LinePattern(()),())


def capture(compression,macros):
    m,_,masses=make(False,macros,clamped=True,coupled=False)
    tip=max(m.mesh.nodes)
    p=nodal.Program((.5,1.),EMPTY,nodal.NodalDeadForces(((tip,float(-compression),0.,0.),)))
    result=nodal.solve(m,p)
    return m,p,masses,result


def family_modes(family):
    return paired(family['left'],family['right'],family['geometric'],family['kinetic'],
        family['free'],family['algebraic'],bounds=(-100.,1e6),num_modes=1)


def evaluate_point(compression,macros,index,constant_families,tmp_path):
    print(dict(stage='actual-preload',macros=macros,index=index,compression=compression),flush=True)
    m,p,masses,result=capture(compression,macros)
    save(tmp_path/('state-%02d.json'%index),result.checkpoint)
    assert result.status=='completed',result.failure
    before=canonical(result.state);state=result.state.mechanical
    reference=np.array([m.mesh.nodes[node].coords() for node in sorted(m.mesh.nodes)])
    displacement=state.positions-reference+state.position_low
    expected=np.zeros_like(displacement);expected[:,0]=-compression*reference[:,0]/1000.
    axial_error=float(np.linalg.norm(displacement-expected));assert axial_error<=1e-11
    record=json.loads(result.checkpoint)['records'][-1]
    reaction_error=abs(record['residual'][0]-compression);assert reaction_error<=1e-11
    packet,guard=nodal.prepare(m,p,result.checkpoint,masses,expected_sha256=sha256(result.checkpoint).hexdigest())
    families=partition(packet,m.mesh.dof_manager.total_dofs,guard)
    modes={}
    for name in ('axial','torsion'):
        f=families[name]
        if name not in constant_families:
            mode=family_modes(f);assert mode.eigenvalues[0]>0.;constant_families[name]=f
        else:
            for key,value in f.items():
                assert np.array_equal(value,constant_families[name][key]),name+' family unexpectedly depends on preload'
    for name in ('bend-y','bend-z'):modes[name]=family_modes(families[name])
    lam=min(float(mode.eigenvalues[0]) for mode in modes.values())
    full_error=None
    if macros==1 and index<4:
        full=paired(packet.left,packet.right,packet.geometric,packet.kinetic,packet.free_dofs,
            packet.algebraic_dofs,bounds=(-100.,1e6),num_modes=1)
        full_error=abs(lam-float(full.eigenvalues[0]))/max(1.,abs(lam));assert full_error<=1e-11
    guard();assert canonical(result.state)==before
    row=dict(index=index,compression=compression,lambda_min=lam,axial_error=axial_error,
        reaction_error=reaction_error,checkpoint_sha256=sha256(result.checkpoint).hexdigest(),
        full_partition_root_error=full_error)
    save(tmp_path/('point-%02d.json'%index),dict(row=row,packet=packet,families=families,modes=modes,
        global_newton_programme_run=True,manufactured_uniform_axial_equilibrium=False,production_qualified=False))
    print(dict(stage='signed-spectrum',**row),flush=True)
    return row

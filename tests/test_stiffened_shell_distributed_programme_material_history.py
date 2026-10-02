"""Signed external loading with actual simultaneous shell/fibre histories."""
import numpy as np
import pytest
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken, SolveCancelled
from examples.stiffened_shell_coupled_plastic_history import definition, activity, OPTIONS, CONTROL


def test_signed_distributed_material_history_restart(request,record_property):
    a=ss.create_analysis(definition=definition());request.addfinalizer(a.close)
    endpoints=tuple(tuple(ss.GEBeamLineAction(e.element_id,(0.,0.,density))
                         for e,_,_ in a._beam_parts) for density in (3000.,-3000.))
    programme=ss.GEBeamDistributedProgramme(a.preflight()['identity'],endpoints)
    targets=(.5,1.,1.25,1.75,2.);token=CancellationToken();accepted=[];history=[]
    def observe(result):
        row=activity(result,accepted[-1] if accepted else None)
        row['position']=result.load_position
        ground=result.support_reactions[:a._shell_count].reshape(-1,6)
        xyz=a._shell_xyz+result.shell_displacement.reshape(-1,6)[:,:3]
        f=np.asarray(result.distributed_load.applied_force)
        m=np.asarray(result.distributed_load.applied_moment_about_origin)
        assert np.linalg.norm(ground[:,:3].sum(0)+f)/12000. <= 1e-8
        assert np.linalg.norm((np.cross(xyz,ground[:,:3])+ground[:,3:]).sum(0)+m)/24000. <= 1e-8
        p=result.load_position
        expected=12000.*(p if p<=1 else 3-2*p)
        np.testing.assert_allclose(f,(0.,0.,expected),atol=1e-10)
        accepted.append(result);history.append(row)
    def cancel(result):
        observe(result)
        if result.load_position==1.:token.cancel('yielded staged prefix')
    with pytest.raises(SolveCancelled):
        a.solve(programme,targets,increment_control=CONTROL,on_accepted=cancel,
                cancellation_token=token,**OPTIONS)
    assert any(row['simultaneous'] for row in history)
    b=ss.create_analysis(definition=definition());request.addfinalizer(b.close)
    b.restore(a.checkpoint());assert a.checkpoint()==b.checkpoint()
    last=a.solve(programme,targets,increment_control=CONTROL,on_accepted=observe,**OPTIONS)
    resumed=b.solve(programme,targets,increment_control=CONTROL,**OPTIONS)
    assert last.load_programme_complete and resumed.load_programme_complete
    assert last.distributed_load.applied_force[2]<0.
    assert any(row['simultaneous'] for row in history if row['position']>1.5)
    assert a.checkpoint()==b.checkpoint()
    record_property('signed_material_history',history)

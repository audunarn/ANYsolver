"""Yielded S3 fixed-target lifecycle; not complete coupled qualification."""
from dataclasses import replace
import numpy as np
import pytest
from anymaterial import DNVC208MaterialCurve
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken, SolveCancelled
from anysolver._stiffened_shell_displacement_checkpoint import decode_snapshot, encode_snapshot
from anysolver._stiffened_shell_q4_algorithmic_pullback import HISTORICAL_POLICY
from test_stiffened_shell_ge_experimental import _panel
from test_stiffened_shell_native_point_displacement import owner, DIRECTION, CONTROL, OPTIONS
from test_stiffened_shell_native_coupled_material import definition_for


def definition(fibre=False, mixed_shell=False):
    base=definition_for(True,True) if fibre else _panel()
    pressure=20_000.
    curve=DNVC208MaterialCurve(pressure,1.05*pressure,1.1*pressure,
                             .005,.01,4.*pressure,.2)
    return replace(base,shell=replace(base.shell,j2_curve=curve,
        q4_elements=((1,2,5,4),) if mixed_shell else (),
        s3_elements=((2,3,6),(2,6,5)) if mixed_shell else
                    ((1,2,5),(1,5,4),(2,3,6),(2,6,5))),
        q4_pullback_policy=ss.Q4_ALGORITHMIC_PULLBACK_V1 if mixed_shell else
                           HISTORICAL_POLICY)


def compare(left,right):
    assert left.history==right.history and left.amplitude==right.amplitude
    assert left.shell_layer_alpha==right.shell_layer_alpha
    for name in ('shell_displacement','support_reactions','cell_resultants'):
        np.testing.assert_array_equal(getattr(left,name),getattr(right,name))
    for a,b in zip(left.shell_q4_material+left.shell_s3_material,
                   right.shell_q4_material+right.shell_s3_material,strict=True):
        for name in ('layer_strain','layer_stress','plastic_strain','alpha'):
            np.testing.assert_array_equal(getattr(a,name),getattr(b,name))


@pytest.mark.parametrize('fibre,mixed_shell',((False,False),(True,False),(True,True)))
def test_yielded_s3_displacement_restart_continuation_and_rollback(request,tmp_path,fibre,mixed_shell):
    model=definition(fibre,mixed_shell)
    analysis=owner(request,model); resumed=owner(request,model); bad=owner(request,model)
    seed=analysis.solve((ss.NodalAction('beam',105,(0.,0.,1000.,0.,0.,0.)),),(.05,),**OPTIONS)
    assert max(max(row) for row in seed.shell_layer_alpha)>0.
    assert not analysis._finite_driver._stable_s3
    initial=analysis._finite_driver._state.q[CONTROL.dof(analysis)]
    seed_alpha=np.concatenate([r.alpha for r in seed.shell_s3_material])
    seed_q=analysis._finite_driver._state.q[:analysis._shell_count].copy()
    kw=dict(OPTIONS,displacement_control=CONTROL)
    prefix=analysis.solve(DIRECTION,(initial*1.01,),**kw)
    assert prefix.free_equilibrium_ratio<=1e-8 and prefix.constraint_max<=1e-9
    assert prefix.shell_s3_material and bool(prefix.shell_q4_material)==mixed_shell
    assert np.any(np.concatenate([r.alpha for r in prefix.shell_s3_material])>seed_alpha)
    assert not prefix.production_qualified
    saved=analysis.checkpoint(); (tmp_path/'plastic-s3-prefix.checkpoint').write_bytes(saved)
    metadata,arrays=decode_snapshot(analysis,saved)
    assert metadata['policy']=='B3_GE_NATIVE_POINT_SHELL_J2_S3_DISPLACEMENT_V1_DEV'
    np.testing.assert_array_equal(arrays['shell_origin_q'],seed_q)
    assert len(arrays['s3_states'])==2*len(model.shell.s3_elements)
    restored=resumed.restore(saved); compare(prefix,restored)
    assert resumed.checkpoint()==saved
    np.testing.assert_array_equal(resumed._finite_driver._shell_predecessor_q,seed_q)
    changed=dict(arrays); changed['s3_states']=arrays['s3_states'][len(model.shell.s3_elements):]+arrays['s3_states'][:len(model.shell.s3_elements)]
    corrupt=encode_snapshot(analysis,arrays=changed,**{k:v for k,v in metadata.items() if k not in ('policy','model','steps')})
    with pytest.raises(ValueError):bad.restore(corrupt)
    assert bad._generation==0 and bad._finite_driver is None
    token=CancellationToken();token.cancel('plastic S3 prefix')
    with pytest.raises(SolveCancelled):
        analysis.solve(DIRECTION,(initial*1.02,),cancellation_token=token,**kw)
    assert analysis.checkpoint()==saved
    with pytest.raises(RuntimeError):
        analysis.solve(DIRECTION,(initial*1.02,),displacement_control=CONTROL,
                       max_iterations=1,max_backtracks=0)
    assert analysis.checkpoint()==saved
    final=analysis.solve(DIRECTION,(initial*1.02,),**kw)
    continued=resumed.solve(DIRECTION,(initial*1.02,),**kw)
    assert analysis.checkpoint()==resumed.checkpoint();compare(final,continued)
    assert final.free_equilibrium_ratio<=1e-8 and final.constraint_max<=1e-9
    assert np.any(np.concatenate([r.alpha for r in final.shell_s3_material])>
                  np.concatenate([r.alpha for r in prefix.shell_s3_material]))
    (tmp_path/'plastic-s3-final.checkpoint').write_bytes(analysis.checkpoint())

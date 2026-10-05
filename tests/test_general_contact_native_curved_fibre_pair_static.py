"""Bounded actual-curved physical-fibre pair integration; development evidence."""
import os
import sys
import time
import json
from pathlib import Path
from hashlib import sha256

import numpy as np
import pytest

from test_general_contact_native_fibre_pair_static import (
    _owner, _check_coupled_commit_and_restart,
)


def _curved_owner():
    return _owner(line_stiffness=4000.,gap_step_control=True,
        reference_rise_m=.005,certify_curved_ownership=True)


def test_actual_curved_reference_and_restart_bind_opt_in():
    owner=_curved_owner()
    for curve in owner.contact.reference_curves:
        assert np.linalg.norm(curve[1]-.5*(curve[0]+curve[2]))>1e-4
    raw=owner._checkpoint(())
    state,records=_curved_owner()._restore(raw,sha256(raw).hexdigest())
    assert state.completed_targets==0 and owner._checkpoint(records)==raw
    for incompatible in (
        _owner(line_stiffness=4000.,gap_step_control=True),
        _owner(line_stiffness=4000.,gap_step_control=True,reference_rise_m=.005),
    ):
        with pytest.raises(ValueError,match='binding'):
            incompatible._restore(raw,sha256(raw).hexdigest())


def test_opt_in_straight_pair_preserves_analytic_line_law():
    from test_general_contact_native_curved_pair_ownership import _kernel,_reference,_pose
    # Unequal material-cell breaks on the same physical interval. Constant gap
    # and declared reference line measure give an independent scalar solution.
    a=_reference(.09998,(0.,1.,2.24));b=_reference(0.,(0.,1.12,2.24))
    kernel=_kernel(a,b,certify_curved_ownership=True)
    actual=kernel.evaluate(*_pose(a),*_pose(b))
    length=2.24;gap=.09998-.1;stiffness=100.
    assert actual.potential_j==pytest.approx(.5*stiffness*length*gap**2,rel=1e-8)
    np.testing.assert_allclose(actual.beam_a_force_n,(0.,-stiffness*length*gap,0.),
        rtol=1e-8,atol=1e-12)
    np.testing.assert_allclose(actual.beam_b_force_n,-actual.beam_a_force_n,atol=1e-12)


@pytest.mark.skipif(os.environ.get('CONTACT_NATIVE_CURVED_PAIR_SOLVE')!='1',
    reason='explicit bounded actual-curved coupled development run')
def test_actual_curved_plastic_pair_commit_material_work_and_exact_restart():
    owner=_curved_owner()
    evaluate=owner._contact
    query=owner._physical_gap
    def trace_context():
        frame=sys._getframe(2)
        result=dict(call_path=[])
        for _ in range(6):
            if frame is None:
                break
            result['call_path'].append(frame.f_code.co_name)
            iteration=frame.f_locals.get('iteration')
            if isinstance(iteration,int):
                result['iteration']=iteration
            frame=frame.f_back
        return result
    gap_calls=0
    def recorded_gap(state):
        nonlocal gap_calls
        gap_calls+=1
        started=time.perf_counter()
        event=dict(call=gap_calls,**trace_context())
        output=os.environ.get('CONTACT_APP_RESULT_RECORD')
        if output:
            Path(output+'-last-gap-pose.json').write_text(json.dumps(dict(
                call=gap_calls,
                pose={key:np.asarray(value).tolist()
                      for key,value in state.descriptor().items()},
                reference_rise_m=.005,gap_tolerance_m=5e-5,
                line_stiffness_n_per_m2=4000.),indent=2))
        try:
            result=query(state)
            event.update(status='completed',lower_gap_m=result)
            return result
        except Exception as failure:
            event.update(status='failed',failure=f'{type(failure).__name__}: {failure}')
            raise
        finally:
            if output:
                event['elapsed_s']=time.perf_counter()-started
                with Path(output+'-gap-trace.ndjson').open('a',encoding='utf8') as stream:
                    stream.write(json.dumps(event)+'\n')
    owner._physical_gap=recorded_gap
    calls=0
    def recorded_contact(state):
        nonlocal calls
        calls+=1
        started=time.perf_counter()
        event=dict(call=calls,**trace_context())
        output=os.environ.get('CONTACT_APP_RESULT_RECORD')
        if output:
            # Retain the latest attempted pose even when the bounded process
            # stops during a successful-but-expensive evaluation.
            Path(output+'-last-contact-pose.json').write_text(json.dumps(dict(
                call=calls,
                pose={key:np.asarray(value).tolist()
                      for key,value in state.descriptor().items()},
                reference_rise_m=.005,gap_tolerance_m=5e-5,
                line_stiffness_n_per_m2=4000.),indent=2))
        try:
            result=evaluate(state)
            event.update(status='completed', **{key:getattr(result,key)
                for key in ('potential_j','conservative_lower_gap_m',
                    'minimum_sampled_gap_m',
                    'integration_intervals','integration_evaluations',
                    'integration_cells_checked')})
            return result
        except Exception as failure:
            event.update(status='failed',failure=f'{type(failure).__name__}: {failure}')
            output=os.environ.get('CONTACT_APP_RESULT_RECORD')
            if output:
                Path(output+'-failed-contact-pose.json').write_text(json.dumps(dict(
                    failure=f'{type(failure).__name__}: {failure}',
                    pose={key:np.asarray(value).tolist()
                          for key,value in state.descriptor().items()},
                    reference_rise_m=.005,gap_tolerance_m=5e-5,
                    line_stiffness_n_per_m2=4000.),indent=2))
            raise
        finally:
            output=os.environ.get('CONTACT_APP_RESULT_RECORD')
            if output:
                event['elapsed_s']=time.perf_counter()-started
                with Path(output+'-contact-trace.ndjson').open('a',encoding='utf8') as stream:
                    stream.write(json.dumps(event)+'\n')
    owner._contact=recorded_contact
    record=_check_coupled_commit_and_restart(owner,restart_factory=_curved_owner)
    assert record['gap_lower_m']>=-5e-5

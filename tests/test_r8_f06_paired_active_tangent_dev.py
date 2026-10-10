"""Frozen saved-state derivative controls; numerical imports only under supervisor."""
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.skipif('F06_ACTIVE_TANGENT_OUTPUT' not in os.environ,
                              reason='fresh bounded active-tangent supervisor required')


def test_source_all_flags_negative_calibration():
    from scripts.r8_f06_paired_active_tangent_dev import checked, write
    keys = ('checkpoint','generation','objects','state_object','state_words','accepted_object','controller',
            'driver_object','driver_accepted_object','driver_accepted_words',
            'applied_load_object','applied_load_bytes','snapshot_object',
            'shell_accepted_objects','shell_accepted_words','shell_predecessors_objects','shell_predecessors_words',
            'beam_accepted_objects','beam_accepted_words','beam_predecessors_objects','beam_predecessors_words')
    flags = {key: True for key in keys}
    assert checked(flags)
    for key in keys:
        with pytest.raises(AssertionError):
            checked({**flags,key:False})
    for bad in ({},{'truthy_integer':1},{'truthy_string':'yes'}):
        with pytest.raises(AssertionError):
            checked(bad)
    write(Path(os.environ['F06_ACTIVE_TANGENT_OUTPUT'])/'atomic-negative-calibration.json',
          dict(all_flags_checked=True,individually_refused_false_keys=keys,truthy_nonbool_refused=True))


def test_source_group_norms_and_common_adjacent_plateau():
    import numpy as np
    from scripts.r8_f06_paired_active_tangent_dev import metrics, adjacent_plateau
    rows=np.arange(2);weights=np.array([1.,10.])
    zero=metrics(np.ones(2),np.zeros(2),rows,weights)
    assert not zero['exercised'] and zero['raw_relative'] is zero['work_relative'] is None
    weak=metrics(np.array([1e-12,0.]),np.array([1e-15,0.]),rows,weights)
    assert weak['raw_relative'] == pytest.approx(1000.)
    assert weak['work_relative'] == pytest.approx(1000.)
    assert adjacent_plateau({'a':[1e-4,1e-6,1e-6],'b':[1e-4,1e-6,1e-6]})
    assert not adjacent_plateau({'a':[1e-6,1e-6,1e-4],'b':[1e-4,1e-6,1e-6]})
    assert not adjacent_plateau({'a':[None,0.,0.],'b':[0.,0.,None]})
    assert not adjacent_plateau({})
    assert not adjacent_plateau({'a':[1e-6,2e-6,2e-6]},threshold=1e-6)


def test_source_atomic_state_history_words_and_objects():
    import numpy as np
    from dataclasses import make_dataclass
    from scripts.r8_f06_paired_active_tangent_dev import capture,atomic_flags,checked
    State=make_dataclass('State',[('q',object),('q_low',object)])
    accepted=(dict(alpha=np.array([.1]),plastic=np.array([1e-19])),)
    predecessor=(dict(alpha=np.array([.09]),plastic=np.array([0.])),)
    driver=SimpleNamespace(_state=State(np.array([1.]),np.array([1e-19])),
        _shell_origins=accepted,_shell_predecessors=predecessor,
        _beam_origins=accepted,_beam_predecessors=predecessor,
        _adaptive_state=object(),_displacement_applied_load=np.array([2.]))
    owner=SimpleNamespace(_finite_driver=driver,_generation=9,_accepted=object(),
        _displacement_snapshot=b'seed',checkpoint=lambda:b'constant canonical checkpoint')
    before=capture(owner)
    assert checked(atomic_flags(owner,before))
    driver._state.q_low[0]=2e-19
    assert not atomic_flags(owner,before)['state_words']
    driver._state.q_low[0]=1e-19
    original=driver._shell_origins
    driver._shell_origins=(dict(alpha=np.array([.1]),plastic=np.array([1e-19])),)
    flags=atomic_flags(owner,before)
    assert flags['shell_accepted_words'] and not flags['shell_accepted_objects'] and not flags['objects']
    driver._shell_origins=original
    owner._generation=10
    assert not atomic_flags(owner,before)['generation']
    owner._generation=9
    predecessor[0]['alpha'][0]=.08
    assert not atomic_flags(owner,before)['shell_predecessors_words']
    predecessor[0]['alpha'][0]=.09
    assert checked(atomic_flags(owner,before))


def test_source_frozen_complete_direction():
    import numpy as np
    from scripts.r8_f06_paired_active_tangent_dev import frozen_direction,row_groups
    owner=SimpleNamespace(_K=np.zeros((78,78)),_C=np.zeros((12,78)),_shell_count=12,
        _beam_ids=(1,2,3),_beam_parts=((SimpleNamespace(section=SimpleNamespace(fibres=())),None,None),
                                    (SimpleNamespace(section=SimpleNamespace()),None,None)),
        _fixed=np.array([0,1,2,3,4,5]),_free=np.arange(6,78))
    vector=frozen_direction(owner,np.zeros(90))
    np.testing.assert_array_equal(vector,frozen_direction(owner,np.zeros(90)))
    np.testing.assert_array_equal(vector[:6],0.)
    assert np.linalg.norm(vector[6:30]) > 0.
    assert np.linalg.norm(vector[30:36]) > 0. and np.linalg.norm(vector[54:60]) > 0.
    for at in (36,60,78,84):
        assert np.linalg.norm(vector[at:at+3]) > 0. and np.linalg.norm(vector[at+3:at+6]) > 0.
    groups=row_groups(owner,90)
    np.testing.assert_array_equal(groups['fibre_retained'],np.arange(30,54))
    np.testing.assert_array_equal(groups['generalized_retained'],np.arange(54,78))
    np.testing.assert_array_equal(groups['constraints'],np.arange(78,90))


def test_source_paired_branch_sign_and_segment_crossing():
    from scripts.r8_f06_paired_active_tangent_dev import _native_signature,branch_smooth
    fibre=SimpleNamespace(fibre_id='f',curve=SimpleNamespace(plastic_strain=(0.,.2)))
    element=SimpleNamespace(section=SimpleNamespace(fibres=(fibre,)))
    # Accumulated high words coincide; low-word plastic increments remain active.
    material=dict(origin=dict(stations=[dict(rows=[(0.,0.,.1,0.)])]),
                  history=dict(stations=[dict(rows=[(1e-19,0.,.1,1e-19)])]),
                  stations=[dict(fibres=[dict(branch='PLASTIC_POSITIVE',plastic_increment=(1e-19,0.))])])
    signature=_native_signature(element,material)
    assert signature[0]['active'] and signature[0]['flow_sign'] == 1
    assert signature[0]['hardening_segment'] == 0 and not signature[0]['hardening_knot']
    metadata=[dict(converged=[True],fallback_mask=[False])]
    assert branch_smooth([signature],metadata)
    crossing=[{**signature[0],'branch':'YIELD_BOUNDARY'}]
    assert not branch_smooth([crossing],metadata)
    knot=[{**signature[0],'hardening_knot':True}]
    assert not branch_smooth([knot],metadata)
    assert not branch_smooth([signature],[])
    assert not branch_smooth([signature],[dict(converged=[False],fallback_mask=[False])])
    assert not branch_smooth([signature],[dict(converged=[True],fallback_mask=[True])])


def test_source_unfrozen_step_refused_before_evaluation():
    from scripts.r8_f06_paired_active_tangent_dev import sample
    class Forbidden:
        def __getattr__(self,name):
            raise AssertionError('refusal reached numerical evaluation')
    with pytest.raises(ValueError,match='frozen'):
        sample(Forbidden(),None,None,2e-6)


def test_source_vector_component_crossing_and_true_branch_transition():
    from copy import deepcopy
    from scripts.r8_f06_paired_active_tangent_dev import same_smooth_branch,branch_smooth
    shell=dict(active=[True,False],flow_sign=[[1,0,-1],[0,0,0]],
               hardening_segment=[0,0],hardening_knot=[False,False])
    generalized=[dict(station=0,branch='PLASTIC',active=True,flow_sign=[1,0,-1,0,1,0],
                      hardening_segment='linear')]
    fibre=[dict(station=0,fibre='f',branch='PLASTIC_POSITIVE',active=True,
                flow_sign=1,hardening_segment=0,hardening_knot=False)]
    base=[shell,generalized,fibre]
    changed=deepcopy(base)
    changed[0]['flow_sign'][0][1]=1
    changed[1][0]['flow_sign'][1]=-1
    assert changed != base and same_smooth_branch(base,changed)
    metadata=[dict(converged=[True],fallback_mask=[False])]
    assert branch_smooth(changed,metadata)
    for group,key,value in ((0,'active',[False,False]),(0,'hardening_segment',[1,0]),
                            (0,'hardening_knot',[True,False])):
        transition=deepcopy(base);transition[group][key]=value
        assert not same_smooth_branch(base,transition)
    for group,key,value in ((1,'branch','ELASTIC'),(1,'active',False),
                           (2,'branch','PLASTIC_NEGATIVE'),(2,'flow_sign',-1),
                           (2,'hardening_knot',True),(2,'hardening_segment',1)):
        transition=deepcopy(base);transition[group][0][key]=value
        assert not same_smooth_branch(base,transition)
    knot=deepcopy(base);knot[0]['hardening_knot'][0]=True
    assert not branch_smooth(knot,metadata)
    yielding=deepcopy(base);yielding[1][0]['branch']='YIELD_BOUNDARY'
    assert not branch_smooth(yielding,metadata)


def test_installed_saved_state_algorithmic_tangent():
    from scripts.r8_f06_paired_active_tangent_dev import assess
    result=assess(Path(os.environ['F06_ACTIVE_TANGENT_OUTPUT']))
    assert result['status'] == 'SCOPED_PASS'

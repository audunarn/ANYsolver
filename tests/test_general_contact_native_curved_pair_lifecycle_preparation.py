"""Identity-only preparation reuse with fake builders; no physical solve oracle."""
import json
from types import SimpleNamespace

import pytest

import test_general_contact_native_curved_pair_lifecycle as lifecycle


@pytest.fixture(autouse=True)
def isolated_identity_cache(monkeypatch):
    monkeypatch.setattr(lifecycle,'_TEMPLATE_IDENTITIES',{})


def _options(**changed):
    options=dict(physical_fibres=True,plastic_fibres=True,targets=(.05,0.,.05),
        separation=.101,force=-.05,line_stiffness_n_per_m2=8000.,
        gap_tolerance_m=5e-5,gap_step_control=True,reference_rise_m=.005,
        certify_curved_ownership=True,reuse_target_trials=True)
    return {**options,**changed}


def _seed(tmp_path,version=1):
    path=tmp_path/'seed.json'
    path.write_text(json.dumps({'records':[{'mechanical':{'version':version}}]},sort_keys=True,separators=(',',':'))+'\n',encoding='ascii',newline='\n')
    return path


def _builder():
    calls=[]
    def build(**options):
        calls.append(options)
        if 'initial_trial' not in options:
            return SimpleNamespace(context=SimpleNamespace(identity='template-'+str(len(calls))))
        return SimpleNamespace(seed=options['initial_trial'],unique=object())
    return build,calls


def test_hits_reuse_only_string_and_actual_owners_are_fresh(tmp_path):
    build,calls=_builder();path=_seed(tmp_path);options=_options()
    first=lifecycle._build_owner_with_template_identity(build,options,path)
    second=lifecycle._build_owner_with_template_identity(build,options,path)
    assert len(calls)==3 and ['initial_trial' in c for c in calls]==[False,True,True]
    assert first is not second and first.unique is not second.unique
    assert first.seed is not second.seed and first.seed['mechanical'] is not second.seed['mechanical']
    assert first.seed['native_model']==second.seed['native_model']=='template-1'
    assert all(type(value) is str for value in lifecycle._TEMPLATE_IDENTITIES.values())
    assert calls[0]==options
    assert all({k:v for k,v in call.items() if k!='initial_trial'}==options for call in calls[1:])


@pytest.mark.parametrize('changed',[{'targets':(.05,0.,.06)}, {'reuse_target_trials':False},
    {'separation':.102}, {'physical_fibres':False}, {'plastic_fibres':False},
    {'force':-.06}, {'line_stiffness_n_per_m2':8001.}, {'gap_tolerance_m':6e-5},
    {'gap_step_control':False}, {'reference_rise_m':.006}, {'certify_curved_ownership':False}])
def test_every_option_is_bound_and_changed_targets_miss(tmp_path,changed):
    build,calls=_builder();path=_seed(tmp_path)
    lifecycle._build_owner_with_template_identity(build,_options(),path)
    lifecycle._build_owner_with_template_identity(build,_options(**changed),path)
    assert len(calls)==4 and len(lifecycle._TEMPLATE_IDENTITIES)==2


def test_seed_raw_byte_mutation_misses_even_for_same_mechanical_descriptor(tmp_path):
    build,calls=_builder();path=_seed(tmp_path)
    lifecycle._build_owner_with_template_identity(build,_options(),path)
    changed=json.loads(path.read_bytes());changed['metadata']='different raw input'
    path.write_text(json.dumps(changed,sort_keys=True,separators=(',',':'))+'\n',encoding='ascii',newline='\n')
    lifecycle._build_owner_with_template_identity(build,_options(),path)
    assert len(calls)==4 and len(lifecycle._TEMPLATE_IDENTITIES)==2


@pytest.mark.parametrize('changed',[{'targets':[.05,0.,.05]}, {'targets':(True,0.,.05)},
    {'targets':(1,0.,.05)}, {'reuse_target_trials':1}, {'reuse_target_trials':'yes'},
    {'separation':0}, {'force':float('nan')}, {'targets':(float('inf'),)}])
def test_nonstandard_or_invalid_inputs_use_original_path_without_type_collision(tmp_path,changed):
    build,calls=_builder();path=_seed(tmp_path);options=_options(**changed)
    for _ in range(2):lifecycle._build_owner_with_template_identity(build,options,path)
    assert len(calls)==4 and lifecycle._TEMPLATE_IDENTITIES=={}
    assert calls[0]['targets'] is options['targets'] and calls[2]['targets'] is options['targets']


def test_float_subclass_is_not_coerced_and_signed_zero_does_not_collide(tmp_path):
    class UserFloat(float):pass
    assert lifecycle._template_options_key(_options(force=UserFloat(-.05))) is None
    assert lifecycle._template_options_key(_options(force=0.))!=lifecycle._template_options_key(_options(force=-0.))


@pytest.mark.parametrize('failure_stage',['template','actual','decode'])
def test_failed_preparation_never_poisoned_cache(tmp_path,failure_stage):
    build,calls=_builder();path=_seed(tmp_path)
    def failed(**options):
        if ('initial_trial' in options)==(failure_stage=='actual'):
            raise RuntimeError('injected '+failure_stage)
        return build(**options)
    if failure_stage=='decode':
        path.write_text('{',encoding='ascii')
        with pytest.raises(ValueError):lifecycle._build_owner_with_template_identity(build,_options(),path)
    else:
        with pytest.raises(RuntimeError,match='injected'):
            lifecycle._build_owner_with_template_identity(failed,_options(),path)
    assert lifecycle._TEMPLATE_IDENTITIES=={}
    _seed(tmp_path)
    lifecycle._build_owner_with_template_identity(build,_options(),path)
    assert len(lifecycle._TEMPLATE_IDENTITIES)==1


def test_cache_is_bounded_without_suppressing_actual_construction(tmp_path,monkeypatch):
    monkeypatch.setattr(lifecycle,'_MAX_TEMPLATE_IDENTITIES',1)
    build,calls=_builder();path=_seed(tmp_path)
    lifecycle._build_owner_with_template_identity(build,_options(),path)
    for _ in range(2):lifecycle._build_owner_with_template_identity(build,_options(targets=(.06,)),path)
    assert len(lifecycle._TEMPLATE_IDENTITIES)==1 and len(calls)==6


@pytest.mark.parametrize('changed',[{'reuse_target_trials':[]},{'targets':()}])
def test_original_validation_exception_precedes_missing_seed_read(tmp_path,changed):
    seen=[]
    def refused(**options):
        seen.append(options);raise TypeError('original builder validation')
    with pytest.raises(TypeError,match='original builder validation'):
        lifecycle._build_owner_with_template_identity(refused,_options(**changed),tmp_path/'absent')
    assert len(seen)==1 and lifecycle._TEMPLATE_IDENTITIES=={}


def test_owner_entry_connects_cache_and_always_calls_original_builder(tmp_path,monkeypatch):
    build,calls=_builder()
    path=tmp_path/'tests/data/general_contact_native_curved_fibre_pair_seeded_k8_v1.checkpoint'
    path.parent.mkdir(parents=True);path.write_text('{"records":[{"mechanical":{}}]}\n',encoding='ascii',newline='\n')
    monkeypatch.setattr(lifecycle,'ROOT',tmp_path)
    monkeypatch.setattr(lifecycle.runpy,'run_path',lambda path:{'analysis':build})
    a=lifecycle._owner();b=lifecycle._owner()
    assert a is not b and len(calls)==3
    assert calls[1]['initial_trial']['native_model']==calls[2]['initial_trial']['native_model']

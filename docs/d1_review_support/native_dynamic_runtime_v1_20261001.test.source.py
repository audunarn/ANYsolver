"""Source-bound resource-contract controls; no physical time steps."""
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
from time import monotonic, perf_counter

import numpy as np
import pytest

from anysolver import _ge_beam3_dynamic_elastic_state as dynamic
from anysolver import _ge_beam3_native_dynamic_restart as codec
from anysolver.ge_beam3_native_dynamics import SELECTOR, create_analysis, workflow_provenance
from anysolver._ge_beam3_native_midpoint import MidpointContext
from anysolver._ge_beam3_operator_validation_scope import operator_validation_scope
from anysolver._ge_beam3_p5_seeded.core import canonical, sha
from test_ge_beam3_native_midpoint import make_analysis


class FloatSubclass(float):
    pass


class IntSubclass(int):
    pass


def _account(value):
    row = asdict(value)
    row['rank_mass_checks'] = json.loads(row['rank_mass_checks'])
    return json.loads(canonical(row))


def _fresh(owner):
    c = owner._context
    assert c._current is c._visible_current is c._current_bytes is None
    assert not c._issued and not c._candidates
    assert c._initial_checks is c._restore_checks is None
    assert c._work_session is c._dynamic._active_session is None
    assert len(c._dynamic._issued) == 1


def test_runtime_admission_and_atomic_restore(monkeypatch, record_property):
    started = perf_counter()
    inputs_path = Path(os.environ['NATIVE_DYNAMIC_RUNTIME_INPUTS'])
    inputs_bytes = inputs_path.read_bytes()
    inputs = json.loads(inputs_bytes)
    output = Path(os.environ['NATIVE_DYNAMIC_RUNTIME_RAW_OUTPUT'])
    assert not output.exists()
    evidence = dict(status='RUNNING', physical_steps=0, successful_constructors=0,
        invalid_constructor_attempts=0, controls=[],
        scope='Resource identity/guard/atomic codec control only; no dynamics qualification',
        input_sha256=sha256(inputs_bytes).hexdigest(),
        effective_environment={key:os.environ.get(key) for key in
            ('PYTHONPATH','NUMBA_CACHE_DIR','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')})
    def save(stage):
        evidence.update(last_stage=stage,elapsed_seconds=perf_counter()-started)
        output.write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n')
        print(json.dumps(dict(stage=stage,elapsed_seconds=evidence['elapsed_seconds'])),flush=True)
        assert evidence['elapsed_seconds'] < 120.
    try:
        for key, binding in inputs['source_hashes'].items():
            assert sha256(Path(binding['path']).read_bytes()).hexdigest() == binding['sha256'], key
        assert all(evidence['effective_environment'][key] == '1' for key in
            ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
        _, definition = make_analysis()
        invalid = [('bool_true',True),('bool_false',False),('float_subclass',FloatSubclass(840.)),
            ('int_subclass',IntSubclass(840)),('nan',float('nan')),('inf',float('inf')),
            ('negative_inf',-float('inf')),('zero',0.),('negative',-1.),('above_cap',900.0001)]
        for label,value in invalid:
            with pytest.raises(ValueError,match='positive finite native dynamic runtime'):
                create_analysis(SELECTOR,(definition,),(),runtime_limit_seconds=value)
            evidence['invalid_constructor_attempts'] += 1
            evidence['controls'].append(label)
        clamped, _ = make_analysis()
        with pytest.raises(ValueError,match='extended runtime requires the dynamic elastic owner'):
            MidpointContext(clamped,runtime_limit_seconds=840.)
        evidence['controls'].append('legacy_nondefault_rejected')
        # Independent captured clock; expiry controls patch the callable only.
        # No captured started/duration is repaired or renewed by this fixture.
        clock0 = float(monotonic())
        monkeypatch.setattr(dynamic,'monotonic',lambda: clock0)
        default = create_analysis(SELECTOR,(definition,),())
        extended = create_analysis(SELECTOR,(definition,),(),runtime_limit_seconds=840)
        evidence['successful_constructors'] = 2
        dc, c = default._context, extended._context
        _fresh(default); _fresh(extended)
        assert dc.runtime_limit_seconds == dc._dynamic.runtime_limit_seconds == 120.
        assert c.runtime_limit_seconds == c._dynamic.runtime_limit_seconds == 840.
        assert type(c.runtime_limit_seconds) is float
        assert 'runtime_limit_seconds' not in dc._dynamic._definition()
        assert c._dynamic._definition()['runtime_limit_seconds'] == 840.
        assert dc._identity == sha(dc._identity_data()) and c._identity == sha(c._identity_data())
        assert dc._dynamic._identity == sha(dc._dynamic._definition())
        assert c._dynamic._identity == sha(c._dynamic._definition())
        assert default.identity != extended.identity
        assert codec.contract(dc)['settings']['lifetime_seconds'] == 120.
        assert codec.contract(c)['settings']['lifetime_seconds'] == 840.
        evidence['identities'] = dict(default=workflow_provenance(default),extended=workflow_provenance(extended),
            default_dynamic_definition=json.loads(canonical(dc._dynamic._definition())),
            extended_dynamic_definition=json.loads(canonical(c._dynamic._definition())),
            default_settings=codec.contract(dc)['settings'],extended_settings=codec.contract(c)['settings'])
        # Default still uses the accepted helper; extended must use direct full checks.
        helper_calls=[]
        original_helper=dynamic.operator_call
        def observe_helper(*args,**kwargs):
            helper_calls.append(True)
            return original_helper(*args,**kwargs)
        with monkeypatch.context() as patch:
            patch.setattr(dynamic,'operator_call',observe_helper)
            with operator_validation_scope():
                dc._dynamic.evaluate(dc._dynamic.reference_state())
        assert helper_calls and default.current is None
        evidence['default_helper_calls'] = len(helper_calls)
        with operator_validation_scope():
            with pytest.raises(ValueError,match='excludes optional operator validation scope'):
                _ = extended.identity
        _fresh(extended)
        evidence['controls'].append('extended_optional_validation_scope_rejected')
        for obj,field,value,label in ((c,'runtime_limit_seconds',841.,'midpoint_duration_alias'),
                (c,'runtime_limit_seconds',FloatSubclass(840.),'midpoint_duration_subclass'),
                (c._dynamic,'runtime_limit_seconds',841.,'dynamic_duration_alias'),
                (c._dynamic,'started',clock0+1.,'dynamic_start_alias')):
            with monkeypatch.context() as patch:
                patch.setattr(obj,field,value)
                with pytest.raises(ValueError,match='captured runtime'):
                    _ = extended.identity
                with pytest.raises(ValueError,match='captured runtime'):
                    c._guard(stage='midpoint.stage')
            _fresh(extended)
            evidence['controls'].append(label)
        work_calls=[]
        original_work=c._loaded_work
        def observe_work(*args,**kwargs):
            work_calls.append(True)
            return original_work(*args,**kwargs)
        with monkeypatch.context() as patch:
            patch.setattr(c,'_loaded_work',observe_work)
            patch.setattr(dynamic,'monotonic',lambda: clock0+841.)
            with pytest.raises(RuntimeError,match='context deadline'):
                extended.initialize()
        _fresh(extended)
        assert not work_calls
        evidence['controls'].append('expiry_before_structural_work')
        # Entry validator succeeds; the real final validator consumes the budget.
        # Save tentative issuance while still invisible, then require rollback.
        validations=[]
        original_require=codec.require_contract
        with monkeypatch.context() as patch:
            # Use this scoped patch for the mocked clock changed inside the validator.
            def scoped_expire_final(context):
                result=original_require(context)
                if context is c:
                    validations.append(dict(call=len(validations)+1,
                        tentative_current=context._current is not None,
                        visible_current=context._visible_current is not None,
                        issued_count=len(context._issued)))
                    if len(validations)==2:
                        evidence['expiry_exit_tentative_state']=json.loads(canonical(context._current))
                        patch.setattr(dynamic,'monotonic',lambda: clock0+841.)
                return result
            patch.setattr(codec,'require_contract',scoped_expire_final)
            with pytest.raises(RuntimeError,match='context deadline'):
                extended.initialize()
        _fresh(extended)
        assert len(validations)==2 and validations[-1]['tentative_current']
        assert not validations[-1]['visible_current'] and validations[-1]['issued_count']==1
        assert c._dynamic.started == c._dynamic._captured_started == clock0
        evidence['final_validation_calls']=validations
        evidence['controls'].append('expiry_after_final_artifact_validation_rollback')
        save('negative_clock_controls_complete')
        with monkeypatch.context() as patch:
            patch.setattr(dynamic,'operator_call',observe_helper)
            prior_helper_count=len(helper_calls)
            state=extended.initialize()
        assert len(helper_calls)==prior_helper_count
        assert extended.current is state and state.epoch==0 and state.time==0.
        assert np.count_nonzero(state.physical_velocity24)==0
        evidence['state']=json.loads(canonical(state))
        evidence['initial_checks']=extended.initial_checks
        evidence['accounting']=_account(extended.endpoint_accounting(state))
        raw=extended.create_checkpoint(); digest=sha256(raw).hexdigest()
        evidence['checkpoint']=dict(sha256=digest,byte_count=len(raw),complete_payload=json.loads(raw))
        assert json.loads(raw)['header']['settings']['lifetime_seconds']==840.
        _fresh(default)
        default_work=[]
        original_default_work=dc._loaded_work
        def observe_default_work(*args,**kwargs):
            default_work.append(True)
            return original_default_work(*args,**kwargs)
        with monkeypatch.context() as patch:
            patch.setattr(dc,'_loaded_work',observe_default_work)
            with pytest.raises(ValueError,match='checkpoint header/body authority mismatch'):
                default.restore_checkpoint(raw,expected_sha256=digest)
        _fresh(default); assert not default_work
        evidence['controls'].append('incompatible_duration_restore_before_work_publication')
        matching=create_analysis(SELECTOR,(definition,),(),runtime_limit_seconds=840.)
        evidence['successful_constructors']=3
        _fresh(matching)
        restored=matching.restore_checkpoint(raw,expected_sha256=digest)
        evidence['restored_state']=json.loads(canonical(restored))
        evidence['restored_accounting']=_account(matching.endpoint_accounting(restored))
        evidence['restore_checks']=matching.restore_checks
        evidence['checkpoint_reexport_sha256']=sha256(matching.create_checkpoint()).hexdigest()
        assert restored is matching.current and restored is not state
        assert canonical(restored)==canonical(state)
        assert canonical(evidence['restored_accounting'])==canonical(evidence['accounting'])
        assert matching.create_checkpoint()==raw
        assert extended.initial_checks['algebraic_rank']==27
        assert extended.initial_checks['physical_mass_min_eigenvalue']>0.
        assert matching.restore_checks['physical_balance_norm']<=1e-11
        assert matching.restore_checks['algebraic_residual_norm']<=1e-11
        assert matching.restore_checks['algebraic_correction_norm']<=1e-11
        assert c._dynamic.started==c._dynamic._captured_started==clock0
        assert default.current is None and evidence['physical_steps']==0
        evidence['controls'].append('matching_duration_complete_restore_parity')
        evidence['status']='PASS'
        save('runtime_controls_complete')
        record_property('runtime_controls',json.dumps(evidence['controls']))
    except BaseException as error:
        evidence.update(status='NONPASS',failure_type=type(error).__name__,failure=str(error))
        save('runtime_controls_failure')
        raise

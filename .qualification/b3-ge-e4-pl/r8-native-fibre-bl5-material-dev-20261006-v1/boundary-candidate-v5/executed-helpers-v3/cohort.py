from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
import json
import numpy as np
import pytest
from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver
from anysolver._ge_beam3_fibre_cell import FibreCellConjugate
from anysolver._ge_beam3_generalized_cell import GeneralizedCellConjugate


def execute(folder,repo):
    current='preparation';reports=[];accepted=[];calls=[]
    original_publish=FinitePointDriver._publish_equilibrium
    original_cell=FibreCellConjugate.response;original_generalized=GeneralizedCellConjugate.response
    original_assemble=FinitePointDriver._assemble;original_advance=FinitePointDriver._advance
    original_boundary=FinitePointDriver._native_boundary_amount
    def save():
        (folder/'accepted-histories.json').write_text(json.dumps(accepted,indent=2))
        (folder/'work.json').write_text(json.dumps(calls,indent=2))
        (folder/'test-reports.json').write_text(json.dumps(reports,indent=2))
    class Record:
        def pytest_runtest_setup(self,item):
            nonlocal current
            current=item.nodeid
        def pytest_runtest_logreport(self,report):
            reports.append(dict(nodeid=report.nodeid,when=report.when,outcome=report.outcome,duration=report.duration))
            save()
    def publish(self,*args,**kwargs):
        generation=self.owner._generation
        try:return original_publish(self,*args,**kwargs)
        finally:
            if self.owner._generation!=generation:
                r=self._accepted
                item=dict(test=current,factor=r.load_factor,generation=r.generation,iterations=r.iterations,
                    relative=r.free_equilibrium_ratio,gap=r.constraint_max,shell=np.asarray(r.shell_layer_alpha).tolist(),
                    beams=np.asarray(r.beam_station_accumulated).tolist(),policy=self.owner._definition.bl5_material_policy,
                    fixed_attempts=[asdict(a) for a in self._adaptive_state.attempts] if self._adaptive_state else [])
                accepted.append(item)
                (folder/('accepted-%04d.bin'%len(accepted))).write_bytes(self.owner.checkpoint())
                save()
    def cell_response(family,original):
        def record(self,*args,**kwargs):
            out=original(self,*args,**kwargs)
            calls.append(dict(test=current,method=family,iterations=out['iterations'],evaluations=out['evaluations'],
                line_trials=out.get('line_trials',0),capture_trial=bool(kwargs.get('capture_trial',False))))
            return out
        return record
    def assemble(self,*args,**kwargs):
        calls.append(dict(test=current,method='assemble',factor=float(args[1])))
        return original_assemble(self,*args,**kwargs)
    def advance(self,*args,**kwargs):
        calls.append(dict(test=current,method='advance',amount=float(args[2])))
        return original_advance(self,*args,**kwargs)
    def boundary(self,*args,**kwargs):
        amount=original_boundary(self,*args,**kwargs)
        calls.append(dict(test=current,method='boundary_amount',amount=amount))
        return amount
    targets=(
        'tests/test_stiffened_shell_native_fibre_bl5_material.py::test_native_material_lifecycle_and_fixed_predecessor_tangent',
        'tests/test_stiffened_shell_native_fibre_bl5.py::test_true_yield_refusal_and_ownership_error_not_domain_or_retry',
        'tests/test_stiffened_shell_bl5_material.py::test_selected_bl5_pre_yield_snapshot_and_legacy_isolation',
        'tests/test_stiffened_shell_bl5_material.py::test_bl5_generalized_yield_reject_rebase_reverse_and_restart',
        'tests/test_stiffened_shell_ge_finite_experimental.py::test_finite_point_panel_accepts_two_complete_elastic_increments',
        'tests/test_stiffened_shell_ge_finite_experimental.py::test_q4_shell_and_beam_yield_atomically_and_restart',
    )
    try:
        with patch.object(FinitePointDriver,'_publish_equilibrium',publish),patch.object(FinitePointDriver,'_assemble',assemble),\
             patch.object(FinitePointDriver,'_advance',advance),patch.object(FinitePointDriver,'_native_boundary_amount',boundary),\
             patch.object(FibreCellConjugate,'response',cell_response('physical_cell',original_cell)),\
             patch.object(GeneralizedCellConjugate,'response',cell_response('generalized_cell',original_generalized)):
            status=pytest.main(['-q','-p','no:cacheprovider','--basetemp',str(folder/'tmp'),
                '--junitxml='+str(folder/'junit.xml')]+[str(repo/t.split('::')[0])+'::'+t.split('::')[1] for t in targets],plugins=[Record()])
        result=dict(pytest_exit_code=int(status),selected_targets=targets,
                    call_reports=[r for r in reports if r['when']=='call'],accepted_commits=len(accepted),recorded_calls=len(calls))
        (folder/'result.json').write_text(json.dumps(result,indent=2))
        return int(status)
    finally:save()

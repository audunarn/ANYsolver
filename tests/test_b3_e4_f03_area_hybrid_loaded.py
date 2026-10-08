"""Tiny finite-pad three-family algebra tests; no registered case execution."""

from hashlib import sha256
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import linalg

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import _b3_e4_f03_area_hybrid_loaded as compared
import _b3_e4_f03_area_loaded as original
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_trace_dual_exact as exact_norm


@pytest.mark.parametrize("topology",("Q4","CST-CB"))
def test_tiny_common_physical_problem_and_original_p1(topology):
    mesh=(2,4,2,2)
    snapshots=[]
    data,states=compared.solve_case(
        *mesh,topology,
        family_sink=lambda name,metrics,q,lam: snapshots.append((name,metrics,q,lam)))
    old_states=[]
    old=original.solve(*mesh,topology,"P1","smooth",.05,
                       state_sink=lambda q,lam: old_states.extend((q,lam)))
    assert data["mesh"]==list(mesh)
    assert data["topology"]==topology
    assert list(data["families"])==["P1","hybrid","enriched"]
    assert [entry[0] for entry in snapshots]==["P1","hybrid","enriched"]
    for name,metrics,q_snapshot,lam_snapshot in snapshots:
        np.testing.assert_array_equal(q_snapshot,states[f"{name}_q"])
        np.testing.assert_array_equal(lam_snapshot,states[f"{name}_lambda"])
        assert q_snapshot is not states[f"{name}_q"]
        assert lam_snapshot is not states[f"{name}_lambda"]
        assert metrics==data["families"][name]
        assert metrics is not data["families"][name]
    snapshots[0][2][0]=np.nan
    snapshots[0][3][0]=np.nan
    snapshots[0][1]["tip_pose_m"][0]=np.nan
    assert np.all(np.isfinite(states["P1_q"]))
    assert np.all(np.isfinite(states["P1_lambda"]))
    assert np.all(np.isfinite(data["families"]["P1"]["tip_pose_m"]))
    np.testing.assert_allclose(states["P1_q"],old_states[0],rtol=1e-10,atol=1e-13)
    np.testing.assert_allclose(states["P1_lambda"],old_states[1],rtol=1e-10,atol=1e-5)
    p1=data["families"]["P1"]
    for key,reference in (("tip_pose_m",old.displacement_tip_m),
                          ("support_wrenches",old.support_wrenches),
                          ("root_elastic_wrench",old.beam_root_elastic_wrench),
                          ("root_port_wrench",old.beam_root_port_wrench),
                          ("root_load_wrench",old.beam_root_load_wrench),
                          ("line_quarter_wrenches",old.beam_port_quarter_wrenches)):
        np.testing.assert_allclose(p1[key],reference,rtol=1e-10,atol=1e-5)
    for key in ("shell_energy_j","beam_energy_j","external_work_j",
                "interface_work_j","gap_l2_m","free_residual_scaled",
                "weak_gap_scaled"):
        np.testing.assert_allclose(p1[key],getattr(old,key),rtol=1e-10,atol=1e-10)
    for family,metrics in data["families"].items():
        q,lam=states[f"{family}_q"],states[f"{family}_lambda"]
        assert q.ndim==lam.ndim==1 and np.all(np.isfinite(q))
        assert np.all(np.isfinite(lam))
        assert metrics["free_residual_scaled"]<1e-8
        assert metrics["weak_gap_scaled"]<1e-8
        assert max(map(abs,metrics["balance_scaled"]))<1e-8
        assert metrics["energy_scaled"]<1e-8
        assert metrics["combined_dual_norm_N"]>=0
        assert len(metrics["physical_line_coefficients"])==mesh[3]+1
        assert np.asarray(metrics["endpoint_atoms"]).shape==(2,3)
        assert np.asarray(metrics["line_quarter_wrenches"]).shape==(4,3)
        assert np.asarray(metrics["physical_quarter_wrenches"]).shape==(4,3)
        root_line=np.asarray(metrics["root_line_wrench"])
        root_end=np.asarray(metrics["root_endpoint_wrench"])
        root_port=np.asarray(metrics["root_port_wrench"])
        np.testing.assert_allclose(root_line+root_end,root_port,rtol=1e-10,atol=1e-5)
        np.testing.assert_allclose(np.sum(metrics["physical_quarter_wrenches"],axis=0),
                                   (np.sum(metrics["line_quarter_wrenches"],axis=0)+
                                    [metrics["endpoint_atoms"][0][0]+metrics["endpoint_atoms"][1][0],
                                     metrics["endpoint_atoms"][0][1]+metrics["endpoint_atoms"][1][1],
                                     .46*(metrics["endpoint_atoms"][0][2]+metrics["endpoint_atoms"][1][2])+
                                     metrics["endpoint_atoms"][1][1]]),
                                   rtol=1e-10,atol=1e-5)
        if family!="P1":
            assert max(map(abs,np.ravel(metrics["endpoint_gaps_m"])))<1e-8
        status=metrics["stability"]
        assert len(status["generalized_eigenvalues"])==len(lam)
        assert status["structural_solve_relative_residual"]<1e-8
    assert data["enriched_energy_order_scaled"]<1e-8
    model=shell.panel(mesh[0],mesh[1],topology)
    # A support at only the beam's x/y/yaw root coordinates, not its slope.
    assert len(beam.root_dofs(mesh[2]))==3
    assert len(states["P1_q"])==model.dof_count+beam.dof_count(mesh[2])


def test_later_failure_preserves_prior_callback_and_exception_type(monkeypatch):
    original_dual=compared.trace_dual.dual_gram
    def fail_hybrid(n_mortar,family,subdivisions):
        if family=="hybrid":
            raise MemoryError("synthetic later-family factorization failure")
        return original_dual(n_mortar,family,subdivisions)
    monkeypatch.setattr(compared.trace_dual,"dual_gram",fail_hybrid)
    completed=[]
    with pytest.raises(MemoryError,match="synthetic later-family") as caught:
        compared.solve_case(2,4,2,2,"Q4",family_sink=lambda *values: completed.append(values))
    assert [record[0] for record in completed]==["P1"]
    assert np.all(np.isfinite(completed[0][2]))
    assert np.all(np.isfinite(completed[0][3]))
    assert any("hybrid finite-pad family" in note for note in caught.value.__notes__)


@pytest.mark.parametrize("topology",("Q4","CST-CB"))
def test_tiny_analytic_norm_keeps_physical_states_and_binds_source(topology):
    mesh=(2,4,2,2)
    historical,historical_states=compared.solve_case(*mesh,topology)
    analytic,analytic_states=compared.solve_case(
        *mesh,topology,norm_source="analytic_h1")
    assert 'norm_source' not in historical
    assert analytic['norm_source']=='analytic_h1'
    digest=sha256(Path(exact_norm.__file__).read_bytes()).hexdigest()
    for family in ('P1','hybrid','enriched'):
        for state_name in ('q','lambda'):
            key=f'{family}_{state_name}'
            np.testing.assert_allclose(analytic_states[key],historical_states[key],
                                       rtol=1e-10,atol=1e-13)
        a=analytic['families'][family]
        b=historical['families'][family]
        for key,value in b.items():
            if key in ('stability','combined_dual_norm_N'):
                continue
            np.testing.assert_allclose(a[key],value,rtol=1e-10,atol=1e-9)
        status=a['stability']
        assert status['norm_source']=='analytic_h1'
        assert status['auxiliary_status']=='PIECEWISE_ANALYTIC_FLOATING'
        assert 'auxiliary_squared_norm_change' not in status
        assert 'norm_source' not in b['stability']
        identity=status['norm_identity']
        metadata=exact_norm.metadata(mesh[3],family)
        assert identity==compared.analytic_norm_identity(mesh[3],family)
        assert identity['source_sha256']==digest
        assert identity['normalized_rows'] is True
        assert identity['row_measures']==list(metadata.row_measures)
        assert identity['selected_enriched_rows']==list(metadata.selected_enriched_rows)
        assert identity['series_terms']==metadata.series_terms
        scalar=exact_norm.dual_gram(mesh[3],family)
        lam=analytic_states[f'{family}_lambda']
        measures=np.repeat(metadata.row_measures,3)
        muhat=lam*compared.scaling.U0*measures/compared.scaling.E0
        independent=float(np.sqrt(muhat@np.kron(scalar,np.eye(3))@muhat)*
                          compared.scaling.E0/compared.scaling.U0)
        assert a['combined_dual_norm_N']==pytest.approx(independent,rel=1e-11)
    assert analytic['enriched_energy_order_scaled']==pytest.approx(
        historical['enriched_energy_order_scaled'],rel=1e-10,abs=1e-12)


def test_unknown_norm_source_fails_before_physical_assembly():
    with pytest.raises(ValueError,match="unsupported independent trace norm"):
        compared.solve_case(2,4,2,2,'Q4',norm_source='unknown')
    with pytest.raises(ValueError,match="requires analytic_h1"):
        compared.solve_case(2,4,2,2,'Q4',stability_sink=lambda *args: None)


def test_saved_analytic_states_reconstruct_without_equilibrium_solve(monkeypatch):
    mesh=(2,4,2,2)
    direct,direct_states=compared.solve_case(*mesh,'Q4',norm_source='analytic_h1')
    source={key:value.copy() for key,value in direct_states.items()}
    def forbid_equilibrium(*args,**kwargs):
        raise AssertionError('equilibrium KKT assembly/factorization was called')
    monkeypatch.setattr(compared.stability,'normalized_kkt',forbid_equilibrium)
    monkeypatch.setattr(compared,'splu',forbid_equilibrium)
    matrices=[]
    replay,replay_states=compared.solve_case(
        *mesh,'Q4',norm_source='analytic_h1',saved_states=source,
        stability_sink=lambda family,s,g: matrices.append((family,s,g)))
    assert replay['equilibrium_source']=='saved_states'
    assert 'equilibrium_source' not in direct
    assert [family for family,_,_ in matrices]==['P1','hybrid','enriched']
    for family in ('P1','hybrid','enriched'):
        for field in ('q','lambda'):
            key=f'{family}_{field}'
            np.testing.assert_array_equal(replay_states[key],source[key])
            assert replay_states[key] is not source[key]
        reconstructed=replay['families'][family]
        reference=direct['families'][family]
        for key,value in reference.items():
            if key=='stability':
                assert reconstructed[key]==value
            else:
                np.testing.assert_allclose(reconstructed[key],value,
                                           rtol=1e-10,atol=1e-9)
        _,schur,gram=next(item for item in matrices if item[0]==family)
        assert schur.shape==gram.shape==(len(replay_states[f'{family}_lambda']),)*2
        expected=np.kron(exact_norm.dual_gram(mesh[3],family),np.eye(3))
        np.testing.assert_allclose(gram,expected,rtol=0,atol=0)
        np.testing.assert_allclose(linalg.eigvalsh(schur,gram),
            reconstructed['stability']['generalized_eigenvalues'],rtol=2e-11)
    matrices[0][1][0,0]=np.nan
    matrices[0][2][0,0]=np.nan
    assert np.all(np.isfinite(replay['families']['P1']['stability'][
        'generalized_eigenvalues']))
    source['P1_q'][0]=np.nan
    source['P1_lambda'][0]=np.nan
    assert np.all(np.isfinite(replay_states['P1_q']))
    assert np.all(np.isfinite(replay_states['P1_lambda']))


def test_saved_states_validate_exact_physical_array_layout():
    _,states=compared.solve_case(2,4,2,2,'Q4')
    incorrect=[]
    missing=states.copy(); missing.pop('P1_q'); incorrect.append(missing)
    wrong_dtype=states.copy(); wrong_dtype['P1_q']=states['P1_q'].astype('f4')
    incorrect.append(wrong_dtype)
    wrong_length=states.copy(); wrong_length['hybrid_lambda']=states['hybrid_lambda'][:-1]
    incorrect.append(wrong_length)
    nonfinite=states.copy(); nonfinite['enriched_q']=states['enriched_q'].copy()
    nonfinite['enriched_q'][0]=np.nan; incorrect.append(nonfinite)
    fixed=states.copy(); fixed['P1_q']=states['P1_q'].copy()
    fixed['P1_q'][0]=1e-14; incorrect.append(fixed)
    for candidate in incorrect:
        with pytest.raises(ValueError,match='saved'):
            compared.solve_case(2,4,2,2,'Q4',saved_states=candidate)


@pytest.mark.parametrize("kwargs",(
    dict(n_s=0,n_y=4,n_beam=2,n_mortar=2,topology="Q4"),
    dict(n_s=2,n_y=4,n_beam=2,n_mortar=1,topology="Q4"),
    dict(n_s=2,n_y=4,n_beam=2,n_mortar=2,topology="wrong"),
    dict(n_s=2,n_y=4,n_beam=2,n_mortar=2,topology="Q4",halfwidth=float("nan")),
    dict(n_s=2,n_y=4,n_beam=2,n_mortar=2,topology="Q4",halfwidth=.21),
))
def test_rejects_outside_bounded_domain(kwargs):
    with pytest.raises(ValueError,match="bounded finite-pad"):
        compared.solve_case(**kwargs)

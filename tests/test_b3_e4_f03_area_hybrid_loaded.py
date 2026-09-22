"""Tiny finite-pad three-family algebra tests; no registered case execution."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import _b3_e4_f03_area_hybrid_loaded as compared
import _b3_e4_f03_area_loaded as original
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_shell as shell


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

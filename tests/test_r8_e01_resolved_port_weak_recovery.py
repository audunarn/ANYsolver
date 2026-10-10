"""Source-only controls for E01 constituent weak-force recovery."""
from __future__ import annotations

import numpy as np
import pytest

from scripts.r8_e01_resolved_port_reference_dev import build, generate
from scripts.r8_e01_resolved_port_weak_recovery import (
    port_wrench, read_deck, recover, recover_from_displacements, rigid_fit,
    station_contract,
)


@pytest.mark.parametrize("sign", (1, -1))
@pytest.mark.parametrize("load", ("fy", "mx"))
def test_port_pullback_and_rigid_work_are_independent_of_domain(sign, load, tmp_path):
    deck, _ = build(sign, load)
    path = tmp_path/"model.inp"
    path.write_text(deck, encoding="ascii")
    model = read_deck(path)
    x = model["x"]
    np.testing.assert_allclose(x[model["ports"]["BeamPort1000"][0]]-
                               x[model["ports"]["ShellPort1000"][0]],
                               (0., 0., sign*.1))
    rng = np.random.default_rng(391)
    for name, ids in model["sets"].items():
        if name not in model["ports"]:
            continue
        ref, _ = model["ports"][name]
        q = np.array((.003, -.002, .001, .006, -.004, .005))
        u = np.zeros_like(x)
        f = np.zeros_like(x)
        for node in ids:
            u[node] = q[:3]+np.cross(q[3:], x[node]-x[ref])
            f[node] = rng.normal(size=3)
        fitted, gap = rigid_fit(x, u, ids, ref)
        np.testing.assert_allclose(fitted, q, rtol=0., atol=1e-14)
        assert gap < 1e-14
        w = port_wrench(x, f, ids, ref)
        assert abs(w@q-sum(f[n]@u[n] for n in ids)) < 1e-13


def test_zero_field_does_not_pass_unbalanced_load(tmp_path):
    path = tmp_path/"model.inp"
    path.write_text(build(1, "fy")[0], encoding="ascii")
    model = read_deck(path)
    physical = {int(n) for conn in model["elements"].values() for n in conn.ravel()}
    zero = {n: np.zeros(3) for n in physical}
    report = recover_from_displacements(model, zero)
    assert report["classification"].endswith("not accepted E01 reference")
    assert report["independent_node_max_residual_n"] == 0.
    np.testing.assert_allclose(report["stations"]["2000"]["residual_n_nm"],
                               (0., -1000., 0., 100., 0., 0.))
    np.testing.assert_allclose(report["root_plus_applied_n_nm"],
                               (0., 1000., 0., -100., 0., 2000.))
    with pytest.raises(ValueError, match="complete finite"):
        recover_from_displacements(model, {})
    zero[next(iter(physical))] = np.array((float("nan"), 0., 0.))
    with pytest.raises(ValueError, match="complete finite"):
        recover_from_displacements(model, zero)


@pytest.mark.parametrize("sign", (1, -1))
@pytest.mark.parametrize("load", ("fy", "mx"))
def test_nonzero_station_work_and_signed_eccentric_action(sign, load, tmp_path):
    path = tmp_path/"model.inp"
    path.write_text(build(sign, load)[0], encoding="ascii")
    model = read_deck(path)
    for station in (1000, 2000):
        shell_ref = model["ports"][f"ShellPort{station}"][0]
        beam_ref = model["ports"][f"BeamPort{station}"][0]
        arm = model["x"][beam_ref]-model["x"][shell_ref]
        qs = np.array((.002, -.004, .001, .003, -.002, .005))
        qb = np.r_[qs[:3]+np.cross(qs[3:], arm), qs[3:]]
        be = np.zeros(6)
        if station == 2000:
            be[1 if load == "fy" else 3] = 1000. if load == "fy" else 100.
        se = be+np.r_[np.zeros(3), np.cross(arm, be[:3])]
        bw = np.array((0., 700., 0., 12., 0., 0.))
        sw = se-bw-np.r_[np.zeros(3), np.cross(arm, bw[:3])]
        actions = {f"ShellPort{station}": dict(wrench=sw, fitted_pose=qs),
                   f"BeamPort{station}": dict(wrench=bw, fitted_pose=qb)}
        good = station_contract(model, actions, station)
        np.testing.assert_allclose(good["gap_m_rad"], 0., atol=1e-15)
        np.testing.assert_allclose(good["residual_n_nm"], 0., atol=1e-13)
        assert abs(good["signed_internal_minus_external_work_j"]) < 1e-13
        actions[f"ShellPort{station}"]["wrench"] = sw+np.r_[
            np.zeros(3), 2*np.cross(arm, bw[:3])]
        bad = station_contract(model, actions, station)
        assert abs(bad["residual_n_nm"][3]) == pytest.approx(140.)
        actions[f"ShellPort{station}"]["wrench"] = sw
        actions[f"BeamPort{station}"]["fitted_pose"] = qb+np.array((0., .001, 0., 0., 0., 0.))
        assert station_contract(model, actions, station)["gap_m_rad"][1] == pytest.approx(.001)


def test_rigid_individual_patches_can_still_violate_connection(tmp_path):
    path = tmp_path/"model.inp"
    path.write_text(build(1, "fy")[0], encoding="ascii")
    model = read_deck(path)
    physical = {int(n) for conn in model["elements"].values() for n in conn.ravel()}
    vectors = {n: np.zeros(3) for n in physical}
    for node in model["sets"]["BeamPort1000"]:
        vectors[node] = np.array((0., .001, 0.))
    report = recover_from_displacements(model, vectors)
    assert max(abs(value["work_discrepancy_j"]) for value in report["ports"].values()) < 1e-8
    assert report["stations"]["1000"]["gap_m_rad"][1] == pytest.approx(.001)
    assert abs(report["stations"]["1000"]["signed_internal_minus_external_work_j"]) > 1e-5


def test_port_reader_rejects_truncated_and_overlapping_support(tmp_path):
    deck = build(1, "mx")[0]
    path = tmp_path/"model.inp"
    path.write_text(deck.replace("*RIGID BODY,NSET=BeamPort2000,", "*RIGID BODY,NSET=BadPort,"),
                    encoding="ascii")
    with pytest.raises(ValueError, match="missing E01 port"):
        read_deck(path)
    path.write_text(deck.replace("*NSET,NSET=PlateRootFree\n",
                                 "*NSET,NSET=PlateRootFree\n1\n"), encoding="ascii")
    with pytest.raises(ValueError, match="overlaps rigid"):
        read_deck(path)


def test_saved_recovery_requires_exact_deck_and_matching_displacement_stem(tmp_path):
    output = tmp_path/"references"
    generate(output)
    deck = output/"e01-resolved-plus-fy.inp"
    frd = output/"wrong.frd"
    manifest = output/"manifest.json"
    with pytest.raises(ValueError, match="does not match deck stem"):
        recover(deck, frd, manifest)
    deck.write_text(deck.read_text(encoding="ascii")+"\n", encoding="ascii")
    with pytest.raises(ValueError, match="differs from saved"):
        recover(deck, frd, manifest)

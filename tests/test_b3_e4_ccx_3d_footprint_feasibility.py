"""Headless structural checks; no CalculiX executable is launched."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import generate_b3_e4_ccx_3d_footprint_feasibility as probe  # noqa: E402


@pytest.mark.parametrize("sign", [-1, 1])
@pytest.mark.parametrize("load", list(probe.LOADS))
def test_six_decks_have_unique_dependent_translations_and_sections(sign, load):
    deck = probe.build_deck(sign, load)
    inventory = probe.validate_deck(deck, sign, load)
    assert inventory["equations"] == 12
    assert inventory["dependent_shell_translations"] == 12
    assert "*ELEMENT,TYPE=S4,ELSET=Panel" in deck
    assert "*ELEMENT,TYPE=B31,ELSET=Beam" in deck
    assert "SECTION=RECT" in deck
    assert "*USER ELEMENT" not in deck
    assert "*STEP\n*STATIC\n*CLOAD" in deck


def test_validator_rejects_wrong_eccentric_lever_arm_and_repeated_pivot():
    deck = probe.build_deck(1, "force_z")
    row = probe.footprint_rows(1)[0]
    original = ",".join(f"{n},{d},{probe._number(c)}" for n, d, c in row)
    with pytest.raises(ValueError, match="lever-arm"):
        probe.validate_deck(deck.replace(original, original.replace("47,5,0.10000000000000001",
                                                               "47,5,0.2")), 1, "force_z")
    # A second equation cannot eliminate the first shell coordinate again.
    lines = deck.splitlines()
    first, second = [i for i, line in enumerate(lines) if line == "*EQUATION"][:2]
    values = lines[second+2].split(",")
    values[:2] = lines[first+2].split(",")[:2]
    lines[second+2] = ",".join(values)
    with pytest.raises(ValueError, match="pivots"):
        probe.validate_deck("\n".join(lines)+"\n", 1, "force_z")


@pytest.mark.parametrize("sign", [-1, 1])
def test_virtual_work_force_and_moment_balance_with_signed_eccentricity(sign):
    forces = ((3., -7., 11.), (-5., 13., 17.), (19., 23., -29.),
              (31., -37., 41.))
    translation = (2., -3., 5.)
    rotation = (-.02, .03, .04)
    beam_position = (.5, 0., sign*probe.ECCENTRICITY)
    shell_displacements = []
    for x, y in probe.SAMPLES:
        r = (x-.5, y, -sign*probe.ECCENTRICITY)
        shell_displacements.append(probe._add(translation, probe._cross(rotation, r)))
    audit = probe.audit_virtual_work(sign, forces, translation, rotation,
                                     shell_displacements)
    assert audit["interface_work"] == pytest.approx(0., abs=1e-12)
    shell_force = tuple(sum(f[i] for f in forces) for i in range(3))
    shell_moment_origin = (0., 0., 0.)
    for (x, y), force in zip(probe.SAMPLES, forces):
        shell_moment_origin = probe._add(shell_moment_origin,
                                         probe._cross((x, y, 0.), force))
    beam_moment_origin = probe._add(audit["beam_moment"],
                                    probe._cross(beam_position, audit["beam_force"]))
    assert probe._add(shell_force, audit["beam_force"]) == pytest.approx((0.,)*3)
    assert probe._add(shell_moment_origin, beam_moment_origin) == pytest.approx(
        (0.,)*3, abs=1e-12)
    # Derive the multiplier work a second way, from the actual deck rows.
    deck = probe.build_deck(sign, "force_y")
    lines = deck.splitlines()
    equation_lines = [lines[i+2] for i, line in enumerate(lines) if line == "*EQUATION"]
    row_work = 0.
    for sample_index, force in enumerate(forces):
        for component, multiplier in enumerate(force):
            terms = equation_lines[3*sample_index+component].split(",")
            gap = 0.
            for j in range(0, len(terms), 3):
                node, dof, coefficient = int(terms[j]), int(terms[j+1]), float(terms[j+2])
                value = (shell_displacements[sample_index][dof-1] if node <= 45
                         else translation[dof-1] if dof <= 3 else rotation[dof-4])
                gap += coefficient*value
            row_work += multiplier*gap
    assert row_work == pytest.approx(audit["interface_work"], abs=1e-12)


def test_offset_reverses_transverse_force_lever_arm_but_not_unit_couple():
    forces = ((0., 100., 0.), (0., 0., 0.), (0., 0., 0.), (0., 0., 0.))
    audits = [probe.audit_virtual_work(sign, forces, (0.,)*3, (0.,)*3,
                                       ((0.,)*3,)*4) for sign in (-1, 1)]
    assert audits[0]["beam_moment"][0] == pytest.approx(-audits[1]["beam_moment"][0])
    assert abs(audits[0]["beam_moment"][0]) == pytest.approx(10.)
    minus = probe.applied_wrench(-1, "force_y")
    plus = probe.applied_wrench(1, "force_y")
    assert minus["applied_moment_about_origin"][0] == pytest.approx(100.)
    assert plus["applied_moment_about_origin"][0] == pytest.approx(-100.)
    assert minus["required_total_support_moment_about_origin"] == pytest.approx(
        tuple(-v for v in minus["applied_moment_about_origin"]))
    for axis in (0, 2):
        shell_forces = probe.torque_couple(axis)
        audit = probe.audit_virtual_work(1, shell_forces, (0.,)*3, (0.,)*3,
                                         ((0.,)*3,)*4)
        assert audit["beam_force"] == pytest.approx((0.,)*3)
        assert audit["beam_moment"] == pytest.approx(
            tuple(-1. if i == axis else 0. for i in range(3)))


def test_cli_writes_lf_decks_once_without_solver(tmp_path, monkeypatch, capsys):
    target = tmp_path / "inert_decks"
    monkeypatch.setattr(sys, "argv", ["generator", "--out-dir", str(target)])
    assert probe.main() == 0
    capsys.readouterr()
    manifest = json.loads((target / "manifest.json").read_text(encoding="ascii"))
    assert manifest["solver_executed"] is False
    assert len(manifest["cases"]) == 8
    for name, record in manifest["cases"].items():
        raw = (target / f"{name}.inp").read_bytes()
        assert b"\r" not in raw
        assert hashlib.sha256(raw).hexdigest() == record["deck_sha256"]
    with pytest.raises(FileExistsError):
        probe.main()

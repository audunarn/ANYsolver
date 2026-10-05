"""Physical inventory checks for the exploratory S4/U1 centerline deck."""

import numpy as np
import pytest

from scripts.probe_b3_e4_f03_ccx_s4_u1_centerline import _timeout_text, deck
from scripts.b3_e4_f03_weak_line_resolution_screen import one_case


@pytest.mark.parametrize("n_s,n_y,n_beam", [(2, 2, 4), (4, 4, 8), (8, 8, 16)])
def test_six_channel_rows_preserve_all_rigid_motions(n_s, n_y, n_beam):
    content, model, rows = deck(n_s, n_y, n_beam, "torsion")
    node_lines = content.split("*NODE,NSET=AllNodes\n", 1)[1].split(
        "*ELEMENT", 1)[0].splitlines()
    positions = {int(fields[0]): np.array([float(v) for v in fields[1:]])
                 for line in node_lines if (fields := line.split(","))}
    assert len(rows) == 6*n_beam+1 == model["equations"]
    assert len({(row[0][0], row[0][1]) for row in rows}) == len(rows)
    for translation, rotation in (
        (np.array([1.2, -.3, .7]), np.zeros(3)),
        (np.zeros(3), np.array([.2, -.4, .6])),
    ):
        def field(node, dof):
            value = np.r_[translation+np.cross(rotation, positions[node]), rotation]
            return value[dof-1]
        for row in rows[:-1]:
            value = sum(coefficient*field(node, dof)
                        for node, dof, coefficient in row)
            assert abs(value) < 2e-12


def test_load_and_section_are_declared_in_both_decks():
    for kind, dof, magnitude in (("torsion", 4, 100.),
                                  ("transverse_force_z", 3, 1000.)):
        content, model, _ = deck(2, 2, 4, kind)
        assert model["load_application"] in (
            "independent_beam_tip_rx", "independent_shell_tip_trace_transpose")
        load_lines = content.split("*CLOAD\n", 1)[1].split("*NODE PRINT", 1)[0]
        terms = [line.split(",") for line in load_lines.splitlines()]
        if kind == "torsion":
            assert terms == [[str(model["tip_node"]), "4", "100"]]
        else:
            assert all(int(node) != model["tip_node"] and int(axis) == dof
                       for node, axis, _ in terms)
        assert sum(float(value) for _, _, value in terms) == pytest.approx(magnitude)
        assert "PanelLeft,1,6" in content
        assert "*BEAM SECTION,ELSET=Beam,MATERIAL=Steel,SECTION=RECT" in content
        assert ".1,.1" in content
        u1, _, _ = deck(2, 2, 4, kind, "U1")
        assert ".01,8.333333333333333e-6,0.,8.333333333333333e-6,.8" in u1


def test_shell_force_couple_has_100_nm_and_native_balance():
    content, model, _ = deck(2, 2, 4, "shell_force_couple_x")
    node_lines = content.split("*NODE,NSET=AllNodes\n", 1)[1].split(
        "*ELEMENT", 1)[0].splitlines()
    positions = {int(fields[0]): np.array([float(v) for v in fields[1:]])
                 for line in node_lines if (fields := line.split(","))}
    load_lines = content.split("*CLOAD\n", 1)[1].split("*NODE PRINT", 1)[0]
    loads = [(int(node), int(axis), float(value))
             for node, axis, value in (line.split(",") for line in load_lines.splitlines())]
    assert model["load_application"] == "four_sample_shell_transverse_force_couple"
    assert all(axis == 3 for _, axis, _ in loads)
    assert sum(value for _, _, value in loads) == pytest.approx(0., abs=1e-10)
    assert sum(positions[node][1]*value for node, _, value in loads) == pytest.approx(100.)
    native = one_case("Q4", 4, "piecewise_constant",
                      shell_port="local_translation",
                      load_kind="shell_force_couple_x", n_s=2, n_y=2,
                      native_half_cells=4,
                      shell_support_policy="full_left_edge")
    assert native["applied_torque_x_n_m"] == pytest.approx(100.)
    assert abs(native["global_torque_x_balance_n_m"]) < 1e-8
    assert abs(native["global_force_z_balance_n"]) < 1e-8


def test_timeout_output_preserves_text_and_bytes():
    assert _timeout_text("partial output") == "partial output"
    assert _timeout_text(b"partial output") == "partial output"
    assert _timeout_text(None) == ""

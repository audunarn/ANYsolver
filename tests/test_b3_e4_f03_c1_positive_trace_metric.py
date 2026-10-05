"""Focused checks for the unqualified fixed C1 positive trace metric."""

import numpy as np
import pytest

from scripts._b3_e4_f03_native_fixture import G, SECTION_DIAGONAL, build
from scripts.b3_e4_f03_c1_positive_trace_metric import (
    LENGTH_M, RATIO_EXTREMES, _active_beam_trace, _beam_action,
    _fixture_contract, evaluate,
)
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def test_constant_lateral_bond_trace_has_declared_section_norm():
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    active, feature, report = _active_beam_trace(beam)
    step = np.zeros(beam.context.count)
    for node, x in enumerate(beam.abscissae):
        if x >= .9 - 1e-12:
            step[6*node+1] = 1.
    scaled_step = step[active]/report["scale"]
    measured = float(np.linalg.norm(feature @ scaled_step)**2)
    expected = SECTION_DIAGONAL[1]/LENGTH_M
    assert measured == pytest.approx(expected, rel=1e-12)
    assert report["trace_rank"] == 15
    assert report["section_weights_N_and_Nm2"][3] == pytest.approx(
        G*square_torsion_constant())
    assert report["section_weights_N_and_Nm2"][3] != SECTION_DIAGONAL[3]

    # An action on an unobserved retained coordinate cannot be assigned a
    # broken-trace dual norm; the diagnostic must refuse it.
    rows = np.zeros((1, beam.context.count))
    rows[0, beam.context.count-1] = 1.
    with pytest.raises(ArithmeticError, match="outside broken B3 trace"):
        _beam_action(rows, active, feature, report)


def test_fixed_c1_positive_modes_are_work_conjugate():
    result = evaluate()
    assert result["shell_metric"]["drilling_columns_max"] == 0.
    assert result["shell_metric"]["min_eigenvalue"] > 0.
    assert result["beam_trace_metric"]["trace_rank"] == 15
    assert [case["supported_row_rank"] for case in result["cases"]] == [12, 18, 18]
    for case in result["cases"]:
        assert case["beam_trace_kernel_relative_action"] < 1e-10
        assert case["dual_gram_upper_lower_ratio"] < 1.000001
        for name in ("full", "nonaxial"):
            mode = case[name]
            lower = mode["quotient_lower_bound_from_upper_dual_gram"]
            upper = mode["quotient_upper_bound_from_lower_dual_gram"]
            assert lower > 0.
            assert upper >= lower - 1e-11
            assert mode["moment_density_conversion_m"] == LENGTH_M
            assert mode["shell_positive_action"] > 0.
            assert mode["beam_positive_action"] > 0.
            assert (mode["shell_positive_action"]+
                    mode["beam_positive_action"] == pytest.approx(
                        lower, rel=1e-10))
            assert len(mode["beam_broken_trace"]) == 2


def test_registered_extreme_fixtures_preserve_broken_trace_norm():
    for _, shell_x, shell_y, beam_half in RATIO_EXTREMES:
        xs, ys = local_grid(shell_x, transverse_cells=shell_y)
        beam = build(beam_half, z_offset=.0675,
                     torsion_constant=square_torsion_constant(),
                     reference_profile="c1_tangent_2um")
        contract = _fixture_contract(xs, ys, beam)
        active, feature, trace = _active_beam_trace(beam)
        expected_cells = 2 if beam_half == 12 else 16
        assert contract["beam_bond_half_cells"] == expected_cells
        assert len(trace["half_cells"]) == expected_cells
        assert trace["trace_rank"] == len(active) == 6*expected_cells+3
        assert contract["largest_dense_square_rows"] <= 1900
        step = np.zeros(beam.context.count)
        for node, x in enumerate(beam.abscissae):
            if x >= .9 - 1e-12:
                step[6*node+1] = 1.
        measured = float(np.linalg.norm(feature @
                                        (step[active]/trace["scale"]))**2)
        assert measured == pytest.approx(SECTION_DIAGONAL[1]/LENGTH_M,
                                         rel=1e-12)

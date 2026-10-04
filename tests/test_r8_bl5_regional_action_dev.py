"""Analytic saved-action controls; no constitutive or reference solver jobs."""
import copy
import hashlib
import json
import math
from fractions import Fraction as F

import pytest

from scripts import r8_bl5_regional_action_dev as action


def records(force=lambda x: 2., intrinsic=lambda x: 3., segments=4):
    result = []
    for i in range(segments):
        for sign in (-1, 1):
            x = (i+.5+sign/(2*math.sqrt(3)))/segments
            fy, mz = force(x), intrinsic(x)
            result.append(dict(x_m=x, measure_m=1/(2*segments),
                               beam_wrench_about_root_density=[0., fy, 0., 0., 0., mz+x*fy]))
    return result


def expected(coefficients, weight=(1,)):
    return float(action.integral(action.multiply(tuple(map(F, coefficients)), tuple(map(F, weight))),
                                 F(1, 4), F(3, 4)))


def test_constant_leverage_intrinsic_and_total_are_separate():
    data = records()
    before = copy.deepcopy(data)
    result = action.native_measures(data, tuple(F(i, 4) for i in range(5)))
    assert data == before
    for name, weight in (("unweighted", (1,)), ("smooth_unit_peak", action.PSI)):
        assert result[name]["leverage_Mz_Nm"] == pytest.approx(expected((0, 2), weight), abs=1e-14)
        assert result[name]["intrinsic_Mz_Nm"] == pytest.approx(expected((3,), weight), abs=1e-14)
        assert result[name]["total_about_root_Mz_Nm"] == pytest.approx(expected((3, 2), weight), abs=1e-14)


def test_affine_fields_require_quadratic_root_torque_and_exact_weighted_integration():
    result = action.native_measures(records(lambda x: 2+4*x, lambda x: 3-2*x))
    for name, weight in (("unweighted", (1,)), ("smooth_unit_peak", action.PSI)):
        assert result[name]["leverage_Mz_Nm"] == pytest.approx(expected((0, 2, 4), weight), abs=1e-13)
        assert result[name]["intrinsic_Mz_Nm"] == pytest.approx(expected((3, -2), weight), abs=1e-13)
        assert result[name]["total_about_root_Mz_Nm"] == pytest.approx(expected((3, 0, 4), weight), abs=1e-13)


def test_released_spin_is_not_inferred_from_small_total_moment():
    result = action.native_measures(records(lambda x: 2., lambda x: -2*x))
    assert result["unweighted"]["total_about_root_Mz_Nm"] == pytest.approx(0., abs=1e-14)
    assert result["unweighted"]["leverage_Mz_Nm"] == pytest.approx(.5)
    assert result["unweighted"]["intrinsic_Mz_Nm"] == pytest.approx(-.5)


def test_polynomial_window_is_exact_unit_peak_with_zero_endpoints():
    evaluate = lambda x: sum(F(c)*x**i for i, c in enumerate(action.PSI))
    assert evaluate(F(1, 4)) == evaluate(F(3, 4)) == 0
    assert evaluate(F(1, 2)) == 1
    assert action.integral(tuple(map(F, action.PSI)), F(1, 4), F(3, 4)) == F(4, 15)


@pytest.mark.parametrize("mutation", (
    lambda rows: rows.pop(),
    lambda rows: rows[0].update(measure_m=-1.),
    lambda rows: rows[0].update(measure_m=.2),
    lambda rows: rows[1].update(x_m=rows[0]["x_m"]),
    lambda rows: rows[0].update(x_m=float("nan")),
    lambda rows: rows[0].update(beam_wrench_about_root_density=[0., float("inf"), 0., 0., 0., 0.]),
    lambda rows: rows[0].update(beam_wrench_about_root_density=[0.]*5),
    lambda rows: rows[0].update(x_m=True),
    lambda rows: rows.__setitem__(slice(0, 2), rows[2:4]),
))
def test_malformed_or_nonfinite_segments_are_rejected(mutation):
    rows = records()
    mutation(rows)
    with pytest.raises(ValueError):
        action.native_measures(rows)


def test_segment_endpoints_cannot_be_changed_to_clip_bad_geometry():
    with pytest.raises(ValueError, match="trace geometry"):
        action.native_measures(records(), (F(0), F(1, 5), F(1, 2), F(3, 4), F(1)))


@pytest.mark.parametrize("text", ('{"x":NaN}', '{"x":1e999}', '{"x":1,"x":2}', '[]'))
def test_bound_json_rejects_nonfinite_duplicate_or_nonobject_data(tmp_path, text):
    path = tmp_path/"saved.json"
    raw = text.encode()
    path.write_bytes(raw)
    with pytest.raises(ValueError):
        action.read_bound(path, hashlib.sha256(raw).hexdigest())


def test_bound_json_owns_parse_and_rejects_wrong_hash(tmp_path):
    path = tmp_path/"saved.json"
    raw = json.dumps({"values": [1, 2]}).encode()
    path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    first = action.read_bound(path, digest)
    first["values"][0] = 99
    assert action.read_bound(path, digest)["values"] == [1, 2]
    with pytest.raises(ValueError, match="SHA256 differs"):
        action.read_bound(path, "0"*64)


def test_external_measure_is_retained_and_intrinsic_spin_not_manufactured():
    supports = []
    for i in range(2):
        supports.append(dict(beam_pieces=[dict(interval_m=[i/2, (i+1)/2],
                                              xi_halfcell_mean_rational="0")]))
    inputs = dict(model=dict(support_count=2), basis="discontinuous_p1_cell_average", supports=supports)
    # External lambda_y=-2 means beam-exerted Fy=+2.
    lam = [0., 0., -2., 0., 0., 0., 0., 0., 0., 0.]*2
    unweighted, smooth = expected((0, 2)), expected((0, 2), action.PSI)
    data = dict(basis=inputs["basis"], row_density_multipliers=lam,
                sign_provenance="+Cphysical.T lambda resisting; -Cphysical.T lambda exerted; ground=(G+Cphysical.T lambda-L) on prescribed DOFs. Raw nodeReaction unused.",
                continuous_density_measures=dict(fixed_region_025_075=dict(
                    closed=[0.]*5+[unweighted], open=[0.]*5+[unweighted],
                    smooth_unit_peak=[0.]*5+[smooth], endpoint_atoms=[0.]*6)))
    before = copy.deepcopy(data)
    result = action.external_measures(data, inputs)
    assert data == before
    assert result["unweighted"]["total_about_root_Mz_Nm"] == unweighted
    assert result["smooth_unit_peak"]["total_about_root_Mz_Nm"] == smooth
    assert result["unweighted"]["intrinsic_Mz_Nm"] == 0.
    data["continuous_density_measures"]["fixed_region_025_075"]["smooth_unit_peak"][5] += 1.
    with pytest.raises(ValueError, match="retained external"):
        action.external_measures(data, inputs)


def test_saved_comparison_requires_all_explicit_bindings_before_reading():
    with pytest.raises(ValueError, match="complete explicit"):
        action.compare_saved("unused", {})


def external_inputs(count=2):
    shell = {str(65*j+i+1): [i/64, .2*j/16, 0.] for j in range(17) for i in range(65)}
    beam = {str(100001+i): [i/16, 0., .0675] for i in range(17)}
    fixes = {str(65*j+1): [1]*6 for j in range(17)} | {"100001": [1, 1, 1, 1, 1, 0]}
    span = 16//count
    supports = [dict(support_id=i, basis="discontinuous_p1_cell_average",
                     interval_m=[i/count, (i+1)/count], beam_pieces=[dict(
                         interval_m=[(i*span+j)/16, (i*span+j+1)/16],
                         xi_halfcell_mean_rational=str(F(2*j+1-span, span)),
                         xi_halfcell_mean=float(F(2*j+1-span, span))) for j in range(span)])
                for i in range(count)]
    return dict(basis="discontinuous_p1_cell_average", load=[0., 0., 0., 0., 0., 10.],
                model=dict(nx=64, ny=16, beam_intervals=16, support_count=count,
                           moment_origin_m=[0., 0., .0675], beam_root=100001, beam_tip=100017,
                           beam_node_ids=list(range(100001, 100018)), shell_node_ids=list(range(1, 1106)),
                           nodes=shell | beam, fixes=copy.deepcopy(fixes)),
                expected_inventory=dict(loads={"100017": [0., 0., 0., 0., 0., 10.]}, fixes=fixes),
                sections=dict(E_PA=210e9, NU=.3, G_PA=80769230769.23077, SHELL_THICKNESS_M=.035,
                              BEAM_AREA_M2=.01, BEAM_TORSION_M4=1.6666666666666667e-5,
                              BEAM_BENDING_M4=8.333333333333334e-6, BEAM_SHEAR_AREA_M2=.008), supports=supports)


@pytest.mark.parametrize("mutation", (
    lambda data: data["load"].__setitem__(5, 1.),
    lambda data: data["load"].__setitem__(0, False),
    lambda data: data["model"]["nodes"]["100001"].__setitem__(1, .01),
    lambda data: data["model"]["fixes"]["100001"].__setitem__(5, 1),
    lambda data: data["supports"][0]["beam_pieces"][0].update(xi_halfcell_mean_rational="-1"),
    lambda data: data["sections"].update(SHELL_THICKNESS_M=.04),
))
def test_matched_inputs_reject_load_geometry_ground_density_or_section_changes(mutation):
    data = external_inputs()
    action.validate_external_inputs(data, 2)
    mutation(data)
    with pytest.raises(ValueError):
        action.validate_external_inputs(data, 2)

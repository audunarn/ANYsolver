"""Saved Ns64/h16 BL5 regional-action discriminator; no solver imports or jobs.

Exact polynomial integration applies to the recovered two-Gauss affine fields,
not to an unknown continuous solution. No norm, acceptance threshold, point law,
released-spin convention, or qualification authority is changed.
"""
from __future__ import annotations

import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path


IDENTITY = "BL5_SAVED_REGIONAL_LATERAL_ACTION_DEV_V1"
REGION = (F(1, 4), F(3, 4))
PSI = (9, -96, 352, -512, 256)
BASE = ".qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1"
INPUTS = {
    "native_inputs": "envelope/owners/ns64_b1_8/owner-v1/native/inputs.json",
    "native_s4": "envelope/owners/ns64_b1_8/owner-v1/native/mz/physical-actions.json",
    "native_s2": "density-control/control-v1.json",
    "control_prepared": "density-control/prepared-v1.json",
    "external_s4_inputs": "density-reference/s4-v1/inputs.json",
    "external_s2_inputs": "density-reference/s2-v1/inputs.json",
    "external_s4": "density-reference/s4-v1/recovered-actions.json",
    "external_s2": "density-reference/s2-v1/recovered-actions.json",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    require(type(value) in (int, float) and math.isfinite(value), "finite numeric input required")
    return F(value)


def vector(value, size):
    require(type(value) is list and len(value) == size, "complete numeric vector required")
    return tuple(number(v) for v in value)


def _finite_tree(value):
    if type(value) is float:
        number(value)
    elif type(value) is list:
        for v in value:
            _finite_tree(v)
    elif type(value) is dict:
        for v in value.values():
            _finite_tree(v)


def _object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def read_bound(path, expected_sha256):
    """Decode the same owned bytes that were hashed; reject ambiguous JSON."""
    require(type(expected_sha256) is str and len(expected_sha256) == 64 and
            all(c in "0123456789abcdef" for c in expected_sha256), "explicit SHA256 required")
    raw = Path(path).read_bytes()
    require(len(raw) <= 16 * 1024**2, "bounded saved JSON input required")
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == expected_sha256, "saved input SHA256 differs: " + str(path))
    def reject_constant(value):
        raise ValueError("nonfinite JSON constant: " + value)
    result = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                        parse_constant=reject_constant)
    require(type(result) is dict, "saved JSON object required")
    _finite_tree(result)
    return result


def multiply(one, two):
    result = [F(0)] * (len(one) + len(two) - 1)
    for i, a in enumerate(one):
        for j, b in enumerate(two):
            result[i+j] += a*b
    return tuple(result)


def integral(coefficients, left, right):
    return sum((c*(right**(i+1)-left**(i+1))/(i+1)
                for i, c in enumerate(coefficients)), F(0))


def _affine(x1, x2, y1, y2):
    slope = (y2-y1)/(x2-x1)
    return y1-x1*slope, slope


def _measure(segments):
    terms = {name: {part: F(0) for part in ("leverage_Mz_Nm", "intrinsic_Mz_Nm")}
             for name in ("unweighted", "smooth_unit_peak")}
    for left, right, force, intrinsic in segments:
        a, b = max(left, REGION[0]), min(right, REGION[1])
        if b <= a:
            continue
        leverage = (F(0), *force)
        for name, weight in (("unweighted", (F(1),)), ("smooth_unit_peak", PSI)):
            terms[name]["leverage_Mz_Nm"] += integral(multiply(leverage, weight), a, b)
            terms[name]["intrinsic_Mz_Nm"] += integral(multiply(intrinsic, weight), a, b)
    result = {}
    for name, parts in terms.items():
        result[name] = {key: float(value) for key, value in parts.items()}
        result[name]["total_about_root_Mz_Nm"] = float(sum(parts.values(), F(0)))
    _finite_tree(result)
    return result


def native_measures(records, endpoints=None):
    """Integrate affine force/couple from consecutive existing two-Gauss pairs.

    Fixed caller supplies exact trace endpoints from the admitted geometry.
    Otherwise endpoints use the unchanged exact_transfer_moments inference.
    Inference/geometry agreement is checked before any window clipping.
    """
    require(type(records) is list and len(records) > 0 and len(records) % 2 == 0,
            "complete two-Gauss segment records required")
    count = len(records)//2
    if endpoints is not None:
        require(len(endpoints) == count+1, "complete segment endpoints required")
        endpoints = tuple(F(v) for v in endpoints)
    segments = []
    previous = 0.
    for index in range(count):
        pair = records[2*index:2*index+2]
        require(all(type(row) is dict for row in pair), "station objects required")
        pair = sorted(pair, key=lambda row: number(row["x_m"]))
        one, two = pair
        x1, x2 = number(one["x_m"]), number(two["x_m"])
        require(x2 > x1, "distinct ordered Gauss stations required")
        m1, m2 = number(one["measure_m"]), number(two["measure_m"])
        width = float(x2-x1)*math.sqrt(3.)
        left, right = (float(x1+x2)-width)/2, (float(x1+x2)+width)/2
        require(m1 > 0 and m2 > 0 and math.isclose(float(m1), width/2, rel_tol=1e-12, abs_tol=1e-14)
                and math.isclose(float(m2), width/2, rel_tol=1e-12, abs_tol=1e-14),
                "physical two-Gauss segment measures required")
        require(math.isclose(left, previous, rel_tol=0., abs_tol=1e-13),
                "ordered complete nonoverlapping segment coverage required")
        previous = right
        if endpoints is not None:
            a, b = endpoints[index:index+2]
            require(b > a and math.isclose(left, float(a), rel_tol=0., abs_tol=1e-13)
                    and math.isclose(right, float(b), rel_tol=0., abs_tol=1e-13),
                    "Gauss segment differs from admitted trace geometry")
        else:
            a, b = F(left), F(right)
        w1, w2 = (vector(row["beam_wrench_about_root_density"], 6) for row in pair)
        # Same root-axis decomposition as exact_transfer_moments; no spin removal.
        force = _affine(x1, x2, w1[1], w2[1])
        intrinsic = _affine(x1, x2, w1[5]-x1*w1[1], w2[5]-x2*w2[1])
        segments.append((a, b, force, intrinsic))
    require(math.isclose(previous, 1., rel_tol=0., abs_tol=1e-13), "complete unit-line coverage required")
    return _measure(segments)


def _near(actual, expected, message):
    value = actual if type(actual) is F else number(actual)
    require(math.isclose(float(value), float(expected), rel_tol=1e-12, abs_tol=1e-13), message)


def _coordinates(actual, expected, message):
    require(type(actual) is list and len(actual) == len(expected), message)
    for row, target in zip(actual, expected):
        require(len(vector(row, len(target))) == len(target), message)
        for value, wanted in zip(row, target):
            _near(value, wanted, message)


def validate_native_inputs(data):
    require(data["fixture_case"] == "ns64_b1_8" and
            data["fixture"] == dict(nx=64, ny=16, halfcells=16, supports=4), "fixed native fixture required")
    policy = data["policy"]
    require(policy["basis"] == "discontinuous_p1_cell_average" and
            policy["continuous_law"] == "BL5 director bond; explicitly released normal spin" and
            policy["support_membership"] == [list(range(4*i, 4*i+4)) for i in range(4)] and
            policy["support_endpoints_m"] == [0., .25, .5, .75, 1.] and
            policy["shell_trace_segments"] == 64 and policy["beam_halfcells"] == 16,
            "original projected five-channel density law required")
    require(vector(data["loads"]["mz"], 6) == (F(0),)*5+(F(10),) and data["beam_tip"] == 117,
            "fixed tip Mz10Nm input required")
    shell = [[i/64, .2*j/16, 0.] for j in range(17) for i in range(65)]
    beam = [[i/16, 0., .0675] for i in range(17)]
    _coordinates(data["xyz_m"], shell+beam, "native unit plate/straight beam geometry differs")
    _coordinates(data["shell_definition"]["coordinates_m"], shell, "native shell geometry differs")
    _near(data["shell_definition"]["thickness_m"], .035, "native thickness differs")
    fixed = [["shell", 65*j+1, d] for j in range(17) for d in range(6)]
    fixed += [["beam", 101, d] for d in range(5)]
    require(data["layout"]["fixed_coordinates"] == fixed, "native root/released-spin support differs")
    require(len(data["beams"]) == 8, "complete native member inventory required")
    elastic = [210e9*.01, (210e9/2.6)*.008, (210e9/2.6)*.008,
               (210e9/2.6)*1.6666666666666667e-5, 1750000., 1750000.]
    for i, member in enumerate(data["beams"]):
        require(member["node_ids"] == [101+2*i, 102+2*i, 103+2*i], "native member nodes differ")
        _coordinates(member["reference"]["coordinates"], beam[2*i:2*i+3], "native beam reference differs")
        require(member["reference"]["nodal_triads"] == [[[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]]*3,
                "native reference frames differ")
        matrix = member["section"]["elastic"]
        require(len(matrix) == 6, "complete elastic section required")
        for r, row in enumerate(matrix):
            vector(row, 6)
            for c, value in enumerate(row):
                _near(value, elastic[r] if r == c else 0., "native physical section differs")
    supports = data["supports"]
    require(len(supports) == 4 and all(s["support_id"] == i and
            s["interval_m"] == [i/4, (i+1)/4] and
            s["native_halfcells"] == list(range(4*i, 4*i+4)) and len(s["multiplier_rows"]) == 10
            for i, s in enumerate(supports)), "complete native support inventory required")


def validate_external_inputs(data, count):
    model = data["model"]
    require(data["basis"] == "discontinuous_p1_cell_average" and
            (model["nx"], model["ny"], model["beam_intervals"], model["support_count"]) == (64, 16, 16, count),
            "matched external fixture/density required")
    require(vector(data["load"], 6) == (F(0),)*5+(F(10),) and
            model["moment_origin_m"] == [0., 0., .0675] and
            data["expected_inventory"]["loads"] == {str(model["beam_tip"]): data["load"]},
            "external beam-root sign/load convention differs")
    require(model["beam_root"] == 100001 and model["beam_tip"] == 100017 and
            model["beam_node_ids"] == list(range(100001, 100018)) and
            model["shell_node_ids"] == list(range(1, 1106)) and len(model["nodes"]) == 1122,
            "complete external physical nodes required")
    _coordinates([model["nodes"][str(n)] for n in model["shell_node_ids"]],
                 [[i/64, .2*j/16, 0.] for j in range(17) for i in range(65)], "external shell geometry differs")
    _coordinates([model["nodes"][str(n)] for n in model["beam_node_ids"]],
                 [[i/16, 0., .0675] for i in range(17)], "external beam geometry differs")
    fixed = {str(65*j+1): [1]*6 for j in range(17)} | {"100001": [1, 1, 1, 1, 1, 0]}
    require(model["fixes"] == fixed and data["expected_inventory"]["fixes"] == fixed,
            "external supports/released normal spin differ")
    expected = dict(E_PA=210e9, NU=.3, G_PA=80769230769.23077, SHELL_THICKNESS_M=.035,
                    BEAM_AREA_M2=.01, BEAM_TORSION_M4=1.6666666666666667e-5,
                    BEAM_BENDING_M4=8.333333333333334e-6, BEAM_SHEAR_AREA_M2=.008)
    require(set(data["sections"]) == set(expected), "complete external sections required")
    for key, value in expected.items():
        _near(data["sections"][key], value, "external physical section differs")
    supports = data["supports"]
    require(len(supports) == count, "complete external density supports required")
    span = 16//count
    for i, support in enumerate(supports):
        require(support["support_id"] == i and support["basis"] == data["basis"] and
                support["interval_m"] == [i/count, (i+1)/count] and
                len(support["beam_pieces"]) == span, "external support membership differs")
        for j, piece in enumerate(support["beam_pieces"]):
            cell = i*span+j
            require(piece["interval_m"] == [cell/16, (cell+1)/16] and
                    F(piece["xi_halfcell_mean_rational"]) == F(2*j+1-span, span),
                    "original h16 projected density means required")
            _near(piece["xi_halfcell_mean"], F(2*j+1-span, span), "external density mean differs")


def external_measures(data, inputs):
    """Return retained measures, with a separate physical-density decomposition."""
    count = inputs["model"]["support_count"]
    require(type(count) is int and count in (2, 4), "fixed S4 or S2 density required")
    require(data["basis"] == inputs["basis"] and
            data["sign_provenance"] == "+Cphysical.T lambda resisting; -Cphysical.T lambda exerted; ground=(G+Cphysical.T lambda-L) on prescribed DOFs. Raw nodeReaction unused.",
            "external exerted sign convention differs")
    lam = vector(data["row_density_multipliers"], 10*count)
    segments = []
    for i, support in enumerate(inputs["supports"]):
        for piece in support["beam_pieces"]:
            xi = F(piece["xi_halfcell_mean_rational"])
            # All five channel coefficients were validated; only lateral force
            # produces z torque for this reference straight released-spin law.
            fy = -lam[10*i+2]-lam[10*i+3]*xi
            left, right = map(number, piece["interval_m"])
            segments.append((left, right, (fy, F(0)), (F(0), F(0))))
    reconstructed = _measure(segments)
    retained = data["continuous_density_measures"]["fixed_region_025_075"]
    require(vector(retained["endpoint_atoms"], 6) == (F(0),)*6, "continuous density has unexpected endpoint atoms")
    result = {}
    for name, key in (("unweighted", "closed"), ("smooth_unit_peak", "smooth_unit_peak")):
        actual = float(vector(retained[key], 6)[5])
        _near(actual, reconstructed[name]["total_about_root_Mz_Nm"], "retained external regional measure differs")
        result[name] = dict(reconstructed[name], total_about_root_Mz_Nm=actual,
                           retained_minus_reconstructed_Nm=actual-reconstructed[name]["total_about_root_Mz_Nm"])
    require(vector(retained["open"], 6) == vector(retained["closed"], 6), "external window endpoint convention differs")
    return result


def compare_saved(repo_root, bindings):
    """Read only eight expressly hash-bound saved inputs; return an owned report.

    bindings maps the eight INPUTS keys to their expected SHA256 strings. Root
    owns manifest selection, supervision, writing this returned report and its
    scientific interpretation. There is no execution or default hash discovery.
    """
    require(type(bindings) is dict and set(bindings) == set(INPUTS), "complete explicit input bindings required")
    directory = Path(repo_root)/BASE
    records = {key: read_bound(directory/path, bindings[key]) for key, path in INPUTS.items()}
    validate_native_inputs(records["native_inputs"])
    for count in (4, 2):
        validate_external_inputs(records[f"external_s{count}_inputs"], count)
    parent, child, preparation = records["native_s4"], records["native_s2"], records["control_prepared"]
    require(parent["status"] == "completed" and
            child["status"] == "COMPLETED_SAVED_OPERATOR_CONTROL_DEVELOPMENT_ONLY" and
            child["predecessor_json_sha256"] == bindings["control_prepared"] and
            preparation["status"] == "PREPARED_DEVELOPMENT_CONTROL" and
            preparation["definition_change"] == "S4->S2 only, H4->H8 diagnostic" and
            (preparation["fine_rows"], preparation["child_rows"], preparation["order"], preparation["trace_count"])
            == (40, 20, 6924, 128) and preparation["load"] == "Mz10Nm",
            "completed saved S4/S2 control provenance required")
    parent_path = BASE+"/"+INPUTS["native_s4"]
    inputs_path = BASE+"/"+INPUTS["native_inputs"]
    require(all(row["inputs"][parent_path] == bindings["native_s4"] and
                row["inputs"][inputs_path] == bindings["native_inputs"]
                for row in (child, preparation)), "control parent physical actions/definition differ")
    endpoints = tuple(F(i, 64) for i in range(65))
    native = {}
    for count, rows in ((4, parent["physical_transfer"]["station_records"]), (2, child["station_records"])):
        require(len(rows) == 128, "all original native trace segments required")
        native[f"s{count}"] = native_measures(rows, endpoints)
        stored = parent["exact_region_wrench"] if count == 4 else child["exact_region_wrench"]
        _near(vector(stored, 6)[5], native[f"s{count}"]["unweighted"]["total_about_root_Mz_Nm"],
              "saved native unweighted regional measure differs")
    external = {f"s{count}": external_measures(records[f"external_s{count}"], records[f"external_s{count}_inputs"])
                for count in (4, 2)}
    difference = {label: {weight: {key: native[label][weight][key]-external[label][weight][key]
                  for key in ("leverage_Mz_Nm", "intrinsic_Mz_Nm", "total_about_root_Mz_Nm")}
                  for weight in ("unweighted", "smooth_unit_peak")} for label in ("s4", "s2")}
    report = dict(identity=IDENTITY, input_sha256=dict(bindings),
                input_paths={key: BASE+"/"+path for key, path in INPUTS.items()},
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                region_m=[.25, .75], smooth_polynomial=list(PSI), root_m=[0., 0., .0675],
                sign="beam-exerted; root-axis Mz=x*Fy+intrinsic Mz", native=native,
                external_retained=external, native_minus_external=difference,
                qualification=False, formal_f03_authority_consumed=False, solve_count=0,
                limitation="Saved recovered polynomial action only; no convergence, physical accuracy, torque/shear, norm or M2 acceptance. Native cell rotations are retained; BL5 normal spin remains released and the point law is unchanged.")
    _finite_tree(report)
    return report

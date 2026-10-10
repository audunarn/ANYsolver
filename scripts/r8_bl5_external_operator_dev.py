"""Fail-closed 16x4 BL5 external operator identity and saved-data feasibility check.

This source-only tool does not execute OpenSees. A future fresh capture must supply
the full physical K and augmented matrix with the declared DOF map; saved response
vectors alone do not identify either operator. No F03 or accuracy claim follows.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
FIXTURE = (HERE / "docs/agent_plans/development/r8-bl5-matched-comparison-20261001"
           / "refinement-v1-raw/external/n16")
SOURCE = (HERE / "docs/agent_plans/development/r8-bl5-matched-comparison-20261001"
          / "refinement-v1-raw/external/b3_e4_bl5_external_p0_refinement_dev.py")
CASES = ("fy", "mx", "mz")
ALPHA_SP = ALPHA_MP = 1e9
RESPONSE_RELATIVE_LIMIT = 1e-8
TRANSLATION_FLOOR_M = 1e-14
ROTATION_FLOOR_RAD = 1e-14
KKT_ZERO_BLOCK_ABSOLUTE_LIMIT = 1e-12
RHS_ABSOLUTE_LIMIT = 1e-12


class IdentityError(ValueError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise IdentityError(message)


def import_recipe():
    spec = importlib.util.spec_from_file_location("_bl5_external_recipe_identity", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fullgeneral_commands(recipe, model, reference, rows, case):
    frozen = recipe.command_recipe(model, reference, rows, case)
    changed = [(name, ("FullGeneral",) if name == "system" else args)
               for name, args in frozen]
    require(sum(name == "system" for name, _ in frozen) == 1 and
            next(args for name, args in frozen if name == "system") == ("BandGeneral",),
            "single frozen BandGeneral command required")
    require(sum(a != b for a, b in zip(frozen, changed)) == 1 and len(frozen) == len(changed),
            "FullGeneral must be the only command change")
    return changed


def fixture_preflight(folder: Path = FIXTURE) -> dict:
    """Check exact saved mechanics, load, poses and provenance without a solve."""
    recipe = import_recipe()
    p0, frozen, service, reference, paths = recipe.services()
    require(sha(SOURCE) == "0e5435e0d38952642662eb1aad7dd374c341c866c9d099c87d2e66ce135a21c0",
            "frozen refinement recipe changed")
    for path, expected in zip(paths, (recipe.P0_SOURCE_SHA, p0.FROZEN_SOURCE_SHA,
                                      p0.SERVICE_SHA, p0.REFERENCE_SHA)):
        require(sha(path) == expected, f"frozen helper changed: {path.name}")
    model = recipe.geometry(16, reference)
    rows, supports = recipe.aggregate_rows(model, reference, p0)
    capture_commands = fullgeneral_commands(recipe, model, reference, rows, "fy")
    dofs = [(int(node), dof) for node in model["physical_node_order"] for dof in range(1, 7)]
    fixed = [(int(node), dof) for node, flags in sorted(model["fixes"].items())
             for dof, flag in enumerate(flags, 1) if flag]
    require(len(dofs) == 708 and len(fixed) == 35 and len(rows) == 40,
            "16x4 physical/SP/MP dimensions changed")
    require(len(supports) == 8 and all(len(row) % 3 == 0 for row in rows),
            "five-channel P0 row inventory changed")
    captures = {}
    mechanics_hash = None
    for case in CASES:
        case_dir = folder / case
        summary = json.loads((case_dir / "summary.json").read_text())
        raw = json.loads((case_dir / "raw-inventory.json").read_text())
        require(summary.get("status") == "completed" and summary.get("case") == case,
                f"{case}: completed matching saved case required")
        require(summary.get("source_sha256") == sha(SOURCE), f"{case}: source identity absent/mismatch")
        require(summary.get("binary_sha256") == service.BINARY_SHA256,
                f"{case}: binary identity absent/mismatch")
        bound = {Path(path).name: value for path, value in summary.get("helper_sources", {}).items()}
        require(bound == {path.name: sha(path) for path in paths},
                f"{case}: helper identities absent/mismatch")
        planned = recipe.planned_inventory(recipe.command_recipe(model, reference, rows, case))
        case_mechanics = digest({key: planned[key] for key in
                                 ("nodes", "elements", "equations", "fixes", "model_commands")})
        if mechanics_hash is None:
            mechanics_hash = case_mechanics
        require(case_mechanics == mechanics_hash, "case mechanics differ")
        require(all(digest(raw.get(key)) == digest({str(k): v for k, v in expected.items()}
                    if isinstance(expected, dict) else expected)
                    for key, expected in planned.items()),
                f"{case}: saved assembly or mechanics differs from frozen recipe")
        require(set(map(int, raw.get("poses", {}))) == set(model["nodes"]),
                f"{case}: complete saved physical response required")
        require(all(len(q) == 6 and all(math.isfinite(float(x)) for x in q)
                    for q in raw["poses"].values()), f"{case}: invalid saved response")
        # Frozen Plain/Linear load pattern, one LoadControl(1) increment. Reject
        # a different time/load convention instead of fitting a candidate RHS.
        commands = recipe.command_recipe(model, reference, rows, case)
        require(("timeSeries", ("Linear", 1)) in commands and
                ("pattern", ("Plain", 1, 1)) in commands and
                ("integrator", ("LoadControl", 1.0)) in commands and
                ("analyze", (1,)) in commands,
                f"{case}: load factor 1 convention not established")
        load = [float(planned["loads"].get(node, (0.0,) * 6)[dof-1]) for node, dof in dofs]
        captures[case] = {"summary_sha256": sha(case_dir / "summary.json"),
                          "raw_sha256": sha(case_dir / "raw-inventory.json"),
                          "response_sha256": digest(raw["poses"]),
                          "load_factor": 1.0, "applied_load": load,
                          "displacement": [float(raw["poses"][str(node)][dof-1]) for node, dof in dofs]}
    return {"status": "source_preflight_passed", "dof_order": dofs,
            "ndf": 6,
            "fixed_dofs": fixed, "rows": rows, "physical_dimension": len(dofs),
            "sp_dimension": len(fixed), "mp_dimension": len(rows),
            "kkt_dimension": len(dofs) + len(fixed) + len(rows),
            "alpha_sp": ALPHA_SP, "alpha_mp": ALPHA_MP,
            "recipe_sha256": sha(SOURCE), "binary_sha256": service.BINARY_SHA256,
            "mechanics_sha256": mechanics_hash,
            "capture_commands_sha256": digest(capture_commands),
            "cases": captures}


def validate_fullgeneral_capture(spec: dict, capture: dict) -> dict:
    """Map an actual flattened FullGeneral KKT through nodeDOFs and match rows."""
    n, m = spec["physical_dimension"], spec["kkt_dimension"]
    require(capture.get("recipe_sha256") == spec["recipe_sha256"], "capture recipe identity mismatch")
    require(capture.get("binary_sha256") == spec["binary_sha256"], "capture binary identity mismatch")
    require(capture.get("capture_commands_sha256") == spec["capture_commands_sha256"],
            "capture command identity mismatch")
    require(capture.get("analyze_code") == 0 and capture.get("system_size") == m,
            "completed exact-size FullGeneral solve required")
    flat = capture.get("printA")
    require(isinstance(flat, list) and len(flat) == m*m and
            all(math.isfinite(float(v)) for v in flat), "complete finite flattened KKT required")
    matrix = [flat[i*m:(i+1)*m] for i in range(m)]
    node_dofs = capture.get("node_dofs", {})
    require(set(node_dofs) == {str(node) for node, _ in spec["dof_order"]},
            "every physical nodeDOFs result required")
    physical_ids = []
    for node, dof in spec["dof_order"]:
        ids = node_dofs[str(node)]
        require(isinstance(ids, list) and len(ids) == spec["ndf"],
                "complete equation IDs required per physical node")
        physical_ids.append(ids[dof-1])
    require(all(type(i) is int and 0 <= i < m for i in physical_ids) and
            len(set(physical_ids)) == n, "physical equation map incomplete or duplicated")
    other_ids = sorted(set(range(m)) - set(physical_ids))
    require(len(other_ids) == spec["sp_dimension"] + spec["mp_dimension"],
            "constraint equation count mismatch")
    k = [[matrix[i][j] for j in physical_ids] for i in physical_ids]
    k_scale = max(1.0, max(abs(v) for row in k for v in row))
    symmetry = max(abs(matrix[i][j]-matrix[j][i]) for i in range(m) for j in range(i))
    require(symmetry <= 1e-10*k_scale, "FullGeneral KKT asymmetric")
    fixed_idx = {spec["dof_order"].index(pair) for pair in spec["fixed_dofs"]}
    coupling = [(i, j, k[i][j]) for i in fixed_idx for j in range(n)
                if j not in fixed_idx and abs(k[i][j]) > 1e-9]
    require(coupling, "full physical fixed/free stiffness coupling absent")
    expected = constraint_rows(spec)
    require(len(expected) == len(other_ids), "SP/MP source row count mismatch")
    unmatched = set(range(len(expected)))
    matches = []
    for eq_id in other_ids:
        observed = {i: matrix[eq_id][physical_ids[i]] for i in range(n)
                    if abs(matrix[eq_id][physical_ids[i]]) > 1e-9}
        possibilities = []
        for row_id in unmatched:
            alpha = spec["alpha_sp"] if row_id < spec["sp_dimension"] else spec["alpha_mp"]
            # OpenSees equationConstraint solves for its declared dependent
            # coordinate: normalize the whole MP row by that first coefficient.
            # The saved FullGeneral row 78 exposes the 1/0.015625 factor of 64.
            if row_id < spec["sp_dimension"]:
                divisor = 1.0
            else:
                source_row = spec["rows"][row_id-spec["sp_dimension"]]
                divisor = float(source_row[2])
                require(math.isfinite(divisor) and divisor != 0.0,
                        "MP dependent coefficient required for normalization")
            target = {i: alpha*v/divisor for i, v in expected[row_id].items() if v != 0.0}
            if set(observed) != set(target):
                continue
            for sign in (1, -1):
                if all(abs(observed[i]-sign*v) <= max(1e-5, 1e-12*abs(v))
                       for i, v in target.items()):
                    possibilities.append((row_id, sign))
        require(len(possibilities) == 1, f"constraint equation {eq_id} has no unique source row")
        row_id, sign = possibilities[0]
        unmatched.remove(row_id)
        matches.append({"equation_id": eq_id, "kind": "SP" if row_id < spec["sp_dimension"] else "MP",
                        "source_row": row_id if row_id < spec["sp_dimension"] else row_id-spec["sp_dimension"],
                        "orientation": sign})
    require(not unmatched and all(abs(matrix[i][j]) <= KKT_ZERO_BLOCK_ABSOLUTE_LIMIT
                                  for i in other_ids for j in other_ids),
            "KKT multiplier block nonzero or rows unmatched")
    observed_poses = capture.get("poses", {})
    require(set(observed_poses) == set(node_dofs), "all captured poses required")
    case = capture.get("case")
    require(case in spec["cases"], "captured case unrecognized")
    saved = spec["cases"][case]
    displacement = [observed_poses[str(node)][dof-1] for node, dof in spec["dof_order"]]
    require(all(math.isfinite(float(v)) for v in displacement), "nonfinite physical response")
    scales = {kind: max((abs(u) for i, u in enumerate(saved["displacement"])
                         if (spec["dof_order"][i][1] <= 3) == (kind == "translation")), default=0.0)
              for kind in ("translation", "rotation")}
    pose_errors = [abs(v-u) for v, u in zip(displacement, saved["displacement"])]
    require(all(error <= max(TRANSLATION_FLOOR_M if spec["dof_order"][i][1] <= 3 else ROTATION_FLOOR_RAD,
                             RESPONSE_RELATIVE_LIMIT * scales["translation" if spec["dof_order"][i][1] <= 3
                                                              else "rotation"])
                for i, error in enumerate(pose_errors)), "FullGeneral physical response differs from saved BandGeneral")
    return {"status": "permuted_kkt_structure_and_pose_validated_development_only",
            "physical_dimension": n, "kkt_dimension": m,
            "physical_equation_ids_sha256": digest(physical_ids),
            "fixed_free_coupling_entries": len(coupling),
            "max_kkt_asymmetry": symmetry, "max_pose_difference": max(pose_errors),
            "constraint_equations": matches,
            "canonical_physical_K_sha256": digest(k)}


def validate_physical_force_assembly(k, displacement, element_force, dof_order,
                                     *, relative_limit=1e-8, force_floor=1e-8,
                                     moment_floor=1e-8) -> dict:
    """Check every physical Kq row, including fixed roots, in force/moment units."""
    n = len(dof_order)
    require(len(k) == n and all(len(row) == n for row in k) and
            len(displacement) == n and len(element_force) == n,
            "physical force assembly dimension mismatch")
    require(all(math.isfinite(float(value)) for row in k for value in row) and
            all(math.isfinite(float(value)) for value in displacement + element_force),
            "nonfinite physical force input")
    residual = [math.fsum(float(a)*float(b) for a, b in zip(row, displacement)) - float(g)
                for row, g in zip(k, element_force)]
    report = {}
    for kind, selected, floor in (("force_N", lambda dof: dof <= 3, force_floor),
                                  ("moment_Nm", lambda dof: dof > 3, moment_floor)):
        slots = [i for i, (_, dof) in enumerate(dof_order) if selected(dof)]
        peak = max((abs(residual[i]) for i in slots), default=0.0)
        scale = max((abs(element_force[i]) for i in slots), default=0.0)
        limit = max(floor, relative_limit*scale)
        require(peak <= limit, f"{kind} Kq differs from archived element force assembly")
        report[kind] = {"max_abs_residual": peak, "reference_scale": scale,
                        "limit": limit, "row_count": len(slots)}
    return report


def constraint_rows(spec: dict) -> list[dict[int, float]]:
    index = {tuple(pair): i for i, pair in enumerate(spec["dof_order"])}
    b = [{index[tuple(pair)]: 1.0} for pair in spec["fixed_dofs"]]
    for row in spec["rows"]:
        coeff: dict[int, float] = {}
        for n, dof, value in zip(row[::3], row[1::3], row[2::3]):
            key = (int(n), int(dof))
            require(key in index, "constraint references absent physical DOF")
            j = index[key]
            coeff[j] = coeff.get(j, 0.0) + float(value)
        require(coeff and any(v != 0.0 for v in coeff.values()), "zero constraint row")
        b.append(coeff)
    return b


def validate_capture(spec: dict, capture: dict, *, tolerance: float = 1e-8) -> dict:
    """Validate an actual full K/KKT bundle; metadata cannot substitute for entries."""
    n, m = spec["physical_dimension"], spec["kkt_dimension"]
    require(capture.get("recipe_sha256") == spec["recipe_sha256"], "capture source identity mismatch")
    require(capture.get("binary_sha256") == spec["binary_sha256"], "capture binary identity mismatch")
    require(capture.get("mechanics_sha256") == spec["mechanics_sha256"], "capture mechanics changed")
    require(capture.get("dof_order") == [list(pair) for pair in spec["dof_order"]],
            "physical DOF order mismatch")
    labels = [["SP", *pair] for pair in spec["fixed_dofs"]] + [["MP", i] for i in range(spec["mp_dimension"])]
    require(capture.get("constraint_order") == labels, "SP/MP multiplier order mismatch")
    require(capture.get("alpha_sp") == spec["alpha_sp"] and capture.get("alpha_mp") == spec["alpha_mp"],
            "constraint scaling mismatch")
    k, a = capture.get("K"), capture.get("KKT")
    require(isinstance(k, list) and len(k) == n and all(isinstance(r, list) and len(r) == n for r in k),
            "physical K dimension mismatch")
    require(isinstance(a, list) and len(a) == m and all(isinstance(r, list) and len(r) == m for r in a),
            "KKT dimension mismatch")
    require(all(math.isfinite(float(x)) for matrix in (k, a) for row in matrix for x in row),
            "nonfinite operator entry")
    scale = max(1.0, max(abs(float(x)) for row in k for x in row))
    allowed = tolerance * scale
    require(all(abs(k[i][j] - k[j][i]) <= allowed for i in range(n) for j in range(i)),
            "physical K asymmetric")
    require(all(abs(a[i][j] - k[i][j]) <= allowed for i in range(n) for j in range(n)),
            "KKT physical block differs from K")
    fixed_idx = {spec["dof_order"].index(pair) for pair in spec["fixed_dofs"]}
    require(any(abs(k[i][j]) > allowed for i in fixed_idx for j in range(n) if j not in fixed_idx),
            "fixed/free coupling missing")
    for r, coeff in enumerate(constraint_rows(spec)):
        alpha = spec["alpha_sp"] if r < spec["sp_dimension"] else spec["alpha_mp"]
        j = n + r
        for i in range(n):
            wanted = alpha * coeff.get(i, 0.0)
            require(abs(a[i][j] - wanted) <= tolerance * max(1.0, abs(wanted)) and
                    abs(a[j][i] - wanted) <= tolerance * max(1.0, abs(wanted)),
                    "KKT constraint sign/order/scaling mismatch")
        require(all(abs(a[j][q]) <= KKT_ZERO_BLOCK_ABSOLUTE_LIMIT for q in range(n, m)),
                "KKT constraint block must be zero")
    for case, expected in spec["cases"].items():
        observed = capture.get("responses", {}).get(case)
        require(isinstance(observed, dict), f"{case}: response absent")
        require(observed.get("saved_response_sha256") == expected["response_sha256"],
                f"{case}: saved response binding mismatch")
        x = observed.get("kkt_solution")
        rhs = observed.get("rhs")
        require(isinstance(x, list) and len(x) == m and isinstance(rhs, list) and len(rhs) == m,
                f"{case}: complete KKT response/RHS required")
        require(all(math.isfinite(float(v)) for v in x + rhs), f"{case}: nonfinite response")
        trans_scale = max((abs(u) for i, u in enumerate(expected["displacement"])
                           if spec["dof_order"][i][1] <= 3), default=0.0)
        rot_scale = max((abs(u) for i, u in enumerate(expected["displacement"])
                         if spec["dof_order"][i][1] > 3), default=0.0)
        require(all(abs(x[i] - u) <= max(TRANSLATION_FLOOR_M if spec["dof_order"][i][1] <= 3
                                         else ROTATION_FLOOR_RAD,
                                         RESPONSE_RELATIVE_LIMIT * (trans_scale if spec["dof_order"][i][1] <= 3
                                                                    else rot_scale))
                    for i, u in enumerate(expected["displacement"])),
                f"{case}: physical response mismatch")
        require(expected.get("load_factor") == 1.0 and
                isinstance(expected.get("applied_load"), list) and len(expected["applied_load"]) == n,
                f"{case}: frozen load convention absent")
        require(all(abs(rhs[i] - expected["applied_load"][i]) <=
                    RHS_ABSOLUTE_LIMIT * max(1.0, abs(expected["applied_load"][i])) for i in range(n))
                and all(abs(rhs[i]) <= RHS_ABSOLUTE_LIMIT for i in range(n, m)),
                f"{case}: RHS differs from frozen unit-factor load or zero constraints")
        require(all(abs(sum(a[i][j] * x[j] for j in range(m)) - rhs[i])
                    <= tolerance * max(1.0, abs(rhs[i])) for i in range(m)),
                f"{case}: KKT residual mismatch")
    return {"status": "capture_algebra_validated_development_only", "physical_dimension": n,
            "kkt_dimension": m, "cases": sorted(spec["cases"]), "tolerance": tolerance}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=FIXTURE)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    spec = fixture_preflight(args.fixture)
    result = {key: value for key, value in spec.items() if key not in ("dof_order", "fixed_dofs", "rows", "cases")}
    result["case_hashes"] = {
        case: {k: v for k, v in data.items() if k not in ("displacement", "applied_load")}
              | {"declared_load_sha256": digest(data["applied_load"])}
        for case, data in spec["cases"].items()}
    result["feasibility"] = ("Saved response/element-force inventories contain no global K, equation map, "
                             "or fixed/free stiffness block. For the first beam element, seven free physical "
                             "coordinates have at most three saved response vectors; a nonzero free direction "
                             "orthogonal to all three exists. Adding vv^T with any fixed-root component changes "
                             "fixed/free K but preserves all three saved responses. Fresh source/binary-bound "
                             "operator extraction is required before common-density inference.")
    if args.candidate:
        capture = json.loads(args.candidate.read_text())
        result["candidate"] = (validate_fullgeneral_capture(spec, capture)
                               if "printA" in capture else validate_capture(spec, capture))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    else:
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

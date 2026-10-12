"""Three prescribed external BL5 P0 reference levels, one case per process.

The family is 16x4/32x8/64x16 ASDShellQ4, 32/64/128 two-node Timoshenko
intervals, and 8/16/32 P0 supports (40/80/160 rows). Geometry, sections,
physical five-channel law, arms, frames and direct root grounds are fixed.
Cases are Fy100N, Mx10Nm, Mz10Nm. This prepares ordinary development reference
convergence evidence, not a converged accuracy oracle or formal F03 gate.
Use disjoint shell/beam IDs; never merge coordinates or copy native C rows.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import traceback


P0_SOURCE_SHA = "180e2c33d1df17239fbf30f66d9c6b400eebbfa9e5f961d83e7c9b68bdc5fdac"
LEVELS = (16, 32, 64)
BEAM_FIRST, BEAM_ELEMENT_FIRST = 100001, 100001
LOADS = {"fy": (0., 100., 0., 0., 0., 0.), "mx": (0., 0., 0., 10., 0., 0.),
         "mz": (0., 0., 0., 0., 0., 10.)}
BALANCE_LIMIT, GAP_LIMIT, DERIVATIVE_LIMIT = 1e-8, 1e-9, 1e-6
DERIVATIVE_STEPS = (1e-4, 3e-5, 1e-5)


class InputIdentityError(ValueError):
    pass


class InterfaceRecoveryError(RuntimeError):
    pass


class PhysicalPredicateError(RuntimeError):
    pass


def services():
    path = Path(__file__).with_name("b3_e4_bl5_external_p0_enforcement_dev.py")
    spec = importlib.util.spec_from_file_location("_external_p0_refinement_services", path)
    p0 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p0)
    frozen, service, reference, paths = p0.services()
    return p0, frozen, service, reference, (path, *paths)


def geometry(nx, reference):
    if nx not in LEVELS:
        raise InputIdentityError("only the frozen three-level family is admitted")
    ny, nb, count = nx//4, 2*nx, nx//2
    nodes = {1+j*(nx+1)+i: (i/nx, reference.WIDTH_M*j/ny, 0.)
             for j in range(ny+1) for i in range(nx+1)}
    shell = tuple((1+j*(nx+1)+i, 2+j*(nx+1)+i,
                   2+(j+1)*(nx+1)+i, 1+(j+1)*(nx+1)+i)
                  for j in range(ny) for i in range(nx))
    shell_ids = tuple(sorted(nodes))
    beam_ids = tuple(BEAM_FIRST+i for i in range(nb+1))
    if set(shell_ids) & set(beam_ids):
        raise InputIdentityError("disjoint physical node namespaces required")
    for i, node in enumerate(beam_ids):
        nodes[node] = (i/nb, 0., reference.BEAM_AXIS_Z_M)
    beam = tuple(zip(beam_ids, beam_ids[1:]))
    roots = tuple(1+j*(nx+1) for j in range(ny+1))
    fixes = {n: (1, 1, 1, 1, 1, 1) for n in roots}
    fixes[BEAM_FIRST] = (1, 1, 1, 1, 1, 0)
    return {"nx": nx, "ny": ny, "beam_intervals": nb, "support_count": count,
            "nodes": nodes, "shell_node_ids": shell_ids, "beam_node_ids": beam_ids,
            "shell_cells": shell, "beam_cells": beam, "root_shell_nodes": roots,
            "beam_root": BEAM_FIRST, "beam_tip": beam_ids[-1], "fixes": fixes,
            "physical_node_order": sorted(nodes), "moment_origin_m": nodes[BEAM_FIRST],
            "beam_element_tags": tuple(BEAM_ELEMENT_FIRST+i for i in range(nb)),
            "ID_policy": "Shell row-major1..(nx+1)(ny+1); beam100001+station; "
                         "shell elements1..nx*ny, beam elements100001+interval; no coordinate merge."}


def aggregate_rows(model, reference, p0):
    """Exact P1/Q1 integrals on union knots, two shell intervals per P0 support."""
    nx, nb, count = model["nx"], model["beam_intervals"], model["support_count"]
    knots = sorted({i/nb for i in range(nb+1)} | {i/nx for i in range(nx+1)})
    rb, rs = reference.BEAM_BOTTOM_ARM_M, reference.SHELL_THICKNESS_M/2.
    rows, supports = [], []
    for index in range(count):
        a, b = index/count, (index+1)/count
        bw, bp = p0.integrated_weights(a, b, nb, BEAM_FIRST, knots)
        sw, sp = p0.integrated_weights(a, b, nx, 1, knots)
        block = [{} for _ in range(5)]
        for n, w in bw.items():
            for d in range(5):
                block[d][n, d+1] = w
            block[0][n, 5], block[1][n, 4] = rb*w, -rb*w
        for n, w in sw.items():
            for d in range(5):
                block[d][n, d+1] = -w
            block[0][n, 5], block[1][n, 4] = -rs*w, rs*w
        dependent = BEAM_FIRST+4*(index+1)
        for d, coefficients in enumerate(block, 1):
            row = [dependent, d, coefficients[dependent, d]]
            for (n, dof), coefficient in sorted(coefficients.items()):
                if (n, dof) != (dependent, d) and coefficient != 0.:
                    row.extend((n, dof, coefficient))
            rows.append(row)
        supports.append({"support_id": index, "interval_m": (a, b), "width_m": b-a,
                         "beam_shape_integrals_m": bw, "shell_shape_integrals_m": sw,
                         "beam_pieces": bp, "shell_pieces": sp,
                         "row_indices": list(range(5*index, 5*index+5)),
                         "dependent_beam_node": dependent, "recovery_beam_node": BEAM_FIRST+4*index+2})
    if len(rows) != 5*count or len({(r[0], r[1]) for r in rows}) != len(rows):
        raise InputIdentityError("one unique nonzero dependent coordinate per integral row required")
    return rows, supports


def command_recipe(model, reference, rows, case):
    """The frozen external recipe, with explicit IDs, dimensions and declared load."""
    commands = [("wipe", ()), ("model", ("basic", "-ndm", 3, "-ndf", 6))]
    commands.extend(("node", (n, *xyz)) for n, xyz in model["nodes"].items())
    commands.append(("section", ("ElasticMembranePlateSection", 1, reference.E_PA, reference.NU,
                                  reference.SHELL_THICKNESS_M, 7850.)))
    commands.extend(("element", ("ASDShellQ4", tag, *cell, 1))
                    for tag, cell in enumerate(model["shell_cells"], 1))
    commands.append(("geomTransf", ("Linear", 1, 0., 0., 1.)))
    commands.extend(("element", ("ElasticTimoshenkoBeam", tag, *cell, reference.E_PA, reference.G_PA,
                     reference.BEAM_AREA_M2, reference.BEAM_TORSION_M4, reference.BEAM_BENDING_M4,
                     reference.BEAM_BENDING_M4, reference.BEAM_SHEAR_AREA_M2, reference.BEAM_SHEAR_AREA_M2, 1))
                    for tag, cell in zip(model["beam_element_tags"], model["beam_cells"]))
    commands.extend(("fix", (n, *flags)) for n, flags in model["fixes"].items())
    commands.extend(("equationConstraint", tuple(row)) for row in rows)
    commands.extend((("timeSeries", ("Linear", 1)), ("pattern", ("Plain", 1, 1)),
        ("load", (model["beam_tip"], *LOADS[case])), ("constraints", ("Lagrange", 1e9, 1e9)),
        ("numberer", ("RCM",)), ("system", ("BandGeneral",)), ("test", ("NormUnbalance", 1e-8, 20)),
        ("algorithm", ("Linear",)), ("integrator", ("LoadControl", 1.)), ("analysis", ("Static",)),
        ("analyze", (1,))))
    return commands


def planned_inventory(commands):
    """Source command projection for checking recorded assembly, not a solver."""
    raw = {"nodes": {}, "elements": {}, "equations": [], "fixes": {}, "loads": {}, "model_commands": []}
    for name, args in commands:
        if name == "node":
            raw["nodes"][args[0]] = list(args[1:])
        elif name == "element":
            kind, tag, *values = args
            raw["elements"][tag] = {"kind": kind, "nodes": list(values[:4 if kind == "ASDShellQ4" else 2]),
                                    "arguments": list(values)}
        elif name in ("fix", "load"):
            raw["fixes" if name == "fix" else "loads"][args[0]] = list(args[1:])
        elif name == "equationConstraint":
            raw["equations"].append(list(args))
        elif name not in ("wipe", "analyze"):
            raw["model_commands"].append([name, list(args), {}])
    return raw


def remap_first_level_raw(raw):
    """Explicit remap by declared IDs, never by coordinates or a range heuristic."""
    node_map = {n: n for n in range(1, 86)} | {1001+i: BEAM_FIRST+i for i in range(33)}
    element_map = {n: n for n in range(1, 65)} | {101+i: BEAM_ELEMENT_FIRST+i for i in range(32)}
    result = {key: value for key, value in raw.items()}
    for key in ("nodes", "fixes", "loads", "poses", "unverified_node_reaction_queries"):
        result[key] = {node_map[int(n)]: value for n, value in raw.get(key, {}).items()}
    result["elements"] = {}
    for tag, element in raw["elements"].items():
        count = 4 if element["kind"] == "ASDShellQ4" else 2
        arguments = [node_map[int(n)] for n in element["arguments"][:count]]+element["arguments"][count:]
        result["elements"][element_map[int(tag)]] = {**element,
            "nodes": [node_map[int(n)] for n in element["nodes"]], "arguments": arguments}
    result["element_global_covectors"] = {element_map[int(tag)]: value for tag, value in raw["element_global_covectors"].items()}
    result["equations"] = [[v for triple in ((node_map[int(n)], d, c)
        for n, d, c in zip(row[::3], row[1::3], row[2::3])) for v in triple] for row in raw["equations"]]
    return result, {"nodes_old_to_new": node_map, "elements_old_to_new": element_map}


def first_level_equivalence(folder, reference, p0, frozen, service):
    summary = json.loads((folder/"summary.json").read_text())
    old = json.loads((folder/"raw-inventory.json").read_text())
    if summary.get("status") != "completed" or summary.get("case") != "mz" or summary.get("source_sha256") != P0_SOURCE_SHA:
        raise InputIdentityError("completed exact-source first-level P0 Mz case required")
    expected_sources = {"b3_e4_bl5_matched_mz_reference_dev.py": p0.FROZEN_SOURCE_SHA,
        "b3_e4_bl5_matched_reference_actions.py": p0.SERVICE_SHA,
        "b3_e4_f03_bl5_opensees_line_reference.py": p0.REFERENCE_SHA}
    bound = {Path(path).name: digest for path, digest in summary.get("frozen_sources", {}).items()}
    if bound != expected_sources or summary.get("binary_sha256") != service.BINARY_SHA256:
        raise InputIdentityError("completed first-level source/binary binding mismatch")
    remapped, mapping = remap_first_level_raw(old)
    model = geometry(16, reference)
    rows, supports = aggregate_rows(model, reference, p0)
    expected = planned_inventory(command_recipe(model, reference, rows, "mz"))
    predicates = {key: remapped[key] == values for key, values in expected.items()}
    # Independent transcriptions compared both with saved actual commands and the
    # former source construction; neither supplies the new generator's rows.
    old_model = frozen.geometry(reference)
    old_rows, old_supports = p0.aggregate_rows(reference)
    source_view = {"nodes": old_model["nodes"], "fixes": old_model["fixes"], "loads": {}, "poses": {},
                   "elements": {}, "element_global_covectors": {}, "equations": old_rows}
    mapped_source, _ = remap_first_level_raw(source_view)
    predicates["source_geometry_equal"] = {n: tuple(v) for n, v in mapped_source["nodes"].items()} == model["nodes"]
    predicates["source_rows_equal"] = mapped_source["equations"] == rows
    predicates["source_support_intervals_equal"] = [s["interval_m"] for s in supports] == [s["interval_m"] for s in old_supports]
    if not all(predicates.values()):
        raise InputIdentityError(f"first-level ID-remapped equivalence failed: {predicates}")
    return remapped, {"predicates": predicates, "explicit_ID_remap": mapping,
        "completed_case_dir": str(folder.resolve()), "completed_case_hashes": {name: service._sha(folder/name)
            for name in ("summary.json", "raw-inventory.json", "inputs.json", "controls.json", "recovered-actions.json")},
        "scope": "Exact first-level geometry/rows/sections/frames/supports/load/commands under explicit ID remap; "
                 "reuse original Mz solve, no new first-level scientific solve."}


def sampled_gap(x, field, model, reference, p0, frozen, service):
    bw = p0.p1_weights(x, model["beam_intervals"], BEAM_FIRST)
    sw = p0.p1_weights(x, model["nx"], 1)
    view = {"nodes": {**model["nodes"], -1: (x, 0., reference.BEAM_AXIS_Z_M)}}
    values = {**field, -1: tuple(math.fsum(w*field[n][d] for n, w in bw) for d in range(6))}
    return frozen.objective_gap(view, reference, {"beam": -1, "shell_weights": sw}, values, service)


def integrated_objective(field, model, reference, p0, frozen, service):
    values, nb = [], model["beam_intervals"]
    for support in range(model["support_count"]):
        terms = [[] for _ in range(5)]
        for segment in range(4*support, 4*support+4):
            a, b = segment/nb, (segment+1)/nb
            for xi, w in zip((-math.sqrt(3./5.), 0., math.sqrt(3./5.)), (5./9., 8./9., 5./9.)):
                gap = sampled_gap((a+b)/2.+(b-a)*xi/2., field, model, reference, p0, frozen, service)
                for d in range(5):
                    terms[d].append((b-a)*w*gap[d]/2.)
        values.extend(math.fsum(t) for t in terms)
    return values


def controls(model, rows, supports, reference, p0, frozen, service):
    width = 1./model["support_count"]
    nodes, beam = model["nodes"], set(model["beam_node_ids"])
    zero = {n: (0.,)*6 for n in nodes}
    rigid = []
    for channel in range(6):
        a = tuple(.01 if channel == i else 0. for i in range(3))
        omega = tuple(.01 if channel == i+3 else 0. for i in range(3))
        field = {n: tuple(a[i]+service._cross(omega, xyz)[i] for i in range(3))+omega for n, xyz in nodes.items()}
        rigid.append(max(abs(v)/width for v in frozen.row_action(rows, field)))
    direction = {n: ((.017*x+.003, .013*x-.002, .011*x+.004, .029*x+.007, .021*x-.003, .031*x+.005)
                    if n in beam else (.011*x+.003*y, .014*x-.002*y, .006*x*y+.005*x,
                                       .023*x+.004*y, .017*x-.002*y, .019*x+.008*y))
                 for n, (x, y, z) in nodes.items()}
    exact = frozen.row_action(rows, direction)
    denominator = max(max(map(abs, exact)), 1e-12*width)
    plateau = []
    for eps in DERIVATIVE_STEPS:
        plus = {n: tuple(eps*v for v in q) for n, q in direction.items()}
        minus = {n: tuple(-eps*v for v in q) for n, q in direction.items()}
        gp = integrated_objective(plus, model, reference, p0, frozen, service)
        gm = integrated_objective(minus, model, reference, p0, frozen, service)
        plateau.append(max(abs((a-b)/(2*eps)-v) for a, b, v in zip(gp, gm, exact))/denominator)
    angle, shift = (.21, -.17, .13), (.03, -.02, .01)
    common = {n: tuple(frozen.rotated(angle, xyz, service._cross)[d]+shift[d]-xyz[d] for d in range(3))+angle
              for n, xyz in nodes.items()}
    spin = {n: (0., 0., 0., 0., 0., .13) if n in beam else (0.,)*6 for n in nodes}
    gaps = {label: max(abs(v)/width for v in integrated_objective(field, model, reference, p0, frozen, service))
            for label, field in (("reference", zero), ("common_finite_pose", common), ("released_spin", spin))}
    return {"six_common_rigid_field_average_gap_scaled": rigid, "objective_average_gap_scaled": gaps,
            "actual_left_exp_derivative_steps": DERIVATIVE_STEPS, "actual_left_exp_derivative_relative": plateau,
            "derivative_integrated_gap_denominator": denominator, "normal_spin_columns_zero": all(d != 6 for r in rows for d in r[1::3]),
            "positive_exact_shape_integrals": all(math.fsum(s[key].values()) == width and min(s[key].values()) > 0.
                for s in supports for key in ("beam_shape_integrals_m", "shell_shape_integrals_m")),
            "scope": "Virgin integrated derivative exact on segmented P1/Q1; finite left-Exp quadrature is "
                     "only a derivative/objectivity control, not finite mechanics."}


def solve(recorder, commands, model, reference):
    for name, args in commands:
        code = getattr(recorder, name)(*args)
        if name == "analyze" and code != 0:
            raise RuntimeError(f"OpenSees analyze returned {code}")
    for n in model["nodes"]:
        q = recorder.nodeDisp(n)
        if len(q) != 6 or not all(math.isfinite(v) for v in q):
            raise PhysicalPredicateError("finite six-component primary nodal pose required")
    for tag, cell in enumerate(model["shell_cells"], 1):
        reference._element_forces(recorder, tag, cell)
    for tag, cell in zip(model["beam_element_tags"], model["beam_cells"]):
        reference._element_forces(recorder, tag, cell)


def recover(raw, model, reference, rows, supports, case, frozen, service, p0, output):
    nodes, poses = model["nodes"], raw["poses"]
    shell, beam = set(model["shell_node_ids"]), set(model["beam_node_ids"])
    sg = service._sum_nodal(raw["elements"], raw["element_global_covectors"], shell, "ASDShellQ4")
    bg = service._sum_nodal(raw["elements"], raw["element_global_covectors"], beam, "ElasticTimoshenkoBeam")
    g, rb, rs = sg | bg, reference.BEAM_BOTTOM_ARM_M, reference.SHELL_THICKNESS_M/2.
    applied = {n: raw["loads"].get(n, [0.]*6) for n in nodes}
    coefficient_maps = [{(n, d): c for n, d, c in zip(r[::3], r[1::3], r[2::3])} for r in rows]
    recovery, density = [], []
    for index, support in enumerate(supports):
        center, weight = support["recovery_beam_node"], support["beam_shape_integrals_m"][support["recovery_beam_node"]]
        if any(model["fixes"].get(center, (0,)*6)[:5]):
            raise InterfaceRecoveryError("free interior center required")
        actual = [[c.get((center, d), 0.) for c in coefficient_maps[5*index:5*index+5]] for d in range(1, 6)]
        expected = [[weight, 0., 0., 0., 0.], [0., weight, 0., 0., 0.], [0., 0., weight, 0., 0.],
                    [0., -rb*weight, 0., weight, 0.], [rb*weight, 0., 0., 0., weight]]
        absent = all(c.get((center, d), 0.) == 0. for j, c in enumerate(coefficient_maps)
                     if j//5 != index for d in range(1, 6))
        if actual != expected or not absent:
            raise InterfaceRecoveryError("disjoint independent center work-map blocks required")
        rhs = [applied[center][d]-bg[center][d] for d in range(5)]
        lam = service._solve5(expected, rhs)
        residual = [math.fsum(a*v for a, v in zip(r, lam))-b for r, b in zip(actual, rhs)]
        recovery.append({"support_id": index, "center_node": center, "independent_5x5_matrix": expected,
                         "actual_5x5_matrix": actual, "other_support_coefficients_zero": absent, "rhs_L_minus_G": rhs,
                         "lambda_density": lam, "residual": residual})
        density.extend(lam)
    service._atomic(output/"interface-recovery-blocks.json", recovery)
    terms = {n: [[] for _ in range(6)] for n in nodes}
    for r, lam in zip(rows, density):
        for n, d, c in zip(r[::3], r[1::3], r[2::3]):
            terms[n][d-1].append(c*lam)
    resisting = {n: [math.fsum(t) for t in channels] for n, channels in terms.items()}
    exerted = {n: [-v for v in q] for n, q in resisting.items()}
    independent = {n: [[] for _ in range(6)] for n in nodes}
    origin = model["moment_origin_m"]
    shifted = {n: tuple(xyz[d]-origin[d] for d in range(3)) for n, xyz in nodes.items()}
    scale = max(max(map(abs, LOADS[case][:3])), max(map(abs, LOADS[case][3:])))  # Lref1m.
    local_errors, records = [], []
    for i, support in enumerate(supports):
        lam, local = density[5*i:5*i+5], {}
        for n, w in support["beam_shape_integrals_m"].items():
            local[n] = [w*v for v in (-lam[0], -lam[1], -lam[2], rb*lam[1]-lam[3], -rb*lam[0]-lam[4], 0.)]
        for n, w in support["shell_shape_integrals_m"].items():
            local[n] = [w*v for v in (lam[0], lam[1], lam[2], -rs*lam[1]+lam[3], rs*lam[0]+lam[4], 0.)]
        for n, q in local.items():
            for d, v in enumerate(q):
                independent[n][d].append(v)
        wrench = service._wrench(local, shifted)
        local_errors.append(max(abs(v)/scale for v in wrench))
        records.append({"support_id": i, "interval_m": support["interval_m"], "density_N_per_m_Nm_per_m": lam,
                        "independent_exerted_loads": local, "common_origin_interface_wrench": wrench})
    independent = {n: [math.fsum(t) for t in channels] for n, channels in independent.items()}
    residual = {n: [math.fsum((g[n][d], resisting[n][d], -applied[n][d])) for d in range(6)] for n in nodes}
    ground = {n: [residual[n][d] if model["fixes"].get(n, (0,)*6)[d] else 0. for d in range(6)] for n in nodes}
    free = {n: [0. if model["fixes"].get(n, (0,)*6)[d] else residual[n][d] for d in range(6)] for n in nodes}
    gaps = frozen.row_action(rows, poses)
    work = {"internal": math.fsum(service._dot(g[n], poses[n]) for n in nodes),
            "applied": math.fsum(service._dot(applied[n], poses[n]) for n in nodes),
            "interface_exerted": math.fsum(service._dot(exerted[n], poses[n]) for n in nodes),
            "ground": math.fsum(service._dot(ground[n], poses[n]) for n in nodes),
            "constraint_resisting": math.fsum(lam*gap for lam, gap in zip(density, gaps))}
    work_scale = max(abs(work["internal"]), abs(work["applied"]), 1e-12)
    virtual = {n: (.017*x+.003*y, .013*x-.002*z, .011*x+.004*y, .029*x+.007*y, .021*x-.003*z, .031*x+.005*y)
               for n, (x, y, z) in nodes.items()}
    virtual_gaps = frozen.row_action(rows, virtual)
    vw = math.fsum(service._dot(exerted[n], virtual[n]) for n in nodes)
    vr = math.fsum(lam*gap for lam, gap in zip(density, virtual_gaps))
    virtual_scale = max(math.fsum(abs(exerted[n][d]*virtual[n][d]) for n in nodes for d in range(6)),
                        math.fsum(abs(lam*gap) for lam, gap in zip(density, virtual_gaps)), 1e-12)
    aw, gw, iw = (service._wrench(f, shifted) for f in (applied, ground, exerted))
    cuts = {label: {"applied_exerted_ground_wrench": service._wrench(
            {n: [math.fsum((applied[n][d], exerted[n][d], ground[n][d])) for d in range(6)] for n in domain}, shifted),
            "internal_G_wrench": service._wrench({n: g[n] for n in domain}, shifted)} for label, domain in (("shell", shell), ("beam", beam))}
    measures = p0.density_measures(supports, density, reference)
    checks = {"all_free_coordinate_equilibrium_scaled": max(abs(v)/scale for q in free.values() for v in q),
        "average_five_channel_gap_scaled": max(abs(v)*model["support_count"] for v in gaps),
        "local_recovery_residual_scaled": max(abs(v)/scale for record in recovery for v in record["residual"]),
        "independent_arm_pullback_scaled": max(abs(exerted[n][d]-independent[n][d])/scale for n in nodes for d in range(6)),
        "each_support_action_reaction_scaled": max(local_errors), "interface_wrench_scaled": max(abs(v)/scale for v in iw),
        "ground_plus_applied_wrench_scaled": max(abs(a+b)/scale for a, b in zip(aw, gw)),
        "complete_domain_cut_wrench_scaled": max(abs(v)/scale for cut in cuts.values() for v in cut["applied_exerted_ground_wrench"]),
        "physical_work_relative": abs(work["internal"]-work["applied"]-work["interface_exerted"]-work["ground"])/work_scale,
        "internal_applied_work_relative": abs(work["internal"]-work["applied"])/work_scale,
        "compatible_interface_work_relative": abs(work["interface_exerted"])/work_scale,
        "solved_dual_work_relative": abs(work["interface_exerted"]+work["constraint_resisting"])/work_scale,
        "virtual_dual_work_relative": abs(vw+vr)/virtual_scale,
        "continuous_density_nodal_total_wrench_scaled": max(abs(a-b)/scale for a, b in zip(
            measures["polynomial_x_moments"]["0"], service._wrench({n: exerted[n] for n in beam}, shifted)))}
    root = set(model["fixes"])
    return {"sign_provenance": "+C^T lambda connection resisting; -C^T lambda connection exerted; "
                "ground=(G+C^T lambda-L) restricted to prescribed DOFs. Root G is not ground; raw nodeReaction unused.",
            "units": "Integrated position rows m^2/director rows m; density N/m,Nm/m; average gaps m/rad. Lref1m.",
            "row_density_multipliers": density, "support_records": records, "local_recovery": recovery,
            "full_q_node_poses": poses, "applied_nodal_L": applied, "shell_domain_nodal_G": sg, "beam_domain_nodal_G": bg,
            "connection_resisting_C_transpose_lambda": resisting, "connection_exerted_minus_C_transpose_lambda": exerted,
            "independent_density_pullback": independent, "actual_ground_exerted_loads": ground,
            "all_free_equilibrium_residuals": free, "integrated_equation_gaps_Cq": gaps,
            "virtual_q": virtual, "virtual_Cq": virtual_gaps, "work_J": work | {"virtual_exerted": vw, "virtual_resisting": vr},
            "applied_wrench_about_beam_root": aw, "ground_wrench_about_beam_root": gw, "interface_wrench_about_beam_root": iw,
            "complete_domain_cuts": cuts, "root_G_wrench": service._wrench({n: g[n] for n in root}, shifted),
            "root_interface_wrench": service._wrench({n: exerted[n] for n in root}, shifted),
            "beam_ground_wrench": service._wrench({model["beam_root"]: ground[model["beam_root"]]}, shifted),
            "shell_ground_wrench": service._wrench({n: ground[n] for n in shell}, shifted),
            "root_provenance": "Shell full x0 column clamped; beam root first5 directly grounded/normalspinfree. "
                "First P0 support allocates interface loads to root; actual G and interface root partition retained.",
            "continuous_density_measures": measures, "scales": {"length_m": 1., "force_N": scale, "moment_Nm": scale,
                "work_J": work_scale, "virtual_absolute_work_J": virtual_scale, "work_floor_J": 1e-12}, "checks": checks}


def main(site, output, first_level_folder, nx, case, reuse):
    output.mkdir(parents=True, exist_ok=False)
    p0, frozen, service, reference, paths = services()
    recorder, original_error = None, None
    summary = {"status": "failed", "case": case, "nx": nx, "python": sys.version,
        "source_sha256": service._sha(__file__), "helper_sources": {str(p): service._sha(p) for p in paths},
        "requested_threads": {k: os.environ.get(k) for k in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS")},
        "thread_scope": "Environment requests only; effective external OpenSees threads unresolved; no resource-qualified claim.",
        "family_policy": {"levels": LEVELS, "ny": "nx/4", "two_node_beam_intervals": "2nx", "P0_support_count": "nx/2",
                          "P0_support_width_m": "2/nx", "rows": "5nx/2", "cases": LOADS, "total_family_cases": 9,
                          "first_level_Mz": "Reuse completed exact-equivalent case; at most8 new scientific solves."},
        "claim_scope": "Growing-space external reference development; no 1%/locking/F03/candidate acceptance; "
                       "no law or criterion tuning, no native C substitution, no global mechanical inverse."}
    try:
        expected = (P0_SOURCE_SHA, p0.FROZEN_SOURCE_SHA, p0.SERVICE_SHA, p0.REFERENCE_SHA)
        for path, digest in zip(paths, expected):
            if service._sha(path) != digest:
                raise InputIdentityError(f"frozen helper identity mismatch: {path}")
        if case not in LOADS or (reuse and (nx != 16 or case != "mz")):
            raise InputIdentityError("reuse applies only to the completed first-level Mz case")
        model = geometry(nx, reference)
        rows, supports = aggregate_rows(model, reference, p0)
        commands = command_recipe(model, reference, rows, case)
        expected_raw = planned_inventory(commands)
        reused_raw, equivalence = first_level_equivalence(first_level_folder, reference, p0, frozen, service)
        service._atomic(output/"first-level-equivalence.json", equivalence)
        service._atomic(output/"inputs.json", {"model": model, "rows": rows, "supports": supports, "commands": commands,
            "load": LOADS[case], "family_policy": summary["family_policy"], "helper_sources": summary["helper_sources"],
            "arms_m": {"shell_top": reference.SHELL_THICKNESS_M/2., "beam_normal": reference.BEAM_BOTTOM_ARM_M},
            "director_channels": "Physical nodal theta_x/theta_y; theta_z free. Shell edge Q1/beam P1, exact union-piece averages.",
            "limits": summary["claim_scope"]})
        control = controls(model, rows, supports, reference, p0, frozen, service)
        service._atomic(output/"controls.json", control)
        if (len(control["six_common_rigid_field_average_gap_scaled"]) != 6
            or any(not math.isfinite(v) or v > GAP_LIMIT for v in control["six_common_rigid_field_average_gap_scaled"]+list(control["objective_average_gap_scaled"].values()))
            or len(control["actual_left_exp_derivative_relative"]) != 3
            or any(not math.isfinite(v) or v > DERIVATIVE_LIMIT for v in control["actual_left_exp_derivative_relative"])
            or not control["normal_spin_columns_zero"] or not control["positive_exact_shape_integrals"]):
            raise PhysicalPredicateError("integrated virgin reference controls failed")
        if reuse:
            raw = reused_raw
            summary["execution_route"] = "No new solve: exact ID-remapped completed first-level Mz raw inventory"
            summary["binary_sha256"] = service.BINARY_SHA256
        else:
            if nx == 16 and case == "mz":
                raise InputIdentityError("reuse first-level Mz; a second solve needs separately justified changed-code authority")
            if sys.version_info[:2] != (3, 12):
                raise InputIdentityError("verified OpenSees binary requires Python3.12")
            sys.path.insert(0, str(site.resolve(strict=True)))
            import openseespy.opensees as ops
            from openseespywin import opensees as core
            summary.update(opensees=ops.version(), binary=str(Path(core.__file__).resolve()), binary_sha256=service._sha(core.__file__))
            if not summary["opensees"].startswith("3.8") or summary["binary_sha256"] != service.BINARY_SHA256:
                raise InputIdentityError("verified OpenSees3.8 binary required")
            recorder = service.RecordingOps(ops)
            solve(recorder, commands, model, reference)
            raw = recorder.raw
            summary["execution_route"] = "One fresh external owner/case"
        service._atomic(output/"raw-inventory.json", raw)
        inventory = {key: raw[key] == values for key, values in expected_raw.items()}
        inventory["all_primary_poses"] = set(raw["poses"]) == set(model["nodes"])
        inventory["all_element_covectors"] = set(raw["element_global_covectors"]) == set(expected_raw["elements"])
        service._atomic(output/"inventory-predicates.json", inventory)
        if not all(inventory.values()):
            raise InputIdentityError(f"complete declared inventory required: {inventory}")
        derived = recover(raw, model, reference, rows, supports, case, frozen, service, p0, output)
        service._atomic(output/"recovered-actions.json", derived)
        for name, value in derived["checks"].items():
            limit = GAP_LIMIT if name == "average_five_channel_gap_scaled" else BALANCE_LIMIT
            if not math.isfinite(value) or value > limit:
                raise PhysicalPredicateError(f"{name}={value} exceeds unchanged physical budget {limit}")
        summary.update(status="completed", physical_nodes=len(model["nodes"]), shell_elements=len(model["shell_cells"]),
                       beam_elements=len(model["beam_cells"]), rows=len(rows), P0_supports=len(supports),
                       applied_work_J=derived["work_J"]["applied"], checks=derived["checks"])
    except BaseException as error:
        original_error = error
        summary["failure"] = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
        raise
    finally:
        cleanup_error = None
        if recorder is not None:
            for name, action in (("retain_raw", lambda: service._atomic(output/"raw-inventory.json", recorder.raw)), ("wipe", recorder.wipe)):
                try:
                    action()
                except BaseException as error:
                    cleanup_error = error
                    summary["status"] = "failed"
                    summary.setdefault("retention_cleanup_failures", []).append({"operation": name, "type": type(error).__name__, "message": str(error)})
        try:
            service._atomic(output/"summary.json", summary)
        except BaseException:
            if original_error is None:
                raise
            traceback.print_exc()
        if cleanup_error is not None and original_error is None:
            raise cleanup_error


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--completed-first-level-dir", type=Path, required=True)
    parser.add_argument("--nx", type=int, choices=LEVELS, required=True)
    parser.add_argument("--case", choices=tuple(LOADS), required=True)
    parser.add_argument("--reuse-completed-first-level", action="store_true")
    args = parser.parse_args()
    main(args.site, args.output_dir, args.completed_first_level_dir, args.nx, args.case, args.reuse_completed_first_level)

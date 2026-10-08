"""Fixed external Mz enforcement-space discriminator, not an accuracy gate.

Keep the frozen 16x4 ASDShellQ4 / 32 ElasticTimoshenkoBeam model and commands.
Replace only its 160 strong rows by 40 exactly integrated P0 work rows on
eight 0.125 m supports. Physical beam rotation is continuous nodal P1 here;
these rows are NOT a rasterization of the native retained-cell rotation law.
Pure stdlib plus the verified Python3.12/OpenSees3.8 runtime, one fresh process.
No effective external-thread, converged-reference, locking or F03 claim.
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


FROZEN_SOURCE_SHA = "6e1b3f25c2b479e1ade3700b57d996cef2f9709812a72108ce7e6a41e346293a"
SERVICE_SHA = "506c5259afddfab1872c50c2a2544a7cb706b4cf14e6e7c6b4771d80a0ff98cc"
REFERENCE_SHA = "5d3616e5fc6f198adc8c0442e01c27c5b7b719e73059f5088561d0027e826f47"
SUPPORT_COUNT, SUPPORT_WIDTH = 8, .125
BALANCE_LIMIT, GAP_LIMIT, DERIVATIVE_LIMIT = 1e-8, 1e-9, 1e-6
DERIVATIVE_STEPS = (1e-4, 3e-5, 1e-5)


class InputIdentityError(ValueError):
    pass


class InterfaceRecoveryError(RuntimeError):
    pass


class PhysicalPredicateError(RuntimeError):
    pass


def services():
    path = Path(__file__).with_name("b3_e4_bl5_matched_mz_reference_dev.py")
    spec = importlib.util.spec_from_file_location("_external_p0_frozen_reference", path)
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    service, service_path, reference, reference_path = frozen.services()
    return frozen, service, reference, (path, service_path, reference_path)


def p1_weights(x, intervals, first_node):
    """Physical shape functions, including the exact right endpoint."""
    if not 0. <= x <= 1.:
        raise InputIdentityError("trace coordinate outside [0,1] m")
    if x == 1.:
        return ((first_node+intervals, 1.),)
    coordinate = x*intervals
    left = int(math.floor(coordinate))
    fraction = coordinate-left
    if fraction == 0.:
        return ((first_node+left, 1.),)
    return ((first_node+left, 1.-fraction), (first_node+left+1, fraction))


def integrated_weights(left, right, intervals, first_node, union_knots):
    """Exact trapezoidal integration of each affine piece, no Gauss atoms."""
    pieces = []
    terms = {}
    for a, b in zip(union_knots, union_knots[1:]):
        if a < left or b > right:
            continue
        endpoints = (p1_weights(a, intervals, first_node), p1_weights(b, intervals, first_node))
        for weights in endpoints:
            for node, weight in weights:
                terms.setdefault(node, []).append((b-a)*weight/2.)
        pieces.append({"interval_m": (a, b), "endpoint_weights": endpoints})
    weights = {node: math.fsum(values) for node, values in sorted(terms.items())}
    if math.fsum(weights.values()) != right-left or any(v <= 0. for v in weights.values()):
        raise InputIdentityError("exact positive shape-function integral required")
    return weights, pieces


def aggregate_rows(reference):
    """Ct=ub-us+theta_b cross rb-theta_s cross rs; Cr=theta_bxy-theta_sxy.

    Arms are rb=-0.05 ez and rs=+0.0175 ez in this sign convention.
    Integrals use m: position rows have m^2, director rows m (rad dimensionless).
    Their multipliers are force density N/m and moment density Nm/m.
    """
    knots = sorted({i/32 for i in range(33)} | {i/16 for i in range(17)})
    rb, rs = reference.BEAM_BOTTOM_ARM_M, reference.SHELL_THICKNESS_M/2.
    rows, supports = [], []
    for index in range(SUPPORT_COUNT):
        left, right = index/8., (index+1)/8.
        bw, bp = integrated_weights(left, right, 32, 1001, knots)
        sw, sp = integrated_weights(left, right, 16, 1, knots)
        block = [{} for _ in range(5)]
        for node, weight in bw.items():
            for d in range(5):
                block[d][node, d+1] = weight
            block[0][node, 5] = rb*weight
            block[1][node, 4] = -rb*weight
        for node, weight in sw.items():
            for d in range(5):
                block[d][node, d+1] = -weight
            block[0][node, 5] = -rs*weight
            block[1][node, 4] = rs*weight
        dependent = 1001+4*(index+1)
        for channel, coefficients in enumerate(block, 1):
            first = (dependent, channel)
            if coefficients.get(first, 0.) == 0.:
                raise InputIdentityError("unique dependent coefficient must be nonzero")
            row = [dependent, channel, coefficients[first]]
            for (node, dof), coefficient in sorted(coefficients.items()):
                if (node, dof) != first and coefficient != 0.:
                    row.extend((node, dof, coefficient))
            rows.append(row)
        supports.append({"support_id": index, "interval_m": (left, right), "width_m": right-left,
                         "beam_shape_integrals_m": bw, "shell_shape_integrals_m": sw,
                         "beam_pieces": bp, "shell_pieces": sp,
                         "row_indices": list(range(5*index, 5*index+5)),
                         "dependent_beam_node": dependent, "recovery_beam_node": 1003+4*index})
    if len(rows) != 40 or len({(row[0], row[1]) for row in rows}) != 40:
        raise InputIdentityError("40 unique dependent node/DOF pairs required")
    return rows, supports


class RowReplacement:
    """Transparent command forwarding; do not mutate the frozen loaded module.

    The original solve still emits its exact 160 rows. Check and consume these,
    then emit the 40 replacements before its next command. Everything else is
    forwarded verbatim to the original recorder and its primary runtime.
    """
    def __init__(self, recorder, expected, replacement):
        self.recorder, self.expected, self.replacement = recorder, expected, replacement
        self.consumed, self.emitted = 0, 0

    def __getattr__(self, name):
        return getattr(self.recorder, name)

    def equationConstraint(self, *args):
        if self.consumed >= len(self.expected) or list(args) != self.expected[self.consumed]:
            raise InputIdentityError("frozen strong-row command sequence changed")
        self.consumed += 1
        if self.consumed == len(self.expected):
            for row in self.replacement:
                self.recorder.equationConstraint(*row)
                self.emitted += 1


def gaussian_solve(matrix, rhs):
    """Bounded 40x40 interface action recovery, never a mechanical inverse."""
    n = len(rhs)
    if n != 40 or len(matrix) != n or any(len(row) != n for row in matrix):
        raise InterfaceRecoveryError("exact bounded 40x40 recovery system required")
    a = [list(row)+[value] for row, value in zip(matrix, rhs)]
    if any(not math.isfinite(v) for row in a for v in row):
        raise InterfaceRecoveryError("finite recovery system required")
    pivots = []
    for column in range(n):
        pivot = max(range(column, n), key=lambda i: abs(a[i][column]))
        a[column], a[pivot] = a[pivot], a[column]
        value = a[column][column]
        pivots.append({"column": column, "selected_row": pivot, "pivot": value})
        if value == 0. or not math.isfinite(value):
            raise InterfaceRecoveryError("singular interface action recovery")
        for i in range(column+1, n):
            ratio = a[i][column]/value
            a[i][column] = 0.
            for j in range(column+1, n+1):
                a[i][j] = math.fsum((a[i][j], -ratio*a[column][j]))
    x = [0.]*n
    for i in range(n-1, -1, -1):
        x[i] = math.fsum((a[i][n], -math.fsum(a[i][j]*x[j] for j in range(i+1, n))))/a[i][i]
    if any(not math.isfinite(v) for v in x):
        raise InterfaceRecoveryError("nonfinite recovered density")
    residual = [math.fsum((math.fsum(c*v for c, v in zip(row, x)), -value))
                for row, value in zip(matrix, rhs)]
    return x, {"matrix": matrix, "rhs": rhs, "pivots": pivots, "residual": residual}


def sampled_gap(x, field, model, reference, frozen, service):
    """Evaluation-only interpolated pose, not an added mechanical station/node."""
    bw, sw = p1_weights(x, 32, 1001), p1_weights(x, 16, 1)
    virtual = -1
    view = {"nodes": {**model["nodes"], virtual: (x, 0., reference.BEAM_AXIS_Z_M)}}
    values = {**field, virtual: tuple(math.fsum(w*field[n][d] for n, w in bw) for d in range(6))}
    return frozen.objective_gap(view, reference, {"beam": virtual, "shell_weights": sw}, values, service)


def integrated_objective(field, model, reference, frozen, service):
    """Three-point rule per affine segment for finite-update derivative controls.

    The virgin derivative is affine and integrated exactly; no finite nonlinear
    law or exact finite-gap quadrature is claimed by this auxiliary evaluation.
    """
    abscissae = (-math.sqrt(3./5.), 0., math.sqrt(3./5.))
    weights = (5./9., 8./9., 5./9.)
    values = []
    for support in range(8):
        terms = [[] for _ in range(5)]
        for segment in range(4*support, 4*support+4):
            a, b = segment/32., (segment+1)/32.
            for xi, w in zip(abscissae, weights):
                gap = sampled_gap((a+b)/2.+(b-a)*xi/2., field, model, reference, frozen, service)
                for d in range(5):
                    terms[d].append((b-a)*w*gap[d]/2.)
        values.extend(math.fsum(t) for t in terms)
    return values


def controls(rows, supports, model, reference, frozen, service):
    nodes = model["nodes"]
    zero = {node: (0.,)*6 for node in nodes}
    rigid = []
    for channel in range(6):
        a = tuple(.01 if channel == i else 0. for i in range(3))
        omega = tuple(.01 if channel == i+3 else 0. for i in range(3))
        field = {n: tuple(a[i]+service._cross(omega, xyz)[i] for i in range(3))+omega
                 for n, xyz in nodes.items()}
        rigid.append(max(abs(v)/SUPPORT_WIDTH for v in frozen.row_action(rows, field)))
    direction = {n: ((.017*x+.003, .013*x-.002, .011*x+.004,
                      .029*x+.007, .021*x-.003, .031*x+.005) if n >= 1001 else
                     (.011*x+.003*y, .014*x-.002*y, .006*x*y+.005*x,
                      .023*x+.004*y, .017*x-.002*y, .019*x+.008*y))
                 for n, (x, y, z) in nodes.items()}
    exact = frozen.row_action(rows, direction)
    denominator = max(max(map(abs, exact)), 1e-12*SUPPORT_WIDTH)
    plateau = []
    for eps in DERIVATIVE_STEPS:
        plus = {n: tuple(eps*v for v in row) for n, row in direction.items()}
        minus = {n: tuple(-eps*v for v in row) for n, row in direction.items()}
        gp = integrated_objective(plus, model, reference, frozen, service)
        gm = integrated_objective(minus, model, reference, frozen, service)
        plateau.append(max(abs((a-b)/(2.*eps)-target) for a, b, target in zip(gp, gm, exact))/denominator)
    angle, shift = (.21, -.17, .13), (.03, -.02, .01)
    common = {n: tuple(frozen.rotated(angle, xyz, service._cross)[i]+shift[i]-xyz[i]
                       for i in range(3))+angle for n, xyz in nodes.items()}
    spin = {n: (0., 0., 0., 0., 0., .13) if n >= 1001 else (0.,)*6 for n in nodes}
    gaps = {label: max(abs(v)/SUPPORT_WIDTH for v in integrated_objective(
                         field, model, reference, frozen, service))
            for label, field in (("reference", zero), ("common_finite_pose", common), ("released_spin", spin))}
    return {"six_common_rigid_field_average_gap_scaled": rigid,
            "integrated_objective_average_gap_scaled": gaps,
            "actual_left_exp_derivative_steps": DERIVATIVE_STEPS,
            "actual_left_exp_derivative_relative": plateau,
            "derivative_integrated_gap_denominator": denominator,
            "normal_spin_columns_zero": all(d != 6 for row in rows for d in row[1::3]),
            "support_partition_integral_exact": all(math.fsum(s[which].values()) == SUPPORT_WIDTH
                for s in supports for which in ("beam_shape_integrals_m", "shell_shape_integrals_m")),
            "limits": "Common-reference derivative/objectivity controls, not finite native mechanics."}


def polynomial_integral(coefficients, left, right):
    return math.fsum(c*(right**(i+1)-left**(i+1))/(i+1) for i, c in enumerate(coefficients))


def density_measures(supports, densities, reference):
    """Integrate continuum P0 actions; allocation to nodes is separate.

    Wrench density is about (0,0,beam_axis_z); line moment is arm moment+x cross F.
    Supports are continuous measures: open and closed windows coincide, with no
    endpoint atoms. Polynomial moments and smooth window are analytically integrated.
    """
    result = {"polynomial_x_moments": {str(p): [0.]*6 for p in range(3)},
              "fixed_region_025_075": {k: [0.]*6 for k in ("open", "closed", "endpoint_atoms", "smooth_unit_peak")}}
    terms = {str(p): [[] for _ in range(6)] for p in range(3)}
    window = {k: [[] for _ in range(6)] for k in ("open", "closed", "smooth_unit_peak")}
    # 256 (x-.25)^2 (.75-x)^2, exact polynomial coefficients.
    smooth = (9., -96., 352., -512., 256.)
    rb = reference.BEAM_BOTTOM_ARM_M
    for index, support in enumerate(supports):
        lam = densities[5*index:5*index+5]
        force = [-v for v in lam[:3]]
        moment = (rb*lam[1]-lam[3], -rb*lam[0]-lam[4], 0.)
        slope = (0., -force[2], force[1])
        coefficients = [[v] for v in force]+[[moment[d], slope[d]] for d in range(3)]
        a, b = support["interval_m"]
        for power in range(3):
            for d, c in enumerate(coefficients):
                terms[str(power)][d].append(polynomial_integral([0.]*power+c, a, b))
        left, right = max(a, .25), min(b, .75)
        if right > left:
            for d, c in enumerate(coefficients):
                value = polynomial_integral(c, left, right)
                for kind in ("open", "closed"):
                    window[kind][d].append(value)
                product = [0.]*(len(c)+len(smooth)-1)
                for i, ci in enumerate(c):
                    for j, sj in enumerate(smooth):
                        product[i+j] += ci*sj
                window["smooth_unit_peak"][d].append(polynomial_integral(product, left, right))
    result["polynomial_x_moments"] = {p: [math.fsum(t) for t in channels] for p, channels in terms.items()}
    for kind, channels in window.items():
        result["fixed_region_025_075"][kind] = [math.fsum(t) for t in channels]
    result["measure_provenance"] = "Continuous P0 density; no strong-station nodal atoms; root origin/arms explicit."
    return result


def recover(raw, model, reference, rows, supports, frozen, service, output):
    nodes, poses = model["nodes"], raw["poses"]
    shell_nodes = {n for cell in model["shell_cells"] for n in cell}
    beam_nodes = {n for cell in model["beam_cells"] for n in cell}
    sg = service._sum_nodal(raw["elements"], raw["element_global_covectors"], shell_nodes, "ASDShellQ4")
    bg = service._sum_nodal(raw["elements"], raw["element_global_covectors"], beam_nodes, "ElasticTimoshenkoBeam")
    g = sg | bg
    applied = {n: raw["loads"].get(n, [0.]*6) for n in nodes}
    selected = [(s["recovery_beam_node"], d) for s in supports for d in range(1, 6)]
    if any(model["fixes"].get(n, (0,)*6)[d-1] for n, d in selected):
        raise InterfaceRecoveryError("recovery coordinates must be free")
    coefficients = [{(n, d): c for n, d, c in zip(row[::3], row[1::3], row[2::3])} for row in rows]
    matrix = [[c.get((n, d), 0.) for c in coefficients] for n, d in selected]
    rhs = [applied[n][d-1]-bg[n][d-1] for n, d in selected]
    service._atomic(output/"interface-recovery-system.json", {
        "selected_free_node_dof_coordinates": selected, "matrix_selected_C_beam_transpose": matrix,
        "rhs_selected_L_minus_G_beam": rhs, "limit": "40x40 interface recovery only, no mechanical inverse"})
    density, recovery = gaussian_solve(matrix, rhs)
    recovery["selected_node_dof_coordinates"] = selected
    terms = {n: [[] for _ in range(6)] for n in nodes}
    for row, value in zip(rows, density):
        for n, d, c in zip(row[::3], row[1::3], row[2::3]):
            terms[n][d-1].append(c*value)
    resisting = {n: [math.fsum(t) for t in channels] for n, channels in terms.items()}
    exerted = {n: [-v for v in values] for n, values in resisting.items()}
    independent = {n: [[] for _ in range(6)] for n in nodes}
    records, support_wrench_errors = [], []
    rb, rs = reference.BEAM_BOTTOM_ARM_M, reference.SHELL_THICKNESS_M/2.
    origin = model["moment_origin_m"]
    shifted = {n: tuple(xyz[d]-origin[d] for d in range(3)) for n, xyz in nodes.items()}
    for index, support in enumerate(supports):
        lam = density[5*index:5*index+5]
        local = {}
        for n, w in support["beam_shape_integrals_m"].items():
            local[n] = [w*v for v in (-lam[0], -lam[1], -lam[2], rb*lam[1]-lam[3], -rb*lam[0]-lam[4], 0.)]
        for n, w in support["shell_shape_integrals_m"].items():
            local[n] = [w*v for v in (lam[0], lam[1], lam[2], -rs*lam[1]+lam[3], rs*lam[0]+lam[4], 0.)]
        for n, vector in local.items():
            for d, v in enumerate(vector):
                independent[n][d].append(v)
        wrench = service._wrench(local, shifted)
        support_wrench_errors.append(max(abs(v)/10. for v in wrench))
        records.append({"support_id": index, "interval_m": support["interval_m"],
                        "lambda_force_density_N_per_m": lam[:3], "lambda_moment_density_Nm_per_m": lam[3:],
                        "independent_exerted_nodal_loads": local, "net_interface_wrench_about_root": wrench})
    independent = {n: [math.fsum(t) for t in channels] for n, channels in independent.items()}
    residual = {n: [math.fsum((g[n][d], resisting[n][d], -applied[n][d])) for d in range(6)] for n in nodes}
    ground = {n: [residual[n][d] if model["fixes"].get(n, (0,)*6)[d] else 0. for d in range(6)] for n in nodes}
    free = {n: [0. if model["fixes"].get(n, (0,)*6)[d] else residual[n][d] for d in range(6)] for n in nodes}
    gaps = frozen.row_action(rows, poses)
    internal_work = math.fsum(service._dot(g[n], poses[n]) for n in nodes)
    applied_work = math.fsum(service._dot(applied[n], poses[n]) for n in nodes)
    interface_work = math.fsum(service._dot(exerted[n], poses[n]) for n in nodes)
    ground_work = math.fsum(service._dot(ground[n], poses[n]) for n in nodes)
    constraint_work = math.fsum(v*gap for v, gap in zip(density, gaps))
    work_scale = max(abs(internal_work), abs(applied_work), 1e-12)
    virtual = {n: (.017*x+.003*y, .013*x-.002*z, .011*x+.004*y,
                   .029*x+.007*y, .021*x-.003*z, .031*x+.005*y)
               for n, (x, y, z) in nodes.items()}
    virtual_gaps = frozen.row_action(rows, virtual)
    virtual_exerted = math.fsum(service._dot(exerted[n], virtual[n]) for n in nodes)
    virtual_resisting = math.fsum(v*gap for v, gap in zip(density, virtual_gaps))
    virtual_scale = max(math.fsum(abs(exerted[n][d]*virtual[n][d]) for n in nodes for d in range(6)),
                        math.fsum(abs(v*gap) for v, gap in zip(density, virtual_gaps)), 1e-12)
    aw, gw, iw = (service._wrench(field, shifted) for field in (applied, ground, exerted))
    cuts = {}
    for label, domain in (("shell", shell_nodes), ("beam", beam_nodes)):
        cuts[label] = {"applied_exerted_ground_wrench": service._wrench(
            {n: [math.fsum((applied[n][d], exerted[n][d], ground[n][d])) for d in range(6)] for n in domain}, shifted),
            "internal_G_wrench": service._wrench({n: g[n] for n in domain}, shifted)}
    root = set(model["fixes"])
    checks = {"all_free_coordinate_equilibrium_scaled": max(abs(v)/10. for row in free.values() for v in row),
        "average_five_channel_gap_scaled": max(abs(v)/SUPPORT_WIDTH for v in gaps),
        "selected_recovery_equilibrium_scaled": max(abs(v)/10. for v in recovery["residual"]),
        "independent_force_arm_pullback_scaled": max(abs(exerted[n][d]-independent[n][d])/10. for n in nodes for d in range(6)),
        "each_support_common_origin_action_reaction_scaled": max(support_wrench_errors),
        "total_interface_common_origin_wrench_scaled": max(abs(v)/10. for v in iw),
        "ground_plus_applied_common_origin_wrench_scaled": max(abs(a+b)/10. for a, b in zip(aw, gw)),
        "complete_domain_cut_wrench_scaled": max(abs(v)/10. for cut in cuts.values() for v in cut["applied_exerted_ground_wrench"]),
        "physical_work_relative": abs(internal_work-applied_work-interface_work-ground_work)/work_scale,
        "internal_applied_work_relative": abs(internal_work-applied_work)/work_scale,
        "compatible_interface_work_relative": abs(interface_work)/work_scale,
        "solved_dual_work_relative": abs(interface_work+constraint_work)/work_scale,
        "noncompatible_virtual_dual_work_relative": abs(virtual_exerted+virtual_resisting)/virtual_scale}
    measures = density_measures(supports, density, reference)
    checks["continuous_density_nodal_total_wrench_scaled"] = max(abs(a-b)/10. for a, b in zip(
        measures["polynomial_x_moments"]["0"], service._wrench({n: exerted[n] for n in beam_nodes}, shifted)))
    return {"sign_provenance": "G element resisting, L applied; +C^T lambda connection resisting; "
                "-C^T lambda connection exerted; actual ground=(G+C^T lambda-L) on fixed DOFs only. No raw nodeReaction.",
            "units": "C translation rows m^2, director rows m; lambda=(N/m,Nm/m); average gaps m/rad. Lref1m.",
            "recovery": recovery, "row_density_multipliers": density, "support_records": records,
            "physical_node_order": model["physical_node_order"], "full_q_node_poses": poses,
            "shell_domain_nodal_G": sg, "beam_domain_nodal_G": bg, "applied_nodal_L": applied,
            "connection_resisting_C_transpose_lambda": resisting, "connection_exerted_minus_C_transpose_lambda": exerted,
            "independent_density_pullback": independent, "actual_ground_exerted_loads": ground,
            "all_free_equilibrium_residuals": free, "integrated_equation_gaps_Cq": gaps,
            "virtual_q": virtual, "virtual_Cq": virtual_gaps,
            "applied_wrench_about_beam_root": aw, "ground_wrench_about_beam_root": gw,
            "interface_wrench_about_beam_root": iw, "complete_domain_cuts": cuts,
            "root_G_wrench": service._wrench({n: g[n] for n in root}, shifted),
            "root_interface_wrench": service._wrench({n: exerted[n] for n in root}, shifted),
            "beam_ground_wrench": service._wrench({model["beam_root"]: ground[model["beam_root"]]}, shifted),
            "shell_ground_wrench": service._wrench({n: ground[n] for n in shell_nodes}, shifted),
            "root_provenance": "First P0 support allocates interface action to fixed root nodes; "
                "root G alone is not actual ground. Beam root DOFs1..5 direct ground, DOF6 free. Root repartition retained.",
            "work_J": {"internal": internal_work, "applied": applied_work, "interface_exerted": interface_work,
                       "ground": ground_work, "constraint_resisting": constraint_work,
                       "virtual_exerted": virtual_exerted, "virtual_resisting": virtual_resisting},
            "scales": {"length_m": 1., "force_N": 10., "moment_Nm": 10., "work_J": work_scale,
                       "virtual_absolute_work_J": virtual_scale, "work_floor_J": 1e-12},
            "continuous_density_measures": measures, "checks": checks}


def validate_inventory(raw, strong, model, rows):
    """Only equations may change; full primary assembly command inventory retained."""
    for key in ("nodes", "elements", "fixes", "loads", "model_commands"):
        if raw[key] != strong[key]:
            raise InputIdentityError(f"fixed external {key} changed")
    if raw["equations"] != rows or len(strong["equations"]) != 160:
        raise InputIdentityError("exact 160-to-40 enforcement replacement required")
    if set(raw["poses"]) != set(model["nodes"]) or len(raw["element_global_covectors"]) != 96:
        raise InputIdentityError("complete 118-pose/96-element-covector inventory required")
    if any(len(q) != 6 or any(not math.isfinite(v) for v in q) for q in raw["poses"].values()):
        raise InputIdentityError("finite six-component primary nodal poses required")


def strong_input(folder, model, frozen, service):
    summary = json.loads((folder/"summary.json").read_text())
    raw = json.loads((folder/"raw-inventory.json").read_text())
    actions = json.loads((folder/"recovered-actions.json").read_text())
    for key in ("nodes", "elements", "fixes", "loads", "poses", "element_global_covectors"):
        raw[key] = {int(k): v for k, v in raw[key].items()}
    if (summary.get("status") != "completed" or summary.get("case") != "mz"
        or summary.get("source_sha256") != FROZEN_SOURCE_SHA
        or summary.get("service_sha256") != SERVICE_SHA
        or summary.get("reference_source_sha256") != REFERENCE_SHA
        or summary.get("binary_sha256") != service.BINARY_SHA256
        or raw["nodes"] != {n: list(xyz) for n, xyz in model["nodes"].items()}
        or raw["fixes"] != {n: list(flags) for n, flags in model["fixes"].items()}
        or raw["loads"] != {model["beam_tip"]: list(frozen.LOADS["mz"])}):
        raise InputIdentityError("completed frozen fixed-model strong Mz reference required")
    return raw, actions, {name: service._sha(folder/name) for name in
                          ("summary.json", "raw-inventory.json", "recovered-actions.json", "inputs.json", "controls.json")}


def comparison(raw, derived, strong, old_actions):
    old_work, work = old_actions["work_j"]["applied"], derived["work_J"]["applied"]
    components = {}
    for label, domain in (("shell", [n for n in raw["poses"] if n < 1001]),
                          ("beam", [n for n in raw["poses"] if n >= 1001])):
        for kind, slots in (("translation_m", range(3)), ("rotation_rad", range(3, 6))):
            differences = [raw["poses"][n][d]-strong["poses"][n][d] for n in domain for d in slots]
            denominator = max(math.sqrt(math.fsum(strong["poses"][n][d]**2 for n in domain for d in slots)), 1e-12)
            components[label+"_"+kind] = {"absolute_l2_nodal": math.sqrt(math.fsum(v*v for v in differences)),
                "relative_l2_nodal": math.sqrt(math.fsum(v*v for v in differences))/denominator,
                "maximum_absolute": max(map(abs, differences)), "denominator": denominator}
    density = derived["continuous_density_measures"]
    moments = {p: {"strong_station_atoms": old_actions["beam_connection_polynomial_wrench_moments"][p],
                   "P0_continuous_density": values,
                   "difference": [a-b for a, b in zip(values, old_actions["beam_connection_polynomial_wrench_moments"][p])]}
               for p, values in density["polynomial_x_moments"].items()}
    windows = {kind: {"strong_station_atoms": old_actions["beam_connection_fixed_region_025_075"][kind],
                      "P0_continuous_density": values,
                      "difference": [a-b for a, b in zip(values, old_actions["beam_connection_fixed_region_025_075"][kind])]}
               for kind, values in density["fixed_region_025_075"].items()}
    ground = {"strong": old_actions["ground_wrench_about_beam_root"],
              "P0": derived["ground_wrench_about_beam_root"]}
    roots = {"strong_G": old_actions["root_nodal_G_wrench_about_beam_root"],
             "strong_interface": old_actions["root_nodal_interface_wrench_about_beam_root"],
             "P0_G": derived["root_G_wrench"], "P0_interface": derived["root_interface_wrench"]}
    return {"applied_work_J": {"strong": old_work, "P0": work, "difference": work-old_work,
                               "relative_difference": (work-old_work)/max(abs(old_work), 1e-12)},
            "same_node_pose_sampling": components,
            "complete_ground_common_origin_wrench": ground, "root_G_interface_partition": roots,
            "beam_connection_polynomial_wrench_moments": moments,
            "beam_connection_fixed_region_025_075": windows,
            "limits": "Fixed external enforcement-space sensitivity only; no acceptance threshold on differences. "
                      "Nodal sample metrics are not continuum L2 or convergence. Strong nodal atoms and "
                      "continuous P0 fixed-window measures differ; full raw actions retained for comparison."}


def main(site, output, strong_folder):
    output.mkdir(parents=True, exist_ok=False)
    frozen, service, reference, source_paths = services()
    recorder, original_error = None, None
    summary = {"status": "failed", "classification": "fixed external P0 enforcement-space discriminator",
               "case": "mz", "python": sys.version, "source_sha256": service._sha(__file__),
               "frozen_sources": {str(p): service._sha(p) for p in source_paths},
               "requested_threads": {key: os.environ.get(key) for key in
                                     ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS")},
               "thread_scope": "Environment requests only. Effective OpenSees threads unresolved; "
                               "no resource-qualified performance or effective-thread claim.",
               "claim_scope": "Unchanged external K/material/model/support/load; only constraint space changes. "
                              "No native C substitution, mesh/refinement, finite native mechanics, 1% convergence or F03 acceptance."}
    try:
        for source, expected in zip(source_paths, (FROZEN_SOURCE_SHA, SERVICE_SHA, REFERENCE_SHA)):
            if service._sha(source) != expected:
                raise InputIdentityError(f"frozen source identity mismatch: {source}")
        model = frozen.geometry(reference)
        rows, supports = aggregate_rows(reference)
        strong, old_actions, old_hashes = strong_input(strong_folder, model, frozen, service)
        if strong["equations"] != frozen.equations(model, reference):
            raise InputIdentityError("saved strong equations must equal frozen construction")
        service._atomic(output/"inputs.json", {"model": model, "load": frozen.LOADS["mz"],
            "supports": supports, "constraint_rows": rows, "constraint_channels": ("x", "y", "z", "director_x", "director_y"),
            "arms_m": {"shell_top": reference.SHELL_THICKNESS_M/2., "beam_normal": reference.BEAM_BOTTOM_ARM_M},
            "strong_reference_dir": str(strong_folder.resolve()), "strong_reference_hashes": old_hashes,
            "source_binding": summary["frozen_sources"], "limits": summary["claim_scope"],
            "row_API": "Flat arbitrary(node,dof,coefficient) triples; first term unique nonzero dependent. "
                       "Homogeneous equations; original Lagrange1e9 scaling and BandGeneral/Linear unchanged."})
        control = controls(rows, supports, model, reference, frozen, service)
        service._atomic(output/"controls.json", control)
        values = control["six_common_rigid_field_average_gap_scaled"]+list(control["integrated_objective_average_gap_scaled"].values())
        if (len(control["six_common_rigid_field_average_gap_scaled"]) != 6
            or any(not math.isfinite(v) or v > GAP_LIMIT for v in values)
            or len(control["actual_left_exp_derivative_relative"]) != 3
            or any(not math.isfinite(v) or v > DERIVATIVE_LIMIT for v in control["actual_left_exp_derivative_relative"])
            or not control["normal_spin_columns_zero"] or not control["support_partition_integral_exact"]):
            raise PhysicalPredicateError("common reference/rigid/virgin derivative control failed")
        if sys.version_info[:2] != (3, 12):
            raise InputIdentityError("verified OpenSees binary requires Python3.12")
        sys.path.insert(0, str(site.resolve(strict=True)))
        import openseespy.opensees as ops
        from openseespywin import opensees as core
        summary.update(opensees=ops.version(), binary=str(Path(core.__file__).resolve()),
                       binary_sha256=service._sha(core.__file__))
        if not summary["opensees"].startswith("3.8") or summary["binary_sha256"] != service.BINARY_SHA256:
            raise InputIdentityError("verified OpenSees3.8 binary required")
        recorder = service.RecordingOps(ops)
        wrapper = RowReplacement(recorder, frozen.equations(model, reference), rows)
        frozen.solve(wrapper, model, reference, "mz")
        summary["row_replacement"] = {"original_commands_consumed": wrapper.consumed, "replacement_rows_emitted": wrapper.emitted}
        service._atomic(output/"raw-inventory.json", recorder.raw)
        if wrapper.consumed != 160 or wrapper.emitted != 40:
            raise InputIdentityError("complete nonmutating row replacement required")
        validate_inventory(recorder.raw, strong, model, rows)
        summary["all_non_equation_primary_commands_equal_strong"] = True
        derived = recover(recorder.raw, model, reference, rows, supports, frozen, service, output)
        service._atomic(output/"recovered-actions.json", derived)
        service._atomic(output/"enforcement-sensitivity.json", comparison(recorder.raw, derived, strong, old_actions))
        for name, value in derived["checks"].items():
            limit = GAP_LIMIT if name == "average_five_channel_gap_scaled" else BALANCE_LIMIT
            if not math.isfinite(value) or value > limit:
                raise PhysicalPredicateError(f"{name}={value} exceeds unchanged physical budget {limit}")
        summary["status"] = "completed"
    except BaseException as error:
        original_error = error
        summary["failure"] = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
        raise
    finally:
        cleanup_error = None
        if recorder is not None:
            for name, action in (("retain_raw", lambda: service._atomic(output/"raw-inventory.json", recorder.raw)),
                                 ("wipe", recorder.wipe)):
                try:
                    action()
                except BaseException as error:
                    cleanup_error = error
                    summary["status"] = "failed"
                    summary.setdefault("retention_cleanup_failures", []).append(
                        {"operation": name, "type": type(error).__name__, "message": str(error)})
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
    parser.add_argument("--site", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--strong-reference-dir", required=True, type=Path)
    args = parser.parse_args()
    main(args.site, args.output_dir, args.strong_reference_dir)

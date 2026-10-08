"""Retain one existing 16-interval five-channel OpenSees reference case.

No model command is added or changed. A transparent recorder calls the existing
direct-equation comparator once (Fy or Mx) in a fresh Python 3.12 process. This
is output retention and equilibrium recovery, not BL5/F03 qualification. The
reference has strong nodal ties; native BL5 has a weak retained-director trace.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import traceback


INTERVALS = 16
BINARY_SHA256 = "25ba42e1672526137d765d9c3631d1403e091f54f5afcdb9242f9243c63c3a96"
REFERENCE_FILE = "b3_e4_f03_bl5_opensees_line_reference.py"
BALANCE_LIMIT = 1e-8
GAP_LIMIT = 1e-9


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _atomic(path, value):
    # Nonfinite raw output must survive a failed predicate without becoming
    # nonstandard JSON. Successful reports contain finite numbers throughout.
    def safe(item):
        if isinstance(item, float) and not math.isfinite(item):
            return str(item)
        if isinstance(item, dict):
            return {str(k): safe(v) for k, v in item.items()}
        if isinstance(item, (list, tuple)):
            return [safe(v) for v in item]
        return item
    descriptor, temporary = tempfile.mkstemp(prefix=".retention-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(safe(value), stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _reference():
    path = Path(__file__).with_name(REFERENCE_FILE)
    spec = importlib.util.spec_from_file_location("_unchanged_bl5_reference", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


class RecordingOps:
    """Record existing calls/results without extra queries or model mutations."""

    def __init__(self, ops):
        self.ops = ops
        self.raw = {"nodes": {}, "elements": {}, "equations": [], "fixes": {},
                    "loads": {}, "poses": {}, "element_global_covectors": {},
                    "unverified_node_reaction_queries": {}, "model_commands": [],
                    "wipe_calls": 0}

    def __getattr__(self, name):
        method = getattr(self.ops, name)
        if name not in ("model", "section", "geomTransf", "constraints", "numberer",
                        "system", "test", "algorithm", "integrator", "analysis",
                        "timeSeries", "pattern"):
            return method
        def recorded(*args, **kwargs):
            self.raw["model_commands"].append([name, list(args), kwargs])
            return method(*args, **kwargs)
        return recorded

    def wipe(self):
        self.raw["wipe_calls"] += 1
        return self.ops.wipe()

    def node(self, tag, *xyz):
        self.raw["nodes"][int(tag)] = list(xyz)
        return self.ops.node(tag, *xyz)

    def element(self, kind, tag, *args):
        count = {"ASDShellQ4": 4, "ElasticTimoshenkoBeam": 2}[kind]
        self.raw["elements"][int(tag)] = {
            "kind": kind, "nodes": list(args[:count]), "arguments": list(args)}
        return self.ops.element(kind, tag, *args)

    def equationConstraint(self, *args):
        self.raw["equations"].append(list(args))
        return self.ops.equationConstraint(*args)

    def fix(self, tag, *flags):
        self.raw["fixes"][int(tag)] = list(flags)
        return self.ops.fix(tag, *flags)

    def load(self, tag, *values):
        self.raw["loads"][int(tag)] = list(values)
        return self.ops.load(tag, *values)

    def nodeDisp(self, tag):
        value = self.ops.nodeDisp(tag)
        self.raw["poses"][int(tag)] = list(value)
        return value

    def eleResponse(self, tag, response):
        value = self.ops.eleResponse(tag, response)
        if response == "globalForce":
            self.raw["element_global_covectors"][int(tag)] = list(value)
        return value

    def nodeReaction(self, tag):
        value = self.ops.nodeReaction(tag)
        self.raw["unverified_node_reaction_queries"][int(tag)] = list(value)
        return value


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b))


def _sum_nodal(elements, covectors, nodes, domain):
    terms = {node: [[] for _ in range(6)] for node in nodes}
    for tag, element in elements.items():
        if element["kind"] != domain:
            continue
        values = covectors[tag]
        for slot, node in enumerate(element["nodes"]):
            for axis in range(6):
                terms[node][axis].append(values[6*slot+axis])
    return {node: [math.fsum(row) for row in channels]
            for node, channels in terms.items()}


def _wrench(field, positions):
    force = [math.fsum(row[d] for row in field.values()) for d in range(3)]
    moment = [math.fsum(row[d+3]+_cross(positions[node], row[:3])[d]
                        for node, row in field.items()) for d in range(3)]
    return force+moment


def _solve5(matrix, rhs):
    rows = [list(row)+[value] for row, value in zip(matrix, rhs)]
    for column in range(5):
        pivot = max(range(column, 5), key=lambda row: abs(rows[row][column]))
        if rows[pivot][column] == 0.:
            raise ValueError("singular reference five-row beam work map")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        rows[column] = [value/divisor for value in rows[column]]
        for row in range(column+1, 5):
            coefficient = rows[row][column]
            rows[row] = [a-coefficient*b for a, b in zip(rows[row], rows[column])]
    result = [0.]*5
    for row in range(4, -1, -1):
        result[row] = rows[row][5]-math.fsum(
            rows[row][column]*result[column] for column in range(row+1, 5))
    return result


def recover(raw, reference, case):
    """Recover through actual recorded equation coefficients and global work."""
    model = reference.geometry(INTERVALS)
    nodes, poses = raw["nodes"], raw["poses"]
    shell_nodes = set(node for cell in model["shell_cells"] for node in cell)
    beam_nodes = set(node for cell in model["beam_cells"] for node in cell)
    primary = shell_nodes | beam_nodes
    if set(nodes) != primary or set(poses) != primary:
        raise ValueError("complete primary shell/beam pose inventory required")
    expected_elements = {
        **{i: ("ASDShellQ4", cell) for i, cell in enumerate(model["shell_cells"], 1)},
        **{100+i: ("ElasticTimoshenkoBeam", cell)
           for i, cell in enumerate(model["beam_cells"], 1)}}
    elements, forces = raw["elements"], raw["element_global_covectors"]
    if set(elements) != set(expected_elements) or set(forces) != set(elements):
        raise ValueError("complete unchanged element/covector inventory required")
    for tag, (kind, cell) in expected_elements.items():
        if elements[tag]["kind"] != kind or tuple(elements[tag]["nodes"]) != cell:
            raise ValueError("reference element connectivity changed")
        values = forces[tag]
        if len(values) != 6*len(cell) or not all(map(math.isfinite, values)):
            raise ValueError("finite global element covector required")
    for node in primary:
        if (nodes[node] != list(model["nodes"][node]) or len(poses[node]) != 6 or
                not all(map(math.isfinite, poses[node]))):
            raise ValueError("unchanged geometry and finite six-coordinate pose required")
    if raw["fixes"] != {node: [1]*6 for node in model["root_shell_nodes"]}:
        raise ValueError("unchanged shell-only root supports required")
    if raw["loads"] != {model["beam_tip"]: list(reference.LOADS[case])}:
        raise ValueError("unchanged declared beam-tip load required")
    equations = raw["equations"]
    if len(equations) != 5*(INTERVALS+1):
        raise ValueError("complete five-channel nodal equation inventory required")
    shell_g = _sum_nodal(elements, forces, shell_nodes, "ASDShellQ4")
    beam_g = _sum_nodal(elements, forces, beam_nodes, "ElasticTimoshenkoBeam")
    g = shell_g | beam_g
    zero = [0.]*6
    applied = {node: raw["loads"].get(node, zero) for node in primary}
    resisting_terms = {node: [[] for _ in range(6)] for node in primary}
    multipliers, equation_gaps = [], []
    # At each unsupported beam node: C_b.T lambda = L_b-G_b. The independent
    # sixth component (normal spin) remains a free-equilibrium predicate.
    for station, attachment in enumerate(model["attachments"]):
        shell, beam = attachment[:2]
        rows = equations[5*station:5*station+5]
        matrix = [[0.]*5 for _ in range(5)]
        for column, row in enumerate(rows):
            if len(row) % 3 or row[:3] != [beam, column+1, 1.]:
                raise ValueError("unique beam dependent term required")
            gap_terms = []
            for node, dof, coefficient in zip(row[::3], row[1::3], row[2::3]):
                if node not in (shell, beam) or dof not in range(1, 6):
                    raise ValueError("declared physical five-channel equation required")
                gap_terms.append(coefficient*poses[node][dof-1])
                if node == beam:
                    matrix[dof-1][column] += coefficient
            equation_gaps.append(math.fsum(gap_terms))
        rhs = [applied[beam][d]-beam_g[beam][d] for d in range(5)]
        lam = _solve5(matrix, rhs)
        multipliers.append({"shell_node": shell, "beam_node": beam,
                            "five_row_multipliers": lam})
        for row, value in zip(rows, lam):
            for node, dof, coefficient in zip(row[::3], row[1::3], row[2::3]):
                resisting_terms[node][dof-1].append(coefficient*value)
    resisting = {node: [math.fsum(values) for values in channels]
                 for node, channels in resisting_terms.items()}
    exerted = {node: [-value for value in row] for node, row in resisting.items()}
    residual = {node: [g[node][d]+resisting[node][d]-applied[node][d]
                       for d in range(6)] for node in primary}
    fixed = set(model["root_shell_nodes"])
    ground = {node: residual[node] for node in fixed}
    roots = {model["root_shell_nodes"][0], model["beam_cells"][0][0]}
    root_interface = {node: exerted[node] for node in roots}
    nonroot_interface = {node: row for node, row in exerted.items() if node not in roots}
    length_scale = reference.LENGTH_M
    load = reference.LOADS[case]
    force_scale = max(max(map(abs, load[:3])), max(map(abs, load[3:]))/length_scale)
    component_scales = [force_scale]*3+[force_scale*length_scale]*3
    free_error = max(abs(residual[node][d])/component_scales[d]
                     for node in primary-fixed for d in range(6))
    gap_error = max(abs(value)/(length_scale if index % 5 < 3 else 1.)
                    for index, value in enumerate(equation_gaps))
    interface_wrench = _wrench(exerted, nodes)
    ground_wrench = _wrench(ground, nodes)
    applied_wrench = _wrench(raw["loads"], nodes)
    wrench_error = max(abs(a+b)/scale for a, b, scale in
                       zip(ground_wrench, applied_wrench, component_scales))
    interface_error = max(abs(value)/scale for value, scale in
                          zip(interface_wrench, component_scales))
    station_interface_errors = []
    for shell, beam, *_ in model["attachments"]:
        wrench = _wrench({shell: exerted[shell], beam: exerted[beam]}, nodes)
        station_interface_errors.append(max(abs(value)/scale for value, scale in
                                           zip(wrench, component_scales)))
    internal_work = math.fsum(_dot(g[node], poses[node]) for node in primary)
    applied_work = math.fsum(_dot(applied[node], poses[node]) for node in primary)
    interface_work = math.fsum(_dot(exerted[node], poses[node]) for node in primary)
    ground_work = math.fsum(_dot(ground[node], poses[node]) for node in fixed)
    work_scale = max(abs(internal_work), abs(applied_work), 1e-12)
    work_error = abs(internal_work-applied_work-interface_work-ground_work)/work_scale
    internal_applied_error = abs(internal_work-applied_work)/work_scale
    compatible_interface_work_error = abs(interface_work)/work_scale
    constraint_work = math.fsum(value*gap for item, gaps in zip(
        multipliers, (equation_gaps[i:i+5] for i in range(0, len(equation_gaps), 5)))
        for value, gap in zip(item["five_row_multipliers"], gaps))
    dual_error = abs(interface_work+constraint_work)/work_scale
    # A noncompatible virtual field exercises the work map beyond the solved
    # state, where almost-zero connection work could conceal a sign error.
    virtual = {node: [(.01*length_scale if d < 3 else .01)*
                      math.sin((node+1)*(d+1)) for d in range(6)] for node in primary}
    virtual_gaps = [math.fsum(c*virtual[n][d-1] for n, d, c in
                             zip(row[::3], row[1::3], row[2::3])) for row in equations]
    virtual_resisting_work = math.fsum(value*gap for item, gaps in zip(
        multipliers, (virtual_gaps[i:i+5] for i in range(0, len(virtual_gaps), 5)))
        for value, gap in zip(item["five_row_multipliers"], gaps))
    virtual_exerted_work = math.fsum(_dot(exerted[n], virtual[n]) for n in primary)
    # Use absolute contributions for this arbitrary signed virtual field;
    # cancellation of its total work is not a physical normalization scale.
    virtual_scale = max(
        math.fsum(abs(exerted[n][d]*virtual[n][d]) for n in primary for d in range(6)),
        math.fsum(abs(value*gap) for item, gaps in zip(
            multipliers, (virtual_gaps[i:i+5] for i in range(0, len(virtual_gaps), 5)))
            for value, gap in zip(item["five_row_multipliers"], gaps)), 1e-12)
    virtual_dual_error = abs(virtual_exerted_work+virtual_resisting_work)/virtual_scale
    return {
        "sign_convention": {"G": "global element resisting covector",
            "L": "applied load", "connection_resisting": "C.T lambda = L-G on free beam",
            "connection_exerted_load": "-C.T lambda = G-L on free beam",
            "ground_exerted_load": "G+C.T lambda-L on fixed shell coordinates"},
        "multiplier_derivation": "solve recorded local five-row beam transpose map; no raw multiplier query",
        "multipliers": multipliers, "shell_domain_nodal_G": shell_g,
        "beam_domain_nodal_G": beam_g, "connection_resisting_covectors": resisting,
        "connection_exerted_loads": exerted, "root_connection_exerted_loads": root_interface,
        "nonroot_connection_exerted_loads": nonroot_interface,
        "ground_exerted_loads": ground, "free_equilibrium_residuals": {
            node: residual[node] for node in primary-fixed},
        "equation_gaps": equation_gaps, "root_interface_wrench_about_origin": _wrench(root_interface, nodes),
        "root_shell_interface_wrench_about_origin": _wrench(
            {node: row for node, row in root_interface.items() if node in shell_nodes}, nodes),
        "root_beam_interface_wrench_about_origin": _wrench(
            {node: row for node, row in root_interface.items() if node in beam_nodes}, nodes),
        "nonroot_interface_wrench_about_origin": _wrench(nonroot_interface, nodes),
        "total_interface_wrench_about_origin": interface_wrench,
        "ground_wrench_about_origin": ground_wrench, "applied_wrench_about_origin": applied_wrench,
        "work_j": {"internal": internal_work, "applied": applied_work,
                   "interface_exerted": interface_work, "ground": ground_work,
                   "constraint_resisting": constraint_work,
                   "virtual_exerted": virtual_exerted_work, "virtual_resisting": virtual_resisting_work},
        "virtual_field": virtual, "scales": {"length_m": length_scale,
            "force_n": force_scale, "moment_nm": force_scale*length_scale,
            "work_floor_j": 1e-12, "physical_work_j": work_scale,
            "virtual_absolute_contribution_work_j": virtual_scale},
        "checks": {"free_equilibrium_scaled": free_error, "five_channel_gap_scaled": gap_error,
            "ground_applied_wrench_scaled": wrench_error, "interface_action_reaction_scaled": interface_error,
            "maximum_station_action_reaction_scaled": max(station_interface_errors),
            "physical_work_relative": work_error, "solved_dual_work_relative": dual_error,
            "internal_applied_work_relative": internal_applied_error,
            "compatible_interface_work_relative": compatible_interface_work_error,
            "noncompatible_virtual_dual_work_relative": virtual_dual_error},
        "station_action_reaction_errors_scaled": station_interface_errors,
        "root_provenance": "root beam remains unsupported; five root equations transfer into fixed shell. "
            "With the shell root fixed, replacing them by direct beam DOFs1..5 preserves this nodal "
            "kinematics and free normal spin, but reclassifies that load as beam ground support. "
            "No such replacement is made here.",
    }


def main(site, output, case):
    output.mkdir(parents=True, exist_ok=False)
    recorder = None
    summary = {"classification": "fixed-mesh matched-reference output retention; development only",
               "case": case, "intervals": INTERVALS, "constraint_form": "direct",
               "source_sha256": _sha(__file__), "python": sys.version,
               "status": "failed", "failure": None,
               "requested_thread_environment": {name: os.environ.get(name) for name in
                   ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
               "thread_scope": "environment requests only; no effective OpenSees thread claim"}
    try:
        reference, source = _reference()
        summary["reference_source_sha256"] = _sha(source)
        _atomic(output/"inputs.json", {"case": case, "intervals": INTERVALS,
            "load": reference.LOADS[case], "geometry": reference.geometry(INTERVALS),
            "constraint_form": "direct", "reference_source": str(source),
            "reference_source_sha256": summary["reference_source_sha256"]})
        if sys.version_info[:2] != (3, 12):
            raise RuntimeError("verified OpenSees binary requires Python 3.12")
        sys.path.insert(0, str(site.resolve(strict=True)))
        import openseespy.opensees as ops
        from openseespywin import opensees as core
        summary.update(opensees=ops.version(), binary=str(Path(core.__file__).resolve()),
                       binary_sha256=_sha(core.__file__))
        if not summary["opensees"].startswith("3.8") or summary["binary_sha256"] != BINARY_SHA256:
            raise RuntimeError("unchanged verified OpenSees 3.8 binary required")
        recorder = RecordingOps(ops)
        historical = reference.solve(recorder, INTERVALS, case, constraint_form="direct")
        recorder.raw["historical_summary"] = historical
        # Raw inventory survives every later recovery/predicate failure.
        _atomic(output/"raw-inventory.json", recorder.raw)
        derived = recover(recorder.raw, reference, case)
        _atomic(output/"recovered-actions.json", derived)
        for name, value in derived["checks"].items():
            limit = GAP_LIMIT if name == "five_channel_gap_scaled" else BALANCE_LIMIT
            if not math.isfinite(value) or value > limit:
                raise ValueError(f"reference output predicate failed: {name}={value} > {limit}")
        summary["status"] = "completed"
    except BaseException as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc),
                              "traceback": traceback.format_exc()}
        raise
    finally:
        if recorder is not None:
            _atomic(output/"raw-inventory.json", recorder.raw)
        _atomic(output/"summary.json", summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--case", choices=("fy", "mx"), required=True)
    args = parser.parse_args()
    main(args.site, args.output_dir, args.case)

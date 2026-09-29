"""Bounded independent OpenSeesPy screen for the M1 elastic point panel.

This development screen does not qualify E01. Its beam section and nodal
connection match the reference-linear native model, while the shell element
is independent and requires convergence/physical-idealization assessment.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys


E = 210e9
NU = .3
G = E / (2 * (1 + NU))
AREA = .01
SHEAR_AREA = .008
SECOND_MOMENT = 8.333333333333333e-6
TORSION = 1.6666666666666667e-5
SHELL_THICKNESS = .07
LOAD_N = 1000.
def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _sha(path: Path):
    return sha256(path.read_bytes()).hexdigest()


def solve(ops, sign: int, intervals: int):
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)
    upper_start = intervals + 2
    tip_node = 101 + 2 * intervals
    shell_nodes = {
        **{1 + i: (2. * i / intervals, -.5, 0.)
           for i in range(intervals + 1)},
        **{upper_start + i: (2. * i / intervals, .5, 0.)
           for i in range(intervals + 1)},
    }
    beam_nodes = {101 + i: (i / intervals, -.5, sign * .1)
                  for i in range(2 * intervals + 1)}
    nodes = shell_nodes | beam_nodes
    pairs = tuple((1 + i, 101 + 2 * i) for i in range(intervals + 1))
    for tag, xyz in nodes.items():
        ops.node(tag, *xyz)

    ops.section("ElasticMembranePlateSection", 1, E, NU,
                SHELL_THICKNESS, 7850.)
    for i in range(intervals):
        ops.element("ASDShellQ4", 1 + i,
                    1 + i, 2 + i, upper_start + i + 1,
                    upper_start + i, 1)
    ops.geomTransf("Linear", 1, 0., 0., 1.)
    for i in range(2 * intervals):
        ops.element("ElasticTimoshenkoBeam", intervals + 1 + i,
                    101 + i, 102 + i,
                    E, G, AREA, TORSION, SECOND_MOMENT, SECOND_MOMENT,
                    SHEAR_AREA, SHEAR_AREA, 1)
    for shell, beam in pairs:
        ops.rigidLink("beam", shell, beam)
    for tag in (1, upper_start):
        ops.fix(tag, 1, 1, 1, 1, 1, 1)

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    ops.load(tip_node, LOAD_N, 0., 0., 0., 0., 0.)
    # The fixed shell root also retains a rigid link. OpenSees documents that
    # Transformation does not follow such chained constraints; exact Lagrange
    # equations retain this supported point law without a penalty.
    ops.constraints("Lagrange", 1e9, 1e9)
    ops.numberer("RCM")
    ops.system("BandGeneral")
    ops.test("NormUnbalance", 1e-8, 20)
    ops.algorithm("Linear")
    ops.integrator("LoadControl", 1.)
    ops.analysis("Static")
    code = ops.analyze(1)
    if code != 0:
        raise RuntimeError(f"OpenSees analyze returned {code}")
    ops.reactions()
    disp = {tag: tuple(float(v) for v in ops.nodeDisp(tag)) for tag in nodes}
    printed_support = {tag: tuple(float(v) for v in ops.nodeReaction(tag))
                       for tag in (1, upper_start)}
    beam_root_force = tuple(float(v) for v in ops.eleResponse(
        intervals + 1, "globalForce"))
    if len(beam_root_force) != 12 or not all(map(math.isfinite, beam_root_force)):
        raise ValueError("global beam-end resisting-force inventory required")
    arm = tuple(nodes[101][d] - nodes[1][d] for d in range(3))
    arm_moment = _cross(arm, beam_root_force[:3])
    support = {
        1: tuple(printed_support[1][d] + beam_root_force[d]
                 for d in range(3))
        + tuple(printed_support[1][d + 3] + beam_root_force[d + 3]
                + arm_moment[d] for d in range(3)),
        upper_start: printed_support[upper_start],
    }
    if any(len(row) != 6 or not all(map(math.isfinite, row))
           for row in (*disp.values(), *support.values(),
                       *printed_support.values())):
        raise ValueError("finite six-coordinate nodal output required")

    gap = 0.
    for shell, beam in pairs:
        arm = tuple(nodes[beam][d] - nodes[shell][d] for d in range(3))
        predicted = _cross(disp[shell][3:], arm)
        gap = max(gap, *(abs(disp[beam][d] - disp[shell][d] - predicted[d])
                         for d in range(3)),
                  *(abs(disp[beam][d] - disp[shell][d]) for d in (3, 4, 5)))
    tip = disp[tip_node]
    if not any(abs(v) > 1e-15 for v in tip[:3]):
        raise ValueError("zero tip response to applied load")
    internal_work = 0.
    for i in range(intervals):
        shell_element_nodes = (1 + i, 2 + i, upper_start + i + 1,
                               upper_start + i)
        for element, element_nodes in (
                (1 + i, shell_element_nodes),
                (intervals + 1 + 2 * i,
                 (101 + 2 * i, 102 + 2 * i)),
                (intervals + 2 + 2 * i,
                 (102 + 2 * i, 103 + 2 * i))):
            forces = tuple(float(v) for v in ops.eleResponse(
                element, "globalForce"))
            if len(forces) != 6 * len(element_nodes):
                raise ValueError("element global resisting-force inventory")
            internal_work += sum(disp[node][d] * forces[6 * j + d]
                                 for j, node in enumerate(element_nodes)
                                 for d in range(6))
    external_work = LOAD_N * tip[0]
    work_error = abs(internal_work - external_work)
    force = tuple(sum(support[tag][d] for tag in support) for d in range(3))
    moment = tuple(sum(support[tag][d + 3]
                       + _cross(nodes[tag], support[tag][:3])[d]
                       for tag in support) for d in range(3))
    applied_moment = _cross(nodes[tip_node], (LOAD_N, 0., 0.))
    force_error = max(abs(force[d] + (LOAD_N if d == 0 else 0.))
                      for d in range(3))
    moment_error = max(abs(moment[d] + applied_moment[d]) for d in range(3))
    if (gap > 1e-10 or force_error > 1e-4 or moment_error > 1e-4
            or work_error > 1e-8 * abs(external_work)):
        raise ValueError(f"link gap/support wrench failed: {gap=:.6g}, "
                         f"{force_error=:.6g}, {moment_error=:.6g}, "
                         f"{work_error=:.6g}")
    return {
        "offset_sign": sign, "shell_intervals": intervals,
        "point_stations": len(pairs), "tip_translation_m": tip[:3],
        "tip_rotation_rad": tip[3:], "support_reactions": support,
        "printed_support_reactions": printed_support,
        "beam_root_global_end_force": beam_root_force[:6],
        "maximum_link_gap": gap,
        "support_force_residual_n": force_error,
        "support_moment_residual_nm": moment_error,
        "element_internal_virtual_work_j": internal_work,
        "applied_virtual_work_j": external_work,
        "virtual_work_difference_j": work_error,
        "node_displacements": disp,
    }


def main(site: Path, output: Path, intervals: int):
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("the installed OpenSeesPy binary requires Python 3.12")
    if intervals not in (2, 4, 8):
        raise ValueError("bounded screen admits 2, 4, or 8 intervals")
    if output.exists():
        raise FileExistsError("preserve previous external screen")
    sys.path.insert(0, str(site))
    import openseespy.opensees as ops
    from openseespywin import opensees as core

    output.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "classification": "E01 independent development screen; not accepted",
        "python": sys.version.split()[0], "opensees": ops.version(),
        "binary": str(Path(core.__file__).resolve()),
        "binary_sha256": _sha(Path(core.__file__)),
        "source_sha256": _sha(Path(__file__)),
        "model": "M1 flat Q4 point panel; ASDShellQ4 and elastic Timoshenko beam",
        "load": "+1000 N x at beam tip; linear elastic",
        "joint": "OpenSees 3D rigidLink beam, shell retained and beam constrained",
        "shell_intervals": intervals,
        "cases": [], "failure": None,
    }
    try:
        for sign in (-1, 1):
            record["cases"].append(solve(ops, sign, intervals))
    except Exception as exc:
        record["failure"] = f"{type(exc).__name__}: {exc}"
    finally:
        ops.wipe()
        output.write_text(json.dumps(record, indent=2, sort_keys=True,
                                     allow_nan=False) + "\n", encoding="utf-8")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--intervals", type=int, default=2)
    args = parser.parse_args()
    result = main(args.site, args.output, args.intervals)
    print(json.dumps({"failure": result["failure"],
                      "intervals": result["shell_intervals"],
                      "cases": len(result["cases"]),
                      "max_force_error_n": max((v["support_force_residual_n"]
                                                for v in result["cases"]),
                                               default=None),
                      "max_moment_error_nm": max((v["support_moment_residual_nm"]
                                                  for v in result["cases"]),
                                                 default=None)}))
    if result["failure"]:
        raise SystemExit(1)

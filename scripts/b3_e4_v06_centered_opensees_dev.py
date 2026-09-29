"""Independent OpenSees point-rib counterpart to the centered V06 screen."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys


E = 210e9
NU = .3
G = E/(2.*(1.+NU))
LENGTH = 2.
WIDTH = .2
THICKNESS = .07
AREA = .01
IY = 8.333333333333333e-6
IX = 1.6666666666666667e-5
SHEAR_AREA = .008
OFFSET = .1
LOADS = ((1000., 0.), (0., 100.), (1000., 100.))


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def _sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def solve(ops, intervals: int, sign: int, force: float, moment: float):
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)
    def shell_id(row, col):
        return 1+row*(intervals+1)+col
    nodes = {shell_id(row, col):
             (LENGTH*col/intervals, WIDTH*(row/intervals-.5), 0.)
             for row in range(intervals+1) for col in range(intervals+1)}
    beam = {101+i: (LENGTH*i/(2*intervals), 0., sign*OFFSET)
            for i in range(2*intervals+1)}
    nodes.update(beam)
    root_nodes = tuple(shell_id(row, 0) for row in range(intervals+1))
    pairs = tuple((shell_id(intervals//2, col), 101+2*col)
                  for col in range(intervals+1))
    for node, xyz in nodes.items():
        ops.node(node, *xyz)
    ops.section("ElasticMembranePlateSection", 1, E, NU, THICKNESS, 7850.)
    shell_count = intervals*intervals
    elements = []
    for row in range(intervals):
        for col in range(intervals):
            eid = 1+row*intervals+col
            corners = (shell_id(row, col), shell_id(row, col+1),
                       shell_id(row+1, col+1), shell_id(row+1, col))
            ops.element("ASDShellQ4", eid, *corners, 1)
            elements.append((eid, corners))
    ops.geomTransf("Linear", 1, 0., 0., 1.)
    for col in range(2*intervals):
        eid = shell_count+1+col
        ends = (101+col, 102+col)
        ops.element("ElasticTimoshenkoBeam", eid, *ends,
                    E, G, AREA, IX, IY, IY, SHEAR_AREA, SHEAR_AREA, 1)
        elements.append((eid, ends))
    for shell, beam_node in pairs:
        ops.rigidLink("beam", shell, beam_node)
    for node in root_nodes:
        ops.fix(node, 1, 1, 1, 1, 1, 1)
    tip = 101+2*intervals
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    ops.load(tip, force, 0., 0., 0., moment, 0.)
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
    disp = {node: tuple(float(v) for v in ops.nodeDisp(node))
            for node in nodes}
    support = {node: tuple(float(v) for v in ops.nodeReaction(node))
               for node in root_nodes}
    first_beam = tuple(float(v) for v in ops.eleResponse(
        shell_count+1, "globalForce"))
    if len(first_beam) != 12:
        raise ValueError("beam root end-force inventory required")
    root_shell = pairs[0][0]
    arm = tuple(nodes[101][i]-nodes[root_shell][i] for i in range(3))
    arm_moment = _cross(arm, first_beam[:3])
    support[root_shell] = (
        tuple(support[root_shell][d]+first_beam[d] for d in range(3))+
        tuple(support[root_shell][d+3]+first_beam[d+3]+arm_moment[d]
              for d in range(3)))
    gap = 0.
    for shell, beam_node in pairs:
        arm = tuple(nodes[beam_node][d]-nodes[shell][d] for d in range(3))
        predicted = _cross(disp[shell][3:], arm)
        gap = max(gap, *(abs(disp[beam_node][d]-disp[shell][d]-predicted[d])
                         for d in range(3)),
                  *(abs(disp[beam_node][d]-disp[shell][d]) for d in (3, 4, 5)))
    internal_work = 0.
    for eid, element_nodes in elements:
        forces = tuple(float(v) for v in ops.eleResponse(eid, "globalForce"))
        if len(forces) != 6*len(element_nodes):
            raise ValueError("complete element-force inventory required")
        internal_work += sum(disp[node][d]*forces[6*j+d]
                             for j, node in enumerate(element_nodes)
                             for d in range(6))
    tip_disp = disp[tip]
    mid = intervals//2
    section_strain = []
    section_curvature = []
    for row in range(intervals+1):
        left = disp[shell_id(row, mid-1)]
        right = disp[shell_id(row, mid)]
        dx = LENGTH/intervals
        section_strain.append((right[0]-left[0])/dx)
        section_curvature.append((right[4]-left[4])/dx)
    applied_work = force*tip_disp[0]+moment*tip_disp[4]
    total_force = tuple(sum(row[d] for row in support.values())
                        for d in range(3))
    total_moment = tuple(sum(row[d+3]+_cross(nodes[node], row[:3])[d]
                             for node, row in support.items())
                         for d in range(3))
    applied_moment = tuple((moment if d == 1 else 0.)+
                           _cross(nodes[tip], (force, 0., 0.))[d]
                           for d in range(3))
    force_error = max(abs(total_force[d]+(force if d == 0 else 0.))
                      for d in range(3))
    moment_error = max(abs(total_moment[d]+applied_moment[d])
                       for d in range(3))
    work_error = abs(internal_work-applied_work)
    if (not all(math.isfinite(v) for row in disp.values() for v in row) or
            gap > 1e-10 or force_error > 1e-4 or moment_error > 1e-4 or
            work_error > 1e-8*max(abs(applied_work), 1e-12)):
        raise ValueError(f"point/work/wrench check failed: {gap=}, "
                         f"{force_error=}, {moment_error=}, {work_error=}")
    return {"shell_intervals": intervals,
            "transverse_intervals": intervals,
            "offset_sign": sign,
            "beam_tip_force_x_n": force,
            "beam_tip_moment_y_nm": moment,
            "tip_x_m": tip_disp[0],
            "tip_ry_rad": tip_disp[4],
            "center_section_shell_axial_strain_by_row": section_strain,
            "center_section_shell_curvature_by_row": section_curvature,
            "point_gap_max": gap,
            "support_force_error_n": force_error,
            "support_moment_error_nm": moment_error,
            "applied_work_j": applied_work,
            "internal_work_j": internal_work,
            "work_error_j": work_error}


def main(site: Path, output: Path):
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("pinned OpenSees binary requires Python 3.12")
    if output.exists():
        raise FileExistsError("preserve prior centered-rib evidence")
    sys.path.insert(0, str(site))
    import openseespy.opensees as ops
    from openseespywin import opensees as core
    record = {
        "classification": "V06 independent centered rib; development only",
        "source_sha256": _sha(__file__),
        "binary_sha256": _sha(core.__file__),
        "python": sys.version.split()[0],
        "opensees_version": ops.version(),
        "model": "ASDShellQ4 plus ElasticTimoshenkoBeam, exact point Lagrange",
        "geometry": {"length_m": LENGTH, "width_m": WIDTH,
                     "shell_thickness_m": THICKNESS,
                     "beam_area_m2": AREA, "beam_iy_m4": IY,
                     "offset_m": OFFSET},
        "cases": [], "failure": None,
    }
    try:
        for n in (2, 4, 8):
            for sign in (-1, 1):
                for force, moment in LOADS:
                    record["cases"].append(solve(ops, n, sign, force, moment))
    except Exception as exc:
        record["failure"] = f"{type(exc).__name__}: {exc}"
    finally:
        ops.wipe()
        output.write_text(json.dumps(record, indent=2, sort_keys=True,
                                     allow_nan=False)+"\n", encoding="utf-8")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = main(args.site, args.output)
    print(json.dumps({"failure": result["failure"],
                      "completed_cases": len(result["cases"])}))
    if result["failure"]:
        raise SystemExit(1)

"""Independent five-channel nodal line comparator for the BL5 development law.

The physical offsets and five tied channels match BL5's first variation on
rigid shell/beam pose fields. Strong nodal ties and ASDShellQ4 remain different
discretizations from the native weak E4-PL/B3 system. This is not F03 acceptance.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sys


E_PA = 210e9
NU = .3
G_PA = E_PA/(2*(1+NU))
SHELL_THICKNESS_M = .035
BEAM_AXIS_Z_M = .0675
BEAM_BOTTOM_ARM_M = -.05
LENGTH_M = 1.
WIDTH_M = .2
BEAM_AREA_M2 = .01
BEAM_SHEAR_AREA_M2 = .008
BEAM_TORSION_M4 = 1.6666666666666667e-5
BEAM_BENDING_M4 = 8.333333333333333e-6
LEVELS = (4, 8, 16)
LOADS = {"fy": (0., 100., 0., 0., 0., 0.),
         "mx": (0., 0., 0., 10., 0., 0.)}


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def geometry(intervals: int) -> dict:
    """Frozen flat-strip topology; no solver import or numerical work."""
    if type(intervals) is not int or intervals not in LEVELS:
        raise ValueError("bounded BL5 comparator level required")
    nodes = {}
    for row, y in enumerate((0., WIDTH_M)):
        for index in range(intervals+1):
            nodes[1+row*(intervals+1)+index] = (
                LENGTH_M*index/intervals, y, 0.)
    shell_cells = tuple(
        (1+i, 2+i, intervals+3+i, intervals+2+i)
        for i in range(intervals))
    beam_cells = tuple((1001+i, 1002+i) for i in range(intervals))
    attachments = []
    for index in range(intervals+1):
        x = LENGTH_M*index/intervals
        shell, beam = 1+index, 1001+index
        shell_aux, beam_aux = 2001+index, 3001+index
        nodes[beam] = (x, 0., BEAM_AXIS_Z_M)
        nodes[shell_aux] = (x, 0., SHELL_THICKNESS_M/2)
        nodes[beam_aux] = (x, 0., BEAM_AXIS_Z_M+BEAM_BOTTOM_ARM_M)
        if any(abs(a-b) > 1e-14 for a, b in
               zip(nodes[shell_aux], nodes[beam_aux])):
            raise AssertionError("shell-top and beam-bottom attachment mismatch")
        attachments.append((shell, beam, shell_aux, beam_aux))
    return {"nodes": nodes, "shell_cells": shell_cells,
            "beam_cells": beam_cells, "attachments": tuple(attachments),
            "root_shell_nodes": (1, intervals+2),
            "beam_tip": 1001+intervals}


def _element_forces(ops, element_id, connectivity):
    values = tuple(float(v) for v in ops.eleResponse(
        element_id, "globalForce"))
    if len(values) != 6*len(connectivity) or not all(map(math.isfinite, values)):
        raise ValueError("finite global element-force inventory required")
    return values


def solve(ops, intervals: int, case: str, *, constraint_form: str) -> dict:
    if case not in LOADS:
        raise ValueError("declared Fy or Mx reference load required")
    if constraint_form not in ("chain", "direct"):
        raise ValueError("declared constraint form required")
    model = geometry(intervals)
    nodes = model["nodes"]
    active_nodes = {tag: xyz for tag, xyz in nodes.items()
                    if constraint_form == "chain" or tag < 2000}
    ops.wipe()
    try:
        ops.model("basic", "-ndm", 3, "-ndf", 6)
        for tag, xyz in active_nodes.items():
            ops.node(tag, *xyz)
        ops.section("ElasticMembranePlateSection", 1, E_PA, NU,
                    SHELL_THICKNESS_M, 7850.)
        for index, connectivity in enumerate(model["shell_cells"], 1):
            ops.element("ASDShellQ4", index, *connectivity, 1)
        ops.geomTransf("Linear", 1, 0., 0., 1.)
        for index, connectivity in enumerate(model["beam_cells"], 1):
            ops.element("ElasticTimoshenkoBeam", 100+index,
                        *connectivity, E_PA, G_PA, BEAM_AREA_M2,
                        BEAM_TORSION_M4, BEAM_BENDING_M4, BEAM_BENDING_M4,
                        BEAM_SHEAR_AREA_M2, BEAM_SHEAR_AREA_M2, 1)
        for shell, beam, shell_aux, beam_aux in model["attachments"]:
            if constraint_form == "chain":
                ops.rigidLink("beam", shell, shell_aux)
                ops.rigidLink("beam", beam, beam_aux)
                ops.equalDOF(shell_aux, beam_aux, 1, 2, 3, 4, 5)
            else:
                # u_b + theta_b x r_b = u_s + theta_s x r_s;
                # theta_bx/y = theta_sx/y. This is the same linear work
                # space as the auxiliary chain, without chained MP nodes.
                rb = BEAM_BOTTOM_ARM_M
                rs = SHELL_THICKNESS_M/2
                ops.equationConstraint(beam, 1, 1., shell, 1, -1.,
                                       beam, 5, rb, shell, 5, -rs)
                ops.equationConstraint(beam, 2, 1., shell, 2, -1.,
                                       beam, 4, -rb, shell, 4, rs)
                ops.equationConstraint(beam, 3, 1., shell, 3, -1.)
                ops.equationConstraint(beam, 4, 1., shell, 4, -1.)
                ops.equationConstraint(beam, 5, 1., shell, 5, -1.)
        for tag in model["root_shell_nodes"]:
            ops.fix(tag, 1, 1, 1, 1, 1, 1)
        ops.timeSeries("Linear", 1)
        ops.pattern("Plain", 1, 1)
        load = LOADS[case]
        ops.load(model["beam_tip"], *load)
        # The auxiliary chain intentionally has overlapping MP equations;
        # enforce the complete set rather than applying a transformation
        # handler that assumes an unchained retained-node graph.
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
        displacement = {tag: tuple(float(v) for v in ops.nodeDisp(tag))
                        for tag in active_nodes}
        if any(len(row) != 6 or not all(map(math.isfinite, row))
               for row in displacement.values()):
            raise ValueError("finite six-DOF external displacement required")
        max_gap = 0.
        max_rigid_gap = 0.
        for shell, beam, shell_aux, beam_aux in model["attachments"]:
            if constraint_form == "chain":
                shell_u, beam_u = displacement[shell_aux], displacement[beam_aux]
                max_gap = max(max_gap, *(abs(shell_u[d]-beam_u[d])
                                         for d in range(5)))
                for primary, auxiliary in ((shell, shell_aux), (beam, beam_aux)):
                    arm = tuple(nodes[auxiliary][d]-nodes[primary][d]
                                for d in range(3))
                    expected = tuple(displacement[primary][d]+v for d, v in
                                     enumerate(_cross(displacement[primary][3:], arm)))
                    max_rigid_gap = max(
                        max_rigid_gap,
                        *(abs(displacement[auxiliary][d]-expected[d])
                          for d in range(3)),
                        *(abs(displacement[auxiliary][d+3]-displacement[primary][d+3])
                          for d in range(3)))
            else:
                su, bu = displacement[shell], displacement[beam]
                rb, rs = BEAM_BOTTOM_ARM_M, SHELL_THICKNESS_M/2
                gap = (bu[0]+rb*bu[4]-su[0]-rs*su[4],
                       bu[1]-rb*bu[3]-su[1]+rs*su[3],
                       bu[2]-su[2], bu[3]-su[3], bu[4]-su[4])
                max_gap = max(max_gap, *(abs(value) for value in gap))
        internal_work = 0.
        support_force = [0., 0., 0.]
        support_moment = [0., 0., 0.]
        shell_work = 0.
        beam_work = 0.
        ops.reactions()
        for node in model["root_shell_nodes"]:
            reaction = tuple(float(v) for v in ops.nodeReaction(node))
            if len(reaction) != 6 or not all(map(math.isfinite, reaction)):
                raise ValueError("finite root-node reaction required")
            arm = _cross(nodes[node], reaction[:3])
            for axis in range(3):
                support_force[axis] += reaction[axis]
                support_moment[axis] += reaction[axis+3]+arm[axis]
        for domain, elements in (("shell", model["shell_cells"]),
                                 ("beam", model["beam_cells"])):
            for index, connectivity in enumerate(elements, 1):
                tag = index if domain == "shell" else 100+index
                forces = _element_forces(ops, tag, connectivity)
                work = sum(displacement[node][d]*forces[6*j+d]
                           for j, node in enumerate(connectivity)
                           for d in range(6))
                internal_work += work
                if domain == "shell":
                    shell_work += work
                else:
                    beam_work += work
        tip = displacement[model["beam_tip"]]
        applied_work = sum(a*b for a, b in zip(load, tip))
        applied_moment = tuple(load[d+3]+v for d, v in enumerate(
            _cross(nodes[model["beam_tip"]], load[:3])))
        force_error = max(abs(a+b) for a, b in zip(support_force, load[:3]))
        moment_error = max(abs(a+b) for a, b in zip(
            support_moment, applied_moment))
        work_error = abs(internal_work-applied_work)
        if (max_gap > 1e-9 or max_rigid_gap > 1e-9 or
                force_error > 1e-5 or moment_error > 1e-5 or
                work_error > 1e-8*max(abs(applied_work), 1e-12)):
            raise ValueError("external five-channel gap, balance or work failed: "
                             f"{max_gap=}, {max_rigid_gap=}, {force_error=}, "
                             f"{moment_error=}, {work_error=}")
        return {"intervals": intervals, "case": case,
                "constraint_form": constraint_form,
                "shell_elements": len(model["shell_cells"]),
                "beam_elements": len(model["beam_cells"]),
                "pointwise_constraint_rows": 5*len(model["attachments"]),
                "tip_translation_m": tip[:3],
                "tip_rotation_rad": tip[3:],
                "applied_work_j": applied_work,
                "shell_internal_work_j": shell_work,
                "beam_internal_work_j": beam_work,
                "max_five_channel_gap": max_gap,
                "max_rigid_link_gap": max_rigid_gap,
                "support_force_error_n": force_error,
                "support_moment_error_nm": moment_error,
                "internal_applied_work_error_j": work_error}
    finally:
        ops.wipe()


def main(site: Path, output: Path, *, canary: bool = False,
         constraint_form: str = "chain"):
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("pinned OpenSeesPy binary requires Python 3.12")
    if output.exists():
        raise FileExistsError("preserve prior external reference evidence")
    sys.path.insert(0, str(site.resolve()))
    import openseespy.opensees as ops
    from openseespywin import opensees as core

    result = {"classification": "BL5 five-channel nodal comparator; development only",
              "constraint_form": constraint_form,
              "scope": "constraint canary n4 Fy" if canary else "4/8/16 Fy/Mx",
              "opensees": ops.version(), "python": sys.version.split()[0],
              "binary": str(Path(core.__file__).resolve()),
              "binary_sha256": sha256(Path(core.__file__).read_bytes()).hexdigest(),
              "runner_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
              "requested_threads": {name: os.environ.get(name)
                                    for name in ("OMP_NUM_THREADS",
                                                 "OPENBLAS_NUM_THREADS",
                                                 "MKL_NUM_THREADS")},
              "geometry": {"length_m": LENGTH_M, "width_m": WIDTH_M,
                           "shell_thickness_m": SHELL_THICKNESS_M,
                           "beam_axis_z_m": BEAM_AXIS_Z_M,
                           "beam_bottom_arm_m": BEAM_BOTTOM_ARM_M},
              "cases": [], "failure": None}
    try:
        for n in LEVELS[:1] if canary else LEVELS:
            for case in ("fy",) if canary else LOADS:
                result["cases"].append(solve(
                    ops, n, case, constraint_form=constraint_form))
    except Exception as exc:
        result["failure"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                     allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"cases": len(result["cases"]),
                      "failure": result["failure"],
                      "output": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--canary", action="store_true")
    parser.add_argument("--constraint-form", choices=("chain", "direct"),
                        default="chain")
    args = parser.parse_args()
    main(args.site, args.output, canary=args.canary,
         constraint_form=args.constraint_form)

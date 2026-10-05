"""Bounded physical-work interpretation of the C1 director-pitch row.

This is a virtual-work identity for an explicit two-sided attachment, not
evidence that a top-face stiffener has that physical connection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import scipy
from scipy.spatial.transform import Rotation

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_distributed_surface_finite import FiniteSurfaceLineHybrid
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _face_pair_work(patch, q, v, beam_state, h):
    """Independent two-face traction work from sampled physical directors."""
    shell = q.reshape(patch.shell_count, 6)
    direction = v.reshape(patch.shell_count, 6)
    frames = Rotation.from_rotvec(shell[:, 3:]).as_matrix()
    plus = Rotation.from_rotvec(shell[:, 3:]+h*direction[:, 3:]).as_matrix()
    minus = Rotation.from_rotvec(shell[:, 3:]-h*direction[:, 3:]).as_matrix()
    frame_change = (plus[:, :, 2]-minus[:, :, 2])/(2*h)
    total_work = 0.
    total_force = np.zeros(3)
    total_moment = np.zeros(3)
    top_only_work = 0.
    for point in patch.points:
        nodes, shape = patch._point_shape(point.x, 0.)
        ids = np.asarray(nodes, dtype=int)
        n = shape@frames[ids, :, 2]
        dn = shape@frame_change[ids]
        _, _, beam_frame = point.port.pose_pair(beam_state)
        x_axis, z_axis = beam_frame[:, 0], beam_frame[:, 2]
        a, c = float(x_axis@n), float(z_axis@n)
        # d atan2(x_b.n, z_b.n) / d n.  Opposite face forces of magnitude
        # M/t produce this director work without a net translational force.
        gradient = (c*x_axis-a*z_axis)/(a*a+c*c)
        top_force = gradient/(2*patch.top)
        bottom_force = -top_force
        top_motion = shape@direction[ids, :3]+patch.top*dn
        bottom_motion = shape@direction[ids, :3]-patch.top*dn
        total_work += point.weight*(top_force@top_motion+
                                    bottom_force@bottom_motion)
        top_only_work += point.weight*(top_force@top_motion)
        total_force += point.weight*(top_force+bottom_force)
        total_moment += point.weight*(2*patch.top*np.cross(n, top_force))
    return total_work, top_only_work, total_force, total_moment


def evaluate():
    xs, ys = local_grid(8, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    patch = FiniteSurfaceLineHybrid(xs, ys, beam, thickness=.035)
    state = beam.context.initial.mechanical
    root = patch.reference_nodes[:, 0] <= -.5+1e-12
    rng = np.random.default_rng(3221)
    cases = {}
    for name, amplitude in (("reference", 0.), ("finite_chart", .035)):
        q = np.zeros((patch.shell_count, 6))
        q[:, 3:] = amplitude*rng.standard_normal((patch.shell_count, 3))
        q[root] = 0.
        v = rng.standard_normal((patch.shell_count, 6))
        v[root] = 0.
        actual = patch.evaluate_e4_total(q.ravel(), state,
            first=(v.ravel(), np.zeros(beam.context.count)),
            second=(v.ravel(), np.zeros(beam.context.count)))[4, 1]
        samples = []
        for h in (1e-4, 5e-5, 2.5e-5):
            work, top, net, moment = _face_pair_work(
                patch, q.ravel(), v.ravel(), state, h)
            samples.append({"step": h, "face_pair_work": work,
                            "relative_error": abs(work-actual)/max(1., abs(actual)),
                            "net_force": net.tolist(),
                            "couple_about_face_midpoint": moment.tolist()})
        if (min(s["relative_error"] for s in samples) > 1e-7 or
                max(np.linalg.norm(s["net_force"]) for s in samples) > 1e-12):
            raise ArithmeticError(f"C1 pitch two-face work failed: {name}")
        cases[name] = {"actual_pitch_derivative": float(actual),
                       "samples": samples}

    # Top-face position stays fixed to first order while the director moves.
    # The two-face pair therefore does work that a top-only position tie cannot.
    v = np.zeros((patch.shell_count, 6))
    pitch = 1e-4*(patch.reference_nodes[:, 0]+.5)/1.5
    v[:, 4] = pitch
    v[:, 0] = -patch.top*pitch
    q = np.zeros_like(v)
    actual = patch.evaluate_e4_total(q.ravel(), state,
        first=(v.ravel(), np.zeros(beam.context.count)),
        second=(v.ravel(), np.zeros(beam.context.count)))[4, 1]
    work, top, net, moment = _face_pair_work(
        patch, q.ravel(), v.ravel(), state, 2.5e-5)
    if (abs(actual-work) > 1e-10 or abs(actual) < 1e-5 or
            abs(top) > 1e-10 or np.linalg.norm(net) > 1e-12 or
            abs(moment[1]-1.) > 1e-12):
        raise ArithmeticError("compensated top-fixed pitch work identity failed")
    sources = [Path(__file__),
        Path("scripts/_b3_e4_f03_native_fixture.py"),
        Path("scripts/b3_e4_f03_distributed_surface_finite.py"),
        Path("scripts/b3_e4_f03_plate_patch_work.py"),
        Path("scripts/b3_e4_f03_square_section_control.py")]
    return {"classification": "bounded two-face pitch work interpretation, not F03/G0B acceptance",
            "question": "Can the extra C1 director-pitch work be represented by a two-sided through-thickness face-force couple?",
            "geometry": "C1 Q4 x8/y4 shell t=0.035 m, B3-12; unchanged 0.1 m line",
            "unit_pitch_dual": "1 N m per normalized line basis; physical density follows basis integral",
            "cases": cases,
            "compensated_top_fixed": {
                "pitch_work": float(actual), "two_face_work": float(work),
                "top_face_only_work": float(top),
                "net_force": net.tolist(), "face_pair_moment": moment.tolist()},
            "interpretation": "C1 pitch permits an embedded/two-sided couple interpretation; a top-only positional bond has zero work on the compensated field",
            "limits": ["virtual-work identity, not a loaded or external reference",
                       "a two-sided physical weld is a distinct idealization from a top-face bond",
                       "does not establish intended joint, shear/locking, torque accuracy or multiplier stability"],
            "provenance": {
                "source_git": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                "python": sys.version.split()[0], "executable": sys.executable,
                "numpy": np.__version__, "scipy": scipy.__version__,
                "env": {k: os.environ.get(k) for k in
                        ("PYTHONPATH", "NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"compensated_pitch_work": result["compensated_top_fixed"]["pitch_work"],
                      "max_finite_error": max(s["relative_error"] for c in result["cases"].values()
                                              for s in c["samples"])}))


if __name__ == "__main__":
    main()

"""Bounded native section/offset control for the solid-bond comparison.

This is a development diagnostic. The square-bar Saint-Venant torsion
constant is substituted explicitly; no product section law is changed.
"""

from __future__ import annotations

import json
import hashlib
import platform
import subprocess
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_info, threadpool_limits

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_channel_basis_reference_kkt,
)
from scripts.b3_e4_f03_beam_window_decision import loaded


def square_torsion_constant(side: float = .1) -> float:
    """Fourier-series Saint-Venant J for a square bar, in m^4."""
    if not np.isfinite(side) or side <= 0.:
        raise ValueError("positive finite square side required")
    odds = np.arange(1, 1024, 2, dtype=float)
    series = np.sum(np.tanh(odds * np.pi / 2) / odds**5)
    return float(side**4 * (1 - 192 * series / np.pi**5) / 3)


def run(output_dir: Path) -> None:
    source = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"],
                               text=True).strip():
        raise RuntimeError("run requires clean source")
    output_dir.mkdir(parents=True, exist_ok=False)
    j_square = square_torsion_constant()
    manifest = {
        "status": "EXPLORATORY_NOT_G0_ACCEPTANCE",
        "question": "How much of the support- and offset-controlled torque difference follows from the native generalized polar J versus the physical square-bar Saint-Venant J?",
        "decision": "If section matching materially narrows torque while force remains similar, develop a mechanically matched footprint reference; otherwise investigate shell and connection operators. Neither result qualifies the six-channel weak line.",
        "source_sha": source,
        "python": platform.python_version(),
        "threads": 1,
        "geometry": "plate x[-.5,1.5] y[-.5,.5] z=0 thickness .07 m; beam axis x[0,1] y=0 z=.085 m; square support half-widths .05/.05 m",
        "supports": "complete shell left edge and native beam root fixed",
        "loads": "separate +100 N m tip Mx and +1000 N tip Fz at beam centroid",
        "sections": {"native_polar_j_m4": 1.6666666666666667e-5,
                     "square_saint_venant_j_m4": j_square,
                     "other_native_elastic_resultants_unchanged": True},
        "torsion_formula": "J/a^4 = (1 - 192/pi^5 sum_{n odd>=1} tanh(n*pi/2)/n^5)/3, odd n<=1023; see https://docs.oasys-software.com/structural/gsa/references-theory/rectangular-sections/",
        "connection": "native six-channel P0 Fz and other channels 4 cells, P0 Mx 8 cells; physical square strip; not conforming solid bond",
        "mesh": "Q4/S3 x8/y4, native B3 16 half-cells",
        "limits": "bounded linearized response, different shell/connection/section warping from conforming C3D8; no physical accuracy acceptance",
    }
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"] = threadpool_info()
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n")
        p0 = LineMultiplierSpace("piecewise_constant",
                                 (0., .25, .5, .75, 1.))
        mx = LineMultiplierSpace("piecewise_constant",
                                 tuple(np.linspace(0., 1., 9)))
        spaces = (p0, p0, p0, mx, p0, p0)
        with (output_dir / "results.jsonl").open("w") as stream:
            for topology in ("Q4", "S3-V2D"):
                shell = FlatE4TrialPanel(make_shell(4, topology, n_y=4))
                for section, constant in (("polar", None),
                                          ("square_saint_venant", j_square)):
                    beam = build(16, z_offset=.085,
                                 torsion_constant=constant)
                    kkt = assemble_channel_basis_reference_kkt(
                        shell, beam, spaces,
                        shell_port="physical_strip_005_005",
                        shell_support_policy="full_left_edge")
                    record = {"topology": topology, "section": section,
                              "tip_mx": loaded(
                                  kkt, shell, beam, kkt.constraint_jacobian, 3),
                              "tip_fz": loaded(
                                  kkt, shell, beam, kkt.constraint_jacobian, 2)}
                    stream.write(json.dumps(record, allow_nan=False) + "\n")
                    stream.flush()
                    print(topology, section,
                          record["tip_mx"]["tip_rx_rad"],
                          record["tip_fz"]["tip_uz_m"], flush=True)


def run_matched_full_bond(output_dir: Path) -> None:
    """Bounded six-channel reference comparison, not a bond equivalence claim."""
    from scripts.b3_e4_f03_weak_line_resolution_screen import one_case

    source = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"],
                               text=True).strip():
        raise RuntimeError("run requires clean source")
    output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "status": "EXPLORATORY_NOT_G0_ACCEPTANCE",
        "question": "With thickness, offset, section, supports and resultants matched, does the native exact six-channel line transfer torque and shear toward the full-bond solid reference at fixed shell/beam resolution as line rows increase?",
        "outcome_rule": "If both loads, plate support shares and work improve at finite line resolution, advance the native pose to registered mesh-ratio/stability testing. If line resolution strongly stiffens or undertransfers, revise the torsional pose or interface law before choosing a multiplier. This is not direct accuracy qualification because a finite-width solid volume bond differs from a one-dimensional B3/E4 strip tie and tip face tractions differ from native nodal resultants.",
        "source_head": source,
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "requested_blas_threads": 1,
        "geometry": "plate x[-.5,1.5] y[-.5,.5] z=0 thickness .035 m; B3 axis x[0,1] y=0 z=.0675 m; square strip half-length/width .05/.05 m",
        "materials": "E=210 GPa, nu=.3; generalized B3 square A=.01 m2, Iy=Iz=8.333333333333333e-6 m4, square Saint-Venant J; elastic E4 Q4/S3-V2D",
        "supports": "all shell left-edge coordinates and native B3 root fixed; same support location and resultant constraints as solid left/root case",
        "loads": "separate +100 N m native tip Mx and +1000 N native tip Fz; solid reference applies work-conjugate quadratic-face tractions",
        "connection": "native exact six-channel P0 physical_strip_005_005 over beam x[0,1], line intervals 4 and 8; solid reference is conforming full-width volume bond",
        "mesh": "native shell Q4/S3 x8/y4, B3 16 half-cells, fixed while line rows change; solid C3D20R factor 4 has a distinct mesh",
        "solid_reference": "f03-ccx-full-bond-quadratic-face-dev-20260925-v1, factor-4 tip_mx/tip_fz, and output-only full-field replay",
        "primal_row_limit": "existing bounded dense reference KKT",
    }
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"] = threadpool_info()
        rows = []
        for topology in ("Q4", "S3-V2D"):
            for intervals in (4, 8):
                for load in ("torsion", "transverse_force_z"):
                    row = one_case(
                        topology, intervals, "piecewise_constant",
                        shell_port="physical_strip_005_005", load_kind=load,
                        n_s=4, n_y=4, native_half_cells=16,
                        thickness=.035, beam_z_offset=.0675,
                        beam_torsion_constant=square_torsion_constant(),
                        shell_support_policy="full_left_edge")
                    rows.append(row)
                    print(topology, intervals, load,
                          row["tip_rx_rad"], row["beam_tip_uz_m"],
                          flush=True)
        data = json.dumps(rows, indent=2, allow_nan=False) + "\n"
        (output_dir / "results.json").write_text(data)
        manifest["results_sha256"] = hashlib.sha256(data.encode()).hexdigest()
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--matched-full-bond", action="store_true")
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    if args.matched_full_bond:
        run_matched_full_bond(args.output_dir)
    else:
        run(args.output_dir)

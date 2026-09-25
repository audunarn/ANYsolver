"""Bounded native section/offset control for the solid-bond comparison.

This is a development diagnostic. The square-bar Saint-Venant torsion
constant is substituted explicitly; no product section law is changed.
"""

from __future__ import annotations

import json
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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    run(parser.parse_args().output_dir)

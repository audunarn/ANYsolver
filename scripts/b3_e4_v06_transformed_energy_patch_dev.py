"""Check the signed transformed-section cross energy in the linear GE owner.

This is a compatible imposed-field patch, not a loaded V06 qualification case.
Native internal B3 coordinates are made stationary for each imposed field.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import spsolve

from scripts.b3_e4_e01_native_point_refinement_screen import E, NU, definition
from anysolver.stiffened_shell import create_analysis


LENGTH_M = 2.0
BEAM_AREA_M2 = 0.01
BEAM_IY_M4 = 8.333333333333333e-6
SHELL_THICKNESS_M = 0.07
SHELL_WIDTH_M = 1.0
OFFSET_M = 0.1
AXIAL_STRAIN = 1e-4
CURVATURE_PER_M = 1e-4


def _field(owner, *, axial: float, curvature: float, offset: float):
    count = owner._K.shape[0]
    physical_end = owner._shell_count+6*len(owner._beam_ids)
    q = np.zeros(count)
    for i, position in enumerate(owner._shell_xyz):
        x = float(position[0])
        q[6*i] = axial*x
        q[6*i+2] = -0.5*curvature*x*x
        q[6*i+4] = curvature*x
    for i, node in enumerate(owner._beam_ids):
        x = float(owner._beam_nodes[node][0][0])
        base = owner._shell_count+6*i
        q[base] = (axial+offset*curvature)*x
        q[base+2] = -0.5*curvature*x*x
        q[base+4] = curvature*x
    gap = float(np.max(np.abs(owner._C@q), initial=0.))
    retained = np.arange(physical_end, count)
    if retained.size:
        krr = owner._K[retained, :][:, retained].tocsc()
        krp = owner._K[retained, :][:, :physical_end]
        q[retained] = spsolve(krr, -krp@q[:physical_end])
        if not np.isfinite(q[retained]).all():
            raise ValueError("finite stationary retained field required")
        stationarity = float(np.max(np.abs((owner._K@q)[retained]),
                                    initial=0.))
    else:
        stationarity = 0.
    return q, gap, stationarity


def evaluate(intervals: int, sign: int):
    if intervals not in (2, 4, 8) or sign not in (-1, +1):
        raise ValueError("registered development grids/signs required")
    definition_, _tip = definition(intervals, sign, intervals//2)
    owner = create_analysis(definition=definition_)
    a, gap_a, station_a = _field(owner, axial=AXIAL_STRAIN,
                                  curvature=0., offset=sign*OFFSET_M)
    b, gap_b, station_b = _field(owner, axial=0.,
                                  curvature=CURVATURE_PER_M,
                                  offset=sign*OFFSET_M)
    k = owner._K
    cross = float(a@(k@b))
    reverse = float(b@(k@a))
    axial_energy = 0.5*float(a@(k@a))
    curvature_energy = 0.5*float(b@(k@b))
    shell_cross = float(a[:owner._shell_count] @
                        (k[:owner._shell_count, :owner._shell_count] @
                         b[:owner._shell_count]))
    expected = (E*BEAM_AREA_M2*sign*OFFSET_M*AXIAL_STRAIN*
                CURVATURE_PER_M*LENGTH_M)
    shell_axial = E*SHELL_THICKNESS_M*SHELL_WIDTH_M/(1.-NU*NU)
    shell_bending = (E*SHELL_THICKNESS_M**3*SHELL_WIDTH_M/
                     (12.*(1.-NU*NU)))
    beam_axial = E*BEAM_AREA_M2
    beam_bending = E*BEAM_IY_M4
    axial_expected = 0.5*(shell_axial+beam_axial)*AXIAL_STRAIN**2*LENGTH_M
    curvature_expected = 0.5*(shell_bending+beam_bending+
                              beam_axial*OFFSET_M**2)*CURVATURE_PER_M**2*LENGTH_M
    relative = abs(cross-expected)/abs(expected)
    symmetry = abs(cross-reverse)/abs(expected)
    return {
        "shell_intervals": intervals,
        "transverse_intervals": intervals//2,
        "offset_sign": sign,
        "expected_beam_cross_energy_j": expected,
        "assembled_cross_energy_j": cross,
        "reverse_cross_energy_j": reverse,
        "axial_energy_j": axial_energy,
        "axial_expected_j": axial_expected,
        "axial_relative_error": abs(axial_energy-axial_expected)/axial_expected,
        "curvature_energy_j": curvature_energy,
        "curvature_expected_j": curvature_expected,
        "curvature_relative_excess": (curvature_energy-curvature_expected)/
                                     curvature_expected,
        "shell_cross_energy_j": shell_cross,
        "relative_cross_error": relative,
        "normalized_skew": symmetry,
        "max_point_gap": max(gap_a, gap_b),
        "max_retained_stationarity": max(station_a, station_b),
        "physical_dofs": owner._shell_count+6*len(owner._beam_ids),
        "retained_dofs": k.shape[0]-owner._shell_count-
                         6*len(owner._beam_ids),
        "nnz": int(k.nnz),
    }


def main(output: Path):
    if output.exists():
        raise FileExistsError("preserve previous V06 development evidence")
    cases = [evaluate(intervals, sign)
             for intervals in (2, 4, 8) for sign in (-1, +1)]
    record = {
        "classification": "V06 imposed transformed-section energy patch; development only",
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "physical_inputs": {"length_m": LENGTH_M,
                            "beam_area_m2": BEAM_AREA_M2,
                            "beam_iy_m4": BEAM_IY_M4,
                            "shell_thickness_m": SHELL_THICKNESS_M,
                            "shell_width_m": SHELL_WIDTH_M,
                            "poisson": NU,
                            "offset_magnitude_m": OFFSET_M,
                            "axial_strain": AXIAL_STRAIN,
                            "curvature_per_m": CURVATURE_PER_M},
        "cases": cases,
        "limit": ("Imposed compatible field and stationary beam retained variables; "
                  "not a solved load-response or V06 acceptance result."),
    }
    output.write_text(json.dumps(record, indent=2, sort_keys=True,
                                 allow_nan=False)+"\n", encoding="utf-8")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    record = main(args.output)
    print(json.dumps({"max_relative_cross_error": max(
        case["relative_cross_error"] for case in record["cases"]),
        "max_axial_relative_error": max(case["axial_relative_error"]
                                         for case in record["cases"]),
        "curvature_relative_excess_by_level": [
            case["curvature_relative_excess"] for case in record["cases"]
            if case["offset_sign"] == 1],
        "max_point_gap": max(case["max_point_gap"] for case in record["cases"]),
        "max_normalized_skew": max(case["normalized_skew"]
                                   for case in record["cases"])}))

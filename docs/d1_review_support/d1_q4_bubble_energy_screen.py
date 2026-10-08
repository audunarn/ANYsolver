"""Exact flat-Q4 bubble strain screen against the current MITC4 tying rule.

This is an independent algebraic derivation for one proposed development
mode, not an enriched element implementation or a contact qualification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from d1_cut_front_two_hat_limit import limit_matrix, null_coefficients
from anysolver.e4_pl_element import _coefficients, _source_fields


def bubble(r: float, s: float) -> tuple[float, float, float]:
    """B=(1-r²)(1-s²), with natural derivatives."""
    return ((1.0-r*r)*(1.0-s*s),
            -2.0*r*(1.0-s*s), -2.0*s*(1.0-r*r))


def screen() -> dict:
    hx, hy, thickness = 0.5, 1.0, 0.05
    young, poisson = 1.0e5, 0.3
    shear = young/(2.0*(1.0+poisson))
    points, weights = np.polynomial.legendre.leggauss(3)
    raw_gradients = []
    mitc_gradients = []
    raw_integral = 0.0
    mitc_integral = 0.0
    for r, weight_r in zip(points, weights):
        for s, weight_s in zip(points, weights):
            _, derivative_r, derivative_s = bubble(r, s)
            raw_gradient = (2.0*derivative_r/hx, 2.0*derivative_s/hy)
            raw_gradients.append(raw_gradient)
            # Current MITC4 shear uses e_rz at (r=0,s=+/-1) and
            # e_sz at (r=+/-1,s=0). Both vanish for every conforming
            # interior transverse bubble, regardless of r,s here.
            top_r = bubble(0.0, 1.0)[1]
            bottom_r = bubble(0.0, -1.0)[1]
            right_s = bubble(1.0, 0.0)[2]
            left_s = bubble(-1.0, 0.0)[2]
            mitc_gradient = (
                2.0*(0.5*(1.0+s)*top_r+0.5*(1.0-s)*bottom_r)/hx,
                2.0*(0.5*(1.0+r)*right_s+0.5*(1.0-r)*left_s)/hy,
            )
            mitc_gradients.append(mitc_gradient)
            raw_integral += weight_r*weight_s*np.dot(raw_gradient, raw_gradient)
            mitc_integral += weight_r*weight_s*np.dot(mitc_gradient, mitc_gradient)
    raw = np.asarray(raw_gradients)
    mitc = np.asarray(mitc_gradients)
    area_weight = hx*hy/4.0
    raw_gauss_energy = float(shear*thickness*area_weight*raw_integral)
    exact_gradient_integral = (128.0/45.0)*(hy/hx+hx/hy)
    exact_raw_energy = shear*thickness*exact_gradient_integral
    mitc_energy = float(shear*thickness*area_weight*mitc_integral)
    if abs(raw_gauss_energy-exact_raw_energy) > 1.0e-12*exact_raw_energy:
        raise AssertionError("raw Gauss and polynomial energies disagree")
    if mitc_energy != 0.0:
        raise AssertionError("bubble unexpectedly enters MITC4 tying shear")
    # The actual default Q4 uses a stationary E4-PL stress space. Its shear
    # stress source functions, including the linear modes, must be checked
    # separately from the scalar MITC4 reference above.
    local = np.array(((-hx/2.0, -hy/2.0), (hx/2.0, -hy/2.0),
                      (hx/2.0, hy/2.0), (-hx/2.0, hy/2.0)))
    coefficients = _coefficients(local)
    e4pl_stress_coupling = np.zeros(14)
    for r, wr in zip(points, weights):
        for s, ws in zip(points, weights):
            source_stress, _ = _source_fields(coefficients, float(r), float(s))
            _, derivative_r, derivative_s = bubble(r, s)
            physical_bubble_shear = np.array((0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                              2.0*derivative_r/hx,
                                              2.0*derivative_s/hy))
            e4pl_stress_coupling += (
                wr*ws*coefficients["jc"]
                *(source_stress.T@physical_bubble_shear)
            )
    coupling_norm = float(np.linalg.norm(e4pl_stress_coupling))
    if coupling_norm > 1.0e-12:
        raise AssertionError("interior bubble unexpectedly couples to E4-PL stress space")
    c1 = float(null_coefficients(sum(limit_matrix()))[0])
    pressure_work = []
    for theta in (0.1, 0.05, 0.025, 0.0125):
        b = theta**2/2.0-theta**3/3.0
        d = 0.25+theta-theta**2+theta**3/3.0
        beta = -b/d
        work = c1*beta/36.0
        pressure_work.append({"theta": theta,
                              "exact_bubble_force_m2_per_pa": work,
                              "force_over_theta_squared_m2_per_pa": work/theta**2})
    return {
        "status": "development algebraic screen; not production enriched shell",
        "source_cell_width_m": hx,
        "source_cell_height_m": hy,
        "thickness_m": thickness,
        "young_pa": young,
        "poisson": poisson,
        "raw_mindlin_shear_energy_coefficient_n_per_m": exact_raw_energy,
        "mitc4_assumed_shear_energy_coefficient_n_per_m": mitc_energy,
        "raw_gauss_gradient_maximum": float(np.max(np.abs(raw))),
        "mitc4_tied_gradient_maximum": float(np.max(np.abs(mitc))),
        "e4pl_stationary_stress_coupling_l2": coupling_norm,
        "pressure_work": pressure_work,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    result = screen()
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"raw_energy": result["raw_mindlin_shear_energy_coefficient_n_per_m"],
                      "mitc_energy": result["mitc4_assumed_shear_energy_coefficient_n_per_m"],
                      "e4pl_stress_coupling": result["e4pl_stationary_stress_coupling_l2"],
                      "pressure_work": result["pressure_work"]}))

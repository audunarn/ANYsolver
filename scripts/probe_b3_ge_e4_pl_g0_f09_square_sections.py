"""Bounded F09 scaling screen with geometrically linked square B2 sections.

This tests a numerical route and one rooted elbow, not public B2 admission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts import probe_b3_ge_e4_pl_g0_f09_physical_range as prior
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


SIDES_M = (.04, .08, .16)
E_PA = 210e9
NU = .3
TERMINAL = np.array((50., -30., 100., 2., -3., 5.))
COMPONENT_REL_TOL = 1e-8
RESIDUAL_REL_TOL = 1e-10


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(side: float) -> dict:
    area = side**2
    inertia = side**4 / 12
    torsion = square_torsion_constant(side)
    section = prior.LinearSection.isotropic(
        E=E_PA, nu=NU, area=area, Iy=inertia, Iz=inertia, J=torsion,
        ky=5 / 6, kz=5 / 6,
    )
    load = np.zeros(18)
    load[12:] = TERMINAL
    _, matrix, reduced = prior.elbow._float_graph(
        prior.elbow._members(section), load)
    free, scale_info = prior._scaled_solve(reduced, load[6:])
    exact = np.asarray([float(value) for value in prior.elbow._exact_solve(
        reduced.toarray(), load[6:])])
    tip_exact = exact[6:]
    physical = prior._physical_tip(section, TERMINAL)
    full = np.r_[np.zeros(6), free]
    tip = full[12:]
    residual = (matrix @ full - load)[6:]
    force_indices = (0, 1, 2, 6, 7, 8)
    moment_indices = (3, 4, 5, 9, 10, 11)
    force_ratio = float(np.max(np.abs(residual[list(force_indices)])) /
                        np.max(np.abs(TERMINAL[:3])))
    moment_ratio = float(np.max(np.abs(residual[list(moment_indices)])) /
                         np.max(np.abs(TERMINAL[3:])))
    # The floor only prevents an almost-zero cross component from defining a
    # meaningless relative error. Report the full six-vectors as well.
    floor = np.r_[np.full(3, 1e-8), np.full(3, 1e-8)]
    scale = np.maximum(np.abs(physical), floor)
    scaled_vs_physical = float(np.max(np.abs(tip - physical) / scale))
    rounded_vs_physical = float(np.max(np.abs(tip_exact - physical) / scale))
    scaled_vs_rounded = float(np.max(np.abs(tip - tip_exact) /
                                     np.maximum(np.abs(tip_exact), floor)))
    passed = (max(scaled_vs_physical, rounded_vs_physical,
                  scaled_vs_rounded) <= COMPONENT_REL_TOL
              and max(force_ratio, moment_ratio) <= RESIDUAL_REL_TOL)
    return {
        "square_side_m": side, "area_m2": area, "Iy_Iz_m4": inertia,
        "Saint_Venant_J_m4": torsion, "E_Pa": E_PA, "nu": NU,
        "terminal_wrench_N_Nm": TERMINAL.tolist(),
        "scaled_tip_m_rad": tip.tolist(),
        "exact_rounded_tip_m_rad": tip_exact.tolist(),
        "independent_force_method_tip_m_rad": physical.tolist(),
        "scaled_vs_physical_component_error": scaled_vs_physical,
        "rounded_vs_physical_component_error": rounded_vs_physical,
        "scaled_vs_exact_rounded_component_error": scaled_vs_rounded,
        "free_force_residual_ratio": force_ratio,
        "free_moment_residual_ratio": moment_ratio,
        "passed_declared_diagnostic": bool(passed),
        **scale_info,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    cases = [_case(side) for side in SIDES_M]
    record = {
        "classification": "F09_PHYSICAL_SQUARE_SECTION_DEV_NOT_ADMISSION",
        "question": "Does the scaled sparse B2 elbow solve preserve fixed mixed physical loads for linked square sections?",
        "geometry": "rooted two-member 2 m + 1.5 m elbow, unchanged private B2 physical flexibility operator",
        "material": "isotropic E=210 GPa, nu=0.3, ky=kz=5/6; area=b^2, Iy=Iz=b^4/12, Fourier Saint-Venant square J",
        "cases": cases,
        "thresholds": {"component_relative": COMPONENT_REL_TOL,
                       "component_floor_m_rad": 1e-8,
                       "separate_force_moment_residual_relative": RESIDUAL_REL_TOL},
        "all_declared_cases_passed": all(case["passed_declared_diagnostic"] for case in cases),
        "limits": ["one rooted elbow and three square sizes, not a complete section admission",
                   "linearized response checked mathematically; no nonlinear validity inference",
                   "no generalized off-diagonal SPD, shell attachment, dynamics, installed artifact or performance claim"],
        "source_sha256": sha(Path(__file__)),
        "prior_scaled_oracle_sha256": sha(Path(prior.__file__)),
        "torsion_oracle_sha256": sha(Path(square_torsion_constant.__code__.co_filename)),
    }
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True,
                                      allow_nan=False) + "\n")
    print(json.dumps({"cases": len(cases),
                      "passed": sum(case["passed_declared_diagnostic"] for case in cases),
                      "max_component_error": max(case["scaled_vs_physical_component_error"] for case in cases),
                      "max_force_residual": max(case["free_force_residual_ratio"] for case in cases),
                      "max_moment_residual": max(case["free_moment_residual_ratio"] for case in cases)}))
    if not record["all_declared_cases_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

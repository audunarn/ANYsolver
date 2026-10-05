"""Bounded generalized-SPD B2 elbow check against an independent force method.

No product dispatch, public admission, dynamic mass, or performance claim.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts import probe_b3_ge_e4_pl_g0_f09_physical_range as prior
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


SIDE_M = .08
E_PA = 210e9
NU = .3
LOAD = np.array((50., -30., 100., 2., -3., 5.))
COMPONENT_TOL = 1e-8
RESIDUAL_TOL = 1e-10


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _section(sign: int) -> prior.LinearSection:
    if sign not in (-1, 1):
        raise ValueError("declared coupling sign required")
    scalar = prior.LinearSection.isotropic(
        E=E_PA, nu=NU, area=SIDE_M**2, Iy=SIDE_M**4 / 12,
        Iz=SIDE_M**4 / 12, J=square_torsion_constant(SIDE_M),
        ky=5 / 6, kz=5 / 6,
    )
    diagonal = np.diag(np.asarray(scalar.stiffness))
    correlation = np.eye(6)
    for i, j, value in ((0, 4, .18), (1, 5, -.12), (2, 3, .08)):
        correlation[i, j] = correlation[j, i] = sign * value
    if np.min(np.linalg.eigvalsh(correlation)) <= .7:
        raise ArithmeticError("declared generalized coupling is not well separated from singularity")
    stiffness = np.sqrt(np.outer(diagonal, diagonal)) * correlation
    stiffness = (stiffness + stiffness.T) / 2
    return prior.LinearSection.generalized(stiffness)


def _independent_tip(section: prior.LinearSection, terminal: np.ndarray) -> np.ndarray:
    """Cut-wrench Castigliano derivative with separately inverted 6x6 law."""
    stiffness = np.asarray(section.stiffness)
    columns = [prior.elbow._exact_solve(stiffness, np.eye(6)[i])
               for i in range(6)]
    compliance = [[columns[j][i] for j in range(6)] for i in range(6)]
    if any(compliance[i][j] != compliance[j][i] for i in range(6) for j in range(6)):
        raise ArithmeticError("independent rational compliance lost symmetry")
    applied = tuple(Fraction(float(value)) for value in terminal)
    tip = [Fraction(0) for _ in range(6)]
    end = tuple(Fraction(value) for value in prior.elbow.POINTS[-1])
    for member, frame in enumerate(prior.elbow.FRAMES):
        start = tuple(Fraction(value) for value in prior.elbow.POINTS[member])
        finish = tuple(Fraction(value) for value in prior.elbow.POINTS[member + 1])
        length = Fraction(2) if member == 0 else Fraction(3, 2)
        for t, weight in ((Fraction(0), 1), (Fraction(1, 2), 4), (Fraction(1), 1)):
            point = tuple(a + t * (b - a) for a, b in zip(start, finish))
            lever = tuple(a - b for a, b in zip(end, point))

            def local(action):
                force, couple = action[:3], action[3:]
                moment = tuple(couple[i] + prior.elbow._cross(lever, force)[i]
                               for i in range(3))
                return tuple(sum(Fraction(axis[j]) * vector[j] for j in range(3))
                             for vector in (force, moment) for axis in frame)

            stress = local(applied)
            for axis in range(6):
                unit = tuple(Fraction(int(i == axis)) for i in range(6))
                derivative = local(unit)
                tip[axis] += length * weight * sum(
                    derivative[j] * compliance[j][k] * stress[k]
                    for j in range(6) for k in range(6)) / 6
    return np.asarray([float(value) for value in tip])


def _case(sign: int) -> dict:
    section = _section(sign)
    load = np.zeros(18)
    load[12:] = LOAD
    _, matrix, reduced = prior.elbow._float_graph(
        prior.elbow._members(section), load)
    free, info = prior._scaled_solve(reduced, load[6:])
    exact = np.asarray([float(value) for value in prior.elbow._exact_solve(
        reduced.toarray(), load[6:])])
    physical = _independent_tip(section, LOAD)
    full = np.r_[np.zeros(6), free]
    tip = full[12:]
    residual = (matrix @ full - load)[6:]
    floor = np.full(6, 1e-8)
    scaled_error = float(np.max(np.abs(tip - physical) /
                                np.maximum(np.abs(physical), floor)))
    rounded_error = float(np.max(np.abs(exact[6:] - physical) /
                                 np.maximum(np.abs(physical), floor)))
    factorization_error = float(np.max(np.abs(tip - exact[6:]) /
                                       np.maximum(np.abs(exact[6:]), floor)))
    force_error = float(np.max(np.abs(residual[[0, 1, 2, 6, 7, 8]])) /
                        np.max(np.abs(LOAD[:3])))
    moment_error = float(np.max(np.abs(residual[[3, 4, 5, 9, 10, 11]])) /
                         np.max(np.abs(LOAD[3:])))
    return {
        "coupling_sign": sign,
        "stiffness_N_Nm": [list(row) for row in section.stiffness],
        "tip_scaled_m_rad": tip.tolist(),
        "tip_exact_rounded_m_rad": exact[6:].tolist(),
        "tip_independent_force_method_m_rad": physical.tolist(),
        "scaled_vs_independent_component_error": scaled_error,
        "rounded_vs_independent_component_error": rounded_error,
        "scaled_vs_rounded_component_error": factorization_error,
        "free_force_residual_ratio": force_error,
        "free_moment_residual_ratio": moment_error,
        "passed_declared_diagnostic": bool(
            max(scaled_error, rounded_error, factorization_error) <= COMPONENT_TOL
            and max(force_error, moment_error) <= RESIDUAL_TOL),
        **info,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    cases = [_case(sign) for sign in (1, -1)]
    record = {
        "classification": "F09_GENERALIZED_SPD_DEV_NOT_ADMISSION",
        "question": "Does scaled sparse B2 preserve off-diagonal generalized-section work under fixed mixed loads and oriented elbow members?",
        "section": "0.08 m square isotropic diagonal, dimensionally scaled symmetric N-My, Vy-Mz, Vz-T couplings of both signs",
        "terminal_wrench_N_Nm": LOAD.tolist(),
        "cases": cases,
        "thresholds": {"component_relative": COMPONENT_TOL,
                       "component_floor_m_rad": 1e-8,
                       "separate_residual_relative": RESIDUAL_TOL},
        "all_declared_cases_passed": all(case["passed_declared_diagnostic"] for case in cases),
        "limits": ["one rooted elbow and two modest SPD coupling signs, not a generalized-section admission range",
                   "independent rational compliance and cut-wrench force method do not validate new shell attachments, mass, prestress or installed B2 dispatch"],
        "source_sha256": sha(Path(__file__)),
        "operator_sha256": sha(Path(prior.LinearSection.__post_init__.__code__.co_filename)),
    }
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True,
                                      allow_nan=False) + "\n")
    print(json.dumps({"cases": len(cases),
                      "passed": sum(case["passed_declared_diagnostic"] for case in cases),
                      "max_scaled_error": max(case["scaled_vs_independent_component_error"] for case in cases),
                      "max_force_residual": max(case["free_force_residual_ratio"] for case in cases),
                      "max_moment_residual": max(case["free_moment_residual_ratio"] for case in cases)}))
    if not record["all_declared_cases_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

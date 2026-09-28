"""Bounded virgin physical-energy transport across nested native L1 grids.

The *actual* E4 PL and retained B3 Hessians are assembled independently on
each grid. Only generalized resultants are eliminated by their stationary
equations; native cell rotations remain physical. Generalized eigenvalues of
the pulled fine operator relative to the coarse operator quantify energy
approximation without mixing raw force/moment coordinate units. This is a
development diagnostic, not an F03 stability score or acceptance threshold.
"""

from __future__ import annotations

import json

import numpy as np
from scipy import linalg

from scripts.b3_e4_f03_l1_candidate_compare import (
    _assembled_macro, _supported_problem,
)
from scripts.b3_e4_f03_l1_physical_injection import physical_injection


def _physical_operator(problem: dict) -> np.ndarray:
    x, p = problem["x"], problem["p"]
    h = linalg.block_diag(problem["shell"], problem["native"])
    symmetry = np.linalg.norm(h-h.T, ord=np.inf)/max(
        1., np.linalg.norm(h, ord=np.inf))
    if symmetry > 1e-10:
        raise AssertionError("actual virgin retained Hessian is not symmetric")
    xx = h[np.ix_(x, x)]
    xp = h[np.ix_(x, p)]
    pp = h[np.ix_(p, p)]
    negative_pp = linalg.cho_factor(-pp, lower=True, check_finite=True)
    stationary = linalg.cho_solve(negative_pp, -xp.T)
    error = np.linalg.norm(pp@stationary-xp.T, ord=np.inf)/max(
        1., np.linalg.norm(pp, ord=np.inf)*
        np.linalg.norm(stationary, ord=np.inf)+
        np.linalg.norm(xp.T, ord=np.inf))
    if error > 1e-10:
        raise AssertionError("stationary resultant solve is inaccurate")
    k = xx-xp@stationary
    if np.linalg.norm(k-k.T, ord=np.inf) > 1e-10*max(
            1., np.linalg.norm(k, ord=np.inf)):
        raise AssertionError("physical operator is not symmetric")
    linalg.cho_factor(k, lower=True, check_finite=True)
    return k


def _energy_ratio(coarse: np.ndarray, pulled: np.ndarray) -> dict:
    """Generalized spectrum in diagonal-equilibrated physical coordinates."""
    diagonal = np.diag(coarse)
    if np.any(diagonal <= 0.) or not np.isfinite(diagonal).all():
        raise AssertionError("positive physical diagonal required")
    scale = 1./np.sqrt(diagonal)
    a = scale[:, None]*pulled*scale[None, :]
    b = scale[:, None]*coarse*scale[None, :]
    values = linalg.eigvalsh(a, b, check_finite=True)
    if not np.isfinite(values).all() or values[0] <= 0.:
        raise AssertionError("pulled physical energy is not positive")
    return {"minimum": float(values[0]), "maximum": float(values[-1]),
            "max_absolute_deviation_from_one": float(
                np.max(np.abs(values-1.)))}


def report(coarse_segments: int = 2) -> dict:
    if coarse_segments not in (2, 4):
        raise ValueError("bounded nested 2:4 or 4:8 grid required")
    cm = _assembled_macro(coarse_segments)
    fm = _assembled_macro(2*coarse_segments)
    cp = _supported_problem(cm, globally_refined=True)
    fp = _supported_problem(fm, globally_refined=True)
    t = physical_injection(cp, fp, cm, fm)
    xc, xf = cp["x"], fp["x"]
    t = t[np.ix_(xf, xc)]
    kc, kf = _physical_operator(cp), _physical_operator(fp)
    pulled = t.T@kf@t
    shell = np.flatnonzero(xc < cp["ns"])
    beam = np.flatnonzero(xc >= cp["ns"])
    return {
        "coarse_edges": coarse_segments,
        "fine_edges": 2*coarse_segments,
        "physical_dofs": [len(xc), len(xf)],
        "resultant_dofs": [len(cp["p"]), len(fp["p"])],
        "complete": _energy_ratio(kc, pulled),
        "shell": _energy_ratio(kc[np.ix_(shell, shell)],
                               pulled[np.ix_(shell, shell)]),
        "native_beam": _energy_ratio(kc[np.ix_(beam, beam)],
                                     pulled[np.ix_(beam, beam)]),
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))

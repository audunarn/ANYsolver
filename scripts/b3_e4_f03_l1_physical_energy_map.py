"""Bounded virgin physical-energy transport across nested native L1 grids.

The *actual* E4 PL and retained B3 Hessians are assembled independently on
each grid. Only generalized resultants are eliminated by their stationary
equations; native cell rotations remain physical. Generalized eigenvalues of
the pulled fine operator relative to the coarse operator quantify energy
approximation without mixing raw force/moment coordinate units. This is a
development diagnostic, not an F03 stability score or acceptance threshold.
"""

from __future__ import annotations

from functools import lru_cache
import json

import numpy as np
from scipy import linalg

from scripts.b3_e4_f03_l1_candidate_compare import (
    _assembled_macro, _supported_problem,
)
from scripts.b3_e4_f03_l1_physical_injection import physical_injection
from scripts.b3_e4_f03_l1_nested_action import grid, injection


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


def _union_action(problem: dict, segments: int) -> tuple[np.ndarray, np.ndarray]:
    """Complete A+B multiplier-density span without duplicate basis columns.

    A supplies P1 translation/twist and edge-P0 pitch/normal. B contributes
    edge-P0 translation/twist except its last edge: A already contains the
    constant field in each of those four channels. B's pitch/normal patch-P0
    fields are contained in A's edge-P0 fields.
    """
    a, b = (problem["action"][name][:, problem["x"]]
            for name in ("P1_translation_twist_P0_pitch_normal",
                         "P0_translation_twist_pair_P0_pitch_normal"))
    extra = np.array([channel*segments+edge for channel in range(4)
                      for edge in range(segments-1)], dtype=int)
    return np.vstack((a, b[extra])), extra


def _union_injection(coarse_segments: int) -> np.ndarray:
    coarse, fine = grid(coarse_segments), grid(2*coarse_segments)
    ja = injection(coarse, fine, "P1_translation_twist_P0_pitch_normal")
    jb = injection(coarse, fine,
                   "P0_translation_twist_pair_P0_pitch_normal")
    coarse_extra = [channel*coarse_segments+edge for channel in range(4)
                    for edge in range(coarse_segments-1)]
    fine_extra = [channel*(2*coarse_segments)+edge for channel in range(4)
                  for edge in range(2*coarse_segments-1)]
    return linalg.block_diag(ja, jb[np.ix_(fine_extra, coarse_extra)])


@lru_cache(maxsize=2)
def _prepared_action_pair(coarse_segments: int):
    """Reuse immutable reference assembly for each space in one bounded run."""
    cm, fm = (_assembled_macro(n) for n in
              (coarse_segments, 2*coarse_segments))
    cp, fp = (_supported_problem(m, globally_refined=True) for m in (cm, fm))
    xc, xf = cp["x"], fp["x"]
    t = physical_injection(cp, fp, cm, fm)[np.ix_(xf, xc)]
    return cp, fp, t, _physical_operator(cp), _physical_operator(fp)


def action_compliance_decomposition(
        coarse_segments: int = 2, *, space: str = "union") -> dict:
    """Finite-grid full-action Ritz/consistency split, not an F03 tail bound."""
    if coarse_segments not in (2, 4):
        raise ValueError("bounded nested 2:4 or 4:8 grid required")
    if space not in ("union", "P1_translation_twist_P0_pitch_normal",
                     "P0_translation_twist_pair_P0_pitch_normal"):
        raise ValueError("complete admitted A/B action space required")
    cp, fp, t, kc, kf = _prepared_action_pair(coarse_segments)
    xc, xf = cp["x"], fp["x"]
    if space == "union":
        j = _union_injection(coarse_segments)
        bc, _ = _union_action(cp, coarse_segments)
        bf, _ = _union_action(fp, 2*coarse_segments)
    else:
        j = injection(grid(coarse_segments), grid(2*coarse_segments), space)
        bc = cp["action"][space][:, xc]
        bf = fp["action"][space][:, xf]
    action_error = np.max(np.abs(j.T@bf@t-bc))
    if action_error > 1e-10:
        raise AssertionError("complete A+B action is not transported")

    pulled = t.T@kf@t
    fc, ff = bc.T, bf.T@j
    coarse_factor = linalg.cho_factor(kc, lower=True)
    fine_factor = linalg.cho_factor(kf, lower=True)
    pulled_factor = linalg.cho_factor(pulled, lower=True)
    cc = fc.T@linalg.cho_solve(coarse_factor, fc)
    cf = ff.T@linalg.cho_solve(fine_factor, ff)
    embedded = fc.T@linalg.cho_solve(pulled_factor, fc)
    residual = ff-kf@t@linalg.cho_solve(pulled_factor, fc)
    ritz = residual.T@linalg.cho_solve(fine_factor, residual)
    defect = embedded-cc
    for matrix in (cc, cf, embedded, ritz, defect):
        matrix[:] = .5*(matrix+matrix.T)

    # Generalized spectra use the same complete action basis and are
    # invariant under a nonsingular physical change of multiplier units.
    linalg.cho_factor(cf, lower=True)
    ritz_eigen = linalg.eigvalsh(ritz, cf)
    defect_eigen = linalg.eigvalsh(defect, cf)
    coarse_eigen = linalg.eigvalsh(cc, cf)
    diagonal = np.sqrt(np.diag(cf))
    balance = diagonal[:, None]*diagonal[None, :]
    split_error = np.max(np.abs((cf-cc-ritz-defect)/balance))
    ritz_error = np.max(np.abs((cf-embedded-ritz)/balance))
    if split_error > 1e-7 or ritz_error > 1e-7:
        raise AssertionError("full-action compliance decomposition failed")
    return {
        "coarse_edges": coarse_segments,
        "fine_edges": 2*coarse_segments,
        "space": space,
        "multiplier_rows": [bc.shape[0], bf.shape[0]],
        "physical_dofs": [len(xc), len(xf)],
        "action_transport_max_abs": float(action_error),
        "split_max_balanced_error": float(split_error),
        "ritz_identity_max_balanced_error": float(ritz_error),
        "ritz_relative_eigen_min_max": [float(ritz_eigen[0]),
                                        float(ritz_eigen[-1])],
        "consistency_relative_eigen_min_max": [float(defect_eigen[0]),
                                               float(defect_eigen[-1])],
        "coarse_to_fine_relative_compliance_min_max": [
            float(coarse_eigen[0]), float(coarse_eigen[-1])],
        "status": "development finite-grid diagnostic; no tail certificate",
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))

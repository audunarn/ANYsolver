"""Standalone sparse supported-energy screen for the classical F03 comparator.

This is a diagnostic of the elastic primal block, not an inf-sup or native
B3-GE/E4-PL qualification. A negative Rayleigh quotient is a direct witness;
an apparently positive Lanczos result alone is not a positivity certificate.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.sparse import linalg as sparse_linalg

import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_shell as shell


def screen_supported_energy(
    stiffness: sparse.spmatrix,
    supports: np.ndarray,
    *,
    tolerance: float = 1e-9,
    maxiter: int | None = None,
) -> dict:
    """Screen the smallest *algebraic* mode after eliminating fixed DOFs.

    Jacobi congruence preserves inertia and tempers displacement/rotation
    scaling. The negative result is backed by an actual free-vector energy,
    whereas the nonnegative result means only that Lanczos found no negative
    mode to the stated tolerance. No dense global matrix is formed.
    """
    k = sparse.csr_matrix(stiffness)
    if k.ndim != 2 or k.shape[0] != k.shape[1] or k.shape[0] < 3:
        raise ValueError("expected a square sparse stiffness of order >= 3")
    support = np.asarray(supports)
    if (support.ndim != 1 or not np.issubdtype(support.dtype, np.integer)
            or len(np.unique(support)) != len(support)
            or np.any(support < 0) or np.any(support >= k.shape[0])):
        raise ValueError("invalid supported DOF indices")
    if not 0 < tolerance < 1 or (maxiter is not None and maxiter < 1):
        raise ValueError("invalid eigensolver controls")
    free = np.setdiff1d(np.arange(k.shape[0]), support)
    if len(free) < 2:
        raise ValueError("at least two free DOFs required")
    a = k[free, :][:, free].tocsr()
    if not np.all(np.isfinite(a.data)):
        raise ValueError("nonfinite supported stiffness")
    scale = max(float(np.max(np.abs(a.data), initial=0.)), 1e-300)
    skew = a - a.T
    skew_ratio = float(np.max(np.abs(skew.data), initial=0.)) / scale
    if skew_ratio > 1e-12:
        raise ValueError("asymmetric supported stiffness")
    diagonal = a.diagonal()
    if np.any(diagonal <= 0):
        index = int(np.argmin(diagonal))
        return {"status": "negative_or_zero_diagonal", "free_dof": int(free[index]),
                "physical_diagonal": float(diagonal[index]), "free_count": len(free),
                "skew_ratio": skew_ratio}
    d = sparse.diags(1 / np.sqrt(diagonal), format="csr")
    normalized = (d @ a @ d).tocsr()
    if not np.all(np.isfinite(normalized.data)):
        raise ValueError("supported stiffness scaling is not representable")
    # SA, unlike shift-invert around zero, searches the negative end of the
    # spectrum even when an unrelated positive mode is very close to zero.
    try:
        values, vectors = sparse_linalg.eigsh(
            normalized, k=1, which="SA", tol=tolerance, maxiter=maxiter
        )
    except sparse_linalg.ArpackNoConvergence as exc:
        raise RuntimeError("smallest-algebraic energy screen did not converge") from exc
    z = vectors[:, 0]
    quotient = float(z @ (normalized @ z) / (z @ z))
    residual = float(np.linalg.norm(normalized @ z - quotient*z))
    # A Ritz value is not a lower bound for the true minimum. It does,
    # however, provide an explicit negative-energy displacement when negative.
    threshold = 10*tolerance*max(1., float(sparse_linalg.norm(normalized, ord=np.inf)))
    if not np.isfinite(threshold):
        raise ValueError("supported energy threshold is not representable")
    status = ("negative_witness" if quotient < -threshold else
              "no_negative_found" if quotient > threshold and residual <= threshold
              else "inconclusive")
    return {"status": status, "free_count": len(free),
            "smallest_algebraic_ritz": float(values[0]),
            "rayleigh_quotient": quotient, "residual_norm": residual,
            "witness_threshold": threshold, "skew_ratio": skew_ratio}


def screen_f03(ns: int, ny: int, nb: int, topology: str, **kwargs: object) -> dict:
    """Assemble only the classical supported primal shell and beam blocks."""
    model = shell.panel(ns, ny, topology)
    stiffness = sparse.block_diag(
        (shell.stiffness(model), beam.assembled_stiffness(nb)), format="csr"
    )
    supports = np.r_[model.supported,
                     model.dof_count + beam.root_dofs(nb)]
    return screen_supported_energy(stiffness, supports, **kwargs)

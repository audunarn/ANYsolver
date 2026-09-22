"""Bounded classical P0 axial Schur screen using a spectral dual enclosure.

This assembles only supported, small-strain reference operators. Its finite
dimensional eigenvalues do not select a native B3-GE/E4-PL interface law.
"""

from __future__ import annotations

import numpy as np
from scipy import linalg, sparse
from scipy.sparse import linalg as sparse_linalg

import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling
from _b3_e4_f03_supported_energy import screen_supported_energy
from _b3_e4_f03_p0_dual_norm import p0_dual_gram


def screen(ns: int, ny: int, nb: int, nm: int, topology: str,
           *, last_mode: int = 1023, retain_matrices: bool = False):
    """Bracket the minimum axial beta in a fixed classical P0 space.

    Conditional on the previously derived positive supported primal energy,
    the Gram lower/upper matrices are analytic Loewner formulas evaluated
    in floating point. The reported beta bracket is correspondingly a
    numerical screen, not a certified interval bound or an SPD proof.
    """
    if (topology not in ("Q4", "CST-CB") or
            any(type(v) is not int for v in (ns, ny, nb, nm)) or
            not 1 <= ns <= 16 or not 2 <= ny <= 16 or
            not 1 <= nb <= 128 or not 1 <= nm <= 64):
        raise ValueError("unsupported bounded classical P0 patch")
    model = shell.panel(ns, ny, topology)
    ks = shell.stiffness(model)
    kb = beam.assembled_stiffness(nb)
    cs, cb, _ = line.coupling(model, nb, nm, "P0")
    k = sparse.block_diag((ks, kb), format="csr")
    c = sparse.hstack((-cs, cb), format="csr")
    supported = np.r_[model.supported, model.dof_count + beam.root_dofs(nb)]
    energy = screen_supported_energy(k, supported)
    if energy["status"] != "no_negative_found":
        raise ValueError("supported primal energy screen is not positive")
    free = np.setdiff1d(np.arange(k.shape[0]), supported)
    scaled = scaling.build(k, c, np.zeros(k.shape[0]), free,
                           model.dof_count, nb, nm, "P0")
    n = len(free)
    kbar = scaled.matrix[:n, :n].tocsc()
    b = (c[:, free] @ sparse.diags(
        scaled.physical_coordinate_scale / scaling.U0)).tocsr()
    axial_rows = np.arange(0, 3 * nm, 3)
    ba = b[axial_rows, :]
    kskew = kbar - kbar.T
    relative_skew = float(np.max(np.abs(kskew.data), initial=0.)) / max(
        float(np.max(np.abs(kbar.data), initial=0.)), 1e-300)
    if relative_skew > 1e-10:
        raise ValueError("asymmetric supported primal energy")
    lu = sparse_linalg.splu(kbar)
    rhs = ba.T.toarray()
    solution = lu.solve(rhs)
    errors = kbar @ solution - rhs
    solve_residual = float(np.max(np.linalg.norm(errors, axis=0) /
                                  np.maximum(np.linalg.norm(rhs, axis=0), 1e-300)))
    raw = np.asarray(ba @ solution)
    schur_skew = float(np.max(np.abs(raw - raw.T))) / max(
        float(np.max(np.abs(raw))), 1e-300)
    if not np.all(np.isfinite(raw)) or schur_skew > 1e-10:
        raise ValueError("invalid axial Schur operator")
    schur = (raw + raw.T) / 2  # Roundoff after checking the unmodified form.
    lower, upper = p0_dual_gram(nm, 1.0, last_mode)
    # H_lower <= H_true <= H_upper reverses the generalized minimum bounds.
    value_lower, vector = linalg.eigh(schur, upper, subset_by_index=(0, 0))
    value_upper = linalg.eigh(schur, lower, eigvals_only=True,
                              subset_by_index=(0, 0))[0]
    witness = vector[:, 0]
    eigen_residual = float(np.linalg.norm(
        schur @ witness - value_lower[0] * upper @ witness) /
        max(np.linalg.norm(schur @ witness) +
            np.linalg.norm(value_lower[0] * upper @ witness), 1e-300))
    if (not np.isfinite(value_lower[0]) or not np.isfinite(value_upper) or
            value_lower[0] <= 0 or value_upper < value_lower[0] or
            solve_residual > 1e-9 or eigen_residual > 1e-8):
        raise ValueError("unresolved classical P0 axial screen")
    result = dict(topology=topology,
                  mesh=dict(n_s=ns, n_y=ny, n_beam=nb, n_mortar=nm),
                  axial_beta_lower=float(np.sqrt(value_lower[0])),
                  axial_beta_upper=float(np.sqrt(value_upper)),
                  relative_beta_enclosure_width=float(
                      np.sqrt(value_upper / value_lower[0]) - 1),
                  maximum_stiffness_solve_residual=solve_residual,
                  axial_eigen_residual=eigen_residual,
                  primal_relative_skew=relative_skew,
                  schur_relative_skew=schur_skew,
                  physical_free=n, multiplier_rows=c.shape[0],
                  coupling_nnz=c.nnz, primal_nnz=kbar.nnz,
                  supported_energy_screen=energy)
    if retain_matrices:
        return result, dict(schur=schur.copy(), dual_lower=lower.copy(),
                            dual_upper=upper.copy(), coupling_axial=ba.copy(),
                            primal=kbar.copy())
    return result

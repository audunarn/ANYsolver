"""Preparatory exact-space embedding and energy identity for F03 Qp.

No physical refinement conclusion follows from the nested algebraic identity.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scripts._b3_e4_f03_conforming_qp_energy import QpOperators
from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import E0, U0, YAW_LENGTH
from scripts._b3_e4_f03_qp_piecewise_moment_oracle import PiecewisePadMomentOracle


@dataclass(frozen=True)
class NestedIdentity:
    coarse_energy: float
    fine_energy: float
    difference_energy: float
    defect_scaled: float
    load_embedding_scaled: float
    root_embedding_scaled: float
    tip_embedding_scaled: float


def _same_physics(coarse: FinitePadQpTrace, fine: FinitePadQpTrace) -> bool:
    p_nested = (coarse.p < fine.p and coarse.x == fine.x and
                coarse.y == fine.y)
    h_nested = (coarse.p == fine.p and coarse.y == fine.y and
                coarse.x[0] == fine.x[0] and
                coarse.x[-1] == fine.x[-1] and
                len(coarse.x) < len(fine.x) and
                all(edge in fine.x for edge in coarse.x))
    return ((p_nested or h_nested) and coarse.offsets == fine.offsets and
            coarse.a == fine.a and coarse.j == fine.j)


def prolongate(coarse: FinitePadQpTrace, fine: FinitePadQpTrace,
               q: np.ndarray) -> np.ndarray:
    """Evaluate the same continuous cell polynomial on nested p or x nodes."""
    if (not isinstance(coarse, FinitePadQpTrace) or
            not isinstance(fine, FinitePadQpTrace) or
            not _same_physics(coarse, fine)):
        raise ValueError("nested Qp levels must share physical geometry and pads")
    source = np.asarray(q, dtype=float)
    if source.shape != (2*coarse.n,) or not np.isfinite(source).all():
        raise ValueError("invalid coarse full nodal field")
    coefficients = PiecewisePadMomentOracle(
        coarse.p, x=coarse.x, y=coarse.y, offsets=coarse.offsets,
        halfwidth=coarse.a, j=coarse.j).coefficients(source)
    result = np.empty((2, fine.nx, fine.ny))
    for ix, x in enumerate(fine.nodes_x):
        i = min(int(np.searchsorted(coarse.x, x, side="right")-1),
                len(coarse.x)-2)
        hx = coarse.x[i+1]-coarse.x[i]
        px = (2*(x-coarse.x[i])/hx-1)**np.arange(coarse.p+1)
        for iy, y in enumerate(fine.nodes_y):
            k = min(int(np.searchsorted(coarse.y, y, side="right")-1),
                    len(coarse.y)-2)
            hy = coarse.y[k+1]-coarse.y[k]
            py = (2*(y-coarse.y[k])/hy-1)**np.arange(coarse.p+1)
            result[:, ix, iy] = np.einsum(
                "cab,a,b->c", coefficients[:, i, k], px, py)
    return result.reshape(-1)


def evaluate_nested_identity(coarse: QpOperators, fine: QpOperators,
                             coarse_q: np.ndarray,
                             fine_q: np.ndarray) -> NestedIdentity:
    """Measure exact Ritz energy embedding without inferring continuum error."""
    if (not isinstance(coarse, QpOperators) or
            not isinstance(fine, QpOperators) or
            not _same_physics(coarse.trace, fine.trace)):
        raise ValueError("incompatible bounded Qp operator levels")
    qc, qf = np.asarray(coarse_q, dtype=float), np.asarray(fine_q, dtype=float)
    if (qc.shape != (coarse.dof_count,) or qf.shape != (fine.dof_count,) or
            not np.isfinite(qc).all() or not np.isfinite(qf).all()):
        raise ValueError("invalid reduced Qp state")
    coarse_full = np.zeros(2*coarse.trace.n)
    coarse_full[coarse.free_columns] = qc
    embedded_full = prolongate(coarse.trace, fine.trace, coarse_full)
    embedded = embedded_full[fine.free_columns]
    kc = coarse.shell_stiffness+coarse.beam_stiffness
    kf = fine.shell_stiffness+fine.beam_stiffness
    delta = qf-embedded
    uc = float(qc@(kc@qc)/2)
    uf = float(qf@(kf@qf)/2)
    adiff = float(delta@(kf@delta)/2)
    scale = max(E0, abs(uc)+abs(uf)+abs(adiff))
    load_gap = float(abs(coarse.load@qc-fine.load@embedded)/E0)
    pose_scale = np.array((1/U0, 1/U0, YAW_LENGTH/U0))
    root_coarse = pose_scale*(coarse.root_constraint@qc)
    root_fine = pose_scale*(fine.root_constraint@embedded)
    tip_coarse = pose_scale*(coarse.tip_pose@qc)
    tip_fine = pose_scale*(fine.tip_pose@embedded)
    root_scale = max(1., float(np.max(np.abs(root_coarse))),
                     float(np.max(np.abs(root_fine))))
    tip_scale = max(1., float(np.max(np.abs(tip_coarse))),
                    float(np.max(np.abs(tip_fine))))
    return NestedIdentity(
        uc, uf, adiff, abs((uf-uc)-adiff)/scale, load_gap,
        float(np.max(np.abs(root_coarse-root_fine))/root_scale),
        float(np.max(np.abs(tip_coarse-tip_fine))/tip_scale),
    )

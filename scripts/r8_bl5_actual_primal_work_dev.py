"""Restrict the declared flat F03 auxiliary norm to actual BL5 owner work.

Development algebra only: this supplies neither an independent multiplier
dual nor an F03 quotient. It admits one straight, zero-lift native line with
coordinate-selection supports and a flat +Z Q4/S3 shell.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse

from scripts.b3_e4_bl5_riesz_controls_dev import beam_norm
from scripts.r8_bl5_mixed_shell_h1_dev import supported_shell_h1


def actual_flat_primal_work(owner, ell: float, width: float):
    """Return (supported H, full-owner embedding E, actual row work C E).

    The beam auxiliary arm is taken from every compiled BL5 reference station;
    it is never inferred from a nominal section or an unverified sign.
    """
    definition = owner._definition
    if (len(definition.lines) != 1 or definition.points or definition.footprints or
            not owner._line_samples or not np.isfinite(ell) or ell <= 0. or
            not np.isfinite(width) or width < 0.):
        raise ValueError("one flat BL5 line and positive auxiliary scales required")
    samples = tuple(sample[0] for sample in owner._line_samples)
    if any(type(sample).__name__ != "BL5LocalOperator" for sample in samples):
        raise ValueError("actual BL5 line operators required")
    arm = np.asarray(samples[0].reference_arm, dtype=float)
    if any(not np.allclose(sample.reference_arm, arm, rtol=0., atol=2e-13)
           or not np.allclose(sample.reference_director, (0., 0., 1.), rtol=0., atol=2e-13)
           or not np.allclose(sample.port.frame, np.eye(3), rtol=0., atol=2e-13)
           or not np.allclose(sample.port.lift, 0., rtol=0., atol=2e-13)
           for sample in samples):
        raise ValueError("constant flat zero-lift BL5 reference required")
    if not np.allclose(arm[:2], 0., rtol=0., atol=2e-13):
        raise ValueError("transverse beam auxiliary arm required")

    shell = definition.shell
    shell_xyz = np.asarray(owner._shell_xyz, dtype=float)
    if (shell_xyz.shape != (len(owner._shell_ids), 3) or
            not np.allclose(shell_xyz[:, 2], 0., rtol=0., atol=2e-13)):
        raise ValueError("flat +Z shell reference required")
    shell_index = owner._shell_index
    elements = tuple(tuple(shell_index[node] for node in cell)
                     for cell in (*shell.q4_elements, *shell.s3_elements))
    shell_fixed = tuple((shell_index[support.node], support.component)
                        for support in definition.fixed if support.domain == "shell")
    h_shell, _shell_active, shell_embedding = supported_shell_h1(
        shell_xyz[:, :2], elements, ell, shell_fixed)

    beam_ids = owner._beam_ids
    positions = np.array([owner._beam_nodes[node][0] for node in beam_ids])
    frames = np.array([owner._beam_nodes[node][1] for node in beam_ids])
    cells = len(beam_ids)-1
    if definition.lines[0].beam_halfcells != tuple(
            (member, cell) for member in range(len(owner._beam_parts))
            for cell in (0, 1)):
        raise ValueError("complete ordered native half-cell line required")
    if (cells < 2 or cells != 2*len(owner._beam_parts) or
            not np.allclose(frames, np.eye(3), rtol=0., atol=2e-13) or
            not np.allclose(positions[:, 1], 0., rtol=0., atol=2e-13) or
            not np.allclose(positions[:, 2], positions[0, 2], rtol=0., atol=2e-13) or
            not np.all(np.diff(positions[:, 0]) > 0.)):
        raise ValueError("ordered straight native half-cell chain required")
    length = float(positions[-1, 0]-positions[0, 0])
    knots, h_beam, beam_active, _ = beam_norm(
        length, ell, cells, 1, arm, width)
    if not np.allclose(positions[:, 0]-positions[0, 0], knots,
                       rtol=0., atol=2e-13):
        raise ValueError("uniform native half-cell coordinates required")
    for member, (element, _slots, _origin) in enumerate(owner._beam_parts):
        if tuple(element.node_ids) != tuple(beam_ids[2*member:2*member+3]):
            raise ValueError("native element and half-cell ordering required")

    nodal = 6*len(beam_ids)
    if owner._beam_count != nodal+24*len(owner._beam_parts):
        raise ValueError("native retained layout required")
    rows, columns = [], []
    for node in range(len(beam_ids)):
        for axis in range(3):
            rows.append(6*node+axis)
            columns.append(3*node+axis)
    for cell in range(cells):
        for axis in range(3):
            rows.append(nodal+24*(cell//2)+3*(cell%2)+axis)
            columns.append(3*len(beam_ids)+3*cell+axis)
    full_beam = sparse.coo_matrix((np.ones(len(rows)), (rows, columns)),
                                  shape=(owner._beam_count,
                                         3*len(beam_ids)+3*cells)).tocsc()
    beam_embedding = full_beam[:, beam_active]
    embedding = sparse.block_diag((shell_embedding, beam_embedding), format="csc")
    if embedding.shape[0] != owner._K.shape[0] or embedding[owner._fixed].nnz:
        raise ValueError("unsupported physical support restriction")
    inactive = np.intersect1d(
        owner._free, np.flatnonzero(np.diff(embedding.tocsr().indptr) == 0))
    omitted = owner._C[:, inactive].copy().tocsr()
    omitted.eliminate_zeros()
    if omitted.nnz and np.max(np.abs(omitted.data)) > 2e-13:
        raise ValueError("BL5 work reaches omitted native or drilling coordinates")
    h = sparse.block_diag((h_shell, h_beam), format="csc")
    work = (owner._C@embedding).tocsc()
    if work.shape != (owner._C.shape[0], h.shape[0]):
        raise ValueError("actual BL5 row and auxiliary trace layout disagree")
    return h, embedding, work

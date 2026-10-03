"""Sparse graph/interval assessment of two SAVED BL5 development operators.

No owner solve, external execution, scientific protocol or production reduction.
The exact-real target uses saved binary64 K/C and declared physical scales.
Only bounded local inverses are used; the complete physical kernel is sparse.
The explicit symmetric lower completion is a verification representative, never
a repaired solver tangent. Its error to the actual Schur work map is bounded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy import linalg, sparse
from threadpoolctl import threadpool_info

from scripts._b3_e4_f03_sparse_certificate import (
    SparseBudget, validate_sparse, check_arithmetic, _sqrt,
)
from scripts.r8_bl5_sparse_kernel_interval_dev import (
    IntervalBudget, down, up, sum_up, factor_pattern, certify_shifted_lower,
    complete_symbolic_pattern,
)

SB = SparseBudget(2400, 1_000_000, 1, 384*1024**2)
EPS = np.finfo(float).eps


def fro_upper(values):
    """Outward Frobenius bound, scaled before squaring (including subnormals)."""
    data = values.data if sparse.issparse(values) else np.asarray(values).ravel()
    if not np.isfinite(data).all():
        raise ArithmeticError('finite norm operands required')
    magnitude = float(np.max(np.abs(data), initial=0.))
    if not magnitude:
        return 0.
    ratios = up(np.abs(data)/magnitude)
    square = sum_up(up(ratios*ratios))
    return float(up(magnitude*_sqrt(square, True)))


def box_dot(lo, hi, right):
    """Local uncertain left operand times exact stored right (<=24 inner)."""
    lo, hi, right = np.asarray(lo), np.asarray(hi), np.asarray(right)
    if (lo.shape != hi.shape or lo.ndim != 2 or right.ndim != 2 or
            lo.shape[1] != right.shape[0] or lo.shape[1] > 24 or
            max(lo.shape+right.shape) > 256 or np.any(lo > hi) or
            not all(np.isfinite(x).all() for x in (lo, hi, right))):
        raise ValueError('bounded finite ordered local interval operands required')
    low = np.zeros((lo.shape[0], right.shape[1])); high = low.copy()
    for k in range(lo.shape[1]):
        a = lo[:, k, None]*right[None, k, :]
        b = hi[:, k, None]*right[None, k, :]
        low = down(low+down(np.minimum(a, b)))
        high = up(high+up(np.maximum(a, b)))
    return low, high


def box_abs(lo, hi):
    return np.maximum(np.abs(lo), np.abs(hi))


def norm_upper(matrix):
    """Induced2 majorant sqrt(induced1*inducedInfinity), directed sums."""
    absolute = abs(matrix)
    row = absolute.tocsr(); column = absolute.tocsc()
    infnorm = max(sum_up(row.data[row.indptr[j]:row.indptr[j+1]]) for j in range(row.shape[0]))
    onenorm = max(sum_up(column.data[column.indptr[j]:column.indptr[j+1]]) for j in range(column.shape[1]))
    return _sqrt(float(up(onenorm*infnorm)), True)


def inverse_bound(lo, hi):
    """Neumann residual proof for every local D in the box, not LU pivots."""
    n = lo.shape[0]
    if lo.shape != (n, n) or hi.shape != lo.shape or n > 18:
        raise ValueError('square local inverse of order<=18 required')
    midpoint = lo*.5+hi*.5
    w = linalg.solve(midpoint, np.eye(n), assume_a='gen')
    left, right = box_dot(lo, hi, w)
    identity = np.eye(n)
    residual = box_abs(down(identity-right), up(identity-left))
    q1 = max(sum_up(residual[:, j]) for j in range(n))
    qi = max(sum_up(residual[j]) for j in range(n))
    if not max(q1, qi) < 1.:
        raise ArithmeticError('local inverse residual does not establish rank')
    w1 = max(sum_up(np.abs(w[:, j])) for j in range(n))
    wi = max(sum_up(np.abs(w[j])) for j in range(n))
    b1 = float(up(w1/down(1.-q1)))
    bi = float(up(wi/down(1.-qi)))
    return w, _sqrt(float(up(b1*bi)), True), dict(residual_one=q1, residual_inf=qi,
        inverse_one_upper=b1, inverse_inf_upper=bi)


def _gamma(count):
    value = float(up(count*EPS))
    if value >= .1:
        raise ArithmeticError('rounding-count domain exceeded')
    return float(up(value/down(1.-value)))


def sparse_product(a, b):
    """Rounded product and absolute error bound; reject underflowing products.

    EPS=2u and 2*max row-count conservatively cover elementary products/sums.
    Positive absolute accumulation bounds exact |A||B| by fl/(1-gamma).
    This is conditional on ordinary IEEE sparse accumulation, not a backend
    factor certificate. Underflow is explicitly refused rather than erased.
    """
    if a.shape[1] != b.shape[0]:
        raise ValueError('product dimensions differ')
    aa, bb = abs(a).tocsr(), abs(b).tocsr()
    aa.eliminate_zeros(); bb.eliminate_zeros()
    if aa.nnz and bb.nnz:
        smallest = float(down(float(aa.data.min())*float(bb.data.min())))
        if smallest < np.finfo(float).tiny:
            raise ArithmeticError('sparse product underflow domain; no relative bound')
    value = (a@b).tocsr()
    absolute = (aa@bb).tocsr()
    if not np.isfinite(value.data).all() or not np.isfinite(absolute.data).all():
        raise ArithmeticError('nonfinite sparse product')
    count = max(1, int(np.diff(aa.indptr).max(initial=0)))
    gamma = _gamma(2*count)
    error = float(up(up(gamma/down(1.-gamma))*fro_upper(absolute)))
    return value, error


def difference_upper(a, b):
    value = (a-b).tocsr()
    magnitude = (abs(a)+abs(b)).tocsr()
    # The positive two-term sum itself is rounded upward via its bound.
    g = _gamma(2)
    return sum_up([fro_upper(value), float(up(up(g/down(1.-g))*fro_upper(magnitude)))])


def scaled_data(matrix, left, right, divide_left=False):
    """Nearest sparse scaling plus elementary outward boxes, same structure."""
    if (np.asarray(left).shape != (matrix.shape[0],) or
            np.asarray(right).shape != (matrix.shape[1],) or
            not all(np.isfinite(v).all() and np.all(v > 0.) for v in (left, right))):
        raise ValueError('finite positive row/column scales required')
    coo = matrix.tocoo()
    value = coo.data*right[coo.col]
    lo, hi = down(value), up(value)
    if divide_left:
        value = value/left[coo.row]
        lo, hi = down(lo/left[coo.row]), up(hi/left[coo.row])
    else:
        value = value*left[coo.row]
        lo, hi = down(lo*left[coo.row]), up(hi*left[coo.row])
    # An exact zero times finite positive scale is exactly zero.
    zero = coo.data == 0.
    value[zero] = lo[zero] = hi[zero] = 0.
    def build(data):
        return sparse.coo_matrix((data, (coo.row, coo.col)), shape=matrix.shape).tocsr()
    return build(value), build(lo), build(hi)


def graph_kernel(c, clo, chi, groups, pivots):
    """Complete exact-kernel graph from disjoint bounded local D blocks.

    For each true C in its boxes, Z*=[I;-D^-1 E]. Local residual enclosures
    bound ||Zhat-Z*||F. Identity rows give full column rank. No rows are removed.
    """
    check_arithmetic()  # Before ANY inverse/graph residual bounds.
    c = validate_sparse(c, SB, square=False)
    clo = validate_sparse(clo, SB, square=False)
    chi = validate_sparse(chi, SB, square=False)
    if (clo.shape != c.shape or chi.shape != c.shape or
            np.any((clo-c).data > 0.) or np.any((c-chi).data > 0.)):
        raise ValueError('constraint boxes must enclose the stored representative')
    m, n = c.shape
    all_rows = np.concatenate(groups); all_pivots = np.concatenate(pivots)
    if (len(all_rows) != m or set(map(int, all_rows)) != set(range(m)) or
            len(all_pivots) != m or len(set(map(int, all_pivots))) != m or
            np.any(all_pivots < 0) or np.any(all_pivots >= n)):
        raise ValueError('complete unique rows and physical pivot inventory required')
    independent = np.setdiff1d(np.arange(n), all_pivots)
    lookup = np.full(n, -1, dtype=int); lookup[independent] = np.arange(n-m)
    rows, cols, data = list(independent), list(range(n-m)), [1.]*(n-m)
    bounds, details = [], []
    for group, pivot in zip(groups, pivots, strict=True):
        if len(group) != len(pivot) or not 1 <= len(group) <= 18:
            raise ValueError('bounded square support pivot required')
        foreign = np.setdiff1d(all_rows, group)
        if any(matrix[foreign][:, pivot].nnz and np.any(matrix[foreign][:, pivot].data)
               for matrix in (c, clo, chi)):
            raise ValueError('pivot couples another support; no block-diagonal D proof')
        active = np.unique(c[group][:, independent].nonzero()[1])
        # Nonzero true entries cannot hide behind a rounded exact zero.
        union = np.unique(np.concatenate([matrix[group][:, independent].nonzero()[1]
                                         for matrix in (clo, chi)]))
        active = np.union1d(active, union)
        if len(active) > 256:
            raise ValueError('local graph support exceeds256 independent coordinates')
        dl, dh = clo[group][:, pivot].toarray(), chi[group][:, pivot].toarray()
        w, inv, info = inverse_bound(dl, dh)
        el, eh = clo[group][:, independent[active]].toarray(), chi[group][:, independent[active]].toarray()
        e = c[group][:, independent[active]].toarray()
        bhat = -w@e
        rlo, rhi = box_dot(dl, dh, bhat)
        residual = box_abs(down(rlo+el), up(rhi+eh))
        error = float(up(inv*fro_upper(residual)))
        bounds.append(float(up(error*error)))
        rows.extend(np.repeat(pivot, len(active))); cols.extend(np.tile(active, len(pivot)))
        data.extend(bhat.ravel())
        details.append(dict(rows=list(map(int, group)), pivots=list(map(int, pivot)),
            active_columns=len(active), graph_error_fro_upper=error, **info))
    z = sparse.coo_matrix((data, (rows, cols)), shape=(n, n-m)).tocsr()
    z.eliminate_zeros()
    return z, _sqrt(sum_up(bounds), True), details


def stationary_error(k, s_hat, scale, x, blocks):
    """Bound exact-real stationary Schur of saved K versus rounded S_hat.

    For every local block, use inverse-residual and lift-residual enclosures.
    Neither symmetry nor positivity of complete native K is assumed.
    """
    base, bl, bh = scaled_data(k[x][:, x], scale, scale)
    reconstructed = base.copy(); absolute = abs(base)
    error_terms = [fro_upper(box_abs(down(bl.data-base.data), up(bh.data-base.data)))]
    details = []
    for block in blocks:
        d = k[block][:, block].toarray()
        _, inv, proof = inverse_bound(d, d)
        coupling = k[block][:, x]
        neighbours = np.union1d(coupling.nonzero()[1], k[x][:, block].nonzero()[0])
        if len(neighbours) > 24:
            raise ValueError('local stationary neighbourhood exceeds24')
        px = coupling[:, neighbours].toarray()*scale[neighbours]
        pxlo, pxhi = down(px), up(px)
        lift = linalg.solve(d, -px, assume_a='gen')
        rl, rh = box_dot(d, d, lift)
        lift_error = float(up(inv*fro_upper(box_abs(down(rl+pxlo), up(rh+pxhi)))))
        xp = k[x[neighbours]][:, block].toarray()*scale[neighbours, None]
        xplo, xphi = down(xp), up(xp)
        ul, uh = box_dot(xplo, xphi, lift)
        update = xp@lift
        arithmetic_error = fro_upper(box_abs(down(ul-update), up(uh-update)))
        local_error = sum_up([arithmetic_error, float(up(fro_upper(box_abs(xplo, xphi))*lift_error))])
        error_terms.append(local_error)
        rr, cc = np.repeat(neighbours, len(neighbours)), np.tile(neighbours, len(neighbours))
        u = sparse.coo_matrix((update.ravel(), (rr, cc)), shape=base.shape).tocsr()
        reconstructed += u; absolute += abs(u)
        details.append(dict(**proof, lift_error_fro_upper=lift_error,
                            schur_update_error_fro_upper=local_error))
    g = _gamma(2*(len(blocks)+1))
    error_terms.extend([float(up(up(g/down(1.-g))*fro_upper(absolute))),
                        difference_upper(reconstructed, s_hat)])
    return sum_up(error_terms), details


def saved_csr(data, name, square=True):
    matrix = sparse.csr_matrix((data[name+'_data'].copy(), data[name+'_indices'].copy(),
        data[name+'_indptr'].copy()), shape=tuple(data[name+'_shape']))
    return validate_sparse(matrix, SB, square=square)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assess(owner, kernel, output):
    check_arithmetic()
    started = time.monotonic(); owner, kernel, output = map(Path, (owner, kernel, output))
    if output.exists() or output.with_suffix('.npz').exists() or not output.parent.is_dir():
        raise ValueError('new paired outputs and existing parent required')
    report = dict(status='FAILED', scope='saved-development-operators-only; no formal F03/qualification',
        formal_f03_authority_consumed=False, source_sha256=sha(__file__),
        dependencies={name: sha(Path(__file__).parent/name) for name in
            ('r8_bl5_sparse_kernel_interval_dev.py', '_b3_e4_f03_sparse_certificate.py')},
        inputs={str(path): sha(path) for path in (owner/'native/operators.npz', owner/'native/inputs.json',
            owner/'summary.json', kernel, kernel.with_suffix('.npz'))},
        effective_pools=threadpool_info(), arrays={})
    arrays = {}
    try:
        if any(pool['num_threads'] != 1 for pool in report['effective_pools']):
            raise ValueError('actual pools1 required for this saved screen')
        metadata = json.loads((owner/'native/inputs.json').read_text())
        predecessor = json.loads(kernel.read_text())
        if (predecessor['fixture_case'] not in ('whole_half', 'whole_double') or
                predecessor['status'] != 'COMPLETED_DEVELOPMENT_ONLY' or
                not predecessor['minimum_kernel_eigenvalue'] > predecessor['spectral_uncertainty']):
            raise ValueError('only two exact saved reciprocal development fixtures admitted')
        for name in ('operators.npz', 'inputs.json'):
            if sha(owner/'native'/name) != predecessor['source_files'][name]:
                raise ValueError('saved predecessor operator/input binding differs')
        if (sha(owner/'summary.json') != predecessor['source_files']['summary.json'] or
                sha(kernel.with_suffix('.npz')) != predecessor['output_npz_sha256']):
            raise ValueError('saved predecessor summary/archive binding differs')
        with np.load(owner/'native/operators.npz', allow_pickle=False) as data:
            k, c = saved_csr(data, 'K'), saved_csr(data, 'C', square=False)
            nshell, nbeam = len(data['shell_node_ids']), len(data['beam_node_ids'])
        with np.load(kernel.with_suffix('.npz'), allow_pickle=False) as data:
            s = saved_csr(data, 'S'); x = data['physical_slots'].copy()
            pp = data['resultant_slots'].copy(); scale = data['physical_scale'].copy()
            row_scale = data['constraint_row_scale'].copy()
        if c[:, pp].nnz or len(x) != predecessor['physical_order'] or len(pp)%18:
            raise ValueError('actual physical/resultant partition differs')
        fixture = predecessor['fixture']; halfcells = fixture['halfcells']
        if nshell != 85 or nbeam != halfcells+1 or halfcells not in (16, 64):
            raise ValueError('exact unchanged saved reciprocal geometry required')
        blocks = pp.reshape(-1, 18)
        offblock = k[pp][:, pp]-sparse.block_diag([k[p][:, p] for p in blocks])
        if np.any(offblock.data):
            raise ValueError('nonlocal resultant coupling not admitted')
        shat, _, _ = scaled_data(s, scale, scale)
        chat, clo, chi = scaled_data(c[:, x], row_scale, scale, divide_left=True)
        supports = metadata['supports']; groups, pivots = [], []
        physical_map = {int(slot): index for index, slot in enumerate(x)}
        nodal = 6*(nshell+nbeam)
        for support in supports:
            cells = support['native_halfcells']; begin, h = min(cells), len(cells)
            if cells != list(range(begin, begin+h)) or h%4:
                raise ValueError('coherent quarter support inventory required')
            a, b = begin+h//4, begin+3*h//4
            full = [6*(nshell+node)+axis for node in (a, b) for axis in range(3)]
            full += [nodal+24*(cell//2)+3*(cell%2)+axis for cell in (a, b) for axis in (0, 1)]
            groups.append(np.asarray(support['multiplier_rows'], dtype=int))
            pivots.append(np.asarray([physical_map[slot] for slot in full], dtype=int))
        z, ez, graph = graph_kernel(chat, clo, chi, groups, pivots)
        es, local = stationary_error(k, shat, scale, x, blocks)
        zn, sn = norm_upper(z), norm_upper(shat)
        first, e1 = sparse_product(shat, z)
        ahat, e2 = sparse_product(z.T.tocsr(), first)
        lower = sparse.tril(ahat, format='csr')
        representative = (lower+sparse.tril(ahat, -1, format='csr').T).tocsr()
        triangle = difference_upper(ahat, representative)
        true_zn = float(up(zn+ez))
        graph_error = float(up(up(up(2*zn*ez)+up(ez*ez))*sn))
        operator_error = float(up(up(true_zn*true_zn)*es))
        epsilon = sum_up([graph_error, operator_error, float(up(zn*e1)), e2, triangle])
        shift = float(up(2*epsilon))
        metric_upper = float(up(true_zn*true_zn))
        report.update(fixture_case=predecessor['fixture_case'], physical_order=len(x),
            kernel_order=z.shape[1], constraint_rows=chat.shape[0], graph_local_proofs=graph,
            stationary_local_proofs=local, graph_error_fro_upper=ez,
            stationary_operator_error_fro_upper=es, kernel_error_upper=epsilon,
            error_terms=dict(graph=graph_error, stationary=operator_error,
                first_product=float(up(zn*e1)), second_product=e2, triangle=triangle),
            graph_metric_upper=metric_upper, fixed_shift=shift,
            saved_dense_minimum=predecessor['minimum_kernel_eigenvalue'])
        for name, matrix in (('Z', z), ('A_representative', representative)):
            arrays.update({name+'_data': matrix.data, name+'_indices': matrix.indices,
                name+'_indptr': matrix.indptr, name+'_shape': np.asarray(matrix.shape)})
        backend_pattern, order = factor_pattern(representative)
        pattern = complete_symbolic_pattern(representative, order)
        proof = certify_shifted_lower(representative, pattern, order, shift=shift)
        arrays.update(pivot_lower=proof.pop('pivot_lower'), pivot_upper=proof.pop('pivot_upper'),
            permutation=np.asarray(order), physical_slots=x)
        margin = float(down(down(shift-epsilon)/metric_upper))
        report.update(interval_proof=proof,
            backend_pattern_nnz=backend_pattern.nnz, complete_pattern_nnz=pattern.nnz,
            physical_kernel_lower_bound=margin if proof['status']=='POSITIVE_SHIFTED_LOWER_COMPLETION' else None,
            status='POSITIVE_SAVED_MECHANICAL_KERNEL_DEVELOPMENT_ONLY' if
                proof['status']=='POSITIVE_SHIFTED_LOWER_COMPLETION' and margin > 0. else 'HOLD_CERTIFICATE',
            limitation='No eigenvalue equality with orthonormal QR; no full native K SPD/inertia, uniform family or qualification claim.')
    except BaseException as error:
        report['error'] = dict(type=type(error).__name__, detail=str(error)); raise
    finally:
        report['elapsed_seconds'] = time.monotonic()-started
        np.savez_compressed(output.with_suffix('.npz'), **arrays)
        report['arrays_sha256'] = sha(output.with_suffix('.npz'))
        output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({key: report[key] for key in ('status', 'fixture_case', 'physical_order',
        'kernel_error_upper', 'physical_kernel_lower_bound', 'elapsed_seconds')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner', required=True); parser.add_argument('--kernel', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(); assess(args.owner, args.kernel, args.output)

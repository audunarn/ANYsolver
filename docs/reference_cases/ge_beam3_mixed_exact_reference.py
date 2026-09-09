"""Exact reference-linear certificate for the GE-B3 mixed macroelement.

This research-only module reconstructs two lowest-order cells directly from
the mixed complementary potential.  It intentionally imports neither
``anysolver`` nor the V1/legacy beam implementations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path
from typing import Any


N_EXTERNAL = 18
N_INTERNAL = 18
N_TOTAL = N_EXTERNAL + N_INTERNAL
CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_K1_MACRO_V2"
FORMULATION_ID = "GE_BEAM3_DC_MIXED_K1_MACRO_V2"
SCHEMA = "anysolver.ge-beam3-mixed-exact-linear-certificate-v1"


def zeros(rows, cols):
    return [[F(0) for _ in range(cols)] for _ in range(rows)]


def transpose(a):
    return [list(row) for row in zip(*a)]


def matmul(a, b):
    bt = transpose(b)
    return [[sum(x * y for x, y in zip(row, col)) for col in bt] for row in a]


def add(a, b, scale=F(1)):
    return [[x + scale * y for x, y in zip(ar, br)] for ar, br in zip(a, b)]


def inverse(a):
    n = len(a)
    aug = [row[:] + [F(i == j) for j in range(n)] for i, row in enumerate(a)]
    for col in range(n):
        pivot = next(row for row in range(col, n) if aug[row][col])
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        aug[col] = [value / scale for value in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            if factor:
                aug[row] = [x - factor * y for x, y in zip(aug[row], aug[col])]
    return [row[n:] for row in aug]


def rank(a):
    work = [row[:] for row in a]
    rows, cols = len(work), len(work[0])
    pivot_row = 0
    for col in range(cols):
        pivot = next((row for row in range(pivot_row, rows) if work[row][col]), None)
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        scale = work[pivot_row][col]
        work[pivot_row] = [value / scale for value in work[pivot_row]]
        for row in range(rows):
            if row == pivot_row:
                continue
            factor = work[row][col]
            if factor:
                work[row] = [x - factor * y for x, y in zip(work[row], work[pivot_row])]
        pivot_row += 1
        if pivot_row == rows:
            break
    return pivot_row


def block(a, rows, cols):
    return [[a[i][j] for j in cols] for i in rows]


def ldl_pivots(a):
    n = len(a)
    l = zeros(n, n)
    d = [F(0) for _ in range(n)]
    for i in range(n):
        l[i][i] = F(1)
        d[i] = a[i][i] - sum(l[i][k] * l[i][k] * d[k] for k in range(i))
        if not d[i]:
            raise RuntimeError(f"zero LDL pivot {i}")
        for j in range(i + 1, n):
            l[j][i] = (a[j][i] - sum(l[j][k] * l[i][k] * d[k] for k in range(i))) / d[i]
    return d


def stiffness():
    lower = [
        [2, 0, 0, 0, 0, 0],
        [1, 3, 0, 0, 0, 0],
        [0, 1, 2, 0, 0, 0],
        [1, 0, 0, 3, 0, 0],
        [0, 1, 0, 1, 2, 0],
        [0, 0, 1, 0, 1, 2],
    ]
    l = [[F(value) for value in row] for row in lower]
    return matmul(l, transpose(l))


def build_macro(reference_triad=None, section=None):
    q0 = reference_triad or [[F(i == j) for j in range(3)] for i in range(3)]
    c = section or stiffness()
    a = block(c, range(3), range(3))
    b = block(c, range(3), range(3, 6))
    d = block(c, range(3, 6), range(3, 6))
    dinv = inverse(d)
    hessian = zeros(N_TOTAL, N_TOTAL)
    ell = F(1, 2)

    def add_product(left, right, coefficient):
        for i, li in enumerate(left):
            if not li:
                continue
            for j, rj in enumerate(right):
                if not rj:
                    continue
                hessian[i][j] += coefficient * li * rj
                hessian[j][i] += coefficient * li * rj

    for cell, (node_a, node_b) in enumerate(((0, 1), (1, 2))):
        beta_start = N_EXTERNAL + cell * 9
        moment_left_start = beta_start + 3
        moment_right_start = beta_start + 6
        gamma = zeros(3, N_TOTAL)
        # R0^T * du/ds.
        for local in range(3):
            for spatial in range(3):
                value = q0[spatial][local] / ell
                gamma[local][node_b * 6 + spatial] += value
                gamma[local][node_a * 6 + spatial] -= value
        # + e1 cross beta(local).
        gamma[1][beta_start + 2] -= 1
        gamma[2][beta_start + 1] += 1
        gt_ag = matmul(transpose(gamma), matmul(a, gamma))
        hessian = add(hessian, gt_ag, ell)

        # y_endpoint = moment_endpoint - B^T gamma.
        y = []
        for moment_start in (moment_left_start, moment_right_start):
            endpoint = zeros(3, N_TOTAL)
            bt_gamma = matmul(transpose(b), gamma)
            for component in range(3):
                endpoint[component][moment_start + component] = 1
                endpoint[component] = [x - z for x, z in zip(endpoint[component], bt_gamma[component])]
            y.append(endpoint)
        mass = [[ell * F(1, 3), ell * F(1, 6)], [ell * F(1, 6), ell * F(1, 3)]]
        for p in range(2):
            for q in range(2):
                term = matmul(transpose(y[p]), matmul(dinv, y[q]))
                hessian = add(hessian, term, -mass[p][q])

        # [Log(QE^T QV).M]_left^right at the reference-linear state.
        for sign, node, moment_start in ((F(-1), node_a, moment_left_start), (F(1), node_b, moment_right_start)):
            for local in range(3):
                rotation_form = [F(0) for _ in range(N_TOTAL)]
                for spatial in range(3):
                    rotation_form[node * 6 + 3 + spatial] += q0[spatial][local]
                rotation_form[beta_start + local] -= 1
                moment_form = [F(0) for _ in range(N_TOTAL)]
                moment_form[moment_start + local] = 1
                add_product(rotation_form, moment_form, sign)

    external = range(N_EXTERNAL)
    internal = range(N_EXTERNAL, N_TOTAL)
    kee = block(hessian, external, external)
    kei = block(hessian, external, internal)
    kie = transpose(kei)
    kii = block(hessian, internal, internal)
    condensed = add(kee, matmul(kei, matmul(inverse(kii), kie)), F(-1))
    return condensed, hessian, kii


def rigid_matrix():
    rigid = zeros(N_EXTERNAL, 6)
    coordinates = (F(0), F(1, 2), F(1))
    for node, x in enumerate(coordinates):
        for component in range(3):
            rigid[node * 6 + component][component] = 1
            rigid[node * 6 + 3 + component][3 + component] = 1
        rigid[node * 6 + 2][4] = -x
        rigid[node * 6 + 1][5] = x
    return rigid


def canonical_bytes(value: Any) -> bytes:
    def validate(item: Any) -> None:
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("nonfinite canonical value")
        if isinstance(item, dict):
            for child in item.values():
                validate(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                validate(child)

    validate(value)
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def build_certificate(*, mutate: str | None = None) -> dict[str, Any]:
    k, full, kii = build_macro()
    if mutate == "condensed_entry":
        k[0][0] += F(1, 101)
    elif mutate not in (None, "section", "reversal"):
        raise ValueError(f"unknown mutation: {mutate}")
    if mutate == "section":
        altered = stiffness()
        altered[0][0] += F(1)
        k, full, kii = build_macro(section=altered)
    rigid = rigid_matrix()
    kr = matmul(k, rigid)
    # leftmost-pivot complement from R^T.
    rt = transpose(rigid)
    work = [row[:] for row in rt]
    pivot_columns = []
    pivot_row = 0
    for col in range(N_EXTERNAL):
        pivot = next((row for row in range(pivot_row, 6) if work[row][col]), None)
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        scale = work[pivot_row][col]
        work[pivot_row] = [v / scale for v in work[pivot_row]]
        for row in range(6):
            if row != pivot_row and work[row][col]:
                factor = work[row][col]
                work[row] = [x - factor * y for x, y in zip(work[row], work[pivot_row])]
        pivot_columns.append(col)
        pivot_row += 1
    free = [index for index in range(N_EXTERNAL) if index not in pivot_columns]
    z = zeros(N_EXTERNAL, len(free))
    for column, row in enumerate(free):
        z[row][column] = 1
    kz = matmul(transpose(z), matmul(k, z))
    pivots = ldl_pivots(kz)

    # Connectivity reversal keeps the physical material-two direction, so
    # R0_rev = R0*diag(-1, 1, -1), while both force and moment strain
    # coordinates transform with -S = diag(1, -1, 1).
    s = [[F(-1), 0, 0], [0, F(1), 0], [0, 0, F(-1)]]
    t3 = [[F(1), 0, 0], [0, F(-1), 0], [0, 0, F(1)]]
    t6 = zeros(6, 6)
    for offset in (0, 3):
        for i in range(3):
            for j in range(3):
                t6[offset + i][offset + j] = t3[i][j]
    c_rev = matmul(t6, matmul(stiffness(), transpose(t6)))
    if mutate == "reversal":
        c_rev[0][0] += F(1, 17)
    k_rev, _, _ = build_macro(reference_triad=s, section=c_rev)
    permutation = zeros(N_EXTERNAL, N_EXTERNAL)
    for new_node, old_node in enumerate((2, 1, 0)):
        for dof in range(6):
            permutation[new_node * 6 + dof][old_node * 6 + dof] = 1
    pulled_back = matmul(transpose(permutation), matmul(k_rev, permutation))
    predicates = {
        "condensed_rank_12": rank(k) == 12,
        "condensed_nullity_6": N_EXTERNAL - rank(k) == 6,
        "full_rank_30": rank(full) == 30,
        "full_nullity_6": N_TOTAL - rank(full) == 6,
        "internal_rank_18": rank(kii) == 18,
        "quotient_ldl_strictly_positive": all(pivot > 0 for pivot in pivots),
        "reversal_covariance_exact": pulled_back == k,
        "rigid_basis_rank_6": rank(transpose(rigid)) == 6,
        "six_rigid_modes_exact": all(not value for row in kr for value in row),
    }
    section_hash = hashlib.sha256(
        canonical_bytes([[str(value) for value in row] for row in stiffness()])
    ).hexdigest().upper()
    condensed_hash = hashlib.sha256(
        canonical_bytes([[str(value) for value in row] for row in k])
    ).hexdigest().upper()
    return {
        "candidate_id": CANDIDATE_ID,
        "counts": {
            "cells": 2,
            "external_dofs": N_EXTERNAL,
            "internal_dofs": N_INTERNAL,
            "internal_moment_dofs": 12,
            "internal_rotation_dofs": 6,
        },
        "formulation_id": FORMULATION_ID,
        "hashes": {"condensed_operator_sha256": condensed_hash, "section_sha256": section_hash},
        "integration": {
            "complementary_moment_polynomial_degree": 2,
            "force_strain_polynomial_degree": 0,
            "force_term_gauss_points": 1,
            "moment_term_gauss_points": 2,
        },
        "ldl": {
            "pivot_count": len(pivots),
            "pivot_signs": ["POSITIVE" if pivot > 0 else "NONPOSITIVE" for pivot in pivots],
        },
        "mutation": mutate,
        "predicates": predicates,
        "schema": SCHEMA,
        "terminal": (
            "NONCLASSIFYING_EXACT_LOCAL_GATE_PASS"
            if all(predicates.values()) and mutate is None
            else "NONCLASSIFYING_EXACT_LOCAL_GATE_FINDING"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--mutate", choices=("condensed_entry", "section", "reversal"))
    args = parser.parse_args()
    payload = canonical_bytes(build_certificate(mutate=args.mutate))
    if args.output is None:
        print(payload.decode("utf-8"), end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# F03 sparse positivity-factor producer: bounded contract

This connects the existing exact sparse congruence proof to an actual sparse
factor producer. It does not select a scientific numerical method or run a
physical equilibrium. The proof remains a sufficient positive-quadratic-form
test of the full represented primal K, including admitted stored skew.

`scripts/_b3_e4_f03_sparse_factor_candidate.py` performs one SuperLU general
LU factorization with `MMD_AT_PLUS_A`, diagonal pivot threshold zero,
`SymmetricMode=True`, equilibration disabled and no iterative refinement.
It neither solves a right-hand side nor uses another ordering or pivot
policy after failure. Backend/programming/memory exceptions propagate.
The selected producer settings are an experimental algorithm, not an SPD
declaration or accepted scientific execution configuration.

SuperLU reports `Pr K Pc = L U`, where the row/column arrays map old indices
to new indices. Require the two maps to agree. The congruence proof receives
their inverse gather `order=argsort(perm_c)`, so it compares
`K[order][:,order]` with `L diag(diag(U)) L.T`. A non-involutive three-cycle
test separately verifies this convention. The convention follows the
official [SciPy 1.17 SuperLU documentation](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.sparse.linalg.SuperLU.html).

Require a structurally valid unit-lower L, upper U and finite strictly
positive diagonal candidate. Differing permutations or nonpositive diagonal
produce HOLD, with no congruence proof attempted and no fallback. Even when
these conditions pass, the producer returns only `CANDIDATE_CREATED` and
`NOT_QUALIFIED`. The existing independent sparse verifier must establish
the complete exact residual bound; it does not assume `U=diag(U) L.T`.
No entry or triangle of K is changed or averaged.

Inputs and factor buffers are owned and validated. The installed SciPy
returns compressed sparse arrays for its factors and can return unordered
compressed columns. The adapter first copies and checks raw finite buffers,
pointer ranges and index bounds, then applies a stable index/value permutation
within each compressed row/column. It performs no value arithmetic and rejects
duplicate entries instead of summing them. An empty bounded matrix shell
receives these buffers; the existing canonical checker runs before conversion.
Cached canonical flags and native conversion of unchecked storage are never
used as validation. Invalid indices and duplicates are tested before traversal.

Canonical CSR entry/data identities use SHA-256 over an explicit schema
tag, dimensions, int64 pointers/indices and binary64 values in little-endian
encoding. The identity retains explicit stored entries, including zeros;
it is deliberately stricter than numerical matrix equivalence. Verification
against another matrix fails before the proof if that identity differs.
The result owns K,L,U, the native maps, inverse gather and diagonal; public
array/matrix access returns copies. The eventual archive must preserve
those values and bind its own expected identities. A digest is not proof
of mechanical admissibility.

Budgets cover bounded input shape/storage, minimum possible factor inventory
before native work, and observed factor nnz/storage afterward. Extract each
native L/U once. The shared validator has its own per-matrix nnz/workspace
cap; the factor budget additionally caps their combined retained storage.
Opaque native factor workspace and failed-attempt diagnostics still require
an external supervisor/journal before any scientific use. A post-factor cap
cannot prevent a native peak allocation. Exact congruence work uses the
separate already-reviewed path/pattern/rational/Python-storage budgets.

Synthetic tests exercise real SuperLU factors, exact non-involutive
permutations, retained skew, ownership, matrix identity, indefinite/singular
inputs, malformed native outputs and early/observed resource checks. A
129-unknown diagonal test and a coupled 98-unknown two-dimensional SPD graph
have no dense global fallback and are not a
performance or physical-scale qualification. This does not change any
previously consumed proof archive or physical HOLD.

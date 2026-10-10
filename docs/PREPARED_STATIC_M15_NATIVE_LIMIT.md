# M15: native solve relation sufficiency limit

Outcome: **NO_GO for using the existing componentwise native residual relation
alone to certify response accuracy/governing identities; INCONCLUSIVE for a
tighter relation describing the actual installed native solve.** This is a
diagnostic result, not an observed SuperLU accuracy defect or a performance result.
Stop this bound-refinement line under its present assumptions. Preserve the
response candidate and canonical fallback.

## Exact counterexample and independent governor control

For U = [[1, 2^20], [0, 1]], b = [0, 1], the exact solution is
[-2^20, 1]. The physical output [1, 2^20] x is zero. A represented binary64
candidate [-2^20 + 2^-31, 1] has exactly represented output/error
2^-31 = 4.656612873077393e-10. It exceeds the unchanged illustrative output
criterion 1e-12 + 1e-12 |0|, while satisfying the frozen M12 residual relation:

    |U xhat - b| <= gamma_6 (|U| |xhat| + |b|) + a
    a_i = 6 mu (1 + |U_ii|) / (1 - 6 u)
    u = 2^-53, mu = 2^-1074

Its first-row allowance is 1.3969838619232186e-9. Exact rational admission is
checked on the candidate itself; no future native intermediate or direct result
seeds the calculation. The negative-load case is symmetric.

Root separately rederived the relation using Fraction arithmetic. A second
physical case b = [2^-32, 1] has true output 2^-32 and admits its exact solution.
The true governor is this second case; the allowed first candidate instead
governs. All RHS, candidate coordinates and output products are represented, with
no tolerance ties, clipping or interval overestimation needed for the reversal.
This proves insufficiency of this information model, not that the native solver
returns the adversarial candidate. Scalar substitution on these constants gives
the exact solution and is explicitly a separate control, not native equivalence.

The example is not a lower bound on the historical free-free fixture, nor a proof
that all stronger native contracts are impossible. M14 already removed proved
exact staged operations in that fixture; native backward uncertainty remained.

## Native authority audit and remaining prerequisite

The version-matched SciPy wrapper invokes resident gstrs and exports CSC L/U and
permutations. Its public exports do not expose resident supernode partitions.
[SciPy wrapper source](https://raw.githubusercontent.com/scipy/scipy/v1.16.3/scipy/sparse/linalg/_dsolve/_superluobject.c)

The version-matched gstrs source chooses scalar division/updates for singleton
supernodes and vendor TRSM/GEMM for larger supernodes. Exported CSC values alone
therefore do not establish executed floating operation/reduction order.
[SuperLU solve source](https://raw.githubusercontent.com/scipy/scipy/v1.16.3/scipy/sparse/linalg/_dsolve/SuperLU/SRC/dgstrs.c)

Prior M12/M14 runtime evidence records SciPy 1.16.3, development OpenBLAS 0.3.29,
SkylakeX runtime dispatch and one thread, binary hashes and matching local RECORD
entries. These identify local artifacts; they do not qualify each native
operation. M15 inspected the public OpenBLAS wheel provider, whose builds vendor
a library and source submodule; it did not establish a pinned source/compiler/
kernel mapping to this installed DLL. Current provider main is not such a mapping.
[Wheel provider](https://github.com/MacPython/openblas-libs/tree/main)

Several version/build source fetches failed; these are retrieval limitations,
not evidence that provenance is inherently unavailable. The `.dev` version label
alone neither identifies a release tag nor proves qualification impossible.
Even exact source identity would still require a justified arithmetic contract
for executed kernels/partition, or a conservative useful partition-independent
proof. No such stronger relation was established in this slice. Do not infer
private layouts, empirically shrink gamma or relabel scalar arithmetic as native
execution. PARDISO/default auto routes are outside this SuperLU control.

## Actual verification and resource accounting

**7 distinct tests passed: 3 owner and 4 independent root; zero failures, skips
or timeouts.** Owner checks signed examples, exact/refusal/underflow controls and
reference/native distinction. Root checks independent exact admission, governor
reversal, represented admission/refusal controls and binary64 underflow terms.
No backend solve was needed for this sufficiency proof.

All checks used C:/Github/ANYsolver/.venv/Scripts/python.exe, the task runner
--kind check --benchmark-epoch m8 --jit 0, isolated solver source/tests, one
configured OMP/BLAS/Numba thread and disabled pytest plugin autoload. Numerical
jobs were serial. Commands, source identities, counts and full logs are retained
in ../evidence/checks/ below.

| Run | Process-wall seconds | Exit | Result |
| --- | ---: | ---: | --- |
| m15-solver-01 | 0.5895185000008496 | 0 | Two signed examples and controls |
| m15-solver-02 | 1.613979400000062 | 0 | 3 focused tests |
| m15-root-01 | 1.445966700000099 | 0 | 4 independent tests |

Owner used 2.2034979000009116 / 120 correctness seconds; root used
1.445966700000099 / 120, no reserve pooling. Combined 3.6494646000010106 seconds.
M8 benchmark ledger remains 540.0326433999871 / 600. No benchmark, activation,
backend change, native build, Git delivery or 10,000-case qualification occurred.
Different-model-family independent review remains unmet; Mistral cached
unavailability persists. Root assessment is independent of author, same family.

New files: tests/prepared_static_response_m15_relation_limit.py,
tests/prepared_static_response_m15_tests.py,
tests/test_prepared_static_response_m15_independent.py, this report and
.prepared-static-evidence/m15* evidence/handoff. Existing product hashes remain:

    prepared_static.py
    9BFD155164823156674CA6B4B1E332E798D390EF615172476253A81298287D70
    prepared_static_response.py
    C4DF1E40C70238C96BFA5F5F0FBB61C20687E8EB79CE35EB9F953167D59C5152

## Decision

Do not start another refinement or benchmark under the same relation. A next
useful implementation must first supply a concrete independently reviewed native
arithmetic contract, or adopt a separately considered execution architecture with
an explicit canonical-governor compatibility decision. Universal replay remains
the safe existing behavior for unresolved stress/envelope contenders. This note
does not authorize a new backend, relaxed identities/tolerances or extra campaign.

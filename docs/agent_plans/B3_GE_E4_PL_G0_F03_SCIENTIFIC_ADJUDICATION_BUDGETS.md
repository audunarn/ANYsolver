# F03 scientific adjudication budgets

23 September 2026. **Implemented infrastructure; no scientific execution or
qualification is implied.** This note records the canonical solve-free replay
budget bundle added after the reviewed local-scientific protocol. The bundle
is serialized into every future case archive plan and must be independently
reviewed before registration.

## Purpose

The manufactured component tests used sparse order 64 and recovery/support
limits sized for at most 1,024 free coordinates. Those limits cannot be reused
for the five scientific cases: `Q1_L2` has 1,470 physical coordinates, its
topology-known recovery estimate is 2,217,853,440 operations, and its support
symbolic-storage estimate is 555,163,648 bits.

`_b3_e4_f03_local_scientific_budgets.py` now owns one immutable nested factory
covering positivity, state/scaling binding, root rank, exact trace binding,
equilibrium/energy, alternate integration, and complete saved-recovery
composition. A deterministic recursive scalar contract is appended to the
existing producer/resource contract in `plan.zip`. A replay must require exact
factory equality; a caller-supplied larger or smaller budget is not canonical.

## Derived inventory limits

The topology-known common maxima are:

| Quantity | Bound |
|---|---:|
| Physical coordinates | 1,470 |
| Station intervals | 47 |
| Complete virtual tests | 426 |
| Interface comparisons | 192 |
| Work comparisons | 2,606 |
| Complete composition comparisons | 2,802 |
| Trace input nnz upper bound | 129,360 |

The trace nnz bound is the complete dense-row envelope for 27 three-row
station operators, three root rows, three tip rows, and one free-slope row:
`88 * 1470`. It does not assume observed sparsity.

Recovery permits 2.5 billion estimated operations, one billion aggregate
integer bits, and 256 MiB of its declared Python-side work estimate. Support
permits 16 million estimated operations, 600 million symbolic bits, and
256 MiB. These caps exceed every topology-known case envelope without changing
any physical tolerance or mathematical operator.

The exact sparse replay retains the protocol's 16,384-bit individual fraction
cap, 100 million cumulative-bit cap, 50 million positivity product paths,
300,000 positivity residual entries, and 4 GiB positivity workspace estimate.
The state binder admits at most twice the frozen KKT nnz cap. Integration admits
the same two-pattern union. The equilibrium six-block cap is 660,000 nnz; with
the largest registered order, its own conservative formula remains below the
protocol's 4 GiB exact-Python workspace cap. Actual saved block counts must
pass this cap before replay.

The complete composition work envelope is 10,066,395,136 bytes. This is an
arithmetic sum of nested component maxima used by the preflight and includes
conservative double counting. It is not an allocation request or an RSS
allowance. The independent process-tree supervisor retains the stricter 6 GiB
sampled RSS limit for any future case execution.

## Verification boundary

The topology-only preflight reconstructs each registered grid and checks
recovery operations/workspace, support operations/symbolic storage/workspace,
virtual-test and comparison inventories, and the dense trace-input/workspace
envelope. It performs no numerical assembly, factorization, solve, recovery,
or adjudication.

Sparse-block counts, saved-array sizes, exact-arithmetic observations, and
factor fill remain runtime evidence. Exceeding a bound fails the registered
case; no automatic larger budget, retry, or replacement case is implied.

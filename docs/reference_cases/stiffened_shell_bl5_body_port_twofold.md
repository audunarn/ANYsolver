# Two-part physical body solution candidate — manufactured controls only

`scripts/r8_bl5_body_port_twofold.py` is a separate source candidate, not a
replacement for the original body-port probe or a solver policy. No native or
continuum specimen right-hand side has been evaluated. The original body V1/V2
failures, common-action correspondence limitations and frozen execution bounds
remain unchanged.

The candidate solves the unchanged sparse equations
`K q + G.T eta = load`, `G q = 0`, with original fixed coordinates zero and
`G = R_rigid.T` when the six-mode gauge is supplied. A reversible diagonal
congruence supplies a sparse indefinite LU. One factorization is reused for an
initial solve and at most three original-equation residual corrections. No
global inverse, SVD, condensation, load projection, symmetry averaging, penalty,
stiffness floor or additional physical support is introduced. The final source
also rejects zero as well as nonfinite congruence factors: that narrow extreme-
range refusal received syntax-only verification after the manufactured runs.

Both physical coordinates and gauge multipliers retain binary64 high and low
parts. TwoSum stages compensate addition without a cancellation magnitude
assumption; FMA retains the scaled correction product remainder. These remain
finite-precision updates and cannot promise convergence. Original CSR entries
contract each high and low part through exact dyadic `Fraction` accumulation.
Original active-row relative ratios and squared global weighted norms are checked
before any binary64 conversion. Decimal formatting does not decide acceptance.
Conversion of correction RHS values to binary64 can still lose an unrepresentable
correction; a stalled or failing physical gate is reported, never accepted.

The physical gate is deliberately **`K q - load`**, excluding gauge reactions.
It retains `max(global weighted residual/load norm, max_active(abs(r_i/load_i)))`
with no active-row floor, threshold `1e-8`. A small legitimate gauge covector can
make joint KKT equilibrium pass while physical equilibrium fails. Gauge
covectors separately remain bounded by `1e-8` and pose by `1e-9`. Original work
checks retain relative `1e-8` and denominator `max(abs(load.T q), 1e-12 J)`.
Reports preserve both parts, original loads/scales/gauge, physical and joint
residuals, supports, paired work, internal pairing and actual correction counts.
Nonfinite corrections, singular factorization, stagnation and exhausted
corrections have explicit failed statuses. Unexpected solve exceptions propagate.

Physical work, support/gauge covectors and sparse trace contractions must use
the represented sum. The candidate has no implicit NumPy conversion that silently
returns only the high part. Existing `beam_material(owner,q)` and pose/point-gap
consumers accept a single binary64 vector; they have **not** been adapted or
validated for this carrier. A future body workflow must explicitly preserve both
parts in stationarity, actual virgin section energy, sided work and common-origin
wrenches. A mixed saddle subblock is not material stored energy; the manufactured
energy test uses its independently declared complementary potential instead.

Ten final manufactured unit instances passed by impact selections: nine in
`micro-v2` and the remaining fixed-support assertion in `micro-v3`. Controls prove
quiet physical rows in a coupled physical/retained indefinite system at loads
`1e-20` and `1e-200`, where the high-only CSR residual misses the quiet row. Six
manufactured rigid modes, support covectors, owned arrays, invalid inputs,
singularity, nonfinite/stagnating correction and programming-error propagation
are covered. A permitted small rigid-load imbalance has a passing joint KKT ratio
but fails the original physical gate. A min-subnormal control whose nonzero
residual converts to binary64 zero still fails its exact active-row gate. A
three-scale six-coordinate control also fails explicitly: two parts do not
guarantee resolution of every cancellation problem.

`micro-v1` preserved three assertion failures/four passes. Exact analytic work
and support assertions exceeded the unchanged scientific tolerance, and an
assumed extreme-load failure was contradicted by a passing manufactured solution.
`micro-v2` preserved one assertion failure/nine passes: Decimal unary negation
rounded an independently represented support value at default precision; exact
sign reversal repaired the test. The early review concerned an 80-digit source
version; the actually executed first version used 4096 digits. The final candidate
uses exact dyadic contractions, avoiding reliance on either precision bound.

Raw evidence is in
`.qualification/b3-ge-e4-pl/r8-bl5-body-port-twofold-dev-20261006-v1/`.
Checks used exact CI dependencies, affinity `[0]`, pools1, JIT off, unforced
backend, 600s/2GiB bounds. These are development controls, not correspondence,
physical accuracy, resource qualification or release acceptance. Independent
review and separate explicit execution authority are required before any saved
body-case evaluation. The next discriminating check is the unchanged failed
shell K/load/support case with both solution parts preserved; a pass would only
resolve that algebraic representation gate, not identify the sole physical cause.

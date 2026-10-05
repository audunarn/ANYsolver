# Interval primitive source review v1

Outcome: no blocking false-positive defect found in certify_shifted_lower for its explicitly stated target under validated IEEE gradual-underflow arithmetic. This is supporting source/evidence review only: no tests or numerical jobs run by reviewer, no source edits, no scientific acceptance. The primitive does not yet certify a saved BL5 mechanical operator.

Reviewed source SHA b951282d0a645e89876d5e4ec4a315addf815617f746a18bfd46ac38be6a6dfc; test SHA a72cde8f81f1c86a44e9bbc4af9ffa199051ade7b126f372c2fe0a21dc16a81f.

## Correctness findings

scripts/r8_bl5_sparse_kernel_interval_dev.py:97–137 validates/owns canonical finite CSR/CSC through the existing strict buffer validator, rejects incomplete permutations/non-lower patterns, and explicitly targets the exact stored LOWER completion AFTER the symmetric permutation, minus shift I. This is not SPD of the original nonsymmetric matrix: upper-triangle and mechanical-target error remain caller obligations.

The arithmetic at76–87 encloses every product endpoint and divides over a strictly positive denominator interval; negative and sign-crossing numerator intervals are handled correctly. Treating a diagonal square as two independent intervals is conservative, potentially widening the bound, without admitting a false positive. Updates at154–160 retain nonzero interval width even when the midpoint is zero. Because lo/hi start equal to exact stored entries and each update is outward, strictly positive pivot lower bounds inductively prove SPD of the declared target. A strictly negative pivot upper bound after certified-positive preceding pivots proves this representative is not SPD; a zero crossing correctly reports HOLD.

Initial-entry lookup and every active elimination clique are checked against the structural pattern at124–129,132,154–156. For a successful positive verdict every step/clique has been visited. Missing fill cannot be silently treated as zero. The structural key ordering, CSC column neighbors, lower clique orientation and SuperLU inverse permutation gather at184 are consistent.

factor_pattern:174–184 now validates caller input before native conversion and converts only trusted backend factor output to owned csr_matrix. LU supplies no positivity verdict. Different row/column permutations are rejected. This resolves the retained sparse-array incompatibility without weakening input-buffer validation.

## Caller/resource obligations

check_arithmetic is called at certificate entry101 and rejects observed FTZ/DAZ through gradual-underflow probes. Exported dot_interval, product_quotient_bounds and sum_up do not call it themselves. The upcoming graph/local-inverse entry must call check_arithmetic BEFORE using these bounds, not only after they have computed epsilonA. Under FTZ a true subnormal product can be erased by much more than one neighboring float, invalidating an unguarded residual enclosure. This is a caller requirement; the certificate loop itself has the guard.

The interval proof preflights pattern/clique/update/workspace counts (114–121), checks time in the pivot loop and reports explicit limits. The workspace figure is an array estimate, not total RSS. factor_pattern has no internal factor-fill/time/RSS limit before opaque SuperLU work; external supervision is necessary, and certification rejection afterward cannot retroactively bound its cost. dot_interval constrains its inner dimension to24 but not its output dimensions; the graph caller must bound/chunk output columns and local workspace explicitly. No larger sparse order or budget is authorized by the defaults.

The main unresolved mathematical work remains outside this primitive: exact-kernel graph reconstruction/rank, absolute stationary/triangle/assembly error, generalized G=Z*.T Z* conversion, and shifted margin versus that error. Primitive positivity alone must not be relabelled actual mechanical-kernel positivity or inertia. Interval widening/fill/resource refusal is unresolved, not formulation failure.

## Retained test evidence

Inspected interval-test-v1/stdout.log and execution.json:13 passed/one failed, exit1,0.9843 s supervised. Failure was the factor-pattern test passing SciPy csr_array into strict canonical validation. Inspected interval-test-v2:the affected old case plus the new pre-backend corrupt-buffer control passed (two passed/13 deselected), exit0,0.8654 s. The two retained runs cover15 distinct passed controls after the targeted fix; the original failure remains preserved.

Meaningful controls include Fraction-exact Schur pivots under two permutations/two shifts, an indefinite positive-diagonal matrix, an exact SPD matrix made inconclusive by interval width, missing initial/generated clique, sign-crossing subnormal products, cancellation dots, shift/budget rejection, invalid buffers/permutation and input ownership. They support the primitive logic; they do not establish large-case interval practicality, mechanical correctness or resource performance. The forthcoming caller should also demonstrate its arithmetic gate executes before local residual bounds and include any final arithmetic/helper delta in its own changed-input checks.
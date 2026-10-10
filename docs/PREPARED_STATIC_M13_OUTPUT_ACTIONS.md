# M13 — output-aware uncertainty, with canonical staged rounding

2026-10-09. Implemented and independently reviewed the next bounded diagnostic
slice. **Supported sampled von Mises bounds are conditionally useful; free-free
contenders remain unresolved. Production activation remains INCONCLUSIVE.**
No numerical tolerances, canonical arithmetic, backend defaults or product code
changed. No benchmark or speedup claim is made.

## Implemented mechanics

M12's independent displacement intervals discarded correlations important to
stress recovery. M13 carries an exact signed row from the resident factor through
each reviewed affine recovery stage, together with independent rounding-error
symbols for the canonical operations. Shared symbols retain their signed
coefficients through subsequent operations and cancel only where the same physical
error appears with cancelling coefficients. Distinct errors are not cancelled.

The graph is an uncertainty tool. It does **not** replace canonical staged stress
evaluation with a flattened matrix product. Actual canonical solve/recovery are
oracles evaluated only after all coordinate/component/derived intervals exist.
No observed direct solution, residual or stress enters interval construction.

For native reordered solve coordinates, let w be an exact linear output row.
Stream transpose actions a=U^-T w and c=L^-T a. With M12's safe triangular
magnitude bounds, external RHS rounding eb and declared native residual radii
RL/RU, the native uncertainty radius is

    |c| dot eb + |c| dot RL + |a| dot RU.

This follows directly from the forward/backward residual equations and applies
absolute values **after** the signed output actions. No global inverse is formed
or stored. The residual bounds include unknown intermediate magnitudes using
M12's enclosures, not observed native intermediate results.

Final scaling, physical/local transforms, S3 enrichment, station kinematics,
material/resultant products and scalar beam/bending recovery contribute separately
tagged rounding symbols. Each allowance uses a safe magnitude enclosure of the
canonical stage. The scalar operation order matches the inspected formulations;
fixed represented material/geometry coefficients remain unchanged. Nonlinear
prepared canonical von Mises intervals are evaluated after physical component
intervals using the existing squared-difference formula.

Root reviewed the signed action and residual derivations. Independent exact
closed-form lower/upper controls show cancellation of correlated forward/backward
factor errors. Separate tests check shared versus independent stage noise,
nontrivial native row/column permutations and external scaling, and refusal after
selected helper mutation. These support the conditional diagnostic, not complete
native or production qualification.

## Results and governing decisions

All **114 sampled linear/beam values and 14 prepared canonical von Mises values**
are contained under the retained arithmetic assumptions. Fixtures and coefficients
are unchanged from M12; no fixture/gamma sweep was performed.

| Quantity | M12 | M13 |
| --- | --- | --- |
| Supported VM maximum width / diagnostic tolerance, case 0 | 2.3295080995922417 | 0.5797735072345366 |
| Supported VM maximum width / diagnostic tolerance, case 1 | 2.3304145202095934 | 0.5802780880962873 |
| Free beam shear width, case 0 | 0.0008564721735612767 | 2.7015925810968573e-5 |
| Free beam shear width, case 1 | 0.0054308886442133615 | 0.00017128332206196284 |

Supported: all 7 VM pairs and 35 of 56 linear-component pairs strictly separate
for minima/maxima. Exact self ties remain unresolved. Near-zero/cancellation-sensitive
linear components still have broad bounds: maximum width/tolerance ratios about
3752 and 3931. Supported VM usefulness does not confer complete requested-output
or whole-model acceptance.

Free-free: shear intervals are approximately **31.7 times narrower**, but neither
pair separates. That is a bound improvement, not a runtime improvement. The
largest radius contribution remains native backward-solve uncertainty:
1.3492687704048837e-5 / 8.554472635008595e-5. Physical-transform contributions are
1.0482572371230602e-8 / 6.65225533957962e-8, local-transform contributions
2.6206430928076575e-9 / 1.6630638348949092e-8. Full per-field attribution is retained
in the diagnostic JSON.

Even deleting native forward/backward and RHS-scaling contributions from the
**current allowance model** leaves free recovery/final-scaling interval widths
approximately 2.64e-8 / 1.68e-7, still above the diagnostic tolerance. This is a
limitation of those conservative allowances, not an observed arithmetic error or
a mathematical lower bound for every possible certificate. Native solve
qualification alone would therefore not complete this route.

The supported cancellation-sensitive shear bounds are mainly driven by enriched
coordinate and station-kinematic roundoff. Their decomposition provides a specific
next investigation, rather than another undirected bound refinement.

## Scope and unresolved prerequisites

All M12 native conditions remain explicit and **UNQUALIFIED**: the gamma_(2n+2)
supernodal/vendor triangular residual relation, diagonal-scaled underflow/reciprocal
behavior, factor-export equivalence and execution authority. M10 recovery dot,
scalar and square-root arithmetic assumptions remain conditional. No smaller gamma
was chosen to make a case pass.

Selected diagnostic helper binding/code identities are checked around callbacks
and enclosure. This is not complete executable admission of Graph/OutputActions,
all dependencies or a production operation lease. Cancellation produces no graph;
foreign helper replacement is refused before that helper executes. Unsupported
backend/type admissions remain inherited from M12. Invalid dot counts, nonfinite
weights, overflow and large-diagonal subnormal cases have focused controls.

No source/full-load assembly error bound, principal/eigensolver, complete reaction,
nonzero-offset, arbitrary history or full-model envelope certificate is supplied.
Different-family independent qualification remains unmet because Mistral is cached
unavailable. Root's independent mathematical/oracle checks are not relabeled as
different-family acceptance. Canonical fallback remains unchanged.

## Actual verification and resources

All checks used `C:/Github/ANYsolver/.venv/Scripts/python.exe`, the existing task
runner with `--kind check --benchmark-epoch m8 --jit 0`, isolated solver source/test
imports, one OMP/BLAS/Numba thread and disabled pytest plugin autoload. Numerical
jobs were serial. Effective runtime identities from M12 remain applicable; these
runs do not establish new native arithmetic qualification.

**9 distinct tests were ultimately verified:** author 4 and root 5. Root's first
run had 4 passing tests and one assertion failure: the test indexed a zero
contribution that the graph legitimately omitted after exact cancellation. Root
corrected its assertion to treat an absent contribution as zero, then reran that
one affected test successfully. No product formula or tolerance changed, and the
failed run is preserved. The other four passed tests were not redundantly rerun.

| Run under `../evidence/checks/` | Process-wall seconds | Result |
| --- | ---: | --- |
| m13-solver-01 | 6.599409799999648 | Four fixture diagnostics, 114 linear/beam + 14 VM containment |
| m13-solver-02 | 1.5454759999997805 | 4 author tests passed on final source |
| m13-root-independent | 2.477495099999942 | 4 passed, 1 root assertion failure |
| m13-root-diagnostic | 6.073875300000054 | Final diagnostic reproduced byte-identically |
| m13-root-independent-repair | 1.5941870999999992 | Corrected affected test passed |

Owner total **8.144885799999429/120** seconds. Root total
**10.145557499999995/120** seconds. No timeout or skip; no benchmark charged or
reserve pooling. M8 ledger remains **540.0326433999871/600** seconds. Exact commands,
effective settings, identities, counts and full logs are in each run directory.
Author/final-root diagnostic SHA256:
`6016442852C5C2CEF283B0D706D4E04305E83B6E6F5F0C9C75DEBF6624352D07`.

New source: `prepared_static_response_m13_output_actions.py`, diagnostic and author
tests, `test_prepared_static_response_m13_independent.py`; evidence/proof/source
hashes in `.prepared-static-evidence/m13-solver-handoff.md`. Product hashes remain
9BFD155164823156674CA6B4B1E332E798D390EF615172476253A81298287D70
(`prepared_static.py`) and
C4DF1E40C70238C96BFA5F5F0FBB61C20687E8EB79CE35EB9F953167D59C5152
(`prepared_static_response.py`). All previous source and failed evidence are
preserved. No main/Git delivery or 10,000-case qualification was performed.

## Decision

Retain M13 as the conditional output-aware proof prototype. Do not activate
production exclusions or start a performance campaign on this evidence.
The next useful discriminator is a targeted audit of the **actual backward-solve
and canonical recovery primitives**, including exact selector/sign/dyadic operations
where the generic dot allowance is overly broad. It must preserve the existing
arithmetic and prove tighter allowances, not reduce them empirically. Both native
and staged errors need attention; further coordinate-only tightening is not the
principal remaining uncertainty. No additional execution authority is supplied by
this note.

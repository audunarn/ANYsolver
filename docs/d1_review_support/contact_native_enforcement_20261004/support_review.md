# Native enforcement globalization source review

2026-10-04. Supporting same-family Read scrutiny only. Inspected `native_shell_static_driver.py`, `native_multi_s3_static.py`, `decision.md` and compact fields from `source01/stronger_penalty.json`. No numerical run, production edit, qualification or acceptance claim.

## Finding and smallest discriminator

No concrete scatter, spatial-linearization or accepted-state mutation defect was found in the scoped source. Assembly retains the full free system, corrects each local native 42-coordinate contact principal once, and preserves shell/native mixed blocks. Trial histories use the preceding accepted origins; only complete `_record`/checkpoint staging swaps the physical accepted state. Source01 failed with zero completed targets and retained the initial physical state/capsule.

The observed failure is more specific than a generic gap obstruction. At the last trial, merit is 0.00276042288 and minimum gap -4.91945891e-5 m. The two final candidates satisfy the 5e-5 m gap limit and slightly improve the displayed minimum gap (-4.90451825e-5/-4.91198662e-5), yet merit rises to 0.607899055/0.0382719369. Seven preceding candidates failed the gap gate; geometry/sweep did not reject. Aggregate minimum gap alone cannot explain the residual growth; per-pair active intervals, reactions and all three residual blocks are needed.

The driver tests a finite dyadic sequence and requires strict reduction of `max(metrics)`. With nine tested cuts, the smallest factor is the angular fraction divided by 256. This is a bounded globalization policy, not a proof that no smaller feasible descent step exists. For a smooth consistent free-system Newton map, sufficiently small steps must locally reduce the free residual norms; strong contact curvature/activation can make that region smaller than the finite sequence. A wrong tangent can produce the same finite-cut symptom, so increasing limits or changing the merit immediately would not discriminate those explanations.

Smallest useful check at the **actual failing state**, with its accepted-origin histories frozen and no commit:

1. Preserve pose, shell displacement, parameter, accepted origins, raw step/angular fraction, pair gaps and active intervals. Check `K_ff*step_f+r_f` using the exact constrained free indices. This distinguishes solve/scatter inconsistency before another nonlinear trial.
2. Compare one-sided `(r_f(advance(alpha*step))-r_f)/alpha` with `K_ff*step_f` at a few bounded smaller alpha values, reporting native equilibrium, compatibility and shell blocks separately, plus each pair's gap/active intervals. Use the same advance chart and physical skin map as the solver. This distinguishes faulty linearization from curvature/branch onset and determines whether the admissible descent region exists below the consumed cut sequence. Diagnostic poses never commit histories or overwrite source01.

The earlier smooth tangent result at the 10000 setting does not establish this failing-state linear response at 1.2e6. Conversely, source01 does not establish formulation failure or that the derived penalty's final equilibrium is infeasible.

## Requirements if adaptive force continuation is introduced

The current `_record` is keyed by requested target ordinal and infers load parameter from `program.targets[target-1]`; checkpoint counts records as completed requested targets. It cannot safely represent additional physical substeps without an explicit contract change. Rebuilding a different target program to resume an old capsule also changes its identity.

A bounded adaptive path must distinguish requested targets from accepted physical substeps, store each accepted substep's actual load parameter and requested-target progress, bind adaptive controls/budgets in identity, and replay each substep with the previous **accepted** histories. Failed/cancelled trials retain the last accepted physical state and continuation cursor. A completed physical substep needs the same independent equilibrium/all-pair gap recheck, all-pair sweep and atomic history/record/checkpoint staging as a requested target. It must not merely advance the mechanical pose while carrying stale material origins; that would be valid only under a separately explicit elastic contract. Substep limits/minimum load increment/rejection reasons need deterministic bounded stopping. Any new schema/profile/optional policy should preserve existing single-native and fixed-target restart semantics.

These are concrete state/replay constraints, not a recommendation for a preferred globalization fix. The next action depends on the failing-state linear-response discriminator.

## Activation controller / projected sweep source follow-up (2026-10-04)

Source02 solve-error and one-sided response numbers are lead-reported, not reproduced here. Their reported 1/256 activation/merit jump and 1/512 descent support a finite-globalization explanation at that state, rather than the previously hypothesized tangent defect. Source03's later Newton-limit nonpass remains distinct preserved evidence. This review inspected current controller, driver hook, profile/schema changes, projected helper and geometry extraction; no runs were made.

### Projected gap bound

No mathematical counterexample was identified to the proposed projected Lipschitz bound under the stated actual paths. Write the retained point relative to the moving triangle centroid as `a(t,s)+f(s)R(t)lift`, with affine centroid-relative nodal interpolation `a`, `0<=f=4s(1-s)<=1`, and spatial rotation generator omega. The triangle cross-product Bernstein projection lower bound supplies `|n'|<=Ln=cross_speed/area_lower`; therefore `|n(t)-n0|<=min(2,Ln)` over the unit path. Consequently:

- projected affine speed is bounded by max over nodes of `|n0·v|+excursion|v|`;
- rotational projected speed is bounded by `(|n0×omega|+excursion|omega|)|lift|`, uniformly in current cell orientation;
- the `n'·relative_position` term is bounded by `Ln*(max endpoint centroid-relative node radius+|lift|)`.

The implemented separate maximum angular coefficient and lift maxima are conservative for both cells. The uniform station bound also bounds the minimum over stations, even when its minimizer changes. The unchanged physical skin path is affine, and the normal lower-bound/rim bounds/roundoff/interval caps remain present. This is source/algebra scrutiny, not a validated floating-point certificate or measured speed claim.

### Controller findings

One activation-contract caveat was sent to the lead: `_activation_fraction` returns immediately when the sampled endpoint minimum for previously open pairs is nonnegative. That skips the later activation-budget prefix certificate. An open-endpoint/hidden-midpoint path can then penetrate beyond the smaller activation budget while staying inside the physical pair gap budget; the later ordinary sweep admits the larger physical budget. This preserves physical gap safety, but does not establish that every open-pair prefix is limited by `activation_gap_m`. Certify that branch or state the narrower endpoint-activation guarantee. A discriminator should use distinct activation/physical budgets and a hidden intermediate dip between them.

The `maximum_geometry_queries` counter/cap bounds `sample()` calls, counted per pair; geometry-only sweep midpoint queries in activation certification and the ordinary new-profile sweep are not included in `activation_queries`. Sweep interval caps still bound those operations. Report/count semantics must distinguish sampled controller queries from all geometry queries; a total-query claim would require counting/enforcement around those midpoint queries too.

Bisection does not prove a first-event location for nonmonotone gap paths; the code explicitly avoids that claim, and its subsequent prefix certificate fails closed. A recovered geometry endpoint, query exhaustion, unresolved bracket or uncertified prefix cannot commit a physical trial. The driver still independently checks candidate pair gaps, every actual path, merit, full equilibrium and staged record/checkpoint before commit.

### Geometry/state/schema

`_geometry_state` extracts the existing fingerprint, finite/degenerate geometry, retained curves, ordered moving normal, roundoff and complete Bernstein rim checks. `geometry_gap` uses the same three curve gaps, quadratic coefficients, endpoints and interior stationary point as `evaluate`'s minimum-gap calculation. It deliberately omits contact integration/activation ambiguity checks; endpoint contact/commit still evaluates the physical work law. No geometry minimum/rim parity discrepancy was found by source.

The activation owner binds its exact settings and projected-bound revision in identity, has a separate profile/schema/run type, and is selected only by the factory's explicit non-None setting. Base defaults retain their former schema/profile values. Activation limiting changes Newton trial fractions; it introduces no physical load substeps, so existing target-record/history replay remains appropriate. Cancellation and all history staging remain in the shared transaction driver. Diagnostic `activation_queries` is cumulative for that owner object and is not checkpoint/restart state; it should not be interpreted as deterministic physical replay metadata. No independent acceptance claim is made.

## Prefix/query-cap correction source follow-up (2026-10-04)

Current source removes the open-endpoint early return and certifies every previously open pair before returning a fraction. Geometry-only midpoint checks can now use `geometry_query`; the activation owner routes that callback through the same `query()` function as endpoint samples, so those calls consume the same per-invocation cap and cancellation/count checks. Binding `j=j` in the callback preserves pair ownership. A reduced certificate interval budget returns false on unresolved work and then requests a smaller prefix; it cannot turn unresolved geometry into admission. No fail-open defect was identified in these corrections.

Counter scope still needs explicit wording: `activation_queries` is cumulative on an owner object across controller calls, including failed calls, and counts endpoint/prefix geometry queries made by the activation controller. The separate ordinary physical-gap `_swept_admissible` queries are not counted or subject to that same per-controller 64 cap; they retain per-pair swept interval caps. The counter is diagnostic and is not physical checkpoint state, so a fresh resumed owner starts its diagnostic count at zero. A total-solver geometry-query or deterministic restarted-count claim would be unsupported.

The policy revision string remains `explicit_gap_prefix_projected_normal_v1` even though both open-endpoint enforcement and the scope of the controller's query cap changed. If earlier draft activation checkpoints remain reusable, change the revision binding so corrected controller semantics have distinct identity. Otherwise explicitly retire those draft capsules. This concerns reproducible continuation/limit behavior; physical work and accepted history replay equations are unchanged. Existing default profiles remain separate.

At inspection time the hidden-pulse test still expects the full controller call to succeed within 64 queries. The lead reports that case actually exhausts 64 while its larger physical-gap sweep admits the full path. Preserve that resource NONPASS and update the test to require explicit full-attempt rejection, then test a separately supplied shorter certified prefix under a fresh identical cap. Distinguish resetting the per-invocation controller budget for a separate requested prefix from silently giving one unresolved attempt extra authority. Source07's reported stronger coupled success is supporting lead evidence, not a run performed here. No acceptance claim.

## Final corrected-identity/test source closure (2026-10-04)

Verified current source binds the corrected controller with revision `counted_open_endpoint_prefix_projected_normal_v2`. The run field documents cumulative activation-controller endpoint/prefix queries, excluding ordinary sweeps and physical history. Hidden-pulse coverage now explicitly requires full-attempt 64-query exhaustion, asserts the physical-budget sweep admits that full path, and uses a fresh identical-cap owner to certify a separately requested <=1/8 prefix. The smaller-five-query failure is also retained. These resolve the previous identity/counter/full-attempt test concerns. No new production defect was identified by this final source inspection.

Strong-setting assertions keep the 1.2e6 physical line law and 5e-5 m final gap cap, compare an independently reconstructed retained quadratic minimum with production gap, check complete residual metrics, both deforming skin coordinates, force/moment closure and fixed-support resultant against the applied loads, and compare independent scalar potential. Public `tight_gap_analysis` supplies explicit one-beam 1e-7 / two-beam 1e-6 activation budgets with 64 queries; the ordinary `analysis`/`main` defaults retain their previous setting. Source08's two-beam 1e-7 Newton-cap NONPASS is not contradicted by source09's explicitly different 1e-6 algorithmic-budget success; preserve both setting-specific conclusions. Reported source09 execution was not performed by this reviewer.

Two remaining evidence qualifications were sent to the lead:

- The strong tangent test uses **one coordinate direction at three perturbation sizes** (1e-4, 1e-5, 1e-6). That is useful smoothness/error evidence, but is not three independent directions or a complete all-column tangent check.
- The hidden-prefix dense-path diagnostic currently calls production `geometry_gap` at every sample despite its comment calling the diagnostic independent. Use the already available `independent_minimum_gap` on sampled poses for an independent scalar geometry crosscheck, or describe the current check as dense sampling of production geometry. A dense sample alone still does not replace the production conservative path certificate.

Installed-wheel checks were still underway according to the lead. This note makes no installed-runtime, engineering acceptance, qualification or release claim. Supporting same-family source scrutiny only; no numerical runs or production edits.

Lead closure: dense hidden-prefix samples now use independent_minimum_gap direct retained interpolation/extrema; affected installed check1pass3.105s. Production unchanged, other installed28pass evidence unaffected. One coupled direction at three h values is documented accurately. Same-family source scrutiny remains supporting, not independent engineering acceptance.

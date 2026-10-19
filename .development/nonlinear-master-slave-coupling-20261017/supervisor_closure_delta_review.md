# Routine integrated non-author closure — 2026-10-18

Read-only delta review of the repaired candidate. No imports, numerical execution, tests, workers, source/test edits or Git mutations. This is routine closure under the existing plan, not a repeat of the completed user-requested Astra review. Source/test identities below identify the inspected versions.

## Outcome

No additional blocking source finding was established in this bounded closure. The earlier tangent-boundary counterexample, typed trial-recovery boundary and material/snapshot observation gaps are repaired statically. A deterministic force-refusal assertion mismatch found during this review was returned to root and is corrected in the final captured test identity. Numerical success and final acceptance remain root-owned and are not inferred from this review.

## Tangent differentiation

`corotational.py:1561–1657` evaluates the exact frozen-force per-master covector at the valid centre before perturbing. It prefers a central stencil. When one side is refused, its forward `(-3C0+4C(h)-C(2h))/(2h)` and backward `(3C0-4C(-h)+C(-2h))/(2h)` formulas have the correct signs and second-order truncation. If neither complete stencil fits, it halves h for at most32 attempts, checks representability and explicitly refuses an unavailable stencil with the typed exception. Only the specific state-domain exception is suppressed at probes; invalid inputs/unrelated exceptions still propagate. Projection and final Hessian symmetrization are unchanged.

For the Astra counterexample with identical x rotations pi-1.5e-6, the positive h1e-6 probe is refused but the two negative probes remain in the admitted chart. The repaired backward stencil therefore avoids the old deterministic abort while retaining the same mean domain. The relative-angle analogue is likewise handled by selecting the permitted side. No mean-domain widening or tolerance relaxation was found.

Boundary regressions `test_nonlinear_beam_shell_slice3.py:965–981` cover absolute and relative boundaries with nonzero translational and rotational slave imbalance. Their finite/nonzero assertions discriminate the original exception. The symmetry assertion alone is not an independent accuracy oracle because the implementation symmetrizes explicitly. Reduced-stencil exhaustion and a larger-than-two-master anchor-boundary stencil remain unmeasured coverage limits; the formulas themselves are correct by static expansion.

## Trial failure and rollback

`SO3MeanDomainError` is a dedicated ValueError subclass; malformed finite/partition/negative-weight inputs remain ordinary ValueErrors. DC catches only the typed failure while mapping candidate q (`nonlinear_static.py:4237–4245`), evaluates admissible candidates only, refuses an inadmissible fallback endpoint, and classifies no-improvement/domain failure. The existing rollback restores q/lambda and discards the pending state before bounded subdivision; the new classifications are included in its cutback predicate (`:4379–4419`). The positive-span and eight-cutback bounds remain intact. The retained admissible full Newton fallback for a control-dominated state is explicit behavior, not evidence of monotone merit globalization.

Force plain Newton catches a typed candidate-map failure and returns the original q/committed state (`:7259–7266`). The caller discards pending state and performs bounded load cutback. The line-search path catches typed mapping and assembly failure and continues reducing the scale; promotion to a tangent evaluation has the same typed handling and pending-state discard (`:7358–7457`). Unrelated ValueErrors are not caught by these branches. Exhausting exclusively domain-refused trials returns the specific internal cause; mixed failure types keep the ordinary search-failure classification.

The public force cutback-limit result deliberately retains `minimum_load_increment_reached` while preserving the specific Newton reason in `info.first_failed_iteration_reason` (`:8218–8227`). The earlier new test incorrectly expected the direct DC classification for force mode; root corrected the test (`slice3.py:1029–1033`) without changing the public product contract. The synthetic refusal tests exercise both control modes, once/all refusal and unrelated-error propagation. Their force settings select line_search=always: the plain-Newton recovery and promotion-specific rejection branches are statically reviewed but are not directly discriminated by those fixtures. No claim of measured branch coverage is made.

## Material and snapshot observation

`test_nonlinear_beam_shell_slice3_continuation.py:359–378` now requires the fixture's expected physical shell/beam element IDs, mandatory nonempty plastic/alpha and layer/fiber arrays, their expected shapes and finite values. Together with the recursive physical-state comparator this closes the earlier silent-common-omission concern for the fixture's integration-point/fiber histories. The equilibrium helper checks the actual private displacement and state mappings supplied to assembly against their own deep preimages (`:437–453`), closing the extra-copy observation gap.

The cancellation test captures accepted snapshots as they are constructed, stores deep preimages, and compares both snapshots after cancellation (`:794–817`); it also retains exact caller input comparisons and reuses those same inputs. Accepted snapshots on completed paths still receive achieved-lambda residual, physical wrench and actual constraint-summary checks. These assertions express the required contracts; full-target/resume numerical satisfaction is not established here.

## SHA256 at review closure

| File | SHA256 |
|---|---|
| src/anysolver/corotational.py | 85E48F9B171A413BB976C1007E8EFF5457A9A5A2CF33204653611A5A0FB22FD8 |
| src/anysolver/nonlinear_static.py | 278BD36410D877694E9D85776EAC5C9EB9FD152D9DC4DE321E7CED03C2B370AD |
| src/anysolver/nonlinear_performance.py | D22FD0F3C29E2E25AC22F306F2F70ACB64A30D0ADB856B30667B6BACD1F7624A |
| tests/test_nonlinear_beam_shell_slice3.py | 495853D43C74716B8E87E1BF5A4DCD24AB26C041FCB63C4B568DBE5A6A58EF40 |
| tests/test_nonlinear_beam_shell_slice3_continuation.py | A753761A791523FBEE4EEDA2B42FA53CF7E8077516469556012CBA686839B927 |

The test file changed during review as root repaired fixture arguments and the force classification assertion; this table records the final inspected content. Parent reports the earlier focused attempt passed7 with6 new-fixture argument failures; after argument correction5of6 passed and the remaining force-classification assertion was repaired. These are parent-supplied observations, not reviewer-run checks. Final collection/verification was active at handoff; no final acceptance is claimed.

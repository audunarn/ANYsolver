# Retained generalized force research funnel passed

Frozen revision `a2a157bcdee94aee7a6de14c4d42754df208b75a` adds the
remaining-Newton-correction gate to the original retained research prototype.
No production source, material or load equation, tolerance, reference geometry,
existing element or default was changed. This is not a qualification release.

## Separate inventories

| Lane | Tests passed | Scientific records | Child seconds |
| --- | ---: | ---: | ---: |
| Saved-operator and moderate-solution smoke | 4 | 6 | 4.616 |
| Ratio10,000 straight/curved | 2 | 2 | 4.417 |
| Ratio1,000,000 straight/curved | 2 | 2 | 4.617 |
| Curved common-rotation covariance at all three ratios | 3 | 3 | 8.626 |

All tests passed without skips. The moderate full residual/Jacobian matches
the previously accepted native operators. Maximum normalized moderate field
difference is9.511e-12. Maximum covariance difference is2.957e-16. Maximum
accepted equilibrium, compatibility and remaining mixed correction metrics
are5.381e-12,3.546e-12 and9.636e-12, respectively. All satisfy their unchanged
1e-11 gates. Straight cases take two Newton corrections per target; curved
cases take three after the stronger correction stopping check.

The prototype solves the two high-ratio geometries that failed in the nested
native path without adding stiffness, changing source equations or loosening
tolerances. This supports integrating a retained-coordinate controller.
It does not establish a universal root-cause theorem about every condensed
solver, full slender engineering qualification, locking freedom or plastic
performance. Process times are diagnostics, not a benchmark or speed claim.

The earlier c1f51b5 smoke remains three passes and one failed curved-resultant
comparison. Its failure and original outputs are preserved. No higher-ratio
cases were launched under that failed freeze. The stricter successor's source
and disclosure are separate commits; this is not a consumed-run retry.

## Preservation and process boundaries

Successful archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-retained-force-a2a157b-20260908`.
Its4,913-byte manifest hash is
`6ACBA171BF00C5F04360E84CE0DE843AF971881A7426EE4647B7B2E0B2CD9821`.
Initial failed archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-retained-force-initial-c1f51b5-20260908`.
Its1,768-byte manifest hash is
`3F34578B8CDC3040D0523EF442636F14674755516645821F51EC7B292B50D773`.
All archived run copies were compared byte-for-byte with their originals.
Canonical JSON, individual JUnit inventories, numerical gates, resource
receipts and empty process trees were rechecked without new mechanics.
Both high-ratio lanes overlapped; concurrency remained below three.
All children satisfied600seconds/24GiB/one-thread bounds and final guards.
No automatic retries. Deterministic repeat cycles have not yet run.

## Next native integration gate

The current research driver owns no native accepted state and rejects any
plastic update. Implement a private retained-generalized controller and
explicit model-bound accepted-state schema without reusing a different
formulation's material/recovery authority. Retain all generalized coordinates
through Newton; keep origins fixed through trials. Publish mechanical state,
proposed history and load point atomically only after equilibrium,
compatibility, correction and physical recovery validation.

Require cancellation and failed-trial rollback, accepted-origin replay,
load/unload continuation, strict canonical checkpoint/restart, foreign-state
rejection and immutable ownership. Start with exact port comparison to these
research outputs, then generalize connected meshes and material transactions.
Do not label virgin elastic state as nonlinear-section parity or collapse the
paired material/history representation used by prior accepted private work.
Preserve current factor-chain modal operators and their successful repeats.

Full objective straight/curved beam qualification, nonlinear section/fibre
and postbuckling references, objective shell connection, independent review,
environment attestation, package isolation and public opt-in integration
remain required. The research driver is not a replacement production facade.
The full goal remains ACTIVE_INCOMPLETE; production qualification false and
independent review PENDING. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

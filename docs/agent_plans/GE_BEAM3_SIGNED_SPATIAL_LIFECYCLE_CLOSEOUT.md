# Signed spatial continuation and actual N20 cancellation

Disposition: PRIVATE_SIGNED_ELASTIC_SPATIAL_LIFECYCLE_REPLAYED. Goal ACTIVE.
Frozen research source3b856f413d5d5dd7b30dc89f49da6883c0a2570b,
tree5aeb3ab05730c1c053cbda5eaef53c4207da5055. Three added research paths;
no src change. Owner file remains SHA256
9d0bf7a01a0577a1867090a1ac4828eb6df2c45d902bcb1767280f007faa9045.
No mechanics, section laws, operators, recovery, aliases or defaults changed.

## Actual signed segment and cancellation results

The original negative-small elastic equilibrium was mechanically revalidated,
then continued -.003 -> -.0045 -> -.006. The negative .0045 prefix was replayed
in a fresh owner and then resumed twice from its ORIGINAL bytes in two fresh
processes. Both full checkpoint, recovery, seed, result and completion files
are byte-identical. The original negative first record was preserved exactly.

Positive originals were not replaced or rerun as a new qualification. Actual
N20 cancellation at target2 before_commit returned the exact prior positive
one-record prefix. Cancellation at target2 committed returned the exact old
two-record complete capsule. Both actual cancelled results were mechanically
replayed and recovered in fresh owners. A further process resumed the original
cancel-before capsule to completion, reproducing the old full checkpoint bytes.
These were real nonlinear target2 iterations, not zero-step cancellation mocks.

Three paired states (seed,.0045,.006) have zero reported difference under the
prescribed reflection for positions, nodal/cell frames, retained resultants,
load, work and nodal reactions. Endpoint strain/resultants/reference/current
frames agree with zero reported difference at all160 stations (20 elements).
The unchanged normalized acceptance bound is1e-11. This establishes signed
symmetry of this elastic segment, not stability, uniqueness or mesh convergence.

## Preserved audit defects — not mechanical corrections

The first same-author saved-data checker used the wrong internal coordinate
grouping: it treated18 retained resultants as three engineering six-vectors.
Its prefix test failed with difference0.38800723293576916 in those internal
coordinates while the other compared fields were exactly equal.

Source _ge_beam3_retained_generalized.py defines k=z+ell and potential p.k.
Two spatial-reference polar3-vectors form z; four local axial rotation-log
3-vectors form ell. For S=diag(1,1,-1),D=diag(1,-1,1), the correct dual map is
diag(S,S,-D,-D,-D,-D). Physical station six-vector transforms are unchanged.
The original audit/test files and incident are retained. audit_v2.py uses this
source-derived map, not a fitted sign choice or a changed scientific tolerance.

The corrected full audit completed all checks and wrote audit-v2.json, then
exited1 because its final console-hash print referenced the old absent filename.
The script and already-created record remain unchanged. A separate read-only
verify_saved_audit.py recomputed the ENTIRE audit and required exact equality
with the saved record; it exited0 and modified no evidence. Do not report the
v2 creation process as exit0. Neither defect reran or changed scientific data.

## Separate tests and process inventories

Protocol suite22passed in0.21s, fresh TEMP/ge-beam3-signed-lifecycle-unit-20260909.
Initial saved-audit suite2tests: one error, one passed. Corrected suite3passed
in0.062s, including10 mutation subcases and explicit dual-coordinate ordering.
Complete saved-data read-only recomputation passed separately. These inventories
are not combined or represented as an independent authorship review. Test/tool
outcomes were observed; raw unittest/pytest stdout was not separately archived.

Six scientific workers all exit0 with empty Windows Job trees:

| Worker | Seconds |
| --- | ---: |
| Negative prefix smoke and replay | 63.291 |
| Negative resume A and replay | 82.583 |
| Cancel before commit and replay | 76.855 |
| Cancel after commit and replay | 82.884 |
| Negative resume B and replay | 77.190 |
| Resume actual cancelled prefix and replay | 76.587 |

Maximum process-tree peak179396608bytes. The first wave batch used three
concurrent workers; the second used two. Wave elapsed about160.2seconds.
Limits600s/24GiB/one numerical thread, max3workers/1800s wave and existing120s
context/CPU inactivity checks stayed intact. No retries or reused output paths.

## Preserved evidence and remaining programme

71-entry external archive, verified before and after copy:
C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-signed-lifecycle-3b856f4-20260909

Manifest9411bytes SHA256
c73cd2bd9c101395ce639f1ce9d60b76596414d7df02a1cdd4f3444742021dbb.
Verified saved audit2651bytes SHA256
5d9148aefaf9581634a50246a5506b6328bb5a3674085bf353c7dfde477ecdbd.
Negative full capsule324864bytes SHA256
632cbe5d09eb7d90afd68fc2f5b216fab49f8cbd7251727c90eb4cd48e9106e7.
Negative prefix216975bytes SHA256
baabb1ca1b21a7ea8bf2dcf987f7acff968c9277ab7bdb6e1eec574ff7d08c97.
All TEMP originals, helper versions and audit incidents remain preserved.

Next actual gate is FE spatial-branch refinement against the separate continuum
reference, followed by broader solver/material/dynamic parity and independent
review. The N24 original onset capsule already exists and may provide a
hash-bound initial guess; do not rerun completed onset campaigns. This owner
is still elastic-only; plastic continuation and path from rest are not proved.
Installed explicit selection and objective eccentric/curved beam-shell joints
remain unresolved. No public activation, main update, push, merge or release.

NO_GO_PRODUCTION_RESTRICTION_UNCHANGED. Existing B2/B3/S3/Q4, main, user untracked
ANYmesher plan and concurrent ecosystem work remain untouched.

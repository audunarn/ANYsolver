# Private precise scalar-work gate: passed on both signed N24 endpoints

Frozen implementation e9cf90940e0f53e5edb728a064bc4c596f99414c,
tree 551004ebd9f0250810704f944e373a99548d9e69. Nine-path extent: three private
GE-B3 source paths, three research programs, two tests, one gate plan. Existing
B2/B3/S3/Q4 mechanics, public factories, defaults, packages and versions unchanged.
The old private arithmetic remains the default; the new arithmetic is explicit.

## Implementation and tests

GE_BEAM3_RETAINED_GEOMETRIC_WORK_DECIMAL80_V1 evaluates the same scalar geometric
work with 80-digit arithmetic and final binary64 rounding. Proper frames, principal
relative rotations and increment bounds remain enforced. Native analytic residual,
Hessian, kinematics, material/history and recovery are unchanged. Distinct operator
and element fingerprints prevent cross-arithmetic hot restart. No history is
inferred or advanced by scalar evaluation.

Final targeted suite: 52 passed in 8.99 seconds (27 scalar/native-policy tests,
8 enrollment/restart tests, 17 prior directional tests). Covers independent SciPy
SO(3) comparison across the admitted chart, common rigid motions, finite
noncommuting rotations, coupled elastic/plastic material potential and directional
derivatives, exact simple work, mutation rejection, cancellation, deterministic
arithmetic independent of caller Decimal context, unchanged material origin,
unchanged old identities/descriptors, new policy binding, and foreign seed/
checkpoint rejection. This is a targeted suite, not the complete beam parity suite.

## Native signed wave

The immutable original endpoint fields were explicitly enrolled as new elastic
equilibrium seeds. The existing owner checked actual equilibrium and a full
correction before issuing each new genesis. The old complete checkpoint hash is
bound as source authority. Original virgin histories were checked. Original
chains were neither modified nor relabelled, and loading from rest is not claimed.
The new empty-chain checkpoint was restored in its owner and checked byte-for-byte;
four separate processes independently regenerated the respective genesis states.

Positive smoke passed before the negative endpoint and two fresh replicas launched
concurrently. Each run covered all 24 elements, 426 original free coordinates,
870 retained coordinates and exactly five native evaluation points. The numerical
displacement controller was not included as a physical support. Both stored
negative directions retained negative scalar potential and residual directional
work. Native directional work: -0.001022921338718573. Exact saved-factor work:
-0.0010229213387185085. Maximum stationary-lift error: 2.0973842714732033e-16.

Identical metrics for both signs:

| Step | Potential error | Residual-work error | Full residual derivative error |
| --- | --- | --- | --- |
| 1e-4 | 2.7414713966826543e-10 | 5.464402027654386e-10 | 9.979937863439307e-10 |
| 5e-5 | 7.899074862087463e-11 | 1.217179232838178e-10 | 9.444499590499492e-10 |

All satisfy the original 1e-7 directional gate; lift/work satisfy original 1e-11.
No step or threshold was changed. Both same-sign replicas are byte-identical.
Material history was not advanced. Accepted new state, checkpoint and recovery
were unchanged after all native trials. Original failed arithmetic evidence remains
FAILED; this is a separate explicit successor result.

| Worker | Seconds | Exit | Peak bytes |
| --- | --- | --- | --- |
| plus-a | 84.3908722 | 0 | 540422144 |
| minus-a | 87.6376232 | 0 | 540016640 |
| plus-b | 89.2348812 | 0 | 541175808 |
| minus-b | 88.0398457 | 0 | 540037120 |

All Windows Job trees empty at completion. No timeout, memory breach, cleanup
failure, retry or resource-request reuse. Wall time approximately 174 seconds.
One numerical thread per worker, max three concurrent after smoke. The existing
600-second/24GiB per-child, 120-second owner and 1800-second wave bounds were kept.

## Saved evidence

A separate standard-library saved-data audit recomputed scalar sums, directional
work and full residual derivative errors from every raw trial vector; it checked
hash bindings, owner capsule hashes, replicas and all four terminal receipts.
This is an arithmetic/custody audit, not independent author review of mechanics.

External ANYrelease archive: ge-beam3-precise-native-e9cf909-20260909.
71 files; canonical manifest 9967 bytes, SHA-256
5be3566fbf5f420f73eef5856a56447c21d44ea8cd23303e714505f7ab9c063c.
Includes frozen source snapshots, all commands/logs/process receipts, raw vectors,
new seeds/checkpoints, canonical outputs, helper scripts and saved audit.

- complete.json: 2279 bytes,
  b758b828edd5d3dc50aa0d9a8ed65040bfce52df92b5666cb9c7a94610f1e0a6.
- saved-audit.json: 1160 bytes,
  5455eaf614a8b17af0dbf9e11e5d83d7d5bbbd92c64ad5b1ea60851ad6033c4d.
- plus precise.json: 1911 bytes,
  ef8512d75739446afac21fe62b9b82ffb1b36ba68e9ee15ada06f5b0bc3697d9.
- minus precise.json: 1912 bytes,
  b8d183769e0020542ff4ca153f7a36ec21458e52f80c7cabcd33c16de0bdac08.

## Remaining programme

This closes the native finite-direction scalar precision gate at these actual
signed spatial endpoints only. A negative direction is not proof of stable
postbuckling. Do not infer full spatial branch qualification or production parity.

Next: advance the explicitly fingerprinted precise candidate through actual
signed continuation and rollback/restart, and independently compare spatial
postbuckling stability. Physical loading path from rest, full nonlinear/plastic
continuation, wider geometry/slenderness coverage, mass/prestressed/modal/buckling
and other solver parity, independent author review, installed explicit selection,
and objective eccentric/curved beam-shell connections remain open. Preserve the
full goal; do not redefine completion around this passed scalar gate.

NO_GO_PRODUCTION_RESTRICTION_UNCHANGED. No public GE-B3 activation, push, merge,
release, tag, version or ecosystem-default change occurred.

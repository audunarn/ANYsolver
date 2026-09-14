# Private G3c local shell implementation freeze

Parent: accepted equations/review checkpoint
44c1574516b8f2c257db1c675b99c76e7fc33012.
Policy GE_BEAM3_G3C_MATRIX_POSE_SHELL_PULLBACK_V1. No accepted numerical result.

Exact new implementation extent: this document,
src/anysolver/_ge_beam3_g3c_local_shell.py,
tests/test_ge_beam3_g3c_local_shell.py,
scripts/run_ge_beam3_g3c_local_shell.py.
All existing source, shell coefficients, public recovery, aliases/defaults,
package/environment files and historical proof packets remain unchanged.

The facade captures binary64 inputs and immutable definitions, uses the actual
Procrustes Jet2 rotation plus Exp(eta)*Qaccepted, evaluates fresh actual Q4/S3
virgin elastic operators, and verifies separate signed source work channels.
It returns the complete chart/spatial pullback and detached diagnostic state.
It has no commit/restart/global owner API and reports recovery_complete=false.
No conventional single-field finite Q4 recovery is invented.

## Bounded development commands

Use C:/Python/Python314/python.exe -I -S -B followed by:

- scripts/run_ge_beam3_g3c_local_shell.py --smoke
- scripts/run_ge_beam3_g3c_local_shell.py

Run the smoke lane once before the full local lane. Smoke selects the actual
reference/finite comparison for square Q4 and right S3: two nodes, not a full
local or graph gate. The full lane has 26 test nodes: six four-shape families
(24 nodes) and two standalone work/ownership tests. Do not add those inventories
together or represent them as formal qualification. The full test families are
independent pose/reference rank, all-step map/force/tangent/energy, common-motion
and rebase, all numbering/passive/director transforms, old-chart comparison,
top-gap/domain guards; the standalone tests cover signed-work sentinels and
ownership/re-entry/nonfinite rejection. All inherited directional steps and
tolerances are retained. Same-input candidate bytes must be deterministic;
same-pose rebase compares numeric candidate fields at the invariant tolerance,
retains exact definition strings and handles source state-integrity digests
separately, since a roundoff-different local vector has a different true digest.
This is not accepted-origin replay evidence.

Both commands require a clean frozen commit and the accepted independent
equation review, verify all source/payload hashes before importing mechanics,
and bind the complete candidate and immutable environment capsule. One process
tree, one numerical thread, 24 GiB, 600-second wall bound, 120-second inactivity
bound, fresh exclusive external outputs, no retry. A child failure does not
authorize a second attempt of the same run. Correct a frozen defect under a new
commit before a new development attempt; retain failed outputs and status.

After local failures are resolved, independently review the complete actual
implementation/test extent. Full shell station tensor transport, original
PHYSICAL_RECOVERY, global graphs, atomic state/restart, G3c formal cycles and
G4/G5 must not be inferred from any subset of these development tests.

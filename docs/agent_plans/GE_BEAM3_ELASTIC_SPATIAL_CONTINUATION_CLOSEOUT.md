# Elastic spatial continuation — actual branch-segment checkpoint

Disposition: PRIVATE_ELASTIC_SPATIAL_BRANCH_SEGMENT_REPLAYED. Full goal ACTIVE.
Frozen implementation 7701e351fccbf42f5c0c0cf07e9390ae75a3cb93,
tree ecfaed1f60da0ceeb106c41011d52c0ecf81a120. Four added paths: private state
owner, unit tests, research runner and plan. No existing element mechanics,
operators, material laws, recovery, aliases, defaults or historical evidence
changed. No public selection or production qualification is claimed.

## Implemented state boundary

The new owner accepts only a strict canonical, externally hash-bound seed
packet with model, operator, physical control and dead-force identities. It
contains no material history. The owner reconstructs virgin origins and
re-evaluates the seed's equilibrium, compatibility, full bordered correction,
material response and recovery. Plastic origins or trial responses are rejected.
The ordinary controller's zero-load genesis and its singular-border rejection
are unchanged. The research trial initializer still cannot issue history.

This explicit nonzero equilibrium is an initial condition, not proof of a
physical loading path from rest. The successor's distinct capsule binds that
fact, its seed, programme and predecessor records. All accepted records replay
through physical assembly, correction and recovery. An ordinary force or
zero-origin translation capsule cannot masquerade as this schema.

## Actual N20 continuation and original-capsule replay

The preserved positive-small .003 spatial equilibrium was used as the seed
input and mechanically revalidated. The new owner then solved, not imported,
the .0045 and .006 states under purely vertical crown force with lateral
quarter-point control. No applied lateral force or artificial stabilization.

| Lateral target | Vertical load | Remaining correction |
| --- | ---: | ---: |
| 0.0045 | 0.027699984598588474 | 1.240e-14 |
| 0.006 | 0.027475446424535123 | 9.988e-15 |

Each required four Newton iterations. Equilibrium/compatibility metrics are
below 1.900e-16; global force balance below 3.885e-17 and moment balance below
9.219e-18. Every test uses the unchanged 1e-11 bounds.

The first worker paused after .0045 and replayed that exact checkpoint in a
fresh owner. Two new processes independently resumed the ORIGINAL one-record
prefix to .006, then each replayed its complete two-record capsule and recovered
all 160 stations. Their seed, checkpoint, result, recovery and completion files
are directly byte-identical. The original first record is exactly preserved.

The endpoint was compared against the separately initialized .006 equilibrium,
not used as its numerical guess. Maximum normalized field difference is
8.146e-13 (recovery); position difference 1.414e-13, nodal-frame 2.550e-13,
load 2.986e-14. All meet 1e-11. This confirms consistency for this branch segment,
not uniqueness, stability, mesh convergence or an independent-author review.

## Separate inventories and process safety

Owner unit suite: 34 passed in 11.89 seconds, fresh TEMP directory
ge-beam3-elastic-continuation-unit-20260909. Includes actual straight analytical
load/unload/reversal, byte-identical original-prefix resume, seed/schema/hash
and rehashed-checkpoint mutations, cloned/foreign/state/map mutations,
cross-schema rejection, and cancellation immediately before/after commit.
Origin rejection is tested directly; plastic response rejection uses a fault
injection. An actual yielding continuation campaign is not claimed.

Saved-data audit: 2 passed in 0.069 seconds, including 8 mutation subcases.
This standard-library postprocessor imports no mechanics; it checks chain,
field comparison, reaction balance and actual file equality. It does not
independently reconstruct the entire discrete operator or loading path.

N20 smoke: 63.375 seconds, peak 175742976 bytes. Two resume/replay workers:
76.981/76.982 seconds, maximum peak 178950144 bytes. All exit 0, empty Job trees.
The two resumption processes overlapped. Limits600s/24GiB/one numerical thread,
at most3workers/1800s wave. Existing120s context and CPU inactivity guards were
not widened. No retry, no reused output, no onset/native-analysis rerun.
No N20 cancellation or negative-branch campaign was run in this gate.

## Preservation and next work

40-entry archive verified before and after copying:
C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-elastic-continuation-7701e35-20260909

Manifest5139bytes SHA256
fdbae90dea53f7226d9451ff46da10caf8ac1571848ab8d0a4bcc05fe7c30e97.
Audit1722bytes SHA256
8fd3ce1e3fc2965de92c66a5165c57c31e33113bd8b594e6284cdd8bff4c6358.
Final checkpoint324914bytes SHA256
1ceffb6a7a35b85fca86920a5b804ef062e736e6532379e5b094c665233accab.
Original prefix217039bytes SHA256
2e4a553cf4f3ee77adc8cdbe79c4c23ff8747204103f4f976022e77f7ebb4d2d.
All TEMP originals retained. Unit output is retained in its TEMP directory;
the archive binds the tests but does not claim a raw pytest stdout recording.

Next: actual signed spatial continuation, interruption/restart tests at N20,
and FE refinement/source-equation branch comparisons. Then close broader
nonlinear/material/dynamic parity, independent review, installed explicit
selection and objective eccentric/curved beam-shell joints. Do not weaken
elastic-only rejection to import plastic histories. A production plastic
handoff needs a genuinely authenticated history and separate tests.

NO_GO_PRODUCTION_RESTRICTION_UNCHANGED. Main and concurrent ANYmesher work
untouched. No version change, public activation, push, merge or release.

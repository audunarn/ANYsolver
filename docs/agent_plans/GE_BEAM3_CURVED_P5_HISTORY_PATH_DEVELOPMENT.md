# P5 atomic nonlinear beam histories — 2026-09-06

Author research successor to `ced8e14d12d475848e074cf76f29d51305f415c3`.
This connects the nonlinear mixed local solve to one global cantilever load
path and all-station transactions. It is not production integration, general
plasticity, restart support or independent qualification.

## Global solve and immutable trial origins

The one-macro driver fixes the first vertex in all six DOFs and accepts
spatial dead nodal forces. It uses the existing nonlinear mixed residual and
consistent condensed tangent unchanged. Positions are updated additively and
nodal matrices multiplicatively; no accumulated rotation vector is used.

Every local solve and global line-search candidate uses exactly the same
committed station-origin tuple. Local convergence does not commit material
history. The global convergence check is 1e-11, with moments scaled by the
reference maximum nodal separation and forces normalized by max(1, maximum
applied force component), as in the earlier research cantilever driver.

The new global bounds are 16 Newton updates, 10 line-search candidates per
update and 256 total full mixed-functional evaluations across every local
solve in a load-step trial. Failed local evaluations count toward that total.
The existing local 25-update, 12-backtrack and 64-evaluation bounds also remain.
Bounds may be reduced by the caller but not enlarged. There is no automatic
load cutback or reuse of an external execution request. Formal process/resource
watchdogs remain required before any qualification execution.

## Atomic commit and accepted-origin replay

The pending record binds its origin epoch, geometry, nodal frames, applied
forces, all station origins, the complete local response, convergence and
evaluation counts. A canonical digest detects accidental mutation.

Commit requires an instance-owned current trial. It reconstructs the accepted
response from the accepted cell rotations, moments and original station
histories in one functional evaluation. It does not rerun local or global
Newton. Local block stability, exact response reproduction, global/local
convergence, clamp identity and complete station order are rechecked.

All new geometry, material histories and accepted-origin replay data are
allocated and validated before publication. They are published together by
one checkpoint-tuple assignment. A failure while validating the last station
therefore leaves the entire previous checkpoint unchanged. Exposed committed
state is a defensive copy. Caller-owned trial arrays are not retained as
authoritative state.

Discard, foreign/stale/repeated commit, invalid trial input and budget failures
are handled without advancing geometry or material history. Replay uses the
accepted *original* histories, not the new committed histories, and compares
the complete reconstructed response. It is a read/reconstruction operation,
not an implicit new loading/unloading trial.

These are in-memory research transactions, not an adversarial Python security
boundary or crash-safe persistent storage. No serialization/restart schema,
model fingerprint, process recovery or multi-element transaction coordinator
is implemented by this turn.

## Observed material load cycle

Reference: existing height-0.4 specimen, complete coupled elasticity and the
declared directed-hardening law (direction `[1,0.2,-0.1,0.3,-0.4,0.5]`,
y0=0.02, H=0.4). Tip force is amplitude times `[0.1,-0.3,0.2]`.
The following cycle used eight points per half, i.e. sixteen stations:

| Amplitude | Global updates | Mixed evaluations | Free residual | Plastic stations | Largest accumulated p |
|---:|---:|---:|---:|---:|---:|
| 0.05 | 3 | 10 | 2.38394e-14 | 0 | 0 |
| 0.1 | 4 | 19 | 6.68888e-15 | 16 | 0.0102017 |
| 0.2 | 4 | 19 | 4.36519e-13 | 16 | 0.0462198 |
| 0.1 | 6 | 32 | 6.37945e-15 | 0 | 0.0462198 |
| 0 | 3 | 12 | 4.39521e-12 | 0 | 0.0462198 |
| -0.1 | 5 | 23 | 3.34455e-15 | 16 | 0.0625583 |
| 0 | 4 | 15 | 1.24293e-15 | 0 | 0.0625583 |

The final unloaded tip displacement is approximately
`[0.0438515,-0.0198230,0.0277224]`. Permanent set is retained, unlike the
earlier elastic cycle. Accumulated plastic history never decreases, and every
station's yield dissipation increment is nonnegative. This is a constitutive/
transaction integration check, not an independently verified plastic engineering
reference or a complete energy-balance qualification.

The default 24-point-per-half configuration is separately tested at amplitude
0.1: all 48 station histories commit and the accepted response replays. This
does not assert equivalence with the sixteen-station cycle or close the
previously identified nonlinear quadrature issue.

## Verification and provenance

- New focused suite: **9 passed in 6.68 seconds**.
- Existing fifteen P5 suites: **232 passed in 20.83 seconds**.
- Checks cover global loading/unloading/reversal, permanent set, force/current-
  geometry moment balance, history chaining, default 48-station publication,
  complete replay, deterministic repeat from an unchanged origin, discard,
  stale/foreign/repeated commit, final-station mutation, late commit failure,
  budgets, invalid input and replay from the accepted origin.
- A test disables Newton after trial convergence and confirms that commit and
  replay still work. Another fails the final station validation and verifies
  byte-identical prior geometry/history and replay afterward.
- Driver SHA-256:
  `9260CCC6568C88C16904CE27986643E7B07292904EEF0E70870171930928DF36`.
- Test SHA-256:
  `3E54F6FE6CC42EB4902063012B07DB49A4E663905BB069EBB6C2B15C2B124115`.

This remains same-author research with the shared geometric/AD implementation
and restricted test law. Only a new research driver, test and this record are
added. No production source, B2/B3/Q4/S3 mechanics, defaults, recovery laws,
dependencies, workflows, package metadata or accepted evidence was changed.
No formal resource request, qualification cycle, merge, release or activation.

## Remaining work

Persist exact model/station/quadrature identities, accepted origins and history
with strict restart validation, and verify continuation after restoration.
Multi-element global transactions and finite load paths, general nonlinear
section adapters, independent engineering references, nonlinear quadrature,
the extreme coupled local failure, dynamic integration, buckling/postbuckling,
curved/slender domain qualification, installed-wheel exposure and objective
eccentric/curved beam-shell connections remain open. The full goal remains
active and unchanged. `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

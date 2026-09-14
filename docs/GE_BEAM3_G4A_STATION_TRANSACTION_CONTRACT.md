# GE-B3 G4a mixed station transaction contract

Status: DESIGN FREEZE ONLY. Candidate
`GE_BEAM3_G4A_MIXED_STATION_TRANSACTION_V1` is an additive private transaction
layer. It does not change a beam/shell operator, section equation, public route,
default, serialization format, or accepted G1--G3 evidence.

## Scope

G4a isolates the smallest unresolved prerequisite for S19, S20 and S24: one
owner must trial, prepare and atomically publish a heterogeneous set of section
stations. The frozen set contains one exact elastic station, one associated
six-resultant ellipsoid station and one physical-fibre station. Histories belong
to station slots, never to shared section objects or element families.

G4a is deliberately not an assembled graph solve. It cannot close S19--S24,
G4, material/solver parity, restart, shell coupling, production qualification,
or any public integration row. G4b must insert the accepted transaction into a
real three-arm graph and cover Newton/line-search/cutback/control paths. G4c must
then authenticate graph restart, final-state replay and physical recovery.

## Frozen fixture

The canonical fixture record fixes three distinct station IDs and their complete
law parameters. The six-stage multiplier history is
`[0, 1, 0.4, 0, -0.8, 0]`; each station has its own six-component strain
direction. This provides virgin, loading, unloading, zero return, reversal and
final unload without selecting a response after execution.

The elastic law has empty history and supplies resultant-level recovery only.
The ellipsoid law supplies generalized resultants and must explicitly report
that fibre stresses are unavailable. The fibre law supplies its four named
physical fibre records. No adapter may infer fibre stresses from either of the
first two laws.

## Ownership and atomicity

The owner captures immutable section identities, ordered station IDs, accepted
strains, accepted histories, accepted responses and epoch zero. `trial_all`
evaluates every station from the same accepted epoch without publication.
`prepare_all` revalidates owner/epoch/token, all immutable inputs and every
response by fresh pure-law evaluation. A proposal is single-owner and
single-use.

`commit_all` validates the complete prepared set before one owner-state pointer
swap. No section object is mutated. Failure or cancellation before that swap
leaves accepted bytes and epoch unchanged; cancellation reported after the swap
retains the new complete state. Discard, stale, foreign, replayed, reordered,
partially prepared, response-mutated, history-mutated and law-mutated inputs are
rejected. Concurrent writers fail closed.

Recovery reads only the accepted owner state, replays each recorded response
from its recorded origin, checks the complete response hash and returns ordered
strain/resultant/tangent/energy/history/provenance. Fibre rows appear only for
the physical-fibre slot.

## Bounded validation

Contract/static tests run before mechanics. Implementation tests then cover the
six-stage history, prepare failure at each slot, before/after-publication
cancellation, foreign/stale/replayed proposals, input mutation, immutable
accepted outputs, deterministic replay and exact recovery capability labels.
An independent reference reconstructs the elastic response and separately calls
the two pure constitutive laws; it never imports the transaction owner.

One process, one numerical-library thread, 24 GiB, 600 seconds, 120-second
inactivity and no retry are sufficient. Two fresh canonical cycles are required
only after smoke/rehearsal and independent implementation review. Their science
must be byte-identical. No complete wave may exceed 1,800 seconds.

Terminal precedence:

1. `BLOCKED_GE_BEAM3_G4A_PROCESS_OR_EVIDENCE`
2. `NO_GO_GE_BEAM3_G4A_STATE_OR_ATOMICITY`
3. `NO_GO_GE_BEAM3_G4A_RECOVERY_OR_WORK`
4. `PROVISIONAL_GO_GE_BEAM3_G4A_STATION_TRANSACTION_ONLY`

Every terminal retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

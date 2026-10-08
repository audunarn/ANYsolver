# Native material transaction and owner increment

The material contributor now feeds a bounded solve_material_increment method on
the existing retained native/S3 owner. It reuses structural assembly, constraints,
scales, _step, program iteration/backtracking limits and cancellation. Newton uses
the total-origin chart tangent and never replaces the physical origin with a
trial. Unresolved crossing gives explicit non-success with unchanged transaction.

NativeS3MaterialTransaction binds native mechanical state, native constitutive
history, shell displacement and friction history. Proposals carry origin identity.
Commit re-evaluates from that origin, checks coupled equilibrium/correction and
gap, validates native histories through the existing context, encodes the next
record, enforces caps, then checks cancellation before one state replacement.
Public snapshots detach arrays and retain immutable native history objects.

The versioned contact capsule reuses native canonical encoding/strict loader and
native state/history reconstruction. V2 explicitly binds the initial origin even
for an empty checkpoint. Every accepted record is replayed and compared in full;
recomputed envelope hashes cannot authorize altered physical history. The old
normal line-contact format is unchanged. Independent OpenAI read found no concrete
commit/replay defect; its empty-checkpoint binding concern produced the V2 change.

## Checks and limitations

V1 transaction checks4passed7.82s. Owner-driver run1passed/1failed6.03s: the failure
was a test assuming the existing GeneralizedCellHistory was a mutable dictionary;
it is immutable. Corrected test verifies immutability and detached snapshot arrays.
V2 module7passed7.76s. Two additional boundary checks pass4.99s: unresolved rotating
activation leaves the whole increment uncommitted, and cancellation after staged
state validation but before atomic replacement discards native/friction state.
Original failed logs retained. All routine180s/953MiB/JIToff; resource/runtime/source
records in transaction_results.json.

The actual native/S3 owner solves two small, open-contact load increments and an
authentic split restart to exactly identical capsules. Its solution matches the
existing open normal-owner reference. This is **open-state verification only**.
Active friction equilibrium, initial touch/rotating activation, distributed surface
integration and accepted friction restart remain unverified; no C5 admission.

## Next decision

The concrete blocker is rotating activation, reproduced by the bounded owner
failure. Need a first-touch/event policy on the declared physical path and actual
surface virtual work. Compare (a) equilibrated event subdivision in continuation,
and (b) a candidate-dependent event-origin return map with correctly distinguished
force map and traction derivatives. An analytical press-slide case must detect
air-gap slip and erroneous scaling of physical tangential reaction. Own independent
reviewer has a bounded read-only mechanics brief; no new runs authorized by that
brief. Retain all dimensional/derivative/state gates and the original programme.

# Native line-load accepted-chain restart and physical recovery

Successor of clean `d060dcb2921e0761113e8d7daedbefefdf9e0f4a` (tree
`f28f7254d777921e423e8c4d7eddd346a771b14e`). Preserve all prior archives,
mechanical kernels, public selectors, B2/B3/Q4/S3 mechanics and defaults.

## Exact six-path implementation extent

1. `src/anysolver/_ge_beam3_native_line_restart.py`: new typed accepted-chain
   codec, exact load-point binding, model/epoch/origin/seed/rotation/equilibrium
   validation, guarded state capture and exact supported-coordinate extraction.
2. `src/anysolver/_ge_beam3_native_line_recovery.py`: physical station recovery
   for this exact load-aware class and schema, preserving the existing physical
   recovery equations and adding the applied-pattern signature as provenance.
3. `src/anysolver/_ge_beam3_native_line_program.py`: optional authenticated
   complete checkpoint input. The constant load at resumed parameter zero must
   equal the checkpoint's last accepted effective load. No arbitrary state dict
   or implicit plastic prehistory is accepted through this private entry point.
4. `src/anysolver/nonlinear_static.py`: two exact candidate-only restart routes:
   guarded typed state ownership and selection-map coordinate extraction. All
   existing element routes retain their original implementations.
5. `tests/test_ge_beam3_native_line_restart.py`: actual whole/prefix/resumed/
   unload/failed-restart solves, typed round trips, physical recovery, mutations
   and connected interface checks.
6. This plan.

## Path and state contract

Every snapshot binds a LoadPoint containing finite binary64 parameter in [0,1],
constant LinePattern and proportional LinePattern. The effective load uses the
same constant-plus-parameter-times-proportional operation order as the actual
driver. A new segment may unload; its constant is the previous accepted pattern.
Do not replace this tuple by an inferred absolute load factor: different segment
descriptions legitimately have different provenance despite identical final
physical states. Complete uninterrupted/resumed physical states must match
byte-for-byte in the registered continuation tests; a changed path descriptor
must not be rewritten merely to make whole checkpoint bytes match.

The checkpoint binds exact model identity, all elements and nodes, stress-free
genesis, every accepted epoch, predecessor hashes, fixed plastic origins,
internal seeds, multiplicative nodal rotations, shared-node agreement and net
free-coordinate equilibrium (1e-11 normalized). Every state must have exactly
the load pattern derived from its LoadPoint. External SHA-256 is mandatory;
self-hashes are integrity checks, not authentication of a replaced valid history.
Reject duplicates, nonfinite numbers, boolean/float substitutions, unknown keys,
wrong schemas, incomplete chains, support changes, changed path/seed/history,
and noncanonical encodings. Limit 2 MiB, 65 snapshots, 16 elements/512 DOFs and
60 seconds per chain validation. No pickle, history inference or legacy coercion.

Native physical recovery uses the accepted internal cell rotations/resultants
and fixed prior origins. Section stresses remain physical, and distributed load
work is not added to section resultants. Check reference/current frame work,
the independently reconstructed lifted-Q2 station position and unchanged history.

## Cases and execution

Straight elastic single macrocell, curved plastic single macrocell, and two
connected curved plastic macrocells; supported standalones with homogeneous
constraints. Each whole solve has two increments; a typed half-load prefix
resumes to the same final state. Unload through a new negative-increment segment;
verify monotonically accumulated plastic history and typed continued-chain
roundtrip. A failed restarted increment must retain the accepted checkpoint state.

Keep inventories separate: initial straight smoke, complete restart rehearsal,
existing line-global regression, Q4 ownership regression, frozen restart cycle A
and frozen restart cycle B. One numerical thread per child; 24-GiB tree memory,
600-second wall, 120-second CPU-inactivity watchdog; at most three task workers.
No automatic retry. Freeze after rehearsal, then run A/B in fresh directories
with exact clean-head/configured-runtime guards and require byte-identical
canonical scientific outputs. Preserve every run, command and supervisor record
externally with exact bytes/SHA-256; never overwrite historical evidence.

This remains private development, not independently reviewed qualification.
General path/staged/arc-length state, arbitrary nonlinear 6x6 sections, spatial
couples, complete mass/modal/buckling/slenderness/engineering gates, packaging,
public integration and objective beam-shell qualification remain required.

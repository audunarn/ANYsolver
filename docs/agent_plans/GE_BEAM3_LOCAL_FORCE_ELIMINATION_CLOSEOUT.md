# GE-B3 local resultant elimination — development closeout

Frozen implementation `e58e6952ba51fcae4c9cd370055d004ae9ad76f0`, tree
`27e85861836c7e382ef960fceac22c69d6e1a5c9`. This follows the independent loaded
modal closeout `1200d6c1478c92e8737d53797830419a4ca7200c`.

Implemented a private linear-system component which eliminates only the
eighteen algebraic force coordinates per native macrocell, solves the smaller
global matrix through the existing ANYsolver SciPy/SuperLU interface, and
back-substitutes every removed increment. Physical cell rotations remain.
No existing controller selects it yet. No element equation, material update,
mass, recovery, accepted state, public route, legacy element or default changed.

The tests use actual complete spatial Newton Jacobians, not just symmetric
energy Hessians. They include straight/curved nonstationary trials, saved
one/two/four-macro loaded states, an accepted plastic-history successor trial,
multiple right-hand sides, factor reuse, zero RHS and an indefinite geometric
block. Invalid material blocks, cross-element resultant coupling (even 1e-20),
layout mutation and malformed RHS are rejected. No stiffness regularization,
negative-mode filtering, force-block truncation or silent symmetrization occurs.

| Saved curved macrocells | Supported full unknowns | Reduced solve unknowns | Recovered full-solve relative difference |
| --- | ---: | ---: | ---: |
| 1 | 36 | 18 | 6.95e-15 |
| 2 | 72 | 36 | 9.79e-15 |
| 4 | 144 | 72 | 2.00e-14 |

The largest componentwise full-system backward error was 1.537e-13, below the
unchanged 1e-11 check. This is matrix-solve parity, not a high-slenderness
conditioning certificate, nonlinear-path comparison or speed benchmark.

Separate inventories:

- Initial rehearsal: 14 passed, 5.286 pytest seconds.
- Complete rehearsal: 17 passed, 5.712 seconds.
- Frozen cycle A: 17 passed, 5.505 seconds (7.0199836 supervised seconds).
- Frozen cycle B: 17 passed, 5.500 seconds (7.0237295 supervised seconds).

All eight canonical packets are byte-identical between frozen cycles. No
historical nonlinear path or eigensolve was rerun. Saved checkpoints were
hash-checked and independently reconstructed by their existing native context;
accepted material states were not advanced. The two frozen processes each used
one numerical thread and a 24-GiB Windows Job, with 600-second wall and
120-second activity limits. No automatic retry occurred; no worker remains.

All forty-two raw preparation/cycle files are preserved with per-file hashes at
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-local-force-e58e695-20260907`.
Original temporary evidence remains. The exact source identities, inventories,
packet comparisons and complete archive manifest are in
`docs/reference_cases/ge_beam3_local_force_elimination_status.json`.

## Next step and completion boundary

Bind a separately selected native controller to the new factorization. Compare
complete converged paths, line searches, rejected trials, cancellation, plastic
origin ownership and restart against the dense controller on small development
cases before broader use. Keep historical paths immutable rather than rerunning
them as new evidence. Sparse assembly and public integration follow successful
transaction parity; the dense layout's current size bound is not removed here.

Independent scientific review, full standalone beam qualification, general
six-resultant nonlinear sections and the objective beam-shell connection remain
unfinished. No qualification, public activation or publication is authorized
by this linear-algebra component closeout.

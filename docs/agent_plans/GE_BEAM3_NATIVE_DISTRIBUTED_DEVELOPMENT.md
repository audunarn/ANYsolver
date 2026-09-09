# Native distributed-couple transaction and solver development

Base: 85fca8ad0e83c382a3de8367bd05b66aac374203. Reuse the preserved physical
retained operator and distributed static boundary frozen at 36dd4f4. Neither
their equations nor existing beam/shell mechanics, defaults or qualification
evidence may change. Add a direct Element implementation, not a legacy beam
subclass or an implicit promotion of the older conservative state schema.

The new private state binds line-force and distributed-couple patterns, native
pose, exact epoch/predecessor/origins/seeds, the general static reduction and
all its provenance. Reconstruct the accepted response at the stored internal
state without rerunning internal Newton. Full spatial Jacobian, general lift,
Schur tangent, applied couple, conservative-part value and physical history
must replay exactly. Live native material validators must reject a locally
valid response from the wrong load trial or store registration.

Uniform reference-line nodal translation work remains external, assembled
once. Distributed couples remain internal load work of the cell rotations.
The returned physical internal residual adds back only external nodal line
work; its chart tangent uses the frozen general condensed spatial derivative.
The actual global force driver must choose GENERAL factorization and own the
effective load pattern at every Newton/line-search/reaction assembly call.

This stage starts from virgin state only. Reject raw initial state and any
unissued driver; old line-only and nodal-couple restart codecs cannot be reused
as distributed-load authority. A subsequent complete typed distributed chain
must enable restart. Unsupported pressure, other control paths, dynamics and
mixed element families remain closed. No public selector is registered.

Tests: independent load-only/full/condensed reconstruction, actual native
commit/discard, fixed-origin directional tangent, straight and curved elastic/
plastic global equilibrium, connected shared rotations, pure distributed
torsion with zero nodal loading, actual GENERAL factorization, load/state/hash
mutations, wrong-trial/store rejection, failure cleanup, rejected initial
states and unsupported routes. Compare separate existing couple, Q4 state and
legacy B2/B3 nonlinear regressions; no historical qualification campaign rerun.

Work/algebra/equilibrium use 1e-11; independent directional derivatives use
1e-7. Do not tune loads, mechanics, cases or thresholds to force a pass. Smoke
before full rehearsal; clean implementation freeze before two fresh-directory
deterministic cycles. Require byte-identical scientific packets, preserve all
failures and raw logs externally, and keep inventory counts separate.

Each child: one numerical thread, 24-GiB process-tree memory, 600-second wall,
120-second CPU-inactivity watchdog; at most three workers and 1,800 seconds
per wave. Exclusive outputs, complete-tree termination, no automatic retry.
Independent review remains PENDING and production qualification false. General
section/path parity, consistent mass and spectral/engineering qualification,
public integration and objective beam-shell connection remain outstanding.

# Arc-owned physical stability preparation

Parent22f1e12e85ebfdf5f01b75c4ce975872c46a4ebc. Add a PRIVATE native arc-modal
entry point, preserving all existing force/arc solvers, beam/shell mechanics,
coefficients, quadrature, defaults, APIs and prior evidence. No public export.
No new arc continuation or reference BVP run. Use archived accepted step1 and
step12 states, bound through the unchanged arch-repeat manifest.

Authenticate the actual full arc chain with its own Context; preserve its
model, parameter, committed history, inertia map and checkpoint authority.
Current-rest elastic-interior perturbation only. Reject material evolution or
yield-boundary ambiguity. Use K=J^T C^-1 J+Hgeom and existing original compliance
and physical kinetic factors. Include nodal dead-force residual exactly once.
Never include the arc row/parameter column in physical stiffness, use saddle
eigenvalues as stability, or give nodal rotation traces fictitious inertia.

Check exact virgin numerical factor equality against the separately owned
force-program preparation. Add authority/mutation/cancellation tests. Then
bounded two-macro step1 smoke. If it passes, step12 and a deterministic repeat
of both snapshots. Inspect small timing before attempting larger meshes.
Use section inertia diag(1,1,1,3e-5,1e-5,2e-5) as a frozen diagnostic mass;
this is not an independent engineering-frequency reference.

For each snapshot, compare six lowest full signed factor-chain modes with a
direct stationary Schur calculation and with the ordered union of planar and
lateral modes. Partition only after original material/kinetic/geometric factors
prove structural-zero decoupling, with no small-entry thresholds. Retain
negative eigenvalues. Require positive algebraic trace block and positive
reduced physical mass; an unstable massless block cannot be dropped. Numerical
equality/residual gates remain1e-11. Root brackets remain numerical, not certified
intervals. No engineering/stability claims beyond the actually inspected mesh.

Each child: one numerical thread,24GiB/process tree,600seconds,120seconds CPU
inactivity. Max3 workers,1800seconds/wave; original120second mechanical Context
unchanged. Full frozen-input checks before and after. No automatic retry;
partial packets/logs remain external diagnostics and no canonical partial
science. Freeze before execution. Smoke before full wave. Two fresh cycles must
produce byte-identical science. Independent review remains pending.

Terminal on successful inspection:
UNCLASSIFIED_GE_BEAM3_ARC_CURRENT_REST_SPECTRA_ONLY.
This does not complete spatial refinement/continuum validation, plastic arc,
full solver/material/load/dynamic parity, independent review, installed public
opt-in or objective beam-shell joints. The full user goal remains active.

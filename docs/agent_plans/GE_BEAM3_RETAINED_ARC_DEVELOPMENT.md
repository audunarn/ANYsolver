# Retained GE-B3 current-spatial arc development

Parent: f6142deda856a6b85041abe4bc643d8fb0805bc2, tree
a66f263fc43ac3534831a6c8f93e322cbcd88b7e. Prior history/objectivity and Euler
archives remain immutable. No prior mechanics or controller is modified.

This private candidate adds a separate Program, State and canonical replay
schema, with no public routing. It composes the retained nodal operator only
for physical capture/evaluation; no dummy force path or old arc history is run.

The physical hyperplane uses A=Q Q_previous^T and
g_rotation=.5*(A-I):hat(w), whose CURRENT spatial row is
axl(skew(hat(w) A^T)). This differs from the old accepted-origin Exp-chart row.
Translations use exact dyadic products of compensated coordinate differences.
Isotropic nodal metric weights are 1/(n*length_scale^2) for translations and
1/n for rotations. Lambda has explicit inverse-square scale; internal retained
unknowns have zero metric but remain fully present in both bordered solves.
Initial orientation is an explicit signed parameter axis. Every subsequent
predictor is reconstructed from the preceding issued state, with positive
metric orientation. Each recorded step binds the predictor, actual lambda,
step size, material origins/history, reactions/work and recovery hashes.

Acceptance requires equilibrium, compatibility, absolute dimensionless chord
gap and normalized FULL remaining bordered correction <=1e-11, including
lambda and all internal unknowns. Frozen-border correction merit supplies
backtracking; there is no automatic retry or cutback. Material origins remain
fixed throughout a step. Unissued/cross-context states and resealed inconsistent
records fail closed. New checkpoints require external SHA-256 and full replay.

## Separate development inventories

- Geometry: finite frame values, independent Frobenius first variations,
  spatial finite differences, general rotations, compensated large positions,
  metric admission, and a scalar fold (not a beam postbuckling result).
- Actual elastic axial paths: both signs, analytic load/displacement/reactions,
  predictor normalization, restart and immutable recovery.
- Actual curved coupled transverse path: current-spatial full-row check and
  whole versus resumed path equality.
- Safety: resealed mutations, ownership, correction gate, cancellation at six
  boundaries, and exact program admission.
- Existing translation-controller regression, reported separately.

Freeze before bounded smoke; run a full rehearsal before any deterministic
repeat. Child limits: 600 seconds, 24 GiB/process tree, one numerical thread,
120 seconds CPU inactivity; maximum three children and 1800 seconds/wave.
Use fresh exclusive external logs; preserve failures, never retry automatically.
Scientific output equality is bytewise; finite derivative gate is 1e-7,
invariants/analytic/replay mechanics 1e-11. No thresholds are relaxed.

This closes only private controller development if it passes. Real curved-arch
post-limit branches against independent BVP references, plastic arc active-set
behavior, distributed/follower loads, solver/public integration, independent
review and complete environment attestation remain open. Plastic/spectral or
beam postbuckling qualification cannot be inferred from the elastic smoke or
scalar fold. Existing B2/B3/S3/Q4, defaults and public APIs stay unchanged.

## Preserved first smoke incident

Freeze ed6d4ed2aaa8e011be2c66a8df69cd95514745ff: geometry/admission 19
passed; axial 2 passed. The curved controller and full replay completed, but
the derivative test then indexed a one-dimensional array with the tuple of
fixed DOFs, raising IndexError. Only that test expression changes to list
indexing. Preserve external smoke directory
`ge-beam3-retained-arc-smoke-curved-exjfbaat` and its completed raw capsule;
it is a failed smoke, not accepted evidence. Mechanics, controller, cases and
tolerances remain unchanged. A new frozen validation follows the correction.

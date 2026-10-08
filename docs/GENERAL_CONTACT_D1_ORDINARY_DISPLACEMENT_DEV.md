# Ordinary displacement shell contact — development example

**Status:** implemented and locally tested; independently accepted and released
status remain open. This is a bounded D1 development profile.

Run `python examples/general_contact_ordinary_displacement_dev.py` from a
checkout with the current ANYsolver package available. The example uses the
ordinary `solve_static_nonlinear` call with `control="displacement"`, a single
`DisplacementControl` and opt-in `ContactSolverSettings`.

The model presses the bottom physical skin of a four-Q4 patch against the top
skin of two fixed S3 V2D faces. The S3 reference-surface offset is 0.01 m.
The prescribed source-node motion is −80 µm in `uz`. The example declares a
50 µm independent physical-gap budget, 10,000 Pa/m normal regularization and
0.01 N complementarity force scale. These are case settings, not application
defaults.

The solver first computes a **contact-free elastic reaction predictor** for
the prescribed displacement. The explicit force scale must not exceed that
positive predictor. It reports the predictor and the solved generalized
control force separately. The latter is the force in the solver's control
equation; the integrated normal contact force is a different quantity.

The current development run completed four steps with one active pressure
mode, an independent minimum gap of approximately −40 µm, and an integrated
normal contact force of approximately 0.07554 N. The generalized control
force was approximately −0.11692 N. Local and isolated-wheel outputs agreed
exactly on these reported mechanics fields. The wheel had SHA-256
`e17944ed67f5937247be3f196222900e3d3a3b358cd793ec9e20e2da4d4ea696`.
These observations are not engineering acceptance.

Admission currently covers one finite unit-weight nodal translation from zero
to one nonzero target waypoint, no applied loads,
the declared planar elastic Q4/S3 profile, and a resolvable contact-free
predictor. Weighted or multiple controls, moments, distributed/follower
loads, other material/formulation combinations and a general mechanism
stabilized only by contact are outside this entry. An incompatible restart
definition rejects. A commanded motion that cannot meet the physical gap
budget returns non-success; the example does not relax that budget.

The [D1 gap map](GENERAL_CONTACT_D1_ACCEPTANCE_GAP_MAP.md) lists the
remaining coupled mechanics, pressure-space, clipping, rollback, package and
independent-acceptance obligations.

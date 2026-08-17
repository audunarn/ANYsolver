# E3-A variational-closure study plan

## Authority and status

This conditional plan is authorized by the E3 route-selection packet only
because `study_e3_p.hw29_linear_isotropic_identity_v1` is
`BLOCKED_E3_P_HW29_PUBLIC_SOURCE`.  It is a study plan, not a registered
candidate, implementation plan, or production authorization.  MITC9i remains
an independent Q9 reference and does not select any Q4 equation.

The immutable base is E2-A commit
`2ac678a7f94c250fe433f66378a83508d86ee499`, tree
`f7382e2b88343ac29c9a9e3c424f618a3652cc01`.  Every historical A/B/C,
rank-four, E0, E1, and E2-A terminal remains unchanged.  The release remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

## Question

Determine whether one complete, publicly reproducible, homogeneous-isotropic
Q4 shell functional can be frozen before outcomes, with 24 external nodal
degrees of freedom and only element-local mixed variables.  The study must
close one exact chain from displacement/director kinematics through strain
measures, mixed spaces, quadrature, local condensation, virtual work, loads,
and physical-resultant recovery.

No formulation identity exists until every indispensable choice is unique.
Alternatives are compared as separately named study branches; they may not be
combined or selected using rank, conditioning, patch, or benchmark outcomes.

## Source and derivation barrier

For each statement, record `P` for printed public primary evidence, `D` for an
independent derivation with dimensional, limiting, symbolic, and review
checks, or `B` for background only.  Background evidence cannot define an
equation, coefficient, quadrature, deletion, stabilization, or pass threshold.

The study first attempts lawful acquisition of the detailed HW29 equations.
If they remain unavailable, HW29 stays blocked; no missing map or coefficient
is reconstructed from published numerical results.  In parallel, a genuinely
open variational branch may be derived, but it must freeze:

- the reference and physical frames, node/edge order, director convention,
  strain/resultant ordering, and admissible geometry domain;
- one displacement and rotation map, including work-conjugate normal moments;
- one membrane, bending, and transverse-shear interpolation;
- every independent stress, strain, multiplier, or enhancement space;
- every coefficient, normalization, deletion, and stabilization term;
- primary and sensitivity quadrature and the exact local block order;
- the uncondensed potential, first variation, tangent, and Schur reduction;
  and
- physical loads and recovery, with numerical drill quantities excluded from
  DNV stress, yielding, fatigue, and code-check outputs.

If more than one non-equivalent identity survives, the study stops
unclassified.  It may propose separately named successor candidates, but it
may not choose among them from observed mechanics.

## Fatal pre-implementation screens

Only after identity closure may an independent exact oracle test:

- 24 external degrees of freedom and exact local-variable dimensions;
- algebraic equality of mixed and condensed virtual work and tangent;
- rank 18 and exactly six physical rigid modes on affine admissible Q4s;
- no common-drill, checkerboard, or positive-mass stiffness kernel;
- D4, reversal, frame, origin, and unit covariance;
- constant membrane, bending, and shear patch closure; and
- use of ordinary isotropic `E`, `nu`, thickness, and density without a new
  public drill, Cosserat, stabilization, or inertia material field.

A valid frozen identity that fails one of these exact gates receives a
scientific NO-GO under its own future candidate name.  Missing identity or
source evidence remains blocked or unclassified and is not a mechanics
failure.

## Deferred work

Distortion campaigns, mesh-uniform stability, locking, generalized sections,
orthotropy, laminates, geometric stiffness, buckling, finite rotations,
nonlinear response, consistent dynamics, coupling, performance, production
dispatch, serialization, and public API work remain outside this study.  Each
requires a separately registered dependent plan after an exact linear
identity passes.

## Evidence and terminal

The study may create only content-addressed plans, source registries,
derivations, exact cases, oracles, contracts, reports, and reviews.  It makes
no `src/`, package, workflow, selector, export, serialization, dispatch,
default, push, publication, or cleanup change.

Its possible terminal is one of:

- `BLOCKED_E3_A_PUBLIC_SOURCE_OR_IDENTITY`;
- `UNCLASSIFIED_E3_A_VARIATIONAL_CLOSURE`;
- `NO_GO_E3_A_FATAL_KINEMATIC_SCREEN`; or
- `PROVISIONAL_GO_E3_A_CANDIDATE_REGISTRATION_PLAN`.

Only the last terminal authorizes a new, separately named candidate
registration plan.  None authorizes implementation or production use.

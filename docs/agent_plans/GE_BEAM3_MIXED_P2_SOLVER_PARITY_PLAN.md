# GE Beam3 Mixed P2 Solver-Parity Preregistration

## Authority and purpose

This successor starts from accepted closeout commit
`9d2bde784356bc7a5a8d314cd91be60c607acac2` and retains the private
`CANDIDATE_GE_BEAM3_DC_MIXED_K1_MACRO_V2` mechanics unchanged.  Its purpose is
to qualify the remaining straight, standalone, linear-elastic interfaces before
the reserved `ge-beam3` selector or formulation identity can be issued.

The accepted P1 evidence covers only a globally straight, collinear, two-cell
macroelement with equal reference cells and zero reference rotation jump.  It
does not authorize solver-coordinate tangents, state transactions, loads, mass,
modal or buckling analysis, restart, recovery, packaging, or public selection.

## Solver-coordinate and state gate

The accepted research tangent differentiates a left-spatial perturbation
`Exp(x) Q_trial`.  The nonlinear solver varies the additive coordinate increment
`delta`, while the authoritative node-shared update is
`Q_trial = Exp(delta) Q_committed`.  The solver path shall therefore derive its
residual and Hessian from the same mixed potential using
`Exp(delta + x) Q_committed`.  The existing research evaluation and its accepted
hashes remain unchanged.

The element shall use the existing node-shared native-rotation transaction.
Native matrices are spatial operators initialized to identity; absolute material
triads used by the beam mechanics are `Q_operator @ R0`.  A model-bound,
integrity-sealed beam state shall bind the exact reference line and triad,
connectivity, policy identifiers, section stiffness and mass fingerprints,
committed displacement, committed spatial operators, four sided station records,
and recovered local variables.  Trial state is committed only with the enclosing
global transaction.  Rejected line searches, cutbacks, cancellations, and
exceptions must preserve the committed state and rotations exactly.

The current linear SPD generalized section is adapted as a stateless four-station
contract.  History-bearing or mutable section objects remain rejected until a
separate partial-complementary trial/commit/discard contract is preregistered and
qualified; legacy fibre return mapping is never wrapped or postprocessed.

## Loads, recovery, inertia, and spectra

Existing nodal loads remain spatial dead loads.  A private, direct element
reference-line load descriptor may support only spatial-dead and material-dead
distributed forces and couples, measured per unit reference arclength, with
constant or nodally linear interpolation and exact consistent integration on
both half-cells.  It is not added to ``LoadCase`` or public serialization in P2.
Follower loads remain typed, fail-closed capabilities.

Native recovery shall return the four sided stations `[-1, 0-, 0+, 1]`, keeping
both midpoint limits, generalized strains and resultants, reference/current
frames, policy identities, and provenance.  It shall not invent fibre stress,
von Mises stress, or section quantities not supplied by the section.

Reference consistent mass requires the section's validated 6x6 inertia per unit
length.  Each half-cell uses the exact linear consistent mass operator, including
translation/rotation coupling, transformed through the persisted reference
triad.  Missing mass authority fails closed.

Reference-elastic modal analysis is permitted only after six free-body modes,
positive physical mass, orientation/reversal covariance, and independent
frequency comparisons pass.  Reference-elastic Euler buckling uses an
unambiguous compression-positive ``axial_compression`` value or, exclusively,
a tension-positive ``axial_force`` value.  Each half-cell adds
``P_compression / ell * [[1,-1],[-1,1]]`` to each local transverse translation
pair, transformed by the reference triad.  Duplicate, ambiguous, nonfinite,
Wagner/torsional, current-state, and legacy geometric terms are rejected.
Current-state modal/buckling, every linear or finite-rotation transient route,
gyroscopic terms, and follower-load stability remain outside this stage and
must fail before element mechanics evaluation.

## Private-parity and successor opt-in boundary

P2 ends with a private-parity terminal.  It cannot issue the reserved formulation
ID, expose `ge-beam3`, build a selector-bearing qualification wheel, or edit
public factories/exports.  A successful P2 authorizes a separately preregistered
P3 gate that freezes the exact selector, serialization, package-isolation, and
paired-performance candidate before testing that exact wheel.  This removes any
circular post-acceptance code change.

Existing B2/B3, `beam`, `quadratic_beam`, Q4, S3, and all defaults and aliases
remain unchanged.  Historical beam records never infer GE Beam3, and
cross-formulation restart is rejected.  P3 must test an installed wheel outside
the repository with source paths removed and may impose the five-percent legacy
route regression bound.  P2 makes no performance or package claim.

## Verification and process controls

The canonical state schema, exact scientific case manifest, and independently
authored standard-library reference program are separate hash-bound
preregistration inputs.  Required development checks include
nonzero-increment solver-chart directional
agreement; two noncommuting committed increments; rollback and split-restart
identity; shared-node operator identity with distinct material triads; reversal
and orientation covariance; exact dead-load work; mass row sums and kinetic
energy; sided recovery; free-body modes; modal and Euler reference comparisons;
and strict native state/restart encoding.  Selector serialization, an installed
wheel, and performance are reserved for P3.

Formal mechanics runs use fresh external directories, one numerical-library
thread, at most 24 GiB per process tree, at most 600 seconds per child, at most
three concurrent children, and at most 1,800 seconds per complete wave.  No
automatic retry or request reuse is permitted.  Two accepted canonical cycles
must be byte-identical.

Terminal precedence is:

1. `BLOCKED_GE_BEAM3_P2_BASELINE_OR_AUTHORITY`
2. `BLOCKED_GE_BEAM3_P2_PROCESS_OR_EVIDENCE`
3. `NO_GO_GE_BEAM3_P2_SOLVER_CHART_OR_STATE`
4. `NO_GO_GE_BEAM3_P2_LOAD_MASS_OR_RECOVERY`
5. `NO_GO_GE_BEAM3_P2_MODAL_OR_BUCKLING`
6. `PROVISIONAL_GO_GE_BEAM3_P2_PRIVATE_PARITY`

The successful terminal authorizes only preparation of P3 selector/package
qualification.  It does not authorize any explicit production use.  Curved or
kinked reference geometry, history-bearing sections, follower loads, linear or
nonlinear transient dynamics, beam-shell joints, default activation, versions,
tags, publication, and ecosystem exposure remain separate successor work.

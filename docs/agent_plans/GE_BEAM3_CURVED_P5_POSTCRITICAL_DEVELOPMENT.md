# P5 planar postcritical reference and beam comparison — 2026-09-06

Research successor to `61ae9c998b3e71e468a819bbe3e7f7ea9165f937`, tree
`43101e70ded8e3f36b0c189152fb712bdb7229c3`. This adds a separate continuum
reference, explicit elastic branch initialization and tests. It does not
modify the existing beam, assembly, continuation or restart mechanics.

## Source preservation and equation map

Milan Batista, arXiv:1508.04424v3, requested from
`https://arxiv.org/pdf/1508.04424v3`. Preserved external PDF:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-elastica-source-20260906\batista-1508.04424v3.pdf`.
Bytes: 1,698,090. SHA-256:
`5B596FA9B26D6AFDAD8A7C7501CE795DA47E7F1B7FD710643FA0D56E763E5E63`.
The archive identifies v3; the PDF retains its older printed 2015 header.
The hash binds the actual downloaded bytes, not an inferred publication date.

The PDF skill required visual verification. Browser screenshots failed; local
Poppler rendering was inspected for complete printed pages 2, 3, 4, 25 and 26.
Relevant source locations: equations (1)-(2) for reference-arclength kinematics,
(5)-(6) for equilibrium, (7)-(10) for linear section relations and force/strain
signs, (94) for clamped/free-moment cantilever conditions, and (98) for its
critical load. No follower-force example is substituted for this dead-load case.

The first-integral regularization and numerical method below are derived here.
They are not the paper's Jacobi-function implementation, independently authored
mechanics review, or a formal source-authority execution contract.

## Derived reference

Use an initially straight planar cantilever of length L, clamped at s=0, with
spatial dead force (-P,0) and zero end moment. Reference arclength s is not
deformed arclength. Axial, shear and bending stiffnesses are EA, GA and EI.
The benchmark family requires positive finite stiffnesses, GA<=EA, positive
axial stretch, and first-branch terminal angle 0<a<=pi/2. These limits define
this reference family only, not the ultimate beam formulation's admitted scope.

Set delta=1/GA-1/EA. In a director basis with angle theta:

    N=-P*cos(theta), Q=P*sin(theta), M=EI*theta_s,
    x_s=cos(theta)-P*cos(theta)^2/EA-P*sin(theta)^2/GA,
    y_s=sin(theta)*(1+P*delta*cos(theta)).

Integrating the scalar moment equation with M(a)=0 gives

    M^2=EI*P*(cos(theta)-cos(a))*(2+P*delta*(cos(theta)+cos(a))).

Set k=sin(a/2) and sin(theta/2)=k*sin(phi), 0<=phi<=pi/2. Then

    ds/dphi=sqrt(EI/P) /
        sqrt((1-k^2*sin(phi)^2)*(1+P*delta*(cos(theta)+cos(a))/2)).

This removes the free-end square-root singularity. The implementation evaluates
cos(theta)-cos(a) as 2*k^2*cos(phi)^2 to avoid small-angle subtraction loss.
Gauss integration of ds, x_s*ds, y_s*ds and strain-energy density gives length,
shape and energy. A scalar load bisection enforces length L. Separate bounded
bisections locate requested material stations; force, moment and strain fields
are then evaluated there. M(s)=P*(y_tip-y(s)) is checked independently against
the first integral. There is no shooting in the reference implementation.

At a=0, Pcrit*(1+delta*Pcrit)=EI*pi^2/(4*L^2). A cancellation-safe positive
quadratic root agrees with the source's equation (98) after converting its
dimensionless parameters. The reference explicitly retains axial and shear
compliance rather than comparing a finite-compliance beam to an inextensible
elastica without accounting for model differences.

Orders are restricted to 32/64/128, stations to 2..65, and each scalar bisection
to at most 64 iterations. Unresolved length, station inversion, moment balance,
input domain or positive stretch fails closed. Only dataclasses, math and NumPy
are imported. It is binary64 with tested refinement, not interval or
multiprecision certification; full independent-author review remains open.

## Elastic discrete branch initialization

The new seed helper accepts a virgin assembly and an explicitly supplied shape,
shared rotation matrices and dead force. It works on a fresh model copy and
uses the unchanged mixed operators. At most 16 Newton updates, ten backtracks
per update and 256 mixed evaluations per element are allowed. Rotational
increments retain the 0.9*pi bound. Singular/local/budget failures are preserved;
there is no automatic retry, branch switching or stiffness regularization.

Every seed evaluation must remain elastic. A nonlinear section that yields
cannot acquire an invented loading history from a postbuckled shape. After
convergence the complete accepted-origin assembly transaction validates before
returning the new model. Late-element failure leaves the caller's state intact.
This is branch initialization, not proof of a physical path from the undeformed
state or a general nonlinear restart/migration mechanism.

## Observed beam comparison

Fixed development case: L=2, EA=1000, GA=400, EI=1, a=0.6 radians.
Critical reference load: 0.6162805724521121.
Postcritical reference load: 0.6449785996190569.
Spatial beam C=diag(1000,400,400,2,1,2), reference axis 2=global z, so the
in-plane bending stiffness is local EI_y=1 and the relevant shear component
is local z. The section yield bound is 1e6 and hardening 1; no station yields.
All elements use order 8. Reference x in [0,2] is translated by -1 for the
existing straight reference builder. Shape and Rz(theta) supply the seed.

| Macro elements | Result | Solved tip angle | Relative tip displacement error |
|---:|---|---:|---:|
| 1 | Seed solve failed, not retried | unavailable | unavailable |
| 2 | Seed solve failed, not retried | unavailable | unavailable |
| 4 | Resolved buckled equilibrium | 0.5795857409258459 | 0.03449512768991858 |
| 8 | Resolved buckled equilibrium | 0.5949766927540527 | 0.00849343852167173 |

Errors compare positions at the same compressive load and normalize by the
continuum tip-displacement magnitude, not absolute tip coordinates. Explicit
tip-angle checks prevent the straight branch from being accepted as a match.
The four/eight-element solves each recorded 168 mixed evaluations. The initial
coarse failure wrapper did not print its underlying exception cause, so no
local-formulation diagnosis is asserted for those two failures. The helper
now includes that cause in future failure messages. The failed cases were not
rerun to fill this missing diagnostic and their failures remain unresolved.

Three additional 0.01 pseudo-arclength steps from the eight-element state are
tested. At each solved tip angle, a new continuum reference gives the matching
load and shape; both differences must be below 2%. This is a branch-parameter
comparison, not adjustment of section coefficients, loads or qualification
tolerances. It does not establish a limit point, broad slenderness coverage,
all eigenmodes, dynamic stability or general postbuckling qualification.

## Verification and inspected hashes

- Reference suite: **22 passed in 0.50 seconds**. Includes independent SciPy
  elliptic-integral solutions when EA=GA, a separately coded arclength ODE
  integrated with DOP853 and a 5,000-evaluation cap, critical-load agreement,
  small-amplitude limit, 32/64/128 convergence, work/force/moment consistency,
  deterministic serialization, parser/input bounds and import separation.
- Seed/beam suite: **5 passed in 11.92 seconds**. Covers the resolved four/eight
  cases, three postcritical continuation steps, elastic-history guard, budgets,
  clamp/nonvirgin rejection and late-commit rollback.
- Existing continuation suite: **15 passed in 12.53 seconds**.

These were small development/unit checks, not a formal qualification wave,
resource-request retry, paired benchmark or evidence promotion. SciPy was
already present and is used only by the separate ODE/elliptic tests; no package
metadata or dependencies changed.

SHA-256 values of inspected working files:

- Reference: `1BEB1193915F1874C478E52CEE43E95A25A6B1758A47B95A9573EC5B211C8FEC`.
- Seed helper: `85B4084D2B5399640DB2A2B70237F7ED8F687ABFBE101DA0E3127CEE898A43E2`.
- Reference tests: `C92DC2DAC7902E79BE260589D6530280B68BFD92B1136108335840B771E8228E`.
- Seed tests: `B9AC62BE88C8550FC449EEC3FF3D5590D769CE57967C0B1AD4665118C2E54067`.

## Resume and remaining goal

Continue on the same P5 branch/worktree. Next investigate the preserved coarse
branch-initialization failure under a separately explicit diagnostic scope,
and extend the compression reference to a bounded buckling/load-path comparison
across section/slenderness scales. Do not infer the eight-element result covers
coarser meshes or the extreme coupled local failure recorded earlier.

Curved arches/rings and real limit-point references, general nonlinear sections,
controller persistence/cutback, prestressed modal/buckling, dynamics, independent
mechanics authorship/review, installed-wheel integration and objective eccentric
or curved beam-shell connections remain open. Full qualification is incomplete.
No src, existing B2/B3/Q4/S3 mechanics, defaults, production state/recovery,
accepted evidence, package or workflow changed. No push, merge or publication.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

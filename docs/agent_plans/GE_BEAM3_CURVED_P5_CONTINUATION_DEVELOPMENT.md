# P5 objective equilibrium continuation development — 2026-09-06

Research successor to `29698bccc92a7adc9979860e2e92d269379d7bb3`, tree
`faa329b141c13491fd4de4999f620748c393b917`. This adds a continuation driver,
not a new beam formulation. Existing beam assembly, local station mechanics,
section laws, restart codecs and historical qualification evidence stay intact.

## Method and equation authority boundary

Background: [BifurcationKit's primary PALC documentation](https://docs.sciml.ai/BifurcationKit/stable/PALC/),
accessed 2026-09-06, equations E/N/PALC and bordered-system description. The
predictor/corrector extends equilibrium by a tangent-oriented constraint. This
implementation is authored here and uses no BifurcationKit dependency/code.
The matrix-frame embedding below is a repository derivation, not a claim that
the cited documentation supplies or independently validates beam mechanics.
The source is not a hash-frozen scientific execution authority.

For dead forces lambda*p, solve f(x,U)-lambda*p=0 on free nodal DOFs. At each
accepted point, solve the bordered tangent system [J,-p; W*t_previous] for a
direction, normalized in W. This avoids requiring J itself to be invertible
at a simple fold. No pseudoinverse, empirical stabilization, stiffness shift,
branch switching or bifurcation classification is used. A singular augmented
system is a typed failure.

The predictor is corrected with a hyperplane in positions, frame chords and
load factor. For node i, reference accepted frame U0 and predicted spatial
rotation rate w0, its rotation contribution is

    (weight/2) * <U-U0, hat(w0)*U0>_F.

Its exact spatial derivative is

    weight * axl(skew(hat(w0)*U0*U.T)).

At the accepted origin this is weight*w0. Translation weights are
1/(free_node_count*reference_span^2), rotation weights 1/free_node_count and
load-factor weight 1. Thus rotational motion participates without accumulated
rotation vectors, numerical frame differentiation or a logarithm branch for
the path metric. The constraint value/gradient transform objectively under
proper common rigid re-expression. This chord constraint is a local path
parameterization, not an exact geodesic arclength or a mechanics potential.

The existing energy Hessian is not altered. For the continuation Newton
equations, the derivative of spatial residual components away from rotational
equilibrium is H-0.5*hat(f_rotation) in each rotational diagonal block, as
obtained from the first BCH commutator. The skew term vanishes at free-node
rotational equilibrium with dead forces. It is checked against independent
central differences of spatial residuals in a nonequilibrium beam state.
This coordinate-derivative correction is not a physical stiffness modification.

## State ownership and bounds

The driver privately copies an accepted assembly. A trial works on another
staged copy, with every station origin fixed throughout prediction and Newton.
It may update geometry and lambda, but cannot commit local or global history.
After convergence, the normal assembly trial and all continuation metadata are
bound together. Commit checks ownership and mutation, replays all elements
through the unchanged assembly transaction on a further staged copy, and then
publishes model, load factor and orientation in one checkpoint assignment.
Late-element failures leave all three accepted components unchanged.

There are at most 16 corrector updates, ten line-search candidates per update
and 256 mixed evaluations per element. The explicit step is positive and at
most 0.25 in the fixed path metric. Rotation increments at or above 0.9*pi
fail or reject that line-search candidate. Callers may lower iteration and
evaluation budgets. No automatic retry, step-size adaptation or cutback occurs.
Each explicit trial is bounded; no unbounded wave runner is introduced.
Formal or resource-heavy campaigns still require their separate process-tree,
memory, wall/activity watchdogs and resource administrator authorization.

The assembled restart codec can persist the accepted beam state. Resuming this
driver additionally requires the explicit load factor and path orientation.
Their complete persistent controller schema is not supplied in this gate.
A restart test passes those separately and obtains byte-identical next trials;
this must not be described as full continuation-controller restart qualification.

## Tests and observed behavior

New suite: **15 passed in 12.55 seconds**. The initial eleven tests passed;
frame-chord and covariance extensions raised that to thirteen passing tests;
the final arch and restored-continuation tests raised it to fifteen. No failing
mechanics test was hidden by a changed tolerance.

Unchanged connected-assembly and assembled-restart regression suites:
**74 passed in 27.24 seconds** (20 assembly and 54 restart tests). Timings are
ordinary test diagnostics, not performance acceptance measurements. No formal
resource wave or consumed-request retry occurred.

- Exact scalar equilibrium lambda=u-u^3 is followed through its mathematical
  fold, onto the negative-slope branch and beyond u=1. The exact singular
  load-controlled tangent at the fold has a nonsingular continuation border.
  A genuinely singular augmented example fails without regularization.
- A coupled two-element beam matches ordinary load control before a fold.
  Accepted-origin replay, discarded/foreign/altered trials, defensive copies,
  zero iteration/evaluation budgets and late-element commit failure are tested.
- The spatial residual derivative is checked at 1e-7 normalized error. The
  objective frame-constraint derivative and its rigid re-expression are checked
  separately; full beam path covariance is checked at 1e-11.
- A two-element, both-end-clamped height-0.1 parabolic arch with
  C=diag(100,100,100,1,0.1,0.1), elastic yield bound 1e6, and downward crown
  force takes twelve explicit 0.04 steps. The crown passes below the reference
  endpoint axis; load remains increasing and the free tangent remains positive.
  This is a finite-compression smoke case, not a snap-through or buckling proof.
- Before the frame-chord refinement, a twenty-step translation/load-metric
  exploratory run of the same arch also completed without a fold. Its last
  load factor was 0.7933740054417018 and crown ordinate -0.15614247377786816.
  Those belong to the earlier path parameterization, not the final regression.
  The frame term was added to include rotational directions objectively, not
  to force a fold or alter the arch's mechanical equilibrium curve.

No independent beam snap-through/postbuckling engineering reference, limit-load
convergence, imperfect-branch selection or compressive slenderness qualification
is established here. The exact scalar fold tests the continuation algorithm,
not the beam formulation's postbuckling accuracy.

Inspected implementation SHA-256:
`27D8B76D212889AA3DF33074308EA573C801C3A4FE556095A6324E1B0E4DF06C`.
Inspected test SHA-256:
`040491238A2B61F96427E095C076B912C85AE4B507B72B395D0149BBCCEBBFCB`.

## Next work and full objective

Freeze an independent geometrically nonlinear beam compression/elastica or
arch reference and its supports, imperfections, section scales and load measure.
Then compare an explicitly bounded refined beam path, including a real limit
point or postcritical branch, without changing the beam mechanics to fit it.
Preserve any local mixed-system failure as a distinct unresolved finding.
Controller persistence and explicit bounded cutback need their own tests.

General nonlinear sections, broad curved/slender coverage, the extreme coupled
local failure, independent mechanics authorship/review, prestressed modal and
buckling, dynamics, installed-wheel production integration, and objective
eccentric/curved beam-shell connections remain open. The goal is unchanged and
incomplete. No source under src, existing element/default, package, workflow or
historical qualification evidence changed. No push, merge, release or activation.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

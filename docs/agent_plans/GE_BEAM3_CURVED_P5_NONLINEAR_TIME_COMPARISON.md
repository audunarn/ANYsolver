# P5 nonlinear time-comparison development

Parent `793e9fb8502980a32a99a7f1c880f787472c8b7f`, tree
`0523cc26d78582eb9dee9e14fa0f29ebab767c95`.
Preserve the midpoint and backward-Euler checkpoints and every existing
mechanics/default/evidence file. Add only this plan, a separate research time
reference and small tests. No production authorization or resource wave.

## Question and independent extent

Does the retained-spin midpoint method converge at second order for a curved,
coupled, finitely rotated, free-vibration macrocell, rather than only its
straight axial invariant subspace? What energy and spatial linear/angular
momentum drift does it introduce?

The comparison uses a separately implemented classical RK4 method. Its cell
rotations are Exp(beta) Uinitial with beta-dot=Jleft(beta)^-1 omega. beta is a
temporary short-trajectory coordinate, not a production accumulated rotation
state. It separately solves algebraic vertex traces and the retained physical
mass system for accelerations. It does not import either existing time-step
implementation or their endpoint-trace solve.

It DOES share the elastic potential and finite-inertia operators. Therefore
it separates time discretizations of the same semidiscrete equations, not
independent mechanics or continuum reference errors. Same-author verification
does not satisfy independent scientific review. No generic production dynamic
integrator is selected by this experiment.

## Registered small development case and observations

One free macrocell, reference nodes (-1,0,0), (0,0.4,0), (1,0,0), and the
existing coupled elastic and eccentric/coupled inertia unit-test sections.
All translations and cell spins are dynamic; all nine nodal rotation traces
are algebraic. No external forces or constraints. Initial nodal displacement:
[(0.01,-0.02,0.015),(-0.015,0.01,0.02),(0.02,0.015,-0.01)]. Initial cell rotation
vectors: [(0.2,-0.1,0.15),(-0.1,0.18,0.05)]. Initial nodal velocities:
[(0.04,-0.02,0.03),(-0.01,0.05,-0.02),(0.02,-0.03,0.01)]. Initial cell angular
velocities: [(0.3,-0.2,0.4),(-0.25,0.35,0.15)]. Solve consistent initial traces.
The two cell rotation/velocity axes are not parallel.

Duration 0.08. Midpoint partitions 4/8/16; separate RK4 partitions 16/32.
Run a 4-step smoke comparison first. Every accepted midpoint trial must pass
fresh replay before commit. Compare final x, U, v and omega, scaled by reference
length and duration. Normalize by the actual reference trajectory change, not
the absolute rigid position. Record endpoint total-energy, linear-momentum and
angular-momentum differences relative to the initial state. Do not call
nonzero drift exact conservation or classify it as a mechanics failure.

Development checks: RK4 refinement difference must be less than one twentieth
of the finest midpoint/reference difference; each midpoint refinement must
reduce the final state difference, with final observed order in [1.8,2.2].
Energy/momentum drift is reported and checked for refinement where above a
1e-11 numerical-resolution floor, not used as a new production tolerance.
Keep failed checks visible; do not retune this case to obtain a pass.

## Bounds and safety

RK4: at most 32 steps / 128 RHS evaluations; each fresh algebraic trace solve
at most ten updates and 64 potential evaluations with ten line-search
attempts. Trace residual divided by reference length <=1e-11. Check positive
physical mass through Cholesky. No mass on nodal traces or static elimination
of cell spins. Temporary rotation chart norm must stay below 0.9 pi.
Maximum reference integration wall time 600 seconds, checked at each RHS and
trace evaluation. The existing midpoint bounds remain unchanged. No automatic
retry. Only small unit tests are run here; future heavy campaigns require the
separate administrator resource process.

Tests also check the inverse Exp Jacobian, reference force balance, free-body
instantaneous energy/momentum rates, model/input rejection, bounds and import
independence from the two time-step implementations. Successful tests only
authorize further research, not qualification, integration or publication.

## Observed result

The five smoke/control tests passed in 7.27 seconds before the refinement
study. The initial full seven-test study passed in 50.05 seconds. After adding
nonfinite/comparison and injected trace-failure controls, the final combined
time-reference, midpoint, axial temporal, backward-Euler and finite-inertia
suites passed **82 tests in 94.89 seconds**. Nine tests belong to this new
comparison suite. No test failure or resource retry occurred. These times are
test-run diagnostics, not speed claims or qualification acceptance thresholds.

| Midpoint steps | Relative physical-state difference | Relative energy drift | Scaled linear-momentum drift | Scaled angular-momentum drift |
| ---: | ---: | ---: | ---: | ---: |
| 4 | 0.005423062905277418 | 3.7765382165245184e-5 | 8.345726999880784e-6 | 2.695781817629548e-6 |
| 8 | 0.0013658669141612561 | 9.233197006223878e-6 | 2.168571872932864e-6 | 6.95216397446447e-7 |
| 16 | 0.0003420985741857575 | 2.2951056795041843e-6 | 5.47357473568893e-7 | 1.7517646219437285e-7 |

The final observed temporal order is **1.9973329224427678**. The 16/32-step
RK4 relative state refinement difference is **1.4742379039764215e-7**, well
below one twentieth of the finest midpoint difference. The reference used
exactly 64 and 128 RHS calls. Its relative energy drifts were
1.5999883315193606e-8 and 5.991012021782534e-10; linear-momentum drifts were
9.796100863915853e-9 and 5.992422625190249e-10; angular-momentum drifts were
5.21590714368787e-9 and 3.2082996993784517e-10.

Physical-state difference uses x/reference-length, cell-frame Frobenius
difference/sqrt(2), velocity*duration/reference-length and angular
velocity*duration. It is divided by the reference initial-to-final state
distance, not a continuum engineering error. Energy drift is relative to
initial total energy. Each momentum drift is divided by max(1,norm(initial
momentum)) in this fixture's units. The reference refinement difference is an
observed numerical difference, not a rigorous error enclosure.

Instantaneous free-body energy and both spatial momentum rates pass the
separate directional time-derivative checks at 1e-7. Nonzero discrete drift
remains visible and decreases on each tested refinement. This supports the
second-order midpoint development method for this curved coupled trajectory;
it proves neither exact energy-momentum conservation nor general nonlinear
dynamic qualification. No prior evidence is reclassified.

## Preserved boundary and next step

Exactly three new research paths are added. Previous files, including both
time steppers and the elastic/inertia operators, remain unchanged relative to
the parent. No production mechanics, public API, aliases, defaults, package,
dependency, workflow or version changes occur. No external qualification
aggregate, resource request, formal cycle or publication is created.

The next substantive step is bounded multi-element retained-spin dynamics:
assemble shared nodal translations and massless traces before their global
algebraic equilibrium solve, retain six inertial cell spins per macro, and
verify shared-node work, rigid motion, the reference full-inertia chain pencil,
and atomic multi-element state handling. Preserve the single-macrocell temporal
results as regressions. Material-history dynamics, native solver/restart
integration, independent scientific review and beam-shell coupling remain open;
the overall production beam goal is not complete.

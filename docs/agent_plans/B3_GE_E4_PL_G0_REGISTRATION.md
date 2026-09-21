# B3-GE / E4-PL multi-element coupling: G0 registration

Status: **G0 IN PROGRESS; no new mixed capability qualified.**

The bounded footprint candidate equations and their open mechanics questions
are recorded in `B3_GE_E4_PL_G0_FOOTPRINT_MECHANICS.md`.
An independent review at commit `5e1cad6` found two P1 proof defects and
two P2 scope gaps; its immutable findings are in
`B3_GE_E4_PL_G0_FOOTPRINT_REVIEW_V1.md`. The original diagnostics stay
unchanged and do not close F04.

This registration implements the first gate of the user-approved complete
development programme. Its terminal outcome is one full release only after
G0–G6 pass. An elastic or point-only milestone is not a release substitute.
The complete programme includes V01–V28, required external comparisons, the
10,000-shell/1,000-beam workload, ANYfem integration, and independent reviews.

## Baseline and identity

- Accepted `origin/main` and isolated starting commit:
  `be41a77a62e1cd7e1767bda6e955253af0819f91` (ANYsolver 0.4.7).
- Integration branch: `codex/b3-ge-e4-pl-integration`, isolated worktree.
- Production profile reserved for the new owner:
  `B3_GE_E4_PL_STIFFENED_SHELL_V1`. It is not an acceptance assertion.
- The default interpreter reports Python 3.14.2 and installed ANYsolver 0.4.6;
  source and installed-package baseline checks must identify their origins.
- The previously released 0.4.7 wheel has recorded SHA-256
  `99c30875ec602d26b5f1ba8b3fb858ced95acefdd01d4ecf3274470ca8bf9307`.
  Verify the local copy before using it; do not infer baseline qualification
  from a 0.4.6 import or a source-only test.

## Frozen programme decisions

- The first representative application is an eccentric stiffened flat panel.
- Intermediate gates remain experimental; all G0–G6 requirements are mandatory
  for one complete release. No performance or external reference can be
  substituted by extrapolation or generated input alone.
- Use one global equilibrium and atomic accepted predecessor; preserve all
  existing B3, GE, native B3-GE, one-shell coupled, Q4/S3, and checkpoint paths.
- Sparse production assembly retains native beam internal coordinates; the
  existing dense beam owner is a bounded oracle, not the large-model route.
- Exact multiplier line coupling is required. Candidate low-order spaces are
  evaluated before a production choice; penalties are diagnostic only.
- A G0B mechanics failure prevents G1 product integration. Changing a
  criterion after seeing candidate data requires an explicit reviewed revision.

## G0A baseline inventory

Record source and installed package identities, CPU/memory/OS, backend and
thread environment; run the existing pose-joint, variational-shell,
coupled-free-beam, durable-coupled, and affected sparse/constraint tests.
Preserve complete logs and record exact test selectors and counts. Freeze case
definitions, physical scales, tolerances and resource budgets before G0B
candidate comparisons. A failed baseline is investigated, not declared a
new-work regression without an accepted-main comparison.

The initial **source regression** inventory is fixed to these eight files,
executed in one pytest invocation from the isolated worktree with its `src`
directory first on `PYTHONPATH`, bytecode disabled, and the repository's
pytest configuration:

```text
tests/test_ge_beam3_pose_joint.py
tests/test_ge_beam3_variational_shell.py
tests/test_ge_beam3_coupled_free_beam.py
tests/test_ge_beam3_durable_coupled.py
tests/test_constraint_audit.py
tests/test_ge_beam3_native_generalized.py
tests/test_ge_beam3_native_fibre_static_element.py
tests/test_e4_pl_s3_v2d_native_state_corotational.py
```

Use `python -m pytest -q` with a fresh output directory for this ordinary
regression, preserving the complete log and process exit code. This is source
baseline evidence, not a substitute for the separate 0.4.7 installed-wheel
baseline or G0B scientific acceptance. Add focused failures to the inventory
through a versioned revision rather than replacing this log.

Setup incident on 21 September 2026: the first attempt at `g0a-source-v1`
in the managed worktree under the user profile exited 1 before pytest could
start. The sandbox denied creation of the evidence directory; Numba also
refused import-time caching there. No scientific test case ran and no canonical
log was created. The clean worktree and branch were moved with Git to
`C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling` without changing
HEAD. The same source inventory will run as `g0a-source-v2` with an accessible
evidence path. This preserves the failed setup attempt as an incident, not a
test failure or successful qualification.

The second setup attempt (`g0a-source-v2`) also stopped before pytest:
the sandbox denies creation of `.qualification` beneath this nested Git
worktree. The worktree source imports successfully when bytecode is disabled
and `NUMBA_CACHE_DIR` points to a writable, ignored evidence directory in the
original `C:/Github/ANYsolver/.qualification` root. Run the unchanged eight
test files as `g0a-source-v3` with log output in that root evidence directory.
Keep source-import provenance separate from the globally installed 0.4.6
metadata. Neither setup incident consumed a scientific G0B trial.

Observed `g0a-source-v3`: **168 passed**, pytest exit 0, 241.90 seconds.
Imported source from the isolated worktree at the frozen commit. Complete log:
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0a-source-v3/pytest.log`,
SHA-256 `a0882e6e87756eb0e5501d19024d58c93cb5a245150c3a6bb33f35f6ebf2f725`.
Pytest emitted a post-summary atexit warning because the sandbox denied
cleanup of its default temporary symlink. All 168 cases finished; future
invocations use a fresh explicit `--basetemp` in the writable evidence root.

Installed baseline inventory is a separate smoke check, using the verified
0.4.7 wheel above and `scripts/probe_b3_ge_e4_pl_g0_baseline.py` from a
neutral working directory in an isolated `--system-site-packages` environment.
Pass the exact wheel path, SHA-256 and venv site directory; require the import
to resolve inside that site, version 0.4.7, explicit B3-GE selector, preserved
legacy B3 factory, a real one-element native owner, and public provenance.
Record stdout, exit code, and the installed dependency graph. This is an
installed *baseline smoke*, not a new acceptance of the old workflow.

Machine observation for this workstation: Windows 11 build 26200, Python
3.14.2, 32 logical CPUs, 136522502144 bytes physical memory, and
`OMP_NUM_THREADS=1` (other queried BLAS/Numba thread variables unset).
System interpreter reported installed ANYsolver 0.4.6; baseline wheel
installation in the isolated environment reported ANYsolver 0.4.7 and
resolved its import to the environment's site-packages.

Installed 0.4.7 baseline smoke `g0a-installed-v1` passed. Its immutable JSON
output is `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0a-installed-v1.json`
(SHA-256 `9ff2f6a358fe552b62195f11a67ee85e33a6fbe2349dbc352c0b59a3019a7237`).
It verifies the wheel hash, imported site-packages origin, explicit selector,
legacy B3 factory, native bounded owner, public provenance and dependency
versions. This is not installed regression qualification of a new product.

G0A external-runner smoke registration, before execution: use the upstream
CalculiX-Windows 2.23.0 zip from the official `calculix/CalculiX-Windows`
repository at `releases/CalculiX-2.23.0-win-x64.zip`, archive SHA-256
`79a674fdee735a22720bbd12bb9ccbadad1e8c8ad5b1de74e1c62f8808b2d395`,
extracted `bin/ccx.exe` SHA-256
`27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f`.
Execute exactly one existing 24x12 S4 simply supported pressure-plate case
through `scripts/probe_b3_ge_e4_pl_g0_calculix.py` with a 120-second timeout,
`OMP_NUM_THREADS=1`, cold output root `g0a-calculix-smoke-v1`; preserve deck,
solver stdout/stderr, FRD/DAT, parsed results and comparison records. Pass
requires process success, parsed results, and all three pre-existing Navier
displacement/stress and vertical-balance comparison tolerances. This is an
external-runner smoke, *not* a coupled external validation. The four required
mixed external comparisons still need separate G0/G6 case registration and
executed qualification.

The original smoke `g0a-calculix-smoke-v1` **FAILED** all three comparisons;
do not overwrite it. Its result JSON SHA-256 is
`7c7a19e9554ade8a06b5761275d20172b4ae00092f8fcf2547cd3cf8cfd1b849`;
the produced FRD SHA-256 is
`ac8a409c6f918405fb5b7f024e009db354580d53a7516846a4a562a3ab932ccd`.
The sibling ANYfileIO parser consumed adjacent positive mantissas as extra
exponent digits in CalculiX 2.23 compact three-digit-exponent records. This
produced spurious extreme stress and incorrect displacement/reaction values.
The original FRD re-parsed read-only through the corrected source passes all
three comparisons; this diagnostic does not change the original outcome.
The correction and regression are committed in isolated ANYfileIO branch
`codex/b3-coupling-calculix-parser` at
`d2dab8c4152d266d2d60dc47925cda6831492288` (44 impacted tests passed).
The sibling's full source suite subsequently passed `197/197` with one
existing duplicate-zip-member fixture warning; that is source regression,
not installed artifact qualification.
The complete captured rerun log is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/anyfileio-full-v2.log`,
SHA-256 `ea9dbe0b8071266a5c63c2026cc8cbf62d65198a24bd645c02bcd53f39409ce5`;
exit code 0, `197 passed, 1 warning` in 2.64 seconds. The earlier uncaptured
full-suite check is not used as immutable gate evidence.

Register `g0a-calculix-smoke-v2` as a new execution because the parser
dependency changed. The existing plate model, ccx archive/executable, thread
setting, timeout and three acceptance limits stay unchanged. Use the corrected
ANYfileIO source from the exact commit above and preserve a distinct cold
output root, with no substitution of v2 for the failed v1 record. Passing v2
establishes runner feasibility only, not mixed external numerical agreement.

The separate v2 execution passed all three comparisons: pressure-plate
maximum displacement relative error `0.0300147410`, surface-stress relative
error `0.0331796028`, and vertical force-balance absolute error
`0.0018402396 N`. The executable ran and the corrected parser read FRD/DAT;
`g0a-calculix-smoke-v2/result.json` has SHA-256
`ae384a78d203f8b6614fc49ed59e6c847a3f629fda5bc1e930c7fbc815aeec21`.
This closes only the G0A external-runner feasibility item. The ANYfileIO
dependency commit must be integrated and installed before final artifact gates.

## G0B preregistered feasibility questions

| ID | Bounded proof | Terminal question |
|---|---|---|
| F01 | Eccentric point pose, nonzero multiplier, rigid motion and derivative | Is work/objectivity preserved in the actual chart? |
| F02 | Beam torque into Q4/S3 shells, shear/drill/thickness sweep | Is moment transfer physical without tuned drill stiffness? |
| F03 | P0, continuous P1 and derived dual multiplier candidates; ratios 1:1 through 1:8 and reciprocals | Does any exact space pass rank, patch, work, inf-sup and mesh convergence? |
| F04 | Rigid/distributing footprint functions and deficient support | Are both objective, differentiable and physically distinct? |
| F05 | Active shell J2 from one fixed accepted predecessor | Does the algorithmic pullback agree with a branch-consistent derivative? |
| F06 | Loaded shell/beam chart rebase | Does physical state, gap and reaction remain invariant? |
| F07 | Small conservative descriptor with massless multiplier/drill DOFs | Are physical low modes and constraint residuals correct? |
| F08 | Generalized and physical-fibre native local operation seam | Can local mechanics be assembled without the bounded dense owner? |

F01 has relevant existing analytic code in `test_ge_beam3_pose_joint.py`:
its independent SciPy-rotation first variation, nonzero-multiplier spatial
derivative, chart Hessian, objectivity and wrench-balance tests passed within
the 168-test source baseline. This is an existing *pose-level oracle*; the
new shell trace/footprint ports and mixed owner have no such evidence yet.

F08 inventory: the generalized retained assembly calls each native element
operator's `evaluate(...)` and gathers a local residual/Jacobian into a dense
global array in `_ge_beam3_retained_generalized_state.Context.assemble`.
The physical-fibre retained assembly likewise calls each probe's `evaluate`
and gathers into a dense global array in
`_ge_beam3_retained_fibre_state.Context.assemble`. These local evaluations are
the extraction seam; the bounded contexts' global dense arrays, repeated
model guards and 120-second deadline are not reusable production assembly.
F08 has not yet passed a local dense/sparse parity experiment for both families.

F07 bounded descriptor case, registered before execution: physical coordinates
`(x_1,x_2)` have diagonal mass `(2,1)`; a drill-like algebraic coordinate
`z` has zero inertia. In coordinate order `(x_1,x_2,z)`, use
`K=[[3,-1,0.2],[-1,4,0.1],[0.2,0.1,2]]` and exact constraint
`c=x_1-x_2=0` with one zero-inertia multiplier. Compare the finite generalized
eigenpair of the 4x4 KKT pencil `(A,B)` (the multiplier sign convention is
`A=[[K,C.T],[C,0]]`, `B=diag(2,1,0,0)`) to independent static elimination
`x_1=x_2=a`, `z=-0.15a`: `lambda=(5-0.3**2/2)/3=1.6516666666666666`.
Pass requires exactly one finite physical mode, the other three generalized
eigenvalues infinite, relative eigenvalue error <= `1e-12`, scaled full
equation and constraint residual <= `1e-12`, and modal physical mass > 0.
Also check that a sparse KKT factorization of `(A-lambda_test*B)` at
`lambda_test=1.0` yields the same finite static response as a dense solve
within `1e-12`. This is a small design proof only, not coupled modal admission
or verification of real beam retained-variable inertia.

F07 `g0b-f07-v1` passed: one finite mode at `1.6516666666666662`, three
infinite modes, full equation residual `2.13e-16`, constraint residual
`3.33e-16`, physical modal mass `1.5` and sparse/dense shifted-solve error
`0`. Raw log `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f07-v1.log`
has SHA-256 `aa62b1ac74977c9a4747f6b4b969c0ce21f26e3bc2b505bb896ccf6f22932cd6`.
This does not close the real mixed modal design or G0B review.

F02 initial *negative-control diagnostic* registration: use one planar Q4
unit square and one planar S3-V2D unit right triangle, `E=210e9`, `nu=0.3`,
thickness `0.07`, normal `(0,0,1)`. Query each existing elastic element's
`compute_stiffness_components` at the reference state. Compare quadratic
energies for a unit normal-axis nodal rotation only at node 1 using the
reported `physical`, `numerical` and `total` matrices. Also report the same
channels for a rigid in-plane rotation field with nodal translations
`(-y,x,0)` and all nodal `rz=1`. No tuning or disabled stabilization is
allowed. This diagnoses whether a point port would mistake numerical drilling
completion for physical normal torque. The result chooses no production pose
or support policy by itself; F02 still requires a resolved footprint and
thickness/refinement/shear checks.

F02 negative control `g0b-f02-drill-v1` found **zero physical quadratic
stiffness** for a single-node normal-axis rotation in both planar elements.
Q4's numerical channel was `589649038.4615384` and S3-V2D's was
`471153846.15384614` in the fixture's units; each equals total stiffness.
Rigid in-plane motion showed only approximately `1e-6` roundoff in the energy
quadratic form. Raw log SHA-256 is
`a0240efad70398803a033dc6f4f50fee6bcc0b979674bceb36b72fbfa700d402`
at `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f02-drill-v1.log`.
This is a diagnostic **no-go for claiming physical beam-normal torque from a
single planar shell node's drill coordinate**. It is not a failure of either
standalone qualified shell element. F02 remains unresolved until a derived
resolved footprint/trace and shell thinning/refinement/shear evidence show
physical moment transfer without relying on this completion. A point pose
law may still serve admitted directional loads, but full physical torque at
an isolated point cannot be advertised from this diagnostic.

F02 physical-footprint *scalar diagnostic* registration: on `[-1,1]^2`,
assemble an `n x n` flat shell grid with `n=8,16`, unit spacing ratio and
thickness `.07`, `E=210e9`, `nu=.3`. Compare Q4 cells and S3-V2D diagonal
triangles separately. Clamp only in-plane translations on the outer boundary.
Impose on all nodes in the square footprint `|x|,|y|<=.25` the in-plane
translation field `u=(-y,x)` for one radian of rotation about its center.
Assemble only each element's reported `physical` in-plane submatrix, solve
free translations, and recover the footprint moment
`M_z=sum(-y*R_x+x*R_y)` and quadratic energy `u.T K u/2`. Require finite,
positive torque and `M_z≈2E` at each mesh/formulation, relative error
`<=1e-8`; report refinement behaviour without claiming convergence at two
levels. This demonstrates a *possible* physical torque path through membrane
strain when the connection covers an area. It does not prove a finite-rotation
footprint map, independent director shear, exact multiplier stability, or a
qualified beam/shell model. No production footprint choice follows alone.

The registered footprint diagnostic `g0b-f02-footprint-v1` passed this narrow
check. At `n=8,16`, Q4 physical membrane torque was respectively
`7.766515398e9`, `7.388116721e9`; S3-V2D torque was `9.213851274e9`,
`7.964385201e9`. Each was positive, and external torque equalled twice
strain energy to relative error <= `2.6e-16` with free equilibrium residual
<= `1.8e-15`. Raw output SHA-256
`869e4e4b18811c0f418a61e5182e2a84826ba83885f289644e0439ce9edcce55`
at `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f02-footprint-v1.log`.
The sizeable two-level S3 difference does not establish convergence or an
admissible interface. A finite region has a physical membrane torque path,
while the isolated nodal drill negative control has none; this is a design
direction, not F02 acceptance. The exact finite-rotation work functional,
independent shear, thickness/refinement, mixed-mesh and attachment tests are
still required.

F04 distributing-pose *candidate feasibility* registration: take a flat
four-node square at `(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)` and a beam
reference position at `(0,0,.2)` with identity frame. The shell-side position
is the arithmetic centroid; its frame is the proper equal-weight Procrustes
fit of the four current shell positions to the reference footprint. Use the
existing second-order fit jets and objective relative-pose law to form
`lambda_t*c_t+lambda_R*c_R`. Shell nodal rotational variables are present but
do not enter this *position-based candidate*; they remain free. Reference
constraints must vanish within `1e-12`.

At reference, apply only unit `lambda_Rz`. Require the shell footprint
force resultant <= `1e-10`, shell moment about the centroid `-1` within
`1e-10`, beam moment `+1` within `1e-10`, and zero derivative with respect
to every shell rotation. At a nonzero configuration use shell translations
`0.01*sin(i+0.3)` over the 12 translational slots, beam translation
`(.02,-.01,.03)`, beam incremental rotation `(.04,-.03,.05)`, and multipliers
`(.6,-.3,.5,-.2,.7,-.4)`. Compare jet potential and first variation with
an independently computed SciPy Procrustes/rotation-log potential by central
differences at `h=2e-6`, and its directional second variation at
`h=2e-4,1e-4` using a unit sine direction. Require relative first-variation
error <= `1e-7` and second-variation error <= `1e-5` for both steps, where
the denominator is `max(1,|reference|)`; require Hessian relative skew
<= `1e-10`. Verify constraints under common rigid motion within `1e-10`.
This only probes one distributing pose map. Rigid footprint, shell shear,
mixed Q4/S3 patches, support degeneracy, refinement and full F04 remain open.

F04 distributing-pose candidate `g0b-f04-distributing-v1` passed its bounded
checks: a unit beam-normal moment caused zero net shell force, shell
position-force moment `-1`, beam moment `+1`, and **zero direct shell rotation
gradient**. The reference gap was zero; the independent SciPy potential
first-variation relative error was `1.86e-11`; directional second-variation
errors were `1.09e-9` and `5.68e-10`; common-rigid-motion gap error was
`4.28e-16`. Raw SHA-256
`b88da33d969af1afa15abf297271781df3a1289c1f2dd798e285b40701d74601`
at `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f04-distributing-v1.log`.
This is a plausible differentiable physical moment-transfer map based on a
finite position footprint. It does not qualify its transverse-shear response,
rigid counterpart, different element topology, multi-footprint overlap or
production state/chart handling. The original single-node drill no-go remains.

Register corrected `g0b-f04-distributing-v2` in response to independent P1:
use the same reference and deformed `trial()` fixture and nonzero multipliers
as v1. Apply the common rotation `Exp(.8,-.4,.6)` and translation `(2,-3,1)`
to actual shell and beam positions; independently recompute the Procrustes
fit from the transformed shell points, while the jet evaluator independently
refits those changed input points. Re-express the transformed beam rotation
in its actual additive chart. Require material pose gaps and potential
within `1e-10`, translational force covariance within relative `1e-10`,
and full physical force/moment balance and spatial beam-moment covariance
within normalized `1e-10`, converting the beam coordinate covector using
the actual left-Exp differential. Do not replace v1 output. This resolves
only the P1 proof issue, not the full shell/line mechanics.

The versioned distributing v2 diagnostic passed: independently refitted
material gaps `5.16e-16`, potential discrepancy `1.56e-16`, translational
force covariance `3.65e-16`, spatial beam-moment covariance `1.94e-16`,
and complete physical wrench balance `1.25e-15`. Log SHA-256
`9c7fe7f4390c018abdadb004ab5fd07ec234ab5d930d628f6d1648e526d01708`
at `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f04-distributing-v2.log`.
The independent P1 proof defect is addressed for this bounded fixture; P2
scope findings remain open.

F04 rigid-footprint *candidate feasibility* registration: use the same four
square reference nodes and beam reference position `(0,0,.2)`. For each node
the exact material correspondence is
`c_i=R_b.T@(r_i-r_b)-(r_i0-r_b0)` with one 3-vector multiplier. Form
`sum(lambda_i*c_i)` with beam left-multiplicative finite rotations and
unconstrained shell director rotations. At reference choose tangential
material multipliers `lambda_i=-cross(z,r_i0)/sum(|r_j0,xy|**2)` and require
net shell force zero, shell normal moment `-1`, beam normal moment `+1`,
reference gaps <= `1e-12`, and zero direct shell-rotation gradient.
At deformed shell positions `0.01*sin(i+.3)` over 12 translation slots and
beam translation `(.02,-.01,.03)`/rotation `(.04,-.03,.05)`, use the same
nonzero multipliers, compare value/gradient/Hessian directional action to
independent SciPy matrix rotations and finite differences as in the
distributing candidate. Require first error <= `1e-7`, second errors
<= `1e-5`, Hessian skew <= `1e-10`, and objective gap under a common rigid
motion <= `1e-10`. With bounded local rotation-to-translation support matrix
`[-skew(r_i0-r_b0)]` using positions projected to the footprint plane,
require rank 3 for four corners and rank 2 for three collinear points.
This is a rigid region idealization and deliberately restricts the patch;
its distinct physical behavior from the distributing candidate needs a
coupled shell response test later.

F04 rigid candidate `g0b-f04-rigid-v1` passed the registered bounded proof:
reference gaps zero, shell moment `-1`, beam moment `+1`, net shell force and
direct shell-rotation gradient zero; first-variation relative error
`2.22e-11`, second-variation errors `8.22e-10` and `2.47e-9`, objective
gap error `8.45e-16`. Four noncollinear corners had local rotational rank
3; the collinear control had rank 2. Raw SHA-256
`0342b5c855096be07c2ec85c0254cf91bba58175950ca98dadf52001aae0853c`
at `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f04-rigid-v1.log`.
This proves neither coupled shell response nor independent full F04 acceptance;
the rigid and distributing functionals must still be compared in an actual
assembled shell model and reviewed for shear/locking/topology.

Register corrected `g0b-f04-rigid-rank-v2` in response to independent P1:
at bounded footprint points use the complete spatial rigid displacement
Jacobian with rows `[I,-skew(X_i-b_0)]`. Use the v1 square (rank six), an
offset collinear three-point line `(-.5,.2,.3),(0,.2,.3),(.5,.2,.3)` with
beam origin `(0,0,.2)` (rank five), three coincident points at
`(.2,.1,.3)` (rank three), and a curved noncollinear three-point arc
`(-.5,.25,0),(0,0,0),(.5,.25,0)` (rank six). Report the rotation-block rank
also to expose the false-positive offset-line case. Normalize translation
and rotation columns by this fixture's characteristic length `1`, use
relative singular threshold `1e-10`, and verify a unit null vector for
each deficient case has residual <= `1e-10`. No v1 log is overwritten.

The versioned rigid-rank v2 diagnostic passed: square and curved supports
had full rank six, offset collinear rank five despite rotation block rank
three, and coincident rank three. Deficient null residuals were <= `5.01e-16`.
Log SHA-256 `f6fd2c21ce9828c79790ddcd8b1cb44e3ec164275e250ab0f434fb17625af312`
at `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f04-rigid-rank-v2.log`.
Use the complete six-column Jacobian and rank-after-translation test in
future preflight, with physical scaling; the original rotation-only check
is retained solely as evidence of the defect, not as admission authority.

F04 assembled small-strain distinction, registered before execution:
reuse the F02 flat `[-1,1]^2`, `n=8,16`, Q4/S3-V2D, `.07`-thick physical
in-plane shell stiffness and outer in-plane supports. For rigid coupling,
prescribe every footprint node's translation `(-y,x)` at unit beam-normal
rotation, as in F02. For distributing coupling, keep footprint translations
free but impose just the uniform-weight mean translations `(0,0)` and
mean rotational work coordinate
`sum_i(-y_i u_xi+x_i u_yi)/sum_i(x_i**2+y_i**2)=1` by exact bounded
Lagrange multipliers. The multiplier associated with the last equation is
the generalized beam-normal moment; its work equals twice equilibrium
strain energy for unit rotation. Require both moments finite positive,
distributing moment strictly below rigid moment in each case, relative
constraint error <= `1e-10`, free equilibrium residual <= `1e-10`, and
relative work discrepancies <= `1e-10`. Report both mesh levels; two levels
do not support a convergence assertion. This is a linear scalar response
test of physical distinction, not the finite-rotation production law.

The assembled `g0b-f04-distinction-v1` diagnostic passed. Distributing
footprint torque is below rigid torque in all four Q4/S3-V2D and `n=8,16`
cases: respectively `7.5001e9 < 7.7665e9`,
`6.6407e9 < 7.3881e9`, `8.7728e9 < 9.2139e9`, and
`7.0168e9 < 7.9644e9`. Constraint, free-equilibrium and work discrepancies
were below `3.2e-15` in their registered normalized measures. Raw SHA-256
`79aa977dca11f06dc0d2fbb2e4202bdbd988b7b26a1be4c4d9765bf8b713bf1f`
at `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f04-distinction-v1.log`.
The two candidates are physically distinct in this linear membrane setting.
They remain experimental pending finite-rotation coupled shells, directors,
thinning, convergence and topology tests.

For F03 reject rank loss, high-frequency interface modes, locking, failed
patch/work checks and a norm-scaled stability measure that decays under the
registered refinement sequence. Among passing candidates use the lowest
multiplier dimension, with sparsity and measured cost as tie-breakers. If none
passes, G0B fails. The exact norm, perturbation plateau, quadrature and case
inputs must be pinned in the case manifest before F03 is run.

F03-S **preparatory scalar trace experiment**, registered before execution,
is deliberately narrower than F03 acceptance. On `s in [0,1]`, use a shell
Q4/S3 straight edge with continuous piecewise-linear position interpolation
and a native B3 reference centerline with the existing three-node quadratic
Lagrange interpolation (`p2_shape_functions` on `[-1,1]`). Offset the beam
reference axis by `.2` in normal direction and subtract that fixed offset,
so the scalar translational reference gap is zero. Use shell/beam element
counts `(N,Nr)` and `(Nr,N)` for `N=4,8,16`, `r=1,2,4,8`, deduplicating
the `r=1` case; all knots at uniform fractions. Split integration at the
union of both meshes' boundaries. Four-point Gauss-Legendre integrates the
polynomial work exactly in each split segment.

Compare five multiplier candidates: discontinuous P0 on the union
segmentation; continuous P1 on shell knots, beam knots, and union knots;
and an elementwise biorthogonal dual assembled on union knots with local
functions `(2N_left-N_right, 2N_right-N_left)`. Calculate
`B_ij=int(mu_i*(N_b,-N_s)_j) ds`, trace Gram
`H=diag(int N_b.T N_b,int N_s.T N_s)`, multiplier Gram
`M_mu=int mu.T mu`, and physical difference Gram
`G=int (N_b,-N_s).T(N_b,-N_s)`. Report ranks using relative singular
threshold `1e-10`, the nonzero singular-value floor of
`M_mu^-1/2 B H^-1/2`, and unresolved difference dimensions
`rank(G)-rank(B)`. Require reference, common constant and common affine
patch weak gaps <= `1e-12`; record candidates with row-rank loss and
unresolved modes. These are dimensionless scalar L2 norms on a unit line.
There is no production acceptance threshold for this preparatory test: the
full vector/rotation trace, actual beam/shell stiffness, exact multiplier
stability, locking, shear and refinement response still determine F03.

F03-S execution `g0b-f03-scalar-v1` produced 105 candidate rows over 21
mesh pairs, all with patch errors <= `8.97e-17` and no multiplier row-rank
loss. Every weak candidate left physical scalar difference modes unresolved;
their mechanical admissibility cannot be inferred from row rank alone.
For union-grid P0 with shell eight times finer than beam, the norm-scaled
nonzero singular floor fell `0.0849 -> 0.0425 -> 0.0213` over `N=4,8,16`.
This refinement decay is a concrete warning against that candidate in this
direction. P1 candidates had nonzero floors >= approximately `1` in the
tested scalar norm, but also unresolved modes; their vector/rotation and
coupled-stiffness behavior is untested. Complete raw JSON SHA-256
`7a1a58cd33bc6998ea16fb0bb2c24d06e647996ced1c31e1900fc2168af32a85`
at `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f03-scalar-v1.json`;
summary log SHA-256
`ac8c23b903b01f3c61c773061dd7fd3f1326504e516301a0af07ac8edf9bd73b`.
F03 remains unresolved and no multiplier space is selected.

F05 initial **diagnostic** case, pinned before its first execution: an S3-V2D
triangle at `(0,0,0)`, `(1.2,0.05,0)`, `(0.2,0.95,0)`, thickness `0.018`,
`E=210e9`, `nu=0.3`, five layers and the existing DNV C208 curve with
`sigma_prop=80e6`, `sigma_yield=85e6`, `sigma_yield_2=100e6`,
`eps_p_y1=0.002`, `eps_p_y2=0.02`, `K=280e6`, `n=0.18`. Issue one committed
local predecessor from the virgin state at local DOFs 6=`0.008` and
12=`-0.002`. The global candidate starts at that vector, then adds
`0.0002` to DOF 6 and `-0.00005` to DOF 12, with node rotation vectors
`(0.003,-0.002,0.001)`, `(-0.001,0.002,-0.003)` and
`(0.001,0.001,0.002)`. Compare the coordinate pullback formula against a
central directional force difference at `h=2e-6,2e-7,2e-8` using a fixed
unit-length sine direction. Require active plasticity, unchanged predecessor,
finite force/tangent and relative derivative error <= `1e-5` at two adjacent
steps. Report skew without imposing elastic Hessian symmetry. This exercise
does not qualify a global owner or disable the elastic-only adapter guard.

F05 diagnostic execution `g0b-f05-v1` returned active plasticity, finite
responses, unchanged accepted predecessor, and directional relative errors
`[1.0818220921447311e-7, 1.371788594087779e-8, 1.5783090551463997e-7]`.
Its raw output is `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f05-v1.log`
(SHA-256 `2a00a06240af1b1ffa1b1e4119a832bb171228cbebeac208506379e6005d78c`).
The adjacent-step criterion passed for this one S3 local fixture; Q4,
attachment work, global assembly, independent review and G0B closure remain
unproven. This is diagnostic feasibility, not production acceptance.

The basic numerical defaults from the complete programme are relative
`1e-10` old/new small-case parity, `1e-9` normalized rigid-motion and weak
constraint residuals, `1e-8` resultant/work and eigen residuals, `1e-6`
elastic and `1e-5` smooth-plastic tangent errors. Case-specific absolute
floors and normalizations must be frozen before each candidate comparison.

## Programme gate ledger and case inventory

| Gate | Current status | Closure evidence |
|---|---|---|
| G0A/G0B | IN_PROGRESS | Baseline, executable F01–F08, frozen contracts, independent mechanics review. |
| G1 | NOT_STARTED | Sparse multi-element elastic point owner with atomic lifecycle. |
| G2 | NOT_STARTED | Nonmatching lines, footprints, seams, topology and native round-trip. |
| G3 | NOT_STARTED | Required coupled material combinations, chart/restart equivalence. |
| G4A–D | NOT_STARTED | Loads/supports; constrained modes/buckling; imperfections; continuation. |
| G5 | NOT_STARTED | Large sparse and active-plastic workloads, scaling and resource evidence. |
| G6A–D | NOT_STARTED | Installed artifact, consumer, external references, independent acceptance, authorized release. |

The required V01–V28 inventory is exactly the verification matrix in the
approved complete programme: one-shell parity; dense/sparse parity; objectivity;
work; tangents; patches; drill/shear; mesh ratios; mixed Q4/S3; curvature;
junctions; footprints; seams; supports; materials; histories; rejection;
charts; loads; modes; buckling; imperfections/capacity; renumbering; scale;
installed consumer; multiplier stability; owner lifetime; and ownership and
snapshot corruption. Every eventual advertised capability cell needs direct
evidence. This ledger is not a claim that any V case has passed.

## Evidence and review rules

Keep raw baseline/G0B output in versioned, non-overwriting evidence locations;
record hashes, exact commands, dependencies and environment. Independent
mechanics review must resolve port work, shell drill/shear, exact multiplier
stability, plastic tangent, and massless-variable handling before G0B closes.
No product code is edited before this initial registration. Product work
cannot begin until the G0 mechanical choices and case contracts are frozen.

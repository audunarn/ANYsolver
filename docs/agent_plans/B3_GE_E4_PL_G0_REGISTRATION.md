# B3-GE / E4-PL multi-element coupling: G0 registration

Status: **G0 IN PROGRESS; no new mixed capability qualified.**

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

For F03 reject rank loss, high-frequency interface modes, locking, failed
patch/work checks and a norm-scaled stability measure that decays under the
registered refinement sequence. Among passing candidates use the lowest
multiplier dimension, with sparsity and measured cost as tie-breakers. If none
passes, G0B fails. The exact norm, perturbation plateau, quadrature and case
inputs must be pinned in the case manifest before F03 is run.

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

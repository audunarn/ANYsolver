# Nonlinear solver performance layer

The package has an optional performance layer for nonlinear solves. Activation
is lazy on the first `solve_static_nonlinear()` call, so ordinary imports and
linear workflows do not pay the PyPardiso/nonlinear-bootstrap startup cost. The
optimized paths preserve the scalar element formulations, discrete
constitutive update, and convergence criteria.

## Implemented

### Linear-time model construction and coupling lookup

Topology and MPC revision updates invalidate global sparsity/signature caches
without scanning every existing element or deleting unaffected element-local
reference matrices. Adding a genuinely new node advances the model-wide
geometry revision without clearing elements that cannot reference that node.
An incoming element has only its own mesh/material-dependent caches cleared,
which also makes precomputed element insertion safe. These rules remove the
former quadratic construction behavior from both element-at-a-time and
interleaved node/element construction.

Structured panel coupling now builds the shell-cell lookup once per coupling
generation and reuses it for every beam node. The lookup maps actual grid cells
to element IDs and does not rely on element-number sequencing. This removes a
second repeated full-grid reconstruction from stiffened-panel generation.

The 2026-07-23 diagnostic sweep measured the topology construction portion of
representative cylinder models as follows on the audit workstation:

| Elements | Before | After | Speedup |
| ---: | ---: | ---: | ---: |
| 2,792 | 1.627 s | 0.051 s | 32x |
| 11,038 | 25.877 s | 0.239 s | 108x |

These timings are diagnostic observations, not release gates; benchmark
comparisons must use the same machine, environment, and model.

### Batched S4 geometric stiffness

Linear buckling assembly batches the S4 initial-stress operator in a compiled
kernel. Membrane resultants, bending resultants, stress second moments and
per-Gauss local transformations retain the scalar element conventions.
Reference derivatives, integration weights and frames are cached by topology
and geometry revision; state sampling remains per assembly. Distorted, rotated
and warped S4 qualification compares the assembled matrix with the scalar
element oracle. Triangles, Q8, beams and unsupported element formulations stay
on the general scalar path, and assembly diagnostics expose both counts and
geometry/kernel timings.

### Persistent nonlinear assembly plan

A `NonlinearAssemblyPlan` is built once for each `(model, num_layers)` pair and
is invalidated when topology, geometry, material or MPC revisions change. It
retains:

- shell grouping by element type, thickness, stabilization and material;
- stacked reference transforms and shell B matrices;
- stacked transforms and strain rows for eligible elastic Beam3 elements;
- element DOF mappings;
- reusable displacement and material-state work arrays;
- flat local force/tangent storage;
- the unique global CSR tangent pattern;
- local-entry-to-CSR scatter indices.

Each Newton iteration therefore updates only displacements, constitutive state,
internal force values and tangent values.

### Direct CSR value assembly

The global tangent sparsity pattern is created once. Local dense tangent values
are accumulated directly into the unique CSR data index space with a
Numba-compiled scatter loop. Repeated Python lists, COO construction, duplicate
sorting and COO-to-CSR conversion are removed from the Newton loop.

### Revision-based sparsity caching

The general matrix-assembly sparsity cache uses mesh topology/MPC revision
counters. A deterministic full-topology SHA signature is still retained for
collision-resistant cache identity, but it is computed once per matrix type and
topology/MPC revision instead of serializing and hashing every element on every
lookup. Assembly timing includes final sparse conversion, checks, and signature
work rather than stopping before post-assembly processing.

### Displacement-control block elimination

The augmented `(n+1) x (n+1)` sparse matrix has been replaced with two right-hand
sides on the ordinary structural tangent:

```text
K a = R
K b = Fref

dlambda = (constraint - c^T a) / (c^T b)
dq      = a + b dlambda
```

The two right-hand sides share one numerical factorization.

### Batch B: elastic shell fast path

When Numba is active, geometrically nonlinear elastic shell batches use a
dedicated in-place kernel that writes directly into the persistent force and
tangent buffers. It removes per-Newton plastic/layer state arrays, constitutive
batch tensors and temporary batch result matrices. The local-to-global shell
transformation is applied in place by 3x3 node-DOF blocks.

When Numba is unavailable, Batch B is not installed; the existing NumPy batch
path remains active to avoid a slow Python-loop fallback.

The general elastic batch records actual layer strains during assembly. The
direct Batch B kernel omits those displacement-derived arrays inside Newton
iterations, then reconstructs the real layer strains once at the final
converged displacement. Returned element states, stress envelopes, and strain
summaries therefore retain the same recovery contract without paying that cost
per iteration. Plastic batches call the same plane-stress return map and its
analytical consistent tangent as scalar assembly. The central-difference
tangent remains an explicit qualification oracle and guarded invalid-row
fallback. A condition number alone does not discard a finite exact analytical
row, and the oracle uses representable, stiffness-scaled perturbations.
Shells carrying initial stress or prestrain fields no longer disable batching
for the whole model. For elastic S4 batches, immutable stress and prestrain are
integrated into exact membrane and bending resultant offsets inside the JIT
kernel; complete layer/provenance state is reconstructed once at convergence.
Initialized plastic shells retain exact scalar element evaluation, while
ordinary shells in the same model remain accelerated. Diagnostics separate
accelerated initialized elements from scalar overrides. A 96-S4 case with
fields on every element measured 2.03 ms accelerated versus 21.82 ms scalar
after warm-up (10.7x). Reduced-integration Q8R is deliberately ineligible for
shell batching because its experimental hourglass stiffness is not represented
by the accelerated local kernel.

### Elastic Beam3 batch

Straight elastic `QuadraticBeamElement` members use a dedicated compiled batch
for von Karman internal force and consistent tangent assembly. Reference
transforms, Gauss-point strain rows and scatter positions are retained in the
nonlinear plan. Generalized sections, fiber plasticity, deleted elements and
corotational analyses retain their qualified scalar behavior. On the audit
workstation, 72 rotated Beam3 elements measured 0.164 ms batched versus
17.43 ms scalar after warm-up (106x); force and tangent qualification uses the
scalar element implementation as the oracle.

### Batch C: direct reduced-coordinate assembly

When constraints reduce the system, element-local values are now scattered
directly into the independent coordinates:

```text
F_int,r = T^T F_int
K_r     = T^T K T
```

The reduced CSR pattern, local-entry scatter maps, force buffer, tangent data
buffer and sparse matrix object are retained for the complete nonlinear solve.
The repeated sparse products `T.T @ K @ T` and `T.T @ F_int` are therefore
removed from force control, displacement control and arc-length correction.

Two setup paths are used:

- `selector` for ordinary fixed supports and unit-coefficient slave mappings;
- `weighted_mpc` for eccentric beam-shell coupling and general MPC coefficients.

The weighted map is expanded once. Set `FE_SOLVER_BATCH_C_MAX_MAP_MB` before
Python starts to change its retained-map memory limit, which defaults to 512 MiB.
If the estimated map exceeds the limit, the solver automatically retains the
full-coordinate assembly and projection path.

Direct reduction also has a solve-cost gate. The representative weighted-MPC
model broke even after about 72 tangent evaluations, so the default threshold
is 144 estimated useful assemblies (a 2x safety margin). The estimate uses up
to four useful Newton evaluations per requested increment instead of the full
failure limit. Short solves keep full-coordinate persistent assembly and avoid
the reduced-plan setup. Set
`FE_SOLVER_BATCH_C_MIN_ESTIMATED_ASSEMBLIES` to override the threshold; status
diagnostics record the estimate, threshold, decision and skip count.

Batch C is installed only when Numba is active. Python/NumPy fallback runs keep
the existing sparse projection path.

#### Nonlinear impact extension

The nonlinear rigid-sphere impact loop can use the same retained reduced
scatter plan for its internal force and tangent. Activation is deliberately
narrower than static Batch C: it requires Numba, von Karman kinematics, a
non-identity transformation, an exactly zero affine offset, no plastic-impact
damage/softening/deletion configuration, a plan below the retained-map memory
limit, and an estimated assembly count above the Batch C cost gate. Every
exclusion keeps the full-coordinate impact oracle and is reported through
`impact_reduced_assembly.fallback_reason` and `exclusion_reasons`.

For eligible HHT-alpha runs, the accepted internal-force history is retained
in reduced coordinates. Because eligibility requires `u0 == 0`, both the HHT
residual and the nonlinear internal-work measure remain algebraically exact:
`u.T @ F_int == q.T @ (T.T @ F_int)`. Public displacement, contact and element
state histories are still materialized through the existing impact result
path. Diagnostics expose direct-reduced and full-coordinate assembly counts,
the selector/weighted-MPC mapping kind, setup memory and timing.

The semantic merge seam is intentionally limited to
`_solve_transient_sphere_impact_nonlinear()` in `contact.py`; eligibility and
plan ownership live in `impact_reduced_assembly.py`. Incoming contact, damage
or ANYfem-facing state changes should remain on the full-coordinate fallback
until their force/tangent and committed-state semantics have explicit direct
reduction qualification.

### Batch D: multicore and sparse backend tuning

When Numba is active, the Batch B elastic shell kernel now uses `prange` over
the element dimension.  `solve_static_nonlinear(...,
resource_config=ResourceConfig(assembly_threads=N))` temporarily sets the Numba
thread count for nonlinear assembly and restores the previous count after the
solve.

`ResourceConfig.solver_threads` is also enforced for every public solver entry
point through a scoped `threadpoolctl` limit. Factorization and reusable-handle
solve diagnostics retain requested and observed pool data. When
`assembly_threads > 1` activates parallel Numba assembly, native BLAS/OpenMP
pools are nested at one thread and both Numba and native limits are restored on
normal return or exception. A missing limiter is reported explicitly; an
omitted resource policy leaves backend defaults unchanged.

The separate `experimental_csr_assembly` module is benchmark-only. It caches a
CSR topology and local-entry scatter map, but the qualified linear K/M/KG path
continues to use COO. Promotion requires at least 20% complete assembly gain,
plus at least 5% end-to-end gain or 15% peak-memory reduction, matrix error no
greater than `1e-12`, and no representative case regression above 5%.

The sparse backend policy is tuneable through:

```text
FE_SOLVER_PYPARDISO_MIN_DIMENSION
FE_SOLVER_PYPARDISO_MIN_NNZ
FE_SOLVER_PYPARDISO_WARM_MIN_DIMENSION
FE_SOLVER_PYPARDISO_WARM_MIN_NNZ
FE_SOLVER_PYPARDISO_MAX_PATTERN_SLOTS
```

The cold defaults (`10,000` equations and `250,000` nonzeros) avoid paying MKL
startup cost on small one-off solves. Lower warm defaults (`1,000` and
`25,000`) apply only when a retained PARDISO slot has the same prepared
sparsity pattern and a matrix type compatible with the incoming matrix class.
Merely having initialized PyPardiso for an unrelated matrix does not activate
the warm policy. Both thresholds must be met.

The auto backend records the active thresholds, prior initialization state,
compatible-pattern decision, retained-slot count, and selected backend in
solver diagnostics. The PyPardiso module and solver object are constructed only
after the policy selects that backend. The PARDISO backend checks standard MKL
library directories without a recursive environment scan, resolves `mkl_rt`
once per process (`PYPARDISO_MKL_RT`), factorizes symmetric matrix classes as
upper triangles with symmetric mtypes (2 / -2, general fallback on failure),
reuses symbolic analysis (phase 22) when the sparsity pattern is unchanged
through a small LRU of pattern slots, and releases MKL internal memory when
slots are evicted or handles are garbage collected. Handle diagnostics report
`pardiso_mtype` and `pardiso_symbolic_reused`.

Linear static reduced stiffness matrices are declared symmetric indefinite
rather than general, allowing a selected symmetric backend to use its native
matrix class while retaining SuperLU fallback.

## Activation and A/B testing

Importing `anysolver` does not install the nonlinear performance layer.
`solve_static_nonlinear()` performs a one-time lazy activation immediately
before a nonlinear solve. Existing public solver calls are unchanged, and an
optional acceleration import/initialization failure leaves the scalar path
available.

Set the environment variable below before the first nonlinear solve to retain
the scalar/legacy assembly path:

```text
FE_SOLVER_DISABLE_FAST_NL=1
```

Runtime diagnostics are available from:

```python
from anysolver.jit_compiler import jit_diagnostics
from anysolver.nonlinear_performance_bootstrap import nonlinear_performance_status

print(jit_diagnostics())
print(nonlinear_performance_status())
```

Before the first nonlinear solve, the status reports that activation has not
yet been attempted. Calling the status helper directly does not activate the
layer.

The plan can be cleared explicitly after non-standard in-place model changes:

```python
from anysolver.nonlinear_performance_bootstrap import clear_nonlinear_assembly_cache

clear_nonlinear_assembly_cache(model)
```

Ordinary model methods update revision counters and invalidate the plan
automatically.

## Validation requirements

After changing the nonlinear formulation, constraint mapping, JIT kernels, or
sparse backend, run:

```powershell
python -m pytest tests -q
python scripts/benchmark_nonlinear_assembly.py --nx 20 --ny 10 --repeats 10
python scripts/benchmark_nonlinear_assembly.py --nx 20 --ny 10 --repeats 10 --weighted-mpc-rows 12
```

The dedicated tests compare optimized and legacy internal-force/tangent assembly,
including tilted shells, selector constraints and weighted MPC transformations.
They also verify cache invalidation, residual-only assembly, CSR uniqueness,
persistent buffer reuse, analytical/numerical plastic-tangent parity, elastic
layer state, mixed initial-field exact overrides, Beam3 scalar-oracle parity,
Q8R scalar fallback, lazy
nonlinear-solver activation, and legacy restoration. Qualification records
warmed constitutive and representative global Newton timings for the
analytical and numerical tangent paths; timing is evidence rather than a
wall-clock pass gate.

## Deferred until measured

The following changes remain deferred until profiling identifies the
next dominant phase:

- upper-triangle-only element tangent integration;
- retained arc-length predictor factorization;
- automatic Numba thread selection (high logical-core counts can oversubscribe
  memory bandwidth, so `assembly_threads` remains an explicit measured choice);
- Q8R batch acceleration, pending a qualified stabilization formulation.

Symbolic sparse-factorization reuse (PARDISO phase 22 with pattern slots) is
implemented in the PyPardiso backend. Historical Batch B/C/D notes were folded
into this guide; this file is the maintained performance documentation.

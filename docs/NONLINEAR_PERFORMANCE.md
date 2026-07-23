# Nonlinear solver performance layer

The package installs an automatic performance layer during ordinary Python
runs. The finite-element formulations and convergence criteria are unchanged.

## Implemented

### Persistent nonlinear assembly plan

A `NonlinearAssemblyPlan` is built once for each `(model, num_layers)` pair and
is invalidated when topology, geometry, material or MPC revisions change. It
retains:

- shell grouping by element type, thickness, stabilization and material;
- stacked reference transforms and shell B matrices;
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
counters. It no longer rebuilds and SHA-hashes a JSON description of every
element on each lookup.

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

Batch C is installed only when Numba is active. Python/NumPy fallback runs keep
the existing sparse projection path.

### Batch D: multicore and sparse backend tuning

When Numba is active, the Batch B elastic shell kernel now uses `prange` over
the element dimension.  `solve_static_nonlinear(...,
resource_config=ResourceConfig(assembly_threads=N))` temporarily sets the Numba
thread count for nonlinear assembly and restores the previous count after the
solve.

The sparse backend policy is tuneable through:

```text
FE_SOLVER_PYPARDISO_MIN_DIMENSION
FE_SOLVER_PYPARDISO_MIN_NNZ
FE_SOLVER_PYPARDISO_MAX_PATTERN_SLOTS
```

The auto backend records the active thresholds and selected backend in solver
diagnostics.  The PARDISO backend resolves the mkl_rt library path once per
process (`PYPARDISO_MKL_RT`), factorizes symmetric matrix classes as upper
triangles with symmetric mtypes (2 / -2, general fallback on failure), reuses
the symbolic analysis (phase 22) when the sparsity pattern is unchanged through
a small LRU of pattern slots, and releases MKL internal memory when slots are
evicted or handles are garbage collected.  Handle diagnostics report
`pardiso_mtype` and `pardiso_symbolic_reused`.

## Activation and A/B testing

The performance layer is activated automatically during normal `anysolver`
package import. Existing public solver calls are unchanged.

Set the environment variable below before Python starts to retain the legacy
assembly path:

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
persistent buffer reuse, nonlinear-solver activation and legacy restoration.

## Deferred until measured

The following changes remain deferred until profiling identifies the
next dominant phase:

- upper-triangle-only element tangent integration;
- retained arc-length predictor factorization.

Symbolic sparse-factorization reuse (PARDISO phase 22 with pattern slots) is
implemented in the PyPardiso backend. Historical Batch B/C/D notes were folded
into this guide; this file is the maintained performance documentation.

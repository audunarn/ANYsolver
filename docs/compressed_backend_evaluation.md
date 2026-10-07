# Optional compressed factorization: bounded evaluation

Date: 2026-10-07. Evaluated against delivered static-batch code `fa13f0d3`
and ANYfem `3e4eb7f`, after their publication. No compressed backend has been
implemented, installed, qualified or selected by default.

## Decision

**BLOCKED at native availability.** The specified Windows CPython 3.13.9
environment has pypardiso 0.4.7, but no `strumpack`, `mumps`, `pymumps`,
`petsc4py` or `torch_strumpack` binding. No STRUMPACK/MUMPS/ButterflyPACK library
candidate was found in the inspected PATH, interpreter Scripts/Library/bin and
site-packages locations. These are targeted checks, not a whole-machine inventory.

Visual Studio 18 BuildTools provides MSVC 14.50 and bundled CMake, although
neither is on the active PATH. No Fortran compiler was found on PATH or in the
checked MSYS, Visual Studio LLVM and Intel oneAPI locations. The first sandboxed
probe encountered read restrictions; a bounded read-only elevated probe completed
with no inspection errors. No build, dependency download, shared-environment
change or compressed numerical solve was attempted.

STRUMPACK's documented native build requires C/C++ and Fortran, BLAS/LAPACK and
METIS. A separate PyTorch binding exists, but its inspected installation examples
use native release wheels and introduce an additional runtime/ABI dependency.
Neither that binding nor PyTorch is installed here. This evaluation does not
claim that a Windows build is impossible or that no suitable binary exists.
It establishes that a usable native provider was not available for this bounded
experiment. [STRUMPACK requirements](https://portal.nersc.gov/project/sparse/strumpack/master/installation.html),
[binding project](https://github.com/sparsexlab/torch-strumpack).

**NO_GO for pursuing the 2x speed target through factor compression on the
measured barge workload alone.** Its 20-case candidate pilot spent 84.9546682 s
overall, 9.4679340 s in all operator preparation and 0.2141113 s in solves.
Even eliminating both entire phases gives an optimistic upper bound of
`84.9546682 / (84.9546682 - 9.4679340 - 0.2141113) = 1.1286264x`.
Preparation includes more than factorization, making this bound deliberately
generous. It is a workload-prioritization conclusion, not a measured BLR speedup
or a rejection of compression on other models. Memory payoff is **unmeasured**.
See [the complete static-batch evidence](static_batch_performance.md).

Repeated static RHS compression qualification and supported buckling inverse
qualification are **not executed**. HODLR is **deferred**. Free-free buckling's
dense quotient remains an independent scalability issue. Existing PARDISO and
SuperLU behavior, sparse operators, load assembly and formulations are unchanged.

## Architecture requirements retained for a future candidate

BLR should compress factorization fronts, not assembled model operators, loads
or time histories. It normally introduces an approximate factorization used
inside an iterative solve, so the compression tolerance is not an accuracy
certificate. [STRUMPACK BLR documentation](https://portal.nersc.gov/project/sparse/strumpack/master/BLR_Preconditioning.html).

Use the existing `FactorizationHandle`, `FactorizationCache` and `AnalysisSession`
interfaces. No second cache service or high-level static API is required. A future
optional provider must have immutable configuration, backend/configuration-aware
reuse identity, explicit matrix-class and analysis-use eligibility, bounded
multiple-RHS workspaces and deterministic native-handle cleanup. Changing a
backend on a live cache must not reuse another backend's handle.

An independent Mistral Read review inspected the actual cache, session, static
certificate and buckling call sites. Root adjudication retains these findings:

- Cache keys currently contain matrix/class/options/shape, not backend identity.
  This is not a demonstrated defect in the current fixed-backend paths. A future
  compressed provider must prevent mixed-backend/configuration handle reuse.
- A backend selected on a session cache applies to every consumer of that cache.
  Static opt-in must not silently admit compressed buckling or shifted indefinite
  inverses. Enforce per-use eligibility within the existing architecture.
- Static batches certify the original reduced/augmented equation with the
  existing `1e-10` backward-error limit. Preserve that certificate and independent
  physical-output comparisons: a small backward error alone does not establish
  small forward error for ill-conditioned systems.
- Supported unshifted buckling calls symmetric `eigsh` with `M=K` and an explicit
  `Minv`. A residual-stopped inner GMRES solve is not automatically a fixed,
  linear, self-adjoint positive inverse action. A fixed stopping tolerance or
  acceptable final eigenpair residual alone does not prove that operator contract.
  Require a justified compatible action and original-pencil acceptance, otherwise
  retain the exact route. [SciPy inverse contract](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.eigsh.html).
- The existing cache does not promise concurrent solve serialization. Preserve
  the serial session/resource contract; do not infer thread safety from cache
  locks. Shift-dependent cache churn is outside the initial unshifted scope.

The review's broad claims that stale numerics are impossible and that fixed-tolerance
refinement or an eigenpair gate alone suffices are not adopted. No new numerical
tolerance, physical assumption, eigensolver or qualification claim follows from
the review.

## Budget, evidence and future promotion

The approved follow-on ceiling was 600 seconds of automated execution, with
120 seconds for native setup, 300 for static checks, 120 for eligible buckling
and 60 reserved for final verification. It stopped at the prerequisite instead
of consuming the unused numerical allocation. Bounded harness records are:

| Attempt | Result | Process wall seconds |
| --- | --- | ---: |
| Native probe 1 | completed; sandbox read limitations retained | 0.9105195 |
| Native probe 2 | completed; no read errors | 0.8519032 |
| Visual Studio/binding follow-up | completed | 0.0569138 |
| Independent contract review | completed, 8-turn bound | 49.3009385 |

These account for **51.1202750 seconds** of bounded subprocess work. Supplementary
source, web-documentation and tool-location reads are not numerical measurements;
their shell/tool wall durations are retained in the chat evidence. The 600-second
execution ceiling was not approached. No static or buckling numerical allocation
was consumed, and no extra execution authority is created by stopping early.

Exact commands, source hashes, stdout/stderr, the initial restricted probe,
successful probe JSON and independent review are retained under
`C:/ANYworkspaceWork/static-batch-20261007/`: `checks/blr-*`,
`blr-native-feasibility.json`, `blr-toolchain-followup.json` and
`blr-contract-review.md`. Probe scripts are `blr_probe.py` and
`blr_toolchain_followup.py`, using `C:/Github/ANYsolver/.venv/Scripts/python.exe`.
Their read-only checks can be rerun after a specifically provisioned native
provider becomes available; current source-independent environment conclusions
must not be treated as permanent platform facts.

Any later candidate must first pass repeated static RHS correctness/reuse, then
supported unshifted elastic buckling if eligible. Keep the adopted promotion
threshold: at least **2x complete-workload speed**, or **50% lower process peak
memory with no more than 5% slowdown**, at unchanged scientific accuracy. Require
short alternating comparisons and a distinct holdout, including conversion,
ordering, refinement, certification, recovery and output costs. Report GO,
NO_GO, BLOCKED or INCONCLUSIVE per workload and matrix class; never count an
exact fallback as compressed success.

HODLR requires a separate bounded proposal supported by BLR front/rank evidence;
its additional ButterflyPACK dependency is not introduced in this evaluation.

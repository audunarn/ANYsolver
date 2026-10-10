# M11 — unseen canonical-solver uncertainty

2026-10-09. Implemented and independently checked a **conditional diagnostic**
bound that does not take a direct solution or its residual as input. Disposition:
**NO_GO for using the generic backward-error gate to skip canonical envelope
cases**. This is not a failure of the response-reconstruction architecture or a
measurement of the actual backend's error. Product execution remains unchanged.

## Decision and evidence

The native `assembly._backward_error` accepts a rounded residual ratio at most
`1e-10`. Even for A=I and b=1, represented q=1+1.5e-10 passes that predicate
(7.500000619990283e-11) while its 1.5000001241105565e-10 error exceeds the
1e-12+1e-12|1| diagnostic output criterion. The unseen enclosure includes that
adversarial q. Thus acceptance alone cannot give the stronger output guarantee.
This is a logical counterexample, not evidence that the production solver returns
the adversarial value.

| Fixture | Unseen result | Direct oracle evaluated afterward |
| --- | --- | --- |
| Supported S3, 12 coordinates | Conditional radius 1.8196079876127868e-5; contraction 0.001511685484766003 | Max coordinate difference 2.710505431213761e-20 |
| Augmented free-free, 54 coordinates | `INCONCLUSIVE_GATE_CONTRACTION`; contraction 13568756587622.697 | Max augmented-coordinate difference 3.570662873376075e-11 |

The second oracle difference is not a physical-displacement tolerance assessment.
The pessimistic free-free comparison bound does not establish formulation failure.
No direct oracle values enter either bound. No output intervals or envelope
exclusion are supplied by this milestone.

## Proof review

Let X be the unknown accepted solution's infinity norm. Conditional rounded CSR
arithmetic and the actual represented checker row norm give
`||Aq-b|| <= alpha*X+zeta`. `alpha` and `zeta` include dot/subtraction, row-sum,
scalar denominator and division rounding, plus additive subnormal allowances.
The actual represented row norm is checked against an exact rational enclosure;
it must remain bound to the same snapshot and reduction authority.

M10's exact represented-factor defect action provides beta >= ||A^-1||inf without
forming an inverse matrix. If beta*alpha<1,

    X <= beta*(||b||+zeta)/(1-beta*alpha)
    ||q-q_reconstructed|| <= beta*(||b-A*q_reconstructed||+alpha*X+zeta).

Root independently reviewed these inequalities and tested closed-form 2x2
solutions, row permutations, signed loads, accepted adversaries generated only
after forming the enclosure, constrained full-load reactions and refusal branches.
The worker's cancellation control shows a true residual hidden by a rounded CSR
dot; the additive subnormal terms remain present. Zero RHS is explicitly outside
this diagnostic's positive-denominator proof domain. Noncanonical CSR, nonfinite
inputs, unsupported precision, overflow and failed contraction do not certify.

Arithmetic assumptions remain conditional: binary64 round-to-nearest, gradual
underflow, finite intermediates and the stated operation-count envelope. These
tests do not qualify arbitrary native implementations, scalar/eigensolver recovery,
load evaluation, prescribed offsets or full-load construction. Reduced loads alone
cannot certify reactions: constrained load changes can leave the reduced RHS
unchanged. Existing tolerances, counterexamples and direct fallback remain intact.

## Backend feasibility inspection

Installed system-site SciPy metadata reports **1.16.3**, git revision
`b9105ccc2237f57acb1060202cd77f6dd264fb34`. Repository SuperLU preparation calls
`splu(csc, permc_spec=ordering)`; its resident solve uses `SuperLU.solve`.
The matching [SciPy 1.16.3 wrapper source](https://github.com/scipy/scipy/blob/v1.16.3/scipy/sparse/linalg/_dsolve/_superluobject.c)
copies RHS and invokes `gstrs` using resident L/U and row/column permutations.
Its [double-precision solve source](https://github.com/scipy/scipy/blob/v1.16.3/scipy/sparse/linalg/_dsolve/SuperLU/SRC/dgstrs.c)
contains supernode triangular solves and updates, with vendor-BLAS and internal
kernel branches. This identifies the next proof boundary; source inspection does
not verify the installed binary's compile choices or floating-point environment.

SuperLU exposes factors and permutations, making a resident-factor diagnostic
possible. Copy mutable factor/permutation containers before using them as evidence;
do not expose writable aliases. Include the supported route's RHS scaling and
solution unscaling, and free-free augmented coordinates/gauge. A factor-defect
bound alone is not a bound on a floating-point triangular solve's returned result.

The current PARDISO wrapper invokes phase 33 and exposes no numeric factor export.
[Intel's `pardiso_export` documentation](https://www.intel.com/content/www/us/en/docs/onemkl/developer-reference-c/2026-0/pardiso-export.html)
limits that routine to sparse Schur-complement export. It cannot be treated as
general L/U export. Refinement settings alone are not a proved solve-error bound.
No backend is switched or added, and no claim covers all PARDISO interfaces.

The next coherent experiment is a backend-specific, componentwise enclosure of
the **actual resident SuperLU solve**, verified against small supported and
augmented fixtures, then propagated through M10 staged outputs. Establish native
arithmetic/runtime authority and bound usefulness before any performance run.
PARDISO requires separate justified solve-error evidence; unsupported backends
retain canonical execution. Do not continue refining the generic gate as if it
could overcome the identity counterexample.

## Actual checks and resources

All checks used `C:/Github/ANYsolver/.venv/Scripts/python.exe`, task runner,
`NUMBA_DISABLE_JIT=0`, one OMP/BLAS/Numba thread, disabled pytest plugin autoload
and isolated solver source/tests imports. Five unique M11 pytest tests passed
independently; three unique author tests passed (run twice after a narrow admission
edit). Two supported/free-free diagnostics completed before and after independent
review. No failures or skips; no benchmark or performance claim.

| Evidence directory under `../evidence/checks/` | Process-wall seconds | Result |
| --- | ---: | --- |
| m11-solver-01 | 4.486165199999959 | Controls and two fixture diagnostics passed |
| m11-solver-02 | 2.9380462999999963 | 3 pytest tests passed |
| m11-solver-03 | 3.0984006999999565 | 3 pytest tests passed after admission edit |
| m11-root-independent | 5.487869200000091 | 5 independent pytest tests passed |
| m11-root-diagnostic | 3.314852700000074 | Final-source diagnostics reproduced numerical results |

Owner total **10.522612199999912/120** seconds. Root total
**8.802721900000165/120** seconds. No pooled/renewed benchmark authority.
M8 ledger remains **540.0326433999871/600** seconds. Exact commands, source
identities, runtime environment, status, counts and stdout/stderr are in each
`run.json` and logs. Later diagnostic JSON adds input-binding metadata and is
not relabeled as byte-identical to the earlier artifact.

Product hashes remain:

- prepared_static.py: 9BFD155164823156674CA6B4B1E332E798D390EF615172476253A81298287D70
- prepared_static_response.py: C4DF1E40C70238C96BFA5F5F0FBB61C20687E8EB79CE35EB9F953167D59C5152

New implementation/verification artifacts are the M11 gate, diagnostic and author
tests, `test_prepared_static_response_m11_independent.py`, this report and task-note
update. Author proof and hashes: `.prepared-static-evidence/m11-solver-handoff.md`.
Main revisions remain solver `da1ba2e9`, ANYfem `f74812d`; isolated revision and
existing dirty work remain preserved. No commit, merge, push or 10,000-case claim.
Different-family assessment remains unavailable; OpenAI independent inspection
does not substitute for that qualification requirement.

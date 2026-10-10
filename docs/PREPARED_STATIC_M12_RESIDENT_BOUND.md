# M12 — resident SuperLU solve bounds

2026-10-09. Implemented the next bounded diagnostic step after M11. The bound
targets the **resident factor's returned solve**, rather than any vector passing
the generic residual gate. It reads no observed direct solution/residual. Product
and default backend selection are unchanged. **Production activation remains
INCONCLUSIVE**: native arithmetic prerequisites and complete requested-output
coverage are not qualified, and the free-free intervals remain too wide.

## Implemented route and review

The diagnostic owns copied factor/permutation/scaling data from the actual
evaluator-owned SuperLU handle. It records the exact represented factor relation
defect but does not mistake that for a proof of returned floating-point results.
Preparation does not factorize another operator. It encloses external RHS scaling,
row permutation, lower/upper triangular solves, column permutation and returned
solution scaling. It then propagates intervals through the frozen M10 staged
recovery and prepared canonical von Mises formula. The direct solve and recovery
are evaluated only after coordinate and output intervals are complete, as oracles.

For a triangular solve it conditionally assumes

    |T*yhat-bhat| <= g*(|T|*|yhat|+|bhat|)+a,
    g=gamma_(2n+2),
    a_i=(2n+2)*mu*(1+|Tii|)/(1-(2n+2)*u).

Here u=2^-53, mu=2^-1074. This is an explicit **unqualified native residual
relation**. Root review identified an underflow hole in a constant count*mu
allowance: dividing 1e-20 by 1e308 may produce zero, leaving a row residual of
1e-20. The diagonal-scaled term and regression test preserve that counterexample.
Vendor TRSM reciprocal packing needs its own analysis; a direct scalar-division
proof is insufficient to qualify the native relation above.

The first positive triangular comparison recurrence is preserved. One targeted
tightening replaced its cancellation loss with exact signed row actions. For
each row, solve T.T*w=e_i using rational arithmetic, then use J_i=|w| and the
transient current row K_i=J_i*|T|. With exact signed center c and input radius eb,

    h=g*(|T|*|c|+|b|)+(1+g)*eb+a,
    e_i=(J_i*h+g*sum_prior Kij*e_j)/(1-g).

Root reviewed the derivation from
`|delta| <= |T^-1|*h + g*|T^-1|*|T|*|delta|`: K is triangular in the direction of
T and Kii=1. The implementation streams row actions; it neither forms nor stores
an inverse matrix. It still performs substantial exact rational work and is a
proof diagnostic, **not a faster online implementation**.

Independent closed-form lower/upper triangular controls verify cancellation,
adversaries satisfying the declared residual relation, scalar underflow, signed
loads/scaling and owned factor data after source mutation/deletion. Unsupported
backends, invalid data and overflow refuse execution. Different-family numerical
acceptance remains unmet; cached Mistral unavailability is retained.

## Observed results

The diagnostic contains **114 linear/beam values and 14 von Mises values**, all
sampled after their bounds were formed. These are conditional containment checks,
not complete full-model or arbitrary-history qualification.

| Quantity | Final result |
| --- | --- |
| Supported 12-coordinate S3 | Coordinate interval widths 9.934002405398434e-18 / 1.22514845490862e-16 |
| Supported linear component pairs | 35 of 56 separate strictly for min and max |
| Supported prepared canonical VM pairs | All 7 separate strictly for min and max |
| Supported VM width / existing diagnostic tolerance | Maximum 2.3295080995922417 / 2.3304145202095934 |
| Augmented free-free 54-coordinate model | Coordinate widths 2.2089854114276813e-8 / 1.4005205251084662e-7 |
| Free-free beam shear | Widths 0.0008564721735612767 / 0.0054308886442133615; neither pair separates |
| Exact self ties | None excluded |

The initial free coordinate widths 778.4649082692811 / 4944.512977605813 are
retained in `m12-resident-01.json`. The signed-action improvement is a bound
tightening, not a measured performance improvement. Free shear widths remain
many orders above the diagnostic tolerance. Broad intervals do not establish
actual backend inaccuracy. Supported separation applies to these widely separated
sample pairs; near ties and unresolved contenders still require canonical replay.
Interval width above a tolerance is not an observed output-error failure.

No principal/eigensolver bound, full reaction certificate, prescribed-offset
qualification, source/full-load assembly uncertainty bound or envelope activation
is supplied. Zero offsets are asserted in these fixtures. Reused M10 recovery
arithmetic assumptions remain conditional. No tolerances, clipping or tie rules
were changed.

## Installed runtime and source evidence

The matched [SciPy 1.16.3 build definition](https://github.com/scipy/scipy/blob/v1.16.3/scipy/sparse/linalg/_dsolve/meson.build)
defines USE_VENDOR_BLAS=1. The
[native solve source](https://github.com/scipy/scipy/blob/v1.16.3/scipy/sparse/linalg/_dsolve/SuperLU/SRC/dgstrs.c)
uses supernode triangular solves and matrix updates. Source identity alone does
not prove the installed binary's exact executed kernel or error bound.

Read-only runtime observations: SciPy 1.16.3; NumPy 2.4.3; loaded SciPy
OpenBLAS 0.3.29.dev and NumPy OpenBLAS 0.3.31.dev, both reporting SkylakeX/pthreads
and **one thread**. This differs from the build metadata's Haswell target; the
observed runtime identity is recorded separately.

Installed binary hashes match the local wheel RECORD:

- SuperLU pyd: 503dd04bcabf2d61a5ef0312bb605445de69de97f1b8299a4f3d8245c01a2516
- SciPy BLAS DLL: 48c358d105077551cc9cc3ba79387ed54f5f57794d8382bffce42ff788135adc

That comparison does not authenticate upstream delivery. Root's read-only
`_controlfp_s(...,0,0)` query returned 0x8001f, with rounding-control and
denormal-control bits zero for the calling thread. The
[Microsoft contract](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/controlfp-s?view=msvc-170)
defines the zero-mask call as a query, and those bits as nearest rounding and
denormal preservation. One scalar and one BLAS product preserved subnormals.
These are observations of the calling thread and sampled operations, not a proof
of every native kernel, future callback or thread state. No runtime settings were
changed. Full JSON: `.prepared-static-evidence/m12-root-runtime.json` and
`m12-runtime-05.json`.

The native triangular residual relation, exported-factor/native-supernode
equivalence, exact operation/reciprocal behavior, runtime authority and complete
recovery arithmetic remain qualification prerequisites. PARDISO is explicitly
outside this prototype; defaults remain intact.

## Checks and resource accounting

All execution used `C:/Github/ANYsolver/.venv/Scripts/python.exe` through the task
runner with `--kind check --benchmark-epoch m8 --jit 0`, isolated solver imports,
one OMP/BLAS/Numba thread and disabled pytest plugin autoload. Numerical jobs were
serial. **10 distinct pytest tests passed**: final author suite 5, independent
suite 5. The earlier author suite had 4 tests and was rerun after the signed-action
change; it is not counted as four additional distinct tests.

| Run under `../evidence/checks/` | Process-wall seconds | Result |
| --- | ---: | --- |
| m12-solver-01 | 3.551157699999976 | Initial comparison-bound fixture diagnostics |
| m12-solver-02 | 1.5516181999998935 | 4 tests passed |
| m12-solver-03 | 4.971860699999979 | Final signed-action fixture diagnostics |
| m12-solver-04 | 1.475950100000091 | 5 tests passed |
| m12-solver-05 | 0.7114882999999281 | Runtime identity observation |
| m12-root-independent | 1.5139205999998921 | 5 independent tests passed |
| m12-root-runtime | 0.6656966000000466 | Runtime/hash/floating-state observations |
| m12-root-diagnostic | 4.867179799999803 | Final diagnostic reproduced byte-identically |

Owner total **12.262074999999868/120** seconds. Root total
**7.046796999999742/120** seconds. No failures, timeouts or skips. Exact commands,
input/source identities, effective settings, counts and full logs are in each
run directory. Final author/root JSON SHA256:
`87ADEACAB9E68F70F5FAA1D2256E7FAFDC85D0C5EFAA3BCFCD3441AF9BA0430C`.
No benchmark charged; M8 ledger remains **540.0326433999871/600** seconds.

## Delivery and next decision

The new M12 diagnostic/tests/runtime evidence, independent tests and this note
remain in the isolated candidate. All product hashes and previous evidence remain
unchanged; no commit, main update, merge, push or 10,000-case claim. Author formulas,
source hashes and preserved first candidate are in
`.prepared-static-evidence/m12-solver-handoff.md`.

Retain the conditional resident-factor proof and canonical fallback. Do not launch
a performance campaign before the bound is qualified and useful for the requested
outputs. The next discriminator is **output-aware error propagation**, particularly
for free-free stress quantities where displacement uncertainty and cancellation
inflate independent coordinate intervals. Preserve canonical staged evaluation;
using a signed linear action to bound its uncertainty is not permission to replace
its arithmetic with a flattened response product. Native arithmetic qualification
is still necessary even if such intervals tighten. This report grants no extra
execution authority or production activation.

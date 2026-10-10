# M14 — exact recovery primitives and native backward-solve audit

2026-10-09. Implemented the next authorized diagnostic slice. **Exact primitive
rules remove the free-free staged selector floor; the native backward-solve
allowance still prevents exclusion.** Supported sampled von Mises bounds tighten
further. Production activation remains INCONCLUSIVE. No backend, canonical
arithmetic, tolerance, product/default API or performance claim changed.

## Rules implemented and independently reviewed

M14 retains M13's signed output actions and stage-error graph. A primitive gets no
new rounding symbol only where numerical binary64 exactness is proved for every
admissible represented operand in its interval:

- Multiplication by zero or a unit/sign, all-zero selectors, a single nonzero
  exact selector, and addition of a proved zero are exact for finite represented
  operands under the retained gradual-underflow arithmetic assumptions.
- Power-of-two upscaling preserves significand bits if the whole interval image
  stays finite. Downscaling is exact only when a represented point's exact product
  is representable, or a one-sided interval guarantees all output magnitudes are
  at least the minimum normal. Unknown subnormal alignment keeps its allowance.
- Division by a power of two uses the equivalent mathematical scaling rule.
  Other factors and multiple nonzero dot terms retain rounding allowances, even
  where coefficients are signs or the mathematical result cancels.

These rules change uncertainty allowances, not the actual canonical operations.
Known RHS scaling points and uncertain final scaling are treated separately.
The normal-output proof is not used on intervals crossing/touching zero.
Numerical exactness does not certify signed-zero payload identity.

Root independent exact-rational controls include minimum subnormal times 0.5,
three minimum subnormals times 0.5 and the value immediately below minimum normal
times 0.5: all are inexact. Twice minimum subnormal times 0.5 is aligned and exact.
Positive/negative normal-output intervals, extreme finite values, overflow,
nonrepresentable downscale proof points, selector/sign/zero rules and multioperand
cancellation are also checked. Canonical operation ordering, recorded constants
and all existing tolerances are preserved.

## Results on unchanged fixtures

All **114 sampled linear/beam and 14 prepared canonical von Mises values** are
conditionally contained. The canonical oracle is evaluated only after intervals
are complete; no observed direct solution, intermediate or residual enters them.

| Measure | M13 | M14 |
| --- | --- | --- |
| Supported VM maximum width/tolerance, case 0 | 0.5797735072345366 | 0.41417271158745167 |
| Supported VM maximum width/tolerance, case 1 | 0.5802780880962873 | 0.4143894285603639 |
| Free beam shear interval width, case 0 | 2.7015925810968573e-5 | 2.6989498679118414e-5 |
| Free beam shear interval width, case 1 | 0.00017128332206196284 | 0.00017111561127996288 |

All 7 supported VM pairs and 35 of 56 supported linear-component pairs separate
strictly for min/max under the conditional model. Exact self ties remain
unresolved. Cancellation-sensitive supported shear remains limited mainly by
enrichment/kinematic roundoff. No whole-model governor claim follows from these
sampled pairs.

The free model has unit scaling and exact selector transforms: RHS/final-scaling
and physical/local-transform noise disappear. This resolves the stage floor
identified in M13. Free radii now comprise:

| Contribution | Case 0 | Case 1 |
| --- | ---: | ---: |
| Native forward | 2.0616355102323604e-9 | 1.3079289894672069e-8 |
| Native backward | 1.349268770404881e-5 | 8.554472635008572e-5 |
| Beam kinematics | 1.174920741216155e-19 | 7.44985559950348e-19 |
| Beam material | 4.75362641034631e-20 | 3.014164422710268e-19 |

Neither free pair separates. Width/tolerance ratios remain about 2.70e7 / 1.71e8.
This diagnoses a conservative bound limitation, not actual backend error. Native
gamma/additive constants were not tuned or reduced. Exact selector bookkeeping
cannot address the dominant allowance.

## Native backward-solve audit

The matched [SciPy 1.16.3 object wrapper](https://github.com/scipy/scipy/blob/v1.16.3/scipy/sparse/linalg/_dsolve/_superluobject.c)
copies the RHS and invokes gstrs using resident factors/permutations. Its exposed
attributes provide shape, nnz, permutations and CSC L/U; they do not export the
native supernode partition or packed vendor-solve operation schedule. The
[double-precision solve source](https://github.com/scipy/scipy/blob/v1.16.3/scipy/sparse/linalg/_dsolve/SuperLU/SRC/dgstrs.c)
distinguishes scalar supernodes from vendor TRSM/GEMM branches and subsequent
column updates. Thus CSC row counts alone cannot establish the exact native
rounding graph.

M12 recorded installed binary hashes, one-thread runtime and calling-thread
floating-point observations. Loaded SciPy BLAS reports 0.3.29.dev/SkylakeX;
metadata does not identify an exact source commit and selected kernel sufficient
to qualify the required primitive relation. The public OpenBLAS v0.3.29 directory
was readable during this audit, but individual requested driver/packing-source
pages returned web cache misses; those contents were not assumed inspected.
The release tag would still not alone establish identity with the installed dev
binary. No private-memory pointer introspection, new native wrapper/build or
backend switch was attempted.

There is **no justified tighter native relation in this slice**. Even hypothetically
reducing only the operation count in the existing generic magnitude allowance to
one rounding unit would leave a very large free uncertainty. That is a usefulness
observation about this model, not a rigorous error floor or permission to alter its
constants. A useful native bound needs evidence of primitive/schedule behavior and
its correlations, rather than an empirically selected gamma.

Native supernodal/vendor relation, factor-export equivalence, transitive arithmetic
and runtime authority remain UNQUALIFIED. Selected diagnostic helper binding/code
checks are not complete executable admission or a production operation lease.
Principal/eigensolver, complete reactions, source/full-load construction,
nonzero-offset, arbitrary-history and full-model certifications remain outside the
prototype. Different-family qualification remains unmet; cached Mistral
unavailability persists. Canonical fallback is unchanged.

## Actual verification and accounting

**12 distinct tests passed:** author 7 and independent root 5. Root independently
reproduced the final diagnostic byte-for-byte. No failures, timeouts or skips.
All runs used `C:/Github/ANYsolver/.venv/Scripts/python.exe`, existing task runner
`--kind check --benchmark-epoch m8 --jit 0`, isolated solver source/tests, one
OMP/BLAS/Numba thread and disabled pytest plugin autoload. Numerical jobs were
serial; no benchmark authority was used or pooled.

| Run under `../evidence/checks/` | Process-wall seconds | Result |
| --- | ---: | --- |
| m14-solver-01 | 5.235063699999955 | Four fixture cases; 114 linear/beam + 14 VM containment |
| m14-solver-02 | 1.4878617999997914 | 7 focused author tests passed on final source |
| m14-root-independent | 1.5484213999998246 | 5 independent controls passed |
| m14-root-diagnostic | 5.458386700000119 | Final diagnostic reproduced exactly |

Owner **6.722925499999746/120** seconds; root **7.006808099999944/120** seconds.
M8 benchmark ledger remains **540.0326433999871/600** seconds. Exact commands,
source identities, effective settings, counts and full stdout/stderr are retained
in each run directory. Author/root JSON SHA256:
`D4D0DED89224A745B3F04AE2707C73A72B49A16F61A0334A65F3DAF77ED27028`.

New M14 exact-action graph, diagnostic and author tests, independent root tests and
proof/evidence remain isolated. Author source hashes and derivation:
`.prepared-static-evidence/m14-solver-handoff.md`. Product hashes remain
9BFD155164823156674CA6B4B1E332E798D390EF615172476253A81298287D70
(`prepared_static.py`) and
C4DF1E40C70238C96BFA5F5F0FBB61C20687E8EB79CE35EB9F953167D59C5152
(`prepared_static_response.py`). Frozen previous source/evidence remain preserved.
No main edits, Git delivery, speedup claim or 10,000-case qualification.

## Decision

Retain the exact-primitive rules and conditional supported VM result. Do not
activate exclusions or launch a performance campaign. Further recovery-only
allowance refinements do not resolve the demonstrated free-free blocker. The next
required evidence is a useful, justified native solve-error relation; public factor
data and runtime identity observations alone do not supply it. Any further work
should target that concrete dependency, preserving fallback and avoiding another
generic count/fixture sweep. This note supplies no additional execution authority.

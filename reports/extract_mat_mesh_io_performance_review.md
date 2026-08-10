# extract_mat_mesh_io performance review

Date: 2026-08-08  
Branch and revision: extract_mat_mesh_io at 711d21c

Implementation follow-up: 2026-08-08 working tree after the audited revision.

## Decision summary

The extraction architecture does not introduce measurable conversion overhead
for the tested models. No change to the ANYmesher -> ANYfem -> ANYsolver package
boundary is justified.

The audit identified a batched/JIT S4 geometric-stiffness kernel as the highest
confidence optimization. The audit prototype
reduced the 360-shell local KG work from 83.44 ms to 2.55 ms after geometry
preparation, with a relative matrix difference of 2.5e-17. It remained 1.95x
faster when uncached geometry preparation was included. It required
qualification across the supported S4 state and geometry space before
production use. That qualification and production integration are now
implemented, including cached reference geometry and batch/fallback diagnostics.

Initial stress and initial prestrain no longer disable the whole-model
optimized nonlinear assembler. Elastic S4 batches integrate exact initial
resultant offsets directly; initialized plastic shells retain scalar element
evaluation and unaffected shells remain accelerated. A 96-S4 all-initialized
case measured 2.03 ms versus 21.82 ms scalar after warm-up (10.7x).
Corotational kinematics still uses the scalar formulation because no
numerically qualified batch exists.

The MPC direct-reduction plan now uses the measured approximately 72-assembly
break-even with a conservative default threshold of 144 estimated useful
assemblies. Eligible elastic Beam3 members now use a compiled batch; 72 rotated
elements measured 0.164 ms versus 17.43 ms scalar after warm-up (106x), with
force and tangent equality qualified against the scalar element.

Do not force PARDISO for the tested 1,932-DOF reduced buckling problem. The
current size policy correctly chose SuperLU. Shift/invert is beneficial when a
reliable target factor is already known, but it should remain an opt-in or
follow-on-analysis strategy rather than the default first solve.

## Method

Measurements used Python 3.13.9, NumPy 2.4.3, SciPy 1.16.3, Numba and
PyPardiso on a 32-logical-CPU Windows host. OMP, MKL, OpenBLAS and Numba were
held to one thread so comparisons measured architecture rather than changing
parallelism. Compiled kernels were warmed before steady-state timing.

Short phases report the median of 5-9 runs. End-to-end nonlinear and
eigensolver comparisons report the median of 3 runs. RSS was sampled every
2 ms; Python allocation peaks use tracemalloc. Traced runs are not used as
timing results because tracing itself adds overhead.

The representative models were:

- A 4.0 m x 2.4 m stiffened panel: 360 S4 shells, 72 Beam2 elements,
  75 weighted eccentric MPC couplings, 475 nodes, 2,850 total DOFs and
  1,932 reduced DOFs.
- Matched pinned columns: 160 Beam2 elements and 80 Beam3 elements, each with
  966 total and 320 reduced DOFs.
- A 96-S4 fixed-edge plate for repeated two-step nonlinear solves.
- A 336-S4 plate passed through the actual ANYfem adapter for extraction
  conversion comparison.

The measurements below describe the pre-implementation audit baseline. The
follow-up changed only recommendations supported by those results; the
extraction boundary, PARDISO policy and linear persistent-CSR architecture
remain unchanged.

## Extraction and model construction

| Phase | Median |
| --- | ---: |
| Raw structured topology generation | 0.290 ms |
| Neutral plate-container construction | 0.430 ms |
| Full stiffened neutral-mesh pipeline, including couplings | 6.855 ms |
| Neutral stiffened mesh -> FEModel | 2.393 ms |
| Actual ANYfem plate -> FEModel adapter | 1.703 ms |
| Direct equivalent plate -> FEModel construction | 1.757 ms |

The actual adapter was 0.054 ms faster than the direct equivalent in this run;
the difference is measurement noise, not overhead. The resulting stiffness
matrices were identical (maximum absolute difference zero). Stiffened
conversion peaked at approximately 76 KiB RSS increase and 0.78 MiB traced
Python allocation.

Conclusion: neutral-mesh construction and FE conversion together are small
beside assembly and eigensolution. The extraction boundary adds no supported
runtime or peak-memory concern.

## Linear assembly and KG

Steady-state full assembly on the stiffened panel:

| Matrix | Median | Notes |
| --- | ---: | --- |
| K | 20.17 ms | All 360 S4 shells use the Numba batch; 147 beam/MPC elements use the general path |
| M | 13.97 ms | Same S4 batch coverage |
| KG | 94.68 ms | Every element is evaluated in the Python element loop |

At audited revision 711d21c, KG was assembled element-by-element and shell-local
work dominated buckling. The follow-up implementation batches S4 elements and
retains scalar assembly for triangles, Q8, beams and other formulations.

### Audit-only S4 KG JIT prototype

| Phase | Median |
| --- | ---: |
| Current scalar local KG for 360 S4 shells | 83.44 ms |
| Geometry/state preparation | 40.33 ms |
| JIT batch kernel | 2.55 ms |

The prototype supports membrane resultants, bending resultants, stress second
moments and per-Gauss local transformations. Against the current element
routine it produced a relative Frobenius difference of 2.5e-17 and maximum
absolute difference of 3.6e-12.

Measured implications:

- First assembly with uncached preparation: 1.95x faster for shell-local KG.
- Repeated assembly with cached reference geometry: 32.7x faster for the
  shell-local kernel.
- The 1.58 MiB batched matrix output should be scattered directly rather than
  retained longer than assembly requires.

This is strong evidence for a production S4 KG batch, subject to qualification
on distorted, rotated and warped S4 geometry and every documented state-key
form. It is not evidence for silently extending the kernel to triangles, Q8 or
unsupported initial-stress terms.

### Production follow-up measurement

After qualification and integration, a 360-S4/485-total-element stiffened
panel measured 16.63 ms median end-to-end KG assembly over nine warmed runs.
The cached S4 kernel portion was 0.488 ms and the geometry cache was reused.
The original audited 360-S4 model measured 94.68 ms, although its beam/coupling
count was not identical; the supported conclusion is that S4 local KG is no
longer the dominant assembled phase, not a strict cross-model speedup ratio.

## COO versus persistent CSR

Using identical element matrices, persistent CSR scatter was exact to
roundoff and 6.0-6.6x faster than COO-to-CSR conversion:

| Matrix | COO -> CSR | Persistent CSR scatter | Isolated scatter speedup |
| --- | ---: | ---: | ---: |
| K | 3.39 ms | 0.55 ms | 6.22x |
| M | 3.45 ms | 0.58 ms | 6.00x |
| KG | 3.53 ms | 0.54 ms | 6.56x |

When scalar local element computation is included, the measured total gains
were only 1.9% for K, 4.4% for M and 3.4% for KG. Production K and M already
batch shell-local work, so their integrated gain could be larger than this
scalar reference, but that integrated implementation was not benchmarked.
The persistent map also consumes memory and setup time.

Decision: do not replace the current linear K/M/KG assembly architecture from
this evidence alone. If pursued, benchmark an integrated batch-output-to-CSR
implementation and measure process peak memory, not only NumPy array sizes.

## Nonlinear acceleration and fallbacks

One nonlinear tangent/internal-force evaluation on the stiffened panel:

| Path | Median | Relative to persistent path |
| --- | ---: | ---: |
| Persistent batched full-coordinate CSR | 5.43 ms | 1.00x |
| Scalar reference von Karman | 14.00 ms | 2.58x |
| Initial membrane stress | 65.31 ms | 12.0x |
| Initial membrane prestrain | 64.90 ms | 12.0x |
| Corotational, rotated tangent | 95.65 ms | 17.6x |

The persistent result matched the scalar force to 6e-21 relative and the
tangent to 1.2e-16 relative. Source dispatch at the audited baseline confirmed:

- Any initial shell/beam stress or prestrain sent the whole model to the scalar
  reference assembler. The follow-up removes this model-wide shell fallback.
- Corotational kinematics sends the whole model to the scalar reference
  assembler.
- Erosion/deleted elements disable direct reduced-coordinate scatter, although
  the full-coordinate persistent assembler can still handle element scaling.
- Orthotropic shells, generalized shell sections, triangular shells and
  reduced-integration Q8 shells remain scalar elements inside the persistent
  CSR plan.
- Beam2, Beam3 and MPC elements were outside the shell batch. The follow-up
  adds the qualified ordinary elastic Beam3 batch; Beam2 remains scalar.

Matched two-step plate solves preserved completion and comparable iteration
counts:

| Case | Median total | Newton iterations | Status |
| --- | ---: | ---: | --- |
| Accelerated von Karman | 63.09 ms | 7 | completed |
| Initial stress | 186.02 ms | 7 | completed |
| Corotational | 284.21 ms | 8 | completed |

The accelerated solve's sampled peak was 2.81 MiB RSS increase and 10.88 MiB
traced Python allocation. Initial-field and corotational outputs were finite;
the audit did not substitute a faster kernel, so their numerical semantics
were not altered.

Conclusion: extending the existing shell batch to carry immutable initial
stress/prestrain is the highest-impact nonlinear investigation. A
corotational batch is also potentially valuable, but its frame update and
consistent/rotated tangent contracts make it a higher-risk qualification task.

## MPC reduction

For the 2,850 -> 1,932 DOF weighted-MPC reduction:

| Operation | Median |
| --- | ---: |
| Full persistent nonlinear assembly | 5.43 ms |
| Post-assembly T-transpose K T | 1.77 ms |
| Direct reduced-coordinate assembly | 5.03 ms |
| Direct reduced-plan setup | 154.83 ms |

Direct reduced assembly saved about 2.16 ms per tangent evaluation, or 30% of
the full-assembly-plus-projection cost, and matched the projected matrix to
3.8e-17 relative. However, the extra plan setup breaks even only after roughly
72 tangent evaluations on this model.

Decision: retain direct reduced assembly, but do not assume it wins every
solve. The follow-up exposes setup/runtime counters and the cost-gate decision,
and avoids setup for short analyses using a conservative 2x break-even margin.
Direct reduced-coordinate linear assembly is not justified by this nonlinear
result alone.

## Beam2 and Beam3 coverage

Both beam formulations are scalar inside the nonlinear persistent plan and
inside linear K/M batching.

Beam-only, 120-element tangent evaluations took 1.71 ms for Beam2 and
18.9 ms for Beam3. In the matched stiffened panel, replacing 72 Beam2 spans by
36 Beam3 elements changed the nonlinear tangent from 5.50 ms to 10.21 ms.
Linear K improved from 30.54 ms to 22.73 ms because the Beam3 model had half as
many elements; KG remained shell-dominated at about 96 ms.

The pinned-column buckling profiles were:

| Model | K | KG | Eigensolve | Total | Euler error |
| --- | ---: | ---: | ---: | ---: | ---: |
| 160 Beam2 | 6.74 ms | 6.04 ms | 1.77 ms | 17.26 ms | 0.121% |
| 80 Beam3 | 11.66 ms | 5.31 ms | 1.59 ms | 20.80 ms | 0.121% |

Residuals were 1.1e-9 and 3.5e-9. Beam3 nonlinear batching has measurable
potential in quadratic stiffened models. Beam2 batching is lower priority
because its realistic absolute cost is small. Neither should be implemented
until a batched kernel is shown to reproduce the current beam force, tangent,
state and generalized-section contracts.

## Buckling eigensolver, linear solve and recovery

Unshifted stiffened-panel buckling:

| Phase | Median |
| --- | ---: |
| K assembly | 20.73 ms |
| KG assembly | 97.26 ms |
| Load tangent | 0.13 ms |
| MPC/fixed reduction | 4.25 ms |
| Sparse eigensolution | 77.29 ms |
| Recovery/filtering | 7-8 ms |
| Total | 203.15 ms |

The sampled buckling peak was 12.18 MiB RSS increase and 19.27 MiB traced
Python allocation.

With the converged first factor supplied as a shift target, cold-cache total
time fell to 156.25 ms and reused-cache time to 142.13 ms. Eigenvalues agreed
within 9e-15 relative and the maximum residual was below 3e-10. This is useful
for repeated nearby load cases, mode tracking or continuation, but a first
solve still has to establish a reliable target.

The ordinary SPD linear factor-and-solve cost was 15.46 ms cold and 1.05 ms
with factorization reuse. Solutions were identical and the relative residual
was 3.9e-13.

### Forced PARDISO comparison

The current auto policy selected SuperLU because the reduced problem is below
the 10,000-DOF and 250,000-nnz cold thresholds.

| Shift/invert backend | First use | Repeated cold cache | Reused factorization |
| --- | ---: | ---: | ---: |
| SuperLU | 34.14 ms | 29.74 ms | 14.81 ms |
| PARDISO | 172.93 ms | 28.12 ms | 20.90 ms |

PARDISO factored faster (6.68 vs 14.57 ms) but its 117 inverse applications
took longer (45.53 vs 28.74 ms), so total reused eigensolution was slower.
The load factors agreed within 1.1e-14.

Decision: keep the current auto threshold and do not force PARDISO for this
problem size. A larger-problem threshold study is still needed before changing
the selector; the present model supplies evidence against lowering it.

## Priorities supported by evidence and implementation disposition

1. Implemented: qualified S4 KG batching with cached reference geometry,
   warped/rotated geometry coverage and documented scalar fallbacks.
2. Implemented: elastic initial stress/prestrain resultants in the JIT shell
   kernel, with exact scalar overrides retained for initialized plastic shells.
3. Implemented: direct-reduction cost diagnostics and a conservative gate for
   short nonlinear solves.
4. Implemented: ordinary elastic Beam3 nonlinear batching; generalized and
   fiber-plastic Beam3 variants remain scalar. Beam2 remains lower priority.
5. Keep targeted shift/invert and factorization reuse for follow-on buckling
   solves; keep SuperLU/PARDISO auto selection unchanged.

Rejected for lack of supporting end-to-end evidence:

- Moving the ANYmesher/ANYfem/ANYsolver boundary.
- A wholesale switch of linear K/M/KG to persistent CSR.
- Forcing PARDISO or lowering its current size threshold.
- Treating initial fields or corotational response as ordinary von Karman
  batches without new kernels and numerical qualification.

## Scope limits

The original S4 KG prototype was validated on one representative stiffened
panel; the production follow-up adds distorted/rotated/warped and documented
state-form scalar-oracle tests. PARDISO was forced on the representative
1,932-DOF reduced model; this review does not establish its large-model
break-even point. RSS sampling can miss allocations shorter than 2 ms, and
tracemalloc excludes native-library allocations. These limits are why
unimplemented proposals remain deferred.

# Elastic Q4 reference reuse — 3 October 2026

**Delivered experimentally:** a guarded reference-compilation optimization and
measured warm workflow improvement. Source commit `5136f026`; no aggregate gate,
G5 qualification, release, or large-model speedup is claimed.

## Change and correctness boundary

The mixed owner previously evaluated two inherited zero-state shell kernels:
`legacy_3 + (qualified - legacy_5)`. For virgin elastic material with the existing
closed-form thickness integration, the three/five-layer operators coincide;
direct qualified stiffness differs only by binary64 subtraction/addition rounding.
The new private seam still applies the **same consistent corotational tangent**,
frame sensitivity, force rotation and diagnostics. It introduces no tangent lag,
constitutive-intermediate cache, new equations, public API, default or version.

Eligibility requires the exact qualified Q4 class, 24 DOFs, no generalized shell
section, exactly shaped/all-zero predecessor arrays, elastic material, constant
reference z and an exactly zero pulled-back deformational field. J2/Hill,
nonvirgin/unknown state, near-planar geometry and nonexact charts use the full
response. S3 and the algorithmic/curved routes retain their existing dispatch.
Returned stiffness and candidate arrays are independently owned; original
qualified revision/provider guards remain active.

## Checks and independent scrutiny

- 22 current focused source checks pass. Earlier dense-oracle checks remain
  valid for unchanged product inputs; all are included in the installed run.
- **35 distinct installed checks pass**, zero failures/skips: 31 core checks plus
  four affected modal/footprint checks. Coverage includes cold work-scaled local
  parity/rigid modes, geometry and unit/thickness/order controls, actual fallback
  and dispatch, state ownership, cache/provider guards, independent dense assembly,
  material histories, finite continuation against forced-full compilation,
  cross-compilation restoration, exact restart, and the 32-member ANYfem Project.
- Independent OpenAI Read review found no product correctness/guard defect.
  Its requested near-planar, dispatch and old-path continuation checks were added.
  Its provenance/criteria findings were resolved by joining frozen identities and
  strengthening adjudication. A small other-route test leaves its owner open;
  this is test hygiene, not a product ownership finding. This is development
  scrutiny, **not cross-family scientific acceptance**.
- Early collection/fixture failures remain in the archive. Complete console
  traces for the first two attempts were not captured to disk; available
  selection, runtime, resource and later full diagnostics are retained.

## Paired timing

Seven serial alternating baseline/candidate pairs per fixed elastic point-panel
case, on Windows/Python 3.14, BLAS/Numba pools 1 and JIT off. The measured warm
route includes definition, two owner compilations, two load cases, recovery,
checkpoint/restore and restarted continuation. Imports, initial warmup, final
evidence writes and cleanup are excluded; import/process times remain recorded.
This is not cold-start or complete application timing. Profiling was separate.

| Case | Baseline median (range), s | Candidate median (range), s | Median reduction | Max physical-vector relative difference |
|---|---:|---:|---:|---:|
| 400 Q4 / 120 B3 | 32.349 (32.049–34.954) | 14.244 (14.154–14.443) | **55.97%** | 3.30e-13 |
| Smaller 24 Q4 / 32 B3 control | 3.506 (3.438–4.389) | 2.409 (2.378–2.800) | **31.29%** | 1.10e-15 |

Preflight identity, DOFs, constraint count, stored nnz, factorization/refinement
counts and rotation diagnostics match. Exact within-artifact restart and
re-encoded checkpoints pass. Frozen physical tolerance is 1e-10; first-solve
equilibrium/compatibility/balance and resource predicates pass. The smaller case
is also optimized; it is not a performance-neutral control. The three-pair screen
and version1 adjudication are preserved alongside the completed version2 checks.

Baseline wheel `c795a5da...bcc7d` retains the `f58abf96` library; candidate wheel
`cd481416...ca2c58` matches source `5136f026`. The prior frozen baseline identity
was joined and **413 baseline / 414 candidate installed modules were reverified
against pinned wheels after samples**; the candidate was also verified before
checks/timing. The timing child checked import roots, rather than hashing binaries
itself. The unchanged consumer wheel `5f5c203c...223a` has 98 matching modules.
Full hashes, imports and dependency entries are retained.

## Same saved practical-size model

The candidate completed the **combined** persisted ANYfem route with 10,000 Q4,
1,000 native B3 elements on ten stiffener lines, 110 explicit point ties, 97,320
mixed rows and 4,972,608 stored nnz. Input/project and prior numerical arrays match
the immutable earlier inventory; no new mesh or connection law was substituted.

- Supervised elapsed **282.497 s**, sampled peak **4,593,385,472 bytes**
  (4.59 GB / 4.28 GiB), within 600 s / 8 GiB.
- Reopen 7.568 s; first compilation 120.925 s; first solve 10.456 s;
  second compilation 127.328 s; restore 0.0189 s; continued solve 10.120 s.
- First equilibrium 5.06e-10; compatibility 1.49e-14; force/moment balance
  9.22e-10 / 9.65e-10. Largest frozen-vector difference **3.97e-11**.
- Exact four-array restart, checkpoint re-encoding and subsequent-load parity;
  one eligible factorization per owner. Pools 1/JIT off verified; up to seven
  process-tree OS threads were observed, not one OS thread.

This candidate-only run establishes feasibility/parity/restart. It is not a paired
large-model timing campaign, the registered nonmatching workload, the short
nonlinear sequence, simultaneous-plasticity scale, or complete G5 acceptance.

## Evidence and next action

[Summary/inventory](summary-v1.json), [review](independent-development-review.txt),
[immutable raw archive](raw-evidence-v1.zip): 264 whitelisted files, 6,887,391 bytes;
SHA256 `ec4502b73887f66b73d33c30253282be1f4cb192fd04fc0d6759b8a0df0cf78b`.
Raw records include wheels, source/fixture versions, failed checks, 28 paired
samples, installed runtimes, provenance bindings, adjudication sources and the
large route. They contain no inherited environment dump or historical canary.

The next bounded discriminator is a moderate finite elastic sequence: separate
local evaluation, chart work, sparse assembly and factorization to identify the
remaining obstacle to the required practical-scale nonlinear route. Do not infer
nonlinear speed from the reference result or automatically launch a larger job.
Connection/external/platform/material/stability obligations remain open; formal
F03 is unconsumed and no publication authority is used.

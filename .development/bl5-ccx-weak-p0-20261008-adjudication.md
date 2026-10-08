# BL5 weak-P0 CalculiX Fy/Mx development comparison — 8 October 2026

**Decision sought.** Can a resolved C3D20 reference execute the declared
five-channel, four-edge weak-P0 connection without changing its row space,
and what physical Fy/Mx response does that reference give beside the native
experimental BL5 owner? This is a development comparison. It does not select
the line law, allocate V5's earlier work ratio, consume F03, or accept G0/G1.

**Model and action.** The existing 1 m panel and rectangular bar use the same
isotropic material, eccentric placement, root support, and 20 weak-P0 rows as
the saved resolved reference. The 20 rows are changed only by an invertible
row transformation for CalculiX `*EQUATION`: unique, non-SPC beam-side pivots
at x=0,.25,.5,.75 m. The serialized pivot block is exactly identity; the
physical row reconstruction error is `6.28e-17`. The resolved end-face
traction has either Fy=100 N with zero centroidal Mx or Mx=10 N·m with zero
net force to quadrature precision. Native loads are the corresponding B3-GE
centroidal nodal wrench. These load fields have equal resultants, but their
work on cross-section warping is not assumed equal. The resolved body has no
independent native quarter-cell side traces.

**Saved attempts.** All directories are preserved, including failures:

| Directory | Outcome |
|---|---|
| `bl5-ccx-weak-p0-20261008-fy-v1` | Metadata JSON preparation rejected a NumPy integer; CalculiX never launched. Partial deck retained. |
| `bl5-ccx-weak-p0-20261008-fy-v2`, `-fy-v3` | Windows DLL-relocation error at sandboxed process launch; no CalculiX mechanics result. Full launch receipts retained. |
| `bl5-ccx-weak-p0-20261008-fy-v4` | Pinned CalculiX 2.23 exited 0 and completed one increment outside the default sandbox; original recovery script had a dense/sparse `lstsq` argument error. Saved FRD, STA, logs, deck and receipt retained. |
| `bl5-ccx-weak-p0-20261008-fy-v4-recovery-v1`, `-v2`, `-v3` | Successive read-only recovery/check versions from the same saved run. `-v3/result.json` is the current development parity record. |
| `bl5-ccx-weak-p0-20261008-mx-v1` | CalculiX rejected a `1.1e-15 N` roundoff `*CLOAD` card. Full failed deck and logs retained. |
| `bl5-ccx-weak-p0-20261008-mx-v2` | Corrected roundoff-only load cards; CalculiX exited 0 and completed one increment. |
| `bl5-ccx-weak-p0-20261008-mx-v2-recovery-v1` | Current read-only development parity record. |
| `bl5-ccx-native-fy-mx-20261008-v1`–`-v5` | Native comparison revisions. `-v3` exposed a missing geometry key; `-v5/result.json` is the current verified comparison, including geometry and prior parity admission. Earlier results retain their original source identities. |

The pinned `ccx.exe` SHA-256 is
`27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f`.
FY deck SHA-256 is
`3e7499ef913d184d681ede0f5324d4accd26ca8a47aa6c7f305ecc64c3849ef0`;
Mx deck is
`7575fbf329ef288b88e3c5eb8c362ec4f93979819ff642277ace65b71495f300`.
The FY specimen source hash (`827238...`) predates the Mx-only roundoff-card
repair; Mx uses `a6fca2...`. Exact source hashes and file hashes are in each
JSON record. No old evidence was overwritten. The `*STATIC` minimum-increment
warning is present, but the saved STA records exactly one accepted full step.
The launch supervisor records CPU0, one thread, JIT off and checks 30 s child
and 60 s total development limits; the total check occurs after the small
postprocessing solve and is not a hard watchdog. Observed child wall times were `0.08224 s` (Fy)
and `0.08071 s` (Mx). Its approximately 3 MB RSS figures are **samples**,
not a hard peak-memory proof; a hard process-tree memory cap is still needed
before treating this runner as formal resource qualification.

**Same-law check.** CalculiX displacement relative to independent sparse
C3D20 KKT is `1.53e-9` for Fy and `3.12e-10` for Mx. Scaled free-equilibrium,
weak-gap, raw-reaction, corrected-support, force/moment balance, and work
checks pass their explicit development parity limits (`1e-6`, with `1e-9`
absolute weak-gap limit); the exact numbers are in the recovery JSON. Raw
CalculiX root `RF` equals `(Kq−f)` at fixed coordinates and excludes the
constraint contribution. Adding the recovered `Cᵀλ` produces physical support
wrenches that balance the applied Fy/Mx actions. This correction is required
for every physical reaction comparison.

**Native comparison.** Both native linear cases completed with a 20-row BL5
constraint and free-equilibrium ratios below `3e-13`. The work-conjugate
responses were:

| Action | Resolved C3D20 | Native B3-GE | Native/resolved |
|---|---:|---:|---:|
| Fy=100 N, average end-face y displacement vs native centroidal tip y | `1.24610738e-5 m` | `1.19569992e-5 m` | `0.95955` |
| Mx=10 N·m, traction-conjugate twist vs native centroidal tip spin x | `8.24615888e-5 rad` | `1.01006732e-4 rad` | `1.22489` |

The native shell-side interface wrench and the negative of the resolved
beam-side interface wrench agree in resultant sign and magnitude to the
reported numerical precision. Both support wrenches balance their own
external action. The response differences remain unallocated among body
formulation, torque-traction/warping, root idealization, and connection trace.
The new Fy/Mx loads are not V5's original +Fz tip-node action. In particular,
the Mx polar face traction is not an exact work image of every native retained
half-cell field. Zero weak interface work follows from `Cq=0` and does not
measure connection compliance.

**Beam-only discriminator.** The saved Mx traction was then applied to the
resolved bar alone, fixing all 39 translation DOFs on its x=0 root face. The
native B3-GE beam block used its two axial members and matched physical section with a
10 N·m tip torque, fixing the six root pose coordinates while retaining all
48 internal coordinates. Both solve/balance checks passed. Work-conjugate
responses are `1.44991865e-4 rad` (resolved) and `1.64701403e-4 rad`
(native), ratio `1.13594`, compared with `1.22489` coupled. The raw runs
`bl5-mx-beam-only-20261008-v1` and `-v2` remain; `-v3/result.json` binds the
final metadata-load guard and is current. The initial focused test attempt
could not create pytest's default sandbox temp directory; the rerun at
`bl5-ccx-weak-p0-20261008-test-v2.log` passed 4/4 using a fresh workspace
temp root, including a mutated-load refusal. Supporting read-only review
found the clamps, work pairing and signs internally consistent. This
beam-only discrepancy shows section/traction/root modelling matters, but
the ratio difference is not an additive allocation of coupled compliance.

**Rigid-shell counterfactual.** A separate same-law local solve then fixed
every shell coordinate and left the beam connected by all 20 weak rows, with
no added root clamp. The resolved and native work-conjugate tip spins are
`2.91845519e-6` and `1.18869316e-5 rad`, ratio `4.07302`. Both KKT,
gap, work and physical interface-wrench checks pass. The local Euclidean
row-normalized algebraic conditions are `7.30` and `3.08`; this is not a
physical inf-sup or mixed-system stability measure. `bl5-mx-beam-only-20261008-v4`
is the first saved rigid-shell run and `-v5/result.json` binds the completed
rank diagnostic and explicit interpretation. This counterfactual restrains
the beam along x∈[0,1] and is much stiffer than a root-only clamp. It
amplifies conforming-versus-broken trace differences and cannot allocate or
predict the coupled `1.22489` ratio. Supporting read-only review found no
KKT sign/work defect and emphasized this boundary-value distinction.

**Next discriminating action.** Stop loaded refinements. Read-only source
inspection found existing global-common-field tests that exercise all five
native and resolved weak-row densities, including beam x-spin, on the
supported globally affine material/director subspace. Those tests do not
represent independent native quarter-cell side rotations. Reuse their
previous execution evidence only after checking its bound source identity.
The remaining mechanics question is the off-common trace space and its
growing-interface stability under the prospective F03 contract. No new
common-field helper, automatic axial refinement, channel tuning, or formal
F03 execution follows from these diagnostics alone.

Three focused source deck tests passed. A supporting same-family read-only
review found no sign or reaction-recovery error and identified the load-work,
source-version, development-threshold and sampled-resource qualifications
addressed above. It is not the required independent mechanics acceptance.

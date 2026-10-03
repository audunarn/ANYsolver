# Projected BL5 density: bounded assessment and installed comparison

Status: IMPLEMENTED_NOT_QUALIFIED. Retain the distinct optional experimental
candidate; withhold production multiplier-policy selection and M2/G0 acceptance.
No formal F03 authority or release authority was consumed.

## Change and decision

The compiler now admits `discontinuous_p1_cell_average`, with separate identity
`BL5_P1_discontinuous_cell_average_span_<n>`. All five channels use the affine
reference-arclength density averaged over each native half-cell. Nonuniform
cell/support lengths use physical endpoint distances; shell segmentation does
not alter the coefficient. Existing bases, defaults, local pose equations,
native retained variables, multiplier curvature and checkpoint meanings remain.
The new identity prevents cross-basis checkpoint restoration.

The preceding [torsion patch](../r8-bl5-torsion-consistency-20261003/results.md)
established a particular affine-density inconsistency. The
[projected patch/work screen](../r8-bl5-projected-density-20261003/results.md)
removed it but did not establish a usable constrained system or matched recovery.
This slice completed those checks and ONE matched coarse development comparison.
It does not select the continuous connection law or satisfy all required line laws.

## Executed evidence

Eight distinct source targets passed after a checkpoint-error-wording test repair.
The initial 7-pass/1-fail evidence and the affected 1-pass retry remain unchanged.
The new tests cover uniform/nonuniform means and support lengths, all-five-channel
P0 row projection/dual work, actual finite-update curvature at nonzero multipliers,
finite stepping, actual density recovery, reciprocal old/new checkpoint rejection
and exact same-candidate restart/continuation.

A fresh installed wheel passed 29 distinct compiler/legacy/helper controls. Initial
installed 12-pass/8-fail and helper 7-pass/2-fail outcomes were missing disposable
script fixtures, not product failures; corrected affected runs passed 8 and 2.
A final affected helper check passed after review hardening. No passing campaign
was rerun without changed scope. An initial fixture-manifest traversal also tried
to hash `__pycache__`; restricting it to files repaired that tooling failure.

Wheel SHA256 `a47e518fe36050e1a2d5a93d9d8c9802138e46c0cc9d8c1c840cc5efdd8650d3`.
All 417 source/wheel/site Python modules matched byte-for-byte; 238 actual solver
imports were from the installed site in the main test run. ANYmaterial remains
editable at its recorded workspace identity; this is not final package-graph,
platform or release verification. Product version remains 0.4.7.

79 math/reference controls passed, including unchanged affine defaults and exact
projected weights, independent Gauss integration, endpoint actions, actual finite
objective work, invertible equation emission, all five density channels/degrees,
and physical beam-root wrench/moments through polynomial order three. Unit-support
m4 endpoint changes +/-1/96 are scalar controls, not actual coarse/fine weights.
Complete C*J and dual-work comparisons passed on saved coarse and growing-fine
traces. J samples common virtual fields; it is not mechanical condensation or an
assertion of equal constitutive discretizations. These are not seven-ratio solves.

The saved coarse native mixed-system oracle retained nodal and half-cell rotations
and eliminated only verified negative local resultant blocks. Native K is not an
SPD energy norm. The existing numerical congruences and uncertainty criteria were
retained: minimum constraint singular value .124202; minimum supported kernel
eigenvalue 1.73935e-5, uncertainty 3.10917e-11; reduced inertia 769+/80-/0,
implied full native inertia 769+/368-/0. Full general sparse and reduced bounded
oracle solves agreed for three RHS, including separate shell/beam-node/cell-rotation
checks, resultants, multipliers and reactions; largest parity discrepancy 2.73e-11.
No constitutive-history parity is measured by this virgin matrix assessment.

## Matched result and interpretation

The independently reviewed comparison froze 16x4 Q4 shells, 16 native members /
32 half-cells, eight supports, geometry/frames/offsets/grounds, Fy100N/Mx10Nm/Mz10Nm,
and the beam-root moment origin (0,0,.0675). Supplementary OpenSees 3.8 execution
used the verified Python3.12 binary; it does not replace mandatory CalculiX evidence.
Each external case completed with physical residuals below 4e-12. Installed native
3-RHS execution used one eligible factorization, equilibrium <=3.61e-13 and weak
gaps <=1.13e-20. All complete ground/domain/work controls passed.

| Case | Unmodified affine work difference | Projected work difference |
|---|---:|---:|
| Fy | -1.04649% | -0.593604% |
| Mx | -1.02387% | +0.0152484% |
| Mz | -0.843272% | -0.182889% |

For Mx, interior-region Mz difference fell from about 11.0894 to .0490446Nm and
beam-ground Fy difference from about 20.4266 to -.0665144N. Native K was exactly
unchanged; installed projected C exactly matched the independently reconstructed
saved assessment. Installed/saved general q discrepancy was <=3.81e-12.

Both native and reference changed their density action. The restricted patch
establishes the particular consistency correction; this loaded solve establishes
improved agreement on the fixture, not continuum accuracy or exclusive cause of
the remaining errors. Fy still has beam-ground differences 6.357N in Fx/3.586N in
Fy; Mz has regional differences 1.400N in Fy/1.065Nm in Mz. Combined shell field
errors are about 1.188% (Fy), .0428% (Mx), 1.087% (Mz), with the recorded 1m
force/moment convention. None is a converged-reference acceptance result.

All jobs were serial and terminal. Effective native BLAS/Numba pools were one,
JIT disabled; no measured speedup is claimed. The bounded oracle took 2.37s/
190MB sampled RSS; matched native execution 4.12s/186MB. External route supervision
sampled one numeric/unresolved thread; general external-thread qualification
remains outside this slice. Limits remained 600s/8GiB/8threads and one heavy job;
small checks used 1GiB. [Raw manifest](raw-manifest.json) binds exact sources,
artifact, inputs, commands, failed and completed logs, results and raw arrays.
It preserves 225 explicit safe files, without protected F03 or canary/history scans.

## Next action and limits

A further saved-array work check identifies a concrete requirement for the
prospective stability contract. A unit infinitesimal bare-beam normal-axis rigid
rotation respects the physical supports, agrees EXACTLY with the saved physical
beam rigid-work map, and has actual full native K*q EXACTLY zero. Its supported
moment-eliminated S residual has normalized backward error8.33e-19. Nevertheless
its absolute norm is 7.405e-6, not exactly zero after floating-point elimination.
C*q is nonzero; one physical density row performs -.1171875J virtual work on it.
This bare structural mode is NOT admissible under the attached constraints;
the coupled KKT check remains valid. An ordinary unconstrained inverse-compliance
norm is therefore not defined for arbitrary interface actions. Rigid nullspaces
and work compatibility require explicit treatment. For a conservative structural
null vector r, the equilibrium requirement is `(C*r)^T*lambda = r^T*f`;
a pseudoinverse alone omits this balance. Neither invented stiffness
nor mass repairs the mathematical interpretation. This is not a nullity count,
SPD proof, stability quotient or formulation-failure claim. No fresh mesh solve
was needed: .535s/63.4MB, one sampled numerical thread. The original manifest
remains unchanged; [supplemental9-file evidence](raw-manifest-v2.json) preserves
the prospective note, exact arrays, source, command and complete diagnostics.

Retain this complete experimental candidate. Next assess whether its consistency
correction survives growing interface spaces, rather than automatically refining
classical axial or fixed-support models. State the specific trace-resolution,
locking or physical-transfer question and action for each outcome before running.
Use a justified mathematical stability contract and existing scientific criteria;
no quotient, rank, small gap or this improved Mx result selects the space.
Director fidelity, shear/drilling, remaining interpolation/force transfer, all
seven ratios/three-level convergence and full mixed-system requirements remain.
Independent review [disposition](review.md) leaves no defect in this slice, but
not different-family scientific acceptance. Full G0-G6/B2/external/scale/platform/
consumer/release requirements remain open; no automatic campaign follows.

## Coarse auxiliary norm and resolution decision — 3 October

Source parent67fa7945. The existing positive kinematic trace norm remains valid;
the saved bare mechanical yaw counterexample obstructs ordinary structural
inverse compliance, not this norm. No native mechanical inverse or artificial
stiffness/inertia was introduced.

One16x4/32-halfcell/eight-support scalar assessment independently integrates all
16 constant/projected-affine moments, including endpoints and cross-products.
The modal P0 reference is projected by congruence. The supported Q1 inverse uses
the variational lower Gram; the prior product Fortin bound applies to all moments
with independent DG0 rotations, constant arms/frames and zero lift.

Initial v1 failed an unnecessary fixture import; v2 completed calculation but
failed helper-path provenance. Both failed source/log snapshots remain. Scalarv3
is **UNRESOLVED** in its recorded coefficient basis: discrete Gram condition
15998.61277 exceeds unchanged1e4. An independently derived physical density-L2
normalization, diag(H,5H/16), gives discrete/reference conditions5020.306/41.6535,
with quotient change2.36e-15. This is a prospective canonical representation
correction, not Gram whitening or a relabeling of v3. The same scalar CS²120.747662
gives sufficient raw floor.0455020 and safe floor.0454782821; no old P0.43 or
growing-family floor is inherited. The weak estimate remains after normalization.

The actual endpoint cancellation is verified: equal affine coefficients on all
supports act only at the root/free endpoint, coefficient5/(8*32)=.01953125.
The independent scalar checker[1,-3,3,-1] has zero coarse work and positive
continuous dual. Duplicate rows are deficient, not removed. Exact rational
moments and independently reassembled equivalent units pass.

Before native values, physical-registration.json froze the canonical basis,
scalar floor and unchanged budgets. Complete physical force/director/arm loads
agree with the saved projected C in all80 columns to3.47e-18. Independent shell
modal and beam equilibrated-reference majorants meet1e-3 total relative error.
The complete native auxiliary result is beta.2555151765, canonical Gram
conditions1299.605/85.7944, inverse residual6.36e-15 and eigen residual1.86e-14;
every numerical predicate passes. The independent normal-force scalar-extremizer
direction gives.2584081498. Thus the weakness reaches the actual auxiliary
coupling, rather than only its conservative product bound. No loaded-response
failure or uniform collapse follows. Bare yaw retains positive auxiliary
norm.6541667, and exact arm-moment cancellation retains positive force dual.

Review identified admission/provenance gaps. Final physical-v3 validates scalar/
representation hashes, floor/modes/criteria/exact L2 scale, actual geometry and
support endpoints/layout, and equality of removed versus fixed physical trace
slots; output binds helper sources, unchanged wheel and imported local operators.
Seven focused mutations are rejected. The affected run reproduces every value.
Latest physical check1.800s/160165888B; mutation checks2.173s/156479488B. Actual
native numerical pools1, JIT disabled; all jobs below600s/1GiB. No speedup claim.

Next bounded discriminator is a distinct complete40-row nested policy over
four-shell-interval supports: for each channel, new0=L0+R0 and
new1=.5*(-L0+L1+R0+R1). Use exact work/Gram congruence plus the saved actual-K
constraint-kernel oracle: removing rows enlarges the kernel. Interior quarter
support action addresses the identified weakness; stronger beta alone cannot
select the policy. No remesh or loaded campaign is authorized by this result.
Full ratios/refinement/transfer/locking/director checks and M2/G0/F03 remain open.

[69-file extension](raw-manifest-v3.json), SHA256
40535b04f7d96c7502524776db503d80a41b17adb30313654598e091c01c0994,
preserves69 explicitly whitelisted files/3607678B, prior failures, commands,
source snapshots, exact arrays and predecessor/prospective notes. Earlier
manifests/evidence remain unchanged. FormalF03 UNCONSUMED; no product/API/default,
release, resource ceiling or scientific acceptance threshold changed.


## Nested complete40-row development decision — 3 October

One complete policy pairs adjacent old supports on the SAME16x4 shell/32 native
halfcells: new0=L0+R0; new1=.5*(-L0+L1+R0+R1), in allfive channels. Four supports
span four shell intervals; this removes40 constraints rather than changing
coordinates. Independent rational halfcell density and quarter-support actions
agree. Registration bound allscalar/physical input hashes BEFORE native values;
CS squared1.5102603 derives safe sufficient floor.4066548912. Full40-column beta
.8379451049 exceeds it (prior80 beta.2555151765). All40 interlacing inequalities,
reference error.0002419613, norm conditions57.3761/40.3748 and work controls pass.
No mechanical K inverse or new norm is introduced.

Fresh actual-K enlarged kernel preserves769 free nodal/cell coordinates and
verified resultant stationarity. Minimum kernel eigenvalue1.73803656e-5 exceeds
uncertainty3.10607102e-11; reduced inertia769positive/40negative/0zero. Initial
fullunrefined sparse solution failed parity/equilibrium/energy despite a passing
kernel; maximum full/reduced parity6.25e-6. This failure is retained. Applying
exactly the EXISTING installed owner policy (one compensated residual correction
using the same fullfactor) gives maximum parity1.01e-11 and passing three-RHS
controls. The reduced oracle does not supply the correction.

Installed unchanged417-module wheel/source/site identity is exact. Actual owner
K agrees exactly and C differs3.56e-18; states/resultants/multipliers/reactions
agree within the existing1e-10. One eligible factorization and three mandatory
corrections suffice for Fy/Mx/Mz. Extended recovery binds actual layout, sections,
frames, supports and stations, exact regional moments and full physical work/
ground/domain balance (maximum9.34e-13). Two development harness failures
(missing scripts import path and the detached inventory's numerical binding)
are preserved before correctedv6. No product/API/default/version change.

ONE supplementary OpenSees batch uses identical geometry, sections, offsets,
grounds, loads and independently assembled projected40 physical action. Exact
nested external rows agree with old80 congruence in784 columns to1.09e-19.
Allphysical derivative/work/equilibrium/weak-gap and emitted inventory controls
pass. Native cell rotations are retained; comparison uses common nodal fields
without identifying them as external beam rotations. Exact region [0.25,0.75]
and x0/x1/x2 wrench moments include the eccentric/root lever arm.

| Load | Prior80 work difference | Nested40 work difference |
| --- | ---: | ---: |
| Fy100N | -0.593604% | -0.599234% |
| Mx10Nm | +0.015248% | +0.014145% |
| Mz10Nm | -0.182889% | -0.267593% |

Regional differences generally improve: regionFy-force difference for Fy falls
1.9771 to.06352N; regionMz-moment difference falls1.2594 to.12070Nm. Under Mz,
corresponding differences fall1.4003 to.10735N and1.0651 to.08454Nm. Some other
components worsen, and beam-support axial-force differences remain5.0629N(Fy),
-.23972N(Mx), .40447N(Mz). Coarse whole-field differences therefore cannot confer
converged1% acceptance or allocate the remaining shell/beam/connection error.
Both reference and native constraint spaces changed; neither is the historical
strong bond. Pointwise gaps are reported independently of weak equilibrium.

Decision: RETAIN the complete40-row space as an experimental candidate for its
required growing-space assessment. Stronger norm plus positive actual kernel
and similar global work with improved regional transfer make it defensible to
advance; they do not select a production policy. First next discriminator is a
joint refinement with the SAME complete four-shell-interval policy and unchanged
physical ratio, after checking the registered meaning of beam ratio/halfcells.
This distinguishes a growing-space improvement from a coarse-space benefit; a
norm/kernel/physical-transfer failure stops expansion for its precise cause.
Allseven ratios/three levels, locking/director/shear/drilling and fullmixed checks
remain required. No automatic axial/S8R campaign or formal F03 execution follows.

Independent complete-slice Read review has no unresolved development defect;
it does not satisfy different-family scientific acceptance. Norm/owner checks
are below4s/196MB; each serial external check below.52s/50MB, one sampled numeric
or unresolved thread. These are diagnostic costs, not measured speedup or fully
qualified external thread settings. Failed runs and limits remain recorded.

[140-file extension](raw-manifest-v4.json), SHA256
cccb7bb60aba3bd42057d0e01f4b63931a18d6424b8dd0617e291965bedd27c4,
preserves13193716B of explicitly whitelisted source/commands/raw arrays/outputs/
failures/reviews and prospective/parent notes. Prior manifests are unchanged;
exact bytes will be verified in source and Git staging. FullM2/G0/F03 and all
programme/material/platform/scale/consumer/release duties remain open.

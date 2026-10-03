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

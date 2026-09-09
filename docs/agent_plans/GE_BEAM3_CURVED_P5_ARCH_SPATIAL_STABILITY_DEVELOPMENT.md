# P5 sampled arch spatial stability — 2026-09-06

Research successor to clean `07025cff6f178d9363acdeea970d90ec28075120`, tree
`4d6054537eb01726b5ec0fba20b6ad0886790dc8`. Adds only the postprocessor,
its small tests, and this record. No assembly, continuation, constitutive,
geometry, recovery, mass, source mechanics, defaults or accepted proof changes.

## What was inspected, not rerun

Use the already completed eight 16-element arch trials from request
`9790867871004048873b26ae6029311e`. That request is consumed and its nonlinear
worker was not rerun. The resource administrator has recorded COMPLETED_PASS
for execution accounting only, with the original qualification restriction.

Input aggregate: 924 bytes, SHA-256
`A53D7BAA8AD6A21CA892DBA2F10968458171CE8A87DA6770A418545477F1BC8E`.
Input worker record: 6499 bytes, SHA-256
`49E71F90D144963D8739918E5851D35A81D78579D93DB2C877B7681461D2C182`.
Source freeze: `cc8f4b7ddea2deee6b29c9446a9b6269ef9b8d1b`, tree
`55afb09201ad7dc130fb5fa46c88be130d4057ef`.
The existing closeout contains the complete sixteen-file external inventory.

Before importing NumPy, the new postprocessor checks the exact registered
aggregate/worker hashes, strict JSON, raw hashes and inherited packet/schema
checks. It imports no beam mechanics or nonlinear solver. This is matrix
postprocessing, not independent reconstruction of the physical operator.
The inspector has a 30-second cooperative deadline around bounded matrix
operations, not an OS watchdog. Matrices are capped at 198 full nodal or 186
free coordinates. No resource-heavy campaign was launched. Input files remain
read-only; outputs must be fresh external paths outside the raw proof tree.

## Reflection, coordinate scale and numerical inertia

The load is a spatial dead crown force and the ends are clamped. The stored
internal tangent therefore is the total-potential Hessian: the prescribed
force potential has zero second variation. Check positions/rotations, proper
frame orthogonality, clamps, and free equilibrium after subtracting the external
force before using this conservative interpretation. Retain support reactions.

Reflection across the xy plane is S=diag(1,1,-1). Translations are polar:
delta r -> S delta r. Spatial rotation increments are axial:
delta theta -> det(S) S delta theta. The even/in-plane coordinates are ux,uy,rz;
the odd/out-of-plane coordinates are uz,rx,ry. Treating rotation increments as
polar would assign the wrong blocks. There are 31 free nodes: 93 coordinates
in each block, 186 altogether.

Scale rotational coordinates by reference span 2 through a positive diagonal
congruence before comparing spectra. This preserves inertia; eigenvalue
magnitudes depend on that coordinate metric and are **not frequencies**. No
mass, invented rotary inertia, or dynamic qualification is involved.

Check symmetry, reflection invariance and full-versus-block spectral union to
normalized 1e-11. Do not symmetrize away failures. Check each eigensystem's
residual, orthogonality and reconstruction against the complete input. For
numerical sign reporting, use the residual norm plus matrix norm times
orthogonality error, plus a 64*epsilon*dimension*norm rounding allowance. Add
the cross-block norm to each block's uncertainty allowance. Values within this
band are unresolved, never declared positive by rounding. This diagnostic band
is not a rigorous directed-rounding interval or an exact rank certificate.
All eigenvalues and the lowest nodal mode of both blocks remain in the output.

## Results: a second sampled negative direction

The stored tangents have zero reflection coupling. Full and block spectra
agree with maximum normalized error 3.572946069626488e-16. Maximum eigensystem
residual is 1.343635239474961e-15; orthogonality error 2.3728727697052092e-14;
reconstruction error 2.07511639128215e-15. No sampled sign is unresolved under
the stated numerical band. These checks support matrix interpretation only.

Steps in this table are zero-based, matching the preserved raw records.

| Step | Crown drop | Lowest in-plane value | Lowest out-of-plane value | Full negative count |
|---:|---:|---:|---:|---:|
| 0 | 0.002903184309488105 | 0.0024734952274028128 | 0.0007569117315472188 | 0 |
| 1 | 0.006574911264755651 | 0.001933676615531231 | 0.0007481397344952116 | 0 |
| 2 | 0.01114956966840841 | 0.001450309721002951 | 0.0007292492769192497 | 0 |
| 3 | 0.016642350214247037 | 0.0010404521624104504 | 0.0006712599671378934 | 0 |
| 4 | 0.022931652221715157 | 0.0007100719737496086 | 0.0005052039928691496 | 0 |
| 5 | 0.02983238936540321 | 0.0003081583065976744 | 0.000299635861138228 | 0 |
| 6 | 0.03717258569148828 | -0.0002679589703225751 | 0.0001282404519927347 | 1 |
| 7 | 0.044820372353098756 | -0.0007416289051271535 | -0.0000023173918075870807 | 2 |

The first negative direction is in-plane at step 6. At step 7 the out-of-plane
block also has one negative value. Its uncertainty band is
1.517753628776951e-8, approximately 153 times smaller than the negative value's
magnitude. The earlier unscaled out-of-plane minimum is approximately
-7.6661e-6; this difference is coordinate scaling, not a changed operator.

Disposition: `SAMPLED_OUT_OF_PLANE_INSTABILITY_PRESENT`. This does not revoke
the valid load/recovery/energy accuracy result. It prevents that result from
being misread as stable spatial equilibrium throughout the descending branch.
Conversely, it does not by itself prove a defective element: a curved arch can
lose spatial stability physically. Eight sampled signs are not a root-located
critical load, uniqueness proof, continuous interval coverage or identification
of a continuum bifurcation. No negative direction is removed or stabilized.

## Repeatability, tests and preserved outputs

Two fresh Python processes read the same frozen matrices, one numerical-library
thread each, and wrote to distinct directories. The combined command completed
in about one second. The complete output bytes, not just summaries, matched.
Each output is **109306 bytes**, SHA-256
`252ACE01CABF4B11818657436F7D49B669325B9B97B7BFE21FAF7C5679495E9F`.

Root:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-arch-spatial-inspection-20260906-145897dcccdb49819744cc786820c1e1`.
Files: `first/inspection.json` and `second/inspection.json`.
Inspector SHA-256 bound in both results:
`B4B5B22CB43C00E0670F022ECD0CFF442CA308928DDC9E2E29F69E9D86AA53B2`.

The small suite passed **20 tests in 0.16 seconds**, covering polar/axial
reflection, scaling without mass claims, negative/near-zero inertia, symmetry
and coupling mutations, load subtraction, planar/frame/support mutations,
hash/deadline guards, import boundaries, disposition precedence and repeatable
serialization. Its artificial matrices are labeled synthetic, not mechanics
evidence. The recorded nonlinear path was not part of the test suite.

## Next substantive check

Independently reconstruct the **continuum out-of-plane second variation** about
the separately solved planar arch branch. Derive spatial virtual-rotation,
shear, bending/torsion and prestress terms from the rod potential, not from
the stored discrete matrices. Verify the straight unstressed/axially loaded
limits and virtual-work signs, then test the lateral boundary-value operator
near the sampled sign change. This should distinguish a physical lateral
bifurcation from a spurious discrete mode before expanding the candidate's
spatial buckling claims. Any fresh large path or refinement needs a new
resource request; there is no automatic retry of the consumed request.

The overall goal remains active and incomplete. Full nonlinear-section/state
parity, broad curved/slender coverage, robust local solves, physical mass and
dynamics, prestressed modal, production interfaces/restart, independent review,
opt-in packaging and objective beam-shell joints remain open. Both outputs
retain `production_qualified=false`, `continuum_buckling_qualified=false`,
`natural_frequencies_computed=false`, and
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`. Main, existing B2/B3/Q4/S3 mechanics,
accepted qualification evidence, defaults, tags and packages remain unchanged.

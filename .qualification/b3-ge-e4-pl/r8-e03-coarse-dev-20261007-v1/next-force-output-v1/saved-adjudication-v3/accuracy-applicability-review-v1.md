# Saved E03 accuracy applicability — supporting Read

The saved level-0/+offset comparison is **FAILED / NOT CONVERGED as a compliance screen**. It does not establish engineering accuracy, identify a solver defect, or qualify E03. No new physical execution, import, pytest, CCX, Git operation or worker was used for this review. Different-family final review remains unmet.

This native result is **B2**, profile `B2_E4_PL_FAST_LINEAR_V1`, law `B2_FINITE_Q4_POINT_REFERENCE_LINEAR_V1_DEV`. It is not the principal GE finite distributing connection result. Neither its compliance nor the external fitted-port comparator supplies a GE independent shell-rotation/director/drill work map or GE accuracy acceptance.

## Matched fixture and actual model distinction

The native result and original external metadata identify case `de068305dc66eee8946e6a22c2e018998abf3e8f4e38a1c8167770215b91c391`, level 0, positive eccentricity. The nominal roof is 0.508 m long, radius 2.540 m, half-angle 0.1 rad, thickness 0.0127 m; E=3.10275e9 Pa and nu=0.3. Ribs have width 0.00635 m and height 0.0254 m. Their local x axes follow global x, local y follows the facet tangent, and local z follows the facet normal. Rib angles are -0.05/+0.05 rad. The centroid offset is +0.01905 m along that normal, applied once through the connection; no effective flange or parallel-axis section addition is made.

The native bulk model has 35 shell nodes/24 flat Q4 facets and ten beam nodes/eight physical B2 members. Its declared section has A=1.6129e-4 m², Iy=8.671488033333333e-9 m⁴, Iz=5.419680020833333e-10 m⁴, J=1.8262996556780857e-9 m⁴, and shear factors 5/6. The external model has 333 physical nodes and 32 quadratic reduced-integration C3D20R solids: 24 roof elements and four elements per rib. There is only one roof element through thickness and one element across each rib width/height.

Both place eight point stations at the same axial midpoints and facet mid-plane centroids. Native shell ports fit a six-role rigid pose to the four vertex translations, then couple it to the B2 physical station trace at station 0.5. External ports fit the same shell vertex translations and four solid section-corner translations, joined by six affine equations per station (48 total). These constraints do not impose a continuous weld or rigidify a complete solid section: local deformations in the fitted projection's kernel remain free. There is no declared released generalized connection role. Native station interpolation is the B2 section/operator trace; external interpolation is a deformable 3D solid section. Thus equal port work does not imply equal bulk stiffness.

Native root nodes restrain all six translations/rotations. External ROOT restrains all three translations on 49 solid face nodes. These impose the same zero generalized root pose, but the solid face also suppresses local section distortion/warping and Poisson deformation that the six-coordinate beam/plate idealization does not resolve. Each rib receives global (0,0,-0.5) N at its tip centroid, without moment; external nodal loads are the fitted-pose transpose of that wrench. The saved external applied wrench is approximately (0,0,-1,0,+0.254,0) about the world origin.

There is one concrete small bulk-geometry inconsistency: the external roof is extruded radially at the polygon vertices, whereas the native flat Q4 thickness is normal to its facet. At level 0 the external facet-normal thickness is `0.0127*cos(0.1/6) = 0.012698236151941494 m`, 0.0138885674% below the native 0.0127 m. Mid-plane vertices and port origins still match; recorded coordinate rounding is at most 6.938893903907228e-18 m. This discrepancy is real, but its size does not justify assigning the much larger compliance gap to it.

## Valid saved comparisons

Applied-force work `p·u` is matched and work-conjugate: native centroid force times B2 tip translation versus external fitted-transpose nodal force times solid nodal translation. This is full linear force-displacement work, not the half-sized strain energy.

| Quantity | Native B2 | External solid |
|---|---:|---:|
| Applied-force work, J | 1.5094209446109492e-5 | 4.210950351426983e-5 |
| Rib 0 tip ux, m | 1.256347105710702e-6 | 2.376811125753351e-6 |
| Rib 0 tip uy, m | -3.5364182908738024e-7 | -3.712864253352215e-7 |
| Rib 0 tip uz, m | -1.5094209446108192e-5 | -4.2109503518539525e-5 |
| Root Fz, N | 0.9999999999998272 | 1.0000000000361065 |
| Root My, N m | -0.2539999999999728 | -0.2540000000439406 |
| Scaled external equilibrium residual | 1.7275070263167436e-13 | 1.4974177636511776e-10 |

External/native work is 2.7897786674162974. The absolute difference divided by the larger work is 0.6415486247422877 (64.15486247%). The second rib mirrors the first to the saved numerical precision. The coarse native model therefore has materially lower compliance for this load than the coarse solid model. This is a failed comparator, not a scored 1% qualification result.

Tip translations and fitted mean section rotations are valid descriptive B2/solid port observations. They do not make independent native beam rotation a complete solid deformation measure. The common-origin root resultant is also comparable and balanced; agreement mostly checks equilibrium and load bookkeeping, rather than constitutive accuracy. Eight external gaps satisfy the adopted compatibility predicate. Raw native point multipliers/gaps use ReferencePointLaw rows; external reduced-equation multipliers use another basis. Neither can be compared component by component as world wrenches without the declared primal/dual transforms. Local stresses, shell nodal rotations, solid corner motions and section warping are not interchangeable quantities.

## What the evidence resolves and what it cannot explain

The adopted uncondensed RF recovery resolves the original omitted-equation-force observability issue. The old ROOT-only balance failure 3.990588429916812 remains preserved. It does not explain the displacement/work discrepancy: changing RF output selection does not change the stiffness, geometry or load.

The concrete idealization incompatibility is deformable 3D continuum sections and clamped solid faces versus plate/beam section kinematics, combined with different interpolation and integration at a very coarse mesh. Available solid U permits non-rigid deformation; fitted tip poses and eight zero gaps constrain only the projected roles. Native saved output contains tip poses, total work and native-row connection data, not a full nodal displacement/energy decomposition. Consequently the saved summary cannot allocate the 64% gap among shell discretization, local solid deformation, root effects and section idealization. Continuum warping is a permitted difference, not a demonstrated cause of the measured gap. No converged external reference or matched idealization/convergence evidence is saved here. The three predefined levels also change the polygonal geometry while refining it, so mesh and geometric convergence must remain distinct in any later adjudication.

## Shortest defensible next action

Retain this result as FAILED / NOT CONVERGED and retain accuracy unassessed. Before choosing any new physical check, perform the bounded source/registered-evidence reconciliation: confirm the E03 section table, material frame and station trace against the accepted F09 local section/trace contract; verify the exact B2 fitted-port primal/dual map and report bulk/model differences explicitly. This discriminates an input/axis/unit/operator or trace-map error without reopening either physical model.

The registered F09 result accepts only `B2_PHYSICAL_FLEXIBILITY_LINEAR_V1` section/local operator and station trace: independent Gauss-Jordan/exact-inverse, force-method/cut-wrench/Castigliano, unequal bending-plane, frame/reversal and station-work/trace checks. It reuses installed 200-case/six-row evidence by unchanged relevant identities and records 14 preservation passes. That foundation is useful evidence against a local section/trace error, but does **not** accept arbitrary assembled graphs or attachments and cannot validate E03's bulk stiffness. E03 coarse controls-v1's 33 passes are runner/refusal checks, not those analytic oracles. E03 source tests contain explicit native/world-row and dual-work checks; their mere presence is not a new pass claim here.

If that reconciliation reveals no mismatch, the remaining question is the physical comparator's idealization and convergence, requiring a separately adopted, discriminating next decision and execution authority. Do not automatically refine, fit section properties, loosen criteria or infer failure of the GE connection. The force-observability programme remains at 44.1285582 s used / 105.8714418 s remaining within original 150 s, reserve 60 s; this review consumes no new physical allowance.

## Exact sources and saved records inspected

- `scripts/r8_e03_curved_reference.py`: case/section/frames, lines 145–200; solid geometry/ports/load/root/deck, 243–353; prepared comparison/convergence, 427–507.
- `scripts/r8_e03_native_reference.py`: native definition/load, 16–59; saved work/tip/root observations, 101–144.
- `src/anysolver/_b2_f10_f11_point_attachment.py`: equal-vertex translation fit, station trace and reference-row construction, 107–162. This describes B2, not GE.
- `docs/reference_cases/stiffened_shell_e03_curved.md`, `stiffened_shell_e03_coarse_screen.md`; `tests/test_stiffened_shell_e03_reference.py`; `tests/test_b2_physical_flexibility_linear.py` (source only).
- Original scoped `native-v1/native-result.json`, `native-v1/phase-context.json`, `external-v1/phase/{case.json,metadata.json}`, `controls-v1/junit.xml`, `root-result-v1.json`, `root-audit-result-v1.json`.
- Current `saved-adjudication-v3/{root-terminal-result-v1.json,external-adjudication-v1/candidate.json}` and saved `external-v1/phase/e03.frd`. Bounded saved-data arithmetic was used; no solver/provider initialization occurred.
- The separately permitted single `.qualification/b3-ge-e4-pl/r8-f09-foundation-20260930-v1/results.md` for registered accepted scope only; no other F09 evidence traversal.

Disposition: supporting OpenAI Read; root independent inspection/adoption remains required. No aggregate or different-family acceptance is supplied.

## Root disposition - 7 October 2026

Root independently read the section/point-map source and saved work fields.
The 2.7897786674162974 ratio and 0.6415486247422877 larger-work relative gap
match the raw records. Area and both rectangular bending inertias match the
case dimensions. Source changes since scoped F09 add recovery/load metadata;
this diff shows no change to the local stiffness, physical station polynomials
or six-row point constraint formula used here. This dependency inspection does
not extend F09's accepted domain to E03 or substitute for an assembled oracle.

Adopt FAILED / NOT CONVERGED as the saved compliance-screen disposition;
engineering accuracy remains unscored, E03 aggregate open. Port work/equilibrium
are valid observations; continuum deformation and plate/beam idealization are
not interchangeable. No concrete axis/unit/section-table discrepancy was found
in this bounded reconciliation. The small radial-extrusion thickness difference
is recorded, not asserted as the cause of the large gap. A later physical
comparison must distinguish bulk idealization/interpolation from connection
transfer and establish convergence before a 1% claim. No automatic finer run,
section fitting, GE-law inference or new physical authority follows.

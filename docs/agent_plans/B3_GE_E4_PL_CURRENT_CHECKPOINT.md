# Current B3-GE / E4-PL / B2 development checkpoint

## Current state — 25 September 2026

**Decision sought:** Select a physically defensible native six-channel beam–shell connection and stable exact line space. Neither the six-independent-P0-rows-per-interval law nor the tested global-My/Mz row reduction is suitable as written; no production line or footprint law is selected. G0B remains open, G1 barred, and formal F03 authority unconsumed.

**Established facts:** A conforming, fully bonded 35 mm C3D20R solid reference with matched geometry, left/root supports, and consistent tip loads changes torque work from `34.782→35.076 µrad` and shear work from `41.289→41.530 µm` over factors 2→4. Its plate torque support share still changes from `10.426→11.333 N m`, so two levels do not establish convergence. On one fixed Q4 x8/y8 and B3-half16 model, increasing the native exact-line count 2→8 changes torque `48.190→23.816 µrad` and shear `43.383→34.553 µm`. Axial-only shell refinement to x16/y8 leaves the torque collapse (`48.914→24.032 µrad`) but reduces shear drift (`44.003→41.597 µm`); transverse-only refinement to x8/y16 partly relieves torque (`50.077→27.942 µrad`) but leaves shear drift (`43.501→34.621 µm`). The norm-scaled weak mode persists in both. A trace-dimension diagnostic retaining local force/torsion means and only one global My/Mz first moment reduces the B3-half8, eight-interval rank loss from 41/48 to 33/34, but does not eliminate it. On B3-half16 it is full rank, yet torque still falls `48.693→26.932 µrad` over 2→8 intervals; shear moves `43.386→40.431 µm`. Its mixed dual norm was deliberately not computed, so this is loaded transfer evidence, not stability acceptance. The bounded single-footprint result remains a distinct, promising point/footprint candidate, not a repeated line law.

**Remaining uncertainty:** The solid has cross-section warping and a volume bond; native B3/E4 has a rigid beam section, shell kinematics and an exact weak surface tie. The external factors 2/4 do not close three-level convergence or torque-partition accuracy. The exact-line P0/P1/dual choices still lack satisfactory loaded refinement and norm-scaled stability across the registered ratios. The failed x16/y16 diagnostic hit the existing 1,900-row dense cap before solving; its record is preserved. The accepted x-only and y-only diagnostics isolate directions but do not substitute for coupled mesh refinement.

**Next discriminating experiment and resulting action:** Stop thinning the same six surface-resultant rows. Isolate whether the remaining torque stiffness comes from the B3 rigid-section/warping idealization or from the E4 surface transfer map, using a bounded mechanically matched reference that declares both section and bond kinematics, support sets, and applied work. If a rigid-section reference reproduces the stiffness, document the modelling limit and derive an admissible weak line law from physical traction work; if it does not, revise the shell-side map before another multiplier-space screen. Any candidate then needs a correct mixed dual norm, registered mesh ratios, finite-rotation work and independent review. Do not extend classical axial refinement or select a space from rank, small gaps, or a spectral quotient alone.

Source-bound development records: `.qualification/b3-ge-e4-pl/f03-ccx-full-bond-quadratic-face-dev-20260925-v1`, `f03-surface-resultant-line-dev-20260925-v1`, `f03-line-trace-compatible-ablation-dev-20260925-v1`, `f03-surface-line-shell-refinement-dev-20260925-v{1,2,3}`, and `f03-trace-compatible-yz-dev-20260925-v1`. The v1 shell-refinement record is the preserved row-cap failure.

## Recent evidence and decisions

**Decision sought:** Choose a physically defensible native six-channel beam–shell connection and a stable, adequately resolving exact line space. Neither is production-selected. G0B remains open, G1 barred, and formal F03 authority unconsumed.

**Established facts:** The immediate transverse-order/line-resolution diagnosis is complete: coupled P0 line8→16 changes torque/tip-z by `−17.3%/−10.5%` while bare B3 is stable; P1/dual remain resolution-sensitive. Seven registered mesh ratios are finite and full rank, but the positive physical-compliance Fz mode weakens with row and joint refinement; small residuals, gaps or an indefinite-tangent spectral quotient cannot select a multiplier. A quadratic C3D20R free-bar control resolves the earlier C3D8 shear error (`188.874→190.276→190.541 µm` versus declared B3 `192.024 µm`) and torque (`87.431→88.358→88.299 µrad` versus `88.072 µrad`). The terminal reverse-Fz solid gives `40.944→41.559→41.762 µm`, with all 32/112/416 paired nodes open; this is a directional shear comparator. Zero-clearance terminal torque penetrates; a 1 µm clearance still has three negative quadratic-face samples at factor 4. A declared 2 µm clearance gives torque `16.559→17.073→17.225 µrad` at factors 1/2/4 with no negative samples on a 9×9 interior grid. Its geometry and finite sampling remain explicit limitations. Native Q4/S3 terminal refinement 2→4→8 leaves distributing torque near `11.8 µrad`, while rigid rises toward `10.7–10.9 µrad`; neither matches the solid work coordinate. The finest Q4 plate/beam torque split is `84.9/15.1 N·m` distributing and `86.3/13.7 N·m` rigid, versus `82.0/18.0 N·m` solid. The solid beam rotation exceeds native along the span and especially near the bonded tip.

**New plate-only evidence:** Source `c2d45950` provides a literal continuous top-face traction with exactly matched global wrench, plate geometry, material and left-edge support in C3D20R and E4 Q4. Six CalculiX and six E4 cases completed under `f03-plate-only-solid-e4-patch-dev-20260925-v2`. Torque compliance work is solid `0.001558→0.001615→0.001623 J` for factors 1/2/4, versus E4 `0.001172→0.001204→0.001299 J` for joint shell levels 2/4/8. At the finest tested levels, E4 is `19.98%` below the solid in torque work but only `0.206%` below in transverse-force work (`0.162263` versus `0.162597 J`). Solid torque changes `0.45%` over its last doubling; E4 torque changes `7.86%`. The E4 patch is narrower than one element in each direction even at level 8 (`0.1 m` patch, `0.125 m` cell pitch), and plate thickness is `0.07 m`; this is not a converged shell/solid comparison. The continuous traction is not the native joint's actual constraint-force distribution. These facts rule out attributing the coupled torque gap solely to the connection or declaring an E4 formulation error.

**Local-resolution attribution:** Source `064a798` assembled the same E4 Q4 zero-state operator on a locally graded grid; its uniform control matches the existing adapter tangent exactly. With 2/4/8 elements across both patch directions, torque work is `0.001452→0.001496→0.001509 J` and shear work `0.161176→0.161189→0.161192 J`; physical shell work accounts for the result and numerical-component work is negligible. The last local torque step changes `0.93%`. Source `a36c074e` then held the four-cell patch fixed and refined only the outer grid within 1,710 dense rows: torque rises `1.16%` to `0.001513 J`, shear `0.51%` to `0.162004 J`. The finest solid-plate torque work remains `0.001623 J`, about `6.8%` above that outer-refined E4 value. Thus subelement patch resolution caused most of the original plate-only difference; the bounded outer-grid change is smaller, but neither proves shell/solid asymptotic agreement. Raw roots are `f03-graded-e4-plate-patch-dev-20260925-v1` and `f03-graded-e4-outer-patch-dev-20260925-v1`.

**Thickness attribution:** Source `ae1f2111` halved plate thickness to `0.035 m` with unchanged in-plane patch, continuous traction, material and clamp. The historical `0.07 m` deck is byte-identical under the new builder, and the graded E4 zero-state tangent still matches the uniform adapter exactly. In `f03-plate-only-half-thickness-dev-20260925-v1`, C3D20R torque work is `0.011456→0.011473 J` for factors 2/4; graded E4 is `0.011138→0.011208 J` for four/eight patch cells. The finest torque gap falls to `2.31%` relative to the solid, from about `7.0%` at `0.07 m`; the solid and E4 last changes are `0.14%` and `0.63%`. Finest shear work is `1.297001 J` solid versus `1.285412 J` E4, a `0.89%` gap. This supports thickness-dependent local three-dimensional effects; two thicknesses do not establish a qualified footprint-to-thickness cutoff or prove asymptotic convergence.

**Remaining uncertainty and next discriminating work:** Derive an explicit physical footprint-to-thickness and shell-mesh admissibility policy for the first application; the diagnostic `0.1 m` patch over a `0.07 m` plate cannot simply be promoted. For any proposed admissible geometry, compare the *actual native constraint-induced patch work* with a physically matched 3D bond and a resolved shell, including section warping, deformed-face nonintersection and consistent quadratic tip traction. A close matched response would support a candidate law; a persistent difference requires revising its pose/transfer map. Neither the literal continuous-traction plate-only result nor the small weak gap ranks rigid against distributing. Assess the required true line separately with physical positive compliance, interface modes, loaded transfer, work, rank and registered ratios.

**Next bounded load-map discriminator (prospective):** On the existing locally resolved E4 Q4 plate, compare three exactly equal-wrench +100 N m patch loads: the executed smooth vertical traction, the native distributing director-couple pullback, and the native rigid-corner force pullback. Hold geometry, thickness, clamp and physical shell operator fixed; use four and, if needed to distinguish resolution from load shape, eight cells across the 0.1 m patch. If work differences shrink with local resolution, advance a physically matched bonded-solid comparison before choosing a law. If they persist, treat the smooth-traction solid result as a different load idealization and recover the actual coupled native interface-force distribution before designing the external comparator. This screen does not select a footprint or multiplier; the completed transverse-order/line-resolution diagnosis above is not repeated.

**Load-map outcome and resulting action:** Source `6ca9b1ef`; both predeclared Q4 screens completed with one BLAS thread and the same E4 tangent, support, thickness and +100 N m wrench. Smooth/director/corner torque work is `0.00149557/0.00142436/0.00145440 J` at four patch cells and `0.00150943/0.00142718/0.00145792 J` at eight. The smooth-to-director gap grows `4.76→5.45%`, smooth-to-corner `2.75→3.41%`, while corner-to-director stays near `2.1%`. The completed pair rules out *local patch underresolution alone* as an explanation for these equal-wrench load-map differences; it does not establish asymptotic convergence, a physical bond law, or native coupled accuracy. Raw roots: `f03-graded-e4-terminal-load-maps-dev-20260925-v1` and `-v2`. Next recover the constraint-induced shell force and moment distribution from the existing bounded native coupled KKT, including its work and common-origin wrench, before constructing another solid comparator. Do not treat the previous smooth-traction 3D plate work as a ranking of rigid or distributing native connections.

**Actual coupled interface action:** Source `f366d42d`; the Q4 x4/y4, eight-half-cell native B3 terminal KKT was rerun with read-only recovery. Tip displacement/rotation match the preserved Q4 level-4 run exactly. Under +100 N m tip Mx, distributing transmits global-origin shell wrench approximately `(Fy=19.75 N, Mx=85.20 N m, Mz=9.87 N m)` and rigid `(Fy=14.65 N, Mx=89.03 N m, Mz=7.32 N m)`; even a pure tip couple produces lateral force and another moment through the eccentric coupled structure. Under +1000 N tip Fz, both laws also transmit kilonewton-scale shell Fx and shell My. Each shell/beam interface wrench cancels below `4e-12`, zero-gap work below `6e-17 J`, and no retained coordinate is loaded by the constraint. Only six shell nodes receive forces on this subelement patch. Raw root: `f03-native-terminal-interface-actions-dev-20260925-v1`. This field is *not* a resolved continuum traction and cannot be imposed on the C3D20R plate as a physical bond reference. The next connection discriminator needs a locally resolved coupled patch or equivalent converged interface transfer, then the matched 3D bond with declared clearance, support, section and load meanings. No additional axial or P0-row refinement is implied.

**Next bounded coupled-resolution discriminator (prospective):** Hold the eight-half-cell native B3, its section/root, the 0.1 m patch, E4 Q4 thickness, left clamp and separate tip Mx/Fz loads fixed. Assemble the existing E4 element operator on the four- and eight-cell graded patch grids, and independently reconstruct the distributing mean/director/yaw trace and rigid corner rows. First require parity with the uniform native rows, exact reference wrench and virtual-work identities. Then compare coupled tip work and recovered interface-field moments. If fields and work settle, use that shape to design the matched solid bond comparison; if they drift materially, revise the patch trace or resolution policy before another external accuracy claim. The 1,872-row upper KKT stays inside the existing bounded development envelope, and neither outcome selects a production law or weak-line multiplier.

**Coupled local-resolution outcome:** Source `cfe4ff2e`; the structured Q4 trace matches the existing uniform native rows within `7e-15`, and the corner rows match exactly. The source-bound `f03-native-terminal-graded-patch-dev-20260925-v1` completed four/eight-cell coupled runs with one BLAS thread, actual E4 element tangent and retained native B3 coordinates. Distributing tip Mx rotation is `12.0493→12.0696 µrad` (+0.168%); rigid is `12.2375→12.2649 µrad` (+0.224%). Their Fz tip motion is `44.7711→44.7864 µm` (+0.034%) and `44.7666→44.7966 µm` (+0.067%). The eight-cell law gap is 1.62% in torque rotation, versus a large apparent rigid/distributing difference on the subelement uniform patch. Distributing uses 25→81 shell nodes, rigid four corners by definition. Mechanics checks close below `6e-12`; physical E4 shell work is positive and its numerical component is reported, not hidden. At eight cells the native shell/beam support Mx split is `84.57/15.43 N m` distributing and `84.32/15.68 N m` rigid, against the saved solid's `82.0/18.0 N m`; the solid tip rotation is `17.225 µrad` on its declared 2 µm clearance geometry, about 29–30% above either native result. The response difference therefore survives local patch resolution, but geometry, 3D warping/bond behavior and actual force distribution remain confounded. No footprint or line-space selection follows. The direct precheck first exposed an invalid NumPy block layout and then an overstrict numerical-component assertion; both were corrected before the source-bound execution, with the nonphysical shell work retained in the raw results.

**Read-only span/tip attribution:** Source `a6c1a344` adds station recovery; `f03-native-terminal-graded-profile-dev-20260925-v1` reran only the resolved eight-cell level and reproduces the earlier tip responses exactly. Under +100 N m Mx, saved C3D20R factor-4 fitted section rotations at x=`0/.25/.5/.75/1 m` are `0/3.671/7.370/11.070/17.166 µrad`. Native distributing is `0/3.017/6.035/9.052/12.070 µrad`; rigid is `0/3.066/6.132/9.199/12.265 µrad`. The solid's exact tip *work* coordinate is separately `17.225 µrad`; fitted tip section rotation is not substituted for it. Read-only parsing of the saved solid reaction DAT gives plate/bar root Mx `−82.022/−17.978 N m`, versus resolved native `−84.569/−15.431` distributing and `−84.319/−15.681` rigid. Hence the 3D/native rotation difference accumulates over the free span and grows further in the last quarter near the attachment. The different torque partition can explain part of the span trend, but the fitted solid section, native beam pose, 2 µm clearance taper and local warping are not identical observables/geometries. Neither a pure local-joint cause nor a pure B3-section cause is established. Do not run another finer axial or patch grid from this result.

**Corrected section-axis torque attribution:** The previous paragraph reports moments about the global origin, which combine beam torsion and the eccentric lever arm of root `Fy`. Read-only recovery from the same saved DAT and model coordinates shifts each bar-root reaction wrench to its actual centroid axis: `z=0.085002 m` solid because of the declared 2 µm clearance, `z=0.085 m` native. Section-axis root torsion is `16.80279 N m` solid, `13.70413 N m` native distributing and `13.92594 N m` native rigid. Under the same +100 N m tip load, native therefore transfers roughly `2.88–3.10 N m` more torsion away from the free beam than the solid. At x=`.25/.5/.75 m`, the solid bonded section rotation divided by its own section-axis torque is `0.218459/0.438637/0.658803 µrad/(N m)`, indistinguishable at displayed precision from the saved *detached solid* control `0.218459/0.438638/0.658815`. Native distributing and rigid both give `0.220181/0.440362/0.660543` on that basis. Thus the two beam section laws agree within about `0.8%` per unit moment, and the free-span rotation gap is primarily a *connection torque-partition* difference, not evidence for a B3 torsion defect. Scaling the detached solid's exact tip-work compliance by the bonded solid's section-axis torque predicts `14.837 µrad`; bonded tip work is `17.225 µrad`, leaving about `2.39 µrad` of additional tip/local compliance. This last subtraction is a diagnostic of the finite bonded region and load/warping field, not an isolated constitutive law or direct footprint qualification. Keep the solid clearance and work-coordinate distinctions explicit.

**Next bounded thickness-domain discriminator (prospective):** The existing *plate-only*, same-traction `t=.035 m` study reduced the resolved E4/C3D20R torque-work gap from about `7%` at `t=.07 m` to `2.31%`; this does not by itself qualify a footprint. To distinguish thickness-related plate idealization from connection transfer, retain the same `.1×.1 m` terminal bond, square bar, supports, material, +100 N m tip load and 2 µm tapered clearance, but halve only plate thickness to `.035 m` in both the quadratic solid and locally graded native Q4/B3 model. The beam centroid follows the plate top (`z=.0675 m` at the native straight reference; the solid root has the declared +2 µm lift). Run solid factors 2/4 within the existing 120 s/case limit and native four/eight-cell patch levels within 1,900 rows; verify default `.07 m` deck parity and exact applied wrench first. If the connection torque-partition and local tip-work gaps materially shrink, a footprint-to-thickness domain is plausible and needs further registered acceptance; if they persist, revise the transfer/warping idealization. Any overlap or unconverged reference blocks accuracy scoring. Do not infer a production thickness cutoff from this one added geometry.

**Half-thickness reference execution state:** Source `8897662e` preserves the historical 70 mm factor-4 deck text exactly and passes three direct new geometry/wrench checks. The first 35 mm factor-2 C3D20R run in `f03-ccx-quadratic-terminal-torque-half-plate-dev-20260925-v1` completed CalculiX with exit 0 and saved deck/DAT/STA/FRD, but the runner marked it `EXPLORATORY_FAILURE` because recovery still matched the historical 35 mm *top-surface coordinate* literally. The failed root remains untouched. The parser now derives the top coordinate from the declared plate thickness, with zero-state recovery checks for both half-thickness levels. Recover the saved factor-2 output under the corrected source and execute only the missing factor-4 solid case; do not rerun a completed solver case solely to replace the failed status.

**Half-thickness comparison and next geometry discriminator:** Corrected source `3fbcf3cd` parsed the saved factor-2 output without rerunning the solver (`f03-ccx-quadratic-terminal-half-plate-factor2-derived-20260925-v1`); the new factor-4 solid and native four/eight-cell roots are `f03-ccx-quadratic-terminal-torque-half-plate-factor4-dev-20260925-v1` and `f03-native-terminal-graded-half-plate-dev-20260925-v1`. Solid exact tip-work torque is `49.381→49.519 µrad` (factor 2→4, +0.28%). Native four→eight-cell torque is distributing `46.787→46.822 µrad` and rigid `46.479→46.509 µrad`; each changes under `0.08%`. At 35 mm the solid/native tip gap is about `5.45%` distributing and `6.08%` rigid, versus about `30%` at 70 mm. The factor-4 solid beam-centroid-axis torsion is `55.77054 N m`, native distributing `53.16366` and rigid `52.80797 N m`; correct axis-shifted comparison, not global-origin `Mx`. Scaling the saved detached solid's exact tip-work compliance by that solid section torque predicts about `49.247 µrad`, leaving only `0.272 µrad` additional bonded tip work, versus `2.39 µrad` at 70 mm. This supports a thickness-dependent connection/plate domain but does not establish an admissible cutoff or accuracy: the 35 mm factor-4 nine-by-nine face sample minimum is only `6.37 nm` (factor 2: `14.65 nm`), and deformed-face nonintersection is unproven. Before scoring the apparent improvement, certify the quadratic reference-normal face gap over *entire* saved unbonded face pairs with a bounded Bernstein subdivision. A negative region invalidates this no-contact torque comparison; a nonnegative certificate still needs a separate deformed closest-point check. No new solver run or production law follows from the certificate alone.

**Deformed seam and consistent-load discriminator, 25 September 2026:** Source `927b786d` established nonnegative floating-point reference-normal Bernstein control nets for all 128 saved 35 mm factor-4 faces; this is not a deformed contact proof. A copy of that exact terminal deck with only `*NODE FILE U` added completed under `f03-ccx-half-plate-deformed-seam-dev-20260925-v1`. Its probe displacements are identical to the original; 9×9 samples on all 128 deformed Q8 face pairs, including eight seam faces, have positive corresponding-normal and same-face-projected gaps, minimum `3.2409 nm`, zero negative samples. The nanometre minimum and sampling preclude a nonintersection certificate. Source `e229df21` adds only an opt-in consistent quadratic end-face torsional traction. The historical 35 mm deck remains exactly identical, the new load has exact `100 N m` wrench and conjugate work, and 60/60 focused tests pass. One terminal and one detached factor-4 case completed within the existing 120 s/one-thread envelope under `f03-ccx-half-plate-quadratic-face-{terminal,detached}-dev-20260925-v1`. Consistent-traction terminal tip work is `49.40004 µrad`, versus corner-weighted `49.51935 µrad` (−0.24%); centroid-axis root torque is `55.76977` versus `55.77054 N m` (−0.0014%). Detached free-bar work is `88.10316 µrad` per `100 N m`; scaling by bonded root torque predicts `49.13493 µrad`, leaving `0.26511 µrad` local/tip excess. Thus changing only the physical tip load map does not explain the remaining transfer split or qualify either native footprint. The terminal consistent-load face sample minimum is `6.36 nm`; no continuous deformed contact proof or external shear agreement is claimed. Preserve the 2 µm tapered solid clearance versus straight native axis, corner/consistent load identities, root-centroid wrench shift, and exact work-coordinate distinction.

**Matched-load solid pose and bond-station decision:** Sources `bd5ebd6a` and `1d3f767d` project the saved quadratic solid into a solid-inferred shell mid-surface/director pose and an area-weighted rigid fit of each beam section. The reference projection vanishes below `1.2e-15`; a common finite rigid motion leaves the six-channel and corner gaps below `1e-9` in their respective units, and the focused test passes. The consistent-load solid deck copied with only `*NODE FILE U` completed in `f03-ccx-half-plate-quadratic-face-full-u-dev-20260925-v1`; its probe displacement is identical to the original consistent-load case. At x=1 m versus the whole shell patch x=.9–1 m, the solid-projected distributing gap is `−0.1979 µm` in y, `+5.0815 µrad` in x rotation and `−1.4207 µrad` in yaw; the rigid-corner maximum is `0.4229 µm`. The fitted beam-section RMS residual is `0.0539 µm`, and the consistent end-face torque work coordinate equals its fitted tip twist to displayed precision. The first-order native interface wrench dotted with this projected relative gap is about `−0.2688 mJ`, close in magnitude to the `+0.2578 mJ` solid/native external-work difference; the sign and scale are diagnostic, not a causal identity or exact nonlinear multiplier work. Whole-patch beam-section rotations at x=`.9/.925/.95/.975/1 m` are `44.071/45.164/46.319/47.641/49.400 µrad` against one `44.319 µrad` shell-patch rotation. Centered local shell windows give remaining relative twists `1.177/1.843/2.991 µrad` at the three interior stations. The actual shared bond face is continuous; these nonzero values arise from reducing a deforming 3D plate and bar to six-channel poses. Plate through-thickness shear and beam-section deformation both contribute, increasingly near the loaded end. This rules out selecting the tip-lumped pose tie as a matched finite-bond law, while leaving a distributed physical surface-work candidate open. The protected raw, projection and comparison records are preserved; no contact or production qualification follows.

**Distributed surface-work screen:** Source `8d1d9dda` adds one opt-in six-resultant weak position-work law over the actual `.9–1 m` bond. It integrates E4 top-surface positions and retained native B3 bottom-surface half-cell traces; the first positional moment is normalized by the reference footprint inertia so duals have force/moment meaning. There is no penalty, tip-only pose tie, shell drilling column or equality of shell director and geometric normal. The reference face gap is zero, inertia eigenvalues are `0.0008333/0.0008333/0.0016667 m²`, all six rows are independent, a common rigid motion gives gap below `1.1e-17`, and a vertical displacement proportional to y produces its physical Mx row. The direct bounded four-cell coupled solve passed equilibrium/work checks and gave `50.25964 µrad` under 100 N m. Source-bound four/eight-cell results under `f03-native-distributed-surface-half-plate-dev-20260925-v1` give `50.25964→50.39269 µrad` torque (+0.265%) and `69.03977→69.08738 µm` transverse motion (+0.069%); the finest mechanics error is `1.46e-11`, physical E4 work is positive and its numerical component remains reported. The finest beam-root centroid torsion magnitude is `54.365 N m`, versus `55.770 N m` in the consistent-load solid and `53.164 N m` with the tip-lumped distributing law. The torque tip difference from the solid is about `2.0%`, not an accepted external agreement; the positive-Fz solid overlaps and supplies no shear accuracy score. This is a promising bounded linearized screen, not finite formulation, contact admissibility, true-line stability or G0B acceptance. The focused surface pytest session remains live without a reported result; direct reference/objectivity checks and both coupled solves completed.

**Reverse-shear physical-reference screen:** Source `7f066b94` adds opt-in consistent quadratic end-face Fz loading without changing historical decks; 61/61 focused solid checks pass. The 35 mm, zero-clearance terminal solid under −1000 N Fz completed factors 2/4 under `f03-ccx-half-plate-quadratic-face-reverse-fz-dev-20260925-v1`. Exact work-conjugate tip motions are `69.01650→69.32388 µm` (+0.445%); no sampled reference-normal face point is negative, and all 32/128 quadratic face control nets are nonnegative in floating arithmetic. A copy of factor 4 adding only full displacement output completed under `f03-ccx-half-plate-quadratic-face-reverse-fz-full-u-dev-20260925-v1` with identical probe displacements: all 10,368 sampled deformed corresponding-normal and same-face-projected gaps are positive, minimum `10.274 nm`; no continuous closest-point proof is claimed. The eight-cell sign-reversed native surface-moment response differs in tip motion by `0.341%`, versus `9.09%` for the tip-lumped distributing law. Solid factor-4 plate/beam-root Fz reaction magnitudes are `72.151/927.849 N`; native surface-moment magnitudes are `69.296/930.704 N`, versus `85.377/914.623 N` with tip lumping. The signs differ because the external solid load is reversed to open the unbonded faces; support and connection definitions remain explicit. This gives strong bounded directional shear evidence but is not G0B external acceptance or a contact proof. Stop further external mesh escalation here and advance the finite mechanics of the new candidate.

**Finite distributed-surface mechanics:** The bounded `b3_e4_f03_distributed_surface_finite.py` proof evaluates the same six weak position/moment rows through actual E4 nodal director exponentials and retained B3 half-cell `Context.advance` states. At a nonzero gap (`0.02854` mixed-unit norm) and nonzero physical force/moment multipliers, it includes moving material-frame curvature, shell-director curvature and native B3 cell-frame curvature. The reference gap is below `2.6e-16`; its first derivative reproduces the prior linearized operator to `1.4e-17` in one independent direction. Analytic first and mixed second multiplier-work derivatives differ from two-sided perturbations by `1.64e-10` and `1.53e-9 J`; the mixed term is nontrivial (`0.05635 J` for the declared directions). A common finite rigid motion of all participating patch poses changes the gap by only `2.5e-16`; common rigid virtual work is `-3.2e-15 J`. The deterministic direct test assertion passes. A focused pytest invocation remains active without a reported outcome and is not counted as passed. This proves a bounded chart/work contract, not stability, nonlinear convergence or full G0B acceptance.

**Bounded physical-compliance interpretation:** Source `d95b654a`, with source-bound manifest and raw results under `.qualification/b3-ge-e4-pl/f03-distributed-surface-compliance-dev-20260925-v1`, completed five local Q4 shell-patch/B3 half-cell pairs (patch cells 2/4; beam half-cells 4/8/16) in 33.3 seconds with one BLAS thread. Source `ac937b30` then corrected the reference integration to split at native B3 half-cell as well as shell-host boundaries. Two direct finite-chart assertions pass, including the crossing case. The corrected source-bound comparison is preserved separately under `f03-distributed-surface-compliance-dev-20260925-v2`: four cases are unchanged exactly; at patch4/beam16, the weakest normalized mode moves `0.149022→0.148563` (−0.308%) and no diagonal action changes by more than 0.231%. The linearized six-row surface bond has rank 6 after support elimination. With declared independent action scales of 1000 N and 100 N m, the diagonal-normalized physical-compliance Gram has minimum mode `0.103–0.149`; its first mode is approximately equal and opposite Fy/Mz, not the alternating Fz mode of the exact line. The shell/beam action split was recovered from the actual E4 and retained B3 operators. E4 numerical completion contributes `0.00017–0.00036` to the dimensionless weakest-mode action; the physical E4 component contributes `0.015–0.019` and B3 `0.087–0.132`. Thus this finite mode is not stiffness supplied solely by drilling completion. Compliance skew is below `8.3e-13`. These are support-conditioned local finite-grid diagnostics; the scales and diagonal normalization do not establish a mesh-uniform inf-sup constant, admissible footprint geometry or a production law. The already registered 1:8–8:1 P0/P1/dual line evidence stays separate and unresolved.

**Physical-surface line hypothesis, closed as an immediate choice:** Source `3c239899` generalizes the linearized surface-position/moment trace to fixed material intervals over x=0–1 m, keeps shell/B3 boundary segmentation, and assembles six exact P0 multiplier rows per interval. The direct reference partition check passes. Its source-bound one-thread 2/4/8 interval screen at fixed Q4 x8/y8, B3 half8 or half16, t=35 mm, eccentric axis z=67.5 mm, full shell-left/root support and separate tip torque/shear loads is preserved under `.qualification/b3-ge-e4-pl/f03-surface-resultant-line-dev-20260925-v1`. At beam-half8, 2/4 rows are full rank with positive physical shell work and closed equilibrium, but eight intervals lose seven ranks (41/48); the exact null projector is 98% Fz with a My remainder in raw row coordinates. Refining only the shell x8→16 retains rank 41; refining the beam half8→16 restores rank 48. On that beam-half16 *same physical mesh*, the H^(-1/2)-normalized weakest physical action drops `2.990e-5→5.754e-6→2.107e-7 J` from 2→4→8 intervals. Tip torque rotation drops `48.19→41.88→23.82 µrad` and tip transverse motion `43.38→42.14→34.55 µm`; work, force/moment balance and finite-mode physical shell action remain checked. The action quotient alone does not select a space; its coincident rank and loaded-transfer drift make this repeated-footprint line law unsuitable as the immediate production choice. This does not reject the single footprint or prove that all exact line formulations fail. The classical axial comparator, historical Q6/finite-pad reference and native six-channel coupling remain distinct.

**Why the seven line rows are dependent:** Source-bound derived evidence `.qualification/b3-ge-e4-pl/f03-surface-line-trace-rank-derived-20260925-v1` checks the scalar continuous-P1 stencil and the actual retained E4/B3 reference rows. Over an interval of length `h`, a P1 transverse gap with endpoint values `g_i,g_(i+1)` has mean `(g_i+g_(i+1))/2` and inertia-normalized first moment `(g_(i+1)-g_i)/h`. Eight intervals therefore supply sixteen Fz/My measurements of only nine nodal gap values: exactly seven dependencies. The actual Fz/My submatrix has rank 9/16 and the other four channels have rank 32/32, yielding the observed 41/48. Refining shell x8→16 alone leaves the Fz/My rank 9/16; refining native beam half8→16 gives 16/16 and combined 48/48. The flat-reference symmetry makes shell-director and beam-section rotations unable to add independent mean Fz/axial-first-moment fields at this order. This explains the reference rank failure; it does not establish finite-motion or mesh-uniform stability. A basis swap or solver regularization cannot create the missing reference kinematic dimension.

**Earlier action, retained:** Rigid and distributing footprints remained distinct research idealizations, with neither qualified. Preserve the C3D8 drift, zero-clearance torque overlap, 1 µm face-overlap, first quadratic card failure, clearance-recovery failure and fixture-rejected native screen. No further classical axial or fixed-grid line escalation follows. At source `ae1f2111`, 54 focused solid-deck/audit checks, eight direct plate-patch geometry/load checks and seven graded-operator/traction checks passed. The focused plate-patch pytest and earlier footprint mechanics pytest remain CPU-active without results and are not claimed as passed.

**New evidence index:** Protected roots `.qualification/b3-ge-e4-pl/f03-ccx-quadratic-detached-section-dev-20260925-v{1,2}`, `f03-ccx-quadratic-detached-section-factor4-dev-20260925-v1`, `f03-ccx-quadratic-terminal-reverse-open-dev-20260925-v1`, `f03-ccx-quadratic-terminal-reverse-open-factor4-dev-20260925-v1`, `f03-ccx-quadratic-terminal-torque-gap-dev-20260925-v1`, `f03-ccx-quadratic-terminal-torque-clearance1-dev-20260925-v{1,2}`, `f03-ccx-quadratic-terminal-torque-clearance1-face-dev-20260925-v1`, `f03-ccx-quadratic-terminal-torque-clearance2-dev-20260925-v1`, `f03-ccx-quadratic-terminal-torque-clearance2-face-factor1-2-dev-20260925-v1`, `f03-ccx-quadratic-terminal-torque-clearance2-face-factor4-dev-20260925-v1`, native `f03-native-terminal-shell-resolution-dev-20260925-v{1,2}`, `f03-native-terminal-shell-resolution-partition-dev-20260925-v1`, `f03-native-terminal-shell-resolution-profile-dev-20260925-v1`, and plate-only `f03-plate-only-solid-e4-patch-dev-20260925-v{1,2}`. Every completed external case retains its deck, DAT, solver log, model, hashes and source-bound manifest. Failed roots remain untouched. The external support-partition figures above are a read-only parse of saved DAT files, not a new solver run.

## Previous synthesis retained as historical record

**Decision sought, 25 September 2026:** Select a defensible physical native six-channel beam–shell connection and a stable, adequately resolving exact interface space. The finite square distributing strip and a true bonded line remain distinct idealizations; neither is production-selected. G0B is open, G1 barred, and formal F03 authority unconsumed.

**Established facts:** The 0.1 m square native strip is objective and work-conjugate in bounded Q4/S3 tests; physical shell energy transfers torque and shear without drilling-component work. Across fixed-mesh Fz P0-4→P0-8, a newly isolated *positive physical-compliance* H^(-1) measure falls Q4 `7.672→5.317`, S3 `7.929→5.400`; H^(-1/2) falls Q4 `3.336→1.090`, S3 `3.427→1.099`. In the registered three-level joint axial series the physical Fz H^(-1) values also decline Q4 `11.146→7.346→5.427`, S3 `11.615→7.614→5.526`. The weakest Fz mode alternates and shifts toward beam shear while shell physical-action share falls. The earlier mixed Fz/Mx/My quotient changes much less under H^(-1) because its absolute retained-coordinate action is not the same positive physical compliance. Seven registered beam:shell ratios remain finite and full rank, but this joint trend, a materially intrusive row cap and the absence of a converged physical target prevent multiplier selection. Coarse P1, dual-P1 and beam-window Fz alternatives did not cure the mode or preserve every loaded response.

**Reference interpretation:** The independent RM-plate/Timoshenko-beam square-strip model matches flat geometry, elastic resultants, left-edge/root supports, strip dimensions and separate 100 N m / 1000 N loads, but evaluates only a linearized three-channel trace; its missing in-plane rigid-footprint rows prevent a six-channel ranking. At fixed plate x8/y4 and P0-8, changing its beam spline 8→16 moves shell support Fz `1138.2→1185.4 N` and torque reaction `−39.67→−42.76 N m`; this finer-line endpoint is not a settled oracle. The conforming full-length C3D8 plate/square-bar bond at factor 4 gives `12.565 µrad` under `100 N m` and `17.627 µm` under `1000 N`, with factor-2 values `10.770 µrad` and `14.047 µm`; it is a different full-bond law and is not mesh settled. The executed C3D8 terminal-only bond uses the same last-0.1 m patch, plate left-edge/bar-root supports, centroid `z=.085 m` and exact tip-load work as the native terminal test. Its factor-2→4 torque and force coordinates still change `14.106→15.980 µrad` and `27.355→36.538 µm`. The deliberately unbonded coincident surfaces overlap under positive Fz by up to `5.045 µm` at sampled midspan points, so that no-contact result is physically inadmissible in that direction. A separate reversed-Fz solve gives positive reference-normal opening at every matching unbonded node on factors 1/2/4 (minimum `0.625/0.352/0.158 µm`, 12/40/144 pairs) and identical linear work-coordinate magnitudes to the positive-load runs. It is a directional open-interface shear comparator, not a converged accuracy target or a torque comparator. The executed B31/S4 knot is a separate rigid footprint; classical axial and historical Q6/finite-pad references remain distinct. No comparator here qualifies the native six-channel weak line.

**Remaining uncertainty and next discriminating work:** The native rigid and distributing last-0.1 m footprints pass bounded finite-chart, physical-wrench and linearized global balance checks yet yield distinct responses. The reverse-Fz solid result establishes a nonoverlapping direction, but factor-2→4 shear displacement changes by `33.6%`. A matched detached C3D8 bar control changes `39.9%` in Fz and `4.0%` in Mx over the same factor-2→4 meshes, while terminal-bond Mx changes `13.3%`; free-bar shear resolution is already insufficient and plate/connection effects still matter for torque. The positive-Fz no-contact state overlaps; an opt-in hard-mortar contact screen fails at the first solver iteration when contact faces reach the shared-bond seam. A trimmed contact face set executes but leaves an untreated interval and reports no active contact records. An independently assembled classical membrane/RM-plate/Timoshenko-beam six-channel terminal model preserves separate rigid and distributing responses at three modest resolutions, with full row rank and closed work; it is not a converged E4/B3 or external accuracy oracle. Native B3 half-cells 4→8→16 on the same E4 panel change both footprint work coordinates only at roundoff. A matched-wrench shell-only screen at fixed patch/supports shows a `12.62%` E4 distributing/rigid torque-compliance difference versus `2.91%` in the independent RM plate at the finer tested level; Fz law differences are `0.091%` and `0.027%`. Numerical E4 shell work is negligible. This localizes a substantial part of the torque distinction to physical shell/footprint work, without identifying an accurate law or proving convergence of either shell discretization. The earlier bounded nonzero-physical-shear field has zero distributing gap but a nonzero rigid-corner gap: the laws intentionally admit different shell deformation, so identical resultants need not produce identical work. No drilling-component work is needed. Use a section-resolved, nonpenetrating 3D torque/shear reference to assess which idealization represents the declared physical connection; do not repeat B3 half-cell, shell-thickness or classical axial screens without a new decision question. The immediate transverse-order/line-resolution diagnosis is already complete: bare B3 is stable while coupled P0 line8→16 changes torque/tip-z `−17.3%/−10.5%`; P1/dual are more beam-resolution-sensitive, and shell-only rank is deficient for the finer rows. Do not repeat those screens. Keep the required true-line law separate, then assess its pose and multiplier space under the registered ratios with a justified dual norm and physical modes. The current one-axis Fz decline cannot establish or refute a mesh-uniform inf-sup bound. Do not extend classical axial refinement or use a smaller gap or quotient alone as a decision.

**Resulting action:** Retain rigid and distributing finite-width footprints as distinct, explicitly selected engineering idealizations: rigid constrains the patch corner positions, while distributing transfers resultant work and admits the tested local shell shear. The six-channel independent and matched-wrench shell-only screens support that distinction but do not rank physical accuracy. Admit the reverse-Fz no-contact solid only as an open-interface directional shear diagnostic; its current C3D8 mesh is not a converged comparator. Preserve the positive-Fz overlap and full-extent hard-mortar failure. Require mesh-settled, nonpenetrating physical torque/shear evidence before either footprint can be qualified for the first application. Keep the required nonmatching true-line route separate and open. Stop P0 row caps, coarse P1-Fz, coarse dual-Fz, the simple beam-window trace and further classical axial or fixed-grid line escalation as space-selection routes. No connection or multiplier space is production-selected; G0B remains open and G1 barred.

**Latest bounded evidence:** Source `f597e0fd`; 38 focused deck/recovery checks passed. Three pinned CalculiX 2.23 reverse-Fz cases completed under `.qualification/b3-ge-e4-pl/f03-ccx-solid-terminal-reverse-open-dev-20260925-v1` with hash-bound manifests, decks, DAT, logs and all-paired-node opening audits. The minimum reference-normal gaps are positive as above; maximum gaps are `2.947/5.826/8.148 µm`. Work-coordinate magnitudes equal the saved forward linear solutions exactly at recorded precision. The reference-normal audit uses corresponding nodes on matching bilinear faces; it does not solve closest-point contact and does not establish mesh convergence or native accuracy. The earlier CPU-active tests were left running.

**Detached section control:** Source `c920946f`; 44 focused checks passed. Six pinned CalculiX 2.23 cases under `.qualification/b3-ge-e4-pl/f03-ccx-solid-detached-section-dev-20260925-v1` use exactly the terminal solid bar mesh, root support and tip-force/couple work, but duplicate every plate/bar interface node. All complete with bounded wrench errors. Free-bar +100 Nm Mx work coordinates are `74.286/83.347/86.704 µrad` for factors 1/2/4, versus the declared square Saint-Venant beam value `88.072 µrad`. Free-bar +1000 N Fz coordinates are `55.597/117.379/164.185 µm`, versus the declared B3 Timoshenko value `192.024 µm`. These are different 3D and beam idealizations, but the large free-bar shear mesh drift independently bars an accuracy inference from the current terminal-solid Fz series. Do not promote either native footprint from this comparison.

**Six-channel terminal comparator:** Source `9bdd31a5` produced historical `.qualification/b3-ge-e4-pl/f03-independent-terminal-six-channel-dev-20260925-v1`. Source `5844f5c9` aligns independent patch yaw to the native mean-curl contract; eight direct focused checks, including independently integrated native/independent yaw-row parity, passed. The corrected v2 screen under `.qualification/b3-ge-e4-pl/f03-independent-terminal-six-channel-dev-20260925-v2` separately assembles Q4 membrane, spline RM plate, planar/transverse Timoshenko beam and linearized six-channel terminal work. At resolutions 2/3/4, distributing versus rigid +100 Nm tip-rx is `10.646/10.921/11.350` versus `8.815/10.302/10.209 µrad`; +1000 N tip-z is `43.813/43.734/44.412` versus `42.801/43.723/43.859 µm`. All 12 systems have full row rank and small equation, gap and work errors. The yaw correction does not materially change these symmetric loads; the independent rigid torque still moves with model resolution. The initial pytest invocation remains CPU-active without a result and is not claimed as a pass. Agreement in direction with the native distinction is not accuracy qualification.

**Fixed-panel native beam check:** Source `b3fe108e`; immutable development root `.qualification/b3-ge-e4-pl/f03-native-terminal-beam-resolution-dev-20260925-v1`. Q4 x4/y4 E4 panel, terminal patch, supports, section and tip loads are fixed while native B3 half-cells vary 4/8/16. Distributing +100 Nm tip-rx is `11.55266746731 µrad` at all three to reported precision, rigid `8.56342077041 µrad`; distributing +1000 N tip-z is `44.25675761351 µm`, rigid `43.17439231856 µm`. Work and global balance remain small. This rules out beam half-cell resolution as the cause of the bounded native footprint difference, not shell/connection accuracy.

**Matched-wrench shell work:** Source `7c36897c`; raw manifest/results under `.qualification/b3-ge-e4-pl/f03-terminal-shell-work-dev-20260925-v1`. On matched Q4 shell x/y divisions 2 and 4, the exact same patch, left clamp, +100 Nm Mx and +1000 N Fz resultants are applied through the distributing director/mean law or the rigid corner-position law. At level 4, native E4 shell-only work is `0.001355886/0.001203922 J` (distributing/rigid torque) and `0.161097983/0.160952101 J` (Fz); independent RM plate work is `0.001328036/0.001290531 J` and `0.162693991/0.162649404 J`. All eight solves have the declared wrench, closed equilibrium/work, conservative native tangent and negligible nonphysical E4 energy. The torque-law relative differences are `12.62%` native versus `2.91%` independent, and remain positive at level 2 (`16.22%` versus `1.70%`). This is a shell/footprint work discriminator, not a converged accuracy comparison or a production selection.

**Current bounded evidence and check:** Native Fz-only source `c724e68b` and joint-run source `3e9a472b` bind raw manifests/results under the worktree `.qualification/b3-ge-e4-pl/f03-native-own-transverse-mode-dev-20260925-v2` and `f03-native-joint-fz-physical-dev-20260925-v1`. Both use a positive Schur-eliminated physical stiffness, no retained Fz constraint columns, the Neumann H^(-1/2)/H^(-1) Gram enclosures, and recovered native B3 bending/shear work. On the fixed mesh, Q4/S3 Fz beam-shear shares rise about `16→62%`; shell physical-action shares fall Q4 `53.5→9.2%`, S3 `56.5→6.8%`. In the one-axis joint series, beam-shear shares rise about `5→62%`. These are Level-A finite-dimensional diagnostics, not the registered interface-stability acceptance. A direct independent three-channel `solve(8,4,nb,m,origin='strip',director='strip',multiplier='p0',basis='spline',strip_half_length=.05,strip_half_width=.05)` check with `nb=8,16`, `m=4,8`, and separate `1000 N`/`100 N m` loads gave P0-8 tip-z `48.686→49.027 µm`, tip-rx `12.558→12.882 µrad`, shell support Fz `1138.2→1185.4 N`, and support Mx `−39.67→−42.76 N m`. At P0-4 its tip-z and tip-rx change only `50.583→50.602 µm` and `15.539→15.568 µrad`. This beam-only change rules out treating the P0-8 spline8 response as a quantitative oracle. The previously launched focused pytest session remains running; no pass is claimed for it.

**Support, offset, section and work control (development only):** Sources `15542c1d`, `3827d43c`, `5851e9c8`, `f20bea50` and `1cca1c96` separate the changes. Four executed CalculiX 2.23 cases each for left-edge-only and left-edge-plus-bar-root supports retain decks, DAT/STA/FRD, source/executable hashes and parsed results under worktree `.qualification/b3-ge-e4-pl/f03-ccx-solid-{left-support,left-root}-dev-20260925-v1`; 24/24 focused solid-deck/recovery tests pass after the local-field extensions. On the factor-4 solid, plate perimeter→left edge→left edge plus bar root changes the *exact work-conjugate* end torque coordinate `5.833→14.896→12.565 µrad`, and force coordinate `0.866→118.638→17.627 µm`. The work coordinates were recomputed from the preserved hash-checked DAT displacement and the exact applied nodal force vectors; the prior unweighted rigid-section fit is not the conjugate observable. Its `~0.18 µm` maximum torsional section-fit residual confirms nonrigid local motion. In the same declared native root/left support and square strip, moving the beam axis from `z=0` to the solid centroid `z=.085 m` changes Q4 torque `13.305→10.247 µrad` and tip-z `46.644→18.985 µm`. Replacing only native generalized polar `J=1.66667e-5 m⁴` with the Fourier-series square-bar Saint-Venant `J=1.40577e-5 m⁴` changes its torque to `10.904 µrad` and leaves tip-z unchanged; native S3 gives `10.861 µrad` and `19.541 µm`. Raw native section-control manifest/results are in `f03-native-square-section-dev-20260925-v1`. The square torsion value follows the rectangular torsion convention in [Oasys GSA theory](https://docs.oasys-software.com/structural/gsa/references-theory/rectangular-sections/); it is an explicit diagnostic material choice, not a change to the qualified generalized section. The new native fixture test remains running and no pass is claimed. The solid factor-2→4 work coordinates still change `10.770→12.565 µrad` and `14.047→17.627 µm`, so stop at this bounded support/section audit; do not score apparent cross-model proximity as accuracy.

**Local bond kinematics (development only):** Sources `5f1c7ae0` and `4a7d0d4e`; the derivation at worktree `.qualification/b3-ge-e4-pl/f03-ccx-solid-local-fields-dev-20260925-v1` reads only four saved left/root DAT files after SHA-256 checks and records full station fields. No CalculiX solve was repeated. The fitted beam-section pose extrapolated `0.05 m` to the shared face is an approximation; the actual solid interface is pointwise continuous by shared nodes. Under `100 N m` torque on factor 4, the shared-face `∂u_z/∂y` minus fitted section `rx` is `−0.0017 µrad` at x=`.5 m` but `−3.469 µrad` at the loaded end, `27.8%` of the latter's `12.488 µrad` fitted twist. The factor-2 loaded-end difference is `−2.663 µrad`, so it is not a demonstrated mesh-vanishing error. Under `1000 N` transverse force, the midspan plate-top geometric `∂u_z/∂x` plus fitted beam `ry` is `+0.514 µrad` at factor 4 (`+0.352 µrad` at factor 2); this is a kinematic shear indicator, not a measured E4 director shear or interface gap. The shared-face mean minus extrapolated fitted-section translation has norm at most `0.035 µm` among these factor-4 load/station records. These observations favor keeping rigid and distributing footprint laws distinct and preserving admissible transverse shear. They do not select a law or settle the solid mesh.

**Matched local footprint work (development only):** Corrected source `b661295b`; raw manifest/results in worktree `.qualification/b3-ge-e4-pl/f03-local-rigid-distributing-dev-20260925-v2`. The preserved V1 used opposite shell-side My signs and is not the paired-wrench comparator. Both laws use the actual Q4/S3 x8/y4 shell pose maps, the same native retained B3 nodal pose at x=`.5 m`, axis `z=.085 m`, square Saint-Venant torsion section, and a `.1×.1 m` material patch. The distributing map uses one six-channel area-mean/polar pose; the rigid comparator ties four corner *positions* to one beam pose through twelve rows. Supported ranks are `6/6` and `12/12`; common rigid-motion gaps are below `3e-18`. A left-edge-supported shell field with nonzero positive **physical** transverse-shear energy has distributing gap below `4e-20` but rigid-corner gap norm `0.0010016 m`. Both corrected virtual multipliers deliver `+100 N m My` to the shell within `6e-13 N m`; on the declared field, distributing work is zero and rigid work `−0.99375 J`. Neither shell force vector uses a drilling coordinate. The rigid patch intentionally restrains local shear; the distributing patch retains it. This is a local linearized row-space/work proof, not a full line, nonlinear footprint, or production stability result.

**Finite rigid-patch chart and physical wrench (development only):** Sources `9ab7c8f0` and `60e95d2c`; the source-bound V4 manifest/results are in worktree `.qualification/b3-ge-e4-pl/f03-local-rigid-distributing-dev-20260925-v4`. V3 precedes physical-wrench recovery and remains preserved. On the same Q4/S3 `.1×.1 m` patch, at a deformed configuration and nonzero `+100 N m My` virtual multiplier, the rigid law has mixed curvature `−0.0318436 J` in the selected chart directions. Its independent four-point finite-difference error is `3.95e-8 J` for Q4 and `4.91e-9 J` for S3; first-variation error is below `2.9e-10 J`. A common finite rigid motion changes work and gaps by less than `5.6e-14`. Recovered physical wrenches balance force exactly to display precision, moment within `1.5e-13 N m`, and directional work within `9e-16 J`. Two direct focused checks passed; the normal pytest invocation remains running, so no pytest pass is claimed. This check is local and does not qualify a full rigid footprint, a distributing footprint or a true line.

**Finite distributing-patch chart (development only):** Source `67590b81` broadens only the diagnostic point-work composition to the native nodal pose port and checks the actual E4 area-mean/polar strip through both charts. Source-bound V5 results are in `.qualification/b3-ge-e4-pl/f03-local-rigid-distributing-dev-20260925-v5`; V4 remains historical. With nonzero mixed physical multipliers, Q4/S3 first-variation errors are `3.37e-9/4.44e-9 J` and mixed-Hessian errors are `1.34e-9/2.64e-9 J` against independent finite differences. Four direct focused checks passed, including two existing point-port cases. This is local derivative evidence, not full finite-patch force recovery, termination or line-space stability.

**Distributing wrench and loaded termination (development only):** Source `d13b21f3` adds explicit finite-patch spatial force/moment and directional-work recovery; source `4b921cf2` adds a small dense linearized Q4/S3 native retained B3 KKT at a separately declared `x=[.9,1.0] m`, `y=±.05 m` patch ending at the beam tip `x=1 m`. Versioned V6 and V7 source-bound results remain under `.qualification/b3-ge-e4-pl/f03-local-rigid-distributing-dev-20260925-v{6,7}`. Q4/S3 finite distributing wrench imbalance is at most `1.8e-15 N m` for moment and zero to display precision for force and directional work. At the terminal patch both reference gaps vanish, supported row ranks are `6/6` distributing and `12/12` rigid, and both transfer `+100 N m` shell My within `2.3e-12 N m`. Under separate `+100 N m` tip Mx / `+1000 N` tip Fz, Q4 distributing versus rigid tip responses are `11.553/8.563 µrad` and `44.257/43.174 µm`; S3 gives `11.626/9.902 µrad` and `44.341/43.426 µm`. Free equilibrium residuals are below `9e-13` scaled, gaps below `2.5e-20`, work error below `5.5e-14 J`, global force/moment balances below `1.4e-10` in the declared SI units. Four direct focused checks passed. These are different, internally consistent idealizations on one bounded linearized mesh, not physical-accuracy, nonlinear, full-footprint or true-line acceptance.

**Matched terminal solid screen and physical admissibility (development only):** Source `7b736111` added an opt-in conforming C3D8 bond only over `x=[.9,1.0] m` while duplicating coincident plate/bar nodes elsewhere; source `00d6bee2` makes the unbonded normal separation explicit. The four historical full-bond left/root decks at factors 2/4 remain line-for-line identical after newline normalization. Thirty direct focused deck/recovery checks passed. The pinned CalculiX 2.23 executable completed six factor-1/2/4 terminal torque/shear cases with raw decks, DAT/STA/FRD, logs, source/executable hashes and parsed work under `.qualification/b3-ge-e4-pl/f03-ccx-solid-terminal-dev-20260925-v{1,2}`. A hash-checked reparse of those saved outputs, without rerunning CalculiX, is in `f03-ccx-solid-terminal-separation-derived-20260925-v1`. Exact work-conjugate torque is `10.508→14.106→15.980 µrad` and transverse displacement `14.366→27.355→36.538 µm`; factor-2→4 changes are still about `13.3%` and `33.6%`. At the unbonded midspan, bar-bottom minus plate-top normal displacement is negative under Fz at all three factors, reaching `−5.045 µm` at factor 4, and under torque on one patch edge reaches `−8.691 nm`. These are sampled penetrations of initially coincident surfaces in a model with no contact law. The terminal solid output is preserved as a mathematical diagnostic, not used for physical accuracy or multiplier selection. Contact-aware external analysis would be a reference-only diagnostic; it would not add product contact scope.

**Hard-mortar external-reference screen (development only):** Source `5ed78763` added an opt-in external-only CalculiX `TYPE=MORTAR` hard contact over the unbonded C3D8 faces, without a penalty or `ADJUST`; the historical decks remain unchanged. Four new direct contact/legacy deck checks passed. The pinned factor-1 torque smoke under `.qualification/b3-ge-e4-pl/f03-ccx-solid-terminal-mortar-dev-20260925-v1` exits `201` during its first stiffness calculation, without a completed step. A hash-bound copy removing only `*CONTACT PRINT` also exits `201` (`f03-ccx-solid-terminal-mortar-no-print-dev-20260925-v1`). Removing the x=`.75–.9 m` contact-face column adjacent to the shared-bond seam lets the torque case finish, both without printing (`f03-ccx-solid-terminal-mortar-trim-seam-dev-20260925-v1`) and with printing (`f03-ccx-solid-terminal-mortar-trim-seam-print-dev-20260925-v1`); the analogous transverse case also finishes (`f03-ccx-solid-terminal-mortar-fz-trim-seam-dev-20260925-v1`). This implicates the seam-edge arrangement but does not prove a CalculiX defect or validate contact: the trimmed decks leave an untreated unbonded interval, their contact print gives `CNUM=0` with no `CDIS/CSTR` records, and only sampled nodal separation was recovered. These controlled outcomes are preserved; no physical comparison or formulation failure is inferred from them. CalculiX 2.22 documentation identifies MORTAR as the 3D static dual-multiplier contact route and omission of `*SURFACE BEHAVIOR` as its hard-contact convention; that published convention is not itself evidence that this 2.23 deck executes correctly. [Official manual](https://www.dhondt.de/ccx_2.22.pdf)

**Current dual-basis evidence:** Sources `34438195`, `a0dc6de8`, `8b289147`; exact coarse-beam P1 biorthogonality, resultant and first moment pass; 5 focused basis tests had passed before the action-split addition. Dual norm moments agree with independent quadrature to `2.1e-16`; lower Gram is positive and tail enclosure is nonnegative to floating roundoff. Q4/S3 loaded and mode raw records are under the worktree `.qualification/b3-ge-e4-pl/f03-dualfz-p0mx-{fixed,modes}-dev-20260925-v1`, with mode action split in `f03-dualfz-p0mx-modes-dev-20260925-v2`. A broad rerun is not implied by these development screens.

**Current beam-window evidence:** Source `427dab20`; the first `f03-beam-window-fixed-dev-20260925-v1` invocation stopped at a NumPy block-layout error before a mechanics result and remains preserved. Corrected `f03-beam-window-fixed-dev-20260925-v2` ran both Q4/S3 cases at fixed shell x8/y4, beam-half16, Fz P0-4/Mx P0-8, separate 100 N m/1000 N loads. Rows remain rank 28/28, window partition and first moment are within `1.2e-16`; Q4/S3 torque tip rotations stay `13.3047/13.3031 µrad`. Shear tip-z moves `46.644→46.791 µm` (Q4), `48.695→48.838 µm` (S3); shell support Fz moves only `1672.82→1674.53 N`, `1527.20→1527.94 N`. The H^(-1) quotients also decrease slightly `4.075→4.058`, `4.824→4.806`. This is a linearized Fz diagnostic only; no nonlinear six-channel law was asserted.

**Current saved-mode mechanics evidence:** Sources `a0cd390c`, `253ecc2a`, `8955d7a1`; raw roots in the worktree `.qualification/b3-ge-e4-pl/` are `f03-saved-fz-beam-energy-dev-20260925-v1`, `f03-native-saved-fz-energy-dev-20260925-v1`, and `f03-saved-fz-beam-resolution-dev-20260925-v1`. All reuse hash-bound four/eight-row independent weak vectors. Native section-recovered bending/shear work agrees with its retained algebraic action to `4e-16` relative and equilibrium to `1.4e-16`. Beam-only spline8 assembly reproduces the earlier saved action. One bounded beam-only spline8→16 change at unchanged load profiles raises eight-row H^(-1) action `0.742e-9→2.515e-9` (native `1.888e-9`); four-row action changes only `1.589e-9→1.598e-9` (native `1.515e-9`). These are diagnostic nonconvergence observations, not a new reference convergence claim or multiplier acceptance.

**25 September force-space decision batch (development only):** On the
fixed independent square-strip plate x16/y4, beam8 grid, changing Fz
P0-4→P0-8 reduces the H^(-1/2) quotient
`3.229e-5→6.686e-6` and the plausible finite-width H^(-1) quotient
`7.000e-5→3.285e-5`; the weakest vector alternates three→seven times
under either norm. H^(-1) changes the decline but does not remove it.
These quotients use that independent model's physical energy and are not
numerically interchangeable with the native retained-system quotient.
On the H^(-1) weak mode, the shell/beam portions of physical action change
from `67.6/32.4%` at four rows to `31.3/68.7%` at eight. Thus fixed-area
shell averaging is not the sole explanation; the near-beam-resolution
force mode matters. Raw roots:
`f03-finite-strip-dual-norm-dev-20260925-v1` and
`f03-independent-fz-action-decomposition-dev-20260925-v1`.

A bounded two-beam-element macroforce-row rule changed only three of the
seven already registered beam:shell ratios; the other four reused the
preserved controls. In six new Q4/S3 cases, combined rows remain full
rank and the H^(-1/2) quotient rises from `2.30–4.12` to `3.93–9.73`.
Torque response is unchanged to `0.02%`, but transverse tip response
changes by `5.52–15.03%` and shell support Fz by `129–220 N` on the same
physical meshes and loads. This rejects the simple cap as a physical
transfer policy despite its favorable finite-mode diagnostic. Raw root:
`f03-native-macroforce-ratio-dev-20260925-v1` (records bind each
unchanged prior control by path and SHA-256).

Source `879bbd85` adds a bounded exact weak-work/KKT oracle with a
separate basis for each physical channel; uniform P0 reproduces the old
reference rows under a known permutation. A candidate with Fz continuous
P1 on four cells, Mx P0 on eight, and other channels P0 on four passes
36/36 affected strip tests, including Q4/S3 nonlinear first/mixed chart
variations and reference-row parity. On the fixed Q4/S3 x8/y4,
beam-half16 mesh, its torque remains `13.305/13.303 µrad`. Tip-z is
`46.248/48.434 µm`, between coarse P0 `46.644/48.695` and fully fine
P0 `45.771/47.517 µm`. But shell support Fz becomes
`1728.74/1588.07 N`, farther from the fine-P0 `1597.05/1392.55 N`
than coarse P0 `1672.82/1527.20 N`. The finite H^(-1/2) transverse
quotient is `2.120/2.473`, below coarse P0 `2.584/2.750` and above fine
P0 about `1.07/1.08`; the weakest mode remains about 99% Fz with four
sign reversals. Rows are full rank, work and balance close, and physical
shell energy is positive. None of these comparators is a converged
external target; the combined evidence gives no basis to select this
space. Raw roots: `f03-p1fz-p0mx-fixed-dev-20260925-v1` and
`f03-p1fz-p0mx-modes-dev-20260925-v1`.

**25 September position, Fz-row and matched-reference decision batch
(development only):** Source `f81e0e41` adds the centerline-position,
finite-area-orientation diagnostic to the existing nonlinear weak work.
The 32 focused strip tests passed, including Q4/S3 actual-chart first and
mixed derivatives, reference rows, objectivity and shear preservation.
On fixed shell x8/y4, beam-half16, coarse4/Mx8, centerline position
changes Q4 torque from `13.304673` to `13.304673 µrad` and tip-z force
response from `46.644` to `47.224 µm`; S3 torque changes
`13.303163→13.307360 µrad` and tip-z `48.695→49.156 µm`. The bounded
H^(-1/2) transverse quotient changes only `2.584→2.600` (Q4) and
`2.750→2.78` (S3); the weakest mode remains approximately 94–96% Fz.
This rejects position averaging as the explanation for the Fz mode,
without rejecting the finite-width pose itself. Raw root:
`f03-native-hybrid-line-origin-dev-20260925-v1`. Its first invocation
failed at Python import before physics evaluation because the checkout
was absent from `PYTHONPATH`; the corrected single-thread invocation
completed and the failed invocation is retained in the run history.

On the *same final* shell x16/y4, beam-half16, Mx16 mesh, coarsening
other channel rows from eight to four (including Fz) raises the finite
transverse quotient from `1.087→2.84` for Q4 and `1.110→2.95` for S3.
All combined rows remain full rank; Q4 shell-only rank is `31/36` and
S3 `36/36`. Torque changes less than 0.1%, while tip-z changes from
`48.591→49.820 µm` (Q4) and `49.252→50.687 µm` (S3). Physical shell
energy stays positive, the numerical shell energy remains zero and work
balances close. This supports Fz overresolution as a *fixed-grid*
explanation, not an accepted row cap, physical response, or inf-sup
proof. Raw root: `f03-native-fixed-grid-fz-row-dev-20260925-v1`.

Source `9bc0a7fb` lets the existing independent RM-plate/Timoshenko-beam
operator use the same square strip; its 16 tests passed. The paired
reference uses plate `[-.5,1.5]×[-.5,.5] m`, `t=.07 m`, the same
`E,ν,GJ,EI,GAs`, left-edge/root constraints, no offset, and separate
`100 Nm` torque / `1000 N` transverse-force tip loads. The independent
trace is the linearized z/rx/ry subset, not the native six-channel
operator. At P0-4 the independent/native Q4/S3 torque tip rotations are
`15.54/15.69/15.73 µrad`; at P0-8 they are
`12.56/13.30/13.30 µrad`. Corresponding tip-z responses are
`50.58/46.64/48.70 µm` and `48.69/45.77/47.52 µm`. Shell support
torque under the torque load at P0-4 is `-56.25/-57.79/-57.13 Nm`,
but at P0-8 is `-39.67/-47.36/-45.93 Nm`. Work and global balance pass.
The common row-resolution trend is independently reproduced, but the
finer-line response/reaction split is not a settled physical oracle.
Raw root: `f03-square-independent-transverse-dev-20260925-v1`.
The C3D8 solid deck separately fixes the full plate perimeter and has
a solid square-bar torsion law rather than the native generalized
`GJ` section; its results cannot be scored against this pair as if their
boundary-value problems matched. No new C3D8 refinement is authorized
by this result.

The independent square-strip spline operator then examined *one fixed*
plate x16/y4, beam8 grid with Fz P0-4 versus P0-8. Its Fz-only
H^(-1/2) action has full row rank but the weakest mode changes from
three to seven sign reversals, and its smallest normalized action drops
by a factor of about `4.8` (`3.229e-5→6.686e-6` in that model's own
energy scale). Under `1000 N` transverse force, independent tip-z moves
`51.014→49.369 µm`. These numbers are not directly comparable to the
native quotient scale, but the direction and mode character agree with
the native fixed-grid result. This makes a native-only assembly error
less likely and confirms that row density alone cannot choose the
multiplier. Raw root:
`f03-independent-fz-trace-image-dev-20260925-v1`.

**25 September native square-strip and stability screen (development
only):** The new `physical_strip_005_005` port uses a fixed 0.1 x 0.1 m
reference area centered at each line station. For affine shears its
reference polar yaw is `+gamma/2` or `-gamma/2`, with no shell `rz`
work. Loaded Q4/S3 torque and transverse-force cases have positive
directly evaluated physical shell energy, zero numerical shell-component
energy, and small global work/wrench errors; the external solid model has
different supports, section and material idealization, so the loaded
displacements are not paired accuracy comparisons. With Q4/S3 shell
x8/y4 fixed, P0 line intervals 4→8 and native beam half-cells 4/8/16,
the reference Neumann H^(-1/2) transverse quotient changes respectively
`1.293→0.0075`, `2.300→0.415`, `2.584→1.071` for Q4 and
`1.579→0.0927`, `2.483→0.436`, `2.750→1.079` for S3. At line8 the
weakest mode is >99.95% Fz in that dual norm and has seven sign changes.
Complete rows remain full rank. At beam-half16/line8, doubling shell x8
to x16 restores Q4 shell-only rank 42/48→48/48 but changes its quotient
only 1.071→1.087; S3 changes 1.079→1.110. Thus shell-x resolution alone
does not resolve the mode. These are bounded absolute-energy algorithmic
diagnostics including E4 numerical completion, not a continuum inf-sup
constant or multiplier selection. Immutable exploratory records and
runner identities are under
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-native-square-modes-dev-20260925-v3`
and `-v4`; the import-failed `-v1` and earlier L2-only `-v2` remain
preserved. Focused new mechanics checks pass 11/11; the pre-existing
affected weak-line and strip suite passed 87/87 before the dual-norm
addition.

**Three-space comparison on the same square-strip model:** With Q4/S3
shell x8/y4, native beam-half16 and line intervals 4→8, the H^(-1/2)
transverse quotients are P0 `2.584→1.071` / `2.750→1.079`,
continuous P1 `2.257→1.114` / `2.586→1.120`, and dual P1
`2.302→1.116` / `2.608→1.123`. Each eight-interval weakest mode is
>99.97% Fz and alternates at every coefficient; all combined row sets
are full rank. Q4 shell-only rank is 42/48 for P0 and 42/54 for each
P1 variant at this resolution. The analytic spectral-tail Gram enclosure
is at most `5.1e-7` relative for these dual cases. Near-equal P1/dual
quotients give no evidence that a basis swap solves the interface mode;
none of the quotients is a mesh-uniform inf-sup proof. The eight raw
three-space outputs, source/dependency identities and limits are in
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-native-square-spaces-dev-20260925-v1`.
The affected strip and dual-norm tests pass 40/40.

**Ratio-cap decision:** A provisional P0 policy of line intervals
`min(shell axial elements/2, native beam elements)` was screened on
Q4/S3 beam:shell ratios 1:8 through 8:1. All fourteen finite systems
have full shell-only, beam-only and combined row rank, and the bounded
H^(-1/2) transverse quotient is at least 2.300. All 28 torque/shear
loaded cases have positive physical shell energy, zero directly evaluated
numerical shell-component energy, and small work and wrench-balance
errors. Those findings alone cannot validate the cap: varying meshes
confounds the broad tip-response spread, and fixed-mesh controls expose
underresolution. With Q4/S3 shell x8/y4 and native beam-half4, line2→4
reduces torque tip twist by `22.61%/22.56%`; with beam-half16,
line4→8 reduces it by `15.19%/15.46%`. The corresponding transverse-tip
changes are `4.00%/3.48%` and `1.87%/2.42%`. The cap therefore gives
a favorable finite-mode screen at the cost of a material torque response
change. It is rejected as a qualification policy, not proof that every
finite-width bond formulation fails. Raw immutable development records
are in `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/` under
`f03-native-square-ratios-dev-20260925-v1`,
`f03-native-square-ratio-loads-dev-20260925-v1` and
`f03-native-square-fixed-line-dev-20260925-v1`.

**Mixed-channel decision and terminal joint series:** Exact P0 row
composition with coarse Fz/Fx/Fy/My/Mz and twice-resolved Mx reproduces
the fully refined torque twist on fixed Q4/S3 x8/y4 beam-half16 to the
reported precision; Fz-only refinement does not change torque materially.
The bounded nonlinear multiplier potential, first/mixed variations through
actual E4/B3 charts, reference Jacobian and constant Mx work pass focused
checks. In fourteen 1:8–8:1 ratio cases, combined rows are full rank,
the H^(-1/2) transverse quotient is at least 2.300, physical shell energy
is positive, numerical shell-component energy is zero, and work/balance
errors are small. Q4 shell-only rank is 27/28 at shell x8/beam-half16;
doubling shell x restores 28/28 but changes torque/shear responses by
3.3%/6.8%. The predeclared three-level *axial-only* joint series at
beam:shell element ratio 1:2 shows Q4 quotient `3.348→2.300→1.087`,
torque twist `15.354→13.305→12.537 µrad`; S3 quotient
`4.197→2.483→1.110`, torque twist `15.387→13.303→11.831 µrad`.
The final weakest mode is >99.95% Fz. Those results trigger the declared
stop rule: no more refinement of this candidate under this diagnostic.
They are not proof of general formulation failure. Raw records are under
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/` in
`f03-native-square-channel-split-dev-20260925-v2`,
`f03-native-square-channel-modes-dev-20260925-v1`,
`f03-native-square-mixed-ratios-dev-20260925-v1`,
`f03-native-square-mixed-q4-shell-refine-dev-20260925-v1`, and
`f03-native-square-mixed-joint-dev-20260925-v1`. The earlier `-v1`
channel-split runner syntax failure is retained. The affected mechanical
suite passed 118/118 after the split load route, and the nonlinear split
work suite passed 26/26.

**25 September bounded physical-bond screen (development only):** The
conforming 3D model is a 2.0 x 1.0 x 0.07 m plate with a 1.0 x 0.1 x
0.1 m square stiffener bonded by common nodes at the plate top. It uses
isotropic E=210 GPa, nu=0.3, free stiffener ends and declared plate-edge
affine shear or fixed edges with a 100 Nm end torque / 1000 N transverse
force. There is no beam/shell MPC, numerical drilling term or reference
offset. On mesh factors 1/2/4, the two shear cases give, respectively,
local square-patch yaw `0.679/0.674/0.675` and
`-0.321/-0.326/-0.329` times gamma; solid midsection fitted yaw
`0.757/0.775/0.789` and `-0.243/-0.225/-0.220` times gamma, with
about 2 micrometres maximum section-fit residual. The line tangent gives
`0.998/0.994/0.991` and `-0.002/-0.006/-0.015` times gamma. The
torque tip twist is `2.697/4.524/5.752` microrad and transverse-force
tip displacement `0.298/0.602/0.864` micrometres. Applied and support
wrenches balance to print precision, but the latter responses remain
materially mesh-dependent. These are distinct solid and native
idealizations, so the yaw contrast informs the connection choice but is
not native accuracy or continuum convergence. Raw records and file hashes
are in `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/` under
`f03-ccx-solid-bond-shear-dev-20260925-v3`,
`f03-ccx-solid-bond-shear-dev-20260925-v4`,
`f03-ccx-solid-bond-loads-dev-20260925-v1` and
`f03-ccx-solid-bond-loads-dev-20260925-v2`. The earlier
`f03-ccx-solid-bond-shear-dev-20260925-v1` input-format failure and
`-v2` elongated-patch response are retained, not overwritten.

**Bounded 25 September diagnosis (development only):** For the chord,
`uy=γx` gives yaw `γ`, `ux=γy` gives zero; the strip gives `+γ/2` and
`−γ/2`, while the affine-patch rigid fit gives `0.43057γ` and
`−0.56943γ`. The fit is not a solved weld. Quadrature orders 2–5 agree
within `2.2e-16`. At fixed shell x8/y4, beam-half16, line intervals
4→8 reduce the work-scaled transverse `Fz/Mx/My` quotient for P0/P1/dual
from `0.761/0.666/0.694` to `0.203/0.230/0.231` on Q4 and from
`0.812/0.769/0.788` to `0.203/0.231/0.232` on S3. All 12 six-channel
row sets have full rank; at eight intervals the weakest transverse mode
has >99.98% `Fz` L2 share. Direct and exactly retained-condensed actions
agree within `4.3e-12` relative. These finite-model quotients include E4
numerical completion and do not establish continuum inf-sup or choose a
production space. The 12 direct single-thread diagnostic results are in
the task trace; this summary is not a registered or immutable gate record.

**25 September external reference advance (development only):** The
*knot-corrected* CalculiX B31/S4 four-point rigid-footprint model already
has separately accepted narrow rigid-mode, tip-translation work and
reciprocal support-wrench screens. This corrects any impression that the
original canary's failed reaction interpretation still applies to that
new model. It remains a finite rigid footprint, not the native six-channel
weak line; its B31 square-section torsion law has not been shown to equal
the native generalized `J=1.6666667e-5 m^4` law. A new four-corner
least-squares recovery passes synthetic six-motion and nonrigid controls.
On the preserved `+1000 N` tip-y loaded baseline it recovers center
translation `uy=1.81986e-5 m`, matching the previously recovered corner
mean, but the maximum rigid-fit corner residual is `1.3546e-7 m`.
The initial inference that this residual makes fitted twist non-conjugate
was too strong. In the pinned CalculiX 2.23 `gen3dforc.f`
(`4585a7c0…`) the tip moment loads a `MEANROTBS` angle; `usermpc.f`
(`d37704bb…`) forms that angle from mean tangential corner motion.
For this symmetric four-corner section, the source formula equals the
least-squares fitted rotation on each axis even for nonrigid corner
motion. An independent source-formula calculation reproduces saved
`rx=-1.9522285e-6 rad`, and a synthetic nonrigid parity test passes.
This establishes the *external model's* linear tip-rotation work map,
not a native comparison, physical section match or rigid section field.
The focused parser/deck tests pass 33/33. The signed tip-`Mx` execution
below uses this same knot footprint. The original canary and its failed
reaction interpretation remain separate.

**Executed signed knot-footprint torque screen, 25 September 2026:** The
frozen source `0994b542` generated two otherwise identical CalculiX 2.23
decks with `Mx=±100 N m`. Both exited zero with one full accepted linear
step, the expected knot, and finite DAT/FRD responses within the 120 s,
one-thread envelope. The source-conjugate four-corner mean twist is
`±3.931475e-5 rad`, signed oddness is zero at printed precision, and
maximum rigid-fit corner residual is `3.54e-12 m`. Reusing the 24
previously executed, hash-checked same-model unloaded support influences
gives for positive torque shell wrench about origin
`(Fy,Mx,Mz)=(-298.0665 N,-64.34595 N m,-74.5682 N m)` and beam-root
wrench `(298.066 N,-5.84742 N m,74.56845 N m)`. Including the beam-root
`0.1 m` lever arm gives total reaction moment `Mx=-99.99997 N m`.
Normalized total force/moment discrepancies are `5e-6/2.5e-6` at the
available external print precision. They exceed the registered G0
`1e-8` balance default: **this is not acceptance**. The raw signed
decks/logs/FRDs and source-bound manifest are retained in
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-ccx-knot-mx-dev-20260925-v1/`;
manifest/result/reciprocal hashes begin `3fe2c3b4/d5214efb/0f34c72d`.
This confirms a bounded external *rigid-footprint* torque route; it does
not decide the native weak-line law, match the native generalized torsion
section, or close F03/G0B. Stop repeating this external screen. Next
compare a section- and connection-matched finite footprint, while the
line-versus-footprint decision uses the declared shear/termination
discriminator above.

**Native rigid-footprint junction comparison, 25 September 2026:** A
bounded native nodal pose port now uses the actual shared B3 position and
nodal frame, with owned outputs and actual-chart variations. In a bare
16-half-cell B3 under `+100 N m` tip torque, left cell, shared node and
right cell twists at `x=.5 m` are respectively
`34.8214286/37.1428571/39.4642857 µrad`; position is continuous but
the one-sided frames differ by `4.6428571 µrad`. Thus using either
half-cell port for a point footprint at that junction would silently
change the connection. The nodal port and translated `z=.1 m` native
fixture retain local operator parity.

A bounded Q4/S3 E4-PL plus retained B3 linear KKT now ties the same four
shell material nodes to that nodal pose. Its twelve virgin translation
constraint rows agree exactly with the CalculiX knot footprint's declared
rows after numbering, including the `0.1 m` eccentricity. Actual-chart
finite differences, reference gaps and physical work pass. For Q4,
native B3 half-cell counts 4→16 give the same `+100 N m` tip twist
`40.2288853 µrad`, shell support `Mx=-87.1762134 N m` and beam-root
`Fy=+45.1524914 N` to reported precision. S3 at half-cell 4 gives
`40.3504420 µrad`. All have scaled equilibrium, compatibility, total
wrench and quadratic-work closure; the focused port/footprint suite passed
19/19. The Q4 native result differs from the external rigid-footprint
twist `39.31475 µrad` and shell support `Mx=-64.34595 N m`. Identical
constraint rows and native half-cell invariance rule out row-sign or
native-beam-resolution explanations on this fixture. B31 versus B3
section/torsion and S4 versus E4 shell operators remain different, so
these are not accepted cross-solver errors or a native weak-line decision.
Stop refining this torque fixture; make the next physical comparison
section- and connection-matched and retain the registered
shear/termination discriminator. F03 authority remains unconsumed,
G0B open and G1 barred.

**Previous bounded chord and strip observations (preserved):** The first fixed chord is not a
strictly local attachment: a P0 tip yaw multiplier on `[.75,1]` acts at a
shell sample beyond the declared beam end. On the aligned Q4 x8/y4 test,
its last yaw row has coefficient `−0.2` at shell `x=1.25 m`, or `16.7%`
of that row's absolute shell-`uy` coefficients. The finite strip likewise
has outboard work, as expected from its explicitly finite footprint;
the prior zero-width local polar law does not. The sample is physical
outboard support, not merely a nonmatching FE shape node.

**Bounded correction and interpretation:** A separate *confined* chord
samples shell positions at `x_−=.6s`, `x_+=.4+.6s` for `s∈[0,1] m`.
Its fixed `0.40 m` gauge has two moving sample maps, stays inside the
declared attachment, and avoids the point atom introduced by simply
clipping one end to `x=0` or `x=1`. Its integrated linear weak law uses
shifted H1 displacement traces; no continuum claim is made for an
individual point pose or the full nonlinear law. Q4/S3 constrained
reference rows now have zero shell work outside `[0,1]` on the aligned
diagnostic meshes. On fixed Q4 x8/y4, beam-8, P0-4, native yaw changes
`3.905→3.881 µrad`; the independent confined value is `3.677 µrad`.
Transverse force and beam-axis torque responses are unchanged to the
reported precision on Q4 and S3. The native P0-4/P0-8 transverse
algorithmic quotient remains `0.678/0.080`; confinement does not repair
line-resolution sensitivity or select P0. Rigid motion, finite-chart
derivatives, nonzero-multiplier point/weak work, eccentricity, loaded
balance and the termination-support check pass bounded Q4/S3 tests.
The confined Q4/S3 reference constraint agrees across Gauss orders 2–5
to at most `2.2e-16` relative on the small segmented case; this rules
out under-integration as the source of its observed response difference.

**Resolved affine-patch kinematic comparator:** For a `0.20×0.23 m`
half-size rectangle and `γ=.01`, the least-squares rigid rotation of the
*given* affine displacement field is `+.004305705` rad for `uy=γx` and
`−.005694295` rad for `ux=γy`. Independent five-point area quadrature
matches `γ a²/(a²+b²)` and `−γ b²/(a²+b²)` exactly at displayed precision.
The gradient-polar strip gives `±.005` rad, while the line tangent gives
`+.01/0` rad. This distinguishes three kinematic reductions; the rigid
fit is not a solved rigid-footprint boundary-value problem, and none is
yet the qualified physical weld reference. The finite strip is best kept
as a distributing-footprint candidate until its law is reviewed. It is
distinct from the already registered F04 distributing functional and its
evidence; the rigid footprint needs its own region constraint and work
functional.

**Remaining uncertainty and next discriminator:** Confinement corrects
where the law acts, but the chord still aligns beam yaw with the shell
line tangent. Under homogeneous in-plane shear that differs by a factor
of two from an area-polar finite-width bond and can constrain native
beam shear. Before treating this as the required *bonded* six-channel
line, use a section-resolved shear/terminated-stiffener reference with
the same geometry, supports, section axes and load work to determine
which rotation is physically intended. If the resolved bond follows
area-polar rotation, keep the confined tangent law as a separately
declared idealization and advance the finite footprint for full-pose
bonding; if tangent alignment is the intended line law, qualify its
shear restriction, curved/rotated reference and mesh-ratio/interface
modes. The prior CalculiX S4/B31 collocation route is preserved as failed
within its 120 s envelope and is not reused as a matched reference.
Formal F03 authority remains unconsumed, G0B open and G1 barred.

**Current state, 25 September 2026 — decision sought:** Determine whether a
declared zero-transverse-width *line-tangent/director* bond can represent
the required nonmatching six-channel line, or whether physical full-pose
bonding needs a finite footprint. A fixed `0.20 m` half-chord on the shell
material line avoids the local polar pose's unbounded normal-gradient yaw:
its *integrated linear weak law* uses shifted displacement traces, which
are bounded by the shell H1 trace norm for a fixed nonzero chord. The
individual point pose is not claimed H1-continuous. This candidate is
distinct from the finite `0.20×0.23 m` half-width strip, classical axial
comparator and historical Q6/finite-pad reference.

**Established development facts:** The chord port passes Q4/S3 rigid-motion,
actual-chart first/mixed-second, eccentric point and weak-line work, shear
preservation and loaded balance checks without a shell `rz` contribution.
On fixed Q4 x8/y4, beam-8, P0-4, native/independent tip yaw is
`3.905/3.713 µrad`, transverse tip z `47.809/50.865 µm` and beam-axis
torsion `16.179/15.636 µrad`; S3 follows the same trends. These are
matched bounded elastic diagnostics, not qualification. Pure in-plane
shear exposes the decisive model distinction: for `uy=γx`, chord yaw is
`γ` while area-polar strip yaw is `γ/2`; for `ux=γy`, chord yaw is zero
while strip yaw is `−γ/2`. Therefore neither may be substituted for the
other or called the canonical bond without a physical connection choice.

**Interface and next action:** Exact retained-coordinate decomposition
agrees with the full signed native interface action to about `2.3e-12`;
the reduced physical stiffness is positive on the bounded cases. All
tested P0/P1/dual six-channel rows are independent, yet Q4 P0 transverse
`Fz/Mx/My` algorithmic quotient drops `2.74→0.678→0.080` for line
intervals 2→4→8 at fixed shell-8/beam-8. Its fine mode is almost pure
alternating `Fz`, while the overall weakest mode is axial. Beam-16 raises
the P0-8 transverse value to `0.203`; at P0-4/beam-16, shell x-intervals
2→4→8 give `0.729/0.809/0.761`. These are finite-model, E4-completion-
inclusive norm diagnostics, not continuum inf-sup or a space selection.
Next compare the *declared physical shear and termination meaning* of the
line-tangent law with a resolved reference, then run the required ratio and
mode qualification only for a mechanically defensible law. If the desired
bond requires area-polar yaw, retain the strip as a footprint candidate
and make the line-scope decision explicit; do not relabel it. No further
classical axial refinement is justified by this batch. Formal F03 authority
remains unconsumed, G0B open and G1 barred.

**Checks:** New chord pose cases passed `4/4`, loaded/weak cases `2/2`,
mode decomposition `1/1`, shear distinction `2/2`, eccentric point cases
`8/8`, independent chord case `1/1`, and selected segmented weak-line
mixed-derivative cases `4/4` by direct single-thread invocation. Existing
rail/local cases were included. The focused pytest runner remained
CPU-active without output for about two minutes and was stopped; it is
incomplete, not a pass. No product source or protected evidence changed.

**Current decision, 25 September 2026:** Keep the strict zero-width
six-channel line unselected. A distinct finite `0.20 m` longitudinal by
`0.23 m` transverse *half-width* material strip now has objective Q4/S3
pose work, physical yaw from area-mean gradients, and independently matched
elastic yaw/torque/shear responses. This supports further finite-footprint
development, not substitution for the required line. At fixed Q4 x8/y4,
P0-4 and beam-8, native/independent strip tip yaw is `3.860/3.663 µrad`;
native Q4/S3/independent tip torsion under `100 Nm` is
`14.410/14.668/14.635 µrad`. Under `1000 N` transverse force, tip z is
`43.740/45.758/46.885 µm`. All three balance work and global loads; these
are bounded development comparisons, not qualification.

**Remaining uncertainty and next discriminator:** The strip does not settle
multiplier stability, all six coupled channels, or whether a genuinely
zero-width yaw law is possible without an unbounded shell gradient trace.
At fixed shell/beam x8/8, P0-2→P0-4 changes native strip yaw
`6.409→3.860 µrad`, while beam-8→16 at P0-4 changes it only
`3.860→3.744 µrad`; the independent model has the same pattern. P1/dual
give still smaller yaw but neither small weak gaps nor the three-channel
spectral quotient selects them. Its weakest normalized mode is axial, not
yaw. The next mechanics slice must compare an energy-continuous, declared
line law with the finite-footprint interpretation and assess norm-scaled
six-channel rank, interface modes, mesh ratios, work and physical response.
If no true line law survives, retain the footprint candidate and surface
the required scope decision explicitly; do not quietly rename the strip a
line. Do not run another finer classical axial refinement absent a new
decision-relevant hypothesis. G0B remains open, G1 barred and formal F03
execution authority unconsumed.

**Bounded transverse diagnosis:** On Q4 x8/y4, native beam-8 and fixed
strip, P0-2→P0-4→P0-8 changes tip z under `1000 N` from
`46.857→43.740→42.021 µm` and tip rx under `100 Nm` from
`18.977→14.410→11.467 µrad`; the independently assembled physical
plate/beam model changes `49.974→46.885→44.335 µm` and
`19.219→14.635→11.371 µrad`. S3 follows the same ordering. Native Q4/S3
reference constraint matrices at Gauss orders 2–5 agree to about `3e-16`
relative, so quadrature order does not explain this spread. No numerical
shell completion energy appears in these transverse cases. This is a
line-resolution sensitivity in the finite-strip diagnostic, not evidence
that the finer answer is more physical or that P0 is stable. Full native
six-channel norm-scaled modes, mesh ratios and convergence remain open.

**Current checks:** The new finite-strip tests pass `8/8` by direct
single-thread invocation; previous independent transverse and yaw tests
pass `12/12` and `5/5`, and two new independent strip mean/load/yaw checks
pass `2/2`.
The focused pytest process produced no output for about two minutes and was
stopped; it is incomplete, not a pass. All nine changed Python files parsed
successfully; `compileall` could not write this checkout's protected
`__pycache__` files. No product or frozen evidence changed.

**Latest decision, 25 September 2026:** The local polar-frame pose restores
yaw work, and a physically matched independent membrane/beam model follows
the native yaw and transverse torque/shear trends. Line resolution remains
the dominant yaw sensitivity; changing beam resolution or removing E4
numerical completion has a much smaller effect. A C1 boundary-layer
witness gives fixed zero-width yaw with physical shell energy tending to
zero. Independent mechanics review confirmed the continuum trace issue. The
next decision is whether the strict zero-width six-channel line needs a
different energy-continuous pose or a declared finite-width connection.
No multiplier is selected. Keep classical axial, historical Q6/finite-pad
and native six-channel claims distinct. Formal F03 authority remains
unconsumed, G0B open and G1 barred.

**New bounded evidence (development only):** Independent/native Q4 tip yaw
on joint shell/beam/P0-line levels x4/y2/4/2, x8/y4/8/4 and x16/y8/16/8
is `6.197/6.810`, `3.730/3.958`, `2.330/2.485 µrad`. Both support moments
approach about `−98 Nm`. The independent physical H^(-1/2) minimum quotient
falls `1.029→0.578→0.343`, but its minimum mode is axial; the yaw-only
lower quotient falls `684.5→276.2→136.5`. These finite-dimensional values
do not prove locking or select a line space. At fixed Q4 x8/y4/P0-4,
native B3 element counts 2→4→8 give yaw `4.334→3.958→3.844 µrad`;
P0-2→P0-4 at fixed beam changes yaw by about 39%. Q4 P0/P1/dual yaw is
`3.958/2.528/2.241 µrad`, S3 `3.922/2.492/2.195 µrad` on the matched
fixed case; the independent model has the same ordering. Smaller gaps do
not establish accuracy. Q4 native/independent transverse tip z is
`47.81/50.86 µm` and beam-axis torque tip rx `16.18/15.64 µrad`; S3 gives
`49.77/50.86 µm` and `16.10/15.64 µrad`. Removing E4 numerical
completion in a native-beam/physical-shell in-plane solve changes yaw by
only 0.2–0.3% across Q4/S3 and P0/P1/dual.

For the supported C1 field `ux=A(x+0.5)d φ(y/d)`, `uy=0`,
`φ(t)=t(1−t²)²` on `|t|≤1`, centerline yaw is `−A/2` while physical
membrane energy is `O(d)`. At `A=1e−4` and widths `0.2,0.1,0.05,0.025 m`,
yaw is always `−5e−5 rad` and energies are
`12.348,6.138,3.065,1.532 J`. This challenges a strict zero-width
normal-gradient trace, not a finite-width strip. The required full mesh
ratios, six-channel stability, mixed meshes and formal acceptance remain
outstanding. Earlier sections below are preserved as historical decisions.

**Independent mechanics check:** A separate read-only reviewer confirmed
that the C1 boundary-layer witness makes the strict zero-width normal-gradient
yaw unbounded against physical H1 membrane energy. Even a constant P0
moment multiplier detects the fixed yaw. This is a continuum trace objection
to this local-frame candidate, not proof of a discrete KKT failure or a
programme-level impossibility. A finite-width alternative must average
gradients over area or use suitable displacement traces/differences; merely
sampling a point gradient on another zero-width line retains the defect.
Width and connection meaning must be explicit, with no reliance on drilling
completion. The next bounded derivation should test a physical finite-width
strip connection for yaw plus local director/shear, without longitudinal
averaging zeros. Candidate work/derivatives and independent physical response
must pass before a multiplier-space selection or formal F03 assessment.

**Checks and reproduction:** Run
`python -m scripts.b3_e4_f03_local_frame_joint_screen` with optional
`--spaces`, `--transverse`, `--beam-ratio` or `--physical-only` for the
bounded comparisons. The new independent-yaw module also has a direct CLI.
Its first three focused pytest checks passed `3/3`. After adding the native
physical-only and boundary-layer assertions, a pytest invocation remained
CPU-active without output for over ten minutes and was stopped as an
incomplete check, not counted as a pass. All five test functions then passed
by direct single-thread invocation in 5.3 s. No product or frozen evidence
was changed.

**Prospective next bounded experiment:** Define a distinct centered material
strip with explicit half-length `0.20 m` and half-width `0.23 m`. Integrate
position, physical director and both material gradients over its *area*;
use their polar frame for six-channel pose work. This tests whether a
finite physical support removes the zero-width trace objection without
borrowing drilling stiffness or suppressing admissible director shear.
Passage through reference consistency, rigid motion, actual-chart first/
second variations and the boundary-layer witness would warrant a later
loaded weak-line and physical-resolution study. Failure would return to
the pose functional. This is a footprint/strip candidate, not a substitute
for the required nonmatching line or a multiplier-space decision.

**Strip pose check:** The fixed `0.20×0.23 m` half-width area mean passes
Q4/S3 exact host coverage, rigid motion, actual-chart first/mixed-second
variations, reference six-channel work, and independent director shear.
The loaded native P0 small case has positive physical shell energy and
global moment/work balance. It strongly attenuates the earlier 0.4 m yaw
wave because the declared *longitudinal footprint* filters that wavelength;
this is a physical footprint property, not evidence for a zero-width line.
The next discriminator is a physically matched independent area-average
plate/beam yaw response. Agreement would justify later strip-resolution and
multiplier work; disagreement would send the pose or section mapping back
for correction. No multiplier or connection type is qualified by these checks.

**Current decision-oriented investigation, 25 September 2026:** Decide
whether the local polar-frame line can advance to a formal interface-space
assessment. The measured yaw sensitivity may come from under-resolved physical
membrane bending/shear, the weak multiplier space, or shell numerical energy.
The next bounded check compares the same flat geometry, full left-edge support,
100 Nm tip yaw moment, generalized beam section and local centerline pose
against an independently assembled in-plane membrane/Timoshenko Ritz model at
two line resolutions. If the response and resolution trend agree, advance the
norm-scaled P0/P1/dual and mesh-ratio assessment; if they differ materially,
diagnose the constitutive/trace or stabilization source before selection. This
is exploratory Level A work, not acceptance. Existing F03 authority and all
G0B criteria remain unchanged.

**Next bounded discriminator:** On the same physical Q4 panel/beam/line
family, jointly increase shell x/y, beam and P0 line resolution through
`(4,2,4,2)`, `(8,4,8,4)`, `(16,8,16,8)` in `(shell-x, shell-y,
beam-half-cell, line-interval)` counts. The independent model uses its own
rooted spline counts at the same physical resolutions. This distinguishes a
fixed-primal trace saturation from a persistent joint-refinement problem.
A leveling physical response with noncollapsing properly scaled interface
stability would support formal space comparison; continuing drift or a
vanishing stability measure would require revisiting the trace/space before
selection. The three-channel independent norm cannot qualify the native
six-channel mixed saddle system by itself.

**Joint-resolution result and next question:** The three physical levels
give independent/native tip yaw in µrad `6.197/6.810`, `3.730/3.958`,
`2.330/2.485`. Shell support Mz approaches about `−98 Nm` in both; native
numerical shell-energy fraction rises `3.5→4.4→6.0%`. The independent
physical H^(-1/2) minimum quotient falls `1.029→0.578→0.343`, but its
minimum mode is axial, as in historical native diagnostics. The yaw-only
lower quotient is `684.5→276.2→136.5`; the L2-based quotient also falls.
These finite-dimensional values do not prove locking, a continuum inf-sup
failure, or a suitable line space. The next fixed-physical-mesh comparison
puts P0, continuous P1 and dual P1 under the same yaw couple on Q4/S3.
If P1/dual yield identical primal states, treat dual as a basis change,
not a resolution cure; if they differ, inspect basis/integration parity.
Compare physical response, numerical energy and balance alongside algebraic
rank, then decide whether to revise pose/interface resolution or prepare a
formal stability assessment. Do not add further axial refinement by default.

**Next mesh-ratio discriminator:** Keep Q4 shell x8/y4, P0 interval count
four, geometry, supports and tip yaw couple fixed. Vary native B3 element
count `2,4,8` (half-cell count `4,8,16`) and independent spline beam count
the same half-cell values. If the yaw response barely changes, the large
P0 line-resolution effect is not a beam-discretization artifact and work
should concentrate on shell trace/interface policy. If it changes strongly,
inspect beam station interpolation and line segmentation before judging the
multiplier. This diagnostic covers beam:shell ratios 1:2, 1:1 and 2:1;
the required 1:4, 1:8 and reciprocals remain formal G0B work.

**Current state and decision, 25 September 2026 (policy 2026-09-24.2):**
The bounded local-material-frame candidate now takes shell position and
physical director at the actual line point and obtains yaw from the polar
fit of one-sided Q4/S3 material tangents. It removes the *fixed*
longitudinal averaging zeros found in the earlier rail and local-director
variants. Common rigid motion, actual finite-chart first/second variations,
reference tangent, weak-line work, explicit C0 host splitting and admissible
transverse shear pass focused checks. It is still only a G0 candidate:
the 0.4 m yaw wave remains substantially under-resolved on the tested
mesh, fixed-mesh P0 line refinement changes loaded yaw rotation about 38%,
and 4.9–5.7% of loaded yaw shell energy is from the existing numerical
component. Positive physical energy and correct moment balance do not by
themselves establish a stable or physically accurate bond. Next obtain an
independent physical yaw/torque/shear reference with matching section,
geometry, supports and connection meaning; study the numerical-energy
partition and norm-scaled interface response under registered joint
refinement and required mesh ratios. Do not select the pose or multiplier
space before mechanics review and G0B acceptance. Keep classical axial,
historical Q6/finite-pad and native six-channel evidence separate. Formal
F03 authority remains unconsumed, G0B open and G1 barred.

**Bounded local-frame evidence, 25 September 2026:** The local reference
yaw is `0.5(∂uy/∂x−∂ux/∂y)` and has no numerical drilling column; director
tilt is interpolated independently of the shell surface normal. Q4 and
S3 x16/y8 give `0.681` of the exact local-polar virtual work for the
previously cancelled 0.4 m in-plane wave; the earlier finite rail gave
approximately zero. The local candidate's x4→x8→x16 ratios are
`0.033→0.213→0.681`, so this is recovery of a continuum local-work
channel, not mesh convergence. A common rigid-motion patch is exact to
`7e-17`; finite first/mixed-second variations and the flat-reference
trace agree with independent differences on Q4/S3. One-sided C0 tangent
jumps are explicit; the weak integral splits at center-line host edges,
including odd shell grids.

For a 100 Nm beam-tip yaw couple on Q4 x16/y8, beam8, P0 line intervals
2→4, the local-frame tip yaw is `6.676→4.141 µrad`, shell support moment
`−111.146→−98.822 Nm`, and numerical shell-energy fraction
`5.15→4.86%`. S3 gives `6.644→4.102 µrad`,
`−111.429→−99.074 Nm`, and `5.45→5.68%`. The physical shell energy is
positive; actual interface and support moments agree within `4e-11 Nm`,
global moment balance within `4e-11 Nm`, and energy-work closure is at
roundoff in these runs. These small residuals do not settle resolution,
stabilization sensitivity or external physical agreement. The affected
five-file mechanics suite passed `140/140`; a subsequent odd-grid
segmentation regression passed `1/1`. All work remains exploratory;
defaults, product source, frozen evidence and scientific criteria are
unchanged.

**Earlier checkpoint, 25 September 2026:**
The fixed-longitudinal-width four-sample frame cannot yet be accepted as
the *local bonded-line* shell pose. Its flat-reference director transfer
has gain `cos(0.2k)` for a director wave of wavenumber `k`, and its yaw
transfer contains a `sin(0.2k)/(0.2k)` factor for a tangential in-plane
wave. Both have
finite physical-wavelength zeros. Q4 and S3 checks find positive physical
shell energy but nearly zero corresponding line virtual work, with no
numerical drilling contribution to the director case. This is a pose-map
work issue, not proof of a global instability. A finite footprint may
legitimately have nonlocal averaging, but that is a separately declared
connection law. A bounded local-material-point/director alternative
removes the director zero and passes actual-chart work/derivative checks;
its inherited yaw fit still has the second zero. Thus it is also not a
selected six-channel line law. P0, P1 and dual-space resolution questions
remain independent and open. Next derive a genuinely local objective
six-channel shell orientation from the physical director and admissible
material tangents, resolve Q4/S3 boundary and transverse-shear behavior,
then repeat loaded work, norm-scaled stability and required mesh ratios.
Preserve the matched torque/shear reference and obtain independent mechanics
review before selection. Formal F03 authority is unconsumed, G0B open and
G1 barred.

**Bounded pose-map evidence, 25 September 2026:** The original four-sample
map uses x offsets `±0.2 m` and y offsets `±0.23 m`. For an imposed
physical director rotation `rx=A sin(2.5πx)` (wavelength `0.8 m`), its
director trace is `[rx(s−a)+rx(s+a)]/2` with `a=0.2 m`, hence gain
`cos(ka)=0`. For an in-plane field `uy=A sin(kx)` with no `ux`, the
four-sample fit's yaw is
`a[uy(s+a)−uy(s−a)]/[2(a²+b²)]`, where `b=0.23 m`.
Its gain relative to the local gradient `∂uy/∂x` is
`[a²/(a²+b²)] sin(ka)/(ka)`; the local infinitesimal polar spin for this
field is half that gradient. Both conventions have the same zero at
`ka=π`. The earlier shorthand `sinc` refers to `sin(ka)/(ka)`.
On Q4 and S3 x16/y8 with director amplitude `A=1e-4 rad`,
the integrated line torque-work ratio relative to the local physical
director is `−0.0001815`; both shells have positive physical energy
(Q4 `20.724 J`, S3 `11.384 J`) and zero numerical shell-component energy.
The added local-director variant gives a `0.9235` work ratio on this mesh,
while retaining the four-sample in-plane yaw fit. For a tangential
displacement `uy=(1e-4/5π) sin(5πx)` (wavelength `0.4 m`), that yaw fit
has analytic sinc gain zero and measured local-spin work ratio `−0.0007781`
on both topologies, again with positive physical membrane energy.
The Q4/S3 x4→x8→x16 trace responses move toward the analytic director
transfer, so the cancellation is not cured by shell refinement.

The existing weak-line oracle now admits the local-director diagnostic
without changing its defaults. It retains local position and physical
director, the existing proper-fit yaw, exact reference consistency and
owned first/second derivatives. At Q4 x16/y8, beam8, P0 intervals 2→4,
native local-director torque tip rotation is `21.132→17.159 µrad` and
independent spline plate/beam is `20.826→16.699 µrad`; native transverse
tip is `53.756→51.481 µm` and independent is `54.031→51.621 µm`.
Native S3 gives `21.096→17.003 µrad` and `54.169→51.912 µm`.
Q4/S3 loaded shell numerical energy is zero and work/equilibrium residuals
are small. The local-director alternative improves one work contract but
does not remove fixed-mesh line sensitivity or the yaw blind mode; none of
these bounded comparisons qualifies a multiplier or external agreement.
The affected existing and new mechanics tests passed `88/88`, followed by
`8/8` focused local-director checks after the yaw regression test was added.

**Earlier checkpoint, 24 September 2026 (policy 2026-09-24.2):**
Keep the finite-width shell director/center material line as the native
development candidate; do not select a multiplier space. On a fixed beam
and P0 line, Q4 shell refinement brings the independently assembled
Reissner–Mindlin/Timoshenko transverse tip response close to the native
response, while a remaining reaction-partition difference is unresolved.
At fixed refined shell and beam, doubling P0 line intervals changes
torque rotation about 23% in *both* formulations. Continuous P1 and
dual-linear candidates also remain line-sensitive. Full row rank and
small work residuals therefore do not establish interface stability.
For nested P0/P1 spaces, a smaller tip compliance after adding weak
constraints is expected on a fixed elastic mesh; the observed drop is
unresolved resolution sensitivity, not by itself instability.
The decision sought is a physically stable native six-channel connection,
not another classical axial digit. Next distinguish line-space/interface
resolution from a shell-trace or physical-reference mismatch using a
section-, geometry-, support-, and load-matched torque/shear reference and
a norm-scaled, physically interpreted mesh-ratio study. If physical
quantities stabilize over joint refinement and the required ratios,
advance the selected candidate to formal F03 review; otherwise revise the
trace, interface space, or resolution policy. Keep the classical axial and
historical Q6/finite-pad evidence separate. Formal F03 authority remains
unconsumed; G0B remains open and G1 barred.

**Bounded torque/shear decision evidence (same date):** Source branch
`97d70e24`; diagnostic scripts are from this worktree. Python 3.14.2,
NumPy 2.4.6, SciPy 1.17.1 imported `anysolver` from the main checkout;
`git diff main HEAD` lists only B2 files under `src/anysolver`, so the B3/E4
operators used here are unchanged. These are unregistered developmental
diagnostics, not installed-artifact or external qualification. Both models
use the flat x=[−0.5,1.5], y=[−0.5,0.5] panel, clamped left shell edge,
rooted beam, E=210 GPa, nu=0.3, t=0.07 m, matching declared generalized
beam stiffnesses, a center material-line pose, 100 Nm beam-tip torque or
1000 N beam-tip transverse force, and exact weak line constraints. The
independent model uses a spline plate/beam basis and is not an identical
discrete E4/native-B3 operator or an external solver.

At eight native beam half-cells and two P0 intervals, the native-minus-
independent relative differences were:

| Q4 shell x/y cells | Torque tip rotation | Torque shell reaction | Transverse tip displacement | Transverse shell reaction |
|---|---:|---:|---:|---:|
| 4/2 | −1.45% | −0.05% | −25.52% | +40.90% |
| 8/2 | −0.59% | +0.09% | −6.83% | +11.60% |
| 16/2 | −0.31% | +0.09% | −2.51% | +4.93% |
| 16/4 | +0.05% | +1.51% | −1.00% | +2.79% |
| 16/8 | −0.66% | +0.79% | −0.63% | +2.41% |

On x16/y8, beam8, P0 intervals 2→4, native torque tip rotation changed
18.795→14.438 microrad and independent changed 18.920→14.534 microrad;
native transverse tip changed 51.382→48.852 micrometres and independent
51.707→49.019 micrometres. Shell torque reactions changed −56.725→−53.148
Nm native and −56.278→−52.431 Nm independent; transverse shell reactions
changed 1556.24→1407.38 N native and 1519.64→1346.56 N independent.
Native six-channel rows were full rank for both P0 resolutions (12/12 and
24/24) in the complete, shell-only, and beam-only matrices. These ranks
are algebraic diagnostics, not norm-scaled inf-sup constants.

On that fixed native mesh, continuous P1 torque tip rotation changed
15.139→12.543 microrad and dual-linear changed 13.937→12.348 microrad
for line intervals 2→4; corresponding transverse tips changed
49.497→47.573 and 49.093→47.823 micrometres. The independently
assembled continuous-P1 model changed torque 15.037→11.892 microrad and
transverse tip 49.193→45.926 micrometres. All solves had small equilibrium
and energy-work residuals. Neither candidate is selected from these
fixed-mesh differences. The reciprocal coarse-mesh probe also found that
an x2-shell/beam8 pairing differs strongly in transverse response while
an x16-shell/beam4 pairing agrees closely; those ratios confound shell
resolution and are not the required mesh-ratio qualification.
The existing exact finite-spline pointwise-bond diagnostic is itself
plate-resolution sensitive, so its smaller gap cannot be used as a
converged physical target. The present loaded comparisons and algebraic
rank checks remain distinct from the required norm-scaled stability and
joint-refinement assessment.

**Earlier checkpoint, 24 September 2026:**
Use the shell center material line and finite-width director frame as the
native *development candidate*. P0 leads the line-space investigation,
but no multiplier space or connection law is qualified. At fixed Q4 x8/y8
and 32 native half-cells, P0 line intervals 8→16 change torque rotation
−17.3% and transverse tip displacement −10.5%; the shell-only trace
rank changes from 48/48 to 69/96 while the complete beam–shell rows stay
full rank. The beam can carry interface oscillations that the shell trace
cannot resolve. Stop further line escalation. Bare native beam stiffness
is exact at 16/32 half-cells in the registered simple loads; the station
port has the expected `h²` position and `h` rotation orders. These facts
point to a connection-resolution question, not bare-beam convergence.
An independently assembled transverse plate/beam spline model follows
the same paired P0 torque trend within 1.6%. Its exact finite-space
pointwise bond is sensitive to *plate* resolution while fixed-plate beam
refinement leaves torque/shear response unchanged. This narrows the next
mechanics work to shell-side trace representability and a physical
reference, without declaring the formulation failed.
Loaded Q4/S3 torque and shear states have zero directly evaluated
numerical shell-component work at the tested thicknesses; physical
components reconstruct assembled energy. Native support torque equals
the actual interface-wrench resultant. Under one isolated shell mesh
refinement, the thin-shell reaction difference from the independent
model narrows but does not vanish. Stop brute-force resolution sweeps.

**Remaining uncertainty and next discriminating action:** Establish an
independent torque/shear target with the same physical geometry, load,
support and section idealization, and a connection whose work can be
compared with the native centerline law. The executed CalculiX S4/B31
probe transfers a physical shell force couple and transverse force, but
uses a rectangular beam section, nodal collocation and a different shell;
its beam-rotation monitor is unvalidated. S4/U1 failed in CalculiX and
B31 rejects the generalized section. A paired refinement on that route
also reached the unchanged 120 s limit for both torque and shear. Do not
repeat it at greater cost under this authority. These are execution and
idealization diagnostics, not the matched target. The next bounded
derivation should establish a resolved, section-matched physical
torque/shear reference and a shell-trace/interface stability argument,
including reaction partition and thickness. If those agree and a
registered joint refinement stabilizes, assess P0 over the required
mesh ratios; otherwise revise the pose or interface space before
selecting one. Keep the
classical axial, historical Q6/finite-pad and native six-channel results
separate. Rank, small gaps or a quotient alone cannot select a space.
Formal F03 authority is unconsumed, G0B open and G1 barred.

**Historical transverse-partition decision, 24 September 2026:** A systematic
midpoint split of all three y intervals (six elements) passed 18 focused
checks and two bounded runs, but it did not improve order-to-order physical
stability at equal coordinate count. Its degree8→12 beam-energy change
is +1.383%, versus +0.860% for the three-interval degree16→24 sequence;
root-force changes are -0.948% versus -0.568%. Full evidence is in
`B3_GE_E4_PL_F03_TRANSVERSE_MIDPOINT_SPLIT_V6.md`. Do not select this
partition as a convergence remedy or infer a continuum target from either
sequence. Next focus on the underlying regularity/localization and native
signed multiplier/torque formulation. Formal F03 authority remains
unconsumed; F03/G0B remain open and G1 barred.

**Earlier transverse-order decision, 24 September 2026:** At fixed x24,
beam512 and P1 line1024, y-degree 12→16→20→24 raises beam energy by
1.000%, 0.540% and 0.317% on successive steps; root-force magnitude
falls by 0.688%, 0.362% and 0.206%. The guarded source/results are in
`B3_GE_E4_PL_F03_TRANSVERSE_ORDER_V5.md`. Sampled child RSS reaches
5.699 GiB at degree 24. Further global y-order increase approaches the
8 GiB envelope; next compare a local transverse partition without
changing the physical operator. No reference or line law is selected.
Formal F03 authority is unconsumed; F03/G0B remain open and G1 barred.

**Earlier separate-order decision, 24 September 2026:** At fixed beam512
and P1 line1024, x-degree 24→32 changes beam energy only -0.0163%, but
y-degree 12→16 changes it **+0.9996%** and root-force magnitude -0.688%.
The bounded source/results are preserved in
`B3_GE_E4_PL_F03_DOUBLE_SEGMENTED_SEPARATE_ORDER_V4.md`. The former
appearance of transverse convergence at coarser line resolution is not
a general physical reference. Next isolate higher y order within the
same resource limit. Formal F03 authority remains unconsumed; F03/G0B
remain open and G1 barred.

**Earlier 1024-line decision, 24 September 2026:** The fixed-space
1024-interval P1 probe is preserved in
`B3_GE_E4_PL_F03_DOUBLE_SEGMENTED_LINE1024_V3.md`. From 512→1024 line
intervals, beam energy changes -0.356%, root-force magnitude +0.115%,
and tip magnitude +0.0154%. This is a useful settling trend in one
classical axial comparator, not a qualified physical target or native
line-space selection. Formal F03 authority remains unconsumed; F03/G0B
remain open and G1 barred.

**Earlier 512-line decision, 24 September 2026:** The separately
preserved double-segmented 512-interval P1 diagnostic is recorded in
`B3_GE_E4_PL_F03_DOUBLE_SEGMENTED_LINE512_V2.md`. At fixed shell and beam
spaces, 256→512 intervals still changes beam energy -0.900% and root-force
magnitude +0.409%; the trend improves but does not establish a physical
reference or signed stability. Formal F03 authority remains unconsumed;
F03/G0B remain open and G1 barred.

**Earlier double-segmented decision, 24 September 2026:** The optional longitudinal and
transverse interface-aligned classical shell is recorded in
`B3_GE_E4_PL_F03_DOUBLE_SEGMENTED_AXIAL_V1.md` with eight bounded runs and
13 passing affected tests. It greatly reduces apparent x-basis error but
does not settle the line: mortar128→256 still changes beam energy by 1.95%
and root-force magnitude by 1.20% at fixed x/y/beam spaces. No physical
target, native shell pose or multiplier space is accepted. F03/G0B remain
open and G1 barred. Prior diagnostics and their failures remain intact.

**Earlier transverse-basis decision, 24 September 2026:** The optional interface-aligned
classical-shell y basis and 14 guarded axial screens are retained in
`B3_GE_E4_PL_F03_SEGMENTED_AXIAL_V1.md`. Transverse order settles rapidly,
but longitudinal, beam and line-resolution effects still interact; no
physical reference or native line law is accepted. F03/G0B remain open and
G1 barred. The detailed chronological evidence follows below.

At matched beam512/mortar256 resolution, the finest segmented screen
still differs from the retained Q4 n256 comparator by 2.12% in beam
energy and 3.34% in root axial magnitude. This reinforces the need for
a physical convergence and interface-stability diagnosis before F03.

**24 September 2026 — independent F03 spectral-shell axial diagnosis.**
A Fourier-sine/Legendre plane-stress shell and separately assembled P1
four-sample line were coupled to the independent classical beam under
the support-matched axial load. Four analytic/direct-integration checks
passed; a seven-case resolution suite and nine resource-bounded higher
order solves completed. Longitudinal response begins to settle, but
transverse and multiplier resolution still change root force and beam
energy materially. At 64 longitudinal modes, y-order 48→64 changes
root force `1.04%` and beam energy `2.93%`; at fixed shell order, line
32→64→128 changes beam energy `11.28%` then `8.16%`. Weak rows near
`1e-22` coexist with a sampled physical gap at least `1.26%` of tip
motion on the largest transverse case. The
[spectral diagnostic report](B3_GE_E4_PL_F03_SPECTRAL_AXIAL_V1.md) retains raw identities, limitations
and the next interface-aware transverse-basis decision. It does not
establish a physical target or select a line law. **F03/G0B stay open;
G1 remains barred.**

**24 September 2026 — B2 F09 mixed weak-shear graph diagnostic.**
A separate exact Castigliano oracle was compared with the private physical
B2 operator assembled into one- and two-member sparse root-clamped graphs.
All four mixed six-component tip-wrench cases, including area `2^-80 m²`
with weak axial/shear loads and order-one couples, matched tip, grouped
support balance and energy to floating precision. The largest tip-channel
relative difference is `2.23e-16`; 27 affected private tests passed.
Source, raw result and scope are in
`B3_GE_E4_PL_G0_F09_MIXED_GRAPH_V1.md` and its JSONL. This is a narrow
feasibility result, not a conditioning envelope or F09 acceptance. The
mandatory B3-GE/E4-PL line foundation remains the main G0B blocker;
F03 and F09 are both open, and G1 remains barred.

**24 September 2026 — independent classical axial resolution isolation.**
The guarded comparator now permits separate bounded beam and continuous-P1
line resolutions, leaving its previous `2n` beam / `n` line default
unchanged. Seven new serial child solves completed: Q4 `n=128` with line
intervals 64/256 at 256 beam elements and beam elements 128/512 at 128
line intervals; CST `n=128` with line intervals 64/256 at 256 beam
elements; and Q4 `n=256` with 128 line intervals at 512 beam elements.
All used the same equilibrated independent classical laws, load and
supports. The largest sampled child RSS was `1.808 GB`; the longest wall
time was `63.7 s`. Each new root records source hashes, parameters, raw
output, parsed result, status and limits.

At fixed Q4 `n=128`, changing 128→256 line intervals changes shell
reaction by `2.64%` and beam energy by `4.08%`; changing 256→512 beam
elements changes them by only `0.0122%` and `0.0290%`. CST `n=128` line
128→256 changes reaction by `1.78%` and beam energy by `3.06%`. At Q4
`n=256`, changing line 128→256 still changes reaction by `1.18%` and
beam energy by `2.04%`. Conversely, along the paired Q4 `n=128→256`
physical and line refinement, shell reaction changes `4.22%` and beam
energy `7.35%`. All cases have small algebraic/weak residuals and
quadratic work discrepancy; those checks do not resolve the physical
discretization sensitivity. The line density is consequential, while
the beam mesh is not the dominant source on this slice. No continuum
target, mortar stability acceptance or native-line selection follows.
This remains independent classical Level-A diagnosis. **F03/G0B remain
open and G1 barred.** The next mechanics decision requires a bounded
signed-stability and physical-torque/trace reference, with an explicit
line-resolution policy; these axial results alone cannot establish it.

**24 September 2026 — guarded classical axial n=128/256 continuation.**
The same independent Q4/CST membrane, quadratic/Hermite beam and
three-channel P1 weak-line comparator was extended to joint `n=128` and
`n=256` with optional six-pass symmetric equilibration. A child-process
runner preserved each manifest, raw stdout/stderr, parsed result and
status, while sampling child RSS every `0.1 s` against `8 GiB` and
enforcing a `300 s` wall limit. A guarded Q4 `n=64` canary reproduced
all six selected saved physical/numerical fields **exactly** before the
larger runs. Both `n=128` and both `n=256` cases completed. Sampled peak
RSS was at most `437.5 MB` at `n=128` and `1.833 GB` at `n=256`; the
longest recorded wall time was `60.8 s`. These are sampled child working
sets, not hard peak or whole-process-tree memory measurements.

The `n=128→256` tip changes shrink to `0.141%` Q4 and `0.257%` CST,
and the two finest-tip values are close. Yet shell-support force changes
by `4.22%`/`3.42%`, shell energy by `1.82%`/`1.72%`, and beam energy by
`7.35%`/`6.76%`. Continuous integrated gaps decrease, while the largest
`n=256` algebraic residual ratio is `1.29e-12`, weak-row norm is below
`7e-24`, and quadratic work discrepancy is below `2.1e-12` relative.
Therefore tip agreement alone cannot establish the resolved response,
and no continuum target is adopted. The exact raw roots are
`B3_GE_E4_PL_F03_CLASSICAL_{Q4,CST}_N{128,256}_GUARDED_V1` under this
directory; the Q4 `n=64` guard parity root is retained too. Admission
bounds were widened between the `n=128` and `n=256` runs, with no change
to the element, trace, load, support or solve equations; each manifest
records its actual source hashes. The next diagnostic should vary line
resolution at fixed physical meshes and, separately, beam/shell
resolution. This is Level-A independent-classical evidence, still
different from native six-channel B3-GE/E4-PL and not an executed
external-solver comparison. **F03/G0B remain open and G1 barred.**

**24 September 2026 — larger independent classical axial reference, still
unsettled.** The separately assembled Q4/CST plane-stress, quadratic/Hermite
Timoshenko beam, three-channel continuous-P1 weak-line comparator was
extended from joint `n=8` to `n=16,32,64` with the same both-edge supports
and fixed `10^5 sin(2 pi s) N/m` load. Its `n=8` tip, shell reaction,
shell/beam energies and integrated gap reproduce the previously saved
classical outputs **exactly**. The unscaled sparse KKT became poorly
conditioned at `n=64`: its weak-row norm was about `1.2e-11` and the
CST work discrepancy reached `1.00e-4` relative. Those raw V1 results
are retained, not used as a converged target.

An optional six-pass symmetric row equilibration changes only the
independent solver's numerical coordinates. It preserves small-grid
physical solutions within verified numerical tolerances; two focused
parity tests and the full **22-test** affected comparator suite pass.
The eight equilibrated V2 cases (`n=8,16,32,64`, Q4/CST) have weak-row
norm at most `2.26e-23`, algebraic residual ratio below `1e-13`, and
quadratic work discrepancy below `7e-14` relative. The `n=64` raw and
equilibrated tip values differ by at most `0.006%`; the much larger raw
work error is a numerical warning, not a change of mechanical model.

Even on the equilibrated route, the `n=32→64` axial-tip magnitude changes
by about `1.85%` (Q4) and `1.94%` (CST); shell energy changes by more
than `4%`, and shell support reaction reverses its previous refinement
direction. Q4/CST tip values at `n=64` are close, but that agreement is
insufficient to declare a converged continuum target or qualify native
B3-GE/E4-PL. Raw files are
`B3_GE_E4_PL_F03_CLASSICAL_AXIAL_{Q4,CST}_N{8,16,32,64}_V1.json` and
corresponding `_SCALED_V2.json`, produced by
`scripts.b3_e4_f03_classical_axial_refinement` with explicit topology,
size and `--equilibrated` for V2. These are Level-A development runs;
peak process memory was not measured. A further resource-bounded joint
refinement and the independent physical torque/trace reference remain
needed. **F03/G0B stay open and G1 barred.**

**24 September 2026 — admissible bonded transverse-shear patch.**
A flat-shell field `w=0.02 x` with unchanged physical directors and a
matching native B3 station field gives coincident shell/beam positions
and frames at five stations, while the shell geometric midsurface normal
is tilted relative to the unchanged director. The physical-shell
quadratic shear energy is positive. On Q4 it matches the independently
computed `0.5 (5/6) G t A gamma²` constant-shear result to `1e-12`
relative for 2/4/8 transverse intervals. On S3-V2D it matches that
unrelaxed result times the element's documented `phi_squared` MIN3
factor; on the joint 2/4/8 grids this factor is approximately
`0.05703`, `0.19480`, `0.49179`. Thus the candidate line kinematics do
not force an independent shell director to the geometric normal or
exclude this nonzero transverse-shear mode. S3's physical shear energy
also changes strongly with mesh under its existing MIN3 relaxation;
that known law must be considered when interpreting cross-mesh loaded
torque response. Six focused kinematic/energy checks passed. This is a
patch and formulation-attribution result, not loaded shear convergence,
an interface stability proof or a physical torque reference. F03/G0B
remain open and G1 barred.

**24 September 2026 — drilling-independent reference torque replay.**
The existing small KKT torque test was extended, without changing product
mechanics, to the support-matched 4-by-4 and 8-by-8 shell grids for Q4 and
S3-V2D and all three P0, continuous-P1 and dual-P1 spaces. Its second
solve replaces the full E4 shell block with the independently assembled
physical shell block and removes every independent shell `rz` coordinate;
the native B3 and the same exact weak-line Jacobian remain. In all
**12** new support-matched combinations, the `100 N m` tip response and
all non-drilling shell coordinates match the full E4 solution within
`rtol=1e-8, atol=1e-12`, the recovered shell support torque about the
common origin matches within `rtol=1e-8, atol=1e-7 N m`, physical-shell
quadratic energy is positive, and the coupled moment balance closes.
The full affected test, including six earlier legacy-support controls,
passed **18/18**. This rules out numerical drilling completion as the
source of the observed P0/P1/dual torque separation on these flat virgin
grids. It does not establish a physically correct torque value, preserve
transverse shear under finite motion, or replace an independent torque
reference. **F03/G0B remain open and G1 barred.**

**24 September 2026 — three-level support-matched joint refinement.**
The bounded flat fixture now has an unregistered common-support screen at
joint `(n_s,n_y,n_half_cells)=(2,2,8),(4,4,16),(8,8,32)` for Q4 and
S3-V2D, piecewise-constant/P0, continuous-P1 and dual-P1 multipliers,
and two fixed physical loads: `10^5 sin(2 pi s) N/m` native axial line
density and `100 N m` tip torque. There are **36** native cases (18 per
load); the continuous-P1 axial cases also have a separately assembled
classical Q4/CST and quadratic-beam comparison. Both models use the
declared two shell x-edge in-plane supports; their discrete shell, beam
and trace laws remain distinct. This is a joint mesh change, not the
required full beam:shell ratio, thickness, stability or external-reference
qualification.

All six native topology/space axial tip sequences change sign from the
coarse to middle grid; so do both classical continuous-P1 axial sequences.
On the middle-to-fine step, native axial tip changes by `8.94–129.17%`
across the six topology/space combinations. The corresponding torsion
tip changes by `13.30–18.25%`, while recovered shell-support torque
continues to fall. At the fine Q4 grid the shell carries `34.35 N m`
(P0), `13.96 N m` (continuous P1) or `7.43 N m` (dual P1) of the
`100 N m` applied torque. S3-V2D gives `33.62`, `13.43`, and `6.91 N m`.
Maximum pointwise gaps decrease with joint refinement, but the finest
torque gaps still range from about `0.49` to `1.69 µm` by space. The
new 24 P0/dual cases have scaled algebraic residual at most `2.28e-16`,
axial balance error at most `7.94e-11 N`, and torque balance error at
most `9.74e-11 N m`; these do not establish physical convergence.

The new coarse classical/native comparison is
`B3_GE_E4_PL_F03_MATCHED_AXIAL_NS2_V1.json`. The new P1 torsion endpoints
are `B3_GE_E4_PL_F03_MATCHED_TORSION_NS{2_NY2,8_NY8}_V1.json`.
The other 12 raw outputs are
`B3_GE_E4_PL_F03_JOINT_{AXIAL,TORSION}_{P0,DUAL}_NS{2,4,8}_NY{2,4,8}_V1.json`,
with matching host/transverse counts in each filename. Existing P1 middle
torsion and P1 middle/fine axial files were reused without rewriting them.
The exact runners are `scripts.b3_e4_f03_weak_line_resolution_screen`
with explicit paired host, transverse count, kind, both-edge support and
axial-density flags as applicable, and
`scripts.b3_e4_f03_matched_axial_reference_screen` for the coarse
classical comparison. Nine focused tests passed after the bounded
comparator was extended to `n_s=2`. This is Level-A development
evidence. **No line space or shell port is selected; F03/G0B remain open
and G1 barred.** The next high-value work is a compatible physical
torque/line reference and the registered beam:shell mesh-ratio and
norm-scaled stability checks; another small equilibrium residual on
these grids cannot make the selection.

**24 September 2026 — support-matched reference torsion diagnostic.**
With both shell x edges supported, a fixed `100 N m` native B3 tip torque,
continuous-P1 weak line, four shell hosts and 16 native half-cells, the
Q4 and S3-V2D fixtures completed at 2/4/8 transverse shell intervals.
At the flat reference, recovered shell-support moments include both nodal
moment and the `r × F` lever arm. The shell carries `31.51–35.84 N m`
of the reaction torque and the beam root the remainder. All six total
torque balances are within `5.70e-11 N m`; shell-plus-beam quadratic
work matches half the applied tip work within `2.68e-13` relative.
Across 2 to 8 transverse intervals, the Q4/S3 beam-tip twist changes by
about `3.46%`/`1.86%`. The maximum pointwise connection gap remains
about `1.18e-6 m`; transverse refinement alone does not close it.
These observations establish transfer and balance only for this bounded
reference-state fixture. They do not establish torque accuracy, drilling
independence, thickness behaviour, line stability or longitudinal
convergence. The three raw outputs are
`B3_GE_E4_PL_F03_MATCHED_TORSION_NS4_NY{2,4,8}_V1.json`, produced with
`scripts.b3_e4_f03_weak_line_resolution_screen` and its explicit paired
host, line-space, support and transverse-grid flags. Two new torque/work
checks and nine combined focused tests passed. **F03/G0B remain open and
G1 barred.** The next mechanics decision needs longitudinal and thickness
sensitivity, weak-line gaps, and a physical torque/trace reference.

**24 September 2026 — bounded shell-block attribution after support matching.**
An unregistered diagnostic retained the native B3, six-channel weak line,
rail port, both-edge support and fixed axial density, then replaced only
the E4 shell in-plane tangent block with the separately assembled physical
membrane block. This hybrid is **not** a valid alternative mechanical
formulation: its other E4 blocks and cross terms remain unchanged. The
unmodified branch reproduced all three saved native observables exactly
in all **12** matched Q4/S3, 4/8-by-2/4/8 cases. The block difference was
`7.90–8.58%` in Frobenius norm. Substitution changed the beam-tip response
by `1.38–14.57%` and increased its absolute discrepancy from the separate
classical comparator in **all 12** cases; the largest scaled algebraic
residual was `4.93e-17`. Thus the earlier near agreement cannot be
attributed to equality of the full E4 and classical shell operators, and
the membrane block cannot simply be swapped into an otherwise native KKT.
Two six-case raw outputs are
`B3_GE_E4_PL_F03_SHELL_BLOCK_SENSITIVITY_NS{4,8}_V1.json`; the runner is
`python -B -m scripts.b3_e4_f03_shell_tangent_attribution` with the
corresponding host count. Five focused tests passed, including exact
unmodified-solution comparisons. This is Level-A sensitivity evidence;
it neither selects a line space nor closes F03/G0B. Next resolve the
physical line torque/shear response and norm-scaled signed stability on
support-matched, mesh-ratio cases before a production mechanics choice.

**24 September 2026 — F03 support-matched axial reference diagnosis.**
The earlier native weak-line KKT deliberately fixed all six coordinates
at only **three left-edge shell nodes**; its prior loaded/rank screens
therefore did not share the two supported x edges of the independent
classical comparator or the support statement in the planar shell fixture.
For transverse grids above two rows, additional left-edge nodes were
free as well. All those historical JSON results remain unchanged and
retain their actual `legacy_three_left_nodes` interpretation. Their
response trends cannot be re-labelled as a both-edge convergence study.

A separately selected `both_xy_edges` policy now fixes in-plane coordinates
on every node at both x ends and fixes left-edge z/rx/ry to remove the
out-of-plane rigid modes, leaving shell rz free. The old default was
verified to reproduce four saved numerical outputs **exactly**. The
native shell fixture now admits 2/4/8 transverse rows; the explicit
two-row source arrays, supports, breakpoints and sample maps retain the
pre-change hashes `c0541e35…` (Q4) and `dfa344d2…` (S3-V2D).
Nine direct grid/support tests passed. An independently assembled
classical axial load was also checked against its analytic resultant
and first moment without importing the native load builder.

An unregistered comparator ran **12** Q4/classical-Q4 and S3-V2D/CST
cases at shell host counts 4/8 and transverse counts 2/4/8, with a
fixed `10^5 sin(2 pi s) N/m` line density, equivalent section constants,
four-sample rail, P1 interval count equal to shell host count, and the
explicit both-edge in-plane supports. At `(n_s,n_y)=(4,2)`, the native
S3/CST tip difference is `0.516%`; the prior left-only native tip was
about four times the both-edge result. At `(8,8)`, Q4/classical-Q4 and
S3/CST tip differences are `0.915%` and `0.950%`. The corresponding
shell-reaction differences are `0.739%` and `1.672%`, and shell-energy
differences `0.730%` and `1.672%`. Both separate solvers satisfy their
small algebraic/balance residuals. Native and classical beam-only axial
tips agree to floating precision, and S3's physical membrane block
matches the independent CST block; the complete E4 trial tangent and
the classical beam interior/three-channel trace remain distinct laws.
At `(8,8)`, a post-screen recovery check finds that full E4 shell energy
exceeds its physical in-plane contribution by `1.6555%` (Q4) and
`1.5398%` (S3-V2D). Removing that difference alone does not reconcile
the independently assembled shell energy; material/trace and
discretization effects still require attribution.
No 1% cross-solver acceptance is claimed for all observables, and neither
an external solver nor a converged continuum target is supplied here.

The four earlier-support transverse cases are retained as
`B3_GE_E4_PL_F03_LEGACY_TRANSVERSE_NS4_NY{4,8}_{RAIL,LOCAL}_V1.json`;
the support-matched comparison is in
`B3_GE_E4_PL_F03_MATCHED_AXIAL_{NS4,NS8_NY2_4,NS8_NY8}_V1.json`.
The latter was produced with `python -B -m
scripts.b3_e4_f03_matched_axial_reference_screen` and explicit
`--shell-host-intervals`/`--transverse-intervals` values. All seven
copied files were parsed and compared with their source outputs.
The combined focused pytest run passed **98 tests**, including the new
comparator, transverse-grid host invariance, retained transverse-load
control, and existing shell/weak-line checks. This is Level-A
diagnosis under the adopted risk-proportionate policy. **F03/G0B remain
open; G1 remains barred.** Next, isolate full E4 tangent/trace effects
on reactions and energy, then assess signed stability, physical torque,
shear and mesh ratios before any space or shell-port selection.

**24 September 2026 — fourth axial loaded resolution level.** The bounded
private E4 trial and native B3 fixture now admit 8 shell host intervals
and 32 native half-cells for the same straight, elastic diagnostic; no
public/product admission changed. The fixed physical density from the
preceding entry was evaluated at one multiplier interval per shell host
for P0, continuous P1 and dual P1 on Q4/S3 and both shell origins.
All **12** added cases completed. The largest scaled KKT residual is
`1.49e-16`, the axial resultant error is below `6.83e-13 N`, and the
analytic first-moment error is below `1.82e-12 N m`.

From four to eight shell hosts, Q4/S3 **rail continuous-P1** tip motions
change by `1.18%`/`0.53%`; rail P0 still changes by `23.67%`/`23.47%`,
and rail dual P1 by `3.63%`/`2.81%`. The **local-origin continuous-P1**
changes are `1.70%`/`3.32%`; its Q4/S3 finest tips remain about
`-1.345`/`-1.195 µm`. Pointwise gaps decrease, but small gaps and
equilibrium residuals do not establish a settled physical response.
The transverse shell grid stayed at two rows, the rail and local origins
are distinct physical maps, and no matched independent displacement target
was executed. This is not a full joint-refinement or multiplier-stability
claim. Raw outputs are
`B3_GE_E4_PL_F03_PHYSICAL_DENSITY_EXTENDED_{RAIL,LOCAL}_V1.json` here;
the command adds `--paired-shell-intervals 8` to the preceding paired
runner, with the applicable shell-origin flag. Both outputs were parsed
and compared semantically with their source files. **No line space is
selected; F03/G0B stay open and G1 barred.** The next decisive work is a
matched physical reference and transverse/mesh-ratio response, not a
smaller algebraic residual on the same strip.

**24 September 2026 — mesh-consistent loaded F03 resolution diagnostic.**
The earlier axial-wave screen placed the same signed force at each beam
node, so changing beam resolution would change the applied physical load.
A separate optional load now integrates the fixed reference density
`q_x(s)=10^5 sin(2 pi s) N/m` through the native station-work pullback.
For native half-cell counts 4, 8 and 16, four direct checks verify the
independently integrated exact nodal-hat loads, zero resultant, the analytic
first moment `-10^5/(2 pi) N m`, no transverse or retained-coordinate force
on this straight fixture, and invalid-amplitude rejection. The existing load
option and default grid are preserved.

Two unregistered paired screens use shell host intervals 1/2/4, native
half-cells 4/8/16 and one multiplier interval per host, for P0, continuous
P1 and dual P1 on Q4/S3 and both rail/local shell origins. All **36**
cases have the same first moment within `3.64e-12 N m`, zero resultant
within `2.73e-12 N` and scaled algebraic residual below `5.31e-17`.
The beam-tip response is still not settled: Q4 rail continuous-P1 changes
from `-0.317` to `-0.806 µm` between the last two grids; Q4 local
continuous-P1 changes from `-0.884` to `-1.322 µm`. At the finest grid,
the Q4/S3 local continuous-P1 tips differ by about 14%. These are
physical-response discrepancies despite small weak residuals, not evidence
for a selected multiplier space or a converged continuum target. The
two complete raw outputs are
`B3_GE_E4_PL_F03_PHYSICAL_DENSITY_PAIRED_{RAIL,LOCAL}_V1.json` here;
the command is `python -B -m
scripts.b3_e4_f03_weak_line_resolution_screen --paired-refinement
--sinusoidal-axial-density --include-dual`, with `--local-translation`
for the second output. The saved JSON was parsed and checked against the
source output. After those screens, only the amplitude type guard was
tightened; the accepted `10^5 N/m` load arithmetic was unchanged and its
focused checks were rerun. This remains Level-A work under the adopted
philosophy.
The existing independent classical comparator has a different beam and
shell law and is not silently treated as a direct native target.
**F03/G0B remain open; G1 remains barred.** The next result must resolve
the loaded-response discrepancy against a physically matched reference
or a justified joint-refinement limit before any multiplier selection.

**24 September 2026 — F03 biorthogonal dual-P1 development candidate.**
From parent `1e18bb053a6a59becf9e1e6f96ea94b30e94f944`, added the local
dual basis `psi_L=2N_L-N_R`, `psi_R=2N_R-N_L` to the bounded weak-line and
native-compliance diagnostics. Its Neumann H^-1/2 Gram has analytic cosine
moments and a floating spectral-tail upper estimate. Four biorthogonality cases, a separate
Gauss-moment check, four Q4/S3 reference-Jacobian checks, four
nonzero-multiplier work/derivative checks and two retained absolute-metric
checks passed by direct invocation (**15 checks**, Python 3.14.2, NumPy
2.4.6, SciPy 1.17.1). A focused pytest collection attempt produced no
result after 50 s and was stopped; it is not counted as a pass.

The unregistered paired and fixed-shell screens compare P0, continuous P1
and dual P1 on both Q4/S3 and rail/local shell ports. At one multiplier
interval per shell host, dual shell rows have full measured rank in all
12 paired cases, but the shell-only norm quotient is as low as 0.00943.
At eight intervals on the fixed four-host shell, dual shell row ranks are
Q4 rail **42/54**, Q4 local **38/54**, S3 rail **54/54** and S3 local
**42/54**; the full-rank S3 rail shell-only quotient is only 0.000165.
This candidate therefore does not repair the fine-interface shell-side
resolution failure. Loaded axial and torsion screens show different
responses among the three spaces; for example Q4 rail dual axial tip motion
changes from -1.697e-6 m at four intervals to -1.243e-6 m at eight, while
dual torsion tip rotation changes from 1.057e-5 to 9.199e-6 rad. The dual
torsion pointwise gap falls on this fixture, but no independent physical
target or convergence claim follows from that observation.

Raw cases (18 each) are retained as
`B3_GE_E4_PL_F03_DUAL_{PAIRED,FIXED}_{RAIL,LOCAL}_V1.json` and
`B3_GE_E4_PL_F03_DUAL_{AXIAL,TORSION}_{RAIL,LOCAL}_V1.json` in this
directory. The commands are `python -B -m
scripts.b3_e4_f03_native_line_compliance_screen --absolute-primal
--include-dual` with either `--fixed-primal` or
`--multiplier-intervals-per-shell 1`, and optionally
`--local-translation`; and `python -B -m
scripts.b3_e4_f03_weak_line_resolution_screen --include-dual` with
optional `--axial-wave` and `--local-translation`. All eight copied JSON
records were parsed and
compared semantically with the source outputs. This is Level-A development
evidence, not the frozen one-use F03 assessment. **No multiplier space is
selected; F03/G0B remain open and G1 remains barred.** The next integrated
result is a physically defined, independently checkable line-coupling
observable and a resolution policy that avoids the demonstrated shell rank
loss without silently narrowing the registered mesh-ratio domain.

**24 September 2026 — F03 axial channel separated by domain and norm.** An
independent unit axial-bar calculation shows that alternating P0 load
compliance divided by the existing H^-1/2 norm falls with refinement even
for a stable bar. A new native shell-row/SVD and shell-only positive-norm
screen finds numerical rank loss at eight multiplier intervals on the
fixed four-host-interval shell panel for Q4 rail/local and S3 local; S3 rail
remains full rank but has small shell-only minima. One interval per shell host has
full shell-row rank across all 24 paired Q4/S3, P0/P1 and rail/local cases,
yet several shell-only quotients remain small or decrease. See the
[attribution report and immutable raw inventories](B3_GE_E4_PL_F03_AXIAL_CHANNEL_ATTRIBUTION_V2.md).
The bar oracle passed 5/5 pytest tests; four native checks passed directly,
while local pytest collection for that module stalled. The observations
neither select a multiplier space nor revise G0B acceptance. F03/G0B remain
open, G1 barred.

**24 September 2026 — native F03 positive-norm attribution.** A bounded
48-case screen replaced the signed inverse of the indefinite native retained
primal tangent with its positive spectral absolute **as a diagnostic norm**;
the physical rows and H^-1/2 multiplier Gram were unchanged. The alternating
axial minimum still declines under both fixed-primal multiplier refinement
and paired shell/beam/multiplier refinement for Q4/S3, P0/P1 and both shell
origins. At fixed Q4 rail, P0 falls `2.963 → 1.406`, P1 `1.970 → 0.764`;
local translation raises the shell contribution but does not remove the
trend. See the [result and four raw inventories](B3_GE_E4_PL_F03_ABSOLUTE_METRIC_DIAGNOSTIC_V1.md).
This distinguishes signed cancellation from the persistent positive-norm
trend but does not establish a physical inf-sup limit or select a line space.
Direct mathematical/native checks passed; the local pytest collection attempt
stalled and was stopped. F03/G0B remain open; G1 barred.

**24 September 2026 — Q6 linear observable bound diagnostic.** Added an
exact-represented rational propagation of the saved scaled-state certificate
to tip pose, external work and root multipliers, including the discrepancy
between the exact represented candidate map and the reported binary64 value.
The X2 source-process check reassembled the existing operator in 324.63 s,
matched its saved displacement scaling and candidate physical-state hash,
and returned a 1.03e-14 m upper error for tip vertical displacement,
9.75e-9 J for external work and 6.21e-4 N for the largest root-force
component. The [raw diagnostic](B3_GE_E4_PL_G0_F03_Q6_X2_LINEAR_OBSERVABLE_DIAGNOSTIC_20260924.json)
records all seven channels and source hashes. Focused tests passed 25/25
with a workspace-owned temporary directory, followed by 8/8 targeted tests
after adding source-identity checks. Initial test attempts had temporary-
directory access errors; the affected tests passed when rerun. This result
only bounds linear recovery from represented Q6 operators; energy, interface
functionals, discretization error, physical settling, installed identity and
native F03 mechanics remain open. It does not amend the earlier 2,258.19 s
resource overrun, close F03/G0B or permit G1.

**24 September 2026 — X2 combined shared-assembly diagnostic.** One source
process assembled Q6 X2 once, then completed the KKT certificate, shell
positivity, physical recovery and spatial audit. Exit 0 took 2,258.19 s at
692,072,448 B sampled peak RSS, exceeding the draft 1,800 s case envelope
by 458.19 s. The physical state, signed outputs, functional, KKT/shell hashes
and spatial results matched prior X2 diagnostics; a tiny iterative eigenvalue
estimate differed. Exact V1 runner source is archived against its attempt
hash. An operator-content fingerprint was added **after** this run for a V2
diagnostic; V1 does not gain that check retroactively. See
`B3_GE_E4_PL_G0_F03_Q6_X2_SHARED_ASSEMBLY_RESULT_20260924.md`. This is a
measured resource overrun of the draft envelope, not a formal scientific
failure. F03/G0B remain open; G1 barred.

**24 September 2026 — three-grid Q6 primal-positivity saved replay.** An
experimental sparse congruence-residual certificate completed on fixed
X0/X1/X2 grids. All three original scaled shell matrices report strict
positive-quadratic-form sufficient bounds; separate replay from archived
matrices, factors, scales and complete inverse columns reproduced each proof
exactly. Source times were 262/441/841 s with sampled peak RSS 295/390/548 MB;
replay times were 161/308/568 s with 267/348/487 MB. All six supervisor
receipts are exit-zero and the affected tests passed 62/62. See
`B3_GE_E4_PL_G0_F03_Q6_THREE_GRID_POSITIVITY_SAVED_REPLAY_RESULT_20260924.md`.
This is unregistered source-level feasibility of archived scaled matrices;
independent physical-assembly binding, installed identity, observable error
propagation, native mechanics and formal review remain. F03/G0B remain open;
G1 is barred. The first failed X0 and unarchived second X0 attempts remain
preserved as evidence. Independent read-only review of all saved bytes and
receipts found no remaining saved-matrix proof issue, but the full installed
route is not timed. Separate X2 timings project about 1,950 s with duplicate
physical assembly or 1,715 s if it too is shared, leaving little margin under
the draft 1,800-second envelope. See
`B3_GE_E4_PL_G0_F03_Q6_POSITIVITY_INDEPENDENT_READ_ONLY_REVIEW_20260924.md`.

**24 September 2026 — three-grid Q6 saved-input feasibility.** Fixed X0/X1/X2
source certificate and saved-only replay routes all completed serially under
supervision. Each replay matched the full source certificate exactly from
the saved scaled system, candidate and inverse columns; all six receipts,
archive hashes and parent/child source identities checked. Source elapsed
times were 297.28/527.75/927.41 s, replay times 196.33/374.57/671.62 s.
See `B3_GE_E4_PL_G0_F03_Q6_THREE_GRID_SAVED_REPLAY_RESULT_20260924.md`.
An independent conditional review found no local compiled arithmetic
counterexample and verified the tested FTZ/DAZ guard modes; see
`B3_GE_E4_PL_G0_F03_Q6_INTERVAL_ARITHMETIC_REVIEW_20260924.md`.
All results remain unregistered source-process diagnostics. Installed identity,
physical-observable error bounds, primal positivity, full physical settling,
native interface mechanics and formal independent review remain open.
F03/G0B remain open and G1 barred.

**24 September 2026 — Q6 X0 saved-only replay.** A bounded archive now
preserves the canonical scaled KKT matrix/RHS and physical coordinate scales
beside the inverse columns. A supervised X0 source run completed in 297.28 s
at 328.5 MB sampled peak RSS; a separate saved-only replay completed in
196.33 s at 256.9 MB and reproduced the certificate exactly, without
assembly, factorization or solve. Archive and evidence hashes matched;
parent and child source hashes matched; focused tests passed 50/50. See
`B3_GE_E4_PL_G0_F03_Q6_X0_SAVED_REPLAY_RESULT_20260924.md`. This is
unregistered source-level reproducibility using the same experimental
interval kernel, not independent arithmetic proof or installed qualification.
F03/G0B remain open and G1 barred.

**24 September 2026 — patched Q6 X2 resource rehearsal.** The full X2
certificate, bound physical recovery and spatial audit completed after the
interval-kernel safety/edge changes in 1,411.19 seconds at 688.8 MB sampled
peak RSS. The inverse, candidate and KKT/RHS hashes and all saved signed and
functional outputs matched the earlier KKT-bound rehearsal. This supports
source-level feasibility for the patched code, not a speedup or formal
installed gate. See `B3_GE_E4_PL_G0_F03_Q6_X2_KERNEL_PATCH_RESULT_20260924.md`.
F03/G0B remain open and G1 barred.

**24 September 2026 — Q6 arithmetic edge correction.** An independent audit
identified missing runtime-subnormal exact-oracle coverage. The new test also
found a valid rectangular CSR input that crashed the compiled helper; the row
bound and pre-Numba structure checks are fixed. Runtime FTZ/DAZ-sensitive
operations and exact-Fraction amplified-subnormal/cancellation/overflow tests
now pass with the affected certificate suite (28/28). See
`B3_GE_E4_PL_G0_F03_Q6_INTERVAL_KERNEL_EDGE_REVIEW_20260924.md`. Formal
compiled arithmetic review, saved-only replay and installed identities remain
open. F03/G0B are open and G1 barred.

**24 September 2026 — X2 scaled KKT/RHS identity bound.** A fresh source-level
rehearsal canonicalized and hashed the full scaled sparse KKT matrix and RHS
in both the certificate and independently reassembled physical recovery path.
The hashes matched, the saved certificate state drove recovery, and the full
numerical/physical/spatial route completed in 1,423.57 seconds at 688.7 MB
sampled peak RSS. Physical state and observables exactly matched the prior
bound-state rehearsal. The affected suite passed 40/40. Independent read-only
review accepted this narrow scaled-system identity transfer. See
`B3_GE_E4_PL_G0_F03_Q6_X2_KKT_BOUND_RESULT_20260924.md`. Compiled-certificate
arithmetic, physical-observable error propagation, geometry/scaling identity,
installed artifacts, saved-only replay, three-grid adjudication, primal
positivity and native interface mechanics remain open. F03/G0B remain open;
G1 is barred.

**24 September 2026 — X2 certificate candidate bound to physical recovery.**
The next source-level X2 rehearsal used the certificate's saved 5,893-coordinate
scaled KKT candidate as the physical pilot state, rather than a separate solve.
Its supervised process completed in 1,426.95 seconds at 691.8 MB sampled peak
RSS. The saved physical state and observables exactly matched the earlier V2
independent-solve pilot; all record hashes and spatial diagnostic limits passed.
Affected mechanics tests passed 39/39. See
`B3_GE_E4_PL_G0_F03_Q6_X2_BOUND_STATE_RESULT_20260924.md`. This resolves only
the source-wrapper state-transfer gap. Independent review found that the
certificate and physical paths still assemble their KKT matrix/RHS separately;
their identities must be bound before the certificate enclosure applies to
reported physical observables. Independent replay, installed identity, primal
positivity and three-grid adjudication remain open. F03/G0B remain open;
G1 remains barred.

**24 September 2026 — three-grid numerical feasibility and X2 integrated
resource rehearsal.** The isolated integration branch now contains full
source-process inverse-column diagnostics for fixed Q6 X0/X1/X2: 293/519/907
seconds, 327/470/691 MB sampled process-tree RSS, complete 3,289/4,405/5,893
column inventories and reported condition/backward bounds within inherited
limits. X2 **exceeded** the earlier 900-second per-case proposal. A first
integrated X2 rehearsal failed after its certificate and physical solve at
the JSON tuple/list evidence boundary; its logs and receipt remain preserved.
The corrected V2 source-level route completed numerical, physical and spatial
work in 1,435.91 seconds at 688.7 MB sampled peak RSS under a predeclared
1,800-second/2 GiB rehearsal envelope. The physical free-state hash, signed
bands and functional norm exactly repeated the earlier X2 pilot. See
`B3_GE_E4_PL_G0_F03_Q6_THREE_GRID_CERT_FEASIBILITY_20260924.md` and
`B3_GE_E4_PL_G0_F03_Q6_X2_INTEGRATED_REHEARSAL_RESULT_20260924.md`.
This remains **unregistered source-level evidence**, with duplicate assembly
and no binding between the certificate candidate and saved physical state.
Independent numerical soundness, installed-artifact identity, saved-only
replay, primal positivity, three-grid physical adjudication, and native
interface mechanics remain open. F03/G0B remain open; G1 is barred. Next:
bind one certified and physically recovered state, then exercise the complete
installed route and independent review before scientific registration.

**24 September 2026 — Q6 X0 certificate feasibility, G0B still open.** The
isolated integration branch contains the evidence and arithmetic commits through
`65c4fe2504ec629a48368fab20d1a8520d641a3a`;
main remains untouched. A new unregistered fixed-Q6 three-grid protocol and
shape contract are committed. The original Python inverse-column interval
loop proved too costly for the proposed 900-second case limit. A compiled
arithmetic counterpart matched the scalar bounds bitwise in bounded tests
and on one actual X0 block. A **complete X0 diagnostic** then verified all
3,289 inverse columns in 823 blocks; reported condition upper bound was
`6.246e5`, amplified backward-error upper bound `7.459e-10`, 293.01 seconds
and 326.9 MB sampled peak process-tree RSS. The 86.5 MB inverse is retained
locally, ignored by Git, with a committed SHA-256 and receipt. The earlier
unreceipted attempt remains preserved as aborted evidence. See
`B3_GE_E4_PL_G0_F03_Q6_X0_CERT_FEASIBILITY_20260924.md` and the linked raw
records. Independent read-only review accepted **only diagnostic feasibility**:
compiled-kernel soundness and full-block parity, source/wheel/dependency
identity, saved-only replay, independent primal positivity and physical-case
adjudication, plus X1/X2 budgets and certificates remain. No scientific
registration has been minted; F03/G0B are open and G1 barred. The affected
focused suite passed 48 tests. Next: close the arithmetic review and resource
envelope, then build/review the one-use installed-artifact producer and
adjudicator before any formal three-grid execution.

**24 September 2026 — active G0B checkpoint.** The latest F03 evidence was
committed at `7cc6673e78928f4a57b9e7877e2f17645952492c` on the isolated
integration branch; main is untouched. The fixed-Q6 X0→X1→X2 h pilot now has saved-state
binding, actual-case nested Ritz identities, all-eight physical band/atom
checks, a bounded one-ulp contribution, and an X2 spatial/support-work audit.
Independent read-only review closed the three findings in the strengthened
v2/v3 audits. See
`B3_GE_E4_PL_G0_F03_QP_H_ADDITIONAL_EVIDENCE_20260924.md` and its linked
raw outputs. This is **unregistered preparatory source-level evidence**;
F03/G0B remain open and G1 remains barred. The next step is an exact-source
one-use scientific registration and supervised installed-artifact rerun of
all X0/X1/X2 cases, after freezing dependencies, budgets, full-route checks,
and independent pre-execution review. The failed earlier Qp screens and
resource abort remain preserved.

**23 September 2026 cross-case component checkpoint.** The solve-free
cross-case arithmetic, retained snapshot reader and five-case pairing adapter
are committed at `1d4648be2a8754909a2324d53fe772443e85c4f3` and
independently reviewed with no remaining findings. The affected suite passed
88 tests, with one Windows symlink-privilege skip. See
`B3_GE_E4_PL_G0_F03_CROSS_COMPONENT_RESULTS.md`. The aggregate inventory,
exclusive receipt and serial coordinator remain unimplemented; no scientific
registration or execution occurred. G0B remains open and G1 barred. The
previous failed physical-settling evidence is unchanged.

**ACTIVE — 23 September 2026.** The user resumed from
`B3_GE_E4_PL_PAUSE_20260922_SIGNED_NORM.md`. The signed-norm component is now
implemented, independently reviewed and closed with corrected immutable
evidence. The complete saved-recovery composition is also implemented,
independently reviewed and closed with corrected immutable evidence. A frozen
scientific numerical protocol is independently reviewed, and its bounded
runner foundation is implemented and independently reviewed. The primary
solve-free numerical, inverse, port, exact-prolongation and saved-component
schemas are now committed. Composition-summary, physical-balance and the
adjudicator-bound per-case receipt schemas are committed and independently
reviewed. Canonical replay budgets, saved numerical semantic binding and the
solve-free single-case adjudicator are committed and independently reviewed.
The bounded plan-envelope reader and the port, saved-interface, saved-work,
saved-norm and common-state saved-observation production factories are also
committed and independently reviewed. The exclusively-writing child producer
is now committed and independently reviewed. The top-level one-use
coordinator is the active next work.

22 September 2026. User authorized continued implementation with increased
effort. The active goal remains the complete programme; **G0B is open and
G1 is barred**. This is a continuity checkpoint, not a pause or completion.

- Worktree: `C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling`.
- Branch: `codex/b3-ge-e4-pl-integration`.
- Latest bounded operator source: `7cb7b77491ef3343b72a231a6bb443e0474ddec1`.
- Latest bounded assembly/probe source: `66b6e109516296bbf8c4ff4155f2aa96c3701d1a`.
- Latest bounded sparse-numerical/recovery source: `ade088e99e3108969baf70b27e7f7cc450351229`.
- Latest factor/integration connection source: `126a4eb1122d4b36b7651d54d73c4b32fa139ead`.
- Latest sparse state/rank source: `7b017d08c29aaf4845e2fb71967d8b1bfb3859ec`.
- Latest sparse trace/equilibrium source: `a858e787d86e6f8e3a65e16f5268ce68fa53c8a1`.
- Latest certified Action/Q1 recovery source: `5be7447fc47b2b216238d15f020b406c7028d165`.
- Latest saved interface/work component source: `5acfd119b576237db4b104d4e56c1e4af93ebb81`.
- Latest signed-norm component source: `8bb018f73f837d25ef4f0d4bd94d9d3a824f0387`.
- Latest saved-recovery composition source: `271d88d094bc89e2fce4fdc23a4b5df2cce68d4b`.
- Latest reviewed local-scientific protocol source: `363d325b`.
- Latest reviewed runner-foundation source: `9f4a6be0`.
- Latest independently reviewed numerical-evidence schema source: `eccbfe2f`.
  This includes actual CSR factor round-trip, producer-native hashes/storage
  accounting and all four frozen nested transitions.
- Latest independently reviewed composition/balance evidence schema source:
  `5d12da1c`. The first review's P1/P2 findings
  were corrected by enforcing composition/work invariants and labeling rounded
  balance numbers as display-only while retaining exact Action identities.
- Latest independently reviewed assembly/scaling diagnostics source:
  `de962e9f`. Both quadrature routes, fixed scales, primary scale reuse,
  producer work/nnz counts and all five exact trace-bit maxima are bound inside
  `numerical_index.json`; no extra archive member was introduced.
- Latest independently reviewed case-receipt source: `103cf51e`. The complete
  45-channel scale vector is frozen, reported observations require exact
  solve-free adjudicator bindings, binary64 signs are retained, and functional
  pass/failure layouts are coherent. The broad saved-evidence/lifecycle suite
  passed 218 tests; independent closure review passed 51 focused tests without
  findings. This remains unexecuted infrastructure, not scientific evidence.
- Latest independently reviewed saved-balance adjudication sources:
  `6d355713` with immutability closure `f7a680d8`. The adjudicator reuses the
  factory-owned composition Actions, binds all 14 exact Action identities and
  saved interface arrays, treats rounded display values as non-authoritative,
  and performs no recovery, norm, solve or factor work. The broad affected
  evidence/lifecycle suite passed 129 tests before final hardening; the final
  affected suite passed 55 tests and the closure reviewer passed 29 focused
  tests without findings. This remains unexecuted infrastructure.
- Latest independently reviewed scientific replay budget source: `5f5d72e4`.
  All 123 ordered positive scalar budget leaves are archive-bound, and all
  five registered cases pass topology-only replay preflight. The largest
  registered equilibrium and composition envelopes remain within their
  declared 4 GiB exact-work limits; the separate supervisor cap remains
  6 GiB RSS. No scientific operator was evaluated.
- Latest independently reviewed numerical replay binding sources:
  `758f7375` with factor-structure closure `bfe9bd2b`. The saved positivity
  matrix, factors, maps, diagonal and root scale are bound to the producer and
  scaled evidence. Unit-lower/upper structure is re-established before a
  candidate or valid HOLD can be admitted. The closure suite passed 42 tests.
- Latest independently reviewed solve-free case-adjudicator sources:
  `e0a7e4ef`, retained-evidence closure `74e591c8`, and retained-lifecycle
  closure `597b1217`. All indexed semantic members plus exact start/terminal
  receipts are held and materialized from verified source handles during
  replay. Inverse blocks are consumed once; every numerical predicate, saved
  composition, balance, work count and final evidence identity is bound before
  the exclusive case receipt is written. The broad affected suite passed 212
  tests; final independent closure passed 47 focused tests with no findings.
  This is implemented infrastructure only and grants no scientific execution
  or registration authority.
- Latest independently reviewed plan-envelope preflight source: `dd3056d8`.
  It proves the bounded two-member ZIP envelope before `ZipFile` allocation,
  retains canonical plan bytes, and preserves `start.json` when full
  post-start validation fails. The closure suite and independent review each
  passed 21 focused tests without findings.
- Latest independently reviewed port producer sources: `85ab7883` with
  resource-envelope closure `e5aec919`. The factory emits the ordered 27
  trace ports, caches each referenced exact interval once, owns all CSR/action
  evidence, and charges the frozen 88*N trace and workspace envelope before
  extraction. Independent closure passed 35 focused tests without findings.
- Latest independently reviewed saved-observation producer sources:
  saved interface `d0b159b7` with resource and nested-Action closures through
  `cb452be8`; signed norm `deedeed5`; saved work `80c20747` with conversion,
  resource and display closures through `a134190a`; and the common-state
  bundle `751f7ae5` with factory-only state binding `46dc032b`. The interface
  retains separate analytic, 48-point and 64-point band routes; work retains
  one support result and an independent 48-point virtual-work route; norm
  retains raw 48/64 observations and identified unavailable values. Exact
  Action/Fraction work, nonzero conversion underflow, array ownership and
  outer/nested resource limits are enforced. Final independent reviews have
  no findings. The final affected suite passed 158 tests in 76.40 seconds.
  These factories perform two state recoveries including the support rebound,
  one support recovery, 16 band observations, two norm observations, and zero
  equilibrium solves or factorizations.
- Latest independently reviewed child case producer source:
  `2b4f2e84742973854fcadd7927ff833a8ba05eaf`. It writes `start.json`
  before topology construction, validates the retained envelope and the
  canonical post-start reread, performs exactly two frozen assemblies and
  scalings, one KKT factor/candidate solve, one positivity factorization and
  one inverse stream, then writes `evidence_index.json` last. The parent broad
  affected suite passed 208 tests in 69.61 seconds; independent review passed
  21 focused and 135 bounded dependency tests with no remaining findings.
  No registered case was launched. See
  `B3_GE_E4_PL_G0_F03_LOCAL_SCIENTIFIC_CASE_PRODUCER_RESULTS.md`.
- Last scientific diagnostic source: `59753d97964795bbe0599c8fa02d44170b2fa8a4`
  (saved-state spatial residual diagnostic). Last equilibrium source remains
  `e7908c1ad3dcff1cf9bc957ba8fd0fe1fe49b5b5`. Neither the comparator
  correction nor saved-only audit changed a mathematical operator.
- Main was observed clean at `be41a77a62e1cd7e1767bda6e955253af0819f91`,
  version 0.4.7. No product promotion or publication occurred.
- Controlling programme: `B3_GE_E4_PL_B2_COMPLETE_PROGRAMME.md`, revision 4.
  B3-GE remains principal; the distinct physical B2 option remains required.

## Latest completed work

1. Finite-pad independent-axis screen: 18 supervised cases completed and
   passed their algebraic/resource checks at source `584835f1`. Owned
   snapshots enabled separate endpoint diagnostics at `bfff7f0d`.
   Both evidence sets passed independent integrity/descriptive review.
   See `B3_GE_E4_PL_G0_F03_FINITE_PAD_AXIS_RESULTS.md`.
2. Endpoint-space comparison at `2b64174b`: ten meshes times P1/hybrid/
   enriched = 30 complete equilibria, preserving each family's partial
   states. **All ten decisions remain UNRESOLVED_AUXILIARY_NORM** because
   enriched's registered 32/64 squared-norm change exceeded 0.001.
   All other frozen metrics passed. Independent review accepted evidence
   integrity and retained HOLD. See
   `B3_GE_E4_PL_G0_F03_ENDPOINT_COMPARISON_V1_RESULTS.md`.
3. Separate pure analytical norm study at `45d3f1aa`: all nine comparisons
   passed against independent Decimal Green quadrature; maximum relative
   operator error `1.66524e-13`. Independent final review accepted this
   norm validation only. See
   `B3_GE_E4_PL_G0_F03_ANALYTICAL_NORM_V1_RESULTS.md`.
4. Joint shell/beam/interface refinement at `707cb39d`: six complete
   supervised cases, comprising 12 fresh equilibria and six reused middle
   states. All numerical checks passed and reused physical arrays/metrics
   matched exactly. **UNRESOLVED_JOINT_REFINEMENT**: every family/topology
   trend and every final topology/family comparison remains open. The
   registered execution is consumed; final adjudication exit1 is the
   intended failure disposition, not a reason to retry. See
   `B3_GE_E4_PL_G0_F03_JOINT_REFINEMENT_V1_RESULTS.md`. Independent review
   accepted the evidence and retained HOLD on mechanics, reproducing all
   saved spectra, physical-force recovery and trend predicates without
   structural or norm-constructor reruns.
5. Saved-state variational attribution at `f8f8e85`: all three Q4
   middle/fine family checks passed, with no equilibrium or Schur solve.
   Independent review accepted raw integrity and bounded interpretation.
   See `B3_GE_E4_PL_G0_F03_VARIATIONAL_ATTRIBUTION_V1_RESULTS.md`.
   The continuous eliminated-primal derivation also passed independent
   mechanics review; that acceptance is not numerical qualification.
6. The independent polynomial Ritz reference, exact root constraints,
   physical recovery, continuous Green norm, bounded archive and five-level
   execution harness were frozen at `e7908c1a` and all five registered
   equilibria completed. Canonical adjudication is **FAILED_EVIDENCE** due
   to a Python/NumPy numeric-type comparison after JSON serialization.
   The first integrated unit run passed51 checks. Following independent
   findings,23 focused operator/check tests and48 affected integration tests
   passed. These are overlapping test inventories, not summed coverage.
   Independent postreview verified215 arrays and exact numerical metric
   parity, but retained two saved-action failures and unresolved physical
   settling. The comparator is corrected;25 affected tests and independent
   scoped code review passed. See `B3_GE_E4_PL_G0_F03_PRIMAL_RITZ_V1_RESULTS.md`.
   No reference convergence or G0B acceptance is implied.
7. The registered saved-only audit at `c8b2f78d` completed5/5 children
   with zero new equilibria/assemblies. Integrity PASSED; canonical status
   **FAILED_NUMERICAL_SCREEN**, exit1, retaining n16/n24 action failures.
   Independent postreview accepted integrity with numerical/physical HOLD.
   All21 focused mock tests passed after review fixes. See
   `B3_GE_E4_PL_G0_F03_PRIMAL_SAVED_AUDIT_V1_RESULTS.md`. The new32-file
   immutable inventory SHA is
   `5073230a813bf9acef534d756ac05fb7deb29d1f7cf7caae507db94afc99014d`.
8. Exact saved-pose attribution at `d0b6d090`:3/3 cases PASSED, exit0;
   independent review accepted diagnostic integrity and attribution.
   Coefficient reconstruction explains the endpoint discrepancy; floating
   evaluation and direct action are much smaller. Original failures and
   physical HOLD remain. See `B3_GE_E4_PL_G0_F03_PRIMAL_EXACT_POSE_V1_RESULTS.md`.
   Its25-file immutable inventory SHA is
   `e7f0b5c8a8a403d7785ddba793e8061628b8b1b163ba4251338b63c3f0e5de0a`.
   All29 integrated synthetic/mock tests and the five affected final
   runner mocks passed (overlapping inventories); raw logs are preserved.
9. Spatial residual diagnostic at `59753d97`: 3/3 cases PASSED, exit 0.
   Independent postreview accepted integrity and descriptive localization,
   reproducing all 126 metrics and canonical summaries with no field/rule
   rerun. Largest metric `1.1651611328125e-13` against `1e-10`.
   The complete serial run took 21.5181126 s, with maximum sampled child
   RSS 105,488,384 bytes. Zero new equilibria or native element operations.
   See `B3_GE_E4_PL_G0_F03_SPATIAL_RESIDUAL_V1_RESULTS.md`.
   Completed 35-file inventory SHA:
   `43a9e2f5064f87b4e32f5e36e6158ae70fd6e0a01617765e5af5c1c3516bcbc7`.
   All 46 integrated checks passed; the 34/28 final affected checks also
   passed (overlapping inventories). All 13 raw development logs, including
   initial failures, and pre/post reviews are sealed with the evidence.
10. Local classical operator foundation at `7cb7b774`: 79 distinct current
    synthetic checks pass across final affected groups (30 foundation,
    19 corrected norm/cross-method, 30 unchanged Decimal oracle). Independent
    reviews accepted the bounded foundation and separately authored oracle.
    The earlier 75-pass run missed Duffy-weight underflow; the independent
    probe, two red regression tests and all fixes are preserved. Exact pad
    moments, membrane patches, C0 trace continuity, free root slope, shared
    ownership/resource guards and full piecewise Green norm are implemented.
    Zero new equilibria/native operations; physical HOLD remains. See
    `B3_GE_E4_PL_G0_F03_LOCAL_OPERATOR_PROOFS_V1_RESULTS.md`. New immutable
    39-file proof inventory SHA:
    `b26d4595f6b883d76ad9f2c66cb04f822e3cd8c9b97997ac2cce1f30c870206a`.
11. Sparse classical assembly and exact-transfer/work/numerical probes at
    `66b6e109`: 37 distinct current tests pass (assembly10, transfer6,
    work7, condition14), with independent final source/mechanics review.
    Sparse global KKT assembly performs no physical solve. Exact P preserves
    full sparse membrane/beam/root/load operators on admitted nested spaces.
    Work identities cover constant line densities and both atoms. Two
    condition-bound methods have a <=64 synthetic exact-Fraction prototype;
    neither scientific method is selected. Five malformed sparse-buffer
    regressions failed before validation was fixed; all raw logs remain.
    See `B3_GE_E4_PL_G0_F03_LOCAL_ASSEMBLY_PROOFS_V1_RESULTS.md`. New closed
    26-file archive `f03-local-assembly-proof-v1` inventory SHA:
    `d02087acd268b0c55cf173582ff0d08a79d20cf71b9b4f7cbb1cc1fd4bfdbf46`.
12. Sparse numerical building blocks and full classical recovery at
    `ade088e9`: 48 distinct current tests pass (interval certificate22,
    scaled sparse8, positivity6, recovery12); independent final review is
    closed for the bounded batch. The mocked negative-square-root regression
    failed before correction; the initial source and all ten raw logs are
    retained. Exact scalar root guards, sparse full-residual positivity,
    physical dual scaling and polynomial/cosine work recovery are verified.
    Six p>=2 support lift residual actions are implemented; p1 lifts remain
    unavailable. No physical reference equilibrium or native evaluation ran.
    See `B3_GE_E4_PL_G0_F03_LOCAL_NUMERICAL_PROOFS_V1_RESULTS.md`. The closed
    23-file proof archive `f03-local-numerical-proof-v1` inventory SHA is
    `43f9a1c950acc315c6fed28548f5f6e40a822b934d566ae5f4eb6b1185817100`.
13. Actual sparse factor production and integration connection at `126a4eb1`:
    33 distinct current synthetic tests pass (producer19, integration12,
    connection2), with independent final review closed. Native sparse arrays
    and unordered columns are safely normalized without value arithmetic.
    Full-K positivity, one candidate solve and saved-column verification
    are connected on synthetic inputs. Root C normalization is restored;
    the full alternate-solution error bound now includes primary residual.
    The separate historical integration diagnostic remains. See the results
    report `B3_GE_E4_PL_G0_F03_FACTOR_INTEGRATION_PROOFS_V1_RESULTS.md`.
    Closed 22-file proof root `f03-factor-integration-proof-v1`, inventory SHA:
    `64ae0becbe72c8a949233e8be3c127c75697287f18f68a09e23476accab93868`.
14. Sparse physical/scaled state binding and root/free-slope rank at
    `7b017d08`: 30 distinct synthetic tests pass (state12, rank16,
    connection2), with independent final review closed. Full H/b bit parity,
    exact D interval and saved physical/action bounds are checked. Exact
    Gram/Sylvester enclosures certify port rank without adding a slope
    constraint or numerical eigensolve. A failed saved action now has an
    explicit FAILED label; the original misleading label and four initial
    rank test-fixture failures are recorded. Five raw logs remain preserved.
    No physical reference equilibrium or native element evaluation ran.
    See `B3_GE_E4_PL_G0_F03_STATE_RANK_PROOFS_V1_RESULTS.md`. Closed root
    `f03-state-rank-proof-v1` has 14 bound files plus inventory, SHA:
    `31bafde0e254091e46f538ab525e9d00c425322633b58c93dbe0fd9ec5a49d6c`.
15. Sparse exact trace binding and numerical equilibrium checks at
    `a858e787` (trace first saved at `22d99107`): 34 distinct tests pass
    (trace20, equilibrium13, connected candidate1), with independent final
    source/mechanics review. Exact extraction binds all27 station operators
    and actions plus direct root/tip/free-slope consistency. Numerical gates
    use actual rounded six-block scaling, separate physical shell/beam work
    and one owned snapshot throughout binding and metrics. Four regression
    failures before correction are preserved with all eight raw logs.
    See `B3_GE_E4_PL_G0_F03_TRACE_EQUILIBRIUM_PROOFS_V1_RESULTS.md`.
    Closed root `f03-trace-equilibrium-proof-v1` has18 bound files plus
    inventory, SHA `e331f76e9ae76ed23558fb7824a3e3a0e9b79ade5a2d6ee5dae5f617f998dc33`.
    The reviewed next recovery contract provides a certified-Action design,
    raw versus represented moment/load balance distinctions and an admissible
    Q1 support-lift derivation; executable proof was completed subsequently
    in item16, without changing that historical record.
16. Certified Action enclosures and supplemental Q1/Qp support recovery at
    `5be7447f`: 32 distinct checks pass (enclosure21, support9, connection2),
    with independent final source/mechanics review. Complete exact interval
    normalization precedes fixed-order Taylor enclosure. Q1 dual support
    routes, true nodal lift shifts, physical versus represented moment balance
    and actual versus nominal load integrals are explicit. A manufactured
    nonequilibrium residual is rejected despite matching work identities.
    All16 logs, including collection/implementation/guard/resource-fixture
    failures, are preserved. No physical equilibrium or native evaluation ran.
    See `B3_GE_E4_PL_G0_F03_RECOVERY_ENCLOSURE_PROOFS_V1_RESULTS.md`.
    Closed root `f03-recovery-enclosure-proof-v1` has26 bound files plus
    inventory, SHA `861a6b02b09fead9b6af8af0c2efc6123c91da097a5688caa15f0369c431c1db`.
17. Owned saved interface/band and support/virtual-work components at
    `5acfd119`: 27 distinct tests pass (interface13, work14), with independent
    final code/mechanics review. All192 signed total/line band comparisons
    bind to recovered and owned saved functionals. Complete local C0 P_(p+2)
    test charts retain all four virtual terms, saved defects and zero checks.
    Matching saved nonstationary shifts still fail. Ownership timing and
    nested/live-Action storage bounds are corrected; eight passing logs and
    the non-test shell exit are recorded. No physical equilibrium/native
    evaluation/norm operation ran. See
    `B3_GE_E4_PL_G0_F03_SAVED_RECOVERY_COMPONENT_PROOFS_V1_RESULTS.md`.
    Closed root `f03-saved-recovery-component-proof-v1` has18 bound files plus
    inventory, SHA `3d738d67a08da8dacfe51c8dc6d23756de0625329f3e0f3c304675279a78e856`.
18. Signed raw norm observation and saved 48/64 binding at `8bb018f7`: 62
    affected tests pass, including literal finite-channel total overflow at
    both orders. The historical strict wrapper matched130/130 successful
    dictionaries bitwise and five historical failure contracts exactly.
    Independent source/mechanics and corrected-archive review found no issue.
    The initial provenance-deficient v1 archive is preserved as FAILED_EVIDENCE;
    corrected closed root `f03-signed-norm-proof-v2` has19 bound files plus
    inventory, SHA `6f01c6fc91fd16034c2813ba77be637db1e6278de582273e9025eb9bc1e35926`.
    See `B3_GE_E4_PL_G0_F03_SIGNED_NORM_COMPONENT_PROOF_V2_RESULTS.md`.
19. Saved numerical/interface/work/norm composition at `271d88d0`: 94 affected
    tests pass and the independent source/mechanics/archive review has no
    findings. One owned q/eta snapshot binds all four component authorities,
    complete compiled topology and every saved identity. Deep nested resource
    guards run before component entry; the fixed work is three recoveries, two
    norm observations and zero solves/factorizations. The initial v1 archive is
    preserved as `FAILED_EVIDENCE`; corrected closed root
    `f03-saved-recovery-composition-v2` has 29 evidence files plus inventory,
    SHA `1e8ad63fe2396d4a6d18b22ae8bf34ad211a6603adb8966c542167f4a837bd3e`.
    See `B3_GE_E4_PL_G0_F03_SAVED_RECOVERY_COMPOSITION_V2_RESULTS.md`.
20. Local-scientific runner foundation at `9f4a6be0`: the exact five-case
    topology/resource inventory, inverse archive plan, process-tree
    supervision, exclusive lifecycle receipts and bounded array storage are
    implemented. The final affected suite passes 83 tests. Independent review
    found and verified corrections for fabricated preflights, resource
    binding, detached descendants, root-PID ownership, bounded receipt reads,
    ZIP size/mutation paths and every validation-before-allocation issue. The
    final review has no findings. This is `IMPLEMENTED_NOT_QUALIFIED`; it
    assembled and solved no scientific case and grants no registration or
    execution authority. See
    `B3_GE_E4_PL_G0_F03_LOCAL_SCIENTIFIC_RUNNER_FOUNDATION_V1_RESULTS.md`.

Raw roots under `.qualification/b3-ge-e4-pl/` are respectively
`f03-area-axis-v1`, `f03-area-axis-analysis-v1`,
`f03-endpoint-comparison-v1`, `f03-analytical-norm-v1`, and
`f03-joint-refinement-v1`, `f03-variational-attribution-v1`, and
`f03-primal-ritz-v1`, `f03-primal-saved-audit-v1`, and
`f03-primal-exact-pose-v1`, and `f03-spatial-residual-v1`. Reports retain their
registration/adjudication hashes; raw reviews and execution provenance
are saved with the latest roots. All these executions are consumed.
Do not overwrite, retry or relabel them. Earlier failed/aborted evidence
remains intact, including finite-pad feasibility v1's adjudication failure.

## Physical finding and exact next action

The earlier attachment-only tip plateau did not establish structural
convergence. Joint refinement from (8,16,16,8) to (16,32,32,16) changes
endpoint-space tip displacement by4.69-5.42%, energy by6.65-8.51% and the
full multiplier functional by4.62-5.09%. Enriched gap RMS/motion is only
0.14-0.16% on the finest meshes, but reactions/energy/band transfers remain
unsettled. Hybrid/enriched fine tips nearly coincide while terminal-band
force/moment differs about10%. P1 remains much further from endpoint
spaces. All finite Schur modes are positive; no continuum stability claim.

The attribution identity is now verified. Enriched's potential change is
mostly shell energy distance (0.77136 J), with beam distance 0.01472 J and
small net constraint work 0.00003296 J. This is a discrete-state split,
not causal continuum-error attribution; cancellation and endpoint error
remain possible. P1 and hybrid have substantial negative constraint work.

The primal reference root `.qualification/b3-ge-e4-pl/f03-primal-ritz-v1`
is now consumed: n=4,8,12,16,24, five equilibria,10 integration assemblies,
60.9037s overall and220.77MiB maximum sampled child RSS. Original
registration/adjudication and all36 completed evidence files are preserved.

The saved-evidence audit is complete and consumed. Its32-file inventory
and the original36-file parent inventory are frozen. Retain the original
FAILED_EVIDENCE and the audit's FAILED_NUMERICAL_SCREEN with n16/n24
saved-action failures (1.49057e-11 and1.15333e-10 against1e-11).
Their only failing component is transverse b'' at s=1. Exact independent
reconstruction now attributes it to the saved coefficient route, while
retaining all floating arithmetic and exact endpoint triangle bounds.
This does not identify every operation inside that reconstruction or
waive either failure. The exact diagnostic changed no saved state.
Independent diagnostic settling also fails: last energy changes4.52%,
2.60%, and full-functional changes2.87%,3.16%; only16/45 scalar sequences
pass. The reference is not ready for FE-as-reference comparisons.
No automatic degree extension or physical rerun is authorized by this
checkpoint. Diagnose and review the next numerical formulation before
any new scientific registration.
This does not replace required executed external comparisons.
Do not automatically add uniform refinement, change
tolerances, drop P1, relabel any HOLD, or promote a production space.
Native full-vector/shear/drilling and all other G0 foundations remain open.

The completed spatial study localizes persistent defects near root pads
(cells 12/30) and right supported/free corners. Its volume-squared totals
are 21.69397, 17.02412, 11.53795 and free-edge-squared totals are 0.0264247,
0.00961514, 0.00454445 for n12/n16/n24. At n24, rightmost free-edge segments
contain 85.4% of that squared edge defect. These are descriptive measures,
not physical-error percentages, acceptance bounds or production-space choices.

The local-reference mechanics foundation and its limitations passed
independent review. Draft SHA:
`36ce310a99df390fa95c83fd2e346315fb46cc795665f6e5de1ba747ddb4bc3b`;
see `B3_GE_E4_PL_G0_F03_LOCAL_REFERENCE_DESIGN_REVIEW.md`.
The operator contract and bounded synthetic proofs are now accepted; see
`B3_GE_E4_PL_G0_F03_LOCAL_OPERATOR_CONTRACT.md` and its results report.
Their raw archive is `.qualification/b3-ge-e4-pl/f03-local-operator-proof-v1`
(39 bound files plus inventory); it is closed and must not be extended.
The sparse eliminated-primal assembly, exact nested transfer and bounded
manufactured work identities are now implemented and independently reviewed.
The latest closed proof root is `f03-saved-recovery-component-proof-v1`
(18 bound files plus inventory); it must not be extended. Its source is
`5acfd119` and its inventory SHA is
`3d738d67a08da8dacfe51c8dc6d23756de0625329f3e0f3c304675279a78e856`.
See `B3_GE_E4_PL_G0_F03_SAVED_RECOVERY_COMPONENT_PROOFS_V1_RESULTS.md` for
27 distinct focused passes, source/limit bindings and independent review.
The scaled candidate solve,
streamed interval condition certificate, supplied-factor sparse positivity
proof and complete polynomial/cosine work recovery are now implemented and
reviewed on synthetic/manufactured inputs. A bounded actual sparse factor
producer and integration perturbation verification are now connected too.
Physical scaling/state binding, three-root/free-slope rank, exact trace
binding, separate shell/beam integration and numerical stationarity/energy
checks are implemented and independently reviewed on synthetic/manufactured
inputs. Certified Action comparisons and the supplemental Q1 support-lift
family now have independent executable proof, including route/shift checks.
The original recovery's unavailable-P1 status remains unchanged; the separate
helper reports its own family. Owned density/cosine/atom binding and partition,
total/line-only bands, saved support routes, raw shift checks and the complete
local scaled virtual-work inventory are now independently reviewed components.
The signed raw norm observation seam, saved48/64 binding and complete saved
numerical/interface/work/norm composition are now complete. The exact next
action is to freeze and independently review the numerical protocol and a new
one-use scientific registration without changing the physical operator or
reusing any consumed execution authority.
Full protocol remains controlled by
`B3_GE_E4_PL_G0_F03_RECOVERY_ADMISSION_NEXT_CONTRACT.md`. Any independently
archived lift root/tip observations need explicit binding; present SavedWork
stores complete coefficient charts. Complete saved archives and independent
adjudication before new scientific registration. Preserve raw physical moment balance
alongside the represented gamma identity, and nominal alongside actual
held-frequency load integrals. Do not remove a predicted physical defect.
Then complete and independently review a frozen numerical protocol and new
registration. No scientific case family or certificate method is selected.
The <=64 exact-rational probe remains a synthetic oracle, never a dense
scientific fallback. Factor peak memory needs external supervision; streamed
inverse columns still require 8*N*N raw saved bytes. Supplemental Q1 support
recovery is now available on bounded manufactured inputs, not yet qualified
on scientific cases. Decimal cosine displays remain noncertified; use the
separate fixed-order enclosure for acceptance and preserve unresolved bounds.
Preserve the same physical operator, held J/gamma, three root
constraints/free slope, signed reaction and full-functional criteria.
Mesh/degree inventories, integration, conditioning, resource and convergence
gates remain to be resolved before any new scientific registration. In
particular: preserve the implemented positive exact intervals whose endpoints
collapse in binary64, retain shared tensor conformity, and bound actual
footprint incidence/nnz/fill/workspace growth. Hanging nodes remain outside
the new helper's scope and require their own conformity proof if introduced.
The complete piecewise norm is synthetically checked; its input bounds and
active normal-weight guard must remain part of numerical admission.
The stress-jump and support-lift signs are independently verified on bounded
manufactured fields; retain them in the general recovered-field implementation.
The controlling correction is `B3_GE_E4_PL_G0_F03_SPARSE_INTEGRATION_ERRATUM.md`:
root C uses max(1,Frobenius norm); the historical integration-only sensitivity
is distinct from the full saved-state alternate error, which includes the
certified primary residual. Both retain separate 1e-6 gates and are null when
alpha>=1. This supersedes incompatible root/bound paragraphs of the older
SPARSE_INTEGRATION_CHECKS and LOCAL_NUMERICAL_ADMISSION drafts.
Other numerical-admission design remains in `B3_GE_E4_PL_G0_F03_LOCAL_NUMERICAL_ADMISSION_DRAFT.md`:
same held energy-diagonal scaling, full stored H, true condition upper bound,
safe backward denominator, explicit positivity/integration/resource checks.
All-column certification has quadratic evidence/work; triangular comparison
can be pessimistic. Compare/select before registration, never as a fallback
after a failed scientific bound. No automatic uniform/global-degree run.

No scientific process is active. The saved interface/work/norm components,
complete composition, protocol, runner foundation, numerical evidence and
solve-free adjudication path through `597b1217` are independently reviewed.
The numerical schema
review closed two P1 findings: native factors are CSR end to end and the
Q1_L0-to-Q2_L0 transfer is present. The resulting focused inventory passed
172 tests; the corrected composition/balance addition passed 133 focused
archive and lifecycle tests; independent closure review passed 32 focused
checks without findings. The assembly/scaling diagnostics passed 135 focused
archive/lifecycle checks and their closure review passed 17 checks without
findings. The independently reviewed case receipt at `103cf51e` passed 218
broad saved-evidence/lifecycle tests and 51 focused review tests. The saved
balance adjudication at `6d355713`/`f7a680d8` is independently closed. The
bounded plan-envelope, evidence-production prerequisites and exclusively
writing child producer are now complete and independently reviewed. The exact
next action is the top-level one-use coordinator. It owns immutable
registration, serial supervised launch, terminal receipts, solve-free
adjudication and aggregate disposition. It must invoke the child only once per
registered case, preserve every partial result, and never retry a consumed
attempt. Registration remains barred until the coordinator passes its bounded
lifecycle/replay tests, preflight demonstrations and independent review on
clean committed sources. The accepted proofs grant no scientific execution
authority. Current product/schema sources are committed; this checkpoint text
records the restart boundary.
All consumed diagnostic sources and completed inventories stay frozen.
No release approval is being exercised. Keep main unchanged during G0.

## 23 September 2026 registration prerequisite

The canonical F03 registration schema and bounded synthetic tests are
independently reviewed, as recorded in
`B3_GE_E4_PL_G0_F03_REGISTRATION_SCHEMA_RESULTS.md`. The child-side identity
checks are independently reviewed in
`B3_GE_E4_PL_G0_F03_CHILD_IDENTITY_RESULTS.md`; one untracked-source finding
was closed. Neither batch registered or launched a scientific case. Read-only
case replay, cross-case adjudication and the serial coordinator remain open.
Do not create the one-use scientific registration
until these prerequisites pass bounded tests and independent reviews on clean
committed source.

## 23 September 2026 typed-cancellation prerequisite

The process-tree supervisor now carries cancellation in a validated typed
receipt, with independent closure review and 55 passing affected tests.
`B3_GE_E4_PL_G0_F03_TYPED_CANCELLATION_RESULTS.md` records the scope and
closed findings. It was not a scientific execution. The next coordinator
prerequisites are cross-case adjudication, followed by the serial one-use
coordinator and its preflight/review gate. Read-only case replay is now
independently reviewed, as recorded in
`B3_GE_E4_PL_G0_F03_READ_ONLY_REPLAY_RESULTS.md`; it did not launch a case.
The exact cross-case implementation boundary is saved in
`B3_GE_E4_PL_G0_F03_CROSS_CASE_NEXT.md`.

## 24 September 2026 current F03 diagnostic checkpoint

The reviewed support-row candidate source is `7dd70e72`, and evidence was
recorded at `11f4a39a` on the isolated integration branch; accepted main
remains untouched. The complete
current result is
`B3_GE_E4_PL_G0_F03_Q6_X2_SUPPORT_REUSE_RESULT_20260924.md`, with raw
tracked receipts and locally retained, Git-ignored numerical archives.
There is no active scientific process, no one-use formal registration, and
no release action.

The saved X0/X1/X2 Q6 state-component bounds are recorded in
`B3_GE_E4_PL_G0_F03_Q6_THREE_GRID_COMPONENT_BOUNDS_20260924.md`.
They apply to exact mappings through stored binary physical scales and do
not settle derived physical observables. The source-level X2 reuse run
completed in 2,082.77 s, with spatial audit 63.20 s shorter than preserved
V1 in one comparison. The physical and spatial outputs agree within the
reported tiny summation differences, and independent read-only review found
no unresolved issue in that comparison. Unaffected phases varied; no
repeatable complete-route speedup is established. The draft 1,800 s
resource envelope remains unmet by 282.77 s. The run is unregistered and
not installed-artifact qualification.

The next decision is prospective: finish explicit error propagation to
every registered physical functional, resolve native line/port moment and
stability mechanics, and freeze/review a feasible installed scientific
resource protocol before any one-use case registration. Do not describe
this classical Q6 diagnostic as G0B or native F03 acceptance. G0B remains
open and G1 remains barred.

## 24 September 2026 native station-port diagnostic

The bounded six-channel native retained half-cell station port and its
independently reviewed tests are recorded in
`B3_GE_E4_PL_G0_F03_NATIVE_SPATIAL_PORT_RESULT_20260924.md`. It closes a
kinematic proof seam only. The next mechanics boundary is the shell-side
six-channel trace and then the relative-pose line law and coupled stability
checks. G0B remains open; no scientific registration was consumed.

The matching bounded flat-reference shell spatial port is recorded in
`B3_GE_E4_PL_G0_F03_SHELL_SPATIAL_LINEAR_PORT_RESULT_20260924.md`.
It uses actual Q4/S3 physical stiffness and excludes numerical drilling
completion. Native and shell port seams are now checked separately, but
finite shell pose, relative-pose curvature, exact line multipliers, and
coupled stability remain unresolved. G1 remains barred.

## 24 September 2026 restart pause — finite shell pose candidate

User requested pause for app restart. The isolated integration branch is at
`5736f071e63c65f4ac51883e5ecfcbaf719a2c69`; accepted main is untouched.
There are uncommitted edits in
`scripts/_b3_e4_f03_shell_finite_pose_candidate.py` and
`tests/test_b3_e4_f03_shell_finite_pose_candidate.py`, plus this checkpoint.
The director-constrained four-sample finite pose passed 10 focused tests before
the last edit. Independent read-only mechanics review found no defect within
its bounded flat-panel domain and identified production gaps: E4 trial-state
binding and drill chart pullback, layer-specific eccentric samples, chart
transport, exact derivatives and line/KKT stability. The last edit added
second-order directional automatic differentiation and tests; those changes
have **not been run or reviewed**. Resume by inspecting the dirty worktree,
running the new focused test, fixing any failures, then obtaining independent
review before recording this candidate as G0 evidence. No scientific process
or one-use registration is active; G0B remains open and G1 remains barred.

## 24 September 2026 resumed finite-pose diagnostic

The unverified derivative edit above was tested, strengthened with all-column
reference checks, and independently reviewed. The finite pose was corrected
from an unconstrained fit that leaked shear-induced spin to a
director-constrained planar fit. The bounded result and exact remaining
boundaries are recorded in
`B3_GE_E4_PL_G0_F03_FINITE_SHELL_POSE_CANDIDATE_RESULT_20260924.md`.
The candidate and related F03 spatial diagnostics passed 89 focused tests.
The next work is binding this physical port to actual E4 Q4/S3-V2D trial
states and coordinate charts, then deriving the relative-pose line potential
and full coupled KKT. G0B remains open; G1 remains barred.

The flat +Z additive-total E4 coordinate adapter and its reviewed chart
derivatives are separately recorded in
`B3_GE_E4_PL_G0_F03_E4_ADDITIVE_POSE_ADAPTER_RESULT_20260924.md`.
It matches the selected Q4/S3-V2D generic corotational rotation convention;
it does not authenticate an E4 material trial. Combined focused diagnostics
passed 92 tests. The next boundary is the validated coupled trial and
relative-pose multiplier curvature.

The point-level relative-pose multiplier curvature is now checked with
native B3 and flat E4 shell station maps at zero and nonzero reference
eccentricity, as recorded in
`B3_GE_E4_PL_G0_F03_COUPLED_POINT_WORK_RESULT_20260924.md`.
Four focused cases passed and independent mechanics review found no issue.
This is not a weak line or authenticated material trial. Those remain the
next G0B mechanics boundary; G1 remains barred.

The next bounded seam evaluates actual four/eight-element Q4 and S3-V2D E4
elastic corotational responses from one frozen virgin predecessor and the
same total coordinates as the shell pose. Its result is recorded in
`B3_GE_E4_PL_G0_F03_E4_MULTI_ELEMENT_TRIAL_RESULT_20260924.md`.
The focused suite passed 22 cases; combined neighboring diagnostics passed
64. Independent review found and then verified fixes for mutable definition
guards, with no remaining finding in the declared scope. This is a small
dense G0 oracle, not a committed owner or plastic trial. The next mechanics
boundary is a fixed-host segmented six-channel weak line with exact
multiplier spaces and full coupled KKT stability. No one-use scientific
registration was consumed. G0B remains open; G1 remains barred.

## 24 September 2026 prospective ecosystem-policy transition

Adopt `ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1`, revision
`2026-09-24.1`, from
`C:/Github/ANYopenSoft/governance/ECOSYSTEM_PHILOSOPHY.md` (SHA-256
`92e458e1c3d1c252fdc22c2f1d90c2ffb976601e67a59545d162ec3d6110468d`).
For future unregistered Level-A exploration, consolidate per-helper
administrative dossiers and repeated full reviews into this living record,
reproducible focused checks, and review of consequential assumptions. Retain
the complete G0–G6 scientific and release gates, frozen F03 registrations,
consumed one-use authorities, explicit no-run boundaries, protected evidence,
resource limits, installed-artifact and external-reference requirements.
The next permitted integrated development slice, once this task is resumed,
is fixed-host segmented six-channel weak-line work using the committed E4
trial and native B3 station ports; it is not a formal F03 assessment run.
No amendment is needed for that exploratory slice. Any change to a frozen
F03 formal procedure or criterion requires a prospective task-owner amendment.
The implementation goal remains paused at `201188851322a1c9d867a1b76f396add1d3b756d`.

## 24 September 2026 resumed F03 integrated development slice

The user explicitly resumed the programme under policy
`ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1` revision `2026-09-24.1`.
The bounded line diagnostic now integrates the objective six-channel joint
work over fixed shell-host, native half-cell, and multiplier-knot segments.
It evaluates the E4 elastic trial and shell pose from one total-coordinate
vector, and native B3 station poses from one retained trial state.
Piecewise-constant and continuous-linear multiplier spaces are *candidates*,
not selections.
The diagnostic also assembles a small dense zero-multiplier reference KKT
from the E4 and B3 tangents and the weak constraint Jacobian, with physical
support elimination and work-conjugate scaling. The line's weak derivative
agrees with that KKT Jacobian; Q4/S3 and both multiplier candidates solve
the bounded loaded system with small scaled and physical residuals.

Focused weak-line/KKT tests passed **28/28**, including six common rigid-mode
constraints and the physical-residual assertion. The neighboring E4 trial,
point-work, finite-pose and spatial-port
suite passed **81/81** before that assertion; no product mechanics changed
afterward. Independent read-only mechanics review found no correctness
blocker in the declared small flat virgin scope. Its request for a varying
reference-correspondence test was addressed with a rigidly rotated shell;
shell-host breakpoints are now directly checked. The review explicitly
did not establish quadrature convergence, mesh-independent inf-sup,
physical torque/load response, multiplier-space selection, nonzero-multiplier
geometric stiffness, or accepted coupled state. Those and the remaining
G0B foundation are the next integrated questions. No formal F03 run or
one-use authority was consumed; G1 remains barred.

A further bounded Q4 torque comparator applies 100 Nm at the native B3 tip
and solves the same reference line KKT using either the ordinary E4 tangent
or a separately assembled physical-only shell block with independent shell
drilling coordinates removed. It finds nonzero physical shell strain energy
and matching non-drilling shell response. Independent mechanics review found
no hidden circularity for that narrow existence result. Because both solves
share the line constraint and native B3 kernel, this is not an independent
physical-response oracle. The same 100 Nm reference case now also recovers
the physical-multiplier support residual and closes global force and moment
balance about a common origin, with a nonzero shell support share. Independent
review confirmed the residual sign and retained-coordinate treatment. The
same no-drilling comparison now passes on S3-V2D as well as Q4 at all three
tested mesh sizes (`n_s=1,2,4` with 4, 8 and 16 native half-cells): each has
positive physical shell energy and nonzero tip torque response, and deleting
all independent shell `rz` coordinates leaves the bounded response unchanged
within the test tolerance. This establishes only the flat, virgin, fixed-
thickness comparator with mesh-tied P0 spaces. Local traction balance,
thinning, physical convergence, distorted geometry and full F03 stability
remain open.

The flat diagnostic fixture now admits an explicit positive shell thickness
and passes it consistently to the in-plane, full E4 trial, and physical-only
assemblies. A three-thickness screen (`0.07`, `0.035`, `0.0175` m) on the
middle mesh with four P0 intervals produced tip `rx` values of
`1.36526e-5`, `3.48877e-5`, `6.07916e-5` rad for Q4 and
`1.41260e-5`, `3.82636e-5`, `6.45397e-5` rad for S3-V2D. The separate
bare native-beam solve gives `7.42857e-5` rad. Every coupled case has
positive physical shell energy, a small scaled KKT residual, and total
support moment `-100 Nm` about the beam axis. This is a finite-range
thinning trend toward the bare beam, not proof of the zero-thickness limit.
The shell's support moment was nonmonotone and changed sign: Q4
`-49.28`, `+19.79`, `+20.93` Nm; S3-V2D `-51.87`, `-0.25`, `+5.15` Nm.
An initial diagnostic assertion that shell energy, then shell support-moment
magnitude, must decrease monotonically failed on both topologies; those
assumptions are invalid for this load-controlled, statically indeterminate
connection. The revised check uses tip compliance relative to the bare beam
and global moment balance. The five affected diagnostic files passed
**89/89** tests. Thickness convergence, local interface transfer and the
physical external target remain open; F03/G0B remain open and G1 barred.
The same small KKT route also executes on three Q4/S3 mesh sizes with 4,
8 and 16 native half-cells and matching 2, 4 and 8 multiplier intervals
for both P0/P1 candidates. This execution check is not a convergence or
inf-sup result.

An unregistered Level-A torsion screen held the flat 1 m native beam, 0.07 m
shell, left shell clamp, beam-root clamp, +100 Nm beam-tip `rx` load and
four-point segmented Gauss rule fixed. On shell resolutions `n_s=1,2,4`
with native half-cells `4,8,16`, the P0 tip rotation (rad) was:

| Shell | P0 intervals 2,4,8 tied to mesh | P0 intervals fixed at 2 |
|---|---|---|
| Q4 | `1.67254e-5`, `1.36526e-5`, `1.08545e-5` | `1.67254e-5`, `1.82472e-5`, `1.84406e-5` |
| S3-V2D | `1.71980e-5`, `1.41260e-5`, `1.10481e-5` | `1.71980e-5`, `1.87112e-5`, `1.85652e-5` |

At the *same* finest physical mesh (Q4 16 or S3-V2D 32 elements, eight
native B3 elements), nested P0 spaces produced these raw outputs. The
relative-pose gap is sampled at 129 equally spaced stations, with rotations
scaled by 1 m. The final column is the smallest singular value of a chosen
work-congruence-scaled algebraic KKT, **not** an inf-sup measure.

| Shell | P0 intervals | Tip `rx` rad | Shell physical J | Shell support `Mx` Nm | Gap L2 m | Gap max m | Scaled algebraic min singular |
|---|---:|---:|---:|---:|---:|---:|---:|
| Q4 | 2 | `1.844058809813e-5` | `3.211551421236e-4` | `-56.2649454614` | `2.759511673074e-6` | `7.800093159069e-6` | `3.003224994536e-6` |
| Q4 | 4 | `1.387728678255e-5` | `3.348266975556e-4` | `-50.4942851897` | `1.080867442640e-6` | `3.213590378424e-6` | `2.631012149539e-6` |
| Q4 | 8 | `1.085451133077e-5` | `3.090653695304e-4` | `-27.0449263450` | `3.749723651701e-7` | `9.481218349173e-7` | `1.969073935270e-6` |
| S3-V2D | 2 | `1.856522608128e-5` | `3.279103708090e-4` | `-57.2532629379` | `2.763342752369e-6` | `7.806516716772e-6` | `3.043007881325e-6` |
| S3-V2D | 4 | `1.408074327543e-5` | `3.469217307510e-4` | `-52.7902713832` | `1.090182833072e-6` | `3.237044224545e-6` | `2.707126745865e-6` |
| S3-V2D | 8 | `1.104809661623e-5` | `3.201529944956e-4` | `-31.3330159916` | `3.750010327881e-7` | `9.629215417814e-7` | `1.989278282796e-6` |

These are descriptive development outputs from the diagnostic functions,
not acceptance thresholds or a matched external comparison.

Independent mechanics interpretation found strong multiplier-resolution
sensitivity in this tip observable. More P0 rows reduce off-station gaps but
also stiffen the response; the screen cannot distinguish coarse-space slip
from fine-space locking or identify a physical limit. Next compare against a
matched independent torsion target, examine a physically norm-scaled
interface-stability measure, and test the continuous/dual candidates across
the required mesh ratios. The formal F03 run and G0B remain open.

The same finest physical mesh was then held fixed for a 12-case P0/P1
resolution screen using the actual coupled linear KKT and 129-station
nonlinear relative-pose gap recovery. Source:
`scripts/b3_e4_f03_weak_line_resolution_screen.py`; raw outputs:
`B3_GE_E4_PL_F03_WEAK_LINE_RESOLUTION_DIAGNOSTIC_V1.csv`. Q4 P1 tip `rx`
falls from `1.45677e-5` to `9.43760e-6` rad as intervals increase from
2 to 8; S3-V2D P1 falls from `1.46932e-5` to `8.97584e-6` rad. At eight
intervals, P1 is 13.1% below P0 for Q4 and 18.8% below P0 for S3-V2D,
while its sampled gap L2 is smaller. The free physical and scaled algebraic
residuals are small in all 12 solves. This comparison adds continuous P1
evidence, but the endpoint count differs from P0 and neither a matched
physical solution nor a norm-scaled interface stability bound is available.
Do not infer that P1 or P0 is more accurate or suitable for production.
The formal F03 run and G0B remain open; G1 is barred.

An additional unregistered native six-channel compliance screen uses the
complete retained B3 tangent and the same E4 trace, with force/moment
conversion at a fixed 1 m characteristic length and an independently checked
Neumann-cosine H^(-1/2) dual norm for both P0 and P1. Source:
`scripts/b3_e4_f03_native_line_compliance_screen.py`; immutable V1 raw rows:
`B3_GE_E4_PL_F03_NATIVE_LINE_COMPLIANCE_DIAGNOSTIC_V1.json`. On paired
`n_s=1,2,4` meshes with 2, 4 and 8 multiplier intervals, the minimum
dimensionless compliance quotient is Q4 P0 `0.6255, 0.3024, 0.1748`, Q4 P1
`0.2310, 0.1624, 0.1192`, S3-V2D P0 `0.6368, 0.3035, 0.1769`, and
S3-V2D P1 `0.2394, 0.1685, 0.1194`. Every finite matrix is positive in
this quotient, but the minima fall with this paired refinement. Maximum
scaled linear-solve residual is `8.74e-13`, Schur relative skew `5.49e-14`,
and the cosine tail-Gram relative bracket `9.15e-8`. The native supported
primal tangent has 36, 72 and 144 negative retained modes on the three
grids. Thus `C K^-1 C^T` is an interface *compliance* diagnostic, not the
positive-primal inf-sup quotient used for a coercive elastic displacement
space. The trend is a reason to inspect weak modes and matched physical
response, not proof of locking, instability or continuum failure. The new
P1 dual-norm checks passed **7/7**. F03/G0B remain open; G1 barred.

A V2 follow-up held the finest physical Q4/S3-V2D mesh and 16 native
half-cells fixed while varying only 2, 4 or 8 multiplier intervals; its
versioned raw result is
`B3_GE_E4_PL_F03_NATIVE_LINE_COMPLIANCE_DIAGNOSTIC_V2.json`. The minimum
quotient for Q4 P0 was `0.7981, 0.3503, 0.1748`; Q4 P1 was
`0.3933, 0.2165, 0.1192`. S3-V2D gives the same trend within the shown
precision. The minimum generalized eigenvector is numerically pure axial
`Fx` in all 12 flat-reference cases. Its dominant coefficients alternate
sign at every neighboring P0 cell or P1 node (1/3/7 changes for P0 and
2/4/8 for P1). This localizes the descending quotient to high-frequency
axial multiplier modes, **not** to the torsional load channel used in the
earlier response screen. It does not by itself prove a continuum inf-sup
failure: the native primal tangent is indefinite and the finite support,
trace norm, and physical convergence still need a reviewed interpretation.
Do not choose a coarse space solely by discarding these modes or claim
that a basis change into a dual space repairs the span. F03/G0B remain open.

The V3 fixed-primal follow-up decomposes the same minimum-mode compliance
into shell and native-beam blocks without changing the mode or norm; raw
values are preserved in
`B3_GE_E4_PL_F03_NATIVE_LINE_COMPLIANCE_DIAGNOSTIC_V3.json`. For Q4 P0,
the shell contribution falls `0.2148 → 0.1116 → 0.0651` and the beam
contribution falls `0.5833 → 0.2387 → 0.1096` over 2/4/8 intervals.
For Q4 P1 the corresponding sequences are
`0.1389 → 0.1040 → 0.0683` and
`0.2543 → 0.1125 → 0.0509`; S3-V2D is similar. Each pair sums to the
minimum quotient within the checked arithmetic tolerance. Both domains
lose compliance in the alternating axial mode. The shell finite-window
trace is therefore not the sole observed contributor; this split does not
establish a causal continuum explanation or a valid multiplier selection.

A separate G0 local-translation pose candidate now places the shell-side
origin at the interpolated material midsurface point `(x=s,y=0)` while
retaining the existing finite-width director/proper-fit frame. Its full
additive-coordinate first and mixed second variations are carried through
the objective point work and segmented line; the small reference KKT uses
the matching local trace. Q4/S3 finite line derivatives, KKT/weak-derivative
agreement, and six rigid modes pass; the two affected diagnostic suites
passed **47/47** tests. This is an alternate candidate, not a change to the
selected shell pose (none has been selected).
Six additional Q4/S3 finite-rigid-motion checks passed on three meshes,
including origin shifts and stations at host boundaries.

On the fixed finest physical mesh, its raw compliance results are in
`B3_GE_E4_PL_F03_NATIVE_LINE_COMPLIANCE_DIAGNOSTIC_V4.json`. At eight
multiplier intervals the minimum quotient rises from rail to local origin:
Q4 P0 `0.1748 → 0.2188`, Q4 P1 `0.1192 → 0.2020`, S3-V2D P0
`0.1769 → 0.2138`, and S3-V2D P1 `0.1194 → 0.1764`. The alternating axial
minimum remains, and its quotient still decreases as intervals are added.
The matching +100 Nm loaded screen is preserved in
`B3_GE_E4_PL_F03_WEAK_LINE_RESOLUTION_DIAGNOSTIC_V2.json`. All six Q4 tip
rotations are unchanged to reported precision; S3-V2D changes by 0.18% to
10.01% (largest at P1 with eight intervals). The largest relative change
in the sampled gap L2 is about 1.2%. Thus improved compliance quotient
does not imply an equivalent physical response or a correct line law.
The needed matched physical target, thickness/refinement interpretation,
and production trace/multiplier choice remain open; F03/G0B stay open.

The identified axial channel was then loaded directly on the same finest
mesh with a self-equilibrated `100 kN × sin(8πx)` nodal beam `Fx` pattern;
the loaded reference-linearized KKT and 129-station gaps were evaluated
for both shell origins, Q4/S3, P0/P1 and 2/4/8 intervals. The 12-case
rail and local raw inventories are respectively
`B3_GE_E4_PL_F03_WEAK_LINE_RESOLUTION_DIAGNOSTIC_V3.json` and
`B3_GE_E4_PL_F03_WEAK_LINE_RESOLUTION_DIAGNOSTIC_V4.json`. Net applied
axial force is zero and maximum scaled algebraic residual is below
`2.0e-16`. At eight intervals, changing rail to local origin raises the
maximum beam `|ux|` from `1.978e-6` to `4.209e-6` m for Q4 P0 (+112.8%)
and from `2.123e-6` to `4.643e-6` m for Q4 P1 (+118.7%); S3-V2D changes
by +70.9% and +80.4%. The axial gap L2 does not improve uniformly:
Q4 P0 rises 54.4%, while Q4 P1 rises 4.0% at eight intervals. These
large response changes confirm that the local-origin change affects the
problem's axial mechanics, which the torsion-only screen concealed.
The 100 kN amplitude is a diagnostic linear load, not an accepted physical
limit or a matched reference. No candidate is selected; external/independent
physical response and interface-stability interpretation remain necessary.

## Pause checkpoint — 2026-09-24

Implementation is paused at user request. The integration worktree is
`C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling`, branch
`codex/b3-ge-e4-pl-integration`, HEAD `42b6d069`. One untracked, unfinished
file is owned by this task: `scripts/_b3_e4_f03_segmented_y.py`. It is an
interface-aware transverse basis prototype with breaks at `y=-0.23,0.23`;
it has not been tested, connected to the spectral solver, or used as
qualification evidence. Preserve it on resume and first check its algebra
and ownership before any loaded run. The completed independent spectral
diagnosis is documented in `B3_GE_E4_PL_F03_SPECTRAL_AXIAL_V1.md` and commit
`42b6d069`; do not repeat it without changed inputs or a concrete concern.

F03/G0B remain open and G1 barred. No line multiplier or shell pose is
selected. Formal F03 execution authority remains unconsumed; existing raw
evidence and failures remain immutable. Apply
`ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1` prospectively, preserving
the scientific and qualification contract. No owned active process is known
at this pause. Do not start implementation again until requested.

## Resumed development — segmented transverse diagnostic, 2026-09-24

The user resumed work. The paused prototype is now an optional, isolated
three-interval classical-shell y basis aligned with the attachment material
lines at `±0.23 m`; the global-basis result was replayed unchanged. Nine
focused mechanics checks passed, and 14/14 serial guarded segmented screens
completed within their limits. The complete compact finding and raw-root
inventory are in `B3_GE_E4_PL_F03_SEGMENTED_AXIAL_V1.md`. At fixed nx64,
beam128, mortar128, p12→16 changes beam energy by 0.0098%, but changing
mortar128→256 still changes it by 3.89%, and nx96→128 at mortar256 by 1.71%.
The efficient transverse basis does not settle the x/beam/multiplier
interaction. The next technical action is a physically matched convergence
and interface-stability diagnosis; no native pose or multiplier selection
follows from this screen. Formal F03 authority remains unconsumed, F03/G0B
open, and G1 barred. Existing historical evidence is unchanged.

## Decision-oriented transverse reference slice — 2026-09-24

Question: can an independently assembled Reissner–Mindlin plate and
Timoshenko beam, with the native fixture's physical geometry, transverse
section resultants, support constraints, tip-z force/tip-x torque and
declared rail/local line work, give a settling *loaded* comparator? The
competing explanations are native port/line sensitivity versus ordinary
physical discretization error. Build one self-contained out-of-plane
variational reference (w, rx, ry plus beam w, rx, ry), verify its analytic
twist and shear patches, virtual work, equilibrium and row rank, then run
exactly three joint polynomial/line levels `(4,4,4,4)`, `(6,6,6,6)`,
`(8,8,8,8)` for rail/local origins and separate `+1000 N` tip-z and
`+100 N m` tip-x loads (12 solves, one thread). These are polynomial
orders and line intervals, not shell/beam element ratios; several axes
change together. A settling result may guide a native comparison after
independent mechanics review; a nonsettling result
requires diagnosing this reference rather than treating either native
port as validated. The flat out-of-plane subsystem cannot qualify the
complete eccentric six-channel law, nonlinear response or G0B by itself.
Do not extend the classical axial sequence for this question. Keep the
existing 8 GiB/900 s-per-case resource envelope and formal F03 authority
unconsumed.

The 12-case independent transverse joint screen passed its stated
algebraic/work/resource checks, but rail tip-z displacement changes
`11.44→19.57→21.69 µm` and rail tip twist changes
`4.548→5.828→6.267 µrad` on levels 4→6→8. The tiny weak/pointwise
gaps do not establish a converged response. The matrix condition also
rises from about `7.5e7` to `2.6e10`. Before higher joint order, use the
level-6 rail model and increase *one axis at a time*: plate `(nx,ny)`
to `(8,8)`, beam `nb` to 8, or line intervals to 8, for each of the
two loads (six solves). If plate change dominates, inspect/refine the
independent shell physics; if beam dominates, inspect beam fields; if
line dominates, revisit interface resolution; if none does, investigate
interactions/conditioning. This is diagnosis, not a new acceptance
criterion or formal F03 run.

The one-axis diagnostic stopped at the first failed check and preserves
five completed cases plus the failure. At the `(6,6,6,6)` rail anchor,
plate-order 8 changes tip-z/twist by about +10.9%/+7.6%; beam-order 8
changes them by about +89.8%/+69.3% while permitting a `0.98 µm` loaded
gap despite zero weak rows. Raising only P1 line intervals 6→8 gives
27 rows of rank 21, a `3.91e21` scaled KKT condition, and no trustworthy
line-response comparison. This is exact polynomial trace-dimension
dependence, not evidence of a native formulation failure. The research
reference now rejects overresolved rows explicitly; a focused null-mode
test confirms underresolved rows can miss nonzero physical gaps. The
failed raw remains `B3_GE_E4_PL_F03_INDEPENDENT_TRANSVERSE_ONE_AXIS_V1.jsonl`.

Next bounded decision: at *matched* plate/beam/P1-line degree 10, run
rail/local and the two fixed loads (four solves). If n8→10 physical
responses remain material or conditioning degrades, stop global degree
increase and improve the independent basis/constraint design; if they
settle, proceed to one-axis and holdout checks with independent mechanics
review before considering a native comparison. This is not a new
qualification threshold, nor authorization to repeat the prior failed
line-only case.

The matched-order-10 four-case screen passed its stated algebraic/work
and resource checks, but 8→10 still changes rail/local tip-z by
`+11.63%/+10.91%` and tip twist by `+5.91%`; condition reaches
`4.91e11`. The reference therefore remains **not converged**. The
line image is exactly polynomial of degree at most `max(nx,nb)`;
P1 intervals above that degree are redundant, while fewer rows permit
high-order physical gaps. This explains the one-axis failure and why
tiny weak/pointwise gaps at matched degree cannot prove physical
accuracy. Stop global-degree escalation. Retain the self-contained
reference and analytic tests as independent operator evidence, then
consider a local/resolved representation that can separate connection
localization from global basis conditioning. Do not compare it to native
responses as a qualified target or select rail/local/P0/P1 from these
data. Raw roots are `B3_GE_E4_PL_F03_INDEPENDENT_TRANSVERSE_JOINT_V1.jsonl`,
`B3_GE_E4_PL_F03_INDEPENDENT_TRANSVERSE_ONE_AXIS_V1.jsonl` (failed
line-only case preserved), and
`B3_GE_E4_PL_F03_INDEPENDENT_TRANSVERSE_MATCHED10_V1.jsonl`.

Next representation question: is the slow loaded response tied to the
global trial basis rather than the declared plate/beam/line mechanics?
Add a local, clamped cubic-spline trial option to the same independent
variational model, keeping geometry, constitutive coefficients, root/left
support, rail/local pose functionals and loads fixed. Integrate each
knot span and every shifted shell-sample/beam/multiplier overlay segment.
First verify partition/support and analytic patch identities plus row
rank; then compare nested 2→4→8 plate/beam elements with 4→8→16 P1 line
intervals, two loads and both origins. If the local representation settles
while global polynomials do not, continue with one-axis and holdout
checks; if it does not, inspect physical gap, line rank and independent
formulation rather than simply increasing order. This is one bounded
development comparison, not acceptance or a new qualification package.

Local cubic splines preserve the analytical plate/beam patches and full
line-row rank on common `(plate-x,plate-y,beam; P1 intervals)` grids
`(2,2,2;4)`, `(4,4,4;6)`, `(8,8,8;10)` for both shell origins. The planned
8/16 endpoint has dependent rows for both origins, and even 4/8 is
dependent for the local origin. The first attempted sweep aborted at that
guard; its six completed rows remain in `...LOCAL_SPLINE_TRANSVERSE_V1.jsonl`.
The rank-valid 12-case V2 shows tip-z motion `12.4→18.5→26.2 µm` (rail)
and `12.5→18.5→25.3 µm` (local); tip twist is `4.36→5.89→6.78 µrad`
under the separate torque load. Both responses still move materially, so
V2 is a diagnostic, not a converged native target or multiplier selection.

Next discriminating check holds plate-x, beam and P1 line resolution fixed
at `(8,8,4)` and varies only transverse plate intervals `2,4,8`; then
holds all trial resolutions at 8 and varies P1 line intervals `4,6,10`.
These separate transverse representability from line-row effects. If
transverse changes dominate, improve the plate reference before native
comparison; if line changes dominate, examine weak-line stability and gap
modes before choosing a space. If neither settles, inspect the physical
model and trace rather than launch a larger blind refinement.

The one-axis spline check found only `+0.8%` rail tip-z and `+4.1%`
tip-twist changes over transverse intervals 2→8 at fixed x/beam 8 and
P1 line 4. At fixed trial 8, P1 line 4→10 instead changes rail tip-z
`39.64→26.19 µm` and twist `11.71→6.78 µrad`; local tip-z changes
`44.77→25.28 µm`. Smaller pointwise gaps and full row rank do not
select the larger multiplier space. Against a native Q4, eight-beam-element,
left-supported, P1 screen with the same nominal flat geometry, section
resultants, loads and four-sample work, the spline reference at transverse
intervals 2 differs by only `-0.04%` in torque tip rotation and `+4–5%`
in tip-z at P1 line 4. At P1 line 10 it is `35–39%` stiffer in those
responses. This points to line/trial resolution compatibility, not a
qualified continuum target. The older native ratio inventory uses a
different `both_xy_edges` support policy; do not combine its numbers with
this left-supported comparison as if they were the same problem.

Next native mesh-ratio question: with P1 line 4, identical left support,
loads, shell thickness and section, does separately changing beam or shell
resolution preserve the torque/tip-z response or expose a host/beam ratio
effect? Execute a bounded one-axis grid around `(n_s=4,n_half=16)`, with
`n_s=2,4,8` at fixed beam and `n_half=4,8,16` at fixed shell, then a
fixed-shell path to the required 1:8 ratio. A stable response would permit
a focused line-space comparison; strong one-axis changes would require a
physical mode/port analysis before choosing the multiplier. This does not
consume formal F03 authority or qualify a space.

The one-axis native Q4 grid confirms different controlling errors. At P1
line 4 and fixed 8 native beam elements, shell-host intervals 2→4→8 give
rail tip-z `21.41→37.32→39.62 µm`; the shell-2 `8:1` endpoint is much
stiffer (`5.34 µm`) and beam refinement near that endpoint barely changes
it. At fixed shell-host 8, beam:shell ratios 1:8→1:4→1:2 give torque
tip rotation `14.99→11.97→11.39 µrad` and tip-z gaps `4.33→2.11→1.44
µm`. The extreme endpoints are underresolved in different domains; a
combined endpoint comparison is not a convergence test. This is fixed P1
line 4, left-edge/root supports, not the historical both-edges ratio set.

The independent *positive-energy* spline model permits a physically scaled
H^(-1/2)-dual line diagnostic, unlike the native retained saddle tangent.
At x/beam 8, y2 and P1 intervals 4→6→10, its minimum normalized
compliance quotient falls rail `2.664→1.560→0.061` and local
`5.109→1.627→0.064`; the weakest mode is nearly all alternating z-force
density. The rows remain full rank, yet the decline and loaded-response
shift preclude selecting a space from rank, gap or one quotient alone.
Next resolve whether the 35–39% independent/native disagreement at line 10
is merely reference x/beam underresolution: hold plate-y=2 and line
4/6/10, raise only local-spline plate-x and beam elements 8→12, retain
both origins and loads. If the fine-line disagreement persists with small
8→12 response change, investigate the shell/beam trace and constraint
mode; if it shrinks materially, the reference still needs convergence.

It shrinks: x/beam 8→12 at fixed plate-y2 and P1 line10 changes
independent rail tip-z `22.77→36.17 µm` (+58.8%) and torque tip-rx
`5.86→8.72 µrad` (+48.9%); local tip-z changes +78.8%. At line4 the
same x/beam change is only +0.4–1.8%. The apparent fine-line disagreement
was substantially an underresolved independent trial space, so no
line-instability verdict follows from the earlier weak mode alone. Next
one-axis split at line10: compare `(plate-x,beam)=(12,8),(8,12)` with
the saved `(8,8),(12,12)` cases. If one direction controls, refine that
reference operator and inspect its interface modes; if both matter, treat
the response as joint trace-resolution dependence. Do not infer a native
multiplier choice from this reference until its loaded response settles.

The line10 split isolates the beam trial as the dominant source: at
plate-x8, beam 8→12 raises rail tip-z `22.77→35.61 µm` and torque
tip-rx `5.86→8.63 µrad`; plate-x 8→12 with beam fixed8 changes them
only to `24.83 µm` and `5.92 µrad`. Local-origin results agree on this
attribution. Pointwise gaps grow when beam modes are added, so the tiny
gap at beam8 was overconstraint by inadequate trial resolution, not proof
of superior line accuracy. Native B3 internal kinematics have a different
approximation space from an equal count of classical Timoshenko elements.
One final bounded beam-only 12→16 check at fixed plate-x12, plate-y2,
line10 and a line4 control will determine whether this independent loaded
reference is settling. If line10 still shifts materially, stop and analyze
the beam/line approximation rather than continue mesh escalation.

At fixed plate-x12, plate-y2 and P1 line10, beam12→16 changes the loaded
independent tip-z by +0.31% rail/+0.53% local and torque tip-rx by +0.32%; the
line4 control changes negligibly. The beam representation is settling on
this bounded check. Before using line10 as a physical comparator, isolate
the remaining transverse plate resolution: at plate-x12/beam16/line10,
compare plate-y2,4,8. If y4→8 is small, move to a matched native y-refined
check with explicitly identical full-left supports; if material, stop this
reference comparison and inspect the rail/plate transverse field. Do not
compare a y-refined native model using the historical three-node support
shortcut, because that would change the boundary-value problem.

The transverse stop check did not show a decreasing twist change:
plate-y2→4→8 at fixed x12/beam16/P1 line10 gives rail/local torque
tip-rx `8.751→9.059→9.453 µrad`. Rail tip-z is
`36.28→36.83→37.18 µm`, local `37.91→38.97→39.61 µm`.
Under the torque load, integrated plate energy rises
`0.000293→0.000309→0.000329 J`; three transverse bands divided at
`y=±0.23 m` retain approximately 28.5% / 42.9% / 28.5% of the energy.
The bending/shear integration reproduces the assembled shell energy.
This does not expose a narrow rail-only concentration or provide a
converged shell target. Stop the spline refinement sequence here.

Development decision: retain rail and local poses as candidates; neither
P1 line10 nor a different multiplier is selected. The local origin exactly
removes the analytic twist-patch positional error, but its loaded tip-z
response and axial coupling differ, so that patch alone cannot decide.
Before a native y-refined comparison, the bounded diagnostic must support
an explicit full-left-edge clamp for every transverse row; the historical
`legacy_three_left_nodes` policy ceases to represent the same support when
`n_y>2`. Compare physical fields/work and use a correctly normed stability
assessment along with loads and gaps. New raw files are
`B3_GE_E4_PL_F03_LOCAL_SPLINE_{TRANSVERSE_V1,TRANSVERSE_V2,ONE_AXIS_V1,
MATCHED_Y2_V1,XBEAM12_V1,LINE10_ONE_AXIS_V1,BEAM16_STOP_V1,Y_STOP_V1}.jsonl`,
`B3_GE_E4_PL_F03_NATIVE_{MATCHED_TRANSVERSE_V1,ONE_AXIS_RATIO_V1,
RATIO_RECIPROCAL_V1}.jsonl`, `B3_GE_E4_PL_F03_INDEPENDENT_SPD_INTERFACE_V1.jsonl`,
and `B3_GE_E4_PL_F03_TRANSVERSE_ENERGY_BANDS_V1.jsonl`. V1 transverse
contains six completed rows before the recorded rank abort; V2 is the
revised, rank-valid run. These are development diagnostics, not G0B
qualification or a formal F03 execution.

Next matched-native transverse question: does E4-PL Q4 at the same
flat geometry, full-left clamp, B3 root support, P1 line10 and separate
100 Nm/1000 N loads show the independent plate's y2→4→8 response trend?
The new `full_left_edge` diagnostic policy has exact free-set and KKT
parity with the historical three-node clamp at y2, and explicitly fixes
all left-edge coordinates at higher y resolution. A similar native
trend would point to a real shell-resolution requirement before port
selection; a different trend would direct analysis to the E4 plate or
shell-pose trace. Preserve P0/P1/dual choice as open either way.

The native Q4 result differs in convergence trend from the independent
plate: at P1 line10 and full-left support, shell-y4→8 changes native
torque tip-rx `9.687→9.727 µrad` (+0.40%) and rail/local tip-z by
+0.65%/+0.76%. The independent y4→8 twist change is +4.35%.
Thus the independent plate is not a qualified loaded native oracle, even
though its coefficients and boundary-value definitions are matched.
Next discriminate native port dependence by changing only shell-x
resolution from `n_s=4` to 8 with beam16 half-cells, shell-y8, P1 line10,
full-left support and the same two loads. If rail/local loaded differences
decay, keep both as discretization candidates pending axial and stability
checks; if they persist, require a separate physical pose/trace decision.

They persist after shell-x refinement: with y8, P1 line10, beam16
half-cells and full-left support, Q4 `n_s=4→8` changes rail tip-z
`35.35→38.12 µm` (+7.85%) and local `35.44→41.85 µm` (+18.07%).
The rail/local difference reopens from 0.27% to 9.78% at the fine x mesh,
while torque tip rotation changes +2.49% and is common to both origins.
All four solves retain small equation/work and global wrench residuals.
Before choosing a port, repeat only the tip-z distinction on S3-V2D at
the same two x levels. A similar Q4/S3 trend implicates the trace/pose
definition; a different trend points to shell interpolation/host mapping.
Neither result alone qualifies a multiplier or G0B.

S3-V2D reproduces the qualitative Q4 pattern at the same full-left
setup: local versus rail tip-z is -1.36% at `n_s=4` and +9.10% at
`n_s=8`; Q4 is +0.27% and +9.78%. Similarity across topologies makes
a Q4-only artifact unlikely, but neither gap nor compliance identifies
the correct pose. The analytic twist patch favors local positional
interpolation for that field. One final same-mesh, self-equilibrated
axial-density loading on the fine Q4 mesh distinguishes whether that
candidate also avoids a large axial response change. A large change
would require axial work/trace analysis before prioritization; a small
change would justify carrying local forward as a *development candidate*,
not accepted mechanics.

The axial cross-check is large and physically interpretable. At the
identical Q4 x8/y8, native 16-half-cell, P1 line10, full-left setup, a
zero-net `100 kN/m × sin(2πs)` beam density gives maximum beam |ux|
`0.918 µm` for rail and `1.522 µm` for local (+65.7%); tip ux is
`-0.918` versus `-1.415 µm` (+54.1% in magnitude). Shell energy is
`0.00814` versus `0.01615 J`, and axial gap L2 is `0.00157` versus
`0.00829 µm`; both retain small global balance/work errors. A center
material point must follow displacement at `(s,0)`, whereas the rail
origin averages `(s±0.2,±0.23)` and filters a y-invariant sinusoidal
axial field by `cos(0.4π)≈0.309` before host interpolation. A separate
Q4/S3 quadratic-field test verifies that the local pose follows an exact
center mesh node while the rail origin differs by over 30 µm. This
explains why the two ports should not be treated as interchangeable
numerical variants. For the declared centerline bonded material
correspondence, prioritize local translation with the finite-width
director frame as the G0B development candidate; rail remains a
diagnostic finite-width-average connection. This is not an accepted
shell pose, multiplier or production line law. The new raw roots are
`B3_GE_E4_PL_F03_NATIVE_{MATCHED_Y_LINE10_V1,FULL_LEFT_X8_Y8_V1,
S3_FULL_LEFT_PORT_V1,FINE_AXIAL_PORT_V1}.jsonl`.

Next line-space uncertainty: at fixed Q4 x8/y8, native 16 half-cells,
full-left support and the center-material-point pose, do P0, P1 and
the existing dual-linear candidate show compatible physical torque and
tip-z responses as line intervals increase 4→10, or do they impose
different effective constraints? Run the 12 bounded combinations with
the same loads, verify work/wrench residuals and sampled gaps, and
check row rank separately. Agreement would permit a norm-scaled
interface-mode/stability comparison before choosing the least costly
admissible space; disagreement would require a mode/trace diagnosis.
This screen cannot select a space from gaps or a quotient alone.

The fixed Q4 x8/y8, B3 16-half-cell, full-left, center-origin screen
found full row rank in all six P0/P1/dual-by-interval combinations.
At P1 line intervals 4→10, tip torque rotation changes
`11.956→9.969 µrad` and tip-z `45.85→41.85 µm`.
At line10 the P0/P1/dual torque values are
`10.988/9.969/9.784 µrad`, and tip-z values are
`44.49/41.85/41.25 µm`; the gap L2 similarly changes but is not
an accuracy selector. All 12 loaded cases retain small global
work/wrench residuals. Physical response has not settled uniformly
among spaces. Do not promote P1 or dual merely because their gaps are
smaller than P0. The next discriminating analysis is a native retained-
variable interface mode with a stated physical multiplier norm and
actual associated trace/work, coupled to a matched external/resolved
torque/shear response. The signed Schur or absolute-primal quotient alone
does not supply the required inf-sup or locking verdict. Raw root:
`B3_GE_E4_PL_F03_NATIVE_LOCAL_SPACE_SCREEN_V1.jsonl`.

Next algebraic uncertainty: B3's retained native block is indefinite,
so a direct positive-energy norm on the full primal vector is invalid.
On a small local-center case, exact block elimination of retained
coordinates yields a positive physical Schur stiffness and reproduces
the full multiplier action to `5.7e-15` relative error; the retained
block has both positive and negative eigenvalues. Test whether that
decomposition remains valid and positive for the fixed fine native
P0/P1/dual line4/line10 cases. If it does, separate physical trace
compliance from the retained direct multiplier term and interpret their
norm-scaled modes alongside the saved loaded responses. If the physical
block or direct term loses the required sign/rank, do not force a
positive-energy inf-sup interpretation; return to the mixed saddle
formulation. This is a bounded diagnostic, not a multiplier selection.

The six fine local-center cases passed exact retained-coordinate
condensation: full versus condensed interface action differs by at most
`3.7e-13` relative; the reduced coordinate block has positive minimum
eigenvalue while the retained block has 144 negative modes. The
H^(-1/2)-dual minimum quotient falls with line refinement in every space,
but all six minimum vectors are alternating **Fx** densities with
negligible direct-retained share. That minimum is not the physical
torque/tip-z mode sought here, and no line-space verdict follows.
Next restrict the same exact condensed action to transverse `Fz/Mx/My`
multiplier channels, report the normed mode and physical/retained work
split, then compare its trend with the saved loaded work/gaps. If the
transverse mode weakens with refinement, inspect actual trace and beam
representation before selecting a space; if stable, proceed to matched
physical reference and mesh-ratio checks. Do not refine the axial minimum.
Raw root: `B3_GE_E4_PL_F03_NATIVE_CONDENSED_INTERFACE_V1.jsonl`.

The transverse-only normalized minimum falls from `9.58→0.72` for P0,
`7.02→0.70` for P1 and `7.18→0.72` for dual as line intervals 4→10.
At line10 it is a nearly pure alternating Fz density in all three:
the native beam accounts for 90–92% of its work, the shell 4.5–5.9%,
and the direct retained term 2.9–3.7%. At line4 the shell and beam
shares are each roughly 40–57%. This exact-condensation result points
to a beam-trace/line-resolution dependency, not an axial or Q4 drilling
mode; it remains a finite-dimensional diagnostic, not an inf-sup proof.
Next change only native beam half-cells 16→32 on the fixed local-center
Q4 x8/y8, P1 line10 setup under the two saved loads. If responses move
materially, reject the present beam/line ratio as a basis for space
selection; if they stabilize, advance the matched physical reference
and one-axis mesh-ratio checks. Stop at this bounded increment.
Raw root: `B3_GE_E4_PL_F03_NATIVE_TRANSVERSE_INTERFACE_V1.jsonl`.

The bounded 16→32 native half-cell check did not settle P1 line10:
center-origin torque tip-rx changed `9.969→9.439 µrad` (-5.31%) and
tip-z `41.85→39.79 µm` (-4.92%) at fixed Q4 x8/y8 and full-left
support. The torque gap L2 rose slightly while the tip-z gap fell;
work and global balance remained small. Do not infer that a smaller gap
or the transverse quotient establishes the correct line space. Stop
this refinement path as declared. The next mechanics work must identify
the beam station trace's relevant modes and compare a matched physical
torque/shear reference, then re-evaluate candidate spaces within the
registered mesh-ratio and stability envelope. Raw root:
`B3_GE_E4_PL_F03_NATIVE_BEAM32_LINE10_V1.jsonl`.

Next station-port question: does the straight native six-channel port
approximate a known smooth beam centerline and twist at the expected
half-cell order, or is its actual state/chart mapping inconsistent?
Construct a trial with exact quadratic nodal z positions and linear
retained-cell twist sampled at half-cell midpoints. Integrated position
error should scale as `h²`, rotation error as `h`, with analytically
known coefficients. Check 8/16/32 half-cells using the actual pose and
chart operations. Exact scaling would support a trace-resolution
policy or a separately derived higher-order station port; failure
would require correcting the current port before line-space work.
This is a kinematic patch, not a coupled accuracy or G0B pass.

The actual state/chart station patch passes 3/3 grids: a quadratic
transverse position has exact RMS interpolation error
`|κ|h²/sqrt(120)`, and a linear twist sampled by retained cell frames
has exact RMS error `|β|h/sqrt(12)`. Thus the port is low-order as
defined, without an observed implementation inconsistency. The patch
alone cannot attribute the coupled ~5% beam-doubling effect, because
the global beam operator and weak line also change their interaction.
Next compare uncoupled native retained beam tip-z and torque at 16/32
half-cells against the same generalized-section beam references. If
those are stable, focus on the line trace/multiplier interaction; if
they move materially, resolve native beam convergence first. Keep
coupled and bare-beam physical questions distinct.

The uncoupled native B3 solves at 16 and 32 half-cells agree with the
declared generalized-section references to roundoff: 100 Nm gives
`74.285714 µrad`, and 1000 N gives `192.023810 µm`, with negligible
free residuals and work error. The coupled ~5% change is therefore an
interface/station-trace effect, not bare-beam stiffness convergence.
Next compare P0 and dual-linear at the same 32-half-cell endpoint, with
the saved 16-half-cell and P1 results. If all spaces shift similarly,
focus on the station-port/line-resolution law; if one is materially
less sensitive, carry it forward only as a candidate for physical
reference and stability checks. No space is qualified by this screen.
Raw root: `B3_GE_E4_PL_F03_BARE_NATIVE_BEAM_16_32_V1.jsonl`.

The four additional 32-half-cell native solves separate the spaces at
fixed Q4 x8/y8, local-center position, full-left support and ten line
intervals. Compared with 16 half-cells, P0 torque/tip-z changes
`−0.18%/−1.11%`; P1 changes `−5.31%/−4.92%`; dual-linear changes
`−7.69%/−6.77%`. All retain small work/balance errors, while sampled
gaps move in different directions. This supports carrying the lowest-
dimensional P0 as the leading *development* line-space candidate and
rejects using either P1 or dual's smaller gaps as promotion evidence.
It does not establish P0 mesh-independent stability or physical
accuracy: at fixed 16 half-cells, P0 line4→10 still changed loaded
torque substantially. Next use one-axis shell/beam/line physical checks
and a genuinely matched torque/shear reference at the declared center
material line; no further blind beam doubling is warranted.
Raw root: `B3_GE_E4_PL_F03_NATIVE_BEAM32_SPACES_V1.jsonl`.

Next aligned line-resolution question: with the better resolved native
32-half-cell beam and fixed Q4 x8/y8 shell, does the leading P0 space
approach a stable loaded response when one line interval matches each
of the 16 shell x hosts? Compare nested P0 intervals 8 and 16 under
the same torque/tip-z loads, retaining line10 as an intermediate
descriptive point. If 8→16 remains material, stop line escalation and
inspect the physical line law and external target; if small, advance
one-axis ratio/stability checks. This does not select P0 or consume
formal F03 authority.

The bounded aligned P0 check is complete and takes the first branch of
that decision. On fixed Q4 x8/y8, native half32, full-left supports and
local-center pose, P0 intervals 8→10→16 give torque tip `rx`
`11.679→10.968→9.659 µrad` and transverse tip `z`
`45.195→43.992→40.443 µm`. The 8→16 changes are −17.296% and
−10.514%. All four new solves completed with small equilibrium and
work errors. Raw root:
`B3_GE_E4_PL_F03_NATIVE_P0_ALIGNED_LINE_V1.jsonl`. Do not refine the
line further on this fixed physical mesh.

The corresponding rank audit used the same complete native retained
linearization, the actual local-center trace, and existing coordinate
scales, with a declared `1e-10` relative row-dependence threshold. At
P0 m8, whole/shell-only/beam-only ranks are each 48/48. At m16, the
whole and beam-only ranks are 96/96, while shell-only is 69/96. In the
transverse Fz/Mx/My subset, whole/beam-only are 48/48 and shell-only
35/48. This is a finite-grid representability audit, not an inf-sup
bound or an accuracy criterion; its loss of shell-only rank explains
why additional line rows can be beam-supported without resolving shell
work. Raw root: `B3_GE_E4_PL_F03_NATIVE_P0_ALIGNED_RANK_V1.json`.
The earlier one-axis inventory remains descriptive: Q4 shell x-host
2→4→8 at native half16/P1 line4 moves local-center tip-z
`29.29→42.30→44.60 µm`, while fixed x-host8 and beam half4→8→16
moves torque `14.99→11.97→11.39 µrad`. These are separate axes; their
apparent endpoint closeness is not a mesh-ratio stability certificate.

The physically defined four-sample +100 Nm shell force couple and
+1000 N transverse force were added only to bounded native and
CalculiX probes. The native Q4 x4/y2, half4, P0 m4 local-center runs
give shell-tip transverse slope `8.929 µrad` for the couple and tip-z
`35.370 µm` for the force, with small global wrench/work residuals.
The exploratory CalculiX S4/B31 rectangular-section, six-channel
*nodal-collocation* deck gives shell slope `7.873 µrad` and tip-z
`20.013 µm` at the same coarse geometric mesh and declared loads.
These differences are not scored against qualification tolerances:
S4 versus E4-PL, B31 rectangular versus native generalized section,
and collocation versus integrated multipliers are material model
differences. The CalculiX S4/U1 run failed with a shell-thickness
expansion error; B31 rejected `SECTION=GENERAL`; a moment placed on
an eliminated beam coordinate produced zero response. Those failed
runs remain preserved. The B31 rotation monitor still reads zero under
the nonzero shell force couple, so no external beam-twist comparison is
claimed. Executed raw roots are under
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-ccx-s4-*-v1/`;
the native root is
`B3_GE_E4_PL_F03_NATIVE_SHELL_COUPLE_COMPARATOR_V1.jsonl`.
Next investigate a reference route with independently recoverable beam
torsion and calibrated section/shear properties; do not relabel these
partial matches as the mandatory external comparison.

The one-step S4/B31 collocation refinement meant to distinguish a
narrowing coarse discrepancy from a persistent route problem did not
produce a numerical comparison: both x8/y4 shell, eight-beam-element
cases timed out at the unchanged 120 s bound. The runner's timeout
recorder then raised `TypeError` while trying to write already-text
stdout as bytes. The decks and solver files were retained, and accurate
`timeout_recovery.json` receipts were added without rerunning. The
recorder now handles text and bytes, with a focused test. The exclusive
roots are `f03-ccx-s4-b31rect-shell-couple-refine-v1` and
`f03-ccx-s4-b31rect-centerline-shear-refine-v1` under
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/`. No refined physical
result exists, and the coarse discrepancy cannot be extrapolated. This
S4/B31 collocation route is not viable as the required reference within
its declared execution envelope. The next reference action must change
the route, resolving beam section/twist representation and line work
while retaining the physical problem and frozen acceptance criteria.

**Native paired P0 and independent transverse decision, 24 September
2026.** With local-center pose, full-left/root supports and matched
geometry/resultants, the native Q4 paired `(shell x, shell y, beam
half-cells, P0 intervals)` grids `(2,2,8,2)`, `(4,4,16,4)` and
`(8,8,32,8)` give +100 Nm tip-rx `18.247→14.071→11.679 µrad`
and +1000 N tip-z `36.971→45.510→45.195 µm`. Work/wrench residuals
remain small, but torque is not settled. Raw root:
`B3_GE_E4_PL_F03_NATIVE_P0_PAIRED_PHYSICAL_V1.jsonl`.

On the fixed finest x8/beam-half32/P0-m8 grid, changing shell-y
2→4→8 gives torque `11.033→11.849→11.679 µrad`; the large paired
torque trend is not explained by this width sweep alone. At fixed
x8/y8/beam-half32, P0 m4→8→16 gives `14.438→11.679→9.659 µrad`.
The m4→8 and m8→16 changes are both material despite smaller gaps.
Raw roots:
`B3_GE_E4_PL_F03_NATIVE_P0_TORQUE_Y_AXIS_V1.jsonl`,
`B3_GE_E4_PL_F03_NATIVE_P0_FINE_LINE4_V1.jsonl`, and the earlier
aligned-line file. Stop fixed-grid P0 line escalation.

The independent Reissner–Mindlin plate/Timoshenko spline model uses the
same transverse geometry, section resultants, supports and local-center
line-pose *definition*, with separately implemented element and trace
operators. At paired grids `(plate x,y,beam elements,P0 intervals)`
`(2,2,4,2)`, `(4,4,8,4)`, `(8,8,16,8)`, it gives torque
`18.272→14.084→11.495 µrad` and tip-z
`38.741→46.802→44.551 µm`. Against the corresponding native grid,
torque differs about `0.14%`, `0.09%`, `−1.57%`; force response differs
about `+4.79%`, `+2.84%`, `−1.42%`. At fixed finest independent trial
space, P0 m4/8/16 torque is `14.389/11.495/9.378 µrad`, following
the native `14.438/11.679/9.659 µrad` trend. This independently
confirms the observed discrete weak-line behavior; it does not prove
continuum accuracy, full six-channel mechanics or external agreement.
Raw roots: `B3_GE_E4_PL_F03_INDEPENDENT_P0_PAIRED_TRANSVERSE_V1.jsonl`
and `B3_GE_E4_PL_F03_INDEPENDENT_P0_FINE_LINE_V1.jsonl`.

A four-point-per-piece cubic trace-image construction then imposed the
*pointwise* bond in each fixed independent spline trial space. Two
relative rank tolerances (`1e-9`, `1e-11`) give identical ranks and
responses; holdout trace gaps are about `1e-21 m` at the declared 1 m
rotation scale. This exact finite-space bond is **not** a continuum
target: on paired plate/beam grids its torque is
`3.884→5.574→6.534 µrad` and tip-z
`12.442→17.305→21.308 µm`, so it is not yet mesh settled. At fixed
fine plate x8/y8, varying beam spline elements 4→8→16 leaves both
responses unchanged to displayed precision; at fixed beam16, plate
2/2→4/4→8/8 reproduces the moving sequence. Thus plate trace
representability, rather than beam trial resolution, controls the
finite-space pointwise-bond response. This does not by itself prove
locking or reject the formulation. The first one-axis attempt stopped
before any solve because an unrelated temporary P0 mortar exceeded its
trace rank; its failure is retained and the corrected V2 discards that
temporary mortar. Raw roots:
`B3_GE_E4_PL_F03_INDEPENDENT_EXACT_TRACE_V1.jsonl`,
`B3_GE_E4_PL_F03_INDEPENDENT_EXACT_TRACE_V2.jsonl`,
`B3_GE_E4_PL_F03_INDEPENDENT_EXACT_TRACE_ONE_AXIS_V1.jsonl`, and
`B3_GE_E4_PL_F03_INDEPENDENT_EXACT_TRACE_ONE_AXIS_V2.jsonl`.

Next derive and independently check which shell-side pose/trace modes
can transfer physical torque and transverse shear without numerical
drilling or unintended shear constraints, then obtain an independently
recoverable section-matched physical reference. Do not add line rows or
raise global axial order to manufacture a smaller gap. P0 remains only
a development candidate. Formal F03 authority is unconsumed, G0B open
and G1 barred.

**Loaded shell work and thin-shell reaction audit, 24 September 2026.**
Existing physical Q4/S3 twist and transverse-shear patches already show
finite-width torque work without using the drilling coordinate, and an
admissible nonzero transverse-shear field. The new loaded audit at Q4
and S3 x4/y4, native half16, P0 m4, local-center pose and full-left
support evaluates each element's declared `physical` and `numerical`
stiffness components directly. For separate +100 Nm tip torque and
+1000 N tip-z force at shell thickness `.07 m`, numerical-component
energy is exactly zero in all four cases. Physical plus numerical
components reconstruct assembled shell energy within `3e-14 J`.
The initial subtraction-only V1 remains preserved; V2 is the direct
component result. Raw roots:
`B3_GE_E4_PL_F03_NATIVE_TORQUE_SHEAR_ENERGY_ATTRIBUTION_V1.jsonl`
and `..._V2.jsonl`.

For +100 Nm torque at `.035` and `.0175 m`, both Q4 and S3 retain zero
numerical-component work and positive physical work. The thinner-shell
analytic physical twist (bending `t³`) and transverse-shear (`t`, with
the admitted S3 relaxation factor) patches pass. Q4 tip-rx rises
`14.071→37.827→64.283 µrad` as thickness `.07→.035→.0175 m`,
approaching the bare native beam's `74.286 µrad`. S3 gives
`14.268→38.589→64.813 µrad`. This supports physical torque transfer
on these bounded cases; it does not qualify line stability or thinning
convergence. Raw root:
`B3_GE_E4_PL_F03_NATIVE_TORQUE_THICKNESS_ATTRIBUTION_V1.jsonl`.

The native constraint-transpose shell-interface torque matches the
independently recovered shell support torque within `1.3e-10 N·m`
across Q4/S3 and all three thicknesses. The shell reaction changes
sign as the shell thins, while the beam-root reaction compensates;
this is an actual discrete load path, not a reaction-recovery error.
Raw root: `B3_GE_E4_PL_F03_NATIVE_INTERFACE_TORQUE_AUDIT_V1.jsonl`.

At matched plate x4/y4, beam8 and P0 m4, the independent transverse
model's thin-shell tip-rx differs from native Q4 by about 2.4% at
`.035 m` and 3.2% at `.0175 m`, but its shell support-torque share
differs much more: Q4 versus independent is `4.14` versus `10.18 N·m`
at `.035 m` and `6.85` versus `17.52 N·m` at `.0175 m`. At fixed
beam/P0 and `.0175 m`, one shell-only refinement x4/y4→x8/y8 reduces
that absolute support-torque difference from `10.67` to `3.18 N·m`;
Q4/S3 fine values are `2.86/2.67 N·m`, independent `6.05 N·m`.
The difference narrows but does not establish a converged physical
reaction partition. Do not score small resultants by relative error
alone or infer a line-space decision from tip rotation. Raw roots:
`B3_GE_E4_PL_F03_INDEPENDENT_TORQUE_THICKNESS_V1.jsonl`,
`B3_GE_E4_PL_F03_NATIVE_THIN_SHELL_XY8_V1.jsonl`, and
`B3_GE_E4_PL_F03_INDEPENDENT_THIN_SHELL_XY8_V1.jsonl`.

Next establish a resolved physical reference with explicit section,
director/shear, connection and reaction conventions, then assess the
shell trace's interface modes and P0 policy at the registered mesh
ratios. No drilling-penalty tuning, extra global axial order, or
larger CalculiX collocation run follows from this audit. Formal F03
authority remains unconsumed; G0B is open and G1 barred.

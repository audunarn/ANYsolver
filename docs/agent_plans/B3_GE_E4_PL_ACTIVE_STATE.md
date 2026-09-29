# B3-GE / E4-PL / B2 active state

Updated 29 September 2026 under Revision 7 and
`ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1`. The complete earlier record
is preserved at commit `a52042d1`. The
[complete programme](B3_GE_E4_PL_B2_COMPLETE_PROGRAMME.md), frozen
registrations, historical failures, and versioned evidence retain authority.

## Decision and gates

Deliver the experimental multi-element GE and B2 workflows while resolving the
native six-channel line law and growing multiplier space. **G0B/F03 remain open;
G1 acceptance and production qualification are barred.** None of F01–F13 is
fully accepted. Formal F03 execution authority is unconsumed. A/B are development
spaces, not selected policy. The dirty factor-4 Fy fallback is outside this
slice; do not edit or run it by default.

## Delivered experimental behavior

- The sparse GE owner solves multi-Q4/S3/native-B3 point panels with retained
  variables, atomic elastic stepping, recovery, and restart. A replaceable L1
  operator works on a bounded matching line, not qualified nonmatching lines.
- The separate physical B2 profile batches 1/10/100 cases with selected
  recovery and eligible factorization reuse. Physical range, attachments,
  mass/prestress, and scale remain open; historical B2 is unchanged.
- The experimental multi-Q4/B2 point owner now validates gaps and affine
  equilibrium without a fixed 1 N/1 m floor. Tiny force/moment tests reject
  a zero backend response; a 1000 N plus 1e-12 N case reports insufficient
  mixed-load resolution. Independent review confirmed the prior false-pass
  was closed and noted conservative refusal of some accurately solvable
  mixed-scale cases. Source `09adb780`, installed wheel SHA-256
  `a42fe0b28cc3d259ab5201660b2a03e6e2aec2491714dc516c26dee3d5b7a132`;
  14/14 installed B2 regressions passed in
  `.qualification/b3-ge-e4-pl/r7-b2-panel-residual-installed-dev-20260928-v1/`.
  The follow-up sparse-pattern sharing change at `ad8c05a1` keeps absolute
  values independently owned while reusing compiled CSR structure. Its new
  installed wheel SHA-256 is
  `11e928c9bb95be096d417be541864c70da34273b062401415e752e98def6a71`;
  14/14 installed B2 checks passed with the actual site import recorded in
  `.qualification/b3-ge-e4-pl/r7-b2-panel-residual-installed-dev-20260928-v2/`.
- ANYfem has a separate experimental save/reopen consumer. The installed
  solver/consumer milestone and review are in
  `.qualification/b3-ge-e4-pl/r7-combined-integration-dev-20260928-v1/`.
- The GE facade now returns a tuple of attachment capability names for both
  point-only and line owners. This makes the experimental machine-readable
  field consistent without changing analysis or checkpoint identity. Source
  `6e83d5ec`, wheel SHA-256
  `0809b913bafd54e29ef86ebb220334956b52d64a795934e108d02c471c373d69`;
  its original 21/21 pytest log had a separate site-import check but pytest's
  repository configuration could import `src`. The later same-process
  installed suite below verifies the current capability behavior. Preserve
  `.qualification/b3-ge-e4-pl/r7-ge-capabilities-installed-dev-20260928-v1/`
  as historically run, without treating that pytest count as wheel evidence.
- GE reference-linear acceptance now uses actual applied-work and active-load
  row ratios rather than a fixed 1 N work floor. A prior installed wheel
  falsely accepted zero response to a 1e-12 N load and a missed 1e-12 N
  component beside a 1 N load; both negative cases are retained in the
  verified before/after logs. The tiny-load physical solution and checkpoint
  still reproduce the ordinary-load solution proportionally. Source
  `93f404f3`, wheel SHA-256
  `89afe61b894efd44f0a44d41ec42426afa64da5a993c36c33d373ca08eca4baa`;
  34/34 point, line, finite and matched-case checks pass with the installed
  wheel imported **in the pytest process** and its source-path override
  disabled. Evidence is in
  `.qualification/b3-ge-e4-pl/r7-ge-linear-scaling-installed-dev-20260929-v1/`.
  This changes reference-linear acceptance and restore; the separate finite
  nonlinear convergence scale used a fixed work floor too. The finite driver
  now uses the same actual-load and active-row check, so zero response to a
  1e-12 N trial cannot be committed as equilibrium. A zero-step backend
  control preserves generation zero; ordinary Q4, mixed and S3 finite
  stepping/restart checks remain green. Source and correctly imported wheel
  checks pass 25/25; the wheel SHA-256 is
  `5AC5C43FF407D9E85B9F3A58D4C4B6647CC7F2E60D8B076B2C3E5EAA83E50D1C`.
  The first system-Python build attempt failed because its older setuptools
  cannot parse `project.license`; the successful wheel used this worktree's
  compatible environment. Both logs are retained in
  `.qualification/b3-ge-e4-pl/r7-ge-finite-scaling-installed-dev-20260929-v1/`.
- GE preflight now checks supported point/experimental-line rows for small
  numerical dependence using frozen physical row/coordinate scales and a
  capped dense audit. Larger rows use sparse structural matching; numerical
  dependence still requires the later sparse factorization check. The audit
  exposes row provenance. It found two dependent rows in a prior supported
  point plus line test fixture, which now has a separate negative test;
  line-only checkpoint behavior remains tested. Source and same-process
  installed-wheel checks pass 35/35. Wheel SHA-256
  `9EC354DE46676B7768DFFDB9382B4241B518B237D71A08F4AE98FEE9D1CC79A1`;
  logs are in
  `.qualification/b3-ge-e4-pl/r7-ge-constraint-audit-installed-dev-20260929-v1/`.
  This is an experimental point/line guard, not the complete nonlinear
  constraint audit or G1 acceptance.

## Connection facts and uncertainty

**G3 generalized-material slice, experimental:** The point-coupled finite
owner retains accepted generalized B3 station histories and uses a separate
V3 binary checkpoint when yielding occurs. A bounded panel yields at a 1.0
load factor and continues identically after restoration; rejected work and
cancellation preserve the accepted prefix. The active-branch assembled tangent
was checked through the actual chart update from one fixed predecessor.
The changed source passed 178 focused checks, and installed-wheel checks passed
36 GE cases plus 23 material cases; the strengthened tangent check passed
against the same wheel. Logs and the wheel hash are under
`.qualification/b3-ge-e4-pl/r7-ge-generalized-material-installed-dev-20260929-v1/`.
The first installed material run had 23 Windows temporary-directory setup
errors, then passed with a local temporary directory; retain both logs.
Independent read-only review found no further defect in predecessor, commit,
cancellation, tangent, or legacy restore paths. It identified a V3 boundary:
endpoint checks do not prove that a re-encoded material history arose from the
recorded path. The digest checks bytes, not trusted provenance. Fast restore
therefore remains an experimental endpoint consistency check; path
reachability needs independent replay or trusted provenance. That earlier
generalized-beam slice did not admit shell J2, fibre sections, reversal, or
G3 acceptance; the later experimental Q4 J2 slice below changes only the
first of those boundaries.

**Next material integration decision (29 September):** Determine whether the
existing qualified Q4 DNVC-C208 J2 update can be evaluated from one accepted
predecessor and published atomically with generalized B3 histories in the
experimental point owner. A bounded Q4-only vertical slice must include
typed material admission, actual-update tangent, rejection, checkpoint and
restart; a local yielded response alone is insufficient. If its candidate
state cannot round-trip and re-evaluate from the saved endpoint, correct the
state contract before adding S3-V2D. S3-V2D has distinct model-bound state and
remains explicit follow-up. No F05/G3 or production acceptance is inferred.

**Q4 J2 mixed-material development result (29 September):** The point owner
now admits a separate experimental Q4 DNVC-C208 J2 definition alongside a
yielding generalized B3 section. A bounded two-shell/two-beam panel yielded
in both domains, rejected trials and cancellation preserved the accepted
prefix, and a binary V4 snapshot restored and continued the same state.
The actual-update fixed-predecessor tangent check passed on the active branch.
The consumer uses an explicit experimental v2 schema while its elastic v1
schema remains unchanged. Source affected checks passed 48/48 and the first
combined installed-wheel run passed 52/52; the enlarged J2 consumer
save/reopen/solve/restore/continue check passed against the installed site.
Independent read-only review found no accepted-predecessor or atomic-publish
defect. V4 restore proves endpoint consistency, not history reachability;
the owner exposes shell alpha diagnostics but not full accepted shell stress
or algorithmic-tangent recovery. A low-yield trial failed its backtrack budget
during development and is not a formulation verdict. S3 J2, physical beam
fibres, reversal, complete material recovery, F05/G3 and production acceptance
remain open.

**Positive unloading/reloading development slice:** The same point owner now
accepts changing positive load factors, preserves material history on
unload/reload, and uses the separate V3 checkpoint for a nonmonotone elastic
history. Historical monotone elastic checkpoints retain V1/V2. The bounded
plastic path `1.0, 0.7, 0.4, 0.2, 0.5, 1.1` agrees exactly after restore;
12/12 source checks passed before the capability correction, and 30/30
same-process installed-wheel GE checks passed on the final product code. Final
candidate wheel SHA-256
`D1A8ABE1D2C7E69E9D5F3CDE66F334D05AE682C9FE212E81C64B308141930758`;
installed logs are in
`.qualification/b3-ge-e4-pl/r7-ge-unload-installed-dev-20260929-v2/`.
Independent read-only review identified a capability exclusion that was too
broad; it now excludes nonpositive finite load factors and the corrected wheel
passed the same installed checks. Preserve earlier failed screens under
`.qualification/b3-ge-e4-pl/r7-ge-reversal-dev-20260929-v1/`:
a `0.4 → -0.2` jump exhausted backtracking,
and a finer `0.2 → 0.1` unload also exhausted it. The latter distinguishes the
problem from a large sign-crossing step alone. Current load-relative
equilibrium normalization is unresolved near zero load with residual material
state. No tolerance was relaxed and sign reversal remains unsupported. The next
technical decision requires a physically justified convergence scale for
loaded-history states before another crossing experiment; more step refinement
alone is not a justified discriminator. This slice is experimental, not G3 or
G4 acceptance.

**G3 near-zero decision:** On the failed `0.2 → 0.1` step, the present global
work ratio stalls at `2.5501516e-8`, while its active-row ratio is about
`1.4e-16` and constraint gap is below `6e-17`. A fixed-reference global ratio
would be `2.5501516e-9`; this isolates normalization, not a demonstrated
material-tangent defect. A development hybrid using peak historical load for
global work and current load for active rows passed 13/13 focused tests,
including tiny-load, rescaled-pattern and near-zero restart checks. It is
**rejected for product integration**: V3 endpoint restore cannot authenticate
historical peak factors. A re-encoded elastic checkpoint with forged factors
`(1e12, 1., 0.5)` was accepted with unchanged physical endpoint and current
load ratio, but its reported global ratio changed from `4.05e-9` to
`2.75e-14`. Raw scripts and logs are preserved at
`.qualification/b3-ge-e4-pl/r7-ge-nearzero-normalization-dev-20260929-v1/`.
The hybrid source/test edits were discarded; no criterion or release claim
changed. Next, establish a trusted or mechanically verified reference state,
or derive a current-state physical scale that does not trust historical load
metadata, before resuming sign-crossing work. Endpoint-only checks cannot
prove path provenance; more load-step refinement does not resolve this issue.

**Near-zero correction result:** At the best unaccepted `0.1` state the sparse
linear backward residual is about `1.12e-21` in the mixed coordinate equations,
while the shell/beam translational correction is at most `5.46e-16 m`, about
one float64 spacing for metre-scale positions. Sampled forward and backward
Newton steps worsen the existing residual ratio. Actual-chart central
differences along the native correction have relative error above 2; scaling
the direction by 100 and 10,000 reduces it to about `1.5e-2` and `6.4e-5`.
This strongly suggests a coordinate-resolution floor but does not prove the
analytic tangent or exclude a branch change. The raw norm of all free equations
mixes force, moment, retained and multiplier units; do not label it newtons.
The bounded same-predecessor ladder through the actual update chart now gives
relative directional errors `6.40e-5`, `2.32e-5`, and `1.18e-6` at `1e4`,
`1e5`, and `1e6` times the correction (`h=0.5`). Measured nonzero differences
in selected beam-position components grow from at least 318 to 31,704 float64
spacings. The thresholded accumulated-increment branch mask did not change.
This supports a representation/evaluation floor at the native Newton step,
against a persistent smooth-branch bias larger than about `1e-6` in that
direction. It does not prove the full tangent, exact constitutive branch
identity, or resolution of every physical and retained coordinate. Independent
read-only review checked the same-predecessor evaluation and these limits.
The first diagnostic log, a failed v2 diagnostic-script run, and the corrected
v2 run are preserved in the same versioned evidence directory. Stop amplitude
sweeps; next pursue a mechanically justified precision or convergence-scale
remedy with trustworthy checkpoint reference before sign-crossing work. No
product criterion changes or F03 authority are involved.

**Finite-position precision development slice:** The GE
finite owner now passes existing high/low position pairs to the native beam and
point-joint operators and sums already rounded local residual contributions
with `fsum`. Without the improved summation, the paired-coordinate path fails
the previously accepted `0.4 → 0.2` unload (best ratio `1.54e-8`); together
they pass it at `8.31e-9`. A new integrated test confirms the joint's weak
constraint detects a `2^-54 m` beam motion at a 1 m reference coordinate.
The focused source check and same-process installed-wheel finite suite pass
14/14. The disposable wheel hash is
`9360502F4B52E23D8DBB687D60D9AFD917B5AD6B3088DDACE7DD43E64EA2549A`.
At `0.2 → 0.1`, the best ratio improves from `1.77e-8` with legacy positions
and improved summation to `1.46e-8` with paired positions, but both still reject
the step at the unchanged `1e-8` limit. A five-sample warm assembly screen on
one small elastic panel measured medians `0.07275 s` before and `0.07494 s`
for the candidate (about 3% overhead); this is not a scale qualification.
The source import needed a temporary Numba cache because cache writes inside
this protected worktree stalled; the wheel test process imported its installed
site. Independent read-only review found no atomicity defect and checked that
beam and joint consume the same beam high/low pair. The shell element still
uses its existing geometry path and recovery exposes only rounded beam
positions; full coupled sub-spacing work/tangent and actual-position claims
need separate evidence and, if required, a recovery contract. `fsum` sums
already rounded local values. Its Python list cost needs G5-scale measurement.
No near-zero, reversal, G3, or G5 acceptance follows from this slice.

**Centered Q4 precision follow-up, experimental:** A same-predecessor
decomposition of the rejected `0.2 → 0.1` trial found that nearly all remaining
free work residual comes from the Q4 shell, including cancellation of opposing
element forces near 164 work units into a roughly 1e-6 residual. An opt-in
centroid-relative Q4 reference in the finite GE owner preserves the original
default corotational route and the physical point-joint origin. It accepts the
registered positive plastic history through `0.1` at the unchanged 1e-8
limit (ratio `6.84e-9`), including restore/reload parity. Actual-coordinate
tangent, zero-state, rigid-motion, translated-origin and cache-invalidation
checks pass. Independent read-only mechanics review found no direct defect in
the exact-arithmetic pullback or ownership, while noting unmeasured two-cache
memory cost. On Python 3.14, installed tests also exposed lazy stdlib `ABC`
annotation metadata appearing after a strict shell-class authority snapshot;
capturing those exact keys up front resolves the false failure without
weakening the namespace comparison. The final same-process installed wheel
imported from its disposable site and passed 78/78 affected tests; wheel
SHA-256 `637671357D66400361FCA99FEFEB2D2A5DA403877DB7760CE7CA34116E293849`.
The earlier installed 50/52 run and its two authority failures are retained
as development history. This is a positive-load precision improvement, not
support for sign reversal, shell J2, fibre plasticity, F03, G3 or G5 acceptance.
The same solver wheel was paired with the unchanged ANYfem consumer wheel for
one consolidated installed run: 40/40 GE, B2 and consumer checks passed,
including construction, save/reopen, finite restart and B2 batching. Both
imports resolved inside the disposable site and OpenBLAS used one thread.
The complete run log, both wheels, hashes and test inventory are retained in
`.qualification/b3-ge-e4-pl/r7-ge-centered-combined-installed-dev-20260929-v1/`.
This confirms the current experimental integration slice on Windows; it does
not satisfy the remaining G0–G6 or cross-platform acceptance.

A separate finite-support flat-Q4 shell-pose prototype has exact box-window
centroid/covariance weights, objective rigid-motion recovery, a bounded
endpoint-witness screen, and first variations through actual shell/native
updates. Seven focused patch checks pass, including six-channel work,
physical pure torque without drilling, vertical transfer with director
freedom, and positive physical-only compliance on one patch. Independent
read-only review found no bounded factory or derivative defect. This is a
line-indexed 2D
distributing-footprint candidate, not a selected bonded line or a uniform
physical-core work proof.

The unsmoothed zero-width L1 normal-spin law includes shell-line endpoint
point evaluations and is unbounded on the continuum shell H1 energy space.
The physical-width rail is a **separate finite connection law**: Q4 E4-PL does
not expose a unique finite interior physical director field. Virgin first-order
Q4 top/frame variations match the owner's shape gradients and Mindlin signs.
At 35/70 mm thickness, point pure Mx/My/Mz and mixed wrenches balance,
include the native beam arm, do no shell drilling work, and excite supported
physical Q4 compliance. Point yaw-slope evaluation remains unbounded on H1;
these local checks do not qualify a line law.

A bounded material rail assembles two Gauss stations per segment with
fixed reference arclength weights and finite-dimensional sampled six-component
densities. Constant yaw density cancels interior shared-node shell work. Pure
moment and mixed densities produce the declared integrated shell/native wrench,
zero resultant and drilling work, and supported physical-only shell compliance.
Same-parent gradients and Hessians follow the actual native update. A
finite P0/P1 six-channel density basis gives owned coefficients,
exact piecewise-polynomial L2 Gram, and coefficient-conjugate projected gaps.
Four-segment tests check shared-node work cancellation, independently derived
growing density Gram, and positive supported E4 physical-only compliance; they
do not establish growing-space stability.
The virgin joint covector now maps to a spatial force and shell-rail moment
including the eccentric lever arm. A four-station physical-wrench quadrature
Gram uses frozen force/length scales; station-map equality alone does not
prove whole-segment constancy. Twenty-four focused checks pass. Independent
read-only reviews found no bounded discrete measure, scatter, or basis algebra
defect. Gauss exactness
applies to density products, not generally to nonlinear density-gap work.
**Generic L2 densities have no point values.** This raw coordinate-density
Gram is distinct from the new physical quadrature Gram. Whole-segment map
constancy or bounded integration error, curved-line transport, growing-space
stability, and full physical assessment remain.

A bare native B3 broken-half-cell L2 screen at 4/8/16 half-cells produced
upper quotients 9.260/9.222/9.213 × 10⁻⁶ J⁻¹. This finite-grid diagnostic
neither proves a uniform trace bound nor selects A/B. Its raw evidence is in
`.qualification/b3-ge-e4-pl/r7-f03-native-broken-l2-dev-20260928-v3/`.
The actual virgin retained Jacobian matches independent half-cell difference,
shear and nodal/cell spin rows on the same three bounded meshes. Those rows
give a mesh-independent broken-pose L2 estimate conditional on a local
energy lower bound. For the affine-straight virgin **constant diagonal
generalized section**, the cell's constant-force and linear-moment compliance gives
exact local energy ratios 1, 2 and 6 against that canonical strain norm,
independent of affine element length. The assembled 4/8/16 checks reproduce
the closed form to about 1e-16 relative matrix error. Independent mechanics
review confirmed that derivation and its Loewner extension to constant coupled
SPD generalized sections; a bounded coupled-section check passes. Curved or
non-affine references, fibres and loaded plastic states remain outside it.
This does not close F03.
Exact coarse-to-fine action transport is not an energy isometry, and three
reference levels do not bound the unseen same-law compliance tail. Historical
F5/S4 comparisons cannot allocate the physical difference to this connection.
The [F03 draft](B3_GE_E4_PL_G0_F03_PROSPECTIVE_ASSESSMENT_DRAFT.md) records
those limits and the mathematical obstruction.

## Next discriminating action

The physical-only Q4 block **does not uniformly control growing P0 yaw
density work on the tested longitudinal-only refinement family**. That
family holds two transverse cells fixed while longitudinal cells shrink;
the rectangles become increasingly anisotropic. Independent review derived
a mode:
nodal lateral pattern (1,-1,1) has zero mean shear on each cell but nonzero
mean over the fixed central rail strip. Alternating longitudinal amplitude h
and matching P0 yaw density give constant work 0.25 while physical energy
quarters for h=.25,.125,.0625. The actual E4 operator reproduces energies
6.579e9, 1.645e9, 4.112e8 J; drilling load and virgin gap are zero. The
negative executable check and raw logs are in
`.qualification/b3-ge-e4-pl/r7-f03-growing-rail-dev-20260928-v1/`.
PL numerical completion can penalize in-plane curl but is not physical shear;
the drill-only hourglass term does no work on this mode. Positive compliance
on one fixed grid did not establish a uniform bound.
The targeted twice-long P0 yaw support also retains this anisotropic family: on 4/8 fine
cells, physical energy 8.224e8/2.056e8 J and work 0.125. Thus a fixed
two-cell macro P0 support does not by itself cure continuity on that family.
Independent mechanics review confirmed the asymptotic witness and
its narrow implication. Its raw log is beside the first counterexample.
Even constant yaw density has a free-end witness: localizing the same
lateral pattern to the last shell cell keeps work 0.5 and fixed density
norm while physical energy halves at each refinement (5.263e10,
2.632e10, 1.316e10 J at h=.25,.125,.0625). Independent review confirms
the endpoint derivation. The executable check and raw log are retained
with the other negative cases.

The previous decision to abandon P0 yaw for all refinements was too broad.
The previous provisional classical comparison paired longitudinal and
transverse refinement; native F03 candidate meshes have not yet been pinned.
The anisotropic witness does not decide the paired family's outcome. The current box-window
prototype proves only bounded kinematics and first work variations; it is
an unselected alternative, not a replacement bonded-line law.

**Paired-refinement result:** The bounded 8/16/32 longitudinal by 2/4/8
transverse Q4 screen kept the rail-cell aspect ratio at 1.25 and the same
fixed physical strip, supports and density actions. The macro-P0 witness's
normalized work was 6.595e-6, 0.862e-6 and 0.795e-6; the constant
endpoint witness's was 4.663e-6, 0.431e-6 and 0.281e-6. The reported
quotient is the numerical work divided by the square root of q^T K_phys q
and the L2 density norm; no unit conversion was applied. Neither
shows the anisotropic divergence. The strip average of the alternating
transverse field is bounded by its two partial end cells and falls with
transverse cell width; q^T K_phys q is constant for this macro field and
increases for the endpoint field on these grids. This is a constructed-mode
screen, not a whole-space bound, mixed-system result or F03 acceptance.
The corrected-provenance raw output is in
`.qualification/b3-ge-e4-pl/r7-f03-paired-refinement-dev-20260928-v2/`.

**Complete yaw-row screen:** On the first two prospective paired grids, the
x=0-supported E4 physical matrices have no eigenvalue near the stated
numerical floor. The squared work-operator norm for all flat-reference P0 yaw
rows, including the shell top-surface rotation-x arm, changes from
7.1751385e-8 to 7.2329517e-8 under the script's unconverted physical
coordinates and L2 density Gram. Independent review checked the row signs
against the actual rail pose derivative and the rotation-only test. The
initial translation-only run is retained as invalid evidence. The
corrected-provenance full-row output is at
`.qualification/b3-ge-e4-pl/r7-f03-paired-yaw-upper-dev-20260928-v3/`.
The roughly 0.81% increase over two grids is not a mesh-uniform theorem.

**Six-channel reference result:** A bounded flat four-segment P0 shell-pose
map now matches the actual rail's Gauss-integrated translation and spatial
spin derivatives for mixed fields, infinitesimal rigid motion and free
transverse shear. It has no drilling work. At the centred virgin connection,
the integrated six-component relative-gap derivative equals native retained
half-cell pose motion minus that shell map, including the beam offset arm.
The focused rail suites pass 29/29 with the worktree source imported.
Independent mechanics review found no
first-order sign or top-offset omission. The native comparison reuses the
port tangent; existing actual-update derivative checks supply a separate
bounded port check. This is not an assembled work-Hessian, loaded-transfer,
finite-motion, physical-core bound or mixed-stability result.

**Next decision:** Keep the rail as a development candidate. Derive or
refute a supported six-channel physical-core/broken-native work bound over
the intended mesh domain; compare matched torque/shear transfer and assess
the constrained mixed system before selecting an interface space. The loaded
screen below rules out a singular or drilling-only response on one flat grid,
but cannot settle the law, discrete stability or physical fidelity. No
historical F5 result is treated as the same connection law. Increasingly
anisotropic Q4 meshes are not silently excluded: the programme has no
explicit aspect-ratio ceiling, and any new admission rule needs scientific
review. The current E4-PL Q4 validation checks Jacobian nondegeneracy and
warpage; it does not supply a fixed element-aspect admission that removes the
tested anisotropic counterexample from this prospective domain.

**Current-law slip discriminator:** The older C1 hybrid's mode-resolved check
already distinguished transverse section nullity from coarse longitudinal
projection nullity. A focused check now applies the even transverse field to
the current finite-width rail itself. The shell root is fixed and the E4
physical tangent gives positive strain energy; local top-surface slip is
10 micrometres at the terminal centre node. Yet the finite rail pose at every
Gauss station has zero six-channel gap, and P0, continuous-P1 and dual rows
at 2/4/8 intervals all vanish to roundoff. This follows from the rail's
transverse averaging, so repeating longitudinal refinement cannot detect
this mode. It is an admitted section deformation if the chosen connection
means an averaged pose bond, but it forbids describing the rail as a
pointwise welded surface bond. This is a law-semantics observation, not a
zero-energy mechanism or candidate acceptance. The next decision must test
the declared reduced law's physical torque/shear transfer against a matched
reference and establish the mesh-domain work bound and mixed-system behavior.
The bounded executable check is
`tests/test_b3_e4_f03_flat_rail_six_channel_map.py` (4/4 source checks).

**Matched-reference allocation:** Existing flat-web CalculiX and native L1
runs match nominal plate/web dimensions, axis, root and applied resultants,
but differ in connection and web idealization. Re-running the native energy
split initially failed the GE work-scaled equilibrium check for the P1
plate-load case; that failed output and row-level diagnosis are preserved in
`.qualification/b3-ge-e4-pl/r7-flat-web-native-energy-dev-20260928-v1/`.
One correction using the unchanged cached sparse factor reduces its ratio
from 2.01e-7 to 1.01e-10, without changing the 1e-8 acceptance limit or
accepted prefix. Product source `4773cfef` and the strengthened matched-case
test pass 24/24 source checks; the historical wheel SHA-256 is
`bf38641fd1009f98a7dcff48ab1905c39cbe22c232a1fc6cab20f825731933ee`.
That 24-test pytest log also had a source-path ambiguity, now resolved by the
34-test same-process installed suite above. The installed native run used one
factorization and one P1 refinement; source
and installed results are retained in the versioned `r7-flat-web-native-energy`
v2 and `r7-ge-linear-refinement-installed` v1 directories.

For plate Fy, native shell energy is 99.65% of total versus 99.86% in the
executed external partition. For web tip Mx, native shell energy is only
0.62–1.51% across P1/P0 versus 18.91% in the welded-shell reference;
native total load work is about 77% of the external result. This is a
specific torque-transfer discrepancy requiring physical connection/section
review. It does not isolate the rail alone: the web is a shell in CalculiX
and a generalized beam natively, and the uncoupled decks change seam
topology, so their work cannot be subtracted as an exact partition. The next
comparison needs verified sided work or an otherwise genuinely same-law
reference before scoring the interface. No finer axial or new external mesh
follows automatically. F03 stays open.

**Saved sided-work decision already closed:** The previously executed C3D20R
F5 cut at x=.95 m was validated and independently reviewed in the historical
checkpoint's V3 sided-port and V2 native-port compatibility records. Its
free-bar/root/support residuals and sampled opening pass; left/right broken
cut twist duals are +57.416/−58.278 Nm, with a +0.862 Nm seam action at the
shared cut. A side-restricted twist of shared bonded nodes is not admissible
for the intact assembly, and no unique conforming extension from the native
retained port to all solid cut nodes is established. Direct sided-port
accuracy scoring therefore remains stopped. The September 29 validator rerun
in `.qualification/b3-ge-e4-pl/r7-f03-saved-sided-port-validation-dev-20260929-v1/`
reproduces that completed bounded result; it is not a new gate milestone.
Use the validated common-field F5 actions and same-action shell response while
the connection law and physical torque/shear transfer are decided.

**Six-channel paired-screen result:** With the same supported 8x2 and 16x4
grids, finite strip, and growing P0 rows, the complete shell-side work map
has no action on a numerical near-null mode on either grid. At a declared
0.1 m force/moment length scale, its largest positive-subspace quotient
changes from 5.16221185e-7 to 5.20803030e-7 (about +0.89%). The leading
density is about 96% transverse force on both grids. An independent yaw-row
formula matches the six-channel scatter exactly; its component reproduces
the earlier complete-row result after the explicit length scaling.
This finite result identifies transverse physical transfer as the next
matched-reference priority; it is not a mesh-uniform theorem, unit-invariant
accepted norm, mixed-system test, or multiplier choice. Raw output is in
`.qualification/b3-ge-e4-pl/r7-f03-six-channel-work-dev-20260928-v2/`.

The existing CalculiX folded-shell comparator is not a matched reference
for that loaded rail: it has a 0.2 by 0.01 m web joined along the full
shared midsurface seam, whereas the current native fixture has a generalized
section with A=0.01 m2 and Iy=Iz=8.333e-6 m4, a 0.0675 m axis height, a half-length
finite-width rail, and a free beam root. The existing external support and
connection outputs cannot score this candidate. The next reference must
match section, axis/offset, load, support and attachment extent, and expose
the relevant physical work before comparison; a finer run of the current
deck would not distinguish the line-law question.
**Loaded flat-screen result:** The 16-Q4, 8-native-half-cell, four-segment
P0 development fixture solves separate +100 Nm tip torque and +1000 N tip
vertical shear with the beam root free. The support wrench balances both
loads; the full KKT residual and integrated connection gap are small. The
physical shell tangent carries positive work. Removing the numerical shell
completion changes tip rotation by about 0.028% under torque and tip vertical
translation by about 0.0008% under shear. Its reported `q^T K q` values are
twice conventional strain energy. This is one flat elastic grid, not a
uniform physical-core bound, a same-law external comparison, or accepted
torque/shear fidelity. Independent review checked assembly signs and support
wrenches and found no bounded-screen defect. Raw output is in
`.qualification/b3-ge-e4-pl/r7-f03-physical-rail-loaded-dev-20260928-v2/`.

**Evidence provenance correction:** The repository virtual environment
originally resolved `anysolver` from the main checkout. Earlier local screen
directories (paired v1, yaw v2, loaded v1) are preserved but are not evidence
of worktree-package execution. The relevant shell/native source hashes matched
and explicit-worktree reruns reproduced their numerical values exactly. The
current screen scripts reject an imported checkout other than this worktree;
their new output records the imported path. These remain source-level
development screens, not installed-artifact qualification.

F03 formal assessment stays barred. The seven ratios, growing spaces, three
refinements, physical transfer, locking, shear, drilling, and mixed-system
checks remain mandatory. No automatic axial sweep or new external reference
is justified without a discriminating hypothesis.

## Execution boundary

At most three workers and one heavy numerical job at a time. New diagnostics:
100,000 rows, 600 seconds/run, eight numerical threads, 8 GiB process-tree
memory; verify effective settings. Historical one-use authorities are not
replayed. Preserve raw failures and exact scientific criteria. G0–G6,
V01–V28, B01–B18, external comparisons, scale, independent reviews,
consumers, and one authorized coordinated release remain mandatory.

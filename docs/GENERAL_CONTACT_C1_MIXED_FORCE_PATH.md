# C1 development: mixed force and displacement shell-contact path

## Bending-direction refinement and sliding limit (27 September 2026)

At unchanged 1 m source span, two fixed S3 targets, physical skins,
total −0.1 N right-edge force and strict 1e-5 Pa multiplier-change gate,
the solver-accepted **press steps** gave 0.01956348, 0.02645245, 0.02857212 and
0.02849993 N contact force on 2, 4, 8 and 16 Q4 source faces. The 8-to-16
change is 0.253%; the 2-to-4 change is 35.2%. All reported press states met
their 50 µm physical-gap gate. The 8-Q4 press used a 100 Pa explicit Schur
pressure cap because its accepted pressure peaked at 17.87 Pa; a 10 Pa cap
had rejected the loaded step. These are development comparisons, not a
registered independent structural reference or C1 acceptance.

An 8-Q4 four-phase right-edge-force route accepted press but rejected the
first slide step at the seven-augmentation limit. Both two- and three-step
phase sampling encountered a weak coupled pressure-response direction near
the target's physical edge. Terminal Q1 support remained positive and the
scaled pressure Gram retained full rank. A local equilibrated-gap response
oracle identified a terminal two-mode root around 77.69 and 159.00 Pa,
explaining why 100 Pa pressure and 5 Pa step caps could not reach it. With
250 Pa pressure and 200 Pa step caps, the unchanged mechanical gates and a
three-step sampling of each phase, the development route completed all 12
steps in 181.29 s. It had 0.028572125 N force at loaded press, 0.022358829 N
at full slide, zero contact force while open and 0.022358829 N at recontact.
The largest accepted pressure was 154.07 Pa; worst reported penetration was
2.0735 µm against the 50 µm registered development gate. A fresh-model
six-step split restart exactly reproduced all 12 saved forces, gaps, active
counts and multiplier changes. These exploratory settings have not been
frozen as an independent response reference or verified in an installed
package. The earlier failed routes remain in the living note and raw reports.

The same twelve-step cycle also completed at 16 Q4s in 343.46 s after the
pairwise Q4 weighted-gap value allowance was propagated consistently into
the assembled patch comparison. Its press/full-slide/open/recontact forces
were 0.028499927/0.023887460/0/0.023887460 N, peak pressure was 77.01 Pa
and worst independent gap was −0.965 µm. The full-slide force differs from
the eight-Q4 value by 6.399% relative to the finer result, well above the
proposed 2% response target. Both meshes place their two active Q1 pressure
nodes near the target's physical x=1 m edge. The finer mesh reduces each
node's overlap support and increases its pressure; this edge response needs
further resolution or a separately bounded interior-overlap qualification
case. The earlier two sixteen-Q4 recontact failures are retained separately.

An interior-overlap development variant widens only the S3 target to x=1.3 m
and keeps the Q4 source, right-edge force, 50 mm slide and all numerical gates.
The branch-aware pressure proposal now considers a projected release candidate
even when a safe fixed-active-set half-step exists. The eight-Q4 cycle
completed with 0.034098737 N at press, full slide and recontact; a projected
proposal released contact at first unloading. The sixteen-Q4 cycle completed
with 0.035030437 N at the same loaded phases. Its first unloading increment
retained a small 0.00121749 N contact force, while both meshes fully opened
and recontacted. The loaded-force change is 2.6597% relative to sixteen Q4s,
above the proposed 2% target. A twenty-four-Q4 cycle also completed, with
0.035326285 N at press, full slide and recontact, and zero force at complete
opening. The sixteen-to-twenty-four change is 0.8375% relative to the finer
mesh; first unloading still retains a small 0.0016770 N force before release.
This three-level development trend supports a refined response reference,
but none has been frozen or independently accepted. The interior variant
also still needs its own split restart and installed-package verification.

A trapezoidally distributed −0.1 N load
completed eight steps but never activated contact. A −0.2 N distributed
load activated contact and rejected the press step; one bounded Schur
relinearization lowered, but did not close, its multiplier residual. The
raw records and exact settings are listed in `GENERAL_CONTACT_RESTART.md`.

Float and Jet2 overlap values have a shared, explicitly capped comparison.
Numerically subresolved Q4/S3 wedges have separate 1e-6 actual-area and
full-vector value caps. Resolved support retains component checks; weighted
gap is compared normwise to handle components near zero by cancellation.
The assembled patch comparison accumulates only the pairwise weighted-gap
allowances already admitted. Twenty-eight affected owner, geometry,
pressure-response and high-precision wedge checks passed. The numerical
polygon-area resolution is an indicator, not a certified error bound.

At one captured physical-edge pose, an independent 80-digit polygon clip
and physical-Q4-work integral reproduced the Jet2 frozen-pressure
directional weighted-gap Hessian to about 4e-15 relative across three
quadrature orders and five smooth perturbations. Independent review checked
the fixture against the captured coordinates and found no circular call or
geometric mapping defect. This qualifies only that local derivative direction;
the full mortar tangent, other tiny-wedge branches, pressure response and
coupled C1 acceptance remain open.

## Differentiated strict-pressure development route (27 September 2026)

An opt-in candidate selects the existing Jet2 Q4/S3 overlap derivative,
projected-matching physical-gap certificate and supported-pressure Schur
acceleration mode for the same force-driven eight-step path. The saved
record does not establish whether a Schur proposal was applied. The explicit normal
stiffness is 10,000 Pa/m, the pressure-change tolerance is 1e-5 Pa, the
physical-gap tolerance remains 50 µm, and at most seven augmentations are
allowed per step. Other Schur and derivative budgets are in
`scripts/general_contact_d1_mixed_jet2_schur_probe.py`.

The path completed press, 50 mm slide, open and recontact in 51.65 s. Its
phase-end active-node counts were 2/2/0/2 and normal contact forces were
0.0195634815/0.0151600225/0/0.0151600225 N. The most negative phase-end
gap was −7.4519 µm. A fresh-model restart after the slide reproduced all
eight saved force, gap, activity and multiplier-change records exactly.
The first probe's console serialization failed after it wrote the completed
JSON; the traceback and raw result are retained separately. The probe now
uses native JSON booleans and refuses to overwrite saved outputs.

An independent planar-overlap calculation for uniform 10 µm compression
predicts 0.81 and 0.765 m² overlap at 0 and 50 mm lateral shift. Its 0.081
and 0.0765 N contact-force and 8100 and 7650 N/m uniform normal-tangent
predictions pass a focused local regression. This tests changing overlap
and the bounded normal work map at prescribed uniform poses. The coupled
path still has the earlier 35.2% two-to-four-Q4 bending-direction response
change at strict enforcement; it lacks a refined response reference and
independent acceptance. The saved path does not include external/support
reactions or deformed overlap areas, so the local prescribed-pose oracle does
not independently verify whole-path equilibrium or overlap. The new route is
a tested development profile.

`ContactPathNodalForce` adds explicit translation-force values, in newtons,
at a `ContactPathProgram`'s waypoints. Force values and displacement targets
interpolate at the same accepted path steps. A segment may change force
while its displacement controls remain fixed. All force histories begin at
zero, use unique physical node/DOF identities, and are bound into the
version-2 contact-path restart contract. Programs without forces retain
their previous contract and history shapes.

At each Newton candidate the reduced equilibrium residual includes the
current external nodal force. Accepted support reactions subtract that
force from the complete internal/contact residual. The history records
nodal force values and a **trapezoidal approximation** to their incremental
work; this is a path diagnostic, not an exact nonlinear energy integral.
No structural or contact state commits until the complete equilibrium,
augmentation and physical-gap checks pass.

`examples/general_contact_refined_q4_s3_mixed_path.py` starts two connected
Q4 source faces 40 µm above two nonmatching physical S3 V2D target faces.
The target is fixed, the source's left edge has z supports, and two left
source x coordinates are prescribed. A force of −0.05 N on each right-edge
node presses the source; the x controls then slide it 50 mm. Unloading to
zero gives a positive 40 µm gap and zero contact force. Reloading restores
contact. There is no prescribed normal overlap or hidden stabilizing
spring. The normal law remains the declared projected augmented Q1 mortar
profile with a 50 µm independent gap budget.

The first 5 mm-gap probe stayed open under 0.1 N total load, as its
measured deflection was only about 56 µm. That result is retained as
`c1-mixed-path-press-first.txt`. With the declared 40 µm initial gap,
the eight-step path completed in 67.66 s (`c1-mixed-path-four-phase-first.txt`).
At the four phase endpoints its active pressure count was 2, 2, 0, 2;
conservative lower gaps were −15.736 µm, −12.811 µm, +40 µm and
−12.811 µm. The source normal contact forces were 0.001067 N,
0.000609 N, 0 and 0.000609 N. Every accepted step met the same 50 µm
physical-gap budget. The source example completed with the same phases
(`c1-mixed-path-example-source-first.txt`).

The opt-in `tests/test_general_contact_mixed_path.py` checks stage
interpolation, legacy contract identity, per-step paired force/moment,
external-versus-support vertical balance, work signs, exact split-restart
checkpoint replay and rejection of a changed force history. It passed
3/3 in 160.95 s with `ANY_RUN_C1_MIXED_PATH=1`
(`c1-mixed-path-full-split-first.txt`). The previous displacement-only
two-step press retained its exact gap and force outputs
(`c1-mixed-path-no-load-press-regression-first.txt`).

This is implemented, locally tested development work. The contact
pressure space still needs partial-contact stability and coupled
mesh/enforcement convergence. The local test does not provide independent
engineering acceptance, and application integration remains open.

Clean source `f466eec2ec110554e98d680ee7a9274155249327` built an offline no-isolation wheel, installed it
without dependencies into an isolated target, and asserted that `anysolver`
was imported from that target. The wheel SHA-256 is
`6CA3D97EF99D4557A5FF84178ABD3A8D417045800854456ABF5F87BA1FE1CE45`.
The complete 1,003-byte source and installed example outputs were
byte-identical (SHA-256
`CF90DB1E471A42885FFE1484A555606FE06C67982281D064ABA9A8593115DDBB`).
The build, install, import-origin and run logs are retained under
`C:/ANYworkspaceWork/general-contact-evidence` with
`wheel-f466eec2-*` and `c1-mixed-path-example-*` names. The wheel was
not published; this checks package routing for this development case.

## Mesh and enforcement sensitivity

A conforming four-Q4 source patch replaced the two-Q4 source while
retaining the same two-S3 target, physical supports, total −0.1 N uniform
right-edge load, 50 mm x controls, 1000 Pa/m normal stiffness, 0.02 Pa
pressure-update tolerance and 50 µm independent gap budget. The four-Q4
path completed all eight steps (`c1-mixed-four-q4-full-first.txt`). Its
active pressure count was 3/3/0/3 at phase endpoints, compared with
2/2/0/2 for two Q4s. The largest active-step integrated normal-force
difference was 0.0070% relative to two Q4s; the largest conservative-gap
difference was 0.000256 µm (`c1-mixed-mesh-compare-first.txt`). This is
two-level sensitivity for one load/regularization path. It does not prove
mesh convergence, particularly for localized partial contact.

The normal enforcement study on the **two-Q4 press only** shows that
normal stiffness and multiplier consistency materially affect the
integrated answer:

| Stiffness (Pa/m) | Update tolerance (Pa) | Result within 16 updates | Source normal force (N) | Lower gap (µm) |
|---:|---:|---|---:|---:|
| 1000 | 0.02 | Completed | 0.0010670 | −15.736 |
| 1000 | 0.002 | Stopped; final update 0.003255 Pa | No accepted force | −11.557 trial |
| 10000 | 0.02 | Completed in 4 updates | 0.0163401 | −9.622 |
| 10000 | 0.002 | Completed in 10 updates | 0.0192712 | −8.349 |
| 10000 | 0.0002 | Stopped; final update 0.000991 Pa | No accepted force | −8.170 trial |

The 10000 Pa/m response changes about 15% between the two **accepted**
pressure-update tolerances. The stricter failed run reached a trial
normal force of 0.0194703 N at update 16, about 1% above its update-10
trial force, but did not meet its declared 0.0002 Pa criterion. Its
structural residual and physical gap were small; neither overrides the
failed contact-consistency gate. The failure retained and restored the
last accepted open state. Failure-only augmentation diagnostics now
include active count, global source-contact-force vector and sampled gap
(`c1-mixed-enforcement-trace-force-first.txt`). These measurements rule
out a C1 response-convergence claim based on the small mesh difference
at the original regularization. No stiffness or update tolerance is
recommended as a universal application setting from this study.

The bounded failure rerun also retained the mortar pressure-space state at
each augmentation. Its six-node pressure Gram matrix had rank 6 and a
condition estimate of about 24.8 throughout. The two active source nodes
(IDs 3 and 6) ended with normalized weighted gaps of +0.0693 and −0.0991 µm
respectively, while the multiplier update still exceeded tolerance. This
evidence does not indicate full Gram rank loss. The coupled structural and
contact response of those two active multipliers is the next numerical
question; their projected update must not be accepted on the basis of
integrated force settling alone. The raw trace is
`c1-mixed-pressure-space-discriminator-source-first.txt`; its temporary
`pressure_gradient_condition` key contains the Gram condition estimate.
The source now gives Gram and gradient diagnostics separate names.

Secant fitting of the two active multiplier coordinates across the retained
failed augmentations gave a projected-map eigenvalue of 0.97732 in its slow
mode. This explains the high iteration count on that branch. The optional
`augmentation_acceleration="active_secant"` predictor described in the
[augmented path guide](GENERAL_CONTACT_C1_AUGMENTED_PATH.md) completed the
unchanged strict press in five updates and the eight-step cycle including
opening and recontact. A four-step split restart reproduced the full
accepted history; changing the option invalidated the checkpoint. The
original projected consistency and independent gap checks still decide each
increment. This reduces iteration cost for the observed branch, but does not
establish physical response convergence or a universal performance result.

### Bending-direction mesh sensitivity at strict enforcement

The earlier four-Q4 comparison split the source across its width, where this
case has nearly uniform loading. Refining along the bending direction gives a
different result under the same −0.1 N total force, 10000 Pa/m normal
regularization, 0.0002 Pa multiplier tolerance and 50 µm physical gap budget:

| Source mesh | Accepted press? | Source normal force | Conservative lower gap | Active pressure nodes |
|---|---|---:|---:|---:|
| 2 Q4 along x | Yes; 5 updates | 0.0195635 N | −7.452 µm | 2 |
| 4 Q4 along x | Yes; 11 updates | 0.0264524 N | −2.790 µm | 2 |
| 8 Q4 along x | No; 16-update cap | No accepted force | −3.584 µm trial | 4 trial |

The accepted two- to four-Q4 force changes by 35.2% relative to the coarse
result. A source-only load applied at x=0.85 m gives equal free tip motion but
local displacement of −39.0 µm on two Q4s and −46.8 µm on four; local
structural interpolation contributes to the coupled difference. The eight-Q4
case required 14,144 declared pair-local Hessian energy evaluations. After
resource admission it stopped because its final projected multiplier change
was 0.025733 Pa, despite a small structural residual and a physical gap
within budget. Its four-active-node secant samples were poorly conditioned;
rank-truncated offline extrapolations either reduced the predicted residual
only modestly or required inadmissible negative/very large multipliers. These
results provide no three-level response convergence and no accepted eight-Q4
reaction. Raw runs and the bounded offline audit are retained under
`C:/ANYworkspaceWork/general-contact-evidence` with `c1-mixed-four-q4-x-*`,
`c1-mixed-eight-q4-x-*`, `c1-source-*-mesh-*` and
`c1-eight-q4-reduced-secant-audit-*` names.

An assembled tangent audit at the failed eight-Q4 pose reproduced the last
observed weighted-gap change to about 4.2×10⁻⁸ relative. The four-active-node
linearized complementarity system has no nonnegative root on that active set;
its locally feasible subset retains only source pressure nodes 9 and 18.
The predicted pressures (about 9.16 and 18.60 Pa) are far beyond those in
the failed trajectory, so this was tested only as a disposable algorithmic
trial. Fixed-multiplier equilibrium was reachable with two active nodes.
Ordinary projected updates remained slow, while one application of the
existing guarded secant predictor brought a subsequent two-node trial below
the declared 0.0002 Pa multiplier-change tolerance with a certified gap.
That trial was not committed by the public solver. Deriving and safeguarding
the active-set pivot in the production path remains necessary before an
eight-Q4 result can be accepted. The tangent and pivot evidence is retained
as `c1-eight-q4-schur-*` and `c1-eight-q4-pivot-*` files.

### Later differentiated interior-overlap development and narrow press gate

The opt-in Jet2 geometry and supported-pressure Schur route subsequently
completed twelve-step press/slide/open/recontact cycles at 8 and 16 Q4 on
the physical-edge target. Their loaded press forces differed by 0.253%, but
their full-slide forces differed by 6.399%; this does not qualify edge
sliding. Moving only the fixed S3 target's right edge to x=1.3 m gave an
interior-overlap development route. Its 8/16/24-Q4 cycles completed under
the same 50 µm physical-gap and 1e-5 Pa multiplier-change criteria. Loaded
forces were 0.03409873708, 0.03503043719 and 0.03532628509 N. The eight-Q4
cycle also replayed all twelve force/gap/active/multiplier-change records
exactly from a fresh-model midpoint restart. These cycles remain development
evidence; first-unload contact differs between 8 and finer meshes.

A separately frozen 32-Q4 **two-step press-only** case completed in 249.114 s
at 0.03547159554 N. Its 24-to-32 force change was 0.40965%, and the
16/24/32 inverse-mesh fit placed the 24-Q4 force within 1.63611% of its
extrapolated limit. Full supported pressure rank, equilibrium, wrench,
accepted load, integration indicator, multiplier and independent gap gates
passed. An independent reviewer checked the immutable source and evidence
identities and the numerical calculations, accepting only this registered
integrated press-force refinement claim. The frozen prediction was fitted
from development data, not derived from an analytical force oracle. The
[registration](reference_cases/general_contact_d1_mixed_interior_response_v1.json),
[review](reference_cases/general_contact_d1_mixed_interior_response_v1_review.md)
and retained raw reports provide the exact boundary. Full-cycle response,
physical-edge behavior, installed verification and C1 remain open.

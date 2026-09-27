# Current B3-GE / E4-PL / B2 development checkpoint

## Current state — 27 September 2026

**Decision sought:** Establish a physically credible native two-sided
beam–shell law and stable exact line space before G1.
**Established:** Native side work and derivatives pass; the six-channel law
is a reduced strip-pose candidate, not a pointwise welded face bond.
Matched detached-solid work differs materially from the native action.
The split-solid torque/opening fields show sampled overlap; the separate
reverse-Fz opening field has positive same-XY samples on 120 available
faces but lacks seam data and continuous separation. B2 physical-section
checks pass at sampled points; fail-closed F09 admission remains unfinished.
A new material-line proof detects the even-slip mode and passes bounded
position/Jacobian checks. Its value-only orientation probe is objective,
non-drilling, and preserves the tested shear mode. Its reference orientation
Jacobian passes Q4/S3 reference and nonzero-gap chart differences;
one chart-corrected mixed-curvature diagnostic passes. A general
second-variation operator and coupled transfer remain open.
**Remaining uncertainty:** Allocate torque/shear differences among the
continuous law, discrete enforcement, contact, and domain idealizations;
assess growing-space stability and physical transfer together.
**Next discriminator:** Design one physically matched torque/shear reference
with a declared connection and admissible surface-order evidence; the
saved C1 half-load no-contact route also overlaps and is rejected. Use
existing native work to derive the separate bonded material-line trace;
advance B2 F09 and independent foundations without repeating axial/opening
sweeps.
**Gate:** G0B open, G1 barred; formal F03 authority unconsumed.

## Detailed reference state and saved-field decision — 27 September 2026

**Decision sought:** Decide whether the declared native two-sided six-channel
joint is physically credible and which exact line space remains stable and
accurate before G1.
**Established:** Finite-state native side work and derivatives pass. A
matched, detached C3D20R solid now has an independently reviewed *linear*
six-channel plate/bar work map. Six capped external action solves give a
positive, reciprocal 6×6 compliance; exact KKT reconstruction closes both
supported load gaps near `1e-19`. On the same E4 x4/y4 shell, replay of its
physical plate action differs materially from native P0/P1/dual actions:
the native-action shell work is about 7–8% higher for opening and 9% higher
for torque. On the same retained B3 beam, the native-action work is about
2% higher for opening and 12–17% higher for torque. The earlier shared-node
F5 bond remains a distinct idealization.
The x16/m16 alternating P0 Fz dual near-kernel persists under two norms but
is not proven primal locking. The exact two-interval solid split lowers
load work by 1.214% opening and 1.533% torque versus the global-six solid.
Its action moves same-domain E4 and B3 work toward native P0, especially
for opening, but a substantial torque gap remains. B2 F09 remains open.
An isolated supported director-pitch couple does work through physical E4
bending with negligible numerical drilling work; this does not validate the
loaded coupled connection.
A bounded loaded My case transfers about `4.1 Nm` to the shell support and
`95.9 Nm` to the beam root, with balanced work but `0.16%` numerical shell
work. Per-channel recovery assigns about `28%` of shell interface work to
pitch and the remainder mainly to Fx/Fz; those channels' large My wrenches
partly cancel. Removing pitch rows raises loaded tip ry `1.2–2.3%` but
barely changes shell support My, so this channel affects the bounded
response without establishing the physical connection's fidelity.
The saved split-solid no-contact fields have independently reviewed sampled
same-deformed-XY surface-order overlap witnesses: 81 torque and 20 opening
samples among the initially negative paired-parametric subset, with minimum
gaps `-45.58 nm` and `-33.78 nm`, respectively. The witnesses are interior
to the paired Q8 faces with negligible XY projection defect. This is not a
global contact or penetration certificate. It does rule out treating these
linear no-contact fields as an admissible physical accuracy reference.
The previously executed factor-4 reverse-Fz solid has **no sampled overlap
witness** on the 120 detached faces with saved interface displacements:
all 9,720 interior same-deformed-XY projections succeeded, minimum gap
`+0.547735 µm`, maximum XY defect `1.77e-14 m`. Eight seam-adjacent faces
lack saved shared-node displacement, and sampling does not certify
continuous separation. This is an opening-only candidate, not the missing
torque/shear reference.
**Uncertainty:** Whether the remaining torque/shear difference is a defect
in the continuous six-channel trace or arises from contact and differing
solid-versus-E4/B3 idealizations. The existing C1 penalty reference also
retains sampled overlap (`31/10,368`, minimum `-3.162 nm`); neither field
allocates that cause, establishes refinement behavior, or selects P0/P1/dual.
**Next discriminator and action:** Reuse the completed C1 mode-resolved
evidence: supported positive-energy even transverse slip has zero continuous
six-channel gap; a distinct longitudinal gap is nonzero continuously and
detected by a growing row space. Thus the current continuous law is a
*reduced strip-pose* candidate; it cannot be called a pointwise welded face
bond. Decide its permitted local deformation and physical pitch/torque work
explicitly, then assess the growing multiplier space, supported work and
locking on the registered ratios. A distinct full-bond law needs its own
trace and evidence if full surface bonding is required. The matched
hard-mortar contact method exited `201`; removing the seam-adjacent column
hit the 2-GiB cap, so this factor-4 route cannot now provide a valid physical
torque reference. Reuse executed F5 and pre-opened C1 evidence only at their
valid levels while redesigning the reference. Do not repeat completed fields,
finer classical axial solves, or a contact stiffness/mesh sweep. Advance B2
F09 and other independent foundations while F03 remains unresolved.
No multiplier space is selected and F03 remains open.
**Gate:** G0B open, G1 barred; formal F03 authority unconsumed.

**Saved reverse-Fz discriminator outcome (27 September):** The negative
witness branch did not occur. The saved field is therefore retained only
for a future complete-face/continuous separation check if opening-reference
accuracy becomes the decision bottleneck; it is not promoted to a physical
no-contact comparator. Versioned results are
`B3_GE_E4_PL_F03_REVERSE_FZ_SAME_XY_DEV_V1.json` (initial face-local
indexing) and `B3_GE_E4_PL_F03_REVERSE_FZ_SAME_XY_DEV_V2.json` (original
face IDs and omitted seam IDs), whose SHA256 is
`856AEE36E922833011227EF2602B9096CBCD036E339D045FF81D3DD7096D38EC`.
The next F03 physical-reference effort must target torque/shear with a
declared connection and an admissible surface-order check. No further
reverse-Fz refinement follows automatically; independent F09 and other
foundations can proceed while that reference is designed.

**Next bounded torque-reference discriminator (prospective):** The saved
linear C1 full-displacement solid has a 2 µm tapered clearance and a
100 Nm no-contact torque field with a previously observed same-XY overlap.
Scale only that saved displacement field by one-half, corresponding to a
50 Nm load on the unchanged linear geometry, and sample all 128 paired Q8
faces at the same interior 9×9 points. First reproduce the full-load
negative witness. A half-load negative witness rejects this route; an
all-positive half-load sample retains a 50 Nm candidate for continuous
gap, idealization and mesh checks. It is not a torque accuracy score or
formal F03 execution, and no solver run or clearance tuning follows from
this diagnostic.

**Torque half-load outcome and decision (27 September):** All 10,368
same-deformed-XY face-interior projections succeeded. The full 100 Nm
field reproduces a `−7.11249 nm` minimum and 43 negative samples; the
linearly scaled 50 Nm field still has 27 negative samples, minimum
`−2.20022 nm`, on the unchanged 2 µm-clearance C1 geometry. Both are
interior surface-order overlap witnesses with XY defects below `5e-16 m`.
The bounded half-load branch therefore fails as a physically admissible
no-contact torque comparator. Do not chase success by another load or
clearance sweep. The next external reference needs a declared, matched
connection whose open/contact state can be independently validated.
The immutable source-bound result is
`B3_GE_E4_PL_F03_C1_TORQUE_HALF_LOAD_GAP_DEV_V1.json`, SHA256
`4A105B42C48C4EDEF501440EF12648DACD8FD25EE3A95836FB48B91D4B44EB66`.
This is a sampled rejection, not a continuous contact or native accuracy
assessment. F03/G0B remain open and formal F03 authority unconsumed.

**F03 connection-law classification decision (27 September):** Independent
read-only mechanics review of the actual operator and mode evidence found
that the current six-channel transverse mean/first-moment plus director-pitch
law is a *reduced distributing strip-pose line*. It is line-integrated, so
it is not the same as a finite-area footprint, and its objective work and
physical pitch transfer remain useful. However, the supported even
transverse shell slip has zero continuous six-channel gap at every x while
its local slip RMS is about `7.439 µm` and physical E4 strain energy about
`30.11 J`. Longitudinal multiplier enrichment cannot detect this mode.
For the programme's required **bonded material line**, a nonzero relative
displacement on the declared weld/material path is inadmissible; permitting
that displacement would change the intended connection to the reduced
strip-pose idealization. Therefore the current candidate cannot, by itself,
fulfil the bonded-line capability. This classifies its scope rather than
declaring it a failed formulation or rejecting its other valid checks.

**Next mechanics slice:** Derive a separate local shell-top/beam-surface
material-line position trace at a declared transverse path, with a physical
orientation transfer that uses the independent shell director and preserves
admissible transverse shear. Compare its continuous gap on the existing
even-slip, rigid-motion, torque, shear and nonmatching patches before
choosing longitudinal multipliers. Verify first/second work variations,
physical wrench balance and drilling independence before loaded accuracy
or ratio sweeps. One ad hoc even-mode row or a higher-order x multiplier
does not supply this law. The independent review does not close F03/G0B;
G1 remains barred and formal F03 execution authority unconsumed.

**Material-line position feasibility slice (27 September):** Private
`scripts/b3_e4_f03_material_line_position.py` now samples the shell top
at the declared material path `y=0` against the actual native retained
B3 underside, splitting at shell and half-cell cuts. The three-component
beam-frame position gap owns its reference correspondence and rejects raw
reference mismatch above `1e-10 m`; it cannot erase a geometric gap by
redefining an offset. The analytic reference Jacobian includes the E4
top-surface lever arm and B3 underside/spatial-chart lever arm. Six focused
tests pass with JIT disabled: the supported positive-energy even-slip mode
is detected while the old six-channel strip mean remains zero; a common
supported shear slope and common translation have zero line gap; actual
chart directional differences, a finite common rigid motion localized to
the bond, Q4/S3 geometric interpolation and mismatch rejection pass.
Independent read-only review found no blocking sign/work defect for the
three-channel derivation and identified the reference-offset loophole,
which the raw-gap guard and negative test closed. This is not a full pose
law: shell director orientation, couple work, second variation, mixed-S3
mechanics, global stability and loaded torque/shear are unqualified.
No production owner, F03 gate acceptance or G1 entry follows.

**Next bounded orientation discriminator (prospective):** At the same
material-line stations, form a shell pose from the independently interpolated
E4 director and the material longitudinal tangent projected perpendicular
to that director. The competing outcomes are an objective, non-drilling
frame that permits director/tangent shear versus a degenerate or
mesh-sensitive frame that cannot support the required line pose. Check the
reference, finite common rigid motions, a director-tilt/shear field, and
Q4/S3 host behavior. A pass only licenses derivation of the orientation
work variations and beam-relative Log constraint; a failure returns the
pose construction to G0 mechanics. No longitudinal multiplier selection or
loaded accuracy inference follows from this value-level test.

**Orientation discriminator outcome (27 September):** The private probe
forms a proper shell frame from the interpolated director and projected
top material-line tangent, stores the reference beam-relative frame, and
evaluates its relative rotation through the actual B3 retained pose. The
focused material-line file passes 7/7 checks, including Q4/S3 reference
orientation, deformed S3 director tilt, finite common rigid motion, Q4
director tilt, drilling insensitivity, and the tested shear slope. An
independent read-only mechanics review found no blocking value-level
objectivity or work-convention issue. This resolves only the frame-value
choice for the next bounded derivation: the orientation first and second
variations, couple work, physical wrench, nontrivial reference-frame
ordering, loaded torque/shear transfer, and growing-space stability remain
unverified. The next discriminating work is the orientation virtual-work
derivative through actual chart updates, followed by its second variation;
failure would revise the frame law before any multiplier selection.

**Reference orientation-work derivative (27 September):** The material-line
probe now differentiates the normalized E4 director and its projected
deformed top-line tangent, converts their frame variation to a spatial
angular variation, and subtracts it from the actual B3 retained-port
angular derivative in the reference beam frame. Q4 and mixed-S3 random
directional differences through `Context.advance` pass `2/2` at maximum
absolute error below `2e-8`; uniform shell drilling has zero derivative.
Independent read-only mechanics review found no blocking sign or
normalization defect in the reference Jacobian. It identified the missing
nonzero-multiplier dual wrench and nontrivial reference-frame checks.
This establishes only the reference first variation for the tested chart.
It does not establish finite-state Log derivatives, multiplier-dependent
curvature, physical couple work, or loaded torque transfer. The next
bounded discriminator is a nonzero-gap first variation and mixed second
variation under the actual finite-rotation updates; disagreement would
revise the chain rule or frame definition before forming a KKT tangent.

**Nonzero-gap orientation derivative (27 September):** A finite-state
`orientation_jacobian` now applies the SO(3) left-Log Jacobian inverse to
the current shell/beam spatial angular difference, including the stored
reference orientation. Q4 and mixed-S3 nonzero-gap directional checks
through actual left-multiplicative shell updates and native
`Context.advance` pass `2/2`, with maximum absolute error below `2e-8`.
The earlier reference and drilling checks also pass after specializing
this general derivative. A nonzero distributed multiplier gives nonzero
separate shell and beam couple work that cancels under one supported common
rigid twist. Independent read-only mechanics review found no blocking
left-Log sign/order or pullback defect. This tests finite-state first
variation and one dual-work identity, not all six wrench directions,
the mixed second variation, or loaded torque transfer. Next, a
nonzero-multiplier curvature check must distinguish a correct constraint
Hessian from a merely correct residual Jacobian before any exact-multiplier
production tangent is adopted.

**Chart-corrected curvature oracle (27 September):** One nonzero-multiplier
orientation work functional now has a bounded mixed directional check in
the actual base chart: the first derivative uses the finite-state analytic
Jacobian with the SO(3) exponential's left Jacobian to convert each base
direction into the current local update. The two mixed orders agree and
match the independent four-state scalar-work stencil within `2e-7`;
omitting the chart conversion disagrees by more than `1e-6`. Independent
read-only mechanics review found the base-chart correction and stencil
valid for this fixture. This is a numerical curvature oracle for one
direction pair, not an implemented general constraint Hessian, loaded
coupling tangent, physical wrench qualification, or G0B acceptance.

**Bounded saved-field discriminator (prospective, 27 September):** The
already-executed reverse-Fz C3D20R case has positive paired-parameter Q8
gaps, but those are not same-deformed-XY separation. On its saved factor-4
field, project an interior 9×9 Gauss grid of each of the 128 detached bar
faces into the matching deformed plate face; record successful projections,
unprojected points, minimum gap, and any negative witness. A negative
interior witness rejects this no-contact field as a physical comparator;
no witness retains it only as a candidate for a continuous deformed-face
certificate and idealization matching. The field is reverse-Fz, not the
unresolved torque/shear reference. This check uses saved artifacts and no
new external solve or resource authority.

**F03 continuous-law interpretation for review (27 September):** In the
current candidate, the shell top and native beam underside are distinct
kinematic traces that coincide spatially on the bonded reference patch;
the declared eccentricity separates shell midsurface and beam axis. At each longitudinal
material station, let `g(x,y)` be their relative position in the native
beam material frame and `I_y=<y²>_y`. The six *continuous* section channels
are `(<g_x>,<g_y>,<g_z>,<y g_z>/I_y,pitch(d_shell,R_beam),
-<y g_x>/I_y)`, before longitudinal multiplier projection. The pitch is the
beam-frame x–z projected E4 director angle at the strip centre; its work couples
to shell director bending and native beam section rotation. The first
transverse moments transfer local x/z couples through finite positional
arms. This is a reduced strip-pose connection: higher transverse slip
shapes, including the demonstrated positive-energy even mode, remain
admissible when all six channels vanish. A common longitudinal slope of
transverse displacement with unchanged directors has zero reference-linearized
gap and retains admissible shell shear. It must therefore be
offered, if eventually accepted, with explicit reduced-line semantics;
rigid/distributing footprints and a full surface bond are different laws.
The existing finite-chart, wrench and shear tests support this meaning,
but loaded physical transfer, independent reference agreement and
growing-space mixed stability still decide whether it is usable. This
interpretation selects neither the production law nor P0/P1/dual. Independent
read-only mechanics review confirmed the channel order, signs and moment
arms and prompted the three wording corrections above; it did not accept
the production connection.

**Next F02/F03 pitch-work discriminator (prospective):** Existing tests
establish the pure director-pitch row kinematically and the mixed six-channel
work, but do not isolate its supported shell energy. On the existing bounded
C1 Q4 shell/beam reference at 35 mm thickness, apply only the pitch-channel
unit couple through the exact reference row to the shell, fix the declared
left edge, and decompose the solved E4 work into physical and numerical
stiffness components. Verify the applied wrench and force/moment balance.
Dominant numerical work or a failed balance sends the pitch map back for
revision; dominant physical work supports retaining it as a candidate for
subsequent thickness, mixed-mesh and loaded-coupling checks. One supported
linear case does not qualify torque transfer, the line law or G0B.

**Pitch-work result (27 September):** The supported 35 mm Q4 C1 shell
under the isolated `−100 Nm` pitch-row action has zero applied force and
the declared `−100 Nm` moment about the reference origin. Free-row
equilibrium, complete force/moment balance and work identity pass. Total
load work (twice linear elastic strain energy) is `0.02008690486007 J`,
physical E4 work `0.02008690486060 J`,
and numerical-component work `−1.45e-13 J`; the pitch action has no shell
drilling column. The new physical-work and existing kinematic controls
pass `2/2`. Thus this isolated supported pitch transfer is not supplied
by drilling completion. It does not yet validate thickness/refinement,
mixed Q4/S3, a coupled native beam load or the production line law.
Independent mechanics review confirmed the applied couple, reaction sign,
wrench balance and work split without extending that scope.

**Next F03 loaded pitch discriminator (prospective):** The isolated shell
couple does not show whether the retained B3 and an exact weak line transmit
a terminal physical My load into that E4 pitch field. Extend only the
existing bounded x4/y4, B3-half12 sparse C1 fixture with an optional
`+100 Nm` terminal My load. For P0, P1 and dual P1, report tip ry,
shell/root My support shares, physical/numerical shell work, complete
interface wrench/work and scaled equilibrium. If all three transfer a
physical My share with balance and negligible numerical shell work, retain
the candidate and assess physical accuracy and growing-space behavior
separately. If any fails, distinguish trace/row, shell constitutive and
mixed-solve causes before changing the law. No multiplier is selected from
this one loaded case, and formal F03 authority is not consumed.

**Loaded My result (27 September):** The opt-in x4/y4, retained B3-half12
`+100 Nm` My solve completed for P0/P1/dual P1 with ranks `12/18/18` and
mechanics errors `5.86e-12/4.80e-12/3.78e-12`. Tip ry is
`13.079/13.109/13.277 µrad`. Shell support My is
`−4.173/−4.159/−4.111 Nm`; beam root My supplies the corresponding
`−95.827/−95.841/−95.889 Nm`. Physical shell work is
`0.00041075/0.00040544/0.00040130 J`, while numerical shell work is
`6.58e-7/6.50e-7/6.28e-7 J` (about `0.16%` of shell work). The loaded
and isolated-pitch focused tests pass `2/2`. The numerical contribution is
larger than the isolated pitch-only case and is not silently called zero;
the loaded response also includes all positional channels. The next
discriminator must apportion pitch versus positional-row transfer on the
same physical fixture and identify the numerical work's mode before this
case can support the physical-connection decision. This result neither
selects a multiplier nor qualifies F03/G0B.
Independent mechanics review confirmed signs and balance but emphasized
that this is combined-six-channel transfer: positional force rows can
also carry My through their arms. The new test guards balance and positive
physical work, not the measured work magnitude or numerical fraction.
Per-channel action/work recovery or a controlled pitch-row ablation is
required before any pitch-specific loaded claim.

**Next loaded-My allocation (prospective):** Keep the just-solved x4/y4
KKT states and all rows unchanged. Recover each of the six channel actions
as `−C_jᵀλ_j`, including native retained coordinates, and calculate its
shell/beam virtual work and physical resultant. Their sums must reproduce
the complete interface action, work and wrench. If the pitch-row shell
work is substantial, it establishes participation in this solved state,
not necessity or a causal ablation. If positional rows dominate, do not
use total shell My as evidence for the director-pitch channel. This
bounded decomposition does not rank line spaces or close the numerical-
work question.

**Loaded My channel allocation (27 September):** Exact `−C_jᵀλ_j`
aggregation over each longitudinal basis reproduces the total interface
action, shell/beam work and wrench; the focused test passes `1/1`.
P0 shell-side interface My has contributions `Fx −18.796`, `Fz +13.322`,
and projected-director `My +9.647 Nm`, summing to `+4.173 Nm`.
P1 and dual P1 have corresponding triples
`(−18.826,+13.321,+9.664)` and `(−18.892,+13.754,+9.249) Nm`.
P0 shell interface work is `0.00011743 J` from Fx,
`0.00017756 J` from Fz and `0.00011642 J` from My, summing to
`0.00041141 J`; pitch supplies about `28%` of that work, with similar
shares for P1/dual. Thus pitch participates materially in this solved
state, while positional channels supply most shell-side work and their
large My wrench contributions about the global origin partly cancel;
individual positional-channel moments change with the chosen origin when
that channel has net force. These signed channel work terms are not
independent E4 strain-energy partitions. The net `4.1 Nm` shell
support share cannot establish pitch necessity. A same-fixture pitch-row
ablation, with rank and physical-work controls, is the next bounded
causal discriminator; it is not a replacement production law or a
multiplier-selection test.
Independent mechanics review found no code or work-conjugacy blocker and
confirmed those interpretation limits. The existing default weighted-line
control passed `1/1` after the opt-in helper change.

**Pitch-row ablation protocol (before execution):** On exactly the same
x4/y4 shell, B3-half12 predecessor, supports and `+100 Nm` terminal My,
remove only channel 4 from every longitudinal basis of P0, P1 and dual
P1. Keep all other rows and scales. Compare rank, tip ry, shell/root
support shares, physical/numerical shell work, complete balance and the
omitted continuous pitch gap. A rank failure identifies a required
constraint direction in this discretization; a supported response shift
identifies pitch causality for this load; near parity would show that the
observed pitch-channel work did not make it necessary for this specific
output. None of these outcomes selects a production five-channel law or
changes the required six-channel G0 criteria.

**Pitch-row ablation result (27 September):** With only every basis's
channel-4 row removed, the same supported KKT retains full row ranks
`10/15/15` and mechanics errors below `7.2e-12`. Relative to the full
P0/P1/dual laws, terminal My tip ry rises by about
`2.28%/1.56%/1.22%`; the omitted mean continuous pitch gaps are
`−1.630/−1.481/−1.386 µrad`. Shell support My remains near `−4.1 Nm`
and physical shell work remains positive, with numerical shell work
still around `6.3–6.5e-7 J`. Thus the pitch row measurably stiffens this
particular My response but is not required for row rank or for the main
shell-support resultant in this fixture. The six-channel law's physical
fidelity still needs a matched connection reference and growing-space
assessment. The focused ablation test passes `1/1`; this diagnostic does
not propose a five-channel production law or select a multiplier.
The reported omitted gap is an unweighted continuous mean, not a
per-basis gap or accepted nonlinear result. Independent mechanics review
found no row-deletion or balance defect and confirmed that the inference
is limited to this fixture; persistence of shell load transfer does not
make the ablated law physically adequate.

**Independent B2 F10/F11 S3 discriminator, before implementation (27
September):** The private B2 reference point proof uses a finite least-squares
rigid pose from four physical Q4 vertex translations; it has no S3 point
proof. A three-vertex noncollinear support may retain six physical pose rows,
or it may lose a moment channel or produce an inconsistent shell action.
Generalize only the private support size, preserving the Q4 law and no-drill
definition. On one actual elastic S3-V2D stiffness, compare objective
reference derivatives, force/moment/virtual-work balance, sparse KKT and an
independent reduced solution under fixed supports and a nonzero eccentric
load. Negative and mutation checks must remain. A pass gives bounded S3
point feasibility only; it does not select the GE line law, qualify a public
B2 route, or close F10/F11/G0B. A failure revises the support law before
topology expansion.

**Outcome (27 September):** The private point compiler now admits an S3
three-vertex physical-translation support with its own development law ID;
the historical Q4 ID and port remain unchanged. On an actual S3 stiffness,
the reference fit has six independent pose rows, the finite-rotation joint
derivative and multiplier work agree, and force/moment balances close. A
supported sparse KKT solution agrees with an independent reduced solution
and reactions; malformed support and caller mutation checks pass. Focused
Q4/S3 tests: `7/7`. Independent mechanics review found no blocking defect.
The initial KKT fixture fixed shell rotational DOFs; the following
discriminator tests whether that restriction hid a failure. This is not a
production attachment. F10/F11 and G0B remain open.

**Next S3 support discriminator (prospective):** The supported KKT fixes all
shell rotations. Determine whether this only removes expected isolated-
element modes or hides an attachment inconsistency: retain the same element,
beam, load, rows and supports, but free S3 bending rotations at the two
non-root vertices while restraining only drilling there. Check finite rank,
equilibrium, interface work, and independent reduced-solve parity. If it
passes, strengthen the private S3 fixture; if singular or inconsistent,
identify the physical/auxiliary mode before changing the attachment law.
Neither outcome qualifies a production point connection.

**S3 bending-active result (27 September):** With only non-root drilling
rotations restrained, the same S3/B2 KKT has full rank `22/22` and its
constrained primal reduction full rank `10/10`. Bending rotations respond
under the load. Sparse versus independent reduced solution differs by
`6.01e-16`, equilibrium by `1.27e-16`, and work by `6.94e-18` on the
bounded fixture. The focused Q4/S3 tests still pass `7/7`. This removes the
all-rotations-fixed limitation for this supported element, but does not
qualify the continuous attachment, other support layouts or the public
B2 route. F10/F11 and G0B remain open.

**Next S3 identity discriminator (prospective):** The finite three-vertex
point support uses a winding-dependent material frame. Reorder the same
physical triangle and its displacement columns through all six vertex
permutations, keeping the member and offset fixed. If the six-row nullspace
changes, the private law depends on arbitrary node order and needs a frame
contract correction. If it is invariant, retain the winding-specific
display components but establish physical constraint-space invariance for
this bounded point; this is not a shell element orientation or public
renumbering qualification.

**S3 winding result (27 September):** After mapping the three shell column
blocks back to physical vertex IDs, all six permutations retain rank six
and the same constraint nullspace. The maximum normalized action on the
original nullspace is `2.01e-16`. The Q4/S3 focused set passes `8/8`.
Material-frame component labels do change with winding, so a public model
still needs its explicit frame/orientation contract. This bounded result
does not qualify shell-element reversal or the B2 production route.

**Next contact-method discriminator, before execution (27 September):**
The saved C1 quadratic terminal-bond torque deck has 128 plate and 128 bar
unbonded contact faces, but its finite penalty formulation activates only
one face's eight contact entries while a same-XY audit finds sampled overlap
on five faces. The competing explanations are finite/underresolved penalty
contact versus an unsuitable shared-seam contact geometry. On the identical
source deck, change only the contact interaction from finite linear penalty
surface-to-surface to hard dual-multiplier mortar and retain the existing
load, supports, section, face inventory, single thread, 120-second and 2-GiB
limits. Check exact deck transformation, solver completion, warnings, contact
activity, sampled same-XY face gaps and balance. If mortar executes without
sampled overlap and balances, advance to matched shear and contact/mesh
convergence before native scoring. If it fails or overlaps, preserve the
failure and revise the reference contact/seam geometry; do not infer native
law failure or run a stiffness/mesh sweep. CalculiX documents mortar as
weak exact contact and warns against additional MPCs at slave edge nodes;
this motivates the method screen but does not predict its result.

**Matched hard-mortar outcome:** The source and solver hashes matched the
saved penalty case; the contact-only transformation was reversible, and the
same 128+128 face inventory, geometry, supports and torque load were retained.
Pinned CalculiX 2.23 exited `201` during its first stiffness calculation
after `1.737 s` (peak solver RSS `251 MB`), without a complete field or
contact result. Its log also warns that no elastic constants were assigned
to the `HARDUNBONDED` interaction name. The official CalculiX 2.22 manual,
Sections 7.129–7.130, explicitly permits omitting `*SURFACE BEHAVIOR` for
true hard mortar ([manual](https://www.dhondt.de/ccx_2.22.pdf)), so that
warning alone does not show an invalid contact declaration. The present
evidence still does not prove that seam-edge contact
topology caused the exit. Preserve the warning and raw failure rather than
relabeling the exit as convergence.
This method switch cannot qualify the reference. The next bounded task is a
seam-edge geometry/contact audit that can separate a shared-edge limitation
from another solver failure; only then choose a revised contact geometry or
solver route. The earlier penalty overlap and split-solid no-contact overlap
remain in force. No native-law
or multiplier-space decision follows, and no G0 status changes.

**Next seam discriminator, before execution:** On the same failed C1
hard-mortar deck, remove only the eight plate and eight bar contact faces
in the final x=`0.8625–0.9 m` column adjoining the shared terminal bond;
retain all elements, loads, supports, interaction and 120 s/2 GiB/one-thread
limits. Establish the element-face coordinate map before editing the two
contact sets. If the reduced-contact solve completes while the full-contact
solve fails, the shared-edge neighborhood is implicated in this solver
route, but the resulting untreated column makes it physically inadmissible
for native accuracy. If it still fails, do not blame the seam; examine the
solver method or reference representation. Neither outcome selects a native
connection or licenses a wider contact sweep.

**Seam discriminator outcome:** The C3D20R element-face map uniquely matched
all 128 paired faces. Only the last eight faces on each contact side, in
x=`0.8625–0.9 m`, were removed; all 120 remaining faces per side and all
other deck content were retained. The pinned one-thread CalculiX run reached
the registered 2-GiB solver-memory cap after `20.763 s` (observed peak
`2,158,915,584` bytes) and was killed before a completed increment or field.
The untrimmed run exited `201` much earlier, but the trimmed resource failure
does not prove that the shared seam caused that exit or establish contact
admissibility. Both raw failures are preserved. Stop this factor-4 hard-mortar
route under the registered resources; no larger cap, mesh sweep, native
accuracy score or formulation verdict follows. Reuse the already executed
fully bonded F5 and pre-opened C1 evidence at their valid levels while
designing a physically and computationally admissible reference path. G0B
remains open and G1 barred.

**Next split-law experiment, pre-execution (27 September):** The competing
explanations are insufficient longitudinal enforcement of the declared
six-channel work law versus a different continuous trace/domain response.
On the *same* C1 detached solid source, construct exact Q8-normalized six
physical rows on each of two half-patch intervals, then reconstruct the
linear constrained response from 12 serial unit-action compliance solves.
The preflight has rank `12/12`, maximum common-rigid gap `5.22e-15`, and
mean recomposition defect `4.22e-15`. A plate-top longitudinal Fz field
with zero global mean produces split gaps `-0.025 m` and `+0.025 m`.
Focused tests pass `2/2`; independent read-only mechanics review found no
blocking issue. Its two provenance/failure-record hardening suggestions
(runner SHA and missing convergence-log handling) are implemented.
Each action solve retains the 120 s/2 GiB cap and one-thread setting.
Compare the 12-row supported action with the saved global-six and native
P0-two-interval actions only after compliance reciprocity, rank, work and
physical balance checks. No formal F03 authority is consumed by this
development diagnostic.

**Exact split-law result and decision (27 September):** Twelve serial
CalculiX unit-action solves completed, each in `17.17–20.19 s` and at most
`1,289,195,520` bytes RSS, within the unchanged `120 s/2 GiB` per-run
limits. The 12×12 scaled work compliance has relative skew `2.09e-7`,
smallest symmetric eigenvalue `9.615e-5 J`, and condition `3.08e4`.
Exact KKT reconstruction closes both gap norms below `2e-18`; joint side
work cancels within numerical precision and physical joint wrench is near
zero. The supported external/support imbalance is at most `8.10e-4 N`
against the 1000 N opening scale. Independent review found no scoped
correctness blocker. Authoritative `reconstruction_v2.json` SHA256 is
`404801872bb7558c7ae5d315af4e4b0028d3386c6afc04df4286984ebafe5267`;
v1 is preserved (SHA256
`d0779f3901f09b7586f6c032a6447097142c80b92cfbd9c9ef6dbed58eccc093`).
The v2 change checks the actual runner hash against all 12 records.

On the *same solid*, load work moves from `0.0703462` to `0.0694925 J`
for opening and from `0.00508602` to `0.00500805 J` for torque. The
native P0 x4/m2 values are `0.0693193` and `0.00477082 J`, respectively;
the remaining cross-model differences mix continuum and E4/B3 mechanics.
On the *same E4 shell*, global-six → split-twelve → native P0 action work
is `0.012321 → 0.012393 → 0.013263 J` (opening) and
`0.00181094 → 0.00181377 → 0.00196900 J` (torque). On the *same retained
B3 beam*, it is `0.107188 → 0.107841 → 0.109441 J` (opening) and
`0.00176505 → 0.00177222 → 0.00206741 J` (torque). Physical wrench,
three/five-point open-half-cell quadrature and reciprocal cross-work checks
pass; independent mechanics review found no blocker. Authoritative replay
hashes are `same_shell_v2.json`:
`d18788b95dc9bd26da72f9a44f3337ccf62700b3dde0ae19d935b5d9fa72ec86`
and `same_beam_v2.json`:
`61c85fcfb74621c04fe6decabc71ad912680c684a12dec1eab69f37b7a6dfd1d`.
Earlier v1 replays remain preserved; v2 removes mixed-unit covector-norm
quotients from the reported physical comparison.

The 128 raw files total `96,526,501` bytes and remain in the active ignored
evidence directory. Their versioned hash/size manifest is
`raw_manifest_v1.json`, SHA256
`3286b7aa8e768a1b7c7c233c86871028b609aadcb12bcfd99e98457068129d11`.
Nineteen JSON evidence records were copied byte-for-byte into tracked
`docs/agent_plans/B3_GE_E4_PL_F03_SPLIT_SIX_CHANNEL_DEV_20260927_V1/`;
all 19 copy hashes match. Keep the active worktree and raw evidence until a
durable programme evidence transfer is verified. F03/G0B remain open and
G1 remains barred.

**Local solid trace-residual diagnostic (27 September):** The same eight
source-bound solid FRD fields and `reconstruction_v5.json` were reused with
no new external solve. The deck- and field-bound result is
`trace_residual_v3.json` (SHA256
`27ee50adc2270c1a6187e8f656171503ff0712a114eb3aca4aa3546950e06ef4`);
v2 is preserved (SHA256
`3edb8bdcdbbf33bed24ebf00b9501d80dae99742daea2b62d8cff3f5738aa13f`)
as is v1 (SHA256
`2dec54cb392a6f4220434c7c02a780b3f11765b6b23b671b081feba26e62a230`).
Both source-deck, all six unit-action, and both loaded-field hashes are
checked before use. Independent read-only review of v2 and its mechanics
found no blocking finding; v3 adds the requested deck-identity check and
reproduces the same results.
At 121 plate sites, fitting local through-thickness director motion leaves
`6.68e-6 J` torque work (0.36% of that side) and `-1.31e-7 J` opening
work (~0.001%). At nine bar stations, fitting local rigid cross-section
motion leaves `5.91e-5 J` torque work (3.16% of |bar-side work|) and
`5.78e-4 J` opening work (4.59%). The exact solid six-channel gap is near
zero; the local-fit gaps are nonzero. The action/gap work identity closes
within `6e-17 J`; two synthetic representability tests pass. These fits
are pointwise and not a projection into globally compatible E4/B3 trial
spaces. Their work residuals cannot by themselves explain the prior
same-domain native-action differences or choose a multiplier space.

**Compatible Q4 plate-patch fit (27 September):** Reusing the same saved
solid fields and physical joint action, an equal-Q8-node least-squares fit
to one C0 x4/y4 Q4 patch (25 shared nodes, 125 translations/director
coordinates) has full rank and recovers an exactly representable synthetic
field. A deliberate single-face displacement remains detectable. The
reviewed final record is `global_plate_trace_v2.json` (SHA256
`f747f7e34ec1e6d5f37b9cb22705dc65c9b57beda10f15823853e4eae69a5e01`);
v1 remains preserved (SHA256
`c9ac3441936a1ca3fec78e0c2d4a484446a5e01ccbb5184b4db09d0006b8528b`).
The signed work outside this particular fit is `1.167e-5 J` in torque
(0.624% of the absolute plate-side action work) and `2.276e-5 J` in
opening (0.181%). The face-node RMS differences are `6.09e-9 m` and
`8.19e-9 m`; fit condition is about `114`. Four focused trace tests pass.
Independent read-only mechanics review found no scoped blocker. Equal-node
least squares is not a physical L2 projection; these ratios are not energy
fractions, error bounds, or a coupled beam/connection-law attribution.
F03/G0B remain open.

**Compatible retained B3 open-half-cell fit (27 September):** The same
source-bound solid state was projected onto 15 active, full-rank native
retained coordinates through the actual station tangent on the *open*
half-cells. Q8 face displacement and the physical solid action density
were integrated at 576 two-face quadrature points; action work recovers
the saved bar-side value. The final record is `global_beam_trace_v2.json`
(SHA256 `a375e030a1ce1acc0794f69107fb78b4a852a447fe5a89651af5f4952bf1a17d`);
v1 remains preserved (SHA256
`a16f2979984b8fa77e9efe8a35b95b398558aa3e8141b309f6ee822cb0044d54`).
The signed action pairing outside this fit is `4.930e-5 J` in torque
(2.636% relative to |bar-side work|) and `1.848e-6 J` in opening
(0.0147%). Face RMS differences remain `6.59e-8 m` and `9.25e-8 m`:
the small opening work pairing does not imply small warping. The fit
condition is about `30.8`. Four focused tests pass: common translation,
common rotation, a nonrepresentable face warp, and independent action
virtual-work parity with the retained-beam port integration. Independent
read-only mechanics review found no blocking issue in the base source;
the subsequent action-parity check strengthens it. This physical L2 face
fit is not a coupled equilibrium solution, accuracy bound, or F03
acceptance. G0B remains open, G1 barred.

**Matched linear external reference and fixed-domain action replays (27
September):** The source-bound C1 detached F4 C3D20R model has separate
plate/bar nodes and unchanged geometry, elements, elastic material, supports
and static controls between the saved `tip_mx` and `tip_fz` load cases. A
new exact-Q8 area-mean six-channel map includes top-face position, transverse
first moments and a plate/bar through-thickness pitch difference. Its six
rows are independent and common-rigid gaps are at most `5.14e-15`;
independent affine force/moment/pitch and action-card checks pass `2/2`.
The complete focused six-channel/finite-connection regression subsequently
passed `33/33` with JIT disabled and one BLAS thread (`440.65 s`); this
expensive clean run need not be repeated without changed mechanics inputs.
Six serial CalculiX action solves took `17.36–17.52 s` each and peaked at
`1.248–1.249 GB` RSS, under the unchanged per-run `120 s/2 GiB` limits.
The exact linear Schur reconstruction (authoritative `reconstruction_v5.json`)
has work-compliance relative skew `3.79e-8`, smallest symmetric eigenvalue
`0.002056 J`, condition about `719`, both constrained gap norms below
`1e-18`, and source-bound generated-deck/solver identities. The supported
external-force balance norms are `7.91e-6` in the torque case and
`3.18e-4` in opening against 100 Nm/1000 N applied scales; the assembled
joint's global wrench is near zero. The earlier v1–v4 reconstructions remain
preserved; v2 corrected the physical KKT sign, v4 bound common stiffness,
and v5 completed generated-deck/solver provenance. Independent read-only
mechanics review found no remaining scoped correctness finding. This exact
linear constraint avoids the historical wide-MPC F5 memory failure; it
does not execute or validate nonlinear/contact behavior.

Against the saved native x4/m2 loaded cases, native external load work is
`1.46–1.69%` lower for opening and `4.40–6.20%` lower for torque than the
solid six-channel reconstruction. At x4/m4 the torque difference grows to
`5.63–9.23%`; this is not a convergence claim. The physical *full plate*
wrench and load-conjugate work are the comparable quantities, not the raw
pitch dual. The common E4 shell replay (`same_shell_v2.json`) validates
native shell wrench, interface work, physical shell work and reciprocal
cross-work (maximum defect `4.44e-15 J`): native-action shell work exceeds
solid-action shell work by `7.10–7.65%` in opening and `8.73–9.26%` in
torque. Independent review found no scoped issue. The common retained B3
replay (`same_beam_v2.json`) integrates the solid surface density on open
half-cells, avoiding ambiguous nodal assignment at sided ports. Third- and
fifth-order quadrature agree to `1.03e-15` relative; physical global wrench
matches both saved solid and native actions. Native-action beam work exceeds
solid-action beam work by `2.10–2.31%` in opening and `11.77–17.13%` in
torque. Independent read-only review found no blocking mechanics or source
identity issue in either fixed-domain replay. These action differences
persist, but one solid mesh,
solid warping, E4 director assumptions and B3 section idealization prevent
causal assignment to the connection law or multiplier space. The historical
shared-node F5 bond remains distinct. F03/G0B stay open; G1 remains barred.

Authoritative SHA256: `reconstruction_v5.json`
`291ada8e4ea51e80cdcce7c06f946484652ca0fc96ab35cd32b5da11a604fa9c`,
`same_shell_v2.json`
`50972551755ac95144efb5eb8db3304e3e6025b9d8434ddff689bf50a311d0dd`,
`same_beam_v2.json`
`4bc19a16444c3a17accd7739bfa4619bd8cfe7f2fa086e302dbbe7c7baee2557`.
All three are under
`.qualification/b3-ge-e4-pl/f03-c1-six-channel-compliance-dev-20260927-v1/`;
the six raw channel subdirectories remain immutable. All 15 versioned JSON
records, including earlier corrected reconstructions, are copied byte-for-byte
into tracked `docs/agent_plans/B3_GE_E4_PL_F03_SIX_CHANNEL_REFERENCE_DEV_20260927_V1/`
(`15/15` SHA256 copy matches). The 48 MB raw solver decks, fields and logs
remain in the ignored local evidence directory; keep this active worktree
until they are transferred to durable programme evidence storage.

**Next bounded matched-sided reference (prospective, 27 September):**
The saved C1 detached C3D20R solid has separate plate-top and bar-bottom
nodes, unlike the historical shared-node bond. A six-channel *linear solid*
work map uses face-mean positional gaps, transverse first moments, and a
through-thickness pitch difference over the same terminal 0.1 m patch.
The competing explanations are a physically different native trace law,
insufficient discrete line enforcement, and the earlier shared-node
reference's different bond. First require exact Q8 quadrature, six-row rank,
common rigid-motion nullity, signed affine-field gaps and transpose work.
Then, within the retained 120 s/2 GiB per-solve caps, apply each row as an
ordinary nodal action to the *detached* external solid. Reconstruct the
linear six-constraint response from its 6x6 compliance only if independent
load solves, reciprocity, positive constrained compliance and force/work
balance pass. This avoids the existing wide-MPC memory failure without
weakening the exact linear constraint. Compare the reconstructed supported
torque/shear outputs to the native six-channel case only after confirming
geometry, loads, supports and connection normalization. A mismatch directs
trace-law revision; agreement permits the registered growing-space study.
No result here selects P0/P1/dual or closes F03/G0B.

**Next bounded sparse mixed diagnostic (prospective, 27 September):** The
co-refined x16/y4 P0-eight case has full row rank but exceeds the existing
1900-row *dense* mixed-metric cap. The uncertainty is whether its actual
native retained indefinite KKT develops a weak mode despite the row rank,
or whether the observed loaded transfer difference is primarily physical
resolution/law response. Assemble the same diagnostic primal/dual metric
and unchanged native tangent sparsely; use a diagonal congruence and
near-zero generalized eigenpairs, keeping the 120 s and 2 GiB limits.
First reproduce the saved x8/y4 P0-four dense minimum to its numerical
accuracy. If that cross-check fails, stop and repair the sparse method.
If it passes, evaluate x16/y4 P0-eight, report equation/constraint/work
residuals and physical/chart near-mode shares, then interpret jointly with
the already saved x16 loaded transfer. A small or nonconverged mode calls
for norm/interface-resolution diagnosis; a comparable mode permits the
registered ratio and locking checks. Neither outcome alone selects P0 or
closes F03. No larger dense assembly or changed resource authority follows.

**Sparse mixed outcome and next discriminator:** The source-bound x8/y4
P0-four sparse generalized minimum is `0.00187655527545041`, agreeing
with the saved dense SVD to about `5e-14` relative. The x16/y4 P0-eight
minimum is `0.00022722462502004843`, with relative eigen-equation
residual `3.3e-13`, full `48/48` rows, `1980` sparse mixed variables,
`42,301` nonzeros, `64.45 s`, and `349 MB` peak. Both are under the
unchanged limits. The x16 weakest mode has `0.9999764` of its diagnostic
norm in the auxiliary shell drilling chart, only `2.36e-5` in physical
shell work, and negligible line-dual/beam shares. The numerical decrease
therefore does not by itself identify interface instability. The first two
x8 attempts reached eigensolution but failed in result bookkeeping
(`len(sparse_matrix)` and drilling-index interpretation); the corrected
run is the saved result. The next bounded check asks whether drilling is
an uncoupled gauge for this reference problem: measure the top-face row
columns on shell drilling DOFs and the actual E4 tangent cross-block in
the same work scales. If both vanish to numerical precision, a physical
quotient can remove the irrelevant chart spectrum. If the tangent couples
them, derive an exact chart elimination or an appropriate physical norm
before interpreting another mixed minimum. Do not tune drilling stiffness
or classify this spectrum as a formulation failure. Raw x8/x16 results:
`B3_GE_E4_PL_F03_TOP_FACE_SPARSE_MIXED_X8_20260927.json` and
`B3_GE_E4_PL_F03_TOP_FACE_SPARSE_MIXED_X16_20260927.json`.

**Drilling-coupling result and exact-elimination decision:** On the
unchanged x16/y4 P0-eight fixture, the reference top-face rows have
exactly zero shell-drilling columns. The *actual* E4 tangent does not
decouple: its diagonally work-scaled physical↔drill block has Frobenius
norm `0.06952` of the scaled full shell tangent and `0.10816` relative
to the geometric mean of its diagonal-block norms. The bounded check
used `66.09 s` and stayed inside the 120 s/2 GiB limits. Raw result:
`B3_GE_E4_PL_F03_TOP_FACE_DRILL_COUPLING_X16_20260927.json`.
The next physical mixed-mode check must therefore retain this coupling.
If the drilling block is nonsingular, eliminate only those shell chart
coordinates by an exact Schur complement of the same tangent, retain all
native beam internal coordinates and the exact weak rows, and compare
the reduced equilibrium/operator with the full system on the bounded
fixture. Then inspect its physically normed near mode and work. If the
drilling block is singular or elimination disagrees, stop and derive a
gauge-compatible norm or alternative exact projection; do not merely
delete drilling rows or tune the stabilization. This is diagnostic
operator analysis, not production static condensation or F03 acceptance.

**Exact chart-elimination result and next decision:** The actual E4
drilling block is positive definite on the supported x8/x16 fixtures;
its exact static Schur lift solves the block to about `4.3e-16` relative,
preserves symmetry, and reconstructs the full physical response within
`1.6e-10` (x8) and `8.8e-14` (x16) relative. The condensed shell tangent
differs from simply deleting drill rows by `3.39%/3.51%` in the recorded
Frobenius measure. All B3 retained variables and original weak rows stay
in the mixed operator. In the *restricted non-drill auxiliary norm*, the
first mixed magnitude is `0.0152021` on x8/P0-four and `0.00713953` on
x16/P0-eight. The x16 mode has `99.2949%` of that norm in the line dual
and `0.7034%` in physical shell work; it is an interface warning in this
chosen norm, not proof of physical instability. These runs used
`33.53/69.38 s`, `280/391 MB`, and `1230/1694` mixed rows. Source-bound
results: `B3_GE_E4_PL_F03_TOP_FACE_DRILL_SCHUR_X8_20260927.json` and
`...X16_20260927.json`. Independent review found no elimination or work
defect and emphasized that the restricted norm is **not** the full metric
pulled through the Schur lift. Next hold the x16 primal/B3 model fixed,
compare P0-four with P0-eight under the same exact Schur tangent, and
report sensitivity to the pulled-back norm as well as the restricted
physical norm. Interpret both with the existing loaded physical transfer;
neither quotient nor F5 proximity alone selects a multiplier space.

**Fixed-primal space/norm result and next discriminator:** A single x16/y4
Q4/B3-12 assembly reused the exact Schur tangent for P0-four/eight and
both declared norms. In the restricted non-drill physical norm, P0-four
has `β=0.0151963` with `98.40%` of the weakest mode in beam kinematics;
P0-eight has `β=0.00713953` with `99.2949%` in the line dual. In the
full metric pulled through the exact chart lift, both minima are
`≈0.00040945` and `99.986%` chart-induced, so the full scalar minimum
masks the interface-mode change. All four eigen residuals are below
`2.1e-11`, both row spaces have full scaled rank, and the run used
`65.88 s` and `466 MB`, within the unchanged limits. Raw result:
`B3_GE_E4_PL_F03_TOP_FACE_X16_FIXED_PRIMAL_SPACES_20260927.json`.
This separates row-growth from shell refinement on one primal, but the
restricted norm is still diagnostic. Combined with saved loaded F5 common
actions (m8 worsens B3-12 but improves B3-24), the next bounded question
is whether more native beam trace resolution stabilizes the new line mode.
Hold the x16 shell, supports, loads, exact work law and P0-four/eight
spaces fixed; change only B3 half-cells 12→24. Reuse the same shell/Schur
preparation, record physical-mode and pulled-norm sensitivity plus the
already saved loaded work. If the line mode recovers, formulate a beam-
to-interface resolution admission rule before ratios. If it does not,
revisit the P0 space/dual norm or law rather than automatically refining.
This is not a multiplier selection or F03 acceptance.

**Fixed-shell beam-resolution result:** The parameterized runner changes
only the native B3 half-cell count `12→24` on the same x16/y4 E4 shell,
supports, section, exact Schur operator and P0-four/eight work spaces.
The restricted physical-norm minima change only `0.0151963→0.0152115`
(P0-four, `+0.10%`) and `0.00713953→0.00714263` (P0-eight, `+0.043%`).
The P0-eight weakest mode remains `99.294%` line-dual; pulled-full
chart-dominated minima remain `≈0.00040945`. Both spaces retain full rank;
eigen residuals are at most `1.6e-11`. The one-preparation run took
`68.77 s`, peaked at `472 MB`, and formed `1886/1910` *sparse* mixed
rows while dense shell/Schur blocks remained under 1900 rows. Raw result:
`B3_GE_E4_PL_F03_TOP_FACE_X16_B24_FIXED_PRIMAL_SPACES_20260927.json`.
Independent review found no source or work defect. B3-12 trace resolution
is not the primary source of this chosen-norm weak P0-eight mode, even
though the saved B3-24 loaded F5 two-hat action changes appreciably.
The next bounded discriminator is an independently derived,
dimensionally consistent physical dual norm for the actual finite-width
traction generated by raw force/first-moment multipliers. Compare P0-four
and eight on the *same* x16/B3-24 Schur tangent under that norm and the
inherited H^(-1/2) diagnostic, reporting physical action and virtual work.
If weakness is norm-dependent, revise the norm/scales before stability
claims; if it persists, examine interface-space resolution/locking. Do
not tune a norm merely to raise the minimum or repeat beam refinement.

**Finite-width traction-norm sensitivity result:** An independently derived
L2 norm of the actual raw P0 force/first-moment traction, with one fixed
dimensional multiplier scale `W²/(E*t)`, was applied to the unchanged
x16/y4, B3-24 exact-Schur mixed operator. Its analytic finite-width Gram
matches independent two-point quadrature to `5.4e-18` relative; the raw
and centered work rows agree to `3.0e-17`. For P0-four/eight, the inherited
restricted-norm minima are `0.0152115/0.00714263`, whereas this traction
L2 sensitivity gives `0.00276896/0.0000357945`. The eight-interval mode
has `99.9964%` of its L2 diagnostic norm in the line dual; its relative
eigen-equation residual is `4.8e-11`. The one-preparation run took
`75.16 s`, peaked at `488 MB`, and stayed within existing limits. Raw
source-bound result:
`B3_GE_E4_PL_F03_TOP_FACE_X16_B24_TRACTION_NORM_20260927.json`.
The scalar minimum is highly norm-dependent; L2 traction is neither the
canonical trace-dual H^(-1/2) norm nor actual E4 compliance. The common
line-dominated eight-interval mode warrants a physical work/locking and
growing-space assessment, but does not prove instability or select P0.
Next derive an appropriate trace-dual norm from the declared continuous
work law, with its scaling fixed before comparing spaces. If that norm
retains a weak line mode, test its supported physical deformation and
transfer on the registered ratios; if it does not, revise the prior
diagnostic interpretation. Do not tune the norm to increase the minimum.
Formal F03 authority remains unconsumed; G0B open and G1 barred.

**Next bounded mode-shape check (prospective):** The question is whether
the 77-fold P0-four/eight drop in the finite-width L2 diagnostic reflects
an oscillatory traction pattern poorly represented by the current trace,
or mainly conversion between this norm and the inherited diagnostic.
Reuse the unchanged x16/B3-24 assembly and both spaces. For each weak
mode, inspect raw piecewise traction coefficients and cross-evaluate its
dual component under both norms. Compare a fixed smooth physical traction
represented on each partition as a normalization control, and retain the
actual work and eigen residuals. If the weak eight-interval mode develops
short-scale oscillation absent from the smooth control, inspect supported
physical deformation/work and interface resolution before further ratios;
if the apparent difference is chiefly norm conversion, derive the
continuous trace-dual norm before classifying the mode. This diagnostic
does not consume F03 authority or select a multiplier space. The first
L2 result omitted three imported helper hashes; preserve it and add the
complete source identity to the next version.

**Mode-shape outcome and decision:** The source-complete V2 run used the
same x16/B3-24 KKT operator and reproduced every prior minimum within
roundoff (`75.72 s`, `488 MB`). Its fixed smooth axial traction has
identical dual norm `1.36054e-12 J` on P0-four/eight under both metrics,
so the comparison is not a blanket partition normalization shift. The
P0-eight restricted and L2 near modes have essentially the same smooth,
long-wavelength raw pattern: transverse force changes sign through the
centre while the pitch-moment density forms a symmetric arch. Neither
shows interval-to-interval alternation. For these two eight-interval
modes, the L2/inherited dual norm-squared ratios are `200.57/201.35`;
their minima differ by almost the same factor (`0.00714263` versus
`0.0000357945`). The P0-four inherited minimum is instead beam-dominated,
while its L2 minimum switches to a smooth line-dominated mode. Thus the
77-fold four→eight L2 minimum decrease does not expose the proposed
oscillatory high-frequency traction mode. It is primarily a change in
which smooth mode is smallest plus the norm assigned to the pitch-moment
traction. The exact continuous trace-dual norm and supported physical
work/locking remain unresolved; this observation cannot establish a
uniform stability constant or select P0. Stop repeated spectral quotient
comparisons. Next derive the norm for the declared trace/work spaces and
compare supported transfer on registered ratios with the physically
matched sided reference. The raw result is
`B3_GE_E4_PL_F03_TOP_FACE_X16_B24_TRACTION_MODE_V2_20260927.json`;
it hashes all eight directly used source files. The V1 result remains
preserved with its narrower provenance. G0B remains open, G1 barred,
formal F03 authority unconsumed.

**Next B2 F09 bounded physical-range discriminator (prospective):** The
passing heterogeneous elbow and the retained weak artificial generalized
graph do not locate the representability boundary for a coherent physical
section family. Keep the rooted 2 m + 1.5 m elbow, the fixed 80×3 mm first
member, the rotated 12×3 mm second member and its reversal control. Scale
only the second section homothetically by `λ=1,2^-5,2^-10` and the complete
tip wrench by `λ^4`; stay inside the existing linear-eligibility and
120 s/2 GiB/one-thread bounds. For each of six cases compare the exact
physical cut-work oracle, a high-precision solve of the rounded matrix,
ordinary stored-coordinate residual, sparse factorization, and a residual
formed from factored `(D,z)` without first rounding `D*z`. This separates
local/assembly, factorization and physical-state storage errors. A failure
is retained and routed to the responsible layer; six passes give sampled
physical-range evidence only, not continuous admission or F09/G0B
acceptance. Keep the existing physical-balance and oracle criteria.

**B2 physical homothety outcome:** The six predeclared cases (three
`λ` values and the second-member reversal) completed as a private
development diagnostic in `1.480 s`, peak `91.7 MB`, with one numerical
thread. An independent source/result audit found all nine recorded source
hashes current and all six cases passed. The maximum sparse ordinary
force/moment balance ratios are `1.144e-10/3.134e-13` against the existing
`1e-9` limit; the largest sparse physical-work relative error is
`1.301e-11`. At `λ=2^-10`, the ordinary stored state and retained `(D,z)`
factored state both satisfy the physical balance, as does the high-
precision rounded-matrix reference; no correction was needed and each
batch had one factorization. Thus the artificial generalized `2^-40`
failure does not transfer merely from its bending-stiffness exponent to
this coherent, load-scaled physical rectangle family. It establishes no
continuous admission range or full F09/G0B acceptance. Retain the weak
generalized-graph failure as a separate negative.

The immutable raw result is
`B3_GE_E4_PL_G0_F09_PHYSICAL_HOMOTHETY_STATE_DEV_V1.json` from source
HEAD `b0b065ae`; the successful command was
`C:\Python\Python314\python.exe -B -u scripts/b2_f09_physical_homothety_state_dev.py`
in this worktree, exit `0`. Two earlier launch attempts produced no raw
result (a sandbox output-write rejection after computation and an approved
shell selecting Python without NumPy); they are execution failures, not
numerical failures. Next F09 work must define a reviewed prospective
physical-section envelope and a fail-closed graph/state rule; do not hunt
an arbitrary smaller exponent or infer qualification from these samples.

**Continuous-law gauge discriminator (prospective, 27 September):** The
top-face candidate's raw force/first-moment work is an affine surface
traction `t=[F+M×(x−.95,y,0)]/W`. The suspected distinction is whether
the smooth eight-interval `Fz/My` mode reflects an exact continuous
coefficient gauge, rather than only a choice of norm or finite-grid
resolution. Derive the coefficient-to-traction map explicitly; test the
field `Fz=(x−.95)μ(x), My=μ(x)` against independent polynomial virtual
gaps, and test its piecewise-constant midpoint representation at 2/4/8/16
intervals against an analytic residual. If the continuous action is zero
for nonzero coefficients, stop treating six raw top-face positional
resultants as six independent local line-pose constraints. Keep the
finite-width footprint result, then decide whether a quotient five-field
one-sided law can meet the declared physical connection or whether an
explicitly different rotational/finite-extent law is required. If the
action is not zero, revisit the raw-row algebra before any norm study.
The bounded analytic test changes no registered criterion or authority.

**Continuous-law gauge result and action:** The source algebra and an
independent nine-test analytic fixture confirm an exact continuum gauge.
For `s=x−.95` and a flat width coordinate `y`, the declared raw work has
`t=[F+M×(s,y,0)]/W`, hence `t_z=(Fz−s*My+Mx*y)/W`. The nonzero coefficient
field `Fz=s*μ(x), My=μ(x)` gives zero traction and zero virtual work for
every gap. At each station the coefficient-to-traction map has rank five,
not six. A midpoint P0 representation of this field has squared traction
and supported linear-gap work proportional to `h²`; the independent
quadrature agrees with the exact formulas for 2/4/8/16 intervals. The
saved x16/B3-24 P0-eight weak-mode coefficients follow the gauge:
uncentered cosine `cos(Fz,s*My)=0.999950/0.999952` under the inherited/L2
metrics, and only
`1.300/1.295%` of their vertical traction-square decomposition comes
from the interval-centre mismatch; the rest is the unavoidable within-cell
variation of `s`. The P0-four cosine values are `0.999578/0.999680`.
These are source-bound mode postprocesses, not a stability constant.
An independent idealized transverse-strip action with a *separate*
director-pitch couple has rank six at each station; that distinguishes a
possible two-sided law algebraically without qualifying its physical use.

The previous finite-dimensional Gram and eigen calculations remain
arithmetically valid, but the conclusion that their small mode was chiefly
an arbitrary norm conversion is superseded: the mode also approaches a
**true continuous-law gauge**. No positive-definite physical traction norm
exists on six unrestricted coefficient fields without quotienting it.
Do not choose P0/P1/dual or derive a six-channel inf-sup claim for this
positional top-face law. Retain its finite-footprint evidence. The required
full-pose bonded line needs a separately declared physical rotational or
finite-extent work component; the existing director-pitch hybrid is a
distinct two-sided candidate, not an automatically qualified one-sided
replacement. Test that law's top-fixed pitch, objectivity, shear, torque,
work and matched geometry before a multiplier-space comparison. The
published [beam-to-surface construction](https://link.springer.com/article/10.1007/s00466-025-02647-9)
uses a separate surface orientation tensor with a Kirchhoff–Love shell,
so it informs this decision without
qualifying an E4-PL adaptation. G0B remains open, G1 barred, and formal
F03 authority unconsumed.

**Next bounded growing-row diagnostic (prospective, 27 September):** On the
already assembled x8/y4 C1 Q4/B3-12 native retained system, grow the exact
top-face P0 space from the saved two/four intervals to eight while keeping
the physical model, supports, and diagnostic primal/dual norms fixed. The
uncertainty is whether new rows expose a weak mixed mode or simply resolve
the same law more finely. Check scaled row rank, the smallest singular mode
of the actual indefinite KKT tangent, virtual work, and its physical/chart
metric partition under the existing 120 s and 1900-row limits. Rank loss or
a new weak mode redirects work to the interface resolution/norm design;
preserved rank and a comparable mode permit the registered ratio and
physical-transfer assessment, without proving mesh-uniform stability or
selecting P0. Do not rerun the already accepted two/four-interval cases.

**Next norm-construction discriminator:** On the existing bounded x8
P0 two/four-interval fixture, express each current centered mean/rotation
row in the common raw force/first-moment rows by an explicit invertible
six-by-six center/inertia transform. Transport the old multiplier norm
with its work-dual transform and verify reference rows, conjugate work
and the actual indefinite native mixed spectrum against the saved old
representation. If that equivalence fails, repair units or frame/arm
mapping before growing-space stability tests; if it passes, carry the
physically interpreted raw norm into the registered ratio assessment.
This is a bounded metric-construction check, not F03 acceptance.

**P0 work-dual norm outcome:** On the bounded x8/y4 C1 B3-12 native
retained mixed operator, the explicit interval center/inertia transform
maps the current centered P0 rows into the common raw P0 rows with
relative defects below `8e-18`. Transporting the multiplier norm by
the conjugate work map preserves a random primal/dual virtual-work
pairing to `1.4e-17` relative and the smallest normed singular value
of the *actual indefinite mixed tangent* to `1.6e-13` relative for
two and four intervals. Raw source-bound result:
`B3_GE_E4_PL_F03_COMMON_TRACE_P0_METRIC_20260927.json`. This is an
equivalence of representations of the existing **diagnostic** norm,
not an independent proof that the norm is mesh-uniform or physically
complete. It permits use of the raw P0 coordinates in the next
registered growing-space test without changing that comparator's
mechanics or numerical metric. G0B/F03 remain open, G1 barred.
Independent review found no transform or mixed-operator defect. The
saved `transported_line_norm.physical_density_units` field is inherited
from the *centered* representation; it must not be read as units of the
raw dual, which are `N/m` and `N/m²` for these rows.

**P0 eight-interval result and action:** The predeclared x8/y4 B3-12
test has rank `41/48` in both the inherited mixed norm and the separate
declared fixture-coordinate row scaling, with seven relative singular values at
`4.5e-16` or below and the next at `0.0435`. Its weakest left-row mode
combines mean-z and longitudinal first-moment rows. The reference gap is
within the existing guard. An initial execution stopped at the rank guard;
a corrected result writer then hit worktree write permission before an
escalated run saved the immutable source-bound result
`B3_GE_E4_PL_F03_TOP_FACE_P0_EIGHT_MIXED_20260927.json`. No mixed
singular value was calculated for dependent rows. Combined with full
`48/48` rank for x16/B3-12 P0-eight, this points to an over-resolved
discrete interface on the x8 host rather than a failed continuous law.
The earlier x2/m2 versus x4/m2 experiment likewise identified a discrete
continuity dependency when only one shell host lies in each interval.
Two shell hosts per multiplier interval is a provisional resolution
candidate, not yet a qualified policy; its work, locking, native KKT,
physical transfer, and registered ratio behavior remain to be tested.
This exact rank result is a dependency diagnosis, not F03 acceptance or a
declaration of formulation failure. Independent read-only review found no
source or rank-interpretation defect. The displayed Fz/My left vector is
one member of the seven-dimensional nullspace, not a characterization of
all seven modes; the fixture scaling is not a canonical inf-sup norm.

**Combined F03 interpretation:** The saved x16 common-action projection
shows that four-to-eight P0 growth changes the lateral/twist two-hat
differences from F5 `0.299/0.185` to `0.682/0.430` for B3-12, but from
`0.861/0.547` to `0.165/0.101` for B3-24. The vertical difference stays
around `0.014–0.025`. Thus the x8 row dependency and x16 full rank do not
license an eight-interval production policy or an accuracy ranking: loaded
transfer still depends strongly on native beam resolution. F5 has a
stronger shared-node bond and cannot select the weak multiplier by itself.
The next useful matched assessment must vary beam and shell resolution
under an explicitly admissible row policy and report physical work and
locking, not only a rank or tip displacement.

**B2 heterogeneous-junction result:** A separate private F09 diagnostic
places 80×3 mm and 12×3 mm rotated physical sections at a two-member
elbow, including a reversed-second-member control. Both passed the
unchanged bounded development checks: maximum stored exact-product
force ratio `1.14e-10` against `1e-8`, and one eligible factorization per
case. The V1 result is retained, but independent review found it omitted
hashes for dynamically loaded probe/product modules. A provenance-only
V2 rerun records the actual resolved paths and SHA-256 of all six direct
sources and uses repository-root HEAD. All source hashes match; ten
selected mechanics fields per case are exactly unchanged from V1. The
current source-bound result is
`B3_GE_E4_PL_G0_F09_HETEROGENEOUS_JUNCTION_DEV_V2.json`. This adds one
sampled heterogeneous graph, not continuous conditioning or F09 admission.
Independent V2 review noted that `source_graph` lists the direct runner,
probe and product modules but not transitive `linalg.py`, `control.py` or
`threading_policy.py`. All three and the listed product files are tracked
and clean against the recorded `4fee957c` HEAD, which binds their bytes for
this Level-A diagnostic. V2 does not record every installed dependency;
it must not be promoted as standalone F09 qualification evidence.

**Next local-mode discriminator (prospective):** First check whether the
supported four-interval top-face row space is contained in the eight-
interval space for each B3-12/B3-24 trace on the same x16 shell. Use
declared physical column scales and report rank and projection defect,
without interpreting that number as inf-sup. If containment fails,
the row-count comparison changes the represented law and its segmentation
must be revisited before another loaded solve. If it holds, recover the
eight-interval weak modes and local physical shell work from the *four-
interval solution* in the minimum matched loaded pair; those modes
identify what enforcement adds. This is a bounded development diagnostic,
not formal F03 execution or multiplier selection.

**Row-containment result:** The bounded x16 Q4/B3-12 and B3-24 reference-
chart matrices each have supported ranks `24`, `48`, and union `48` for
four rows, eight rows, and their union. With the fixture's physical
coordinate scales, the maximum rowwise projection defect of the four-
interval space into the eight-interval space is `3.82e-15` (B3-12) and
`6.23e-15` (B3-24). This establishes algebraic nesting on these supported
fixtures, not inf-sup or absence of locking. The raw source-bound result
is `B3_GE_E4_PL_F03_TOP_FACE_X16_ROW_NESTING_20260927.json`. Next recover
the eight-interval gaps of the four-interval loaded solution, interval
interface work, and physical shell work by cell in one paired solve for
each beam trace. Nonzero added modes identify what the refined law
suppresses; their physical strain/work interpretation determines whether
to revise the row policy or advance the registered stability assessment.

**Selected local-mode outcome:** The paired x16 B3-12 and B3-24 routes
reproduce the earlier separate four/eight solutions within `1e-8`
relative and `1e-12` absolute checks on tip, external, shell and
interface work. Each included per-element physical E4 matrices during its
single shell assembly; their recovered work sums to the global physical
shell work. The four-interval solution has its own weak rows closed to
about `1e-17`, but the eight-interval probe detects new modes: under
torque, the largest angular moments are `rx=0.245/rz=0.225 µrad` for
B3-12 and `rx=0.278/rz=0.135 µrad` for B3-24; under opening, `ry` peaks
at `1.465` and `1.809 µrad`. Translational mean gaps are at most
`0.017/0.018 µm` under opening and `0.010/0.012 µm` under torque. The
eight-interval solutions close both nested weak spaces to numerical
precision. The angular rows have radians while mean rows have metres;
raw maxima cannot rank them. With a 0.05 m transverse lever for `rx/rz`
and 0.00625 m half-interval longitudinal lever for `ry`, their implied
face motions are roughly `7–14 nm`, comparable with the `10–18 nm`
translational means. The added enforcement therefore constrains both
subinterval mean and angular position modes, not only one channel.

Sampled maximum pointwise position gaps fall from `0.062→0.047 µm`
(B3-12 torque), `0.054→0.041 µm` (B3-24 torque),
`0.150→0.130 µm` (B3-12 opening) and `0.153→0.140 µm` (B3-24 opening).
Physical E4 work in the bonded x=[.9,1] m cells changes from
`0.285→0.255 mJ` for B3-12 torque, `0.272→0.273 mJ` for B3-24 torque,
`1.079→0.998 mJ` for B3-12 opening, and `1.097→1.047 mJ` for B3-24
opening. The torque-case sum of absolute interval Fy divided by net Fy
rises `29.6→37.1` for B3-12 and `18.2→62.2` for B3-24; each interval's
shell/beam work cancels and all work balances pass. This highlights
self-equilibrated high-frequency transfer, but may include a legitimate
couple and is not a locking diagnosis by itself. The raw source-bound
results are `B3_GE_E4_PL_F03_TOP_FACE_X16_B12_LOCAL_MODES_20260927.json`
and the corresponding `B24` file. One selected old-route regression
passed `1/1`. Independent read-only review found no algebra or work-unit
defect: element work sums within `1.3e-12 J`, interval shell/beam work
cancels within `2.9e-16 J`, and interval work sums to global within
`4e-17 J`. Signed interval interface work is a force-displacement pairing,
not nonnegative strain energy. Next distinguish physical couple transfer from unstable
multiplier oscillation using a norm and reference that resolve these
angular modes, without using F5's coarser two hats or a new mesh sweep
as a surrogate. G0B remains open, G1 barred, formal F03 authority
unconsumed.

**Next C1 connection-law decision (27 September):** The saved matched
fixed-grid C1 experiment already contains both six position-moment
`surface_moments` and six-channel director-pitch `line_hybrid_single_interval`
under the same 35 mm Q4 plate, 2 µm tapered B3 reference axis, terminal
patch, supports and separate tip torque/shear loads. At x2/y2, torque tip
rotation is `50.0238` versus `49.1629 µrad`; at x4/y4 it is `50.4280`
versus `49.6074 µrad`. These are different *laws*, not a P0/P1 space
comparison. The existing compensated top-fixed pitch witness gives zero
top-face positional work but nonzero hybrid pitch work, already interpreted
as a two-sided face couple. Therefore keep the top-face and two-sided weld
semantics separate and do not use the F5 top-face solid to score hybrid
accuracy. The bounded next implementation question is whether the existing
top-face finite-width positional work can be segmented longitudinally into
a differentiable six-resultant line candidate without changing its
continuous law. Test reference consistency, actual E4/B3 chart work,
supported rank and the compensated pitch distinction before a loaded solve.
If those pass, F5 supplies a compatible top-face *physical-transfer*
comparator, though its shared-node bond remains stronger than six projected
moments and cannot by itself qualify that weak law; if not, revise the
segmentation. Neither outcome selects
a multiplier space, qualifies C1, changes formal F03 authority, or enters
G1. Independent read-only review confirmed the two distinct laws and found
no contradiction in the compensated-pitch or face-pair virtual-work checks.
It also found that fixed-grid torque and shear support-wrench partitions
change appreciably, so matching tip motion alone is not a physical-transfer
score. The F5 solid supports only the top-face positional comparison; a
separately defined two-sided stitch is needed to assess the hybrid weld.

**Top-face segmentation discriminator:** The first bounded test found rank
`11/12` for two six-row intervals on an x2 terminal shell grid, although
the one-interval reference, chart derivative and nonzero-chart work checks
passed. Row-normalized SVD gives smallest singular value `1.56e-16`; the
same left-null combination exists in shell-only and beam-only columns. It
links the two interval mean-z rows to their pitch-moment rows and is an
exact discrete continuity relation, not a raw-unit rank cutoff. **Question:**
is this an inherent duplicate in the proposed line law or the consequence
of one linear shell host per interval? Compare the same two-interval law on
one x4 terminal grid with two hosts per interval, without a loaded solve.
The x4 grid has rank `12/12` in full, shell-only and beam-only supported
traces, with row-normalized smallest singular value `0.57735`; x2 has the
exact identity `mean_z[0] - mean_z[1] - 0.025*(pitch_y[0] +
pitch_y[1]) = 0` (maximum coefficient error `2.1e-15`). This identifies
coarse primal representability as the immediate source: one linear host
per interval cannot support twelve independent moment equations, while two
hosts can. The next production decision needs a resolution-aware row policy
or a different admissible multiplier basis, then work, locking, and
growing-space stability checks. This diagnostic does not itself choose
that policy, establish stability, or select a multiplier space.
The bounded two-test first pass recorded the x2 `11/12` failure against an
initially incorrect full-rank expectation. After identifying the exact
relation and adding the x4 discriminator, the complete focused file passed
`25/25` (`NUMBA_DISABLE_JIT=1`, plugin autoload off, one BLAS/MKL/OMP thread;
400.51 s). The initial failed check is retained as the discovery, not
silently described as an accepted x2 full-rank result. No loaded solve,
formal F03 run, G0 acceptance or multiplier selection follows.

**Next bounded loaded discriminator:** For the first application, an
externally attached top-face stiffener provisionally uses positional
finite-width work as its leading physical law; the C1 director-pitch
channel remains an explicitly two-sided/embedded candidate. The available
x4 shell has two hosts per each of two top-face intervals and full local
row rank. Solve its existing +100 N m tip torque and -1000 N tip shear
influences once with those two intervals, under the saved C1 geometry,
supports, section and loading. Compare complete work, support/interface
wrenches and tip response with the saved one-interval top-face and hybrid
calculations. If segmentation materially changes transfer, carry both
physical transfer and growing-space stability into the selection; if it
does not, prioritize the independently resolved reference and stability
over further loaded interval sweeps. This local solve cannot score accuracy
against F5's stronger shared-node bond or qualify a multiplier space.

**Loaded top-face segmentation result:** The x4/y4, B3-12, 35 mm, one-thread
two-interval solve has rank `12/12` and maximum mechanics error
`5.40e-12`; its complete raw result and source hashes are in
`B3_GE_E4_PL_F03_C1_TOP_FACE_SEGMENTED_DEV_20260927.json` beside this note.
Compared with the saved one-interval top-face result under exactly matched
reference geometry, supports, section, and separate loads, torque tip
rotation changes `50.42799→47.41278 µrad` (`−5.98%`), opening tip motion
`−70.25176→−69.38174 µm`, torque shell-support `Fy`
`−55.3359→−67.2982 N`, and torque shell-support `Mz`
`−29.0251→−32.1831 N m`. Thus longitudinal resolution materially changes
physical transfer on this grid. The hybrid remains a different continuous
law; its saved x4 torque tip is `49.60736 µrad`, shell `Fy=−68.0414 N`
and `Mz=−32.7149 N m`, while its opening shell `Fz=82.4897 N` versus
`70.9111 N` for the segmented top-face law. Proximity of any isolated
quantity to F5 is not accuracy evidence because F5 enforces a pointwise
shared-node bond. Do not stop at the one-interval law or select a multiplier
from these numbers. Next: match top-face integrated transfer and shell
response against F5 at its valid level, then assess growing-space stability;
keep a separate independently resolved two-sided reference for the optional
embedded pitch law. The first two identical numerical solves passed their
rank/work assertions but evidence-file creation was denied by the normal
sandbox; the third run saved the full output after using the installed
Python in the isolated worktree. The selected existing loaded tests first
gave `1/2`: a station-finiteness assertion fed mixed scalar/vector values
to NumPy's ragged-array conversion. The assertion now checks each numeric
value directly; the same two tests pass `2/2` (39.63 s). This was a test
compatibility correction, not a change to solved mechanics. Independent
read-only mechanics review found no concrete work-map, frame, source-identity
or loaded-comparison defect. It emphasized that the rank-11 relation belongs
to this one-host-per-interval discrete fixture, not every two-interval
space. The review does not confer G0 acceptance. G0B and F03 remain open.
The review's sole coverage limit was a missing finite B3 mixed-direction
check at a recentered interval. A new nonzero E4/B3 port-state test now
checks first, second and mixed multiplier-work derivatives through actual
state advances; the three focused top-face checks pass `3/3` (6.42 s).
This closes that local test gap without changing the physical-law or
stability status.

**Next F5 action discriminator (prospective):** Use the saved validated F5
bar-on-plate action and the x4 native one-/two-interval top-face actions;
make no new solid or native solve. Project each onto the same continuous
two-hat lateral, vertical and physical-twist virtual fields over the
terminal bond. Check action sign, reference geometry, global wrench and
the first longitudinal moment before interpreting the difference. A
coherent contraction of all relevant action discrepancies would justify
the same-action shell-response comparison; mixed changes instead require
that comparison without ranking either law from tip motion. Both outcomes
leave higher modes, shell idealization and retained one-sided work open.

**F5 two-hat action result:** Existing hash-bound F5 combined action and
the saved x4 native cases have matching physical reference geometry,
supports, section, and `+100 N m Mx −1000 N Fz` linear combination. The
one→two-interval top-face lateral-force hat relative L2 discrepancy changes
`1.684→0.530` and physical-twist discrepancy `0.797→0.336`, but vertical
force changes `0.000531→0.0283`. The solid total lateral force is
`54.6236 N`: one interval gives `55.3359 N`, two give `67.2982 N`.
Its lateral-force first x moment is `16.6724 N m`, versus `−11.7720`
and `25.6106 N m`. This is a mixed change, not coherent improvement;
do not rank the laws or multiplier by one lower norm. **Next bounded
discriminator:** Replay the validated saved F5 action and the new native
two-interval action through the *same* Q4 x4/y4 shell and compare their
top-face fields at fixed stations, with the saved solid face field as a
separate idealization check. If the F5-action E4 response already differs
materially from the solid, shell discretization, kinematics, action
projection and the stronger pointwise bond remain possible contributors; if it agrees
but native-action E4 differs, investigate the connection/beam action.
Either outcome remains finite-grid diagnostic, not G0B acceptance.

**F5/native same-shell result (saved-output replay):** The bounded runner
`scripts/b3_e4_f03_c1_top_face_f5_same_action.py` verifies the protected
F5 inputs, reconstructs the validated bar-on-plate stress action, checks
its wrench, and applies it and the native two-interval action separately
to the same E4 Q4 x4/y4 shell. It reads the saved pre-opened combined F5
displacements; no CalculiX or new native coupled solve runs. Complete v1
and v2 outputs remain in this directory; v2 adds the solid face slope.
At x=.95 m, the solid top-face mean z is `−66.19777 µm`; E4 under the
*F5 action* gives `−65.43089 µm` (`+0.76688 µm`), while E4 under the
*native action* gives `−66.26292 µm` (`−0.06515 µm` relative to solid).
The native-versus-F5-action E4 change is `−0.83202 µm`. The physical
transverse face slope is `45.342 µrad`, versus `44.2065` and `45.0138
µrad` for F5-action and native-action E4 respectively. The same pattern
appears at x=.9 and 1 m. Thus shell response to the same recovered F5
action and changed interface action are of comparable magnitude and
opposite sign in mean z. The native result's closer finite-grid face
motion may be cancellation; it cannot validate its law or allocate the
remaining beam/joint difference. Same-shell reciprocal cross-work error
is `5.67e-16 J`; both shell solves pass equilibrium. One mesh and the
stronger F5 pointwise bond remain limitations. Independent read-only review
found no sign or top-face projection defect, verified the saved F5 and native
wrench signs, and independently checked all native active-node moments
against the +17.5 mm top-face pullback (maximum defect `2.7e-15 N m`). It
also confirmed that the sampled mean-z cancellation is descriptive, not a
unique causal allocation; solid/E4 kinematics, mesh resolution and the
pointwise-versus-weak bond remain unresolved. The slope cancellation is
incomplete. G0B and the multiplier decision remain open.

**Next top-face resolution discriminator (prospective):** Keep the same C1
reference section, loads, supports, 35 mm shell and B3-12 predecessor.
Compare the saved x4/two-interval route with x8/two and x8/four; on the
same x8 primal mesh, the latter pair isolates multiplier enrichment. Four
intervals have two shell hosts each. Check exact reference gaps, full
supported row rank, loaded equilibrium/work/wrench, and physically scaled
constraint inventory. A rank failure or unsupported mode revises the
resolution policy; a large x8 two→four transfer shift requires locking and
physical-mode analysis before extension. If x8 remains well behaved, move
to the actual retained mixed-tangent norm and the registered ratio/three-
level programme. The x4→x8 comparison alone cannot prove convergence
because shell resolution changes.

**Top-face x8 same-primal result:** The private sparse route checks exact
reference closure, supported rows and full E4/B3-12 KKT load/work balance
for x8/two and x8/four intervals. The first output is retained as v1;
the v2 source adds explicit reference-gap preflight. In v2, maximum
reference gaps are `1.64e-16` and `3.58e-16`; every interval has the
expected `.05` or `.025 m` basis integral. Combined and shell-only
row-normalized ranks are `12/12` and `24/24`. Beam-only ranks are `11/12`
and `14/24` on this *fixed B3-12 trace*; the missing beam-only rows do not
make the combined system singular, but must be interpreted in the native
broken-trace/mixed norm. Torque tip rotation changes `47.5318→46.9399
µrad` for x8 two→four (about `−1.25%`), opening tip motion
`−69.4260→−69.2719 µm`, and both cases balance to the registered
development tolerance. The saved x4/two route has torque `47.4128 µrad`;
the x4→x8 difference also includes shell refinement. Do not infer locking
absence or choose a multiplier from these smooth outputs. **Next bounded
test:** Apply the already defined native retained mixed KKT and physical
primal/dual auxiliary norms to x8/two versus x8/four, with a near-null
decomposition, not a positive trace quotient alone. A materially collapsing
mixed inf-sup or unsupported mode would revise the interface resolution;
otherwise advance the registered ratio/convergence programme. G0B stays
open and formal F03 authority unconsumed.

**Retained mixed-system norm result:** The actual indefinite E4/B3-12 KKT
with the existing physical-plus-chart primal and P0 density-dual diagnostic
norm gives normalized constraint ranks `12/12` and `24/24` for x8/two and
x8/four. Its smallest normalized singular values are `0.0018764829` and
`0.0018765553`, with conditions `52695.02` and `52694.95`; normalized
work errors are near machine precision. The near-null metric is 99.935%
auxiliary shell drilling chart in both cases, with physical shell about
0.0645% and negligible beam/line shares. Thus two→four does not expose a
new mixed weak mode on this grid; the global minimum is dominated by a
nonphysical norm component and does not establish uniform interface
stability, locking absence, or fidelity. The raw result
`B3_GE_E4_PL_F03_TOP_FACE_X8_MIXED_METRIC_20260927.json` records source
hashes, finite reference gaps, scaling and limitations.

**Next decision-oriented physical check:** Compare x4/two, x8/four and
x16/eight with two Q4 hosts per interval, the same B3-12 and same loads,
supports and 35 mm section. Check reference closure, supported rank,
separate torque/shear work and support/interface wrench. A persistent or
growing physical-transfer shift sends the top-face trace or interface
resolution policy back for review; a settling response permits the
registered ratio/growing-space and independent physical-reference work.
Changing shell resolution together with multiplier resolution cannot
isolate their separate effects; the saved x8/two→four pair supplies that
control. This bounded three-level sequence is not formal F03 execution or
a production multiplier choice.

**Aligned three-level result and control decision:** The x16/eight route
passed rank `48/48`, reference closure `3.23e-16`, and torque/opening
mechanics errors below `6.7e-11`. Its first raw output used the opposite
shear sign from x4/x8; it is preserved as v1 and excluded from the opening
comparison. Corrected v2 uses the matching `−1000 N Fz` and includes an
explicit sign assertion. Across x4/two, x8/four and x16/eight, torque tip
rotation is `47.41278, 46.93986, 46.42699 µrad`; the successive changes
do not shrink. Opening tip motion is `−69.38174, −69.27193, −69.16948 µm`.
Torque shell-interface Fy is `67.2982, 66.1857, 67.4918 N`, so this
fixed-beam three-level sequence has no demonstrated transfer limit yet.
At fixed x8, two→four rows change torque by `−0.59198 µrad`; shell and row
changes are confounded in the next x8/four→x16/eight shift. The single
bounded x16/four control separates x16 shell refinement at fixed four
intervals from row enrichment at fixed x16. If the latter dominates,
review interface resolution/locking and physical work; if the former
dominates, check shell/beam idealization and convergence before further
line-space changes. Neither outcome selects a multiplier or closes G0B.

**Fixed-shell control outcome:** The x16/four run passed rank `24/24`,
reference gap `2.37e-16`, and mechanics balance. With four intervals held
fixed, x8→x16 shell refinement changes torque tip rotation
`46.93986→47.04893 µrad` (`+0.10907 µrad`). At fixed x16, four→eight
rows change it `47.04893→46.42699 µrad` (`−0.62193 µrad`). Thus row
enrichment dominates the combined `−0.51287 µrad` change and continues
the material row-resolution dependence observed at fixed x8
(`−0.59198 µrad` for two→four). Torque shell-interface Fy at x16 changes
`66.0252→67.4918 N`; opening displacement changes
`−69.30418→−69.16948 µm`. All full and shell-only scaled rows retain
rank; beam-only rank stays 14 for both x16 spaces. These bounded outcomes
point to interface resolution/physical-work and locking analysis as the
next decision, not another automatic refinement. They do not prove
locking, establish a transfer limit, or select P0. An independent
read-only review of this allocation is pending. The selected existing
terminal tests initially gave `1/2` because one expected an obsolete
validation message; its expectation now matches the existing bounded-C1
admission and the same two tests pass `2/2` (56.94 s). G0B remains open,
G1 barred, formal F03 authority unconsumed.

**Saved F5 common-action replay and next bounded test:** No new solid or
coupled solve was used. The saved x8/four, x16/four and x16/eight native
actions were projected onto the same validated two-hat lateral, vertical
and physical-twist fields. Relative L2 deviations from the F5 action are
respectively `(0.4033, 0.01927, 0.2508)`, `(0.2993, 0.01427, 0.1847)`
and `(0.6818, 0.01720, 0.4301)`. At fixed x16, adding four intervals
therefore worsens these low-order lateral and twist differences even though
the x8→x16 shell-only change at four intervals improves all three. F5's
shared-node pointwise bond is stronger than the native weak law, so this
is a directional warning, not a target tolerance, accuracy ranking or
multiplier selection. Independent read-only review confirmed matched
models, the response decomposition and the drilling-norm limitation; it
found no calculation blocker. The next discriminating pair holds x16 Q4
and the declared top-face law fixed, refines native B3-12→B3-24, and
compares four versus eight intervals with actual work and a physical-mode
measure that excludes the auxiliary drilling direction. If the row effect
shrinks substantially, investigate beam-trace resolution and locking; if
it persists, investigate the continuous trace and enforcement policy.
Neither result alone qualifies a multiplier. The action replay is saved
as `B3_GE_E4_PL_F03_TOP_FACE_X16_COMMON_ACTION_20260927.json` with
protected-input and script hashes. G0B remains open, G1 barred.

**Beam-resolution discriminator result:** At the same x16 shell and
35 mm top-face law, B3-24 completes four/eight interval cases in 69.61/66.85
s, with full/shell ranks `24/24` and `48/48`, reference closure below
`3.24e-16`, and mechanics balance. The beam-only row ranks are `21/24`
and `26/48` versus B3-12's `14/24` and `14/48`. Torque tip rotation is
`47.25236→46.30221 µrad` for B3-24 (`−0.95015 µrad`) versus
`47.04893→46.42699 µrad` for B3-12 (`−0.62193 µrad`); beam refinement
does not eliminate the row effect. Opening motion is
`−69.04278→−68.92262 µm` for B3-24. The extended read-only F5 common-hat
comparison gives lateral/vertical/twist relative L2 deviations
`(0.8608, 0.01653, 0.5469)→(0.1652, 0.02451, 0.1014)` for B3-24,
opposite the B3-12 lateral/twist direction
`(0.2993, 0.01427, 0.1847)→(0.6818, 0.01720, 0.4301)`. F5's pointwise
shared-node bond and continuum shell are different idealizations, so this
reversal cannot rank row spaces or prove locking. It instead shows strong
interaction between native beam trace resolution and enforcement. Stop
mesh escalation. Next inspect the *physical* newly constrained modes,
actual half-cell port work and shell strain-energy distribution on these
saved matched cases; derive an admissible interface-resolution policy and
test its work/locking/stability on registered ratios. If these outputs
cannot be reconstructed from saved cases, add only the needed selected
recovery to this bounded fixture, then rerun the minimum matched pair.
The validated F5 action lacks verified sided retained-port work, so use
it only at common continuous fields until that reference is resolved.
G0B/F03 remain open, G1 barred, formal F03 authority unconsumed.

**Continuous-law correction (independent mechanics review):** The current
`FiniteSurfaceTopFaceLine` normalizes each multiplier-weighted footprint,
recomputes its center and inertia, and evaluates its material frame at that
center. Its longitudinal `My` row is a weighted least-squares slope of
the mean top-face normal-position gap, not a pointwise independent
director-pitch channel. For the *complete six rows in one common gap
frame*, moving the center and applying invertible inertia normalization
are block-invertible row changes of the basis-weighted zeroth/first
position moments; center dependence alone does not change their zero
subspace. This does not settle physical multiplier densities, norms or
the meaning of a pointwise six-channel trace. The C1 helper also changes
its material frame with basis center; because its fixed reference arm
and frame rotation need not commute with the cross product, strict
same-law equivalence requires either a common frame/arm convention or
an explicit covariant row-transform proof. A signed endpoint dual basis
has negative normalized longitudinal variance `−h²/6`, so the current
positive-inertia guard rejects it despite a potentially invertible
raw-moment representation. The exact x2 `11/12` row relation and full
x16 P0 supported ranks show resolution-dependent representability, not
proof of locking or law failure. Preserve all P0 evidence; do not reuse
the helper's named rows as P1/dual physical densities without proof.

**Next derivation and executable discriminator:** Define a basis-independent
raw top-face position-work integrand with one reference material frame,
one reference arm convention and fixed transverse width. Keep its three
zeroth and three first moment components and derive each P0/P1/dual row
as `∫ φ_i(x) q[g](x) dx`; put any invertible center/inertia transform and
the physical dual mapping outside that common integral. Test exact
reference-chart row-space equivalence against the current P0 helper,
and an invertible signed dual construction without a positive-covariance
assumption. Derive finite-chart work, one-sided native port behavior,
boundary terms and physical dual units. Check whether the longitudinal
moment is a derived position-slope constraint and whether continuous
mean-position enforcement already supplies its physical bending work;
do not silently drop moment transfer. Then test affine reproduction,
rigid work, transverse shear freedom, top-fixed pitch distinction,
reference rank/nesting and first/mixed
derivatives before any loaded P0/P1/dual comparison. Failure revises the
trace; success advances the registered same-law stability and physical
reference assessment. G0B remains open, G1 barred, formal F03 authority
unconsumed.

**Fixed-frame same-integrand outcome:** One reference material frame at
`x=0.95 m` and one shell-top arm convention yield raw zeroth/first
position-work rows. On supported x16 Q4/y4 C1 B3-12/B3-24 fixtures,
their P0 four/eight spaces and the current centered P0 helper have ranks
`24/48`, union ranks `24/48`, and bidirectional maximum unit-row
projection defects from `3.1e-15` to `4.5e-14`. This validates P0
reference-chart row-space equivalence on these fixtures, not finite-chart
equivalence or physical fidelity. The source-bound result is
`B3_GE_E4_PL_F03_TOP_FACE_COMMON_TRACE_20260927.json`.

The same raw integrand admits P0, continuous P1, and signed dual basis
pairings without requiring a positive weighted inertia. Their full-bond
partition work closes with relative error at most `8.3e-16`, and the
global constant/affine/quadratic *partition sums* close under the
existing quadrature; individual basis-function moment reproduction has
not been checked. Supported ranks are `24/24` and `48/48` for P0;
`29/30` and `53/54` for P1; `30/30` and `53/54` for dual, for both B3
traces. These are rank diagnostics, not inf-sup or locking acceptance.
P1's single exact dependency is analytic: its hats reproduce the affine
function `x−0.95`, so the sum of longitudinal first-moment rows equals
the corresponding affine combination of normal mean-gap rows for every
gap field. It does not indicate locking. The dual-eight smallest singular
value is about `1e-16` of the largest, and its left-null vector is confined
to the mean-normal/longitudinal-moment pair; dual-four is full rank.
The remaining question is why that dual near-null relation arises at
eight intervals on the discrete primal space. Source-bound results are
`B3_GE_E4_PL_F03_COMMON_TRACE_SPACES_20260927.json` and
`B3_GE_E4_PL_F03_COMMON_TRACE_NULL_MODES_20260927.json`.
The complete-column check retains rank `53/54` for B3-12 and B3-24;
smallest/next relative singular values are about `1e-16` and
`0.0023/0.0030`. The supported left mode has zero residual on fixed
columns, so eliminating root supports did not create it. Source-bound
result: `B3_GE_E4_PL_F03_DUAL_EIGHT_SUPPORT_20260927.json`. Raising
reference quadrature from order three to five, with geometry, primal
columns and dual basis fixed, retains rank `53/54` for both beams; the
next relative singular value stays at `0.00232/0.00303`. The tested
quadrature is therefore not the cause. The evidence points to finite
trial/trace representability, but does not establish physical locking
or select another space. Raw result:
`B3_GE_E4_PL_F03_DUAL_EIGHT_QUADRATURE_20260927.json`. Stop grid and
quadrature escalation. Derive the exact discrete relation, check
per-basis moments, then develop finite-chart work and signed dual
mapping before the registered growing-space stability assessment. The
next finite-chart discriminator uses one co-moving B3 frame at the fixed
reference center and the existing top-face positional work, with P0,
P1 and a signed dual basis row on one bounded Q4/B3 fixture. It checks
reference closure, objective rigid motion, one-sided retained-port
variation, and first/mixed formal-work derivatives in the spatial-left
shell chart. Failure requires
repair of the common work law; passing permits a physically interpreted
growing-space assessment, but does not select a multiplier or close G0B.
G0B/F03 remain open, G1 barred, formal F03 authority unconsumed.

**Common finite-chart work outcome:** The bounded x4/y4 Q4/B3-12 C1
fixture reuses one co-moving center frame and top-face positional law for
selected P0, P1 and endpoint dual rows. The dual actually carries
negative quadrature weights. All three have reference gaps below
`1.0e-19`, reference *directional* Jacobian discrepancies below `2.3e-20`, nonzero
deformed gaps, and finite common-rigid-motion errors below `1.3e-18`.
First-direction formal-pairing finite-difference errors are at most
`1.7e-12`; mixed-direction errors at most `2.6e-12` through spatial-left
shell increments and retained B3 state updates. The source-bound raw result is
`B3_GE_E4_PL_F03_COMMON_TRACE_FINITE_WORK_20260927.json`. This validates
the selected spatial-increment rows' formal work and derivatives on
one bounded state, not the E4 additive total-rotation chart, all basis
functions, physical dual units,
interface stability, or engineering fidelity. Continue the exact
discrete-relation, per-basis moment and E4 chart derivations; then assess the same
law's physically normalized growing-space behavior. G0B/F03 remain
open, G1 barred, formal F03 authority unconsumed.

The saved diagnostic labels the formal pairing-error fields `_J`; that
unit label is not justified until the signed row multipliers receive
their physical force/couple-density units. This limitation was identified
by independent read-only review and is retained with the immutable raw
result rather than recasting it as physical energy evidence.
The next bounded check holds the same reference trace, finite state and
signed rows but varies E4's *additive total rotation coordinates* at a
nonzero configuration. It compares the AD pullback and finite-difference
first/mixed derivatives through the actual E4 chart. A mismatch requires
repair of the coordinate pullback; agreement closes only this chart
uncertainty, not physical dual units or interface stability.

**Actual E4 total-chart outcome:** On the same selected P0, P1 and signed
dual rows, the existing E4 additive total-rotation AD pullback was
evaluated at a nonzero shell rotation state and compared with finite
differences that perturb those *total coordinates*. The B3 retained
state advanced through the same native chart. Reference directional
errors stay below `2.3e-20`; first formal-pairing errors are below
`9.4e-13`, and mixed errors below `3.2e-12`. The dual row still includes
negative weights. Raw source-bound result:
`B3_GE_E4_PL_F03_COMMON_TRACE_E4_CHART_20260927.json`. This resolves
the prior chart mismatch for the selected rows and state, but does not
establish physical dual units, full-basis behavior, growing-space
stability, or a connection selection. G0B/F03 remain open, G1 barred,
formal F03 authority unconsumed.

**Next physical-dual discriminator:** Because raw mean-gap rows have
units `m²` and raw first-position moments `m³`, assign their duals
`N/m` and `N/m²` for energy work. The corresponding surface traction
at quadrature point `p` is the co-moving frame applied to
`(λ_F + λ_M × a_p)/width`, with `a_p` the fixed material arm. On one
reference fixture, compute physical resultant and moment about a common
origin from that traction, then compare them with the actual shell and
native B3 virtual work under separate rigid motions. If conjugacy or
action–reaction fails, repair the dual map before any multiplier-norm or
external transfer comparison. Agreement establishes only this bounded
map, not the full loaded connection law.

**Reference physical-dual outcome:** On the same selected P0, P1 and
signed dual rows, assign mean-gap duals `N/m` and first-position-moment
duals `N/m²`. With the 0.1 m transverse average, the corresponding
surface traction for one basis row is
`φ_i(x)R_c(λ_F+λ_M×a)/0.1 m`. Direct quadrature of that
traction gives a force and moment about the common origin. The actual
E4 shell and native retained B3 reference variations under each of six
independent rigid translations/rotations recover respectively the same
and opposite wrench, with maximum componentwise relative discrepancy
`8.9e-16` and zero action–reaction residual at displayed precision.
The signed endpoint dual includes negative weights. Raw source-bound
result: `B3_GE_E4_PL_F03_COMMON_TRACE_PHYSICAL_DUAL_20260927.json`.
This establishes a dimensionally defined reference dual and its bounded
work conjugacy; it does not recover display-ready finite-state wrenches,
qualify stability or validate external physical transfer. G0B/F03
remain open and G1 barred.

Independent review confirmed the units, cross-product sign and B3
retained-port rigid variation. It identified a documentation erratum in
the immutable raw JSON: the displayed traction formula omits `φ_i(x)`.
The code includes that basis factor in each quadrature weight, so the
saved numerical wrench check is unaffected. The check integrates the
same weighted point set as the operator; it does not independently
sample a continuous traction field.

**Top-fixed pitch distinction:** A supported terminal shell field
rotates its director while compensating the shell reference translation
so the top-face position is unchanged. Its physical E4 shell work is
positive, while selected common P0/P1/signed-dual raw rows have zero
reference work to `1e-12`. The separate two-sided hybrid pitch row
responds by `1e-5 rad`, as expected for its different law. The focused
mechanics test passed `1/1`. This demonstrates director-pitch freedom
for the top-face law on one reference field. The positive *total*
physical E4 work includes the transition region and does not isolate
transverse-shear energy inside the bond or establish thickness/
mesh-uniform behavior.

**Per-basis integration check:** On the x16/y4 C1 B3-12 reference
fixture, each of the eight-interval P0, P1 and signed dual basis
integrals of `1`, `x−0.95`, and `(x−0.95)²` agrees with an independent
exact rational polynomial integral to `2e-15` absolute tolerance. The
focused test passed `1/1`. This closes the per-basis quadrature question
at that resolution; it does not explain the dual-eight discrete primal
near-null or qualify a multiplier space.

**Next dual-eight span discriminator:** Contract the saved P1 and
dual-eight left-null coefficients with the common continuous
normal-position gap integrand, using fixed longitudinal bases and
independent high-order quadrature on smooth fields. P1 should vanish
pointwise by its analytic affine identity. If dual-eight acts on a
smooth gap while annihilating every current shell/B3 trial column, its
near-null is a discrete primal representability issue; if it vanishes
pointwise, derive the missing continuous identity before changing row
policy. This is one bounded algebraic check, not a new mesh sweep or
multiplier selection.

**Dual-eight continuous-gap result:** Contracting the saved null
tractions with the common scalar normal-position gap gives an exact
continuous P1 identity to about `5e-16` relative L2 action, as the
affine-hat derivation predicts. The dual-eight kernel instead has
relative continuous L2 action `0.06922` for both B3-12 and B3-24, and
its tested pointwise action is nonzero. Smooth low-order polynomial and
first-harmonic pairings are small (maximum `6.1e-6` relative to absolute
terms), showing that this is a high-frequency difference; they are not
evidence of a large physical response. The raw source-bound result is
`B3_GE_E4_PL_F03_DUAL_EIGHT_CONTINUOUS_GAP_20260927.json`. The dual-eight
near-null belongs to the present discrete primal/trace pairing, not to
an identity of the declared continuous six-moment law. The tested
dual-eight configuration therefore cannot be admitted with all 54
independent multiplier rows. This does not reject the dual-space family
at other admissible resolutions or establish locking. G0B/F03 remain
open and no multiplier space is selected.

**Global work partition from the saved solves:** The fixture reports
`uᵀKu` work, without a one-half energy factor. Equilibrium gives native
beam work as external work minus physical and numerical shell work. Under
torque, B3-12 four→eight intervals change physical shell work
`1.954615→1.921030 mJ` and inferred beam work
`2.749470→2.720912 mJ`; B3-24 changes them
`1.977298→1.949419 mJ` and `2.746697→2.679713 mJ`. The numerical
shell completion remains `0.00076–0.00124 mJ`, far smaller than the
physical transfer changes. Thus the extra rows alter both physical
domains and cannot be attributed to drilling completion alone. These
global totals do not identify which local gap/strain modes are suppressed
or distinguish intended surface bonding from locking. Selected
per-interval work and strain-energy recovery is the next useful
diagnostic; no additional mesh level follows from these totals.

**Bounded F09 physical-section decision (27 September):** The prior
`2^-20`/`2^-40` weak-shear graph brackets a numerical issue in an artificial
section family, not a physical admission limit. Test one specified off-axis
rectangular elastic section on the existing two-member elbow under fixed mixed
tip wrenches and a reversed-member control. Derive its stiffness and compliance
from dimensions, material constants and section rotation independently; compare
cut-wrench work, rounded assembled solutions, exact-product force/moment balance,
and local section response. Agreement supports this one physical case only and
leaves the admission envelope open. A cut-work discrepancy points to section or
frame assembly; exact-rounded agreement with failed stored-state balance requires
a fail-closed range or verified state representation. No F03 decision, G0B
acceptance or G1 entry follows from this diagnostic.

**F09 off-axis rectangle result (27 September):** A 40 × 12 mm rectangular
section at 31° with `E = 210 GPa`, `nu = 0.3`, declared approximate
Saint-Venant `J`, and 5/6 shear factors produces a coupled bending block.
Two fixed mixed tip wrenches were applied to the 2 m + 1.5 m elbow, forward
and with its second member physically reversed. Analytic section compliance
and cut-wrench integration agree with the assembled work; station resultants
and strains agree with the oriented physical cuts. On the first forward case,
an exact product of the stored matrix and sparse-solver state has scaled force
residual `1.0746248336e-11` and moment residual `1.8317402206e-13`.
The high-precision rounded-matrix solution, after binary64 storage, still has
scaled force residual `7.9054984781e-12`. Thus this case exceeds the existing
`2e-12` *F09 diagnostic* while meeting the registered `1e-8` physical-balance
limit; the diagnostic failure is retained, not reclassified as F09 acceptance.
The private batch solves both cases with one factorization and selected station
recovery. The new physical-section tests and existing F13 tests pass `21/21`.
The broader focused F09/F13 set passes `32/32`. Two exploratory stdin probes
that attempted repeated full rational graph elimination were interrupted after
excessive runtime; they produced no accepted data. The bounded test instead
uses a 100-digit solve of the stored rounded matrix and exact products of the
stored binary64 state.
The full physical geometry/conditioning envelope, attachment behavior,
production admission, independent review, F09 and G0B remain open.

**Next F09 component discriminator:** The off-axis cut-wrench energy and
station-resultant checks could still miss a compensating component mapping
error in the six tip responses. On the same two fixed mixed wrenches and
forward/reversed elbow, differentiate the independently derived sectional
cut energy with respect to each physical tip force and couple. Compare all six
predicted tip translations/rotations with the sparse solution in a bounded
component diagnostic. Its `rtol=1e-8, atol=1e-10` check was not a frozen F09
gate measure and cannot replace the registered physical normalization. A
mismatch points to the force/displacement or frame mapping; agreement strengthens this one
physical-section case only and does not establish a conditioning envelope or
qualify F09/G0B.

**F09 six-component result:** Both fixed mixed wrenches and the reversed
second member pass the independent energy-gradient comparison for all six
physical tip components. The identity `0.5 * tip_wrench · predicted_tip =
cut_energy` also passes. Independent read-only review found the cut lever arm,
axis reversal and tip-DOF ordering consistent, and required the diagnostic
tolerance wording above. This extends the one-section physical response
evidence without establishing the F09 admitted range or G0B acceptance.

**Additional thin physical-section point:** A private 80 × 3 mm steel
rectangle with rational 3-4-5 axis rotation, the declared approximate
Saint-Venant torsion constant and 5/6 shear factors passed forward and
reversed two-member elbow checks under one small fixed mixed tip wrench.
Independent rational cut-wrench work, six tip responses, station resultants
and strains, and a 100-digit solve of the stored rounded matrix agreed.
The stored sparse state had exact-product relative force residual
`3.89e-10`, length-scaled moment residual `8.27e-13`, and relative work
error `9.86e-11`; both cases used one numerical thread and finished in
`0.59 s` at `92 MB` peak RSS. This is one admissible linear-response
diagnostic, not a continuous section range or F09 qualification. Its
source-bound raw result is `B3_GE_E4_PL_G0_F09_THIN_SECTION_DEV_V1.json`.

**Next bounded F09 physical-range screen (registered before execution):**
Hold the elbow, material (`E=210 GPa`, `nu=0.3`), 31° section-axis rotation,
two mixed tip wrenches and forward/reversed definitions fixed. Evaluate solid
rectangles `(width, depth)` in metres at `(.08,.04)`, `(.04,.012)` and
`(.012,.003)`, using the same declared Saint-Venant approximation and 5/6
shear factors. These sample compact, intermediate and thin physical sections;
they do not prove a continuous range or local buckling validity. For each,
check independent cut work, all six tip components, station resultants and
strains, applied-scale `1e-8` force/moment balance, and one-factorization
batch behavior. A failing endpoint remains a recorded numerical or
idealization boundary for diagnosis; passing samples support only these
points and a prospective envelope design, not F09/G0B admission. Do not
substitute another dimension to obtain a pass.

**F09 sampled physical-range result:** All three predeclared rectangles pass
the independent cut-work, six-component tip, station response, reversal,
registered `1e-8` applied-scale balance, and private two-load batch checks.
The thin endpoint initially stopped before mechanics evaluation because the
test's `2e-15` absolute `S*C≈I` assertion rejected a `2.438e-15`
floating-point off-diagonal. The identity guard was corrected to a
dimensionless `32*eps` roundoff bound, without changing a physical or gate
tolerance; the original setup failure remains recorded here. The focused
physical-section file passes `6/6`. These three samples do not prove a
continuous physical range, attachment response, practical scale or F09/G0B
acceptance. The next F09 decision is whether a section/load/graph-dependent
balance screen can be made an explicit fail-closed numerical admission policy,
while the physical joint law remains separately open.

**Independent F09 admission review (27 September):** Keep the provisional
`1e-12` exact-LDL pivot screen in this private operator until a replacement
is tested; its value and basis are not physical criteria. A defensible
replacement separates exact SPD and representability of the stored law,
physically scaled preservation of weak local actions after binary64 rounding,
and per-load global applied-force/moment balance plus backward error before
selected outputs. Independent cut-wrench or high-precision physical-graph
references still establish forward accuracy. Merely removing the cutoff
could admit a rounded K that loses a weak combination or fails physical
balance, as the retained `2^-40` graph illustrates. The next bounded F09
design task is to freeze the physical reference scales and action-error
measure for the already tested rectangular family, then test the proposed
local screen against those cases and one retained failure. Do not infer a
section cutoff from the artificial exponent bracket. F09/G0B remain open.

**Next bounded F09 rounding discriminator (27 September):** For the three
already declared rotated rectangular sections and the elbow's 2 m/1.5 m
member lengths, compare the private exact-rational six-basic inverse with
its binary64 storage on six force/couple basis actions
and fixed mixed-sign actions at declared `1000 N` and `1000 Nm` scales.
Check applied-scale action residual, work and positivity of the diagonally
scaled rounded basic operator. Loss of a positive mode or material action
error sends local representation/admission back for revision. Agreement
supports only these physical section samples and shifts the remaining
numerical question to graph/factorization and the prospective admitted
range. It neither replaces independent cut-wrench mechanics nor changes
the provisional private pivot guard or any F09/G0B criterion.

**F09 local rounding result (27 September):** All six predeclared
rectangle/length combinations passed nine exact-rational versus binary64
basic actions apiece. The rounded dimensionless basic matrices remained
positive definite; applied-scale force/couple and positive-work comparisons
met the `1e-8` development discriminator. The affected file passed `12/12`
with single-thread numerical libraries and pytest plugin autoload disabled.
The test-file import order was corrected to load its lightweight private
probe before importing the package, eliminating a package-wide collection
stall. Two earlier runs were stopped without a numerical result at the
existing 120 s diagnostic bound; their empty runner logs are retained at
`%TEMP%/b2-f09-local-rounding-20260927-v1.log` and `-v2.log`. This sampled
rounding result does not establish F09 admission: next assess physical
applied-scale graph/factorization error and the prospective admitted range
without changing the provisional pivot guard or frozen criteria.

**Next F09 graph discriminator (27 September):** Existing physical elbow
checks cover two mixed wrenches. Reuse the same three rotated rectangles,
independent cut-wrench reference and high-precision rounded-matrix solve;
add six pure `Fx/Fy/Fz/Mx/My/Mz` cases at fixed `1000 N`/`1000 Nm` scales.
These distinguish load-component or near-zero-response failures concealed by
mixed cases from a general graph/factorization error. If any fails, inspect
the physical cut, stored assembly and solve before changing admission. If all
pass, retain the sampled evidence and design the prospective continuous
section-range screen; do not infer F09 qualification from these points.

**F09 pure-action graph result (27 September):** All six pure wrench
channels passed for each of the three rotated physical rectangles, in both
member orientations, against the same independent cut-work/cut-resultant
reference and 100-digit solve of the stored matrix. The first run failed
only the new pure-action componentwise comparison at near-zero cross
responses on the thinnest section: its largest reported discrepancy was
`3.3161e-12` against the old mixed-case `1e-12` absolute floor. The pure
comparison now uses the existing physical tip-response floor `1e-10`, while
mixed cases retain `1e-12`; no equilibrium or registered physical criterion
changed. The affected file then passed `12/12` in `3.28 s`. This excludes an
observed pure-channel failure on the sampled graph; it does not establish
the admitted continuous section range or F09/G0B acceptance. Next design
the physical-range representability and fail-closed graph admission screen,
with the retained weak-graph counterexample as a negative control.

**Next F09 local-versus-graph bound (27 September):** The sampled physical
elbows pass and the retained `2^-40` graph is rejected by per-load balance,
but that does not allocate error to local operator storage or global
assembly. For the same three physical sections and the retained weak
generalized section, calculate an exact-rational, diagonally scaled
operator perturbation bound using `F=K_basic^-1` and the actually rounded
binary64 `K_basic`. Compare the dimensionless response bound with the
existing `1e-8` development diagnostic. If the weak case already fails
locally, investigate a local admission rule; if it passes locally while the
graph fails, keep local and graph screens distinct. Do not replace the
provisional pivot guard or infer a continuous section range from four
samples.

**F09 local-versus-graph result (27 September):** The exact-rational
identity `K_basic F=I` and the rounded binary64 `K_basic` were checked in
the same six-basic, power-of-two-scaled coordinates. With
`eta=||A^-1||_inf ||A_rounded-A||_inf`, the rigorous local inverse-response
bound `eta/(1-eta)` is at most `2.702e-15` across the six physical
rectangle/length samples and `1.802e-12` for the retained `2^-40`
generalized section. All are below the `1e-8` development discriminator;
the affected F09 file passes `19/19`. The previously retained weak elbow
still fails the private batch's per-load physical-balance check, so its
failure cannot be attributed to storage of one local basic operator.
Global assembly, factorization/state representation and load-specific
balance need their separate fail-closed screen. These finite samples do
not define a continuous section envelope or accept F09/G0B; the private
`1e-12` pivot guard remains unchanged.

**Next bounded B2 compile decision (27 September):** The private B2 member
currently rebuilds exact-rational local stiffness and 12 station-trace
polynomials for every member, even when an immutable section and length are
shared. Measure cold and warm construction for one repeated physical section
and one varied-length control, keeping evaluation and solve out of timing.
If repeated preparation dominates and immutable sharing preserves
definition-bound ownership, add a caller-owned local-operator cache to the
private G0/F13 seam; if not, leave the operator unchanged and profile a
complete route before optimization. The screen is a development cost check,
not a practical-scale or B2 speedup claim.

**B2 repeated-operator compile slice (27 September):** A single-thread
development screen on the intermediate rotated physical rectangle measured
five warm 12-member construction samples. Rebuilding the same
section/2 m operator took median `0.174493 s`; rebuilding 12 varied lengths
took median `0.187143 s`. Cold first construction was `0.015095 s`.
The private definition now accepts an optional caller-owned cache keyed by
the *same section object* and exact member length. Cached operators are
immutable; compiled members still own distinct frames and definition
identities. A focused ownership/parity test passes `1/1`, including changed
length, value-equal but distinct section, cache clear, and invalid cache
rejection. The first broader definition/F13 process (PID `54444`, exec
session `54296`) remained CPU-active without a collection or test result and
was stopped at the announced 40-minute local resource ceiling. A separate
selected F13 collection likewise exceeded 120 s without JIT disabled and
was stopped. Both are incomplete runner attempts, not numerical failures.
With `NUMBA_DISABLE_JIT=1`, the private assembly import completed in
`0.705 s` and the affected definition/F13 suite passed `36/36` in `9.49 s`.
A new connected, equal-length two-member case verifies one cache hit/one
construction and exact equality of ten batch solutions, assembled matrices,
selected section resultants/strains and one factorization per batch.

Five serial alternating warm component pairs on twelve 2 m members sharing
the declared 40 × 12 mm rotated section measured median private compilation
`0.194872 s` without reuse and `0.017173 s` with the cache (an `11.35×`
component ratio). Raw seconds in paired order: uncached
`[.1939472,.1948717,.1956497,.1945395,.1973137]`, cached
`[.0171726,.0163651,.0171755,.0165009,.0174021]`. The screen ran on
Windows/Python 3.14.2 with JIT disabled and one BLAS/MKL/OMP thread.
This source-run result excludes cold import/JIT, solve,
recovery, shell assembly and installed artifacts. It is not a complete-route
B2 speedup, practical-scale qualification or G1 entry. Keep JIT-enabled
dispatch/verification and production compiler ownership open.

**F13 residual-admission decision (27 September):** The private B2 batch's
fast residual route treats `eps * row_scale <= 1e-9 * physical_scale` as
sufficient to trust a rounded sparse dot. That ignores row length and how
close the rounded residual is to the acceptance threshold. A bounded
synthetic 2,002-entry row with coefficients `1e10`, 2,000 copies of `1e-8`,
and `-1e10` produces rounded residual zero, while its exact small-term sum is
`2e-5`. Here `eps * row_scale = 4.44e-6`, so an applied-scale threshold
`1e-5` would be incorrectly fast-accepted. This is a numerical admission
counterexample, not a physical stiffness matrix or F09 failure. A first
probe importing the full batch helper was interrupted after prolonged
startup and produced no result; a standalone sparse-dot reproduction
produced the values above. Next replace the single-epsilon gate with a
row-operation-count roundoff bound including residual margin. If the bound
cannot certify fast acceptance, use the existing accurate-product/refinement
route and fail closed. Ordinary short rows should retain the fast path.

**F13 independent numerical review:** The row-count bound is appropriate for
ordinary finite binary64 rows, but the existing physical scale samples only
`Fx` and `Mx` (`driving[0::6]` and `[3::6]`), omitting both transverse forces
and both bending couples. Before relying on the new gate, test pure `Fy`,
`Fz`, `My` and `Mz` batch cases and derive the scales from all six nodal
components. A failure of the old path is a real admission defect, not a new
formulation failure. Treat the roundoff gate as a conservative fast screen;
subnormal or numerically marginal rows must take accurate products. Large
graph overhead and formal numerical certification remain unproven.

**F13 pure-load failure and second admission decision:** Before repair, all
four prescribed pure `Fy/Fz/My/Mz` cases failed the batch residual gate,
confirming the missing-component scale bug. After including all six
components, the two transverse-force cases pass; the two pure bending-couple
cases still fail. Independent sparse solutions and the batch's initial
scaled factorization have applied-scale force/moment residuals about
`1e-15`, far below the unchanged `1e-9` private physical-equilibrium bound.
The rejecting rows have `~1e-18` residuals against `~1e-16` local absolute
row scales, so a *per-row* relative backward-error test spuriously rejects
near-zero uncoupled rows. Keep the rowwise applied-physical-scale limit and
use a per-case global backward scale as the supplementary numerical check.
If the repaired route passes, this corrects a false numerical rejection; it
does not relax the registered physical balance criterion or qualify F13.

**F13 reviewer follow-up:** The six-component scale repair and row-count
fallback have no identified correctness blocker. The first per-case backward
supplement uses a raw maximum across force and moment rows, however, and is
not invariant under equivalent units. Before retaining it, normalize each
row's backward scale by its own physical equilibrium scale, take the maximum
of those dimensionless ratios per case, and map that limit back to each row's
units. Keep the independent `1e-9` rowwise physical criterion. Verify the
normalization under a force/moment unit change; zero-scale rows must still
fall back to accurate evaluation. This is numerical screening, not a formal
sparse-backend rounding certificate or a large-graph performance claim.

**F13 private admission result:** The batch now scales all `Fx/Fy/Fz` and
`Mx/My/Mz` components. Its fast residual screen includes row operation count
and acceptance margin; uncertain and tiny-scale rows take the existing
accurate-product/refinement path. The supplementary backward check uses a
per-case maximum of dimensionless row-scale ratios, mapped back to each
row's units, while the separate rowwise physical `1e-9` condition remains
unchanged. All four pure transverse/bending cases, including the two that
still failed after only the component-scale fix, now solve and agree with an
independent sparse solution. The ordinary ten-case fixture keeps one
factorization and makes no accurate-product calls. The 2,002-entry
counterexample is sent to accurate evaluation. Focused F09/F13 tests pass
`43/43`. Independent read-only numerical review found no remaining definite
defect within this private scope. Its rounding allowance is an engineering
screen, not a formal backend certificate; the unit test checks algebraic
row-unit covariance, not a fully converted model. Large sparse cost,
physical-range admission, F13/G0B acceptance and G1 entry remain open.

## F07 free-free descriptor discriminator — 27 September 2026

**Decision sought:** Does the existing native Q4/B3 point-candidate rest
operator retain exactly six physical rigid motions when supports are removed
from its *spectral diagnostic*, with retained cell coordinates, shell
drilling treatment and multipliers kept algebraic? **Established:** The
supported physical-mass descriptor passed its bounded work and eigenvalue
checks, but cannot demonstrate the required free-free modes. **Competing
explanations:** The full reference operators have the six objective null
motions, or an extra/deficient null reveals a kinematic or mass/constraint
problem. **Bounded discriminator:** Use the already captured full K, M and
six exact point rows at the unloaded rest state, without modifying the
supported owner or its admission. Form the small full massless-multiplier
descriptor; count finite near-zero roots, check eigen/constraint residuals
and physical rigid-motion content. Passing permits broader mixed Q4/S3 and
mesh checks; failure sends the exact operator or interpretation back for
diagnosis. This is not a selected point law, production free-free owner or
F07/G0B acceptance.

**Q4 result and immediate S3 check:** The unloaded Q4/native-B3 full
descriptor has exactly six finite near-zero modes after removing supports
from the *diagnostic* matrices; each nodal mode fits a common physical rigid
field and satisfies the eigen/constraint residual checks. The focused test
passed 1/1. Before interpreting this as a formulation-family property,
repeat only the same check on the existing S3-V2D rest fixture, whose shell
rotations are algebraic. An S3 extra/deficient mode would identify its
separate mass/kinematic treatment for review; a six-mode result extends the
bounded observation, without admitting production free-free analysis.

**S3 result and boundary:** The same support-free *descriptor diagnostic*
has exactly six finite near-zero modes for S3-V2D as for Q4. Every mode's
shell and beam nodal field fits one common rigid displacement/rotation to
`1e-8` relative, the six fitted rigid coordinates span dimension six,
and eigen/constraint residuals pass the bounded `1e-8` checks. The three
F07 focused files pass 5/5. The capture still comes from a supported owner
at rest; this is not a public free-free solve, a mixed mesh, an accepted
point-law choice, a large sparse descriptor or F07/G0B acceptance.

**Independent F07 review and bounded follow-up:** The reviewer confirmed
that capture forms full K/M/C before the supported owner's free set enters
the reduced lift, so removing supports in this *diagnostic* is valid. The
six nodal rigid fits are useful, but the eigen residual uses the same
captured matrices and the shell factor is built on a known rigid
complement; neither is an independent formulation oracle. Before relying
on the six roots even as a rest-state descriptor screen, check full rest
residual including reactions, positive mass in the counted subspace and
finite-root count against the constrained mass rank. Failure revises the
screen; passing retains only bounded Q4/S3 evidence. Direct full K/C
annihilation by analytically constructed rigid fields with retained cell
coordinates, unsupported-block independent witnesses, mixed meshes and
production free-free analysis remain open.

**F07 review follow-up result:** Both Q4 and S3 rest fixtures have zero
full-owner scaled residual, including the coordinates held by the ordinary
static fixture. All finite descriptor roots are real within the declared
`1e-8` screen, their number equals the rank of physical mass restricted to
the independent constraint nullspace, and the six near-zero eigenvectors
span a positive-mass rigid subspace. The focused F07 set remains 5/5.
These guards resolve the review's supported-reaction, positive-mass and
finite-count concerns for this diagnostic; the independent full K/C rigid
action and unsupported-block witness remain open. This is not F07/G0B
acceptance or permission for a public free-free owner.

**Next F07 rigid-action discriminator:** The eigenvectors' nodal fit and
positive mass do not directly test the full captured operator on a
mechanically prescribed rigid variation. At unloaded rest, build six
analytic common translations/rotations from the shell and beam reference
points, assigning each of the two native retained cell frames the same
infinitesimal spatial rotation. Check `K R` and `C R` under fixed physical
normalization and compare their six-dimensional image with the counted
eigenspace. A failure identifies a full unsupported block or retained-chart
issue; a pass strengthens only this small rest-state descriptor screen.
Do not infer mixed-mesh, loaded or public free-free qualification.

**Direct rigid-action result:** On both Q4 and S3 rest fixtures, the six
analytic common rigid variations assign their spatial rotation to both
retained cell frames and satisfy the full captured stiffness and point-row
annihilation checks at relative `1e-9`. Their physical coordinate span
matches the six counted near-zero descriptor modes to `1e-8` relative.
The focused new file passes 2/2. This resolves the missing direct K/C
rigid action for these two small rest cases; the capture remains a rounded
diagnostic, and independent unsupported-block assembly, loaded/geometric
terms, mixed meshes, scalable sparse modes and F07/G0B acceptance remain
open.
Independent read-only follow-up confirmed that native cell-frame updates
use left spatial multiplication, so the common infinitesimal rotation is
the correct rest-state retained variation and the new K/C action resolves
the review's specific rigid-action finding. It does not independently
verify the captured rounded unsupported blocks.

**Separate F07 rest-block check:** Direct calls to the existing shell response
and native retained-beam assembly, without spectral capture or its factor
reconstruction, each annihilate six analytic rigid variations on the Q4 and
S3 rest fixtures at relative `1e-9`. The retained beam variations include
both cell-frame rotations and zero resultant changes. Both separate residuals
also vanish at the reference state. The three focused F07 files pass 7/7.
This checks constituent rest blocks independently of the captured combined
matrix, but shares their production kernels; it does not test loaded joint
curvature, mixed meshes, scalable sparse modes, or F07/G0B acceptance.

## F12 constant-axial prestress discriminator — 27 September 2026

**Decision sought:** Does the retained physical B2 station displacement
trace support a conservative, representable member geometric stiffness for
one declared constant axial prestress, without adding inertia or changing
the historical B2 route? **Established:** The private operator owns exact
polynomial station maps; physical section mass and a bounded massless KKT
descriptor have passed, but prestress and buckling have not. **Competing
explanations:** The trace derivative gives the expected second variation of
transverse centerline stretch, or it produces an inconsistent energy or
nonconvergent buckling mode. **Bounded discriminator:** Integrate
`N ∫ (Dv'ᵀDv' + Dw'ᵀDw') dx` from the existing trace coefficients; compare
its quadratic work to independently differentiated station displacements,
test symmetry/rigid translation, and check a slender cantilever's first
compressive factor over 1/2/4/8 elements against the analytic Euler limit.
**Action:** Passing permits later assembly, attached prestress, frame,
external-load and descriptor work. Failure revises the candidate operator.
This is not production buckling admission or F12/G0B acceptance.

**Initial buckling screen:** The energy/rigid-translation check passed, but
strict monotone convergence to the Euler–Bernoulli critical force failed:
relative 1/2/4/8-element errors were `0.00748515`, `0.000469753`,
`0.0000112182`, `0.0000423455`. The final upward error is of the same
order as the finite-shear correction for the declared physical B2 section;
the Euler comparison is not a matched asymptote. Retain this failure and
compare the unchanged candidate against the [Engesser shear-corrected
cantilever critical force](https://www.sciencedirect.com/science/article/pii/S0997753816303096)
`P_EB/(1+P_EB/(kGA))`. A nonconvergent result against that matched limit
requires revising the candidate; a pass advances only bounded F12 work.

**Matched F12 result:** The constant-reference-axis axial term integrates
the exact retained B2 transverse trace slopes in rational arithmetic and
returns a physical 12×12 tangent. Independent station-difference work
agrees for scalar and off-diagonal generalized sections; the matrix is
symmetric, changes sign with axial force and annihilates rigid transverse
translation. A 1/2/4/8-member cantilever gives a monotone decreasing error
against the matched shear-corrected critical force, with the 8-member error
below 1%; each selected generalized eigenpair satisfies a `1e-8` scaled
equation residual. A tilted member and its reversed equivalent have the
same global prestress work after node permutation. The bounded file passes
4/4. This does not include follower/external geometric terms, variable
prestress, attachment curvature, shell coupling, massless-descriptor
buckling, or independent acceptance. F12/G0B remain open and G1 barred.

**Independent F12 review and next discriminator:** Read-only mechanics
review found no algebraic error in the stated member-only term or its
global congruence. It noted that the original slender case has
`P_EB/(kGA)≈4.45e-5`, far below its 1% error bound; that screen alone cannot
separate the Engesser limit from Euler. The station-difference check reuses
the same trace coefficients, and reversal currently covers one isotropic
tilted member. On the same length and material, run one declared stockier
radius with 1/2/4/8 members and compare the unchanged candidate to both
Euler and Engesser; require the finer mesh to move materially toward the
shear-corrected limit. If it does, retain the narrow member result; if not,
revisit the geometric energy/trace before any attached buckling claim.
The axial force here means an equilibrated conservative resultant on the
reference centerline. Eccentricity, variable force, attached curvature and
external/follower load terms remain separate.

**Stockier result:** With radius `.05 m` instead of `.005 m` at the same
`1 m` span, the Engesser/Euler separation exceeds `0.3%`. The unchanged
candidate's first compressive factor converges monotonically across
1/2/4/8 members and the 8-member relative error to Engesser is below
`1e-4`, less than one tenth of that separation. The slender case also
meets the stronger `1e-4` bound; all selected eigenpairs retain the
`1e-8` equation-residual check. The focused file passes 5/5. This
distinguishes the chosen shear-corrected continuum limit in these two
bounded circular sections. It does not qualify arbitrary sections,
prestress distributions, shell attachments or production buckling.

**Next bounded F12 descriptor composition:** Physical B2 mass, a constant
member axial geometric term, and point-multiplier curvature each passed
separate small checks, but have not entered one constrained descriptor.
On the existing Q4/physical-B2 point specimen with the same explicit
supports, add one declared compressive axial term and nonzero point
multiplier curvature to its reference tangent. Check that both survive
constraint projection, multiplier rows remain massless, finite eigenpairs
match an independent nullspace reduction, and equation/constraint residuals
meet the existing `1e-8` screen. Failure isolates assembly or descriptor
treatment; passing is only a provisional point-law algebra check. It does
not establish an equilibrated loaded shell/beam state, selected connection
law, attached buckling prediction or F12/G0B acceptance.

**F12 composition result:** The same Q4/physical-B2 point specimen now
combines a declared compressive member axial term, nonzero objective joint
multiplier curvature, physical shell/beam mass and massless multiplier rows.
Both geometric contributions remain nonzero after the exact point rows are
eliminated. The descriptor has the expected finite-root count; each finite
eigenpair meets the bounded `1e-8` equation and constraint residual screen,
and its roots match a separate constrained-nullspace reduction. The focused
F12 and point-attachment files pass `15/15`. This checks composition of
existing candidate operators, not an independently equilibrated prestressed
mixed state or a physical buckling prediction. Selected connection law,
attached material/geometric prestress, loaded curvature, sparse production
spectra and F12/G0B acceptance remain open.

**Next F12 physical-mass admission decision:** The private B2 mass record
currently requires only a positive-semidefinite six-channel matrix. That
does not prove a rigid cross-section's physical kinetic inertia: its
translation block must be scalar mass, translation/rotation coupling must
encode a first mass moment, and its central second-moment tensor must be
positive semidefinite. Check those structural identities for owned metadata
without inferring mass from stiffness. Preserve admitted particle-derived,
offset and reversed examples; reject deliberately PSD but physically
impossible matrices. A pass strengthens the B2 mass contract, while a
rejection of a valid particle example requires revisiting the numerical
admission arithmetic. This remains private F12 feasibility, not production
mass, spectra, or G0B acceptance.

**F12 rigid-mass admission result and review:** The private `MassMetadata`
record now requires scalar translational mass, a skew first-moment block,
and a numerically nonnegative central second-moment tensor, in addition to
the existing exact full-matrix PSD check. Centralization uses rational
arithmetic on the supplied binary64 entries so an offset cannot mask a
negative central mode through floating subtraction. A first version scaled
its negative-eigen tolerance by the inertia about the *declared origin*;
independent mechanics review found an exact PSD matrix with center at
`10^7 m` and impossible central covariance `diag(-1,1,1)` that it would
admit. The corrected central-scale check rejects that case and a separate
large-central-inertia negative mode, while admitting the exact distant
point mass and existing particle, offset and reversed records. The focused
definition/mass tests pass `12/12`, and the affected B2 definition, F12 and
F13 tests pass `37/37` after tightening the central tolerance from `128`
to `16` binary64 epsilons. The read-only follow-up found no further defect
in the reviewed rigid-section contract and did not run tests. Very small negative
central eigenvalues relative to the central scale remain within the stated
roundoff allowance. Generalized or added mass is not admitted by this
private record; it would need a distinct contract. Physical density,
cross-section geometry, attached modes, scale and F12/G0B remain open.

## F13 affine factorization dependency slice — 27 September 2026

**Decision sought:** Can the private B2 route reuse an unchanged sparse
factorization when only an audited prescribed value changes, while rebuilding
for a structural MPC change? **Established:** The real common constraint
auditor supplies the B2 graph's affine `T` and `u0`; a value-only change keeps
`T`, whereas an MPC coefficient change alters it. The private batch already
owns its operator and affine arrays and certifies its reduced residual.
**Competing explanations:** Cached factorization may be safely keyed by the
scaled reduced matrix, or hidden structural/prescribed dependencies may make
that key insufficient. **Bounded discriminator:** Recompile the same physical
two-member graph with a local owner-supplied factorization cache under the
original plan, a value-only offset change, and a changed MPC coefficient.
Compare each selected solution to independent audited affine solves, check
cache hit/miss counts, and retain cancellation/invalid-plan behavior.
**Action:** If value-only reuses the factorization and structural change
misses with solution parity, retain this private seam for G1 owner design. If
not, fix the identified dependency before any public route or performance
claim. This does not close F13 or admit G1.

**Result:** A caller-owned, local `FactorizationCache` now enters the private
B2 batch through the existing `factorize_cached` service. On the audited
two-member graph, first/value-only/changed-MPC constructions produce cache
`(hits, misses)` of `(0,1)`, `(1,1)`, and `(1,2)` respectively. The value-only
batch retains the original handle even after the previous batch closes;
changed MPC gets a different handle. All three selected solutions match
independent audited affine solves, and mutation of the caller's prescribed
array after construction does not change the batch. The focused F13 suite
passes 10/10, including earlier cancellation and numerical-failure checks.
This demonstrates dependency-key feasibility only. The private result's
handle counters are not yet per-owner accounting across cache reuse;
production diagnostics and owner/cache lifetime remain G1 design work.

**Next F13 decision:** Can the same bounded B2 batch return requested local
member resultants/strains without retaining full-model solutions for every
case? A selected result must come from the solved physical affine state, not
the reduced vector or an unowned caller array. Compare requested stations
against an independent per-case full-state element evaluation for both
member orientations; verify a 100-case selected route, invalid requests,
and complete-case cancellation. If parity holds, retain the opt-in local
recovery seam; if not, correct the physical/state mapping. This is private
feasibility, not B07 or G1 acceptance.

**Result:** The private batch now accepts requested compiled member IDs and
normalized stations, reconstructs only those members' physical nodal states
from each solved affine column, and returns owned local section resultants
and strains with each complete case. The local operator has a section-only
path so recovery does not recompute its full tangent. A 100-case, two-member
screen matches independent full-state `evaluate` results at both requested
stations; invalid member/station requests are rejected before publication.
Cancellation still returns only a complete ordered prefix, and mutating the
caller station list in a callback does not alter later results. This is local
section recovery only, with no coupled reaction or public B2 B07
qualification.

A cancellation injected during section recovery now discards that incomplete
case before callback/publication. The focused F13 file passes 13/13 after
this safe-point check; earlier completed cases remain a whole ordered prefix.

**F13 ordered-input discriminator:** The private batch previously validated
case IDs before solving but sliced the caller's sequence between chunks. A
callback could replace or remove a future pair after validation, changing the
promised ordered inventory. The batch now freezes case IDs and load references
before callbacks, while copying numerical loads only at each bounded chunk.
On the ten-case elbow, a callback replaced case six and removed the last
submitted list entry; all ten original IDs and selected results still matched
independent sparse solves. The focused F13 file passes 14/14. This establishes
outer sequence ownership, not invocation-time ownership of mutable numerical
arrays or F13 acceptance.

**F13 active-owner guard:** The private batch now rejects `close` and
recursive `solve_many` while an operation holds its factorization. A callback
that catches either error leaves the ten-case result complete; a callback
exception releases the operation guard so a subsequent solve can run, and
closing afterward still rejects use. The focused file passes 15/15. This is
bounded single-owner lifetime evidence, not concurrent throughput, public
B2 dispatch, or F13/G0B acceptance.

## Native connection decision record — 27 September 2026

**Decision sought:** Select the physical native beam–shell connection and its
exact line enforcement before G1 integration. **Established:** C1 is a
six-channel reduced finite-strip *rotational-weld* candidate, not the same law
as the F5 top-face positional bond. Its pitch couple acts even when that face
is positionally fixed. Loaded wrenches close; the drill-quotient KKT screen
isolates a growing P0 line mode, while P1/dual do not show the same decline
on the tested grid. Neither that result nor small weak gaps selects a line
space. The saved F5 common work exposes a transfer-shape difference, but its
sided cut lacks the conforming plate/seam virtual work needed to score native
B3 ports. Independent Q4/S3 plastic, rebase and native descriptor development
has advanced; the private native B3 sparse adapter now enforces its owners'
admission and passes bounded loaded-state tangent checks. B2 has a private
eccentric Q4 point candidate, matched
low-mode mass convergence, an explicit mass-origin pullback, a bounded
physical Q4/B2 massless-multiplier descriptor check, and a private scaled
affine batch route. **Remaining uncertainty:**
Whether the primary joint is a top-face positional bond, an intentional
through-thickness rotational weld, or both separately admitted; its matched
torque/shear transfer and growing-space stability; remaining G0 foundations.
**Next discriminator/action:** Keep the existing physical-joint clarification
pending. Once specified, compare that exact law's continuous work and
physical transfer against the matching reference, then assess growing-space
line stability and registered ratios. Do not resume classical axial
refinement or infer a multiplier choice from one quotient. Independent B2 and
state foundations may advance meanwhile. **Gate:** G0B open, G1 barred;
formal F03 authority unconsumed.

**Next bounded physical discriminator:** The validated F5 common-action
comparison shows a low-order transfer-shape difference, but it cannot assign
that difference to shell response, native B3 one-sided ports, or reduction of
the solid bond to six line components. The existing
`f03-c1-factor5-native-six-gap-dev-20260926-v6` already projects the saved
face onto the candidate rows, measures Q4 proxy errors, and rejects direct
replacement of the pitch row by a longitudinal-position moment (rank 11/12).
Do not repeat it. Its face/section fit is kinematic and its weak rows alone
do not measure whether excluded transverse deformation carries physical
interface work. On the same saved pre-opened F5 field, use the independently
validated bar-on-plate bond nodal action to calculate work on a transverse
affine projection and its complement at the actual shared face nodes. Check
that the action and virtual fields recover the known bond wrench and work.
If the complement carries material work, the reduced transverse idealization
needs correction or a declared bound before choosing an enforcement space.
If it is negligible, prioritize the already observed same-action E4 response
and obtain a sided B3 reference only if that remains necessary. This is a
single finite-grid discriminator, not a six-channel law qualification or
substitute for the required shear/director and mesh-ratio checks. No new
external solve or axial refinement follows automatically.

**Result and action:** The source-bound saved-stress run is
`B3_GE_E4_PL_F03_C1_F5_TRANSVERSE_WORK_DEV_V2.json`; V1's mismatched
rounded-FRD force reconstruction stopped at its archive guard and is retained
in `B3_GE_E4_PL_F03_C1_F5_TRANSVERSE_WORK_DEV_V1_FAILURE.md`. V2 exactly
reproduces the validated F5 seam wrench and `0.0152174641 J` bond work.
Fitting translation independently at all eleven x stations as an affine
function of transverse y leaves a `13.30 nm` weighted component RMS and
`111.47 nm` maximum vector residual. Its omitted signed weak work is
`-4.119e-5 J`, `0.271%` of the signed bond work. A quadratic y fit leaves
`5.06 nm` RMS and `-6.813e-6 J`, `0.0448%` of bond work. Thus this saved
F5 field does not expose a large work contribution from transverse
*face-position* content outside an affine section trace. The inference is
limited to one mesh, one pre-opened combined load and a fitted face field;
the E4 director-pitch and native B3 retained one-sided rotations are not
represented by that projection. It cannot establish six-channel fidelity or
select P0/P1/dual. The existing same-solid-action E4 response and the
missing sided B3 port work are now the discriminators; do not launch another
transverse or classical axial refinement from this small remainder.

**One bounded sided-reference execution (prospective):** The saved F5
quadratic-solid grid places x=`0.95 m` inside a `.94–.96 m` element, so
its integration-point stress cannot supply exact element-side virtual work
for the native B3 retained-port cut. Insert `0.95 m` as a base cut in both
solid domains while retaining the declared C1 geometry, supports, bond,
pre-opening, loads and element family. The opt-in generator must reproduce
the old deck and model with the flag off, and the new mesh must have no
element crossing the cut. Execute only this combined case, with one thread
and the existing 120 s limit, saving the full displacement and stiffener
Gauss-stress output. A completed, balanced, open field with recoverable
side contributions advances to one-sided work; timeout, failed mechanics or
inconsistent side action stops this reference rather than triggering a finer
run. This is preparatory Level-A external evidence, not the consumed formal
F03 gate execution or a multiplier selection.

**Sided-reference result and decision:** The opt-in generator preserves the
historical F5 deck text and JSON model with the flag off. Its new x=`.95 m`
base cut puts no plate or bar element across the section; the declared load
resultant remains `(0,0,-1000 N; 100,1000,0 Nm)`. The pinned CalculiX 2.23
one-thread run completed in `94.46 s`, inside the existing 120 s cap.
Protected raw root:
`.qualification/b3-ge-e4-pl/f03-c1-factor5-sided-port-cut-dev-20260926-v1`.
Versioned validation is
`B3_GE_E4_PL_F03_C1_F5_SIDED_PORT_DEV_V3.json`; V1/V2 remain unchanged.
Printed Gauss-stress recovery gives maximum free-bar residual `4.23e-5 N`,
bar-root RF difference `5.67e-5 N`, and bond-versus-independent plate-support
wrench difference `1.73e-4 N/Nm`. The sampled unbonded reference-normal gap
is positive at all recorded points, minimum `3.48 nm`; this is not a
continuous deformed-intersection certificate. Applied-load work is
`0.074348233 J` versus archived F5 `0.074342088 J` (`+0.0083%`) on the
changed terminal mesh, supporting a close directional comparison only.

The stress-conjugate *broken-space* unit section twist at x=`.95 m` gives
left/right element-side work duals `+57.4160/−58.2776 Nm`. The cut contains
`341` bar nodes, including `21` shared with the bonded plate; their
bar-on-plate interface action has `+0.861539 Nm` about the same axis.
The displayed left/right/seam closure is algebraic bookkeeping, not an
independent traction validation. Independent read-only mechanics review
confirmed Gauss ordering, force sign and the bounded broken-space work
interpretation, and identified that a side-restricted twist at shared nodes
is **not an admissible variation of the intact bonded assembly** when the
plate is held fixed. V3 makes this limitation explicit and narrows the
status to passed stress/reaction and sampled-gap guards. These numbers
cannot score the native B3 retained port or select P0/P1/dual. Before any
native comparison, derive a port-to-solid virtual displacement/warping map
with the companion plate/seam work and test its representable work. If that
map is not defensible, use only the already validated continuous common
fields and same-action shell response; do not request another finer solid
solve just to obtain a different scalar. G0B remains open and G1 barred.

**Native-port trace compatibility audit:**
`scripts/b3_e4_f03_c1_port_trace_compatibility.py` and its V1 JSON bind the
above cut and actual B3 half-cell spatial ports. Independent read-only review
identified a needed distinction: V1's twelve coordinates are those of two
*formal* independent rigid poses. Actual B3 endpoint ports share all three
translation tangent rows; their paired image has dimension nine, with three
independent relative retained rotations. The source-bound
`scripts/b3_e4_f03_c1_port_trace_compatibility_v2.py` and V2 JSON check this
actual image and bind the V3 F5 validation status and input hashes. Under an
*assumed* rigid-section extension to all 341 common solid cut nodes, relative
rotation trace rank is three and continuity leaves a six-dimensional native
compatible image. The 21 plate-bonded nodes alone have formal pose rank five,
but their relative-rotation trace rank is three; neither rank supplies a
unique physical extension of the native spatial port.
For a declared equal-side projection of a left-only unit twist, the omitted
*bar-only broken-space* work is `57.8468 Nm/rad`; this depends on the chosen
projection and excludes unknown side allocation of plate/seam work. It is
not an admissible intact-assembly work error or a bound on connection error.
The bounded decision is to stop direct sided-port accuracy scoring until a
conforming extension and complete work map are specified. This is not a
failure of the native beam or of the connection law. Preserve V1 as the
original formal-pose calculation and use V2 for the native interpretation.
Preserve the validated
common-field F5 comparisons and proceed to the physical trace/torque/shear
decision. G0B remains open, G1 barred.

**Next bounded continuous-law discriminator (before execution):** The C1
hybrid's independent director-pitch row may encode a real local rotational
weld idealization or may overconstrain what is meant by a top-surface
positional bond. On the unchanged C1 Q4/native B3 reference, prescribe a
supported E4 director-pitch field and exactly compensate each midsurface
translation so every shell-top surface point stays fixed while the beam stays
fixed. Measure all six continuous hybrid gaps, the sampled top-surface gap,
and physical E4 strain energy. A nonzero pitch row with zero top-surface
position gap establishes that this row is an extra director-couple law, not
an equivalent representation of surface-position traction. It does not by
itself prove that the idealization is wrong: keep it only with an explicit
physical connection and work reference; otherwise revise that component
before multiplier selection. If the pitch row also vanishes, investigate the
operator rather than attributing the F5 transfer difference to this channel.

**Compensated-director result and action:**
`scripts/b3_e4_f03_c1_director_compensation.py` and
`B3_GE_E4_PL_C1_DIRECTOR_COMPENSATION_DEV_V1.json` show a supported actual
E4 rotation field with midsurface translations chosen so every nodal and
interpolated shell-top position is unchanged while the B3 reference stays
fixed. The current continuous C1 gap changes only in director pitch:
`+96.667 µrad`; its other five channels change by zero. The reference-state
physical E4 quadratic energy is positive (`13.9315 J`) and excludes numerical
stabilization. Independent read-only mechanics review found no blocking
defect and confirmed the complete interpolated top surface remains fixed.
This proves C1 includes an independent director-couple idealization that a
bond defined solely by top/bottom surface positions does not contain. It does
not imply a full face bond cannot transmit moments in other fields, nor that
a deliberately rotationally welded line is wrong. Resolve the intended
physical rotational connection and its work reference before treating F5
positional-bond agreement as an accuracy score; keep the registered torque,
shear and growing-space checks. No multiplier or formulation is selected,
F03/G0B remain open and G1 remains barred.

**Bounded native stability discriminator (registered before execution):** The
actual retained KKT minimum is dominated by E4's numerical drilling chart,
while the physically positive trace quotient declines for growing P0 rows.
Distinguish a drill-norm artifact from a line-coupled weak mode on the same
C1 Q4 x8/y4, B3-12, P0/P1/dual m4/m8 fixtures. Verify the line rows have
zero drilling columns. Eliminate *only* the unconstrained drilling coordinates
by the exact Schur complement of the actual shell tangent, retaining the
native B3 retained variables and actual indefinite mixed operator. Use the
physical E4 energy on the remaining coordinates and the existing reviewed
beam/line norm contracts, with no drilling coefficient tuning or product
change. Check Schur reconstruction, transpose work, constraint rank and
weakest-mode split. A line-dominant decline would send the law or resolution
policy back for revision; absence of it would isolate the old KKT minimum
from interface stability but would not offset the positive-trace concern or
select a space. Preserve the 120 s and 1900-row diagnostic bounds.

**Drill-quotient result and action (27 September):**
`B3_GE_E4_PL_C1_DRILL_QUOTIENT_DEV_V2.json` retains the six finite-grid
native KKT cases and captures exact source hashes, Python/package identities,
effective one-thread pools, and configured environment inside the target
process. V1 has the identical six minima but only an incomplete retrospective
provenance sidecar; it is preserved and is not the source-bound evidence.
An intermediate V2 attempt computed successfully but could not write its
result under the filesystem sandbox; the permitted rerun saved the result.
Exact elimination
of 198 free E4 numerical drilling rows leaves 990 physical E4 rows and the
216 complete native B3 rows. The line rows have zero drilling columns;
Schur-action error is `3.66e-16`, drilling equilibrium error `1.25e-15`,
and all normalized line row sets have full rank. From m4 to m8, the
smallest normalized singular value changes P0 `0.0152313→0.0122832`,
continuous P1 `0.0152309→0.0152539`, and dual P1
`0.0152269→0.0152451`. The P0 m8 weakest vector is `98.78%` line-dual
in this declared metric; P1 and dual P1 remain about `98.37%` native beam
kinematic. The earlier drilling-dominated minimum masked this P0-specific
finite-grid weak mode; drilling removal does not erase the positive-trace
concern. Work transpose agrees to `5e-18 J` in the bounded tests.
Independent read-only review found no algebra/indexing blocker in the exact
drilling elimination, while noting this metric cannot establish uniform
stability or physical fidelity. Do not select or reject a multiplier from
one grid or one singular value. Prioritize P0's growing-space
resolution/locking test only after the rotational-weld work reference is
defined; carry P1 and dual P1 as comparators through the registered
ratios and refinement levels. G0B/F03 remain open and G1 remains barred.

**Next physical-work discriminator (before execution):** C1's pitch row
acts while every shell-top point remains fixed, so a top-surface positional
bond cannot supply its work. Competing interpretations are a realizable
through-thickness force couple in an explicitly embedded/stitched joint,
or a purely kinematic rotational constraint with no such face-action
representation. On the unchanged C1 reference and one small finite-rotation
state, compare the actual E4-chart pitch derivative with the independently
derived top/bottom face-pair virtual work. Check resultant force/moment and
the already established compensated top-fixed field. Equality permits a
specific two-sided reference definition; failure sends the pitch law back
for mechanical revision. This is a kinematic work identity, not proof that
the intended stiffener is physically two-sided, nor a substitute for a
loaded matched reference, torque/shear or mesh-ratio acceptance.

**Two-face pitch work result and decision (27 September):** Source-bound
`B3_GE_E4_PL_C1_PITCH_FACE_PAIR_DEV_V1.json` evaluates the unchanged C1
patch and actual E4 additive-chart pitch derivative. Independently, an
equal/opposite top/bottom face-force pair uses the physical director
separation `t n` and the derivative of `atan2(x_b·n,z_b·n)`; its net force
vanishes and its moment is `1 N·m` about y at reference. Three finite-
difference steps at reference and at a nonzero rotated state reproduce the
actual pitch work with maximum normalized discrepancy `4.23e-10`. For the
supported compensated field, the top-face-only work is `5.46e-22 J` while
the pitch and two-face work are both `9.66667e-5 J` per unit pitch dual.
This supplies an explicit *two-sided/through-thickness* work interpretation
for the extra C1 row. It does not make a top-face welded stiffener into that
idealization. Keep C1 labelled as an embedded rotational-weld candidate;
define a resolved two-sided reference with matched geometry, loading and
supports before assessing its physical torque/shear accuracy. The existing
F5 top-surface positional bond remains a separate comparator. No formal
F03 authority was consumed, no multiplier was selected, and G0B/G1 status
is unchanged.
Independent read-only mechanics review found the top/bottom pair and its
zero-force, pitch-work interpretation correct. It emphasizes that this is
an analytical representation of the *same* pitch functional, not an
independent physical material or loaded reference.
For a top-face-only position bond at fixed longitudinal station, a purely
transverse lever arm `(0,y,0)` produces no pitch moment about y from
`r × F`; pitch transfer comes from longitudinally separated vertical
forces. Thus a local independent My row requires a declared director/
through-thickness couple, or a longitudinally nonlocal position law.
The previously tested longitudinal-moment replacement lost one row of
rank in its bounded two-interval layout. Do not repair that by relabelling
the C1 director row as a surface-position weld.

**Native KKT metric result:** Commit `2028c8d8` preserves the failed V1
layout check and the completed V2 source/manifest/result in
`B3_GE_E4_PL_G0_F03_C1_NATIVE_MIXED_METRIC_DEV_V2`. The actual supported
KKT uses 1,188 E4 and 216 complete native B3 primal coordinates, including
retained half-cell rotations and generalized resultants, plus 24/30 or
48/54 line rows. With its declared auxiliary physical/unit Riesz factors,
the m4→m8 smallest singular values are P0 `0.00187656→0.00187923`, P1
`0.00187669→0.00188061`, and dual `0.00187673→0.00188068`. Every weakest
vector has about `99.93%` of its norm in shell numerical drilling chart
coordinates and at most `0.0051%` in the line dual. The work transpose,
constraint ranks and scaled SVD residuals check numerically, but the
minimum is governed by the auxiliary drilling norm, not the growing line
space. This cannot offset the positive-trace P0 decline or establish native
line stability. Preserve the raw V1/V2 evidence. Any next stability metric
needs a physically justified treatment of the E4 drilling coordinate and
independent norm review; do not tune a coefficient just to expose a desired
singular mode.

**Next independent F09 discriminator:** The bounded six-case B2 scaling
screen passed exact rounded and independent force-method oracles, but held
`Iy=Iz=J=1 m^4` while area tended to zero. That is a numerical stress
family, not physical section admission. On the same two-member elbow,
use a declared series of square sections with area, bending inertias and
torsion linked to the side length, fixed mixed physical terminal loads,
and a narrow independent force-method oracle. Check each nonzero response
component, separate force/moment residuals and representability guards.
Agreement permits a draft physically bounded scaling policy for further
generalized SPD/attachment tests; failure separates operator, rounded
assembly and sparse factorization errors. This is one G0 preparatory screen,
not a production admission, B2 speed claim or G1 entry.

**F09 square-section result:** The source-bound
`B3_GE_E4_PL_G0_F09_SQUARE_SECTIONS_DEV_V1.json` tests side lengths
`0.04/0.08/0.16 m` with `A=b²`, `Iy=Iz=b⁴/12`, the Fourier Saint-Venant
square `J`, `E=210 GPa`, `ν=0.3`, fixed terminal
`(50,-30,100 N; 2,-3,5 Nm)`, and the existing rooted two-member elbow.
All 3/3 pass the declared componentwise `1e-8` and separate force/moment
residual `1e-10` diagnostic limits. The maximum scaled-vs-independent
force-method component error is `8.39e-13`; maximum free force and moment
residual ratios are `2.33e-12` and `9.10e-14`. The record also retains the
exact solve of the rounded assembled graph and complete tip vectors. This
removes the earlier geometric-inconsistency objection for these finite
square cases, but does not define the full physically admitted section
range or cover off-diagonal generalized SPD, new attachments, mass,
prestress, installed behavior, or B2 speed. F09/G0B stay open. Proceed to
those missing contracts rather than another smaller square-section sweep.

**F09 generalized-section result:** Source-bound
`B3_GE_E4_PL_G0_F09_GENERALIZED_SPD_DEV_V1.json` adds two signs of
dimensionally scaled off-diagonal `N–My`, `Vy–Mz` and `Vz–T` coupling to the
0.08 m square-section diagonal. A separate exact rational inverse of the
six-by-six section and cut-wrench Castigliano derivative supplies the
physical response oracle; a rational solve of the rounded global graph
separates operator from sparse-factorization error. Both 2/2 oriented-elbow
fixed-load cases pass the declared `1e-8` component and `1e-10` separate
residual limits. Maximum scaled-versus-independent component error is
`3.73e-13`; force and moment residual ratios are `2.55e-13` and
`1.53e-13`. This covers one modest SPD coupling family of both signs,
not the full admission range, member reversal, attached shell, mass,
prestress, public dispatch, installed package or speed. F09/G0B stay open;
next work should target those missing contracts, not repeat these elbow
loads at more side lengths.

**F09 coupled graph reversal result (27 September):**
`B3_GE_E4_PL_G0_F09_GRAPH_REVERSAL_DEV_V1.{md,json}` tests two mixed
terminal wrenches on a two-member generalized-SPD B2 elbow. Reversing the
second member while explicitly transforming its six-channel section tensor
preserves the assembled matrix and tip response to binary64 reporting
precision; an independent rational cut-wrench compliance integral agrees
with the sparse work within `4.44e-16` on the declared unit-floor measure.
Keeping the tensor unchanged changes the matrix by `9.35%` and the work by
`0.75%/0.16%`, showing that the loads expose the orientation error. The
five-station pose/Jacobian/work pullback also passed, as did `29/29` focused
private B2 tests. This establishes a bounded explicit section-axis reversal
contract, not a physical admission envelope, shell attachment, mass,
prestress, installed behavior, speed or F09/G0B acceptance.

**Next bounded B2 F12 mass-contract discriminator (before execution):**
Can the implemented physical station trace, paired with separately supplied
section mass at an offset mass center, reproduce the independently derived
six-rigid-motion spatial inertia of one straight member? Compare four-point
integrated trace mass against an analytic rod/parallel-axis inertia, verify
station rigid velocities, and reverse member connectivity with the mass-center
coordinates transformed into the new local frame. Failure distinguishes a
trace/frame/offset defect from a metadata-definition ambiguity before any
coupled modes are implemented. Passing would establish only this local rigid
kinetic identity; it would not select a dynamic interpolation, qualify
deformational mass, prestress, buckling, attachments or F12/G0B. Keep the
declared 6x6 mass metadata independent of stiffness and invent no inertia.

**B2 F12 local rigid-mass result:** Source-bound
`scripts/probe_b3_ge_e4_pl_g0_f12_b2_rigid_mass.py` and
`B3_GE_E4_PL_G0_F12_B2_RIGID_MASS_DEV_V1.json` use a 2 m rectangular
member, 7850 kg/m³ density, and an explicitly offset mass center. The
four-point integrated station-trace mass reproduces the independently
derived rigid spatial inertia to `9.74e-17` relative, the reversed-member
global matrix to `1.51e-16`, and rigid station velocities to `2.23e-16`
absolute; the bounded matrix is symmetric and has minimum eigenvalue
`0.00558`. The first script invocation failed before writing evidence because
its local `np.block` argument used a tuple; the repaired source generated
V1, which reproduces from the current source. This is a local rigid-motion
identity only. The cubic static trace has not been accepted as the dynamic
mass interpolation; deformational modes, coupled algebraic variables,
prestress, buckling, attachment effects and independent review remain open.
No F12/G0B status change follows.
Independent read-only review found no mechanics error in the spatial-inertia
formula, single offset application, reversal frame or exact-degree quadrature.
Its analytic oracle reuses the supplied section mass matrix and member frame,
so it validates the trace against that metadata, not the physical derivation
of density-to-section inertia. That narrower interpretation is retained.

**Next F12 dynamic-interpolation discriminator (before execution):** The
rigid mass identity does not show that the physical B2 static station trace
is an adequate deformation velocity interpolation. Compare its assembled
mass and stiffness on a uniform slender cantilever at 1/2/4/8 straight
elements, with explicit density and section inertia, against the analytic
Euler–Bernoulli first bending frequency. The competing outcomes are
convergent low-mode behavior, which permits a broader modal and shell-
attachment assessment, or a persistent bias/nonphysical mode, which sends
the dynamic interpolation back for revision. Inspect mass positivity,
symmetry, mode shape, and equation residuals; the analytically slender
limit is not a full Timoshenko qualification. This is a bounded G0
development check, not a B2 spectral admission or F12/G0B acceptance.

**F12 V1 result and revised discriminator:**
`B3_GE_E4_PL_G0_F12_B2_DYNAMIC_MASS_DEV_V1.json` preserves the failed
strict-monotonic Euler–Bernoulli screen: relative first-frequency errors
at 1/2/4/8 elements are `0.0047362/0.00046423/0.000012965/0.000017811`.
All masses are positive, modes have small nodal-shape discrepancies and
eigen-equation residuals remain below `7e-10`. The final small increase
may be the physical shear/rotary-inertia offset from the Euler–Bernoulli
asymptote, not a dynamic-interpolation failure. Before changing the
interpolation, construct one *independent* high-order Timoshenko
Rayleigh–Ritz reference with the same E, G, shear factor, density and
rotary inertia. Confirm its polynomial-order convergence, then compare
the unchanged B2 mesh results against it. Convergence toward the matched
reference permits broader F12 checks; persistent nonconvergence or
nonphysical modes requires revising the mass interpolation. Keep V1 as
failed evidence; no tolerance or scientific gate is relaxed.

**F12 matched-reference result (27 September):** V2 is retained as a failed
binary64 polynomial Ritz attempt; severe bending/shear conditioning made its
high-order estimates nonmonotone, so it is not a reference. V3 introduced an
independently assembled 60-digit Decimal Timoshenko Rayleigh–Ritz model.
Independent review found its energy integrals and inverse iteration sound,
but V3 converted the order-10/12 convergence difference to binary64 before
reporting it as zero. V4 retains the exact Decimal eigenvalues and records the
relative frequency change as about `1.015e-17`, rather than zero. Its
monotone Ritz upper bounds converge to `13.12400219865733 rad/s`. The
unchanged physical B2 1/2/4/8-element first-mode errors against that matched
reference are `0.0047563/0.00048418/0.000032911/0.0000021350`; reduced
mass is positive and equation residuals pass the bounded screen. V1–V3
remain as historical failed or superseded diagnostics, and V4 is the
interpreted comparison. This supports proceeding to mixed shell/attachment
mass, prestress and spectral algebra checks, not B2 modal/buckling admission
or F12/G0B closure. The scalar cantilever comparison does not validate
section mass-center, frame, reversal or parallel-axis metadata.

**F10–F11 private B2 point result (27 September):** A physical B2 station
trace was coupled to a finite four-vertex Q4 translation fit through the
reference differential of the existing objective point law. The bounded
development tests check the beam trace and composed actual joint derivative,
nonzero-multiplier work, global force/moment balance, sparse KKT against an
independent dense reduced solution, support reactions and invalid geometry.
The focused B2 definition/trace set passed 15 tests. The private source and
limits are in `B3_GE_E4_PL_G0_F10_F11_POINT_DEV_NOTE.md`. This identifies a
viable finite-support point *candidate*, not a selected shell point port,
nonmatching line law, S3/generalized-section admission, or F10/F11/G0B
qualification. Further point work depends on the primary physical connection
choice; independent B2 mass and state foundations may continue meanwhile.

**Next independent F12 metadata discriminator:** The matched cantilever used
centered inertia and cannot establish the mass-center/section-origin contract.
On one explicitly eccentric section, derive the 6x6 velocity-order inertia
from density, center offset and centroidal tensor, then test rigid translation,
rotation, cross work, frame rotation and member reversal against direct
particle-level kinetic energy. Check whether the current exact-PSD metadata
admission accepts an analytically physical matrix. If it does, retain the
representation and advance the distinct coupled-mass/prestress assessment;
if it rejects it or changes energy under equivalent frames, revise metadata
admission/transform before spectral integration. This bounded experiment
does not infer mass from stiffness or qualify F12.

**F12 eccentric-metadata V1 result and next action:** The four physical
section particles give an independently summed kinetic-energy matrix.
Metadata expressed at the beam reference axis admits the resulting coupled
6x6 inertia. Across an oblique section frame and reversed member, the
maximum global-matrix relative error is `1.91e-16` and kinetic-energy error
is `3.68e-16`; all masses are positive. The development result is
`B3_GE_E4_PL_G0_F12_B2_MASS_METADATA_DEV_V1.json`. A nonzero metadata
origin remains untested and no existing assembler pulls its velocity back
to the beam axis. Next derive that exact kinematic congruence and check it
against the same physical particle cloud before coupled spectral work.
No section density, centroidal inertia or mass center is inferred from
stiffness; F12/G0B and spectral admission remain open.

**F12 mass-origin pullback (27 September):** The private `MassMetadata` now
states its velocity datum explicitly and returns an owned 6x6 inertia at the
member reference axis using `v_origin = v_axis + omega × r`. Two nonzero
metadata origins reproduce the same independently summed four-particle
kinetic matrix and mixed translation/rotation work; mutation of the return
does not change the record. The focused definition suite passes `6/6`.
This supplies a missing local kinematic contract only. Coupled mass assembly,
geometric stiffness, descriptor treatment, prestress/buckling and installed
qualification remain open. Do not assign active-plastic or nonconservative
spectral capability from this check.

**Next F12 coupled-mass discriminator:** Assemble the physical B2 static-
trace mass from explicit, axis-referred sectional inertia and combine it
with the existing Q4 physical mass on the bounded F10 point system. The
independent questions are whether rigid kinetic work equals mass-per-length
times beam length, and whether the exact six multiplier coordinates remain
massless in the full generalized eigenproblem. Compare finite roots with
an independently eliminated constrained pencil; any mismatch sends the
assembly or descriptor layout back for revision. Passing only permits
broader mesh, frame, S3, prestress and free-free investigations; it cannot
close F12 or admit production modes.

**F12 bounded coupled-mass result (27 September):** The private B2 member
now integrates its explicit, origin-pulled sectional inertia through the
existing station trace with four Gauss points; the returned matrix is owned
and no density is inferred. On the physical four-particle section, its
rigid work equals an independent two-point axial kinetic-energy integral.
One real Q4 mass, one physical B2 mass and the F10 six-row finite-support
point law form a supported descriptor whose six multiplier rows have exact
zero mass. Finite roots, equation/constraint residuals and an independent
null-space reduction agree; both focused tests pass `2/2`. This is a small
elastic development oracle, not an installed or production eigensolver.
S3, free-free modes, changing frame/mesh, prestress, buckling, shell-side
point-law admission and the growing-interface problem remain open. F12/G0B
remain open and G1 barred.

**Next bounded F12 free-free discriminator:** The supported Q4/B2 descriptor
does not test the six common rigid motions of a connected free-free point
assembly. On the *same* bounded physical-mass and six-row point fixture,
remove only supports in the diagnostic pencil. Check the analytic common
rigid translation/rotation fields against the full stiffness and constraint
rows, check positive physical mass on their span, and count finite near-zero
roots against the constrained-mass rank. Exactly six consistent roots would
extend the bounded spectral feasibility to this unsupported Q4/B2 fixture;
extra or missing roots would identify a shell, beam, constraint or mass
contract to diagnose. This does not admit free-free production modes, select
the shell port, or close F12/G0B.

**F12 bounded free-free result:** The unsupported diagnostic of the same
Q4/B2 point fixture has six finite near-zero roots. Analytic common rigid
translations and rotations annihilate its full elastic stiffness and six
constraint rows within the `1e-9` normalized screen, have positive physical
mass, and span the six computed zero-mode vectors within `1e-8`. The finite
root count matches the independent constrained physical-mass rank; full
descriptor equation and compatibility residuals pass `1e-8`. The focused
F10/F12/definition tests pass `14/14`. This is a single small elastic
rest-state descriptor screen using the provisional F10 point law. It does
not establish mixed shells, nonmatching attachment mass, prestress,
buckling, production free-free execution or F12/G0B acceptance. The physical
connection choice and G1 bar are unchanged.

**F12 oblique mass-frame check:** An explicit four-particle section on an
oblique straight B2 member reproduces independent integrated rigid kinetic
work with its offset mass origin. Reversing the member and rebuilding the
sectional inertia from the same physical particles in the reversed frame
gives the same complete global 12-by-12 candidate mass matrix after nodal
permutation. The related definition, mass/descriptor and prestress tests pass
17/17. This checks frame and reversal covariance for one physical section;
it does not admit general mass laws, attached spectra, or F12/G0B.

**Independent F12 mechanics review:** A read-only reviewer found no
actionable algebraic defect in the private mass-origin congruence, oblique
frame/reversal treatment, exact-degree trace-mass quadrature, or the stated
constant-reference-axis axial geometric term. The reference point candidate
still pulls a joint Hessian through affine shell and beam ports; that does not
include their loaded-state second derivatives or an equilibrated multiplier.
The next useful F12 discriminator is one loaded, equilibrated B2/Q4 point
state with nonzero axial resultant and multiplier, checking total shell,
beam, port and joint curvature against independent physical-work variation.
Its point-law interpretation follows the pending primary connection choice.
The reviewer's separate focused test process was stopped without a result;
no new pass is attributed to that review. F12/G0B remain open.

**Next bounded F12 point-prestress discriminator:** The private B2/Q4 point
law currently retains only six affine reference rows. For conservative
buckling about a prestressed connected state, determine whether the
objective pose law contributes nonzero multiplier-dependent curvature after
the existing finite shell fit and physical B2 station trace are composed.
Use the same F10 geometry and fixed nonzero physical multiplier, compare
the composed joint Hessian with an independent finite difference of joint
work through the actual pose updates, and check symmetry, force/moment
work and zero multiplier behavior. A consistent nonzero term becomes a
private candidate for the later spectral tangent; a mismatch identifies a
port/chart defect. This does not change the reference-linear static law,
select a shell port, or admit B2 buckling/F12/G0B.

**F12 point-prestress candidate result:** The private F10 point record now
owns its two reference frames and can pull the objective pose joint's
nonzero-multiplier chart Hessian through the existing affine four-vertex
shell fit and physical B2 station trace. The returned 36×36 curvature is
owned, symmetric to numerical precision and exactly zero for zero
multiplier. A three-step mixed finite difference of independently updated
shell/beam poses agrees with its virtual-work action at the bounded
`1e-6` screen. F10/F12/mass/definition checks pass `20/20`. This is a
conservative *reference* attachment-curvature candidate only. It is not
assembled with member geometric stiffness, a loaded prestress state, sparse
buckling, an accepted shell port or a production B2 profile. Independent
read-only mechanics review found no algebraic defect in this reference
affine-port composition. It identified the material boundary: the four-
vertex shell fit and B2 station trace have only reference differentials,
with no nonlinear second derivatives; a true loaded-state attachment
tangent needs current poses, equilibrated multiplier and those missing port
terms alongside member/shell geometric stiffness. The record's input arrays
are now bytes-backed so callers cannot re-enable writing and make curvature
inconsistent with stored rows; the impacted `20/20` tests still pass.
This does not admit B2 buckling. F12/G0B remain open and G1 barred.

**Next F13 local compilation discriminator:** The immutable physical B2
definition currently constructs its exact force-flexibility operator again
for each `local_operator()` or `trace_global()` request. Test a private
compiled member that owns one operator and fixed local/global maps, and
returns independently owned traces and masses for repeated loads. Parity
with the existing definition path, mutation isolation and fresh-definition
invalidation would permit reuse by a later B2 model owner; any changed
physical response or borrowed-array leak sends the adapter back for revision.
This does not establish graph batching, factorization reuse, cancellation,
resource scale, public dispatch or F13/G0B acceptance. Measure construction
counts before making a performance claim.

**F13 local compilation result (27 September):** A private compiled member
retains one exact operator and owned fixed frame maps for its immutable
definition. It shares one trace/mass mapping implementation with the
ephemeral route. Three repeated trace/mass requests reproduced the prior
values exactly while the counted operator construction stayed at one;
returned arrays could be mutated without changing later results. A new
definition compiled a separate operator, and a foreign operator/definition
pair was rejected. Impacted focused suites passed `19/19`, followed by
`7/7` definition checks after the owner guard. This is no public B2 session,
batching, factorization, cancellation or speed claim. The next independent
F13 question is whether unchanged sparse affine operators can serve 1/10/100
ordered RHS in bounded chunks with one factorization, complete-case
cancellation and selected outputs. Keep G0B open and G1 barred.

**F13 batch discriminator before execution:** On the already checked two-
member generalized B2 elbow, assemble from retained local operators into a
small sparse graph with an explicit clamped-root affine transform. Compare
1/10/100 ordered, fixed-magnitude mixed-load cases against independent
per-case solves; retain only selected tip values. Count one factorization
for the unchanged operator, bound each RHS block to eight, and cancel after
a completed case to check ordered-prefix publication. A failed factorization
must publish no case or plausible offset-only result. Passing permits a
later owner to integrate with `AnalysisSession` and full constraint audit;
failure requires fixing the local batch semantics first. This is not G1
dispatch or a practical-scale/performance qualification.

**F13 private batch result (27 September):** The bounded two-member elbow
assembles retained physical B2 local operators into a sparse affine graph
and uses the existing sparse factorization handle for 1/10/100 ordered,
fixed-magnitude mixed-load RHS. The selected six tip values agree with
independent per-case sparse solves; the unchanged operator factors once and
RHS blocks never exceed eight. An input transform/offset mutation after
compilation does not change the owner. Cancellation after case five returns
exactly the five complete ordered cases; a singular factorization raises
before any case result is created. Focused tests pass `5/5`. This private
beam-only feasibility code does not use the production `AnalysisSession` or
constraint auditor, and does not admit shell attachments, prescribed-motion
combinations, installed execution, scale or a speed claim. The next F13
integration decision is how the mixed-profile owner will bind an actual
audited `ConstraintPlan` and invalidate a factorization only when its
structural dependencies change. F13/G0B remain open; G1 remains barred.

**Next bounded B2 batch-scaling decision:** F09's rounded-graph checks
show that positive diagonal scaling can recover a weak mixed-load response,
but the private F13 batch prototype still factors its unscaled affine
matrix. Apply the same reversible coordinate scaling inside that private
owner, leaving the physical `K`, affine plan and selected outputs in their
original coordinates. Reject nonpositive, nonfinite or unrepresentable
diagonals before factorization. Recheck 1/10/100 ordered cases, one
factorization, bounded RHS chunks, complete-case cancellation and failed
factorization; add the coherent slender circular elbow as a physical
screen. If results or failure semantics change, repair or revert the
prototype. This is not production scaling admission or a performance claim.

**B2 private batch-scaling result:** The compiled affine batch now factors
`D (Tᵀ K T) D`, with `D` from the positive reduced diagonal, and maps
loads and solutions back to physical coordinates. It rejects nonfinite,
nonpositive or unrepresentable scaling, and checks each solved block's
componentwise reduced residual before publishing selected case values.
An injected backend that returns zeros is rejected without a case callback.
The unchanged 1/10/100 case, cancellation and singular-factorization
checks pass; the three coherent solid-circle elbow cases match an exact
rounded solve and independent cut-wrench work. Focused tests pass `9/9`.
This remains private beam-only feasibility: no audited mixed constraint
plan, shell attachment, installed validation, performance measurement or
F09/F13/G0B acceptance follows.

**Next bounded F13 audited-affine decision:** `AnalysisSession.ConstraintPlan`
is tied to a session-owned structural matrix and cannot truthfully be
fabricated for the private B2 graph. Test the actual shared constraint
auditor and `build_constraint_transformation` against that graph's sparse
physical stiffness, with a fixed root and one declared translation MPC.
Check solved work/compatibility, a value-only prescribed refresh, a changed
MPC coefficient, and contradictory supports. If the auditor produces
correct affine maps, the later mixed owner can bind them to its structural
identity; if not, resolve that interface before F13 integration. This
does not imply a session-owned B2 `ConstraintPlan` or enter G1.

**F13 audited-affine result:** The actual shared constraint auditor and
`build_constraint_transformation` accept the private two-member B2 sparse
stiffness with a fixed root and one translation MPC. The resulting 11-free-
coordinate solve satisfies the declared MPC and projected equilibrium;
the private scaled batch consumes that audited `T/u0` and reproduces the
independent selected tip values to `1e-11` relative/absolute;
changing only the prescribed value preserves `T`/independent indices and
changes `u0`, while changing the MPC coefficient changes `T`. A
contradictory root support is rejected before numerical reduction. The
focused batch/audit file passes `10/10`. This establishes a usable
one-shot affine transformation source, not session ownership, automatic
cache invalidation or permission to use the affine auditor for nonlinear
beam–shell attachments. Binding a true mixed-owner structural identity
remains an F13/G0B requirement; G1 is still barred.

## Latest bounded evidence and interpretation

**Current bounded discriminator (after `2c87ee7c`):** The x8 shell/m4→m8
loaded screen changed torque response, but its compact output omitted the
beam-root/interface wrench and line duals. The competing explanations are a
physically distributed change in connection work and a concentrated or
cancelling enforcement artifact; the screen cannot distinguish them. Rerun
only the existing x8/m4 and x8/m8 fixtures with the same geometry, loads,
supports and operator, retaining those missing observables. Audit global and
interface wrench closure and report basis-weighted material duals without
calling them display-ready spatial tractions. If the added rows produce a
balanced, bounded redistribution, proceed to the separately required physical
norm and growing-space assessment; if they concentrate or cancel pathologically,
revise the line-resolution policy before that assessment. If these observables
still cannot distinguish the law from the F5 full-face reference, stop
refining and obtain the specifically needed sided reference. This is a
development discriminator, not a multiplier selection or G0B acceptance.

**Result and decision:** The two detailed same-source reruns are retained in
`B3_GE_E4_PL_C1_ENRICHED_LOADED_Q4_X8_M4_DEV_V2.json` and
`B3_GE_E4_PL_C1_ENRICHED_LOADED_Q4_X8_M8_DEV_V2.json`. All 12 prior
rank/response/work/gap summaries are exactly unchanged from V1. Across the
six family/load cases at each resolution, the maximum absolute six-component
global support-plus-root-plus-applied wrench defect is `2.65e-9` in the
recorded N/Nm components; shell-plus-beam interface wrench defect is at most
`2.29e-12`. The shell-side interface work stays positive for both separate
linear influences. Thus the response change is not an unbalanced applied
load or lost interface wrench in this fixture. For the torque influence,
the sum of absolute material y-dual coefficients divided by the absolute
signed sum grows from `34.3` to `124.0` for P0, `40.6` to `46.6` for P1,
and `13.6` to `20.7` for dual P1 as m4→m8. P0's maximum basis-mean y-dual
coefficient per metre grows `3.64x`. These are basis-dependent material
coefficients, not display-ready spatial tractions or a norm-scaled inf-sup
test; the increase signals unresolved oscillatory/cancelling enforcement,
not a proven unstable formulation. It also prevents selecting P0 just from
rank, balance, and tip response. Stop repeating this loaded resolution screen.
Reconstructing the declared material y-channel density as
`sum_i (lambda_i / basis_integral_i) * basis_i(x)` and integrating its
piecewise-linear absolute value over the 0.1 m line gives L1/net ratios
`34.3→124.0` (P0), `27.5→32.1` (continuous P1), and `20.3→27.4`
(dual P1). Thus the P0 growth is not only a coefficient-basis artifact;
the declared material density itself shows much stronger cancellation at
this fixed shell resolution. This is still not the physical spatial wrench
distribution, a convergence sequence, or a stability verdict.
The next native calculation must define the physical primal and dual norms,
reconstruct work-conjugate interface distributions, and assess the growing
space with shell/beam refinement and registered ratios. In parallel, use the
matched F5 common-action observables for physical torque/shear interpretation;
request actual sided B3 reference work only if the law-vs-reference cause
still cannot be separated. No F03 formal authority was consumed.

**Independent F09 bounded question:** The preserved moderate/extreme elbow
diagnostic and its read-only review show that the exact solve of the rounded
12-free-row B2 graph agrees with the independent force method, while default
sparse factorization loses the tiny applied-force response in the extreme
case. Its 120 s/2 GiB preparatory envelope and unchanged mechanical inputs
are reviewed; no formal F09 acceptance authority is invoked. On that same
rounded matrix, compare a bounded set of sparse orderings/pivot choices with
and without positive diagonal coordinate scaling. Separate force and moment
residuals relative to their own applied scales and compare tip response to
the exact rounded and physical oracles. If a sparse variant recovers both,
design and review an admitted scaled route; if none does, retain the typed
admission and investigate representation or a defensible physical range.
No numerical floor, historical B2 law change, or F09 pass follows from a
single extreme fixture.

**F09 result and action:** The source-bound result is
`B3_GE_E4_PL_G0_F09_SCALED_SPARSE_DEV_V1.json`; it reassembled the same
moderate and extreme 12-free-row graph, checked the default sparse tip
bit-for-bit against the preserved raw record, and tested 12 sparse variants
per area. In the extreme case, every positive-diagonal-scaled variant
(`NATURAL`/`COLAMD`/`MMD_AT_PLUS_A`, pivot thresholds 0/1) recovered the
exact-rounded tip within `3.89e-16` under the diagnostic component floor,
with separate free-force and free-moment residual ratios at most `4.45e-16`
and `2.97e-16`. Unscaled threshold 0 also recovered this fixture, but
unscaled threshold 1 retained errors of order `1e7–1e8`; default pivoting
therefore remains unsafe for this weak-force case. The moderate scaled
variants also agreed with the exact-rounded tip within `6.88e-16`. This
supports designing a unit-aware scaled sparse route and testing it over a
registered physical range; it does not justify disabling pivoting in the
product, alter B2 admission, or close F09. The exact and physical references
are the preserved independently reviewed record, not newly regenerated
external evidence.

The independently owned F09 follow-up at commit `c4236be9` extends the same
diagonal-scaling idea across six declared mixed-elbow stiffness/area and
load-rescaling samples. Its exact-rounded and independent rational force
oracles agree with the scaled sparse response to at most `1.12e-15` by its
component-scaled diagnostic measure; separate free-force/moment residual
ratios are below `9e-16`. It explicitly rejects zero diagonal and erased
subnormal coupling. The focused private B2 mechanics suites passed `27/27`.
See `B3_GE_E4_PL_G0_F09_PHYSICAL_RANGE_DEV_V1.md` and its raw JSON. The
fixed section inertias with vanishing areas are numerical stress cases, not
a physically realizable admission range; F09/G0B stay open. Next define a
physical section range and test more graphs and attachments before product
admission.

**Independent F05 bounded result:** At commit `610e4ef7`, a yielded
three-layer Q4 fixed-predecessor trial was composed with an eccentric,
nonzero-multiplier pose joint through actual additive rotation charts.
Separated material, joint and combined directional errors were at most
`8.86e-7`, `2.06e-8` and `8.86e-7` over sampled adjacent steps; all 12
stations kept their sampled active mask, and the predecessor was byte-identical.
The source, settings and raw measurements are in the F05 V2 manifest/result
and `B3_GE_E4_PL_G0_F05_POSE_PULLBACK_DEV_V2.md`. This is one developmental
pullback check; mixed-owner lifecycle, more port geometries, independent
mechanics review and F05/G0B acceptance remain open. Preserve the elastic
adapter guard.
An independent read-only mechanics review found no defect in the bounded Q4
fixed-predecessor pullback or pose-chart check. Its sampled active masks do not
prove branch continuity between finite-difference points. The reported
`joint_cross_block_norm` includes shell-to-beam *and* shell-to-multiplier
columns; it does not alone measure a pure shell–beam Hessian block. F05 stays
open for S3 and direct mixed-owner lifecycle evidence.

**Next bounded F05 discriminator (before execution):** The Q4 yielded
fixed-predecessor material/pose pullback passed, but S3-V2D has a distinct
local material update and chart mapping. On one admitted plastic S3 triangle,
form a nonzero-multiplier eccentric point joint at a rotated trial from one
yielded accepted predecessor. Compare material, independently computed joint,
and combined directional actions through actual additive charts across an
active-mask-stable finite-difference plateau; check predecessor immutability.
A failure separates S3 material/chain-rule and pose-chart terms before any
mixed-owner integration. A pass is bounded S3 feasibility only: it does not
prove the full mixed material adapter, other port geometries, owner lifecycle
or F05/G0B acceptance. Do not relax the existing elastic adapter guard.

**S3 F05 bounded result:**
`scripts/probe_b3_ge_e4_pl_g0_f05_s3_pose_pullback_dev_v1.py` and
`B3_GE_E4_PL_G0_F05_S3_POSE_PULLBACK_DEV_V1.json` reproduced in this checkout from current
source. A plastic S3 material update from virgin supplies one fixed yielded
predecessor (`alpha_max=0.00760`); the checked trial activates 15 sampled
station-layer points (three in-plane stations by five layers) relative to it.
Independent SciPy/closed-Jacobian pose action agrees
with the owner first variation to `2.51e-16` relative. Two actual-chart
directions each have adjacent finite-difference steps below the registered
`1e-5` developmental tolerance for separated material, joint and combined
actions, with unchanged sampled active masks and byte-identical predecessor.
The largest sampled directional error is `2.10e-6`, while finer adjacent
steps are smaller. The result is a local S3 material-predecessor and joint
composition check, not a global accepted owner or branch-continuity proof.
Its `joint_cross_block_norm` groups beam and multiplier columns; it is not an
isolated shell–beam stiffness norm. Direct mixed accepted/rejected-state
mechanics remain open; F05/G0B remain open.

**Independent S3 F05 review (27 September):** Read-only mechanics review
found no actionable defect in the fixed-predecessor material pullback,
actual additive-chart pose composition, or the source-bound directional
checks. It verified the runner hash against current source and retained the
existing limitations: sampled masks do not establish branch continuity or
hardening-segment invariance, and the mixed-owner lifecycle is not tested by
this local composition. The bounded S3 review obligation is addressed;
direct coupled atomic-state mechanics and F05/G0B acceptance remain open.

**F05 mixed-state rejection development (27 September):** The source-bound
`b3_e4_g0_f05_mixed_rejection_dev_v1.json` and focused test pair an
accepted yielded S3-V2D shell state with an accepted yielded retained-B3
beam checkpoint. A deliberately rejected next beam trial leaves both
accepted artifacts byte-identical; replay from the same predecessors
reproduces the shell trial, and separately accepted/restored artifacts
match. The test also evaluates a nonzero eccentric pose cross-block from
those states. The focused run passed `1/1` in `4.24 s`; it preserves an
initial test-harness chart-flag failure. This is test-local composition,
not an atomic mixed-owner publication or production shell-plasticity
adapter. Branch continuity, direct coupled rejection, independent mechanics
review and F05/G0B acceptance remain open.
The read-only reviewer found no bounded mechanics defect, but the V1 JSON
binds only its runner hash, not imported solver-module or environment
identities. It remains development evidence, not exact-artifact qualification.

**Independent F06 bounded result:** At commit `d5dcc74b`, one curved S3 /
native-B3 accepted two-step loaded prefix was represented in reference and
rebased beam charts with unchanged physical frames, material/resultant
recovery, eccentric pose work/gap and support reactions. The largest
solver-scaled residual difference was `1.38e-16`; accepted descriptor and
checkpoint bytes stayed unchanged. The terminal v1e result and four earlier
source-bound setup/reporting/numerical attempts are preserved in
`B3_GE_E4_PL_G0_F06_BEAM_CHART_DEV_V1.md` and its reference-case JSON files.
This is chart-description feasibility only. Actual owner-held beam anchors,
atomic accepted rebase/continuation, direct restore, larger noncommuting
motion and independent mechanics review remain required; F06/G0B stay open.

**F06 accepted beam-chart development v5 (27 September):** A separate
prototype now owns native B3 nodal and retained-cell anchor/coordinate
arrays in its accepted checkpoint. On the existing curved S3 two-step
loaded prefix, it stages the shell/beam rebase before moving the accepted
head, restores that snapshot directly, and carries the beam anchors through
one loaded cursor-three continuation with nonzero nodal and cell chart
coordinates. Rehashed anchor and lineage corruption and stale continuation
are rejected. The focused test passed `1/1`; source/test hashes and the
earlier writable-array setup failure are recorded in
`B3_GE_E4_PL_G0_F06_BEAM_CHART_V5_DEV.md`. This is an ownership/restart
prototype, not a physical chart-coordinate B3 Newton operator: the native
beam residual and tangent still use physical frame matrices. Q4, large
noncommuting rotations, repeated rebases, cutback and independent mechanics
review remain open. F06/G0B status and the G1 bar do not change.

**Next F06 physical-chart discriminator:** The accepted anchor/checkpoint
prototype does not yet establish Newton work in additive B3 rotation
coordinates. On the already checked two-element elastic generalized B3
fixture, impose one nonzero nodal and retained-cell chart state, keeping
all other coordinates and the accepted material predecessor fixed. Pull
the extracted spatial residual and Jacobian through the analytic left-Exp
map, including the residual-weighted derivative of that map; independently
perturb the actual native frames through `advance` according to the
additive chart and compare chart-coordinate residual slopes over the
registered elastic `1e-6` plateau. A pass establishes one bounded
physical-chart tangent seam; a failure distinguishes representation or
curvature terms for correction before mixed-owner use. Preserve the native
spatial residual/tangent and existing checkpoint identities. This does not
close F06, admit a charted production owner, or alter G1's bar.

**F06 native chart-pullback result:** The bounded two-element generalized
B3 fixture now tests nonzero free nodal and retained-cell additive chart
coordinates against *actual* physical frame advances. Both the unloaded
and native distributed-load cases reproduce the chart-coordinate residual
slope over the three-step elastic finite-difference plateau at the
registered `1e-6` limit. The analytic pullback includes the left-Exp
Jacobian on both sides of the native spatial tangent and the
residual-weighted derivative of that Jacobian; the same checks distinguish
the omitted curvature term. The focused F06/F08 impacted set passed
`14/14`. This supports one elastic generalized B3 chart-tangent seam, not
a charted mixed owner or plastic-history transport. Noncommuting loaded
rebases, Q4/mixed shell coupling, physical-fibre branches, cutback and
independent mechanics review remain open. F06/G0B remain open and G1
remains barred.

**F06 private sparse chart operator:** The analytic left-Exp pullback is now
an owned sparse operator for native B3 nodal and retained-cell rotation
coordinates. It keeps the F08 spatial trial and accepted material predecessor
unchanged, returns a separate residual/CSR tangent, and carries the
candidate-history tuple without regenerating local material updates. A
separate dense calculation checks the block map and residual curvature;
actual-frame finite differences pass the `1e-6` elastic plateau for two
generalized cases (unloaded and distributed loading) and one physical-fibre
case. The focused file passes `3/3`; the F06/F08 impacted suite passed
`14/14` before the additional physical-fibre test. This is a reusable G0
coordinate seam, not a mixed-owner Newton solve, a smooth-active plastic
derivative, loaded chart rebase, production sparse-scale result or F06/G0B
acceptance. The physical connection choice and G1 bar remain unchanged.

**Next F06/F08 fixed-predecessor chart discriminator:** The sparse chart
operator passes elastic physical-fibre work, while the accepted yielded
three-step state lies within a tested branch-switch interval. Reuse the
existing `1e-4` positive trial from that exact accepted predecessor, where
the F08 spatial tangent already passes a constant-active-row plateau.
Represent its nodal and cell rotations in a nonzero additive chart anchored
at the accepted physical frames. Compare chart-coordinate residual slopes
from actual native advances with the sparse pulled tangent while requiring
unchanged active-row counts and unchanged predecessor/checkpoint identity.
A pass extends this seam to one smooth active branch; a failure separates a
chart defect from a new branch crossing before any correction. Do not apply
the smooth criterion to the original accepted-state branch switch or close
F06/F08/G0B from this one direction.

**F06/F08 smooth-active chart result:** From the unchanged accepted
three-step physical-fibre predecessor, the nearby `1e-4` positive trial has
active plastic rows and keeps the same active-row identities on both sides
of all three tested chart-coordinate perturbations. The private sparse
pullback's directional residual slope meets the registered smooth-plastic
`1e-5` limit on the plateau, using actual native physical-frame advances;
the accepted material history, configuration descriptor and checkpoint
hash remain unchanged. The focused F06 file passes `4/4`. This establishes
one bounded active-branch chart seam, not the accepted-state semismooth
tangent policy, other material branches, coupled plastic ownership or
F06/F08/G0B acceptance. Preserve the earlier failed accepted-state central
difference and its independent interpretation.

**F06/F08 independent-review correction:** Read-only review of the first
sparse chart implementation found that its physical-fibre input was an
Exp-chart energy Hessian, although the pullback requires a spatial residual
Jacobian. The fibre local adapter now applies the same residual-moment
`−0.5 skew` block correction used for the generalized family. The native
dense fibre owner remains unchanged; F08 adapter parity explicitly converts
that owner's chart Hessian before comparison. At a nonzero-moment elastic
state, a zero-coordinate chart now recovers the dense energy Hessian on a
rotation block, and rotation-focused actual-frame finite differences pass
the elastic plateau. The smooth-active fixed-predecessor chart test also
passes with the corrected representation. Focused F06/F08/ownership tests
pass `21/21`. Earlier passing global-norm tests were insufficient to reveal
this block defect; preserve their historical result but use this corrected
contract for subsequent work. Bounded independent re-review found the
original representation defect resolved and no new definite defect in the
reviewed scope. The dense parity oracle now reconstructs internal moments
before conversion, so a later nodal-couple fixture is not silently judged
against the total residual. The sampled active-row identity check does not
prove an unobserved branch margin. F06/F08/G0B remain open and G1 barred.

**Next C1 enforcement discriminator:** The x8/m4→m8 torque solve shows
growing oscillation of the P0 material dual density while all six-channel
global balances close. The competing explanations are a weakly controlled
growing multiplier mode and a legitimate but steep redistribution under a
still unresolved physical line law. Reuse the existing positive physical-E4
and broken-retained-B3 trace quotient at *fixed x8/y4, B3-12*, changing only
four to eight line intervals for P0/P1/dual. If the normalized lower quotient
falls sharply for P0 but not the others, prioritize its interface-resolution
policy and full mixed-system mode test; if all remain comparable, the loaded
dual growth alone cannot choose a space, and proceed to work-conjugate
physical transfer and native mixed-system tests. This quotient remains a
bounded representability diagnostic, not inf-sup, physical fidelity, or G0B
acceptance. Do not extend to another mesh or classical axial run from this
screen without a new decision question.

**C1 quotient result and action:** The two-case x8/y4/B3-12 run completed at
`.qualification/b3-ge-e4-pl/f03-c1-positive-trace-growing-line-dev-20260926-v1`
(manifest SHA-256 `63ec284010adbe604bf45fadcc2d1fc3d107861ca38051e5605b681867de0393`;
result SHA-256 `86311ba41dbb3422442e5541c59a7d42cbb3714b0caef9268bf850c91da9ccba`).
The run used `python -B`, local source, `NUMBA_DISABLE_JIT=1` and one BLAS/
Numba thread. The manifest records generation-time HEAD `07cd0031` and
the exact modified diagnostic source hash; the source and this interpretation
are committed subsequently. All supported row sets retain full rank (m4: 24/30/30;
m8: 48/54/54), with the same positive shell metric and B3 observable trace
rank 15. The reported floating full quotient estimate is
`0.22039→0.01244` for P0,
`0.17588→0.09087` for continuous P1, and `0.17142→0.09084` for dual P1.
Independent read-only review found that the x8/m8 continuous-P1 values
labelled lower/upper in the raw result are reversed by `1.09e-11` (and the
nonaxial pair by `1.43e-11`). They cannot be called an ordered numerical
enclosure. Preserve the raw result; use the values only as floating
diagnostic estimates until an outward error allowance or better-resolved
Gram calculation repairs the bound status. This does not change the much
larger finite-grid P0/P1 contrast, but blocks a certified bound claim.
The same independent review recomputed all 12 V2/V1 retained summaries,
wrench defects, material-density integrals, source hashes and P0 weak-mode
channel/action split, finding no other calculation blocker. It confirmed
that the material dual density is work-conjugate to the weighted-mean gap,
but is not a display-ready spatial traction. The review is read-only G0
development scrutiny, not F03 or G0B acceptance.

**Full mixed-system next test:** A separate read-only mechanics design
identified the actual support-reduced native KKT as the needed object:
physical E4 coordinates, B3 nodal coordinates, both retained half-cell
rotations, all retained generalized resultants, and exact multiplier rows.
The positive broken-trace quotient omits part of that space and cannot stand
in for its well-posedness. A proposed diagnostic Riesz metric separately
norms physical shell energy, *all* independent native kinematic/resultant
coordinates and physical H^(-1/2) line duals, with units and SPD checked;
any E4 drilling coordinate must enter only a declared diagnostic norm,
never an added physical tangent. A bounded x8/m4→m8 P0/P1/dual test may
proceed only after the retained-variable and drilling norm can be defended.
Compare its near-null directions and work to the positive quotient without
identifying the two metrics. This remains a design under implementation,
not a revised scientific criterion or an inf-sup acceptance.
P0's m8 weakest mode is alternating **vertical** material action
(`−13.24,+40.77,−62.39,+73.83,−73.82,+62.39,−40.71,+13.18` in the
recorded force-equivalent coordinates) and about `99.5%` shell positive
action. The prior loaded torque dual cancellation is mainly **lateral**;
these are not shown to be the same mode or cause. The fixed-shell P0 drop
prioritizes its growing-space/mixed-KKT and locking audit, while the reduced
P1/dual quotients prevent selecting either without further physical and
registered-ratio evidence. No quotient establishes native indefinite-system
well-posedness or the intended connection law. The first unprivileged run
stalled before evidence creation; a `python -B`/JIT-disabled import check
passed, but the next attempt could not create the protected evidence root.
The exact-path authorized run produced the result above. Neither failed
attempt is a mechanics failure or a second result.

**C1 law currently implemented, for the pending physical decision:** The
candidate integrates over x=`.9–1 m` and the finite transverse
y=`−.05…+.05 m` strip at the 35 mm shell top/beam bottom. In each material
section its first three channels are the mean relative position expressed in
the beam frame. Its fourth and sixth channels are the transverse first
moments of vertical and axial position gap, normalized by transverse second
moment; its fifth is the relative beam-frame/E4-director pitch at the strip
centre. The beam pose comes from the actual retained half-cell port, including
one-sided values. The pitch channel is a *declared director-couple transfer*,
not a tie between director and geometric surface normal. This law excludes
even transverse local slip from its six section actions and is not a
pointwise full-width solid bond. It has bounded objective/reference/chart
checks, but its physical transfer and mesh-stable exact enforcement have not
been accepted. The rigid and distributing finite-footprint laws remain
separate; neither can be inferred from a zero weak residual here.

**Decision sought:** Determine whether the current native six-channel C1
connection has the intended continuous section work law, then assess its
P0/P1/dual enforcement. The same fields must be measured as sampled local
slip, continuous `g6(x)`, and integrated weak rows. A zero weak row alone
does not classify the law or prove instability.

**Established:** The bounded, actual-C1 mode check in
`B3_GE_E4_PL_C1_CONTINUUM_MODES_DEV_V1.json` separates two effects. An even
transverse field, confined to the declared 0.1 m bond width and zero at the
root, has 7.439 µm sampled slip RMS, but every continuous six-channel gap is
below 7e-20 and all projected rows are below 9e-20; physical E4 strain energy
is 30.11 J without drilling completion. Thus the continuous reduced trace
admits this local section deformation; that alone neither classifies the
intended connection nor proves a mechanism. A separate longitudinal field
has a nonzero continuous vertical gap (8.463 µm maximum, 2.973 µm weighted
RMS), while its fixed two-cell P0/P1/dual rows stay below 2e-20; its physical
E4 energy is 50.02 J. This is a fixed-space projection null, not a uniform
stability result. The bounded V2 projection of that same continuous field
detects it with all P0/P1/dual spaces at four and eight x intervals: the
largest basis-mean gap at four intervals is 0.269/1.670/5.550 µm respectively.
The two-interval means remain below 3e-21 m. Thus targeted longitudinal
enrichment resolves this *specific detection* failure; it does not select a
space or establish stability or locking freedom. Both prescribed fields are
translation-only diagnostics, not loaded coupled solutions. A subsequent
bounded native-retained Q4/B3-12 loaded screen assembled x4/m2, x4/m4, x8/m4 and
x8/m8 with all three spaces. Every assembled row set retained full rank and
both load cases passed the existing runtime mixed equilibrium/work checks
(maximum reported mechanics error 2.85e-11). At fixed x8, m4→m8 lowered the
torque tip rotation by 3.04% P0, 1.24% P1 and 1.26% dual; the added rows materially
change the response, but two shell levels and these linear influences do not
establish locking freedom or convergence. The versioned raw results are
`B3_GE_E4_PL_C1_ENRICHED_LOADED_Q4_*_DEV_V1.json`. The raw fixture-file
hash in those results reflects mixed Windows line endings
(`94d9e1a3`); normalizing CRLF to LF is byte-identical to the committed
fixture blob (`912b55e5`). The other operator source hashes match commit
`ea47fa83` directly; this is a provenance encoding difference, not a mechanics
change. The JSON `source_git=7d16458` is the generation-time parent; the
matching source and results were committed together at `ea47fa83`.
Independent read-only review found no calculation blocker and confirmed the
response changes. The compact results omit beam-root details and multiplier
densities, so they do not independently reconstruct full balance or physical
traction distribution. Neither bounded screen selects a multiplier. The prior
F4/F5 findings remain bounded diagnostics. The implemented candidate expressly defines a
six-channel reduced transverse-strip law; allowing the even local section
field is consistent with that declaration, but whether this is the intended
physical bonded-line idealization remains open. The F5 shared-node solid
bond constrains the full finite face, so its physical response is a demanding
transfer reference, not an equivalent pointwise law for a 1D reduced strip.
The earlier lost pytest terminal results are not passes;
two resumed focused pytest runs stalled without test output and were stopped
after exceeding the 900 s diagnostic envelope. A third current-source pytest
run was stopped when the same known collection behavior appeared. None is a
mechanics pass or failure. The current-source transverse-section test function
passed by direct invocation with controlled threads, and the complete mode
diagnostic exited 0. Standard pytest collection remains unresolved.
B2 F09 fixed mixed-wrench independent checks passed 36 focused tests. An
independent exact force-method matrix equals the private flexibility matrix;
for the same weak generalized SPD section, the minimum provisional
pivot/diagonal ratio changes from below 1e-12 to above 0.01 after a physically
scaled shear/midspan-moment basis transformation. Thus this rejection is
basis-dependent, not proof of unrepresentable physical response. Stable
rounded global assembly/solve and a qualified range remain open; the cutoff
is unchanged. The preserved 36-test JUnit predates a one-line exact-Fraction
test refinement; the refined pivot-basis test passed by direct invocation
with local source and JIT disabled (the B2 operator itself is pure Python).
F07 now has a bounded existing-kernel descriptor check in addition to its
analytical identity: massless retained coordinates give modal eigenvalue
4.8 and full buckling multiplier 1.5, matching independent QZ; reusing the
modal static lift would give 6. Direct invocation passed 2/2. This does not
qualify actual coupled beam/shell mass or prestress.

**Remaining uncertainty and next action:** Declare whether the transverse
section deformation is physically admissible for the intended bonded pose
law. Check the native torque/shear work against the validated F5 common
action at the same geometry, loads, supports and connection interpretation.
Next use a frozen growing-interface policy and physical primal/multiplier
norms to assess the native mixed system, work, locking and convergence over
the registered mesh-ratio range; row detection and bounded loaded/dual
screens have been answered. If sided B3 work is essential to distinguish causes,
obtain a
reference that recovers actual side contributions before using it. Review F09
conditioning separately. Formal F03 authority remains unconsumed; G0B is
open, G1 barred.

## Pause checkpoint — 26 September 2026

Work paused at user request before a new mechanics decision. The integration
worktree was clean at `85ede9d3` before one uncommitted focused test was added
to `tests/test_b3_e4_f03_distributed_surface_finite.py`. That test asks whether
the current six-resultant hybrid strip has an even transverse slip mode with
zero weak gaps but nonzero sampled local slip. This is a kinematic reduction
probe; its original automatic classification as a distributing strip was too
strong. The F5 physical comparison and multiplier decision remain unresolved.

At this historical pause, the focused pytest was running in session `57101`
(Python PID `52940`) and the older pre-thin-SVD pytest in session `27660`
(PID `57260`). Both later handles and PIDs were absent, with no recovered
terminal output. Do not count either as passed or repeat completed F4/F5
evidence. G0B remains open, G1 barred, formal F03 authority unconsumed.

## Current state — 26 September 2026

**Decision sought:** Defend the native six-channel beam–shell connection and
its exact line space. The classical axial comparator, historical Q6/finite-pad
reference, and native six-channel law remain separate. No small gap,
residual, rank or spectral quotient chooses P0/P1/dual.

**Established:** The bounded transverse-order/line-resolution and detached
bar checks do not motivate further classical axial refinement. The fixed
C1 positive trace metric and its registered `16:2`/`2:16` ratio endpoints
retain physical-shell positivity, compatible full-rank B3 traces and
P0/P1/dual row ranks `12/18/18`. The source-bound thin-SVD rerun exactly
reproduces the previous endpoint result. These three finite grids show no
collapse under this metric, not uniform inf-sup stability. On the saved F4
pre-opened solid, actual B3 port sides jump `0.180 µm RMS` at `.95 m`.
Face-stress cut actions fail to cancel sufficiently for exact sided work:
F4 has `4.95%` scaled axis-wrench and `79.4%` displacement-work mismatch;
F5 cuts at `.94/.96 m` have `2.67/3.50%` and `26.6/17.9%`. The older F5
bond-face extrapolation also failed as a conservative weak-action proxy.

The new saved-F4 common-*continuous*-trace comparison avoids cut allocation.
The physically matched total solid weak action and native shell action
differ by `76.5%` lateral, `53.7%` vertical and `57.9%` twist in the
three-hat channel L2 measures. Opposite solid-side projections differ much
less, and the integrated solid wrench checks against printed supports.
This is a one-mesh difference between solid and native *coupled* models,
not an allocation of cause to the shell, beam or connection.

The matched F4 shell-only replay reproduces the saved native shell work
within `8e-13 J` and preserves the pulled-back solid-action wrench to
`3e-13 N/Nm`. Its solid-action route differs from the solid tip face by
`3.43 µm RMS`, while native-action replay differs by `0.15 µm`.
But the F4 reconstructed solid weak Fz differs from independent printed
support by `1.96 N`, and opposite-side solid action is worse. That is
material to the face gap, so no causal compensation claim follows.
The independently reviewed F5 same-action shell comparison remains the
better shell-side evidence: `+0.776 µm` opening tip-mean difference and
`1.13–1.27 µrad` transverse slope differences, with a validated solid
weak wrench. Pure torque there is a linear influence of the pre-opened
combined load, not a standalone contact state.

The new *validated F5* two-hat common-trace comparison confirms a physical
low-order transfer-shape difference without relying on F4 nodal-force
recovery or a cut traction. Solid first x moments of `Fy/Fz` about `.95 m`
are `16.67/−84.15 N·m`; native P0, P1 and dual give respectively
`31.80/−63.62`, `32.48/−60.60` and `27.19/−60.13 N·m`. The recovered
solid wrench agrees with independent support within `0.001 N/Nm`.
At the F5 combined-load tip, the solid face mean z is `−69.287 µm`;
E4 under the *same solid action* gives `−68.511 µm`, while native
P0/P1/dual give `−69.187/−69.023/−69.174 µm` by linear superposition
of the saved physical influences. Native action therefore changes the
transfer shape in a way that improves this tip observable despite a
shell/solid same-action difference. One scalar improvement does not
establish correct six-channel connection mechanics or select a space.

**Remaining uncertainty and next discriminator:** The shell-side pose,
transverse shear/director interpretation and one-sided retained B3 port
work must be reconciled before a native connection decision. Use the
existing F5 same-action response and validated common-mode transfer to
derive a specifically testable shell trace/footprint law. A one-sided
port-work comparison needs a resolved reference with a verified sided
force partition; the saved shared-node solid and face-stress extrapolation
do not supply one. Check the candidate with objective/patch/work tangents
and the registered mesh-ratio/interface-mode cases, then request the G0
mechanics review. Do not select a multiplier from these finite diagnostics
alone. No new external solve was run. The old
pre-thin-SVD pytest remains permitted and running (session `27660`, PID
`57260`); do not interrupt it. Formal F03 authority remains unconsumed;
G0B is open and G1 barred.

New roots: `.qualification/b3-ge-e4-pl/f03-c1-positive-broken-trace-metric-extreme-ratios-dev-20260926-v2`,
`.qualification/b3-ge-e4-pl/f03-c1-factor4-cut-flux-dev-20260926-v1`,
`.qualification/b3-ge-e4-pl/f03-c1-factor5-cut-flux-bracket-dev-20260926-v1`,
`.qualification/b3-ge-e4-pl/f03-c1-factor4-common-weak-work-dev-20260926-v1`,
and `.qualification/b3-ge-e4-pl/f03-c1-factor4-shell-action-dev-20260926-v1`.
The validated F5 common-mode root is
`.qualification/b3-ge-e4-pl/f03-c1-factor5-common-weak-work-dev-20260926-v2`;
v1 is preserved. Independent read-only review found no calculation blocker
and corrected one interpretation limit; see
`docs/agent_plans/B3_GE_E4_PL_C1_F5_COMMON_WORK_INDEPENDENT_REVIEW_20260926.md`.

## Previous current-state summary — 26 September 2026

**Decision sought:** Defend or revise the native six-channel beam–shell
connection before selecting P0/P1/dual. The bounded transverse-order and
line-resolution diagnosis is complete; classical axial, historical
Q6/finite-pad and native six-channel evidence remain separate.

**Established:** The new detached C1 square-bar/plate experiment has no
shared nodes or contact, matched bar reference axis, root support and end
resultants. Native bare B3 versus factor-four C3D20R work differs by
`−0.035%` for +100 N m torque and `+0.780%` for −1000 N opening force.
The apparent `~2.3 µrad` native retained-pose/solid-section endpoint
torque gap compares unlike measures: native rotation is constant per
half-cell. Against the two solid half-cell Simpson section averages its
differences are only `0.173/0.114 µrad`; native nodal tip work rotation
differs from the solid fitted tip section by `0.082 µrad`. Independent
review verified geometry, wrenches, completion and this interpretation.
One solid level and Simpson averaging are diagnostics, not exact port
equivalence. In the *coupled* F5 comparison, native torque `Fy` transfer
still exceeds solid by `18–20%`, while the same-force opening channels
are closer. Solid face slopes are closer than endpoint B3/solid section
rotations in the three-station RMS, but that scalar does not rank spaces.
The saved torque and opening rigid-section seam-pairing remainders are
`6.91–7.19%` and `6.24–7.02%` of their own seam pairings; they are not
path energy or a causal explanation. Seven native mesh ratios provide
finite-grid rank, transfer and signed action, not inf-sup evidence.

**Remaining uncertainty, next discriminator and action:** Bare torque
work and cell-consistent rotations no longer justify blaming a gross
square-section torsion error or endpoint load-coordinate extraction.
Test the *coupled* retained half-cell trace and its work pullback against
the saved F5 solid bond action, separating shell-side pose from beam-side
port and checking the physical `Fy/Mx/Mz` transfer. A mismatch localized
to the trace calls for a mechanically distinct law; a mismatch in the
underlying shell response calls for that formulation/idealization audit.
Do not change the line law from a small gap, residual, or quotient.
Independently define/review positive C1 broken-trace and primal norms
before using existing ratios as stability evidence; retained B3 yaw jumps
preclude an automatic continuous-trace norm. No more classical axial
refinement is indicated. New roots under `.qualification/b3-ge-e4-pl/`
are `f03-c1-detached-port-dev-20260926-v1` (preserved F4 postprocessing
failure), `-v2` (completed), and `f03-c1-detached-cell-rotation-dev-20260926-v2`;
the earlier cell `-v1` remains preserved. Formal F03 authority is
unconsumed; G0B open, G1 barred. No external process is running.

## Prior bounded decision record — 26 September 2026

**Current decision and next bounded experiment (later 26 September):** The
native six-channel weighted line remains a candidate; no multiplier space
is selected. At source `ed18bea2`, the fixed C1 x2/y4, B3-12 Q4/S3-V2D
transition replaces the first bond cell's four Q4s with eight S3 triangles.
Actual-chart first/mixed work, stress-free reference, row rank, loaded
balance, and positive reported physical shell/beam mode action pass for
P0/P1/dual. The paired raw root is
`.qualification/b3-ge-e4-pl/f03-c1-mixed-q4-s3-transition-dev-20260926-v1`.
Relative to the same Q4 grid, separate torque applied work changes by
`+0.006/+0.039/+0.042%` and opening-force work by
`+0.011/-0.049/-0.045%` for P0/P1/dual. The support-conditioned 1 m
nonaxial signed quotients change `1.575→1.572`, `0.584→0.568`, and
`0.591→0.575`. The asymmetric diagonal causes small reciprocal
torque/shear cross-action; it must not be read as a physical coupling
accuracy result. Numerical shell-component work remains below `0.151%`
of physical shell work in these fixed-grid loaded cases. This detects
no immediate mixed-host defect but is neither a mesh-uniform stability
proof nor a basis choice. Existing axial and reciprocal ratios already
show reference/rank and signed action; do not extend classical axial grids.

**Next discriminating physical-reference question:** F2/F4 saved solid pure
torque and pure opening-force work sum to their combined loads within
`1.5e-9 J`, but the native Q4 P0 torque is about 4% below F4 while its
opening work is about 0.3% below F4. Comparing only combined work hides
this difference. Execute the two pure-load F5 *linear influence* fields on
the already frozen C1 solid geometry, end-face traction, bond, supports,
and 120 s/case limit, then compare each work and the combined
superposition. If the separate solid responses settle, persistent native
torque discrepancy directs the next study to section/warping and
connection idealization; if they move materially, the F2/F4 solid
reference was insufficient. A failed, overlapping, or unbalanced pure
torque field remains a linear algebraic influence only; the saved
pre-opened combined F5 field retains the physical gap assessment. No
outcome alone selects P0/P1/dual, qualifies G0B, or consumes formal F03
authority. This is one bounded extension, not a further axial refinement.

**Decision sought:** A defensible native six-channel beam–shell connection
and stable exact line space, separate from the classical axial comparator
and the historical Q6/finite-pad footprint.

**Established:** On the fixed C1 geometry, the native weighted P0/P1/dual
six-channel rows pass reference, actual-chart work, rank and loaded balance.
Axial-only shell ratios through `1:8` and reciprocal beam-bond ratios through
`8:1` retain rank and positive reported shell/beam signed action. The
reciprocal x2/y4 Q4 fixture holds exterior C1 cuts fixed and uses 2/4/8/16
bond half-cells at source `e915094d`; all loaded mechanics errors are below
`5e-12`. P0/P1/dual final nonaxial quotients are `1.680/0.699/0.701`;
last-step Mx applied-work changes are below `0.14%`. The exact-source root
is `.qualification/b3-ge-e4-pl/f03-c1-hybrid-weighted-reciprocal-ratios-dev-20260926-v2`.
The v1 root preserves an 8:1 P1 diagnostic failure: a symmetric eigensolver
read one triangle of a roundoff-skew compliance Gram while the work split
used its full quadratic action. The corrected diagnostic evaluates the
quadratic Gram explicitly without altering a tangent or solve. Focused
reciprocal and existing weighted-norm tests passed directly.

**Remaining uncertainty and next discriminating action:** No multiplier
space is selected. The signed quotient is finite-grid/support/scale
conditioned, and pointwise gaps are not weak stability certificates.
The full-range P1/dual torque-work shifts are `-1.61%/-3.17%` although
their last-step changes are below `0.14%`; bare B3 tip compliance is
invariant across bond subdivisions. Exact-source Q3/Q5 loaded line
integration at B3-12/26 leaves all six primary work values unchanged to
printed precision. Root:
`.qualification/b3-ge-e4-pl/f03-c1-line-quadrature-attribution-dev-20260926-v1`
at source `b423c2a1`. Thus the drift belongs to the coupled trace/space
discretization rather than free-beam compliance or three-point quadrature.
The saved solid side/root-end seam question is now resolved for the
interpolated F2/F4 fields by a positive seam-factored separation bound.
The third matched solid level completed inside the existing cap, with
positive saved-field surface separation and a `0.108%` F4→F5 applied-work
change. Native 8:1 P0/P1/dual superposed work is
`0.074018/0.073448/0.073395 J` versus F5 `0.074342 J`; different solid
section/warping and native line idealizations prevent selecting the nearest
number. The next bounded mechanics discriminator is the same six-channel
line law across an admitted Q4/S3 transition, with actual-chart work,
drilling/shear, rank, scaled mode and loaded transfer checks. A defect
returns the shell trace/pose law for revision; sound results permit the
registered multi-ratio and physical-wrench assessment. Do not extend
classical axial refinement. Formal F03 authority is unconsumed, G0B open
and G1 barred.

The saved F2/F4 solid underside/top bounds are positive. Initial AABB
overcoverage left eight seam-adjacent side/plate pairs per level unresolved.
An independent read-only seam-factored Q8 edge and plate-top Lipschitz
check then bounded their positive bottom-edge separation by at least
`0.965 µm` (F2) and `0.541 µm` (F4), and all exposed side/root-end faces
rise above the top surface except their permitted shared x=.9 seam edge.
This is a floating-point certificate for saved interpolated fields, not
outward-rounded interval proof, solver-error bound or contact-law validation.
These resolved 3D square-section, distributed-load cases are directional
references, distinct from both the classical axial comparator and the
native six-channel line law.

The bounded third solid candidate at source `83dd50d4` uses factor five,
an explicit 825 mm transition knot, the unchanged C1 clearance/bond,
`-1000 N Fz + 100 Nm Mx`, left plate/beam-root supports and quadratic
face traction. Rebuilt F2/F4 deck bytes equal their saved input files.
It completed in `73.38 s` at
`.qualification/b3-ge-e4-pl/f03-ccx-c1-preopen-combined-factor5-dev-20260926-v1`:
18,000 C3D20R elements, exact declared load/support/bond identity, no
solver warning or failure, work `0.07434208825 J`, and balanced support
wrench. F2/F4/F5 work is `0.073934/0.074262/0.074342 J`. Its 250
unbonded matching-coordinate faces have no negative sampled or Bernstein
reference-normal gap. Independent read-only Q8 saved-field bounds give
`0.245 µm` nonseam and `0.221 µm` seam-factored underside/top margins,
plus positive exposed side/root separation over 600 faces. The hashes of
F5 deck, FRD, DAT and model match its result. These floating-point saved
field bounds do not cover solver truncation, volume Jacobians or contact
law qualification; pose/yaw probes also use a different F5 stencil.

The reciprocal discriminator holds the Q4 shell at two axial/four
transverse bond cells, the physical C1 profile and two multiplier cells,
then subdivides the native beam bond from 2 to 4/8/16 half-cells. It must
use a fresh B3 context per case and keep each dense square block below
1900 rows and each retained context within 120 s. A weak-mode collapse,
loaded transfer drift or inability to execute inside these limits returns
the fixture/law for review; balanced results still require Q4/S3, solid
reference and mesh-uniform stability evidence before any space choice.

The immediate bounded ratio discriminator holds B3-12/24, the 0.1 m bond,
two multiplier cells and the C1 geometry fixed while doubling only Q4
bond resolution four→eight cells. It first checks sparse/dense action parity
on four cells, then rank, reference, normed nonaxial mode and shell/beam
work at eight. Collapse or material drift changes the trace/pose decision;
stable results motivate a separate sparse fixture for the full registered
ratio envelope. No dense matrix may exceed the retained 1900-row cap.

At source `ccc6d965`, sparse/dense parity passed directly and the exact
B3-12 sparse two/four/eight-cell result retained rank and reference
closure. P0/P1/dual nonaxial actions respectively rise
`1.499→1.786→1.858`, `0.577→0.629→0.715`, and
`0.585→0.638→0.726`; weakest reported modes carry positive work in both
domains. Raw root:
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-weighted-sparse-shell8-dev-20260926-v1`.
This isolates shell resolution and does not include loaded transfer. The
next bounded discriminator therefore compares the same weighted spaces'
loaded torque/opening transfer on four and eight shell cells using a sparse
KKT with no dense matrix above the 1900-row cap. Material drift would
revise the law; stable transfer permits broader registered ratios, not
space selection. Independent sparse-path review found no blocking defect
but clarified that `local_grid` doubles both x and transverse y resolution;
this is **not** an axial-only beam:shell ratio test. The shell operator is
dense within 1710 rows and only its solve is sparse. A later axial-only
reference-cut fixture must hold y cuts fixed for ratio attribution.

The exact loaded root at source `02411412` is
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-weighted-sparse-loaded-shell8-dev-20260926-v1`.
P0/P1/dual four→eight x/y refinement changes torque tip work by
`0.528/0.520/0.487%` and opening work by `0.152/0.176/0.203%`; all
reported mechanics errors are below `2.2e-11`. This is balanced shell
refinement, not an axial ratio result. Independent loaded-path review
found no blocking KKT or work defect. The next single-axis test holds four transverse shell cells,
B3-12 and the two multiplier cells fixed while using 4/8/16 axial shell
bond cells: beam-half-cell:shell-cell ratios `1:2`, `1:4`, `1:8`.
The 16×4 bond grid has 1782 shell DOFs, below the retained dense-square
1900 cap. Changed transfer or collapsing normed modes would return the
line trace/pose law for revision; stable results permit a reciprocal-ratio
fixture, never space selection by themselves.

**Axial-only result:** Source `814642d8` has exact-source P0/P1/dual norm
and x4/x8 loaded files in
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-weighted-axial-ratios-dev-20260926-v1`.
The x16 loaded case in that root aborted during gap recovery because the
shared B3 context crossed its 120 s lifetime; `failure.json` preserves
the incomplete run. The unchanged x16 case completed in a fresh context
at `.qualification/b3-ge-e4-pl/f03-c1-hybrid-weighted-axial-x16-fresh-dev-20260926-v1`.
No prior result was replaced. On x4→x8→x16 with y4 fixed, the normed
nonaxial actions are P0 `1.786→1.836→1.849`, P1
`0.629→0.711→0.736`, dual-P1 `0.638→0.723→0.749`; rank remains
`12/18/18`, reference gaps are ~`1e-16 m`, and reported weakest modes
have positive shell and beam work. Combined separate-load applied work
changes x4→x16 by about `0.079/0.113/0.149%` for P0/P1/dual;
largest x16 mechanics error is `5.59e-11`. Point-gap RMS, especially
dual-P1 opening, does not settle identically and is not a weak-gap or
stability certificate. The one-sided axial sequence supports retaining
all three as unqualified candidates pending reciprocal ratios, Q4/S3
interfaces and physical reference. Independent read-only review found no
blocking defect, confirmed x-only refinement and the fresh-context
interpretation, and recommended a reciprocal fixture with a fresh B3
context per case. It did not accept G0B.

**Executed factor-two opening reference:** Source `da1d2a0c` contains the
tested factor-two C1 deck/gap guards (`80/80` focused tests). The
CalculiX result at
`.qualification/b3-ge-e4-pl/f03-ccx-c1-opening-shear-dev-20260926-v2`
completed with one thread and the 120-second per-case cap. Its
manifest/result SHA256 are `2474796056FFAC94E2FE8E8C2A3F7C4BAB4A14C4C791999F9D28829F28BFF993`
and `C73C9B12C583F5A6F1B585361146B0E381BFF8D058167BDC17DB67FC2B16525D`.
Factor two→four changes conjugate opening tip displacement
`69.01466→69.32203 µm` (+0.445%), plate support Fz
`71.84356→72.15187 N` (+0.429%), and plate My
`−47.96981→−48.13664 N m` (+0.348%). Both have positive sufficient
continuous face-gap bounds on the saved top/underside field: minimum
nonseam margins `2.112→0.786 µm` and seam-factored margins
`1.049→0.643 µm`. This is two-level directional evidence, not a
three-level convergence or accuracy qualification. The earlier approval
service HTTP 401 prevented the first commit attempt; an identical reviewed
path later succeeded, so it is no longer the execution blocker.
Direct deck-definition comparison confirms both levels use the same
35 mm plate, terminal bond `x=.9–1 m`, C1 tangent beam axis at `z=.0675 m`,
left/root supports, no contact, and applied end wrench
`(Fz,My)=(-1000 N,+1000 N m)`; the factor-two/four models have
`1024/8192` solid elements and `32/128` unbonded paired faces.

**Pre-opened torque discriminator, read-only:** The factor-four C1
no-contact pure-torque and opening-shear decks have identical 38,041 node
positions and identical structural/support input through the load block
after removing only the shear-name comment (normalized prefix SHA256
`b695640939156c81a16d39f2ff45b1776968e35ca323be4e66947aa70538da4b`).
The only differing model metadata are load forces and audit flags. Both
saved complete FRD displacement inventories match. Their sum at the
declared loads has a positive sufficient opposed-face gap bound:
minimum nonseam margin `0.770 µm`, seam-factored margin `0.540 µm`;
the opening-only margins are `0.786/0.643 µm`. This is exact linear
superposition of the declared no-contact elastic equations, but a
derived field rather than an executed combined-load solve. The pure
torque field itself has 43 negative sampled face gaps and cannot be
scored as a zero-preload physical reference. The derived pre-opened
incremental torque is a candidate only; side-surface admissibility,
actual combined-load execution and mesh convergence remain unchecked.

**Two-level torque-basis result and direct-run decision:** The additional
factor-two pure-torque **basis**, source `4e8f4980`, completed in the
exclusive root
`.qualification/b3-ge-e4-pl/f03-ccx-c1-torque-basis-dev-20260926-v1`.
Manifest/result SHA256 are
`0E5DCC97AED62EA589B0D9E5A553E06A183C47CB8FEAAA17678DE722AA6F2F84`
and `4B4E337DA0D8E74103DC4637986F301AB171A07BDE9FFD3A9A2151687682228C`.
Pure-torque saved sampling has 5 negative face points at factor two and
43 at factor four, so neither standalone result is a physical contact
reference. The factor-two torque/opening decks and full node inventories
match exactly apart from load/comment/audit fields, as at factor four.
Superposed fields have positive sufficient opposed-face gap bounds:
nonseam `2.105/0.770 µm`, seam-factored `0.965/0.540 µm` at factors
two/four. Incremental torque tip rotation is `49.1943→49.4000 µrad`
(+0.418%); plate support `Mx` is `−40.5421→−40.5301 N m` (0.030% in
magnitude). The existing Q4 four-cell six-moment footprint gives
`50.4280 µrad` and plate `Mx=−41.7216 N m`; this is a different
dimension-reduced connection and is **not** scored as accuracy. The
specific next experiment is an executed combined-load solve on these
same two C1 meshes with unchanged supports, end-face quadrature and
bond. For this output-rounded external diagnostic, require maximum
nodal displacement difference at most `2e−5` times the maximum saved
displacement plus `5e−10 m`, and each support-wrench component difference
at most `2e−5` of its declared force (`1000 N`) or moment (`1000 N m`)
scale. These are decision-screen bounds, not relaxed G0 mechanical
criteria. A larger direct/superposed field discrepancy, failed wrench balance or
negative continuous opposed-face bound rejects this route; agreement
only advances side/contact and third-level assessment. No multiplier
space or native bond is selected by the two-level comparison.

**Executed pre-opened combined-load result:** Source `825f1445` adds the
opt-in mixed load to the existing bounded CalculiX runner; `83/83`
affected tests passed. Separate one-thread direct factor-two/four solves
completed under the 120-second per-case cap. Immutable roots and hashes
are in `B3_GE_E4_PL_C1_PREOPEN_COMBINED_DEV_20260926_V1.json` beside
this checkpoint. Across all saved nodes, direct versus separately
executed superposed displacement differs by at most
`0.500/0.540 nm`, below the registered `2.917/2.925 nm` bounds.
Largest plate/root support-component discrepancies are
`0.00060/0.00134` in their N or N m units, below the `0.02` scaled
decision bound. Direct mixed work is `0.073934/0.074262 J` at factors
two/four. Full six-component wrench residuals are retained in raw
results. Both direct saved fields have zero negative sampled opposed-face
points and positive sufficient continuous bounds: nonseam
`2.105/0.770 µm`, seam-factored `0.965/0.541 µm`.
This makes the pre-opened incremental torque an executed directional
external reference. It does **not** qualify virgin pure torque, guarantee
all side-surface noncontact, establish three-level convergence or score
any native law. The next native step must preserve matching C1 geometry,
load, supports, terminal bond extent and work conjugacy before comparing
tip or reaction numbers. G0B stays open and G1 barred.

**Next native C1 geometry discriminator, before execution:** The saved solid
opening-shear field uses a 2 µm C1 tangent-aligned beam-axis lift over
x=`.75–.9 m`; the existing native fixture is straight and uniformly
spaced. Build two native retained B3 chains on the same bounded 12-half-
cell stations, splitting the C1 quadratics at `.825` and `.9 m`: one
straight, one with the exact C1 positions and section frames. Check
reference continuity, local sparse/dense tangent parity, zero reference
residual and the admitted B3 frame guard. Then run one unchanged Q4
terminal-patch KKT with the external opening `−1000 N Fz` on both chains.
If curvature materially alters work, tip response or plate/root transfer,
retain it in the matched native comparator; if negligible at this grid,
retain the exact C1 route anyway but avoid treating curvature as the main
explanation of a solid/native discrepancy. Neither outcome scores physical
accuracy, selects distributing versus rigid/line coupling, or changes G0.

**Native C1 geometry result and next bounded patch test:** The 12-half-cell
native C1 construction has exact reference continuity at `.75/.825/.9 m`,
zero initial residual and zero local sparse/dense tangent difference on
the tested fixture. At Q4 patch level four and `−1000 N Fz`, straight
versus exact C1 gives distributing tip `−75.60015/−75.59814 µm` and rigid
tip `−75.42529/−75.42327 µm`; plate support Fz changes by under
`0.001 N`. The C1 curvature is therefore negligible for this bounded
comparison, while the saved solid's conjugate tip displacement is
`69.32220 µm`. External DAT reactions put `72.15187 N` on the plate and
`927.84815 N` at the bar root; the native C1 distributing split is
`85.49282/914.50718 N`, rigid `86.22476/913.77524 N`. These are
different continuum and reduced models, and finite distributing/rigid
laws are not the continuum bond; the numbers are diagnostics, not scored
accuracy. An older *different-geometry/load-map* detached solid gives
`190.541 µm` against `192.024 µm` for the native free B3, suggesting
but not proving that bare beam compliance alone is not the full coupled
gap explanation. The next discriminator holds the exact C1 beam, load,
supports, laws and section fixed while changing only the bounded Q4
terminal patch grid from two to four cells. Movement of tip work and
plate/root split toward the solid values directs attention to shell/patch
resolution; little movement directs attention to connection work or
dimension-reduced shell/section idealization. Two levels cannot establish
convergence or select a law; do not exceed the existing dense row cap.

**Physical-work alternative, before execution:** The two-to-four-cell Q4
patch screen below does not close the solid/native opening-shear gap.
On the same exact C1 beam, Q4 patch grid, support, section and load, test
the existing six-resultant *surface-position moment* functional alongside
the distributing/rigid pose ties. Split its integration at the actual
nonuniform native half-cell boundaries, verify zero reference gap, rank,
work and balance, then compare tip work and plate/root wrenches. A
substantial coherent move toward the solid keeps the physical surface
law for further independent mechanics review and mesh study; no movement
redirects effort to reduced shell/section idealization or bond extent.
This finite footprint is not a true exact line law and cannot select a
line multiplier from a single grid.

**Physical-work fixed-grid result and next check:** At Q4 patch level four,
the actual C1 surface-position-moment trace has zero reference gap,
six independent rows, no drilling columns and a `0.01 m²` footprint.
Under `−1000 N Fz`, its tip is `−70.25176 µm`, plate support is
`Fz=73.07544 N`, `Fx=5947.899 N`, `My=−49.49825 N m`; work and
global KKT balance close within `4.5e−12` in the recorded numerical
measure. The same-grid distributing/rigid pose ties give
`−75.59814/−75.42327 µm`, `Fz=85.49282/86.22476 N`. The saved solid
gives conjugate tip `69.32220 µm` and plate `Fz=72.15187 N`,
`Fx=5978.922 N`, `My=−48.13664 N m`. Surface moments therefore move
the fixed-grid tip and support quantities coherently toward the solid;
this is a *development discriminator* across different dimensional
idealizations, not a qualified `1%` comparison. The next bounded check
changes only Q4 patch cells two→four with the same C1 beam and physical
surface law. If this change is small relative to the remaining solid
gap, preserve the law for independent mechanics review and a sparse
mesh study; if material, resolve Q4/interface discretization first.
No multiplier space, true-line operator or footprint is production-selected.

**Two-level result and bounded decision:** With the same C1 beam and
`−1000 N Fz`, surface-position moments change from Q4 patch cells two→four:
tip `−70.11908→−70.25176 µm`, plate Fz `71.99932→73.07544 N`,
plate Fx `5950.563→5947.899 N`, plate My `−49.42810→−49.49825 N m`.
The tip change is small but moves slightly *away* from the solid
`69.32220 µm`; the Fz partition changes `1.076 N`, comparable to the
remaining `0.924 N` four-cell difference from the solid. Rigid and
distributing ties remain around `75.3–75.6 µm`. Thus the surface law is
the strongest **finite-footprint development candidate** on these matched
loads and support observables, but two levels do not establish
convergence or the `1%` external threshold. The actual nonuniform native
half-cell cuts now drive surface quadrature; at C1 patch level two the
finite-chart reference gap and first directional row agree with the
linearized trace within `1e−12`. Existing straight-reference mixed-chart
checks remain separate. A sparse third level and independent mechanics
review, not a raised dense row cap, are the next meaningful finite-patch
steps. This does not settle a zero-width exact line law or physically matched
torque accuracy.

**C1 physical torque-work check and line-space decision:** On the same
exact C1 native beam, 35 mm Q4 plate, 0.1 by 0.1 m physical terminal
footprint and +100 N m tip torque, the surface-position-moment law gives
tip twist `50.024→50.428 µrad` and plate support Mx
`−42.186→−41.722 N m` for patch cells two→four. Both grids have positive
physical shell strain work (`0.001955/0.001952 J`); numerical-completion
work is `2.25e−7/1.28e−7 J`, respectively. Total wrench/work errors are
below `4.1e−12` in the recorded numerical measure. The focused C1 test
now checks external torque work, support-moment balance and physical-work
dominance. The actual C1 finite chart also passes nonzero-gap,
nonzero-multiplier first and mixed finite differences (`8.1e−10` and
`1.7e−9 J` errors), a common finite rigid motion (`1.9e−16` gap error)
and reference-row parity (`4e−17`); six focused checks pass. These results
support retaining this **finite-width distributing
footprint** for review; the saved solid torque field remains contact-
inadmissible, so no torque accuracy claim follows. This law's six
integrated moments do not enforce a pointwise solid bond or constitute the
required true line law. Across the existing native line experiments, P0
line intervals 8→16 on fixed Q4 x8/y8 and beam-half32 still move loaded
torque by `17.3%` and transverse tip displacement by `10.5%`; at P0 m16
the shell-only row rank is `69/96` while the complete and beam-only ranks
are `96/96`. The normed transverse minimum shifts toward an alternating
Fz density dominated by beam work as line resolution increases. These
are discrete representability and mode diagnostics, not a mesh-uniform
inf-sup bound or a multiplier selection. Next derive a physical six-channel
line work law with a distinguishable shell trace, check its fixed-grid
transfer and normalized modes, then assess the registered mesh ratios.
Do not add P0 rows merely to reduce a gap or the quotient.

**Independent footprint review and unresolved-gap result:** A read-only
mechanics reviewer found no work-conjugacy, objectivity or finite-chart
blocker in the six-resultant law at source `9c5e8093`. The dual traction
of its mean/first-moment coordinates gives the stated force and moment;
finite multipliers are material generalized duals, so current spatial
wrenches require virtual-rigid-motion recovery. The law intentionally
does **not** tie the solid face pointwise: the nonzero affine gap
`g=(epsilon·(x−.95),0,0)` has zero mean and all three first-moment rows.
The added analytic control passes this null mode without weakening the
existing six-channel work checks. Complete C1 native records are retained
in `B3_GE_E4_PL_C1_NATIVE_PATCH_DEV_20260926/{manifest,results}.json`
(source `e95c43af`) and the immutable V2 sibling (source `cd7a1e52`).
Their tip, reaction, physical/numerical-work and mechanics-error fields
match exactly. V2 recovers the linearized shell-top/beam-bottom pointwise
gap at the declared quadrature: for +100 N m torque, RMS
`0.09617→0.09881 µm` and maximum `0.16301→0.17223 µm`; for −1000 N
opening Fz, RMS `0.16919→0.16920 µm` and maximum
`0.29191→0.32467 µm`. Six weak gaps remain below `7e−19` in the
reported mixed units. Thus the footprint remains a credible **distributing
connection** candidate; its proximity to one solid opening-shear tip and
support split cannot establish a bonded-line or pointwise-bond claim.
The bounded sparse third grid may later assess this footprint's support
partition, but cannot eliminate its admitted unresolved mode. The
independent review did not accept G0B or the physical torque reference.

**Continuous-gap precondition, before execution:** For the saved C1 opening
field, convert each paired Q8 face's *corresponding-material-coordinate*
vertical separation into its biquadratic Bernstein control net. If any
control coefficient is negative, this simple sufficient nonpenetration
route fails and requires a more precise geometric check; if all are
nonnegative, the corresponding-coordinate gap is continuously nonnegative.
On the eight seam-adjacent faces, factor the exactly shared zero-gap edge
and check the remaining control net. This is only a precondition: actual
same-deformed-XY nonintersection also requires bounding the horizontal
reprojection correction. It does not qualify the reference by itself.

**Reprojection bound, before execution:** The corresponding-coordinate
control nets pass with a strict positive factored seam margin. Bound each
saved face's horizontal plate–bar mismatch and bar vertical derivative by
Bernstein controls, and the inverse horizontal map by its affine Jacobian
minus a bounded deformation perturbation. If the worst possible vertical
reprojection correction exceeds the proven gap margin, the control-net
route is inconclusive; if every margin stays positive, the sampled shear
candidate has a continuous *within-paired-face* gap bound, but face-edge
coverage and mesh convergence remain separate. Do not add more point
samples to resolve this question.

**Global map follow-up, before execution:** If the local face bounds pass,
recast them in common physical material XY coordinates over the convex
unbonded rectangle. A uniform Bernstein bound `||D R_xy−I||<1` for the
deformed bar map makes it globally injective and gives an inverse
Lipschitz bound across face edges; combine it with a global vertical
Lipschitz bound and each face's factored seam gap. If the resulting lower
gap is positive for every overlapping deformed XY point, retain a
continuous contact-free *saved-field* shear reference candidate. If not,
the face-edge issue remains open. This still does not establish mesh
convergence, exact-solution nonpenetration or native accuracy.

**Continuous saved-field gap result:** All 128 paired unbonded Q8 faces
have nonnegative corresponding-coordinate biquadratic Bernstein gap
controls. On the eight faces adjoining the x=`.9 m` bonded seam, the
control net's zero seam edge is exact and the factored positive gap has a
minimum control coefficient of `643.6 nm`; other faces have minimum
`786.4 nm`. The deformed bar XY map over the convex unbonded rectangle
has a global `||D R_xy−I||_F ≤ 4.891e−5` Bernstein bound and is therefore
injective with inverse Lipschitz factor `1/(1−4.891e−5)`. Its vertical
Lipschitz bound is `1.066e−4`; the maximum corresponding-coordinate
horizontal mismatch bound is `3.336 µm`. The resulting worst vertical
reprojection correction is at most `0.356 nm`. Every nonseam lower gap
remains at least `786.1 nm`; every seam-face gap remains at least
`(1−t)·643.4 nm`, where `t=1` is the bonded edge. Thus the *interpolated,
rounded saved displacement field* has positive vertical separation at
every overlapping deformed XY location on the specified unbonded face
pairs, with zero permitted at the shared bonded seam. This is a sufficient
continuous face-gap bound, not a proof about unsampled side surfaces,
the exact unrounded solver solution or mesh convergence. A 384-point
cross-check reconstructs Q8 values from Bernstein coefficients within
`3.4e−16 m` and x-parametric derivatives within `1.3e−11 m` of finite
differences. The identical control-net method has five negative-control
faces in each retained torque field, consistent with their independent
negative-gap samples; a negative control alone is not a penetration proof.
No external accuracy or native multiplier selection follows yet.
The read-only calculation is now reproducible through
`bound_c1_unbonded_vertical_gap` in the existing solid-pose diagnostic,
using the saved deck, FRD and `model.json` face pairs. It validates the
128-face rectangular inventory and returns typed positive/inconclusive
status. The saved opening field returns
`POSITIVE_SAVED_FIELD_FACE_GAP_BOUND`; the two retained torque fields return
`INCONCLUSIVE_FACE_GAP_BOUND`, consistent with their separate sampled
penetration witnesses. The two directly affected test files pass `79/79`
with a workspace-local disposable test directory. This source-level
development check still needs independent mechanics scrutiny before it
can support a G0 acceptance record.

**Next bounded decision probe, before execution:** At the interior of the
same saved C1 factor-four, 35 mm terminal bond under +100 N m, compare the
three-dimensional plate's polar-band and transverse-material-chord frames
with the independently fitted solid bar section at identical x stations.
The competing explanations are that the chord's altered native torque split
tracks an actual finite-width material-line motion, or that it is merely a
different discrete constraint with no better physical correspondence. Use
the existing no-contact and matched penalty displacement fields, unchanged
geometry/load/support/section and shared bonded nodes; record both pose gaps,
section-fit residuals and the contact-field limitation. If the chord is
consistently closer at interior bonded stations with a credible section fit,
retain it for a later matched loaded/reference check; if not, stop treating
it as a preferred law. Neither outcome selects a multiplier, certifies the
external result, or justifies new axial or line-row refinement. The existing
B2 F09 experiment continues independently. Formal F03 authority remains
unconsumed, G0B open, G1 barred.

**Follow-on reference discriminator, before execution:** The corrected
same-station solid projection below can distinguish pose meaning but cannot
admit the C1 torque reference while its unbonded faces penetrate. Reuse the
identical C1 tangent-aligned section geometry, 35 mm plate, shared terminal
bond and left/root supports for a separate *opening* `−1000 N Fz` quadratic
end-face load. This tests whether a contact-free, physically admissible
transverse-shear reference can advance independently of torque contact.
Require exact applied wrench, shared-bond identity, one completed solve,
balanced support wrench and nonnegative deformed unbonded-face separation
before using it even as a directional comparator. A negative gap or failed
solve stops this route; an open, balanced case advances to a matched native
shear model and refinement, not an accuracy score or multiplier selection.
Keep the existing one-thread, 120-second development limit and preserve all
older deck identities.

**Corrected same-station projection result (development only):** The first
read-only attempt used an axial-area average for the polar frame and is not
decision evidence: native `physical_top_transverse_band_005` has no axial
average. Recomputing the solid's top-surface x/y gradients and through-
thickness director at the same material stations `.925/.950/.975 m`, with
left-host x derivatives and exact Q8 width integration, gives polar versus
chord yaw gaps to the fitted 3D bar section of `−1.529/−1.448`,
`−1.598/−1.376`, and `−1.731/−1.336 µrad` in the saved no-contact torque
field. The matched penalty field gives essentially the same values:
`−1.528/−1.447`, `−1.599/−1.376`, `−1.731/−1.337 µrad`. The y-gradient
integral agrees with the material end chord within `4.9e-12` in the
dimensionless gradient. Chord reduces the full orientation-gap norm by
only `0.064/0.141/0.185 µrad` no-contact; fitted-section RMS residual is
`16.6/20.6/30.1 nm`, and the shared x-rotation gap remains
`1.15/1.80/2.89 µrad`. Thus the chord is a somewhat closer *yaw
projection* in this bonded interior, but the unresolved section deformation
and much larger pose gap prevent a physical law choice. Contact changes
these interior numbers little, yet its sampled penetration still blocks
external accuracy use. Saved deck/FRD SHA-256 pairs: no-contact
`cc88870f…`/`543dbbb0…`, penalty `54c15a39…`/`f013af27…`; exact hashes
remain in their protected raw roots. The same C1 final-state tip load work
measure changes only `49.400037→49.398605 µrad` with penalty contact and
plate support Mx changes `−40.53012→−40.54268 N m`; this tiny global
change is not integrated path-work or a contact-admissibility certificate.

**Opening-shear route prepared:** Existing deck builder now admits only the
explicit C1 `−1000 N Fz` no-contact opening case with the unchanged
two-quadratic tangent-aligned reference profile, 2 µm clearance, 35 mm
plate, C3D20R, quadratic face load, factor four and full displacement
output. The torque deck SHA-256 identity and node/element/support/shared-
bond identities remain unchanged; the new shear deck has the exact applied
force/moment wrench `[0,0,−1000,0,+1000,0]` in SI units. Focused builder
checks pass `74/74`. This is deck preparation, not a completed physical
shear result.

**Opening-shear result and decision (development only):** Source
`8dd140a6525a338fc4311f047e937ed1e663dd87`, pinned CalculiX 2.23,
one thread, and a 120 s limit produced one completed factor-four C3D20R
step in `18.612 s` with no solver failure. Protected root:
`.qualification/b3-ge-e4-pl/f03-ccx-c1-opening-shear-dev-20260925-v1/`;
deck/FRD SHA-256 `49b6e57d…`/`499dd3ea…`. The actual applied wrench is
`[0,0,−1000,0,+1000,0]` within `2e-12` in SI units; DAT-derived total
support imbalance reaches `0.000623 N` and `0.0000735 N m` in individual
components. Final-state conjugate load displacement is `69.322 µm` and
`F·u=0.069322 J`, not integrated path work. The existing 9×9 face sample
has `0/10,368` negative same-deformed-XY gaps, minimum `10.329 nm`;
the preregistered 17×17 near-seam check has `0/36,992`, minimum
`3.040 nm` at face 127, `ξ=η=.990575`, with no projected point outside
its paired face and XY residual below `1e-14 m`. The same projection
reproduces the historical no-contact torque minimum `−7.113 nm` and the
penalty torque minimum `−3.162 nm`; its slightly different penalty negative
sample count reflects near-zero points and is not an acceptance metric.
The positive shear samples retain a *directional* external candidate only.
They approach the bonded seam and cannot certify nonintersection or mesh
convergence. Do not add more sampling levels as a surrogate for proof.

The same saved shear field also gives an independent kinematic check at
interior bond stations x=`.925/.950/.975 m`: width-averaged solid midplane
slopes are `−61.87/−63.02/−62.15 µrad`, while through-thickness inferred
director pitches are `+57.65/+59.85/+60.14 µrad`. Their physical
transverse-shear indicators are therefore `−4.22/−3.17/−2.01 µrad`, not
zero. Fitted bar-section y-rotations are `+64.63/+63.37/+62.77 µrad`,
with `35.6–41.7 nm` section-fit RMS residuals. These are 3D field
projections, not E4 director states or a native/solid acceptance comparison;
they reinforce the requirement to preserve independent shell shear rather
than identifying director rotation with geometric surface normal.

**Near-seam gap follow-up, before execution:** The source-bound C1 opening
solve completed and the same-deformed-XY 9×9 face sample is positive, but
its minimum is only `10.33 nm` near the bond seam. A denser 17×17 sample
on the same saved 128 face pairs distinguishes an interior overlap missed
by the coarser grid from a still-open *sampled* field. Any negative sample
rejects the no-contact directional reference; all-positive samples retain
it only for continuous-gap and mesh checks before accuracy scoring. This
does not change geometry, loading, resource limits or native selection.

**Numerical-completion discriminator, executed:** On the registered matched Q4/S3 torque cases, the diagnostic changed only E4's declared numerical tangent factor `0.5→1→2`. Both poses retained scaled linear residuals below `1.1e-16` and work errors below `2.8e-15 J`; factor `1` exactly reproduces the saved loaded responses. Across `0.5→2`, the largest shell support-torque change relative to factor `1` is about `0.53%` (S3 polar band); the chord changes by about `0.34%` (Q4) and `0.31%` (S3). Tip twist changes by under `0.5%`. Thus the roughly `30%` pose-law torque-partition difference is not primarily driven by this bounded stabilization variation. This does not prove zero-drilling or refinement independence, select a line law, or supply the missing physical torque reference. Stop stabilization tuning and continue the physical connection/reference discriminator.

**Fixed-grid loaded and physical-mode result:** On the same 35 mm Q4/S3 x8/y4 panel, eight native beam half-cells, square-section torsion constant, `.0675 m` beam-axis offset, full-left support and four P0 intervals, the transverse chord changes +100 N m tip twist from `28.171→26.969 µrad` (Q4) and `27.793→26.591 µrad` (S3) relative to the polar band. Shell support-torque magnitude rises `13.885→18.115 N m` and `12.848→16.794 N m`; under +1000 N Fz, tip-z rises `43.008→43.555 µm` and `43.239→43.676 µm`. Work and global wrench residuals are small, but numerical shell-component energy is nonzero (`0.67–1.14%` of physical shell energy for torque). In the matched positive-physical/absolute-retained H^(-1/2) diagnostic, both 24-row spaces are full rank; Q4 lower quotient changes `3.658→3.860`, S3 `4.724→5.017`. The S3 weakest mode remains about `94%` Fz by the chosen norm and about `94%` physical work for the chord. This is a bounded, norm-dependent improvement of about `6%`, not a mesh-uniform stability result. The roughly `30%` torque-partition change and missing physical reference prevent a defensible selection; stop this pose before ratio escalation rather than using a small residual or quotient as proof.

**Current decision:** Keep the transverse-chord native line pose experimental and stop its mesh-ratio escalation. Its final focused file passes `26/26`; on the same 35 mm Q4/S3 physical geometry it changes shell torque partition by about `30%` while improving the bounded positive-action lower quotient only `5.5–6.2%`. Torque still carries about `0.7–1.1%` numerical shell-component energy. Neither pose has a verified physical torque reference or mesh-uniform line-stability result, so neither selects P0. The matched C1 factor-4 contact solve executed, but same-deformed-XY projection still finds `31/10,368` negative samples, minimum `−3.1621 nm`; they occupy five faces, with the dominant 17 samples on the one face with eight active contact springs. Preserve its parser-marked failure and do not score native accuracy. The later runner change accepts only that exact generic *STATIC notice; its focused deck/parser file passes `73/73`, and the historical raw result is unchanged. The next reference discriminator must distinguish missed/underintegrated contact from an inadmissible connection geometry on the same load/support/section model; only a nonpenetrating, balanced and mesh-checked result can enter native comparison. Continue the already-running B2 F09 diagnostic independently. Formal F03 authority is unconsumed, G0B open and G1 barred.

**Process observation, 26 September:** The previously recorded session handles `87958` and `37844` now return unknown-process errors, and PIDs `45760` and `49308` are absent. No terminal output was recovered from either handle. The fixed-source transverse-chord check independently passed `26/26`; do not infer that the original pre-fix run passed. The F09 exact-rounded/sparse-scaling diagnostic has no recovered result and must not be marked passed or failed. Older handles `82615` and `63398` were not re-run. A new F09 experiment requires an explicit review of its surviving output and original authority before dispatch.

**Operator interpretation:** A focused Q4 check disproved the initial assumption that center interpolation equals symmetric band averaging across the piecewise trace at `y=0`. The chord changes both Fz and yaw rows, and its supported row space is distinct. Actual-chart derivative, rigid-work and shell-shear checks pass on Q4/S3. The matched loaded and physical-mode screens above establish a finite-grid difference, not improved accuracy or stability under refinement. Source `112f62d6` corrected the selector-shadowing bug before final tests.

**Next matched-contact discriminator (before execution):** The coarse C3D8 penalty result cannot be paired with the C1 factor-4 C3D20R no-contact result. On the *same* C1 tangent-aligned terminal geometry, shared bonded patch, +100 N m tip torque, 35 mm plate, quadratic face load and left/root supports, enable complete unbonded-face surface-to-surface linear penalty contact at the previously tested `4.2e14 N/m³` stiffness. Retain one thread and the existing 120 s limit. First check exact deck geometry/load/support identity and 128+128 contact-face coverage; then inspect execution, contact output, sampled deformed gaps and wrench balance. If it fails to execute or still penetrates, do not score native accuracy; diagnose contact formulation or revise the physical reference. If it yields an admissible field, a matched shear case and mesh/contact convergence are still required. Do not infer a hard-contact solution from one penalty run or vary stiffness again automatically.

**Decision sought:** A defensible native six-channel beam–shell connection and stable exact line law. The finite footprint remains provisional; no multiplier is selected. G0B is open, G1 barred, and formal F03 authority unconsumed.

**Established facts:** The transverse-order diagnosis is complete. The C1 tangent-aligned, factor-4 C3D20R no-contact torque solid has a reviewed interior penetration witness of `−7.1125 nm`, so it is not a physical accuracy comparator. A separate-node terminal `*TIE` reproduces its shared-node no-contact solve (`2.30e-17 m` maximum probe difference; identical final `F·u`), but its complete mortar-contact solve fails before an increment: CalculiX rejects contact slave edge nodes used in tie MPCs. The separate factor-1 C3D8 complete-face penalty deck executes and balances the wrench; increasing normal stiffness 10× reduces reported contact-point overclosure `2.26→0.33 nm` while sampled interior penetration remains `−12.24→−10.62 nm` (`24→14` negative samples of 648). These are different meshes and reference geometries, not a paired accuracy comparison. The final `F·u` change is `0.0135%`, not integrated path-work convergence. Independent read-only reviews found no material error in these narrow conclusions. All new solves used pinned CalculiX 2.23, one thread and the existing `120 s` limit. Protected roots under `.qualification/b3-ge-e4-pl/`: `f03-ccx-c1-tangent-spatial-gap-derived-dev-20260925-v1`, `f03-ccx-solid-terminal-separate-tie-dev-20260925-v1`, and `f03-ccx-solid-terminal-penalty-face-dev-20260925-v{1,2}`; earlier failed roots remain preserved. Classical axial, historical Q6/finite-pad, and native six-channel evidence remain distinct.

**Remaining uncertainty:** No physical torque contact reference or matched curved native coupled solve is admitted. The fixed-mesh penalty overlap may depend on mesh or contact discretization; the samples do not certify a global gap. Seven registered line mesh ratios are finite and full rank, but their positive physical-compliance transverse mode and loaded transfer remain resolution-sensitive. An indefinite KKT quotient is not an inf-sup measure and does not select P0/P1/dual.

**Combined interface-stability interpretation:** A read-only comparison of the already saved six-case joint Fz physical-action record `f03-native-joint-fz-physical-dev-20260925-v1/results.jsonl` gives Q4 lower quotients `9.00→3.10→1.11` under H^(-1/2), versus `11.15→7.35→5.43` under the finite-width H^(-1) diagnostic, for shell-axial/beam-half/Fz counts `4/4/2→8/8/4→16/16/8`; S3 gives `9.37→3.19→1.14` and `11.62→7.61→5.53`. The saved H^(-1) weak-mode B3 transverse-shear share rises about `5→17→62%`. These data jointly show a norm-sensitive high-frequency mode and a changing physical action split. Three levels do not establish a positive continuum limit, while the distinct fixed-mesh loaded torque/partition drift still blocks space selection. Do not extrapolate one quotient, treat the indefinite retained KKT spectrum as an inf-sup constant, or restart finer axial sweeps from this observation.

**Next discriminating work and decision:** Stop face-set, orientation and penalty-stiffness variants on this factor-1 seam deck. The immediate transverse-order diagnosis is complete; further P0/P1/dual refinement alone cannot decide the law. At a single material station, tractions on a zero-length transverse strip give only five independent local section actions: the eccentric-axis `My` is tied to `Fx`. Re-origining the same finite-pad six moments does not add a mode; the already tested director-`My` hybrid gains rank but its fixed-mesh torque and plate partition drift. The native spatial port has a rigid section frame, not a warping displacement trace. The next *operator* discriminator must therefore specify genuinely different connection work and the beam-section and shell-shear modes it constrains or leaves free. On the unchanged supported Q4/S3 and native-B3 model, compare its compliance-weighted row space with the existing law **before solving**: coincident spaces stop the proposal; a distinct space proceeds to objective work, loaded `Mx`/`Fz`, support partition and positive physical-compliance modes. Only a credible result proceeds to frozen mesh ratios. For the external comparator, specify complete bond/noncontact coverage with a verified contact field; require nonpenetration, wrench balance and mesh/work convergence before scoring accuracy. A failed reference does not imply native formulation failure. Do not resume classical axial refinement. [CalculiX contact restrictions](https://www.dhondt.de/ccx_2.22.pdf).

**G0 native pose discriminator, before execution:** Test an opt-in shell-side frame made from the physical E4 director and the deformed transverse material chord across the declared `y=±0.05 m` bond width, with centerline position and no axial averaging. The current polar-band frame uses both in-plane gradients, while this frame follows the transverse material line; under `u_y=γx` its yaw is zero rather than `γ/2`, and under `u_x=γy` it is `−γ` rather than `−γ/2`. Thus it is a distinct connection idealization, not a row re-origin. First check reference consistency, common rigid motion, Q4/S3 actual-chart first/mixed-second variations, shell-director shear freedom, and the supported scaled row-space projector against the existing polar-band law on fixed shell x8/y4, native beam-half8, P0-4. If the work space coincides or any work/shear/derivative check fails, stop the candidate before a loaded solve. If distinct and mechanically consistent, use that unchanged geometry for separate `+100 N m Mx` and `+1000 N Fz`, support partitions and positive physical-compliance modes; only credible loaded transfer warrants registered ratios. This adapts the single-material-direction surface-triad idea to E4's independent director and exact multipliers, so the published Kirchhoff–Love/regularized result does not qualify it. [Beam-to-surface formulation](https://link.springer.com/article/10.1007/s00466-025-02647-9).

**Independent B2 F09 diagnostic, before execution:** The existing mixed-elbow extreme-area case separates exact rounded assembly from sparse factorization: the rational solve of the rounded matrix agrees with the physical force-method reference, while the default sparse solve loses the weak force response. Test the unchanged 12-free-row assembled matrix with bounded sparse ordering/pivot choices and physical diagonal scaling, retaining separate force and moment residuals against their applied scales. Recovery of the exact rounded and physical responses with those checks would justify designing a reviewed scaled sparse route for F09. Failure would direct F09 toward a different stable representation or an explicit representability limit; it would not justify a shear floor, a changed historical B2 law, or an F09 pass. This diagnostic is separate from the B3-GE/E4-PL line decision and does not consume formal F09 authority.

**Native section-work boundary:** Source inspection of `NativeHalfCellSpatialPort` confirms a lifted centerline and rigid material frame with a six-row pose tangent; the retained generalized B3 operator carries its existing six-component cell strains/resultants, not an independent section-warping displacement or conjugate warping energy. Adding a freely adjustable warping displacement only inside an attachment would therefore create an unpaired interface action, not a consistent extension of this B3 element. A restrained-warping beam is a separate derived formulation with additional section data/state and work; it cannot be used as an unreviewed shortcut to pass the exact-line gate. The next native candidate must either stay within the present B3 pose/section contract or explicitly seek a formulation amendment. This is a source-and-work inference, not a finding that the existing B3-GE or every exact line connection fails. [Warping theory context](https://backend.orbit.dtu.dk/ws/files/128071152/Analysis_and_Design.pdf).

**G0 F07 bounded descriptor check, before execution:** Test one conservative two-translation system with a massless retained coordinate and an exact displacement constraint. In order `(u_shell,u_beam,r,lambda)`, use `k_shell=12`, `k_beam=20`, `k_retained=30`, physical masses `2,3`, zero inertia for `r` and `lambda`, and constraint `u_shell-u_beam=0`. The independently eliminated finite eigenvalue is `(12+20*30/(20+30))/(2+3)=4.8`; the three remaining descriptor eigenvalues are infinite. Require exactly this finite count/value, normalized equation and constraint residuals `<=1e-12`, and no mass added to algebraic coordinates. A pass establishes only this G0 elimination/descriptor identity; it does not qualify B3/E4 mass operators, free-free modes or buckling. A failure sends the constrained-mass design back for correction without affecting F03 or consuming its authority.

**G0 F07 bounded result:** `tests/test_b3_e4_g0_f07_massless_descriptor.py` passes `1/1` in `0.35 s` with the prescribed finite eigenvalue and algebraic-variable checks. This closes the small descriptor identity only. Physical B3/E4 inertia, retained-coordinate mass coupling, constrained sparse modes, free-free rigid modes and buckling remain open; G0B and G1 statuses do not change.

**F07 native physical-mass development (27 September):** On one supported
Q4/native-B3 owner, `test_b3_e4_g0_f07_native_physical_descriptor.py`
checks rigid-translation mass work `4.4` against shell `0.4` plus beam
`4.0`, positive retained-cell inertia, exact zero mass for six algebraic
retained coordinates and six multipliers, and a full descriptor with 24
finite and 18 infinite roots. Its first three finite roots match the
native factor modes. Direct execution passed; an initial standard pytest
collection stalled and was stopped, then the same focused file passed
`1/1` in `2.57 s` with the worktree environment, non-JIT and single-thread
settings. Details and source hashes are in
`B3_GE_E4_PL_G0_F07_NATIVE_PHYSICAL_DESCRIPTOR_DEV.md`. This is one
conservative current-rest mass/descriptor feasibility result. Mixed Q4/S3,
free-free rigid modes, loaded/prestressed spectra, mesh convergence,
release behavior and buckling still bar F07/G0B acceptance.

## Prior state — 25 September 2026, native connection decision

**Decision sought:** Keep the six-position-moment 100×100 mm finite footprint as a provisional native connection while deriving a mechanically distinct, stable exact line law. No footprint or multiplier is production-selected. G0B remains open, G1 barred, and formal F03 authority unconsumed.

**Established facts:** The transverse-order/line-resolution diagnosis is complete, and existing P0/P1/dual evidence does not select a stable multiplier. The provisional 100×100 mm footprint passes bounded local/loaded controls, but its plate-force partition remains mesh-sensitive. A proposed six-resultant moving pad on the *same* physical patch is only an invertible re-origin of that law; Q4/S3 supported row spaces coincide, so no further solve was run. In the saved fully bonded 3D field, a 125 mm patch's torque Mx reduction gap is concentrated at the loaded tip and a smaller yaw reduction persists inside. The complete solid-section rigid-fit residual grows from roughly `10–12 nm` inside to `49.9 nm` at the tip. The shared face remains continuous. Four focused projection controls pass; this is not native-footprint accuracy evidence. Classical axial, historical Q6/finite-pad and native six-channel evidence remain distinct.

**Remaining uncertainty:** No tested exact line law has stable supported loaded transfer, and a physical sixth local action cannot be created by changing coordinates. The terminal solid torque has a 2 µm piecewise tapered clearance absent from the native axis; its 6.36 nm minimum sampled gap is not a continuous nonintersection certificate. A literal lifted native axis failed B3's tangent-aligned frame guard, so the saved taper is not matched by changing nodal heights alone. In its saved torque field the deformation-induced seam slope changes sign across the width, so a smooth zero-slope clearance cannot be assumed contact-free. The saved opening-shear solid uses opposite load sign and zero clearance. Section deformation, shell shear and connection work remain confounded. G0B is open; this does not establish formulation failure.

**Next discriminating experiment and resulting action:** A new exact line law must have a justified physical mechanism beyond the same six patch moments, with explicit section/warping and shell-shear freedoms. Only a distinct law receives fixed-grid work, transfer and positive-mode checks before registered ratios. Separately, first define a common terminal native/3D reference geometry whose B3 section frames and bonded patch are valid; then certify deformed unbonded-face nonintersection or admit consistent contact before paired torque/opening-shear solves. Compare tip work, support partitions, six interface resultants and virtual work, spatial transfer and section-fit residual. Complete agreement can support a provisional candidate; tip-only agreement cannot. Recover the native multiplier pullback and a *declared* quadrature traction representation, not a unique continuum contact traction. Stop old axial and line-row refinements; preserve failures and thresholds.

**Matched-reference geometry discriminator:** A C1 two-quadratic clearance transition is algebraically possible over x=.75–.90 m: with t=(x-.75)/.15, use z-offset d(1-2t²) on 0≤t≤.5 and 2d(1-t)² on .5≤t≤1, with d=2 µm. Position and tangent agree at t=.5, and the tangent is horizontal at both ends; the maximum slope magnitude is 2d/.15 = 26.67 µm/m. This is only a candidate construction, not an admitted native/solid model. Its B3 nodal frames must match each quadratic's exact tangent and remain identical at the shared node; the solid mesh must split at the transition's midpoint and keep the bonded x≥.90 face conforming. The saved *old-geometry* torque field has positive deformation-induced gap slopes on some free faces next to x=.90. A C1 clearance with zero seam slope would then overlap locally if that old field were held fixed, whatever d is; a newly solved field could differ. Therefore the next bounded preflight must test native curved-reference admission, solid element quality and a continuously bounded deformed-face gap under the same geometry before any cross-model accuracy score. If a common contact-free geometry cannot pass, use a declared consistent contact reference rather than increasing clearance or comparing unlike models. This does not consume formal F03 authority.

**Native frame preflight result:** The two C1 quadratic spans were passed directly through the actual `CurvedBeam3ReferenceGeometry` admission. Shared position/frame errors were zero, the normalized tangent mismatch was `7.4e-16`, and both outer frames were horizontal. The focused source-level admission test passes in the deck-builder file. The solid must map each section with the native tangent-aligned frame, not just lift its nodes vertically: at the transition midpoint the bottom section shifts approximately `1.33 µm` longitudinally. This matters at the same order as the 2 µm clearance. No solved solid response, deformed-contact certificate, coupled solution or F03 acceptance follows from this frame check.

**Solid geometry preparation:** The existing C3D20R terminal-bond deck builder now has an explicit, default-off `c1_tangent` reference profile. It maps solid bar nodes through the tangent-aligned C1 section map, splits the x=.825 m transition midpoint, leaves the x≥.9 m shared face and tip load IDs intact, and retains the legacy generator output exactly (`SHA256 85c7fd286fbf0363227e3209f9982c2a8beb32508d692f05946c5761b2e60344`). The new generated deck is `SHA256 003c812ccb4e4c47e6e97df3a37d00b7f2b7827540803f4bc3a9f2c59acb8172`; the midpoint bottom section moves `−1.333333 µm` in x and about `+1.000018 µm` in z relative to the plate. The full deck-builder test file passes `71/71`; an independent Hex20 shape calculation checks positive reference Jacobians at 27 Gauss points in each of the 1,280 bar elements. These are construction and reference-element checks, not a solved deformed-contact or physical accuracy result. Next use this *same* geometry for a bounded external deformed-contact screen; only if admissible build the matching native curved model and compare work, root/support partitions and interface resultants. A contact failure routes to a declared contact reference, not to another old-geometry score.

Current bounded code: `scripts/b3_e4_f03_local_footprint_work.py` and `scripts/b3_e4_f03_solid_bond_pose_projection.py`; the latter's four focused tests pass. Saved full-bond inputs are `.qualification/b3-ge-e4-pl/f03-ccx-full-bond-full-field-dev-20260925-v1/solid-4-tip_{mx,fz}` with deck/FRD hashes verified against each `result.json`. The prior reverse-Fz full-u deck/FRD hashes remain `6adcacf961de9de398ce418421861137e1ea7709ab4ccc661dceaa0aceec8c16` / `eecf83fe6486d53b31ff903f42d069fcdc878af40acf49fab5d83a17e53c6d94`. All previous versioned evidence remains unchanged below.

**Line-mechanics decision, same candidate geometry:** For a zero-longitudinal-length strip, a surface point relative to the beam axis has arm `(0,y,-e)`. A position traction `t(y)` gives `F=∫t dy` and `M=∫(0,y,-e)×t dy`, hence `M_x=∫y t_z dy+e F_y`, `M_y=-e F_x`, `M_z=-∫y t_x dy`. Its local wrench span is at most five; independent `M_y` needs longitudinal force support or a declared physical couple. This is a work identity, not a numerical rank threshold. On the unchanged Q4 x4/y4, native B3-half8 supported grid, the six-local positional P1 rows have ranks `17/18` and `29/30` for two/four intervals; replacing only `M_y` by the tested director couple gives `18/18` and `30/30`. Row-normalized combined supported ranks are `22` and `38`, with the last nonzero singular values `0.387/0.131` followed by numerical zeros below `5e-16`: the director variant changes the row space, rather than merely recombining rows. Its already-preserved loaded torque and plate-partition drift therefore remains a substantive counterexample to selecting that variant. The rank comparison alone is not an inf-sup result or a new line candidate. Do not obtain an independent sixth local action by relabeling position tractions or by selecting a smaller weak residual. Source `6dc29b20` also checks total physical support force/moment for all bounded Q4/S3 torque/shear cases; maxima are below `1.8e-9 N` and `1.6e-9 N m` on the tested x4/y4, x8/y4 and x4/y8 grids.

**Independent G0B F08 bounded registration, before execution:** Determine whether the two native B3 families already expose a reusable 42-coordinate local residual, Jacobian and candidate-history seam without calling their global dense assemblers. Use (a) the existing two-element straight generalized square-section `build(4)` fixture and (b) the existing two-element curved physical axial/biaxial fibre `make_model(contrast=1.)` fixture with `ForceProgram` target `0.25`. Evaluate virgin and one deterministic supported small trial from the same virgin material predecessor; compare an independent sparse local gather with each existing dense owner at the same load parameter. Require local/global residual and tangent relative differences at most `1e-12`, identical candidate material histories, unchanged predecessor state, and finite local outputs. Cap each context at its existing 120 s deadline and 256 retained coordinates; no global dense matrix may be created by the sparse gather. A failed seam blocks F08 and is diagnosed, not hidden by a wrapper. This is a G0 feasibility check, not F03 acceptance or permission to enter G1.

**F08 bounded result:** Source `a6083523` adds the direct four-case comparison in `tests/test_b3_e4_g0_f08_local_operator_seam.py`; `python -m pytest tests/test_b3_e4_g0_f08_local_operator_seam.py -q` passed 4/4 in 2.82 s. Both two-element native families reproduce the dense owner residual/tangent within the registered `1e-12` relative limit at virgin and small trial states, with identical candidate histories and unchanged predecessors. The local gather uses only 42-coordinate blocks and COO-to-CSR scattering; the dense owner is invoked solely as the oracle. This establishes the extraction seam's bounded feasibility, not large-scale sparse performance, accepted plastic-state parity, independent mechanics acceptance or completion of F08/G0B. F03 and G1 status remain unchanged.

**F08 accepted-predecessor extension, registered before execution:** Use the same two-element curved physical axial/biaxial fibre model with the existing target sequence `(.25,.5,1.,.5,0.,-.5,0.)`, nodal force `(5,.4,-.005,0.)`, and `stop_after=3`. Require a completed three-step accepted prefix and at least one positive plastic-history measure; otherwise do not label this a yielded case. From its accepted physical state and accepted material histories, compare sparse 42-coordinate local scatter with the dense owner at the same target for (i) the accepted configuration and (ii) one deterministic supported small trial, always from that same accepted predecessor. Require residual/tangent relative differences `<=1e-12`, exact candidate-history identity and no mutation of the accepted predecessor or checkpoint. Keep the existing 120 s context deadline, <=256 coordinates and no dense global allocation inside the local gather. A failure remains evidence; no rerun with adjusted targets merely to obtain a pass. This extension does not qualify coupled plasticity, restart or G0B.

**F08 accepted-predecessor result:** Source `c5022326` passed the preregistered yielded-history test and the complete focused file (`5/5`, 8.43 s). The three-step accepted prefix has positive plastic history. Sparse local and dense-owner residual/tangent differences satisfy `<=1e-12` at the accepted state and one small trial from its accepted material predecessor; candidate histories are exactly identical, and the predecessor/checkpoint hashes remain unchanged. This closes that bounded extraction uncertainty, but does not establish the final F08 independent review, coupled material-state ownership, large sparse execution or G0B acceptance. The native connection F03 remains the primary unresolved foundation.

**F08 read-only review of the bounded seam:** An independent reviewer checked
the focused test and both native owners. The 42-coordinate gather calls local
element operators and scatters to CSR without invoking the owners' dense
assemblers; dense allocation is confined to the oracle and small comparison.
Both paths intentionally share local physics and correction functions, so this
is assembly-path parity, not an independent derivative or material-law oracle.
The yielded accepted-predecessor case meaningfully checks one paused plastic
prefix and immutable origins, mechanical state and checkpoint. The four virgin
cases check origin immutability but do not separately snapshot mechanical
state. This review leaves F08's complete acceptance and production owner/state
contract open; it does not advance G0B or G1.

**Next F08 extraction decision (27 September):** The passing 42-coordinate
local sparse gather still lives only inside its test. Move it behind one
private typed adapter that returns actual candidate histories, residual and
CSR tangent for both native section families without invoking their dense
global assemblers. Reuse the same accepted-predecessor and virgin fixtures;
compare all values and histories with the bounded dense owner, verify that
predecessors and checkpoints remain unchanged, and reject nonfinite local
outputs. Parity permits a later mixed owner to reuse the adapter; mismatch
or aliased predecessor histories requires fixing the extraction contract.
This is G0 feasibility, not precomputed production sparsity, scale, or G1
entry. Do not alter element equations or the accepted F08 evidence.

**F08 typed extraction result (27 September):** The formerly test-only seam
now has a private single-element 42-coordinate response and sparse gather
adapter for generalized and physical-fibre native B3. Both return actual
candidate histories from the same accepted predecessor. The local residual,
tangent and slot arrays are owned; repeated evaluations survive mutation of
a returned array. Four virgin/small-trial cases and a yielded accepted-prefix
case reproduce the earlier test seam exactly and the bounded dense owner to
`<=1e-12` relative. Candidate histories are distinct objects with identical
canonical values, while origins, accepted mechanical state and checkpoint
remain unchanged. The dense assembler was patched to fail during adapter
calls; the focused suite passed `6/6`. Existing historical F08 tests/evidence
were not rewritten. The adapter still consumes bounded old-owner contexts and
uses COO scattering rather than a compiled sparse pattern. It does not close
independent derivative review, mixed atomic state, practical scale, F08/G0B,
or the G1 bar.

**F08 adapter review and repair (27 September):** Independent read-only
review found two fail-closed differences from the bound owners: the fibre
adapter skipped frozen-model/program guards, and the generalized adapter
skipped retained-state admission. The adapter now invokes the native guard,
reconstructs/validates the mechanical state, validates every accepted
history, and guards again after evaluation. Sparse gather performs this
admission once per trial, rather than once per local element. New negative
tests show that a changed fibre reference node and a displaced fixed
generalized DOF are rejected by both the native owner and local/sparse
adapters. The focused file passed `8/8` after a test-only correction to
the expected fibre error wording. A read-only independent repair review
found no remaining actionable admission or formula issue; it did not run
tests or assess independent derivatives or scale. F08 and G0B remain open;
G1 remains barred.

**Next bounded F08 derivative decision:** Existing sparse/dense parity
shares the same element formulas and cannot detect a shared tangent error.
On the same two-element virgin generalized and physical-fibre fixtures,
compare the extracted assembled tangent action with central differences
of residuals obtained through each native physical state update. Use a
fixed supported direction mixing nodal translation/rotation and retained
coordinates, three step sizes, and the registered elastic `1e-6` relative
threshold over a plateau. Agreement supports this local trial contract;
failure identifies a derivative issue to diagnose before integration. This
does not determine the beam–shell connection or close F08/G0B.

**F08 derivative result and review:** The new two-family test first makes
a supported nonzero trial from each virgin accepted predecessor, mixing
nodal translation/rotation and native retained coordinates through its
actual `advance` operation. It then compares central residual differences
at `1e-5`, `3e-6`, and `1e-6` with the sparse tangent action. At least two
steps in each family meet `1e-6` relative error; the focused file passed
`10/10` after this nonzero-trial strengthening. Independent read-only
review confirmed this checks a derivative rather than dense-owner parity.
The unloaded generalized fixture still does not test line-work/couple-load
derivatives; the physical-fibre fixture does not test a yielded plastic
tangent. These are remaining coverage limits, not observed formula failures.
This is not a full derivative envelope or independent material-law oracle.

**Next bounded F08 loaded-path discriminator:** Repeat that same physical
state-update derivative check with one nonzero generalized line force and
cell couple on the existing model. This distinguishes an untested load
correction or spatial chart term from the already passing unloaded operator;
pass supports the extracted loaded trial contract, while failure isolates
the load/tangent path for repair. Keep the fixture small and do not infer
general loaded-model qualification from one direction.

**F08 loaded-path result:** The one-element line-force/cell-couple load
on the same two-element generalized model passes the physical-update
directional plateau with the extracted sparse tangent. The focused file
passes `11/11` including the previous unloaded and ownership checks.
This resolves the narrow unloaded-path coverage concern for that fixture;
yielded plastic tangents, other directions and larger compiled layouts
remain outside this result. No additional loaded sweep is implied.

**Next bounded F08 yielded-branch discriminator:** Reuse the existing
three-step accepted physical-fibre prefix already proved to contain
positive plastic history. From that exact predecessor, perturb the same
supported nodal/retained direction through the actual state update at
three central-difference sizes, and compare with the adapter's consistent
tangent under the registered smooth-plastic `1e-5` limit. A plateau pass
supports this one active-branch derivative; failure requires checking
active-set transition before attributing an operator defect. No new load
history or adjusted target is authorized by this diagnostic.

**F08 yielded-branch result and retained failure:** A central derivative
at the exact three-step accepted state failed the smooth-plastic test at
`0.00248489946` relative error, unchanged over `1e-5`, `3e-6`, and
`1e-6`; this failed diagnostic is retained. One-sided inspection shows a
material branch switch: the accepted-state candidate has no further
plastic increment, positive perturbations activate 14 fibre rows, and
negative perturbations activate none. The tangents evaluated on the
positive and negative sides match their respective one-sided residual
slopes at `8.28e-9` and `8.22e-9` relative for `1e-6`. Applying the
registered smooth-plastic limit to a nearby positive trial from the same
accepted predecessor, with unchanged active-row count on both sides,
passes the three-step plateau check; the focused file passes `11/11`.
This locates a yield-branch switch within the tested interval and finds no
smooth-active-branch tangent defect for this direction. It does not prove
that the accepted point is exactly on the yield surface. Independent
read-only mechanics review identified a remaining acceptance question:
the tangent *at the accepted state* differs from the negative one-sided
slope by `3.078e-4` relative and from the positive slope by `5.235e-3`;
the side-specific checks use tangents evaluated at the perturbed states.
No semismooth tangent policy is accepted from these data. The failed
central check and accepted-state discrepancy remain visible for a later
targeted constitutive/chart review. Other active branches and F08/G0B
remain open.

**Next accepted-tangent discriminator:** The side-specific tangents match
their slopes, but the accepted-state tangent differs from both one-sided
slopes. Inspect the native cell response's recorded `derivative_kind` at
the accepted state and at the two perturbations using the same predecessor,
without changing its load history. A semismooth boundary classification
keeps central differencing outside the smooth-plastic criterion and leaves
the local generalized-derivative policy to review; a claimed smooth branch
with this persistent mismatch is a tangent defect to correct. Do not use
the passing nearby smooth test to erase the accepted-state observation.

**Accepted-tangent result and action:** Direct native material inspection
reports `CLASSICAL_SMOOTH_BRANCH` in both elements at the accepted state
and at both signs of the `1e-6` perturbation. The actual fibre branches
show why that label cannot validate a finite-difference plateau here:
element 1 has `17` plastic-positive rows at the accepted state, `26` at
the positive perturbation and `11` at the negative; element 2 stays at
`14`. The central tangent discrepancy remains about `0.002485` as the
perturbation shrinks from `1e-7` to `1e-10`, while the same differing
branch counts persist. These finite binary64 perturbations cross multiple
nearby yield boundaries; they do not establish the derivative at the
mathematical accepted point or prove a constitutive tangent defect.
The `derivative_kind` records exact local branch equality, not a distance
to the nearest branch switch. Stop shrinking this central difference.
Retain the failed check and the separate passing one-sided and nearby
smooth-active results. The accepted-state semismooth policy needs targeted
constitutive/chart review before F08 acceptance; no material tolerance or
element equation is changed by this development diagnosis.
Independent read-only review confirmed this interpretation and the
finite-step limit: `CLASSICAL_SMOOTH_BRANCH` is assigned from exact
branch labels at each point and does not imply a common smooth
neighborhood. The observed count changes prove crossings for the tested
steps, not exact yield equality at the accepted state. No product tangent
defect or F08 acceptance is inferred.

**Next bounded F09 physical-range decision:** Existing scaled sparse
successes used fixed bending/torsion inertias while area vanished, which
is a numerical stress case rather than a coherent section family. On the
already reviewed two-member elbow, use solid circular elastic sections
with area `pi r²`, both second moments `pi r⁴/4`, and polar torsion
`pi r⁴/2` at three declared radii spanning slender to stocky members.
Keep the same member lengths, frames, supports and a fixed nonzero mixed
tip force/moment. Compare scaled sparse work and free force/moment
residuals with the independent cut-wrench Castigliano integral and an
exact solve of the rounded assembled matrix. Agreement makes this
physical section range a candidate for later admission; failure isolates
section representation or global conditioning. This bounded local graph
check does not admit B2 attachments or close F09/G0B.

**F09 coherent-section result:** The bounded elbow check uses `E=210 GPa`,
`nu=0.3`, a declared `0.9` shear factor, radii `0.005/0.02/0.08 m`,
the corresponding solid-circle `A/Iy/Iz/J`, unchanged 2 m + 1.5 m
members, and tip `(0.1,-0.08,0.06 N; 0.01,-0.012,0.008 Nm)`.
Diagonal-scaled sparse solutions agree with exact solves of the rounded
12-free-row matrix to relative displacement norms
`1.16e-11/5.32e-13/4.52e-14`; total work agrees with the independent
cut-wrench Castigliano integral to
`1.88e-11/1.18e-13/6.68e-15`. Separate free force/moment residual checks
meet `1e-9` of their applied scales. The focused file passed `5/5`.
This extends the earlier nonphysical area-only stress case with one
coherent scalar-section range on the same elbow graph, but does not
establish generalized SPD admission, all attachments, resource scale, or
a production sparse solver policy. F09/G0B remain open.

**Next bounded F09 coherent-coupling discriminator:** The same elbow has
passed a physically coherent scalar circular-section range, while the
existing generalized-section graph and reversal cases use moderate
dimensionless coefficients. Keep the three circular radii, graph, supports
and mixed force/moment loading, but introduce a non-diagonal SPD sectional
correlation with the correct force/moment dimensions. Compare the
diagonal-scaled sparse solve with the exact rounded assembled system and
the independent cut-wrench compliance work, including explicit member
reversal and section-axis transformation. Agreement supports the coupled
section representation over this bounded physical range; failure
identifies a scaling, frame or assembly defect before admission. Do not
infer attachment, full conditioning-envelope or F09/G0B acceptance.

**F09 coherent generalized-range result:** The two-member elbow now uses
non-diagonal SPD sectional stiffness formed from each physical circular
section's `EA`, `GA`, `GJ` and `EI` scales, with explicit dimensionally
consistent cross-couplings. Across radii `0.005/0.02/0.08 m`, two fixed
mixed force/moment signs, and a reversed second member with its section
axes transformed, the graph matrices and independent cut-wrench work agree
within the focused `1e-9` relative checks. Positive-diagonal-scaled sparse
solutions agree with rational exact solves of the rounded 12-free-row
matrices; force and moment residuals pass separate applied-scale checks.
The focused F09 file passes `11/11`. This extends the coherent scalar range
to coupled generalized sections on one elbow graph. It does not establish
attachment accuracy, a production sparse conditioning policy, large graph
scale or F09/G0B admission. The physical connection choice and G1 bar are
unchanged.

**Next bounded F09 equivalent-unit discriminator:** The coherent elbow
supports one SI scalar-section range; the generalized operator's coupled
force/moment representation still needs an explicit unit-covariance check.
On one non-diagonal SPD generalized section, convert metres/Nm to
millimetres/Nmm analytically, scaling length, translational coordinates,
section resultants and curvature strains with their physical dimensions.
Compare local energy, force, tangent, selected section response and offset
station trace against the original through the exact congruence. Agreement
retains the operator representation for later graph/admission checks;
failure identifies a dimension or trace-map defect. This private numerical
conversion does not change the public SI-only definition policy, set a
conditioning envelope, or close F09/G0B.

**F09 generalized unit-covariance result:** A non-diagonal SPD generalized
section was converted numerically from metres/Nm to millimetres/Nmm using
the declared force/moment and translation/rotation congruences. The private
B2 operator's energy, nodal force, tangent, section resultants/strains and
eccentric station trace agree with the original under those transforms.
The focused local operator suite passes `15/15`. This is a dimension and
trace-map check on one moderate section, not public unit-system admission,
an extreme conditioning range, sparse-graph accuracy or F09/G0B acceptance.
The primary C1 law still requires the pending physical-joint choice; neither
this result nor the earlier mode/solid diagnostics selects it.

**F09 generalized weak-shear basis candidate:** The private generalized B2
operator now inverts its exact integrated flexibility in a fixed midpoint
shear/moment basic-wrench basis, then transforms the inverse back to the
original physical coordinates. It keeps the section SPD screen and the
provisional `1e-12` normalized-pivot screen; the scalar branch is unchanged.
The formerly rejected `2^-40` coupled-shear example still fails that screen
in the original basis, but passes it in the fixed separated basis. Its
recovered inverse equals an independent exact Gauss-Jordan inverse; fixed
mixed-wrench forces, energy, three interior poses, section resultants and
strains, and two pure weak-direction tangent actions match independent
cut-wrench/integrated-strain references at the developmental `1e-8` checks.
An independent read-only review found no algebraic defect in the congruence
or force-coordinate recovery. The five physical-B2 test files and F13 file
pass 56/56 in separate focused invocations. A broad one-command invocation
was stopped without a result and is not counted. This does not establish a
full conditioning envelope, attached or large-graph solve, production B2
admission, F09/G0B acceptance, or a revised scientific tolerance.

**Next F09 graph discriminator:** The separated-basis inverse passes a weak
local mixed wrench, but global assembly and binary64 factorization may still
lose that mode. On the existing rooted two-member elbow, use the same
`2^-40` generalized section on both members and one fixed order-one mixed
tip wrench. Compare the bounded scaled sparse batch tip/work with an exact
solve of its rounded assembled matrix and the independent cut-wrench work;
check the batch's own residual and factorization status. Agreement permits
broader physical-range admission work, while failure identifies assembly,
rounding or factorization as the next repair target. Do not infer a scale
envelope, attached behavior, speed or F09/G0B acceptance from one graph.

**F09 weak-shear graph decision:** The same `2^-40` section was assembled on
both members of the rooted elbow under the registered fixed mixed tip wrench
`(0.7, -0.8, 0.5, 0.2, -0.3, 0.4)`. The rounded graph's exact rational solve
and independent cut-wrench work agree closely, but the initial scaled sparse
solution had a maximum row-scaled residual of `2.79219e-7`. One correction
through the retained factorization reduced the *backward* row-scaled residual
to `4.32304e-17`; its tip and work remained close to the exact rounded
solution. That did **not** make the physical equilibrium acceptable: an
independent exact-product evaluation of free-node force rows found a maximum
`1.06534e-4 N` imbalance against the `0.8 N` applied-force scale, about
`1.33e-4` normalized. This is a connected-solve conditioning/representation
limit, not evidence that the local force-flexibility law is wrong or that a
connection law has been qualified.

The private batch now retains its backward-error check and also checks the
reduced force/moment residual against provisional physical load scales pulled
through the affine map. A failed or cancellation-risk fast check invokes
accurate sparse products and at most two same-factorization corrections. The weak graph is
rejected before selected recovery or callbacks; ordinary batch and affine
cases remain accepted. The focused F13 suite passes `18/18`, and five related
B2 graph/attachment/definition/trace files pass `30/30`. Independent read-only
review found no correction-sign or publication-boundary defect and required
this separate physical-balance check; the review did not accept a production
scale or large-graph cost. The initial failure remains part of the evidence.

**Next F09 decision:** Do not extend the section range merely from local
inverse accuracy or graph tip/work agreement. Distinguish whether a better
global variable basis or factorization preserves the weak graph's applied-
scale force and moment balance within the existing criteria without dense
production work; otherwise bound the admitted conditioning range explicitly.
Use a small fixed graph and compare exact rounded residuals before any scale
experiment. F09 and G0B remain open; G1 is barred.

**F09 state-representation discriminator:** On that same fixed graph, the
independent rational solve of the rounded assembled matrix was converted to
ordinary binary64 physical coordinates. Exact-product evaluation of those
stored coordinates still exceeds the `1e-9` applied-force balance check.
Thus improving factorization alone, while returning the nearest binary64
coordinates of this exact solution, does not admit this extreme section.
This does not prove that every neighboring binary64 vector fails; the
remaining bounded choice is to establish a defensible conditioning admission
range or a verified state representation that passes physical balance.
The focused F13 file remains `18/18`. A piped read-only diagnostic and a
six-case exploratory sweep were stopped without outputs after excessive
runtime; their owned child processes were stopped and the temporary sweep
script removed. Neither aborted run is evidence. The committed fixed-graph
test is the completed check; a later range study needs an explicit time bound.
No large-scale or production conditioning claim follows. F09/G0B remain open.

**Next bounded F09 admission bracket:** The `2^-40` generalized-shear
graph fails applied-scale balance even after exact rounded-matrix algebra is
stored in binary64, while coherent physical sections previously passed.
On the same rooted elbow and identical mixed wrench, check just one
`2^-20` coupled-shear section with an exact-product free-row balance oracle.
A pass establishes a bounded passing point below the extreme failure and
directs later admission to physical section families; a failure calls for
diagnosing the batch graph representation before defining a range. This is
not a new tolerance, a production cutoff or an unbounded refinement sweep.

**F09 admission-bracket result:** The `2^-20` coupled-shear section on that
same two-member graph and mixed wrench completes through one sparse
factorization. Independently evaluated exact products of its stored
binary64 solution satisfy separate `1e-9` applied-force and applied-moment
free-row balances. The F13 focused suite passes `19/19`; the `2^-40` case
continues to reject before publication. This brackets numerical behavior
for one deliberately nonphysical generalized section family; it does not
set an admitted cutoff. Further F09 work should use explicitly physical
section geometry, orientation and units, with attachment and graph checks
where technically possible. Do not refine this exponent sequence merely
to locate a floating-point threshold. F09/G0B remain open.

**Finite-footprint classification:** At one unchanged 70 mm Q4/S3 x4/y4 panel, eight-half-cell native B3, 100×100 mm terminal patch and identical supports, the existing six-row tip-pose distributing footprint and the provisional six-row distributed surface-position-moment footprint each have supported rank `6`. Their combined supported row rank is `12` on both Q4 and S3-V2D (row-normalized smallest union singular values `0.04855/0.04984`, well separated from the `1e-9` numerical rank cut). The provisional law is therefore a distinct constraint space, not a row-basis rewrite of the old tip-pose footprint. This exact finite-dimensional distinction does not rank accuracy, show continuum stability, or make either law production-selected; the scalar singular values are not mixed-unit inf-sup measures. Preserve the separate 35 mm physically matched work screens for connection assessment.

## Prior state — 25 September 2026, native connection decision

**Decision sought:** Carry the six-resultant distributed surface-position work law as the provisional *finite-footprint* native connection, while resolving whether any exact nonmatching line extension can transfer torque and shear without rank loss or locking. No footprint or multiplier is production-selected. G0B is open, G1 barred, and formal F03 authority unconsumed.

**Established facts:** On the 35 mm panel with a 100×100 mm terminal bond, the finite six-resultant surface-position law has zero reference gap, objective work, no drilling column, a full six-row local rank and checked finite first/second variations. Four→eight local cells change its native torque/shear work coordinates by `+0.265%/+0.069%`. The executed quadratic-solid consistent-tip-load torque work is `49.400 µrad` versus native `50.393 µrad`; its bar-axis root torque is `55.770 N m` versus native `54.365 N m`. The *opposite-sign, opening* solid shear work is `69.324 µm` versus native `69.087 µm` in magnitude, with plate reaction magnitudes `72.151` versus `69.296 N`. These are promising directional comparisons, not matched-model accuracy scores: the solid torque has a 2 µm tapered clearance, the native axis is straight, and the unbonded faces have no contact law. A hash-checked read-only projection of that loaded solid field onto the **actual finite six-position-moment patch** gives mean y gap `−8.29 nm`, Mx moment gap `−1.093 µrad`, and Mz moment gap `+0.380 µrad`. The older *tip-lumped pose* comparator instead gives `−0.198 µm`, `+5.081 µrad`, and `−1.421 µrad` on its distinct definition. The new pointwise reduced-section gap RMS is `52.58 nm`: endpoint rigid-section fit contributes `52.95 nm` RMS, while face interpolation contributes `1.68 nm` and beam-pose interpolation is negligible. The actual shared solid bond face remains continuous; these are reduction gaps, not contact openings. The physical top-surface transverse-band Q4/S3 mixed reference rows also match independently differentiated finite-chart work with eccentricity and nonzero force/moment multipliers. Classical axial, historical Q6/finite-pad, and native six-channel evidence remain distinct.

**Remaining uncertainty:** At one zero-length surface station, position tractions on a fixed-width strip span at most five section actions: about the shell-surface center, `M_y=0`; about the eccentric beam axis, `M_y` is tied to `F_x`. Independent local My therefore needs longitudinal support or physical director work. Repeating the six-resultant surface footprint as P0 loses seven of 48 rows at one shell/beam ratio; with beam resolution increased to restore rank, 2→4→8 rows still change torque `48.19→41.88→23.82 µrad` and shear `43.38→42.14→34.55 µm`. The six-local continuous-P1 traction has a row dependence; its longitudinal My force moment is not a stable solution by itself. A new flat-reference hybrid replacing that My moment with an independent shell-director/beam-frame couple has full `18/18` and `30/30` supported ranks at two/four intervals and preserves objective work and shell shear, but fixed-mesh torque falls `27.845→24.137 µrad` and plate support Mx magnitude `13.583→5.302 N m` (about 13% and 61%). Shear tip motion changes only `42.598→41.725 µm`. Stop this hybrid before a finer screen. The top-band mixed P0/dual line also has unresolved paired loaded drift; its finite-band H^-1/L2 quotient changes the weakest mode from legacy Fy to about 98% Fx but selects no multiplier. The single-footprint five-pair compliance check has rank 6/6 and positive physical shell action, not a continuum line envelope. The solid has no continuous deformed-contact certificate. Native nonlinear state/lifecycle and registered reciprocal mesh ratios remain unproved. None of these diagnostics proves formulation failure.

**Next discriminating experiment and resulting action:** Keep the finite-footprint surface-position law as a bounded candidate, but stop the tested exact-line families; replacing only My repairs algebraic rank without fixing torque transfer. The saved solid now supports the *finite patch's* kinematic question, although its reduced section residual is fit-dominated and cannot qualify contact or B3 accuracy. Before another line solve, derive a mechanically distinct work law stating which finite-width shell and B3 section modes are constrained and which plate shear/beam warping modes remain free. Compare its compliance-weighted supported row space with the existing laws first; an invertible row recombination is not a new mechanics candidate. Its first loaded discriminator uses one unchanged Q4/S3/native-B3 geometry and the same torque/shear and plate/root quantities. Only a physically credible, distinct law advances to the registered norm-correct mesh-ratio study. No new classical axial or finer-row screen is justified now. This does not change F03 criteria or consume formal authority.

Current sources and records: `f03-native-distributed-surface-half-plate-dev-20260925-v1`, `f03-ccx-half-plate-quadratic-face-{terminal,detached}-dev-20260925-v1`, `f03-ccx-half-plate-quadratic-face-reverse-fz-dev-20260925-v1`, `f03-distributed-surface-compliance-dev-20260925-v2`, and the preserved surface-line and transverse-band records. The new read-only physical projection is `f03-ccx-surface-moment-projection-derived-20260925-v1`, source `dd77d6e2`, result SHA-256 `6997757b844cc2c6f6c4f5d8fab5c97344ab6cb2131c747a002b5f553d83af47`; the saved deck and FRD hashes were checked and zero-reference/objectivity control passed. The finite-band norm comparison is `f03-finite-band-mixed-norm-dev-20260925-v1`, source `5970eba7`, result SHA-256 `c64166582a27c98dffad716378bf5dd888935470e59691d0ca95a243c8594120`; its 8/8 fixed-model evaluations completed. The stopped hybrid is source `44b2133b`, raw record `f03-hybrid-director-my-dev-20260925-v1`, result SHA-256 `d4224672f22607cda8ea0ed260f22547d9f63bba48c8e04060032c4799523fd8`. The new Q4/S3 finite-chart mixed-row direct checks and three focused hybrid/legacy controls passed; two older pytest sessions remain running and are not claimed as passed. Preserve all failed V1 records and protected external inputs.

**Finite-band mechanics contract (derivation, not qualification):** For a physical strip of fixed width `w=.1 m`, the width mean `B_w u(x)=w^-1 ∫[-w/2,w/2] u(x,y) dy` maps an H1 shell position/director field into H1 along the beam, with `||B_w u||_H1 ≤ w^-1/2 ||u||_H1` on the strip. Its mean material tangents are `B_w ∂x u=∂x B_w u` and `B_w ∂y u=[u(x,w/2)-u(x,-w/2)]/w`, both controlled in L2. At the flat reference, top-band translation and director spin have H1 control; polar yaw contains these tangents and is generally only L2. Thus uniform H^-1/2 is a finite-grid comparator, not the established inf-sup norm for this width-mean pose. The Neumann H^-1/L2 finite-band quotient was evaluated with force/moment scaling and a signed-retained decomposition check; it remains a finite-model diagnostic, not continuum inf-sup proof. Exact dual pairing, boundary conditions and a registered mesh-ratio envelope still require review. No registered F03 norm or acceptance criterion changes without explicit reviewed amendment.

## Prior state — 25 September 2026, matched native torque/shear screen

**Decision sought:** A defensible native six-channel beam–shell connection and, only then, a stable exact line space. G0B remains open, G1 barred, and formal F03 authority unconsumed.

**Established facts:** Finite-strip polar yaw has balanced physical boundary work and preserves symmetric shear; the weakest finite interface modes do not explain loaded torque drift. With matched plate thickness, beam offset/section and supports, the exact six-channel native line changes Q4/S3 torque twist about `27→24 µrad` from n4→n8, while shear stays near `41–43 µm`. Mx and Fy/Mz rows interact. A separate six-*local*-resultant physical traction law passes wrench, rigid-work and no-drilling checks. Its P1 rows are dependent (`17/18`, `29/30`, `53/54`); P0 is full rank but Q4 torque changes `45.769→39.790→21.515 µrad` across n2/4/8 and plate support torque changes sign. Paired shell/beam/interface refinement still changes torque `39.790→26.018 µrad`; this is not solely a fixed-primal row effect or a convergence claim. The full-bond solid gives `35.076 µrad` torque and `41.530 µm` shear but represents a different bond and tip-load idealization. All native balance/work checks close. The first matched-screen hash error is preserved in v1; its corrected byte-identical v2 and later records have verified hashes.

**Remaining uncertainty:** Neither tested exact six-pose line nor six-local-traction P1/P0 space is qualified over the required loaded and mesh-ratio envelope. The two-level paired result does not prove the physical traction law itself fails; trace kinematics, enforcement space, shell/beam discretization and the difference from a full-width volume bond remain entangled. The solid record has a combined support wrench, not a reliable plate/root partition. Rank and finite absolute-energy quotients are not continuum stability proofs. Classical axial, historical Q6/finite-pad, and native six-channel evidence remain distinct.

**Next discriminating experiment and resulting action:** Stop this line-row refinement series. Use the existing bounded finite-footprint, finite-strip and full-field solid records to derive one alternative *physical* beam-to-shell connection contract: specify the actual surface region, independent beam section actions, shell trace and permissible shear/warping before coding another line space. Its first executable discriminator is a fixed-mesh loaded work/torque/shear comparison against both current candidates, with explicit plate/root partition and local interface modes. If that contract cannot transfer torque while preserving shell shear, revise the pose or idealization within G0; only a credible loaded law advances to norm-scaled mesh-ratio and multiplier-space selection. Do not use smaller residuals, rank, or a spectral quotient as acceptance.

Current source-bound records: `.qualification/b3-ge-e4-pl/f03-polar-yaw-dual-dev-20260925-v{1,2,3,4}`, `.qualification/b3-ge-e4-pl/f03-matched-native-full-bond-dev-20260925-v{1,2,3,4}`, and `.qualification/b3-ge-e4-pl/f03-six-local-traction-decision-dev-20260925-v{1,2}`. The original matched-solid and full-field evidence remains listed below. Five direct physical-traction controls and two offset-root torque controls passed; existing long-running pytest processes have not reported completion and are not claimed as passed.

## Prior state and retained development evidence — 25 September 2026

**Decision sought:** Select a physically defensible native six-channel beam–shell connection, then a stable exact line space. No production line or footprint law is selected. G0B remains open, G1 barred, and formal F03 authority unconsumed.

**Established facts:** Under matched full-bond geometry and supports, factor-4 quadratic solid gives `35.076 µrad` for +100 N m torque and `41.530 µm` for +1000 N transverse shear; its stronger rigid-section control gives `31.178 µrad` and transfers `10.601 N m` of torque to the plate support. The original six-local-row native line changes `48.190→23.816 µrad` over 2→8 intervals at B3-half16; its eight-interval plate torque is only `4.526 N m`. Continuous four-profile physical traction changes `45.855→42.094 µrad`, but plate torque falls `12.706→1.570 N m` and shear tip displacement changes `43.068→35.922 µm`. It spans six *global* resultants but only four independent local section wrenches. Prior six-row ablation shows that Fy+Mz with Mx reproduces its torque response. Adding a physical `−y Fx` local-Mz dipole stiffens torque to `24.137→22.775 µrad` over n4→n8, but plate torque remains small (`5.302→3.065 N m`) and shear is unchanged. An output-only replay of the same factor-4 full-bond solid cases gives byte-identical decks after removing the output card and byte-identical historical DAT results. On two equal 0.125×0.1 m interior patches, solid-inferred shell versus nearly rigid beam-section yaw gaps under torque persist at `1.337/1.496 µrad`; shear rotational gaps are `0.324/0.067 µrad`. Thus yaw transfer is physically consequential and its mismatch is not solely terminal, but neither solid projection nor small weak gaps selects a native connection. Earlier normed transverse modes weaken with line refinement and are dominated by alternating Fz/beam work; rank or quotient alone selects no multiplier. Classical axial, historical Q6/finite-pad, and native six-channel questions remain separate.

**Remaining uncertainty:** The rigid control constrains shared plate/bar nodes as well as the solid stiffener; it is not a pure B3 warping experiment. The solid volume bond and native B3/E4 weak surface tie remain different idealizations. The new pose projections use one factor-4 solid field and a 0.125 m patch, so they are not convergence or native-pose accuracy claims. Existing six-local-row spaces lack satisfactory loaded refinement and norm-scaled stability over registered ratios; four- and five-profile traction lack independent local My. The x16/y16 diagnostic hit the existing 1,900-row cap before solving; that failure is preserved.

**Next discriminating experiment and resulting action:** Stop adding surface-traction rows or refining the solid reference. Reuse the existing finite-strip pose/work and six-row ablation evidence. Resolve how a six-channel exact weak connection should transfer *physical finite-width yaw* without imposing an unsupported equality of the shell's area-polar rotation and a rigid beam-section fit at every station. State the proposed work functional and its admissible local modes before another loaded solve. If that contract cannot preserve shell shear and objective wrench work, revise the pose; if it does but loaded torque partition or line modes remain poor, revise the beam trace/interface space. Only a credible loaded candidate proceeds to norm-scaled stability and registered mesh ratios. G0B stays open and G1 barred.

Source-bound development records: `.qualification/b3-ge-e4-pl/f03-ccx-full-bond-quadratic-face-dev-20260925-v1`, `f03-full-bond-rigid-tip-projection-derived-20260925-v1`, `f03-ccx-rigid-sections-full-bond-dev-20260925-v{1,2}`, `f03-rigid-section-connection-comparison-derived-20260925-v1`, `f03-surface-resultant-line-dev-20260925-v1`, `f03-line-trace-compatible-ablation-dev-20260925-v1`, `f03-surface-line-shell-refinement-dev-20260925-v{1,2,3}`, `f03-trace-compatible-yz-dev-20260925-v1`, `f03-continuous-surface-traction-dev-20260925-v1`, `f03-continuous-yaw-traction-dev-20260925-v1`, `f03-ccx-full-bond-full-field-dev-20260925-v1`, and `f03-full-bond-interior-pose-derived-20260925-v{1,2,3}`. The first pose-derived attempt is preserved as a failed read of a mesh-only FRD; versions 2/3 use the output-only replay. The v1 shell-refinement record is the preserved row-cap failure. Automatic approval review rejected a further x-only shell-axial screen as repetitive of the stopped diagnostic; it was not run or substituted through another route.

**Matched full-field pose discriminator (development only):** Source `8095aba9` adds the guarded displacement-output option to the existing C3D20R runner. Both factor-4 torque/shear jobs completed in about 18 seconds each within the existing one-thread/120-second limit. Removing the output card recovers each historical input deck exactly, and each DAT file is byte-identical to the saved solved case. All 555 FRD probe displacements agree with the DAT values to `5e-12/5e-11 m` maximum for torque/shear (about `1.2e-6` relative to maximum probe motion), consistent with output precision. The bounded 0.125×0.1 m patch has zero reference gap and passes common rigid motion. At section x=.8125/.9375, torque solid-inferred shell/beam-section yaw gaps are `−1.337/−1.496 µrad`; the beam-section rigid-fit RMS is `0.011/0.016 µm`. Corresponding total rotation-gap norms are `1.365/2.167 µrad`, and rigid-corner mismatch is `0.167/0.210 µm`. Under Fz, rotation-gap norms are `0.324/0.067 µrad` and corner mismatch `0.080/0.069 µm`. This is a persistent torque-yaw idealization difference in one physical solid field, not evidence that E4/B3 must fail or that an exact line multiplier is stable. The 0.125 m projection patch differs from the historical 0.1 m native strip, so these are not direct native accuracy scores.

## Recent evidence and decisions

**Six-resultant moving-pad row-space stop:** On one physical 100×100 mm patch, let `g` be shell top-surface minus native B3 bottom-surface position, `r=(x−x_c,y,0)`, `A` the area, and `J=A⁻¹∫(|r|²I−rrᵀ)dA`. The six coordinates `ḡ=A⁻¹∫g dA` and `θ=J⁻¹A⁻¹∫r×g dA` perform exact resultant work `F·ḡ+M·θ=∫[(F+(J⁻¹M)×r)/A]·g dA`. This is precisely the existing finite six-position-moment footprint. Translating the *pose coordinates* to the beam axis by `d=(0,0,−0.05) m` gives `[ḡ_axis,θ]=[[I,[d]×],[0,I]][ḡ,θ]`; dual wrenches transform by `T⁻ᵀ`, preserving work. A fixed Q4/S3 x4/y4, native-B3-half8 supported row-space calculation found rank `6/6` before and after. The exact algebraic identity proves that re-origining creates no new row space. A separate `C K⁻¹ Cᵀ` calculation happened to be positive on these six rows, but the retained B3 `K` is indefinite; its quotient is **not** a physical-compliance or inf-sup certificate and is not used for selection. No new KKT solve or package was made. Repeating this re-origin as a P0 moving pad cannot create an independent warping coordinate; existing high-frequency line-mode concerns remain.

**Matched-reference audit and saved-field decomposition:** The saved factor-4 C3D20R full-bond cases have a 35 mm plate, 100 mm square bar, axis `z=.0675 m`, shared nodes over `x=[0,1] m`, left plate-edge and bar-root clamps, and exact +100 N m torque or +1000 N shear resultants about the tip. Original deck/FRD hashes verify. Read-only projections onto equal `125×100 mm` windows `x=.5–.625/.75–.875/.875–1 m` give torque `(Mx-like, Mz-like)` reduced gaps in µrad `(-.006,+.277)/(-.075,+.295)/(-.941,+.110)` and shear My-like gaps `−.076/−.083/+.163 µrad`. Torque reduced-gap RMS is `20.8/23.0/48.4 nm`; the complete beam-section rigid-fit RMS is `10.4–10.5/10.9–12.2/12.2–49.9 nm` at each window's stations, while the terminal face-interpolation RMS is only `5.5 nm`. These are within-solid reduction measures, not a gap in the shared 3D face. The terminal solid torque closest to native work has a 2 µm taper outside the x=.9–1 bond; its smallest sampled deformed gap is `6.36 nm`, so no continuous nonintersection follows. Zero-clearance terminal torque penetrates on one y-side under either torque sign. Saved reverse-Fz opens but uses a different geometry and load sign. The next matched pair must account for these identities; six weak rows determine their multiplier pullback, not a unique physical contact-traction field.

**Native reference-frame prerequisite:** A disposable attempt to give the existing native fixture exactly the saved solid's piecewise linear 2 µm axis lift stopped before assembly with `GeBeam3CurvedFrameError: nodal frame axis must match the oriented reference tangent` in `_ge_beam3_centered_reference.py`. Assigning identity material frames to sloped elements is invalid. Giving each straight element its own tangent-aligned frame would conflict at the taper's sharp slope changes because `_ge_beam3_retained_generalized_state.py` requires identical shared-node frame authority. The unfinished fixture edit was restored; no product or diagnostic source was retained. A matched comparator therefore needs a separately derived admissible C1 reference/section geometry and a solid deck with that same geometry, or an explicitly qualified junction/contact idealization. The saved sharp taper cannot simply be declared native-matched.

**Seam-slope preflight using the saved field:** The original terminal model/mesh and the output-only full-displacement deck have identical node coordinates. Their source deck and FRD hashes are `a70142232fd432fe3d61197254771dfe8390361376680489f8e0bda24a23f942` and `a278eda344276cf5713b813eb0a519305512aad932550b1ee4a068107d72a6ff`. On all eight quadratic face pairs ending at x=`.9 m`, the reference clearance contributes `−13.333333 µm/m` to the x-directed normal-gap slope. Polynomial edge derivatives of the *deformation-induced* gap at face y-centres, in order from `−.04375` to `+.04375 m`, are `+1.604,+.147,−.235,−.129,+.129,+.235,−.147,−1.604 µm/m`. The total saved slopes are negative because the linear clearance dominates; face-centre gaps at x=`.88125 m` are `232–268 nm`. Removing the clearance slope while holding this solved displacement field fixed would make the gap negative immediately left of the seam on faces with positive deformation slope. A newly solved smooth geometry may change that field, so this is a direction test, not a no-contact impossibility proof. It rules out treating smooth taper as automatically admissible; contact or a different explicitly matched geometry must be checked before accuracy scoring.

**Rigid-section discriminator (development only):** Source `fbd31123` adds a bounded CalculiX control using documented `*RIGID BODY` constraints on every non-root quadratic-solid stiffener section; the shared plate/bar nodes on each section participate, so this is intentionally stronger than a weak mortar and not an exact B3 equivalent. The original full-bond geometry, C3D20R elements, E/ν, left/root supports, and consistent +100 N m tip wrench are unchanged. Three new deck guards and the 65 existing solid checks passed (68/68). Pinned CalculiX 2.23 completed factors 2/4 in `f03-ccx-rigid-sections-full-bond-dev-20260925-v{1,2}` with no reported diagnostic. Rigid torque work is `31.414→31.178 µrad`, versus `34.782→35.076 µrad` for the unconstrained solid; factor-4 plate support torque is `10.601` versus `11.333 N m`. The hash-bound reparse under `f03-rigid-section-connection-comparison-derived-20260925-v1` records work, support wrenches and model limitations. A separate hash-bound fit to every loaded quadratic tip-face node shows that nonrigid tip-face motion carries `0.157%` of factor-4 torque work and `0.000625%` of factor-4 shear work; the old station subset omitted 144 loaded midside nodes and was not used for that claim. Rigid section restraint materially stiffens the solid, but the native six-row eight-interval response remains `7.361 µrad` stiffer and sends `6.075 N m` less net torque to the plate support than the rigid control. These differing idealizations are diagnostics, not external accuracy or line-space acceptance. [CalculiX 2.23 rigid-body contract](https://dhondt.de/ccx_2.23.pdf)

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

## Current decision — C1 native connection, 26 September 2026

**Decision sought:** whether a stationwise native six-channel reduced line
weld merits development, rather than promoting the classical axial
comparator or treating the historical Q6/finite-pad and six-moment
footprint as that weld. The new single-interval C1 hybrid uses mean
shell-top/beam-bottom position, transverse position moments for Mx/Mz,
and E4 director pitch for My. It is a declared reduced-section law, not
pointwise 3D bonding or a selected mortar space. Source `ddcfcc30`;
17/17 affected tests passed. On the fixed C1 two-cell grid its reference
gap is `5.15e-16`, spatial-left chart Jacobian error `2.95e-17`, first/mixed
work derivative errors `5.65e-10/5.56e-10 J`, common-rigid gap error
`3.19e-16`, and raw drilling columns vanish. A supported pitch witness
is invisible to the old surface-position moments but activates the new
My row; a common transverse-shear field remains admissible.

**Established physical context:** independent review retained the
executed F2/F4 *pre-opened incremental torque* solid reference without
a blocking geometry, load, support, work or reaction finding. Its
saved opposed faces stay open in the overlap region; pure zero-preload
torque penetrates. Side clearance, contact, three-level convergence and
native accuracy remain unproven. On exactly the corresponding C1
geometry, loads and supports, the new native hybrid's combined tip rx
is `49.163/49.607 µrad` versus direct-solid `49.040/49.317 µrad`, and
tip z is `−70.237/−70.690 µm` versus `−69.010/−69.320 µm` at F2/F4.
Its combined F·u is `0.075153/0.075651 J` versus solid
`0.073934/0.074262 J`. The native beam uses a generalized square
section and the external model a resolved square solid; these are
directional comparisons, not the frozen cross-solver pass. The old
six-moment footprint gives `50.024/50.428 µrad` under torque, but is a
distinct distributing law. The hybrid's supported, energy-normalized
six-row compliance minima are `0.15498/0.15938`; the weakest action is
mostly Fy/Mz, with physical shell and beam work both positive and only
small numerical-shell work. This is a finite-grid diagnostic, not an
inf-sup certificate or multiplier-space selection. Raw root:
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-fixed-dev-20260926-v1`
(manifest/results/compliance SHA256 prefixes `0c694837/2bb26e61/83d1d32f`).

**Remaining uncertainty and next discriminating experiment:** the present
six rows average the entire x=.9–1 strip, so they do not establish
stationwise work, interface stability or the required 1:1 through 1:8
mesh ratios. On the same C1 reference, first split the hybrid into the
two native/shell host intervals and check reference closure, spatial-left chart
derivatives, row independence, physical action and the shear/pitch
witness. If rows become dependent or induce nonphysical shear/drilling
work, revise the shell pose law before a loaded ratio study. If they
pass, compare fixed-grid loaded response and norm-scaled interface
modes across the registered ratios, then obtain independent mechanics
review before selecting a multiplier policy. No further classical axial
refinement follows from this slice. Formal F03 authority is unconsumed;
G0B remains open and G1 barred.

**Two-interval result and bounded follow-up:** At fixed C1 Q4 two-cell
grid, the two x-host intervals have 12/12 independent supported rows,
each with stress-free reference, objective spatial-left work and zero
reference drilling columns. Relative to the single-interval hybrid,
tip Mx rotation moves `49.163→46.883 µrad` (−4.64%) and opening Fz
tip-z moves `−70.237→−68.896 µm`; balance errors remain below
`3e-12`. The normalized weakest action is alternating interval Fz,
minimum `9.24e-5`; its work is shell-physical `7.8035e-5`, beam
`1.4368e-5`, numerical shell `1.3e-10`. Under pure Mx, the two
interval Fy multipliers are `+646.2/−713.1 N`; under pure Fz the Fz
multipliers are `−990.6/+1059.7 N`. These are large opposing local
actions, not a rank failure or proof of instability. Raw root:
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-segmented-dev-20260926-v1`,
source `0962a554`. The external solid comparison and all historical
failure records remain unchanged.

The next one-axis discriminator is Q4 patch cells 2→4 at the *same two
intervals*, B3 half-cells 12, C1 geometry, supports and loads. If the
one→two-interval response shift shrinks with shell resolution, inspect
shell trace interpolation/kinematics; if it persists, investigate the
reduced line law against physical bond tractions and director freedom.
Do not add line rows or select a multiplier space from this quotient.

**Chart review and one-axis outcome:** Independent mechanics review found
that the earlier finite derivative screen differentiated spatial-left E4
frame updates, whereas the actual E4 trial uses additive total rotation
coordinates. Its linear reference results remain valid; its nonlinear
E4-chart claim was withdrawn. A new diagnostic adapter now uses the same
`Exp(total_theta)` convention as the E4 corotational trial, including
first and mixed director/top-surface variations. The nonzero-rotation
finite-difference check exposed and fixed a mixed beam/shell position
variable-shadowing bug. Physical spin about each current director is
null. The independent read-only reviewer found no new blocking defect
in this adapter; it verifies connection kinematics, not a coupled E4
material tangent or G0B acceptance. Focused affected tests pass 20/20.

The Q4 two→four-cell check at unchanged B3/line resolution did **not**
remove the one→two-interval effect: torque tip rx shifts
`49.607→47.708 µrad` (−3.83%) and opening tip-z
`−70.690→−69.319 µm` (+1.94% in magnitude toward the solid).
The two-interval four-cell shell support Mx under torque is
`−40.896 Nm` and Fz/My under opening `71.498 N/−48.816 Nm`;
the resolved F4 solid values are about `−40.530 Nm` and
`72.152 N/−48.137 Nm`, but the native tip rotation is 3.26% below
the solid fitted-section rotation. The solid bonded-face slope is
`45.770 µrad` versus its fitted-section `49.317 µrad`, with
`0.341 µm` maximum section warping residual. Native rigid-section
rotation cannot be identified with both observables. Raw four-cell
root: `.qualification/b3-ge-e4-pl/f03-c1-hybrid-shell4-two-interval-dev-20260926-v1`,
source `d9dab27d`. No physical-accuracy or mortar-space verdict follows.

**Next fixed-grid discriminator:** transform two interval rows into
six common plus six alternating actions. On the unchanged two-cell C1
model, ablate alternating Fz for opening and the remaining active
alternating channels for torque. If one channel explains each response
shift, focus the physical transfer/reference check there; if shifts
require several channels, revisit the reduced line-law definition.
Keep actual applied work distinct from the solid fitted tip pose: the
solid end-face F·u includes warping and differs from a rigid-tip
F·u reconstruction by `2.03e-5/1.08e-5 J` at F2/F4.

The fixed-grid common/alternating ablation at source `48c5eb9c` passed
rank, balance and work checks. Alternating Fz alone moves opening tip-z
`−70.237→−69.965 µm`, only `0.272 µm` of the full `1.342 µm`
shift. The other five alternating rows give `−69.178 µm`; their
Fy/Mx/Mz subset does not change opening but accounts for the entire
torque change `49.163→46.883 µrad`. Thus opening also depends on
alternating Fx and/or director-pitch My. Raw root:
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-action-ablation-dev-20260926-v1`.
The last bounded ablation will separate Fx from My on this same grid.
If My controls the shift, check its director/shear assumption against
the 3D bonded face; if Fx controls it, check axial trace and eccentric
work. Either result requires physical interpretation before ratio or
multiplier selection. Do not continue row addition after this split.

**Current-state summary, 26 September 2026:** The decision remains whether
the native six-channel reduced line weld has a physically defensible
stationwise transfer law; no mortar space is selected. The last fixed-grid
ablation (`7d318912`, raw
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-action-ablation-dev-20260926-v2`)
shows alternating Fx alone moves opening tip-z `0.830 µm`, Fz alone
`0.272 µm`, My alone `0.035 µm`, and Fx+My together `1.059 µm` from
the single-interval result; all six alternating rows move it
`1.342 µm`. Torque's full `2.280 µrad` change is carried by the
Fy/Mx/Mz group. The changes are balanced and physically energized,
but the large cancelling interval actions and the solid's warping /
face-slope versus section-rotation split prevent an accuracy claim.
The executed external reference has an additive independent review
record in `B3_GE_E4_PL_C1_PREOPEN_COMBINED_DEV_20260926_V2.json`;
V1 and raw evidence remain unchanged.

Next use the *saved* C1 solid displacement fields and the native
solutions at the same terminal stations to compare bonded-face slope,
rigid-section fit, shell director and local work, with explicit geometry,
load and support mapping. If the mismatch is localized to solid
warping/rigid-section idealization while transferred shell wrenches
remain consistent, retain the two-interval law as an unqualified
candidate for the registered mesh-ratio/stability checks. If the
interface kinematics or work differ materially before that
idealization boundary, revise the reduced pose law first. Do not
resume classical axial refinement. Formal F03 authority is unconsumed,
G0B remains open, and G1 barred.

**Current-state summary, 26 September 2026 (supersedes the preceding next
action):** Decide whether the native six-channel, two-interval reduced line
weld has defensible physical transfer before choosing a multiplier space.
The saved direct C1 solid F2/F4 decks have independently checked geometry,
loads, supports and a pre-opened bond; pure zero-preload torque is still an
inadmissible comparator. At F4, the native two-interval Q4 four-cell result
has tip opening `−69.319 µm`, applied work `0.074090 J` and shell support
`(Fz,Mx,My)=(71.498 N,−40.896 Nm,−48.816 Nm)`, versus saved solid
`−69.320 µm`, `0.074262 J` and approximately
`(72.152 N,−40.530 Nm,−48.137 Nm)`. Its tip *nodal* beam rotation is
`47.708 µrad`, its one-sided retained *material port* rotation
`46.089 µrad`, and its E4 top-face secant slope `45.467 µrad`. The solid
stiffener fitted-section rotation is `49.317 µrad` and the bonded-face
slope `45.770 µrad`; those observables and the 3D plate director proxy
are distinct, so the apparent closeness is directional evidence only,
not bond accuracy. The saved F2 comparison has the same trend. Native
rank, force/moment/work balances and physical shell work pass their bounded
checks; material-port rotations are one-sided at interior stations, so
the earlier nodal-only station record must not be called a port result.
Raw exact-source station root:
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-station-kinematics-dev-20260926-v2`
(`dfd63c75`).

The fixed two-interval, 12-half-cell transverse-action screen now compares
Q4 two versus four patch cells. Its weakest diagonal-energy-normalized
mode remains alternating interval `Fz` (`9.24e-5→1.29e-4`); the shell's
physical share rises `7.80e-5→1.13e-4`, the beam share stays about
`1.5e-5`, and numerical-shell work is below `1.3e-10`. Thus coarse shell
resolution contributes but does not remove this weak finite-grid action.
This is neither a physical multiplier-norm inf-sup bound nor evidence of
locking or failure. The fixed bond hosts give only 1:1 and 1:2 local
interval:shell-cell ratios, not the registered ratio envelope. Raw root:
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-segmented-shell-resolution-dev-20260926-v1`
(`47ab9659`). The immediate transverse-order/line-resolution diagnosis
is complete; no axial escalation follows.

**Norm interpretation:** For the same two intervals, the integrated
N/Nm duals were converted to P0 densities using their 0.05 m lengths;
moments use a declared 1 m characteristic length. An independently
analytic, bracketed Neumann `H^-1/2` P0 density Gram on the 0.1 m bond
changes the weakest *full* signed-compliance action to alternating `Fx`
(`0.750→0.906` on Q4 two→four cells). Restricted to nonaxial channels,
the weakest action is alternating `Fy/Mz` (`1.499→1.786`), with positive
shell/beam contributions and a Gram bracket ratio below `1.00000003`.
About 99% of the saved native torque multiplier field projects onto this
nonaxial mode under the **declared 1 m moment scale**; opening `Fz` does
not. With the same mechanics but a 0.1 m moment scale, that torque
projection is `0.782/0.790` on the two/four-cell grids and the nonaxial
quotient `1.265/1.518`. The mode is still mainly alternating `Fy/Mz`,
but its projection is materially scale-dependent. The analytic Gram's
`1.00000003` bracket ratio bounds norm truncation only. The earlier
diagonal-energy `Fz` minimum was normalization-dependent. Neither norm
turns the indefinite retained tangent into a coercive primal, and these
two fixed meshes do not prove mesh-uniform inf-sup or select P0.

**One-axis beam/line decision:** Each original C1 B3 half-cell was bisected
while retaining the same physical geometry, 0.05 m P0 intervals, Q4
four-cell trace, loads and supports. The 24-half-cell construction passed
its native sparse/dense parity guard. Tip `Mx` rotation changes
`47.708→47.730 µrad`, opening
`Fz` displacement `−69.319→−69.408 µm`, and combined work
`0.074090→0.074181 J` (saved solid F4 `0.074262 J`). The normed
nonaxial `Fy/Mz` minimum changes `1.786→1.866`, still positive and
torque-relevant; both domains carry work. Rank is 12/12 and maximum
loaded mechanics error `4.37e-12`. This bounded refinement does not
suggest beam underresolution is the dominant cause of the earlier
one→two-interval response shift. The one-sided tip retained port moves
`46.089→46.773 µrad` despite stable nodal rotation, so its apparent
closeness to the solid tip bonded-face slope is a resolution artifact.
In contrast, the quadrature-weighted port interval means change only
`44.3490→44.3365` and `46.0892→46.1042 µrad`; native E4 top-face
means change `44.0609→44.0500` and `45.5369→45.5510 µrad`. Saved F4
solid bonded-face means are `44.567/45.775 µrad`, using its quadratic
face interpolation. These are directional, distinct representations.
The independent read-only mechanics review found no blocking algebraic
or fixture defect and endorsed these limits; it did not qualify G0B.
Raw interval-mean and saved-solid roots are
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-interval-mean-dev-20260926-v1`
and `f03-c1-solid-face-interval-dev-20260926-v1` (`45f08f16`).
Raw 24-half-cell root:
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-beam24-resolution-dev-20260926-v1`
(`89747c9f`). Normed 12-half-cell root:
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-p0-density-norm-dev-20260926-v1`
(`916a9153`); focused affected tests pass `17/17` for the norm change
and `20/20` for the beam-fixture extension. These are development
diagnostics, not qualified reference or continuum stability evidence.

The moment-scale sensitivity root is
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-moment-scale-dev-20260926-v1`
(`6340f75b`).

**Remaining uncertainty and next action:** Keep the two-interval native
line weld as an *unqualified candidate*. Freeze a mechanically justified
moment/force scaling convention with independent review. Define P1 and dual-line test
spaces from the same physical six-channel work law, then compare loaded
transfer, pointwise gaps and the declared normed/signed modes over the
registered 1:1–1:8 and reciprocal ratios, including Q4/S3 transitions.
Also close the solid reference's side-clearance and three-level physical
convergence limitations before accuracy scoring. A ratio-dependent weak
mode or transfer drift sends the design back to the beam/line trace or
pose law; compatible stable responses permit a reviewed least-dimension
space decision. Do not select P0 from small gaps, a positive quotient or
the current near-match to solid work. No axial escalation follows.
Formal F03 authority is unconsumed; G0B remains open and G1 barred.

**Next bounded operator discriminator:** On the unchanged C1 Q4 four-cell,
B3 12-half-cell reference, build P0, continuous P1 and dual-P1 weighted
rows from the *same pointwise six-channel hybrid work integrand*. Normalize
each row by its exact basis integral and preserve the physical dual map.
First check P0 parity with the existing two-interval rows, stress-free
reference, actual-chart first/mixed work, row independence and supported
row-space distinction. Coincident spaces or failed work checks require
revising the basis construction before a loaded solve. Passing those
checks permits one fixed-grid loaded transfer comparison; it does not
select a space or authorize a mesh-ratio claim.

Two pytest invocations for weighted actual-chart derivatives were stopped
after 900 s with no test output. Later timed stages showed a weighted
mixed evaluation takes about `0.06 s`, and the exact 25-node P1/dual
endpoint derivative function passes directly in `1.85 s`; the existing
P0 actual-chart function passes directly in `1.51 s`. Pytest
`--collect-only` also stalled, including with plugin autoload disabled,
so the aborted runs indicate a local collection/runner anomaly rather
than a failed mechanics derivative. The direct check is valid bounded
development evidence, but the standard pytest route remains unresolved.

**Fixed-grid weighted-line finding:** On C1 Q4 four-cell/B3 12-half-cell,
P0 weighted rows reproduce the existing two-interval rows exactly;
P1/dual basis integrals are `(.025,.05,.025) m`, reference gaps are below
`1e-15`, each supported space has full row rank, and P1/dual combined
supported rank is `24` rather than one coincident span. Direct test
functions verify actual-E4-chart first/mixed work for endpoint P1/dual
representatives. On the same loaded KKT, P0/P1/dual tip `Mx` rotations
are `47.708/48.032/48.621 µrad`, tip opening `Fz` displacements
`−69.319/−69.155/−69.251 µm`, and combined applied works
`0.074090/0.073958/0.074113 J`; all reported balance errors are below
`5.1e-12`. The P1/dual differences are real fixed-grid behavior, not a
space-selection verdict. The sampled pointwise position gaps and
force/moment partitions must be interpreted together with normed modes
and the registered mesh ratios. The exact-source evidence root and
independent review are pending; G0B remains open.

## Weighted C1 operator and norm development result

**Current decision and bounded discriminator (26 September):** Retain a
native six-channel line candidate only if its interface modes and loaded
transfer remain interpretable under a basis-specific dual norm and changing
beam:shell resolution. The fixed-grid P0/P1/dual work experiment at source
`cd03575c` passed reference, rank, actual-chart work, loaded balance and P0
parity; raw evidence is
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-weighted-spaces-fixed-dev-20260926-v1`.
P1 and dual-P1 are distinct signed row spaces; the sampled physical
position gap is not a weak six-channel or stability certificate. An
independent mechanics review found no blocking weighted-row algebra defect
and required a full **basis-specific** dual Gram for P1/dual. The 35 mm C1
reference guard was added and directly tested after that review. The next
single-axis diagnostic compares P0/P1/dual on the same two- and four-cell
shell grids, with the same B3 reference and declared 1 m and 0.1 m moment
scales. A collapsing or representation-sensitive torque-relevant nonaxial
mode sends the line trace/pose or norm definition back for revision; stable,
balanced modes permit the separately registered mesh-ratio and physical
solid-reference work. Neither outcome by itself selects a multiplier space.
The saved solid F4 has side-clearance and three-level convergence limits;
these must be checked before accuracy scoring. G0B remains open, G1 barred.

**Discriminator result:** Source `500f3b1f` and raw root
`.qualification/b3-ge-e4-pl/f03-c1-hybrid-weighted-density-norm-dev-20260926-v1`
contain all six exact-source P0/P1/dual × 1/0.1 m cases. The focused
basis-specific regression passed directly (`130.05 s`); standard pytest
collection remains anomalous. At the declared 1 m scale, the Q4 two→four
cell nonaxial signed-compliance minima are P0 `1.499→1.786`, P1
`0.577→0.629`, and dual-P1 `0.585→0.638`. At 0.1 m they are P0
`1.265→1.518`, P1 `0.558→0.615`, and dual-P1 `0.565→0.625`.
The reported weakest full and nonaxial modes have positive shell and beam
work; each space has full supported row rank and a basis-specific Gram
bracket ratio below `1.000000034`. The weakest
nonaxial action remains an alternating `Fy/Mz` family, but its component
weights change materially with moment scale. P1/dual carry additional
rows, so their smaller quotients are neither failure nor superiority.
These are support-conditioned, indefinite-tangent finite-grid actions,
not inf-sup bounds. The independent read-only norm review found no
blocking normalization or Gram-orientation defect and confirmed that
rankings remain convention-sensitive; it did not qualify G0B. Saved mode
vectors are force-equivalent density coefficients in N/m for all channels;
multiply their rotational entries by the declared characteristic length
to read physical moment density in Nm/m.

**Next discriminating action:** Existing C1 B3 fixtures give two or four
bond half-cells; local Q4 grids give two, four or eight bond cells.
The resulting native half-cell:shell-cell ratios are only `1:1`, `1:2`,
`1:4`, `2:1`; the eight-cell grids need `1986/2202` dense KKT rows for
B3 12/24 plus P1, beyond the retained `1900` cap. Thus the present
fixture cannot establish the registered `1:8` and reciprocal envelope.
Build a bounded sparse ratio diagnostic with explicit reference cuts and
resource checks before claiming mesh-ratio stability. In parallel audit
the saved F2/F4 solid side surfaces and obtain a third physical level;
the saved models do match the C1 2 µm tapered axis, 35 mm plate, left/root
supports and +100 Nm/−1000 N resultant, but use a resolved square solid
and distributed tip-face load rather than the native generalized section
and tip wrench. This is a directional comparison only. No further classical
axial refinement or multiplier selection follows. Formal F03 authority is
unconsumed; G0B open and G1 barred.

**B2 F13 ownership decision (27 September):** The private affine batch freezes
case IDs but reads later numerical load arrays only when their chunk starts.
A callback may therefore mutate a submitted future load. The bounded
discriminator is to mutate a later array after the first completed case and
check whether the batch silently solves the changed load. If so, retain bounded
RHS chunks but fingerprint finite value snapshots at submission and reject a
changed future array before its chunk is solved. If no mutation can affect a
later numerical load, leave this path unchanged. This is a private ownership
check, not F13 qualification or a measured performance claim.

**Outcome:** The discriminator failed as expected before the change: the
callback altered a future load and the batch returned a completed result.
The private batch now validates and fingerprints each finite load at
submission, retaining only digests; each bounded chunk copies and checks its
loads before solving. A changed future input raises a typed value error,
while mutation of the outer case list still cannot change the submitted
inventory. The active-operation lock is released after this error and the
batch remains reusable. The focused F09–F13 set passed 59 tests. Input
mutation concurrent with snapshot creation is outside this synchronous
callback check; eventual public definitions must own their arrays. Batch
timing and F13 acceptance remain unmeasured/open; G0B remains open and G1
barred.

**F03 growing-interface decision (27 September):** The earlier x4/x8/x16
axial-only shell sequence held two multiplier cells fixed, so it established
a bounded fixed-space response rather than the required growing-space
behavior. On the existing 35 mm C1 Q4 x16/y4, B3-12 fixture, test one
aligned sixteen-interval exact line space with the same geometry, loads,
supports and 1900-row dense-component cap. Rank loss, failed work/balance or
material transfer drift relative to x8/m8 sends the trace or interface
resolution policy back for revision. Otherwise proceed to the reviewed
basis-specific norm and reciprocal ratios; neither outcome selects a space
or closes G0B. This is a development diagnostic, not formal F03 execution.

**First outcome and next discriminator:** The x16/m16 sparse C1 run completed
in 66.01 s at `.qualification/b3-ge-e4-pl/f03-c1-growing-x16-m16-dev-20260927-v1`.
P0/P1/dual supported ranks are 96/102/102 and all reported balance/work
errors are below `8.9e-11`. Relative to existing x8/m8, separate torque
work changes by `-0.644/-1.074/-1.110%`; opening work changes by
`-0.077/-0.064/-0.062%`. This coupled refinement cannot allocate the
torque change to shell or multiplier resolution. Run the same x16 shell and
B3-12 with m8 to isolate row enrichment. If m8→m16 changes torque materially,
review interface resolution and physical transfer before norm extension;
if it does not, assess shell-resolution convergence and the reviewed norm.
Neither result establishes physical fidelity or multiplier-space selection.

**Fixed-shell result and action:** The x16/m8 control completed in 67.34 s at
`.qualification/b3-ge-e4-pl/f03-c1-fixed-x16-m8-dev-20260927-v1`.
At unchanged x16/y4 shell, B3-12, loads and supports, m8→m16 changes
separate torque work by `-2.536/-1.269/-1.190%` for P0/P1/dual and
opening work by `-0.238/-0.117/-0.092%`. Torque tip rotations move
`46.447→45.269`, `47.106→46.508`, and `47.494→46.928 µrad`;
shell-interface Mx changes `40.778→40.471`, `41.045→40.888`, and
`41.179→41.022 Nm`. The sampled position gaps also change, but cannot
choose an enforcement space. All m8/m16 row sets retain their expected
rank (`48/54/54` and `96/102/102`) and the largest reported mechanics
error is `8.9e-11`. Conversely x8/m8→x16/m8 changes P0 torque work by
`+1.942%`, P1 by `+0.198%`, and dual by `+0.082%`; coupled shell/row
refinement had concealed the opposing P0 effects. These finite-grid results
show a material row-resolution dependence without proving locking or a
formulation defect. Review whether the added longitudinal modes enforce the
declared physical work and how transfer approaches a stable limit before
another refinement or multiplier selection; retain the native mixed-system
and physical-reference checks. Raw SHA256: x16/m16
`5C7BADB7AB7645D473DC02D258A5724D7116162D72D0EEC9AAA5B7B74AEE0B00`,
x16/m8 `D59F793BF13D26D70CEA91D265750F20F8F79D7B00EBE5D77747DE2CAEE70940`.
Each result embeds source hashes; the `source_git` is the pre-edit
`ed3d4f14`, so the hashes, not that commit alone, bind the changed allowlists.
Both runs used one BLAS/MKL/OMP thread and completed under the 120 s cap.
Formal F03 authority remains unconsumed; G0B open and G1 barred.

**Independent reading and next bounded check:** A read-only mechanics review
confirmed the comparisons and noted that complete supported row rank alone
does not show whether m16 rows are represented by shell deformation. A
historical *different local-center trace* P0 m16 audit had whole/beam-only
rank 96 but shell-only rank 69; it is a caution, not a rank result for the
current hybrid. Check the current x16/m16 P0 shell-only and beam-only ranks
with the declared row scaling before interpreting its transfer. A deficiency
sends interface resolution or trace design back for review; full rank still
requires normed stability and physical transfer checks. A separate six-build
quadrature comparison produced no output within 120 s and was stopped; it
supplies no quadrature result and is not a reason to extend that sweep.
An inline stdin-piped rank probe likewise yielded no fixture-ready output
within 120 s and was stopped. No rank claim follows. Use the existing
bounded standalone C1 runner with a shell/beam row inventory instead of
another piped one-off probe; this changes the diagnostic output, not the
mechanical law.

**Current hybrid rank outcome:** The bounded standalone x16/m16 rerun
completed in 65.42 s at
`.qualification/b3-ge-e4-pl/f03-c1-growing-x16-m16-rank-dev-20260927-v1`;
SHA256 is `83A6119E3A1481F8793A0C32E0EECC5C2D5E1A4378133ABA656061676DF4947B`.
The new inventory scales columns with the existing mixed-coordinate scales,
normalizes each row, and applies a declared `1e-10` relative singular-value
cut. Whole/shell-only ranks are P0 `96/96`, P1 `102/102`, dual-P1
`102/102`; beam-only rank is 15 for each. Thus this particular current
hybrid grid does not reproduce the historical *different-law* P0 shell-rank
deficit. It only shows algebraic shell representability; the row singular
ratios are not physical inf-sup constants or a space ranking. The separate
torque/opening work values are exactly unchanged from the previous x16/m16
run. The row-resolution transfer effect therefore remains to be judged by
physical work and normed growing-space behavior, including integration
accuracy. Formal F03 authority remains unconsumed; G0B open and G1 barred.

Independent read-only mechanics review confirmed that the support-reduced
column ordering and common row normalization make the shell/beam split valid
for this narrow algebraic claim. It found no blocking rank-code defect and
explicitly did not accept inf-sup, energy-weighted transfer, uniformity or
physical fidelity.

**Next bounded integration discriminator (27 September):** Before treating
the x16/m8→m16 torque shift as an enforcement effect, rerun the unchanged
x16/m16 C1 geometry, supports, loads and P0/P1/dual spaces with five-point
instead of three-point longitudinal line quadrature. Use the existing
standalone sparse runner, one thread and 120 s cap; retain a new raw result.
If the work/transfer difference explains a material part of the observed
row-resolution shift, revise or qualify the integration rule before
interpreting the multiplier study. If it is far smaller and mechanical
guards remain satisfied, retain the row-resolution observation and move to
physical work and normed stability. This is an integration diagnostic, not
a relaxed criterion or new mesh-refinement milestone.

**Integration outcome:** The five-point x16/m16 run completed in 68.39 s
at `.qualification/b3-ge-e4-pl/f03-c1-x16-m16-quadrature5-dev-20260927-v1`;
raw SHA256 is
`D40F80D4DABBBC6DC5679C20C2F0E1A2DEB68DC9FD544075F07235BED018DC37`.
At identical source geometry, loads, supports, beam and multiplier spaces,
three→five-point longitudinal quadrature changes P0/P1/dual separate-load
applied work by at most `3.01e-9%` in magnitude and the torque-case shell
Mx by at most `1.99e-9 Nm`. Whole/shell-only row ranks remain
`96/96`, `102/102`, `102/102`; all reported mechanics errors are below
`8.8e-11`. Near-zero torque rotations under the opening-only load are not
compared by relative percent. Integration order therefore cannot explain
the percent-level m8→m16 torque-work changes on this bounded case. This
does not qualify quadrature for every geometry or line law. Stop this
quadrature check; return to the physical rotational connection and reviewed
growing-space norm/transfer assessment. G0B remains open, G1 barred, and
formal F03 authority unconsumed.

## Latest F03 sided-reference decision — 27 September 2026

**Current physical-reference discriminator (prospective):** The saved F5
combined-load solid field has an actual top-face positional bond, while the
native six-row hybrid adds a separate E4-director/beam-pitch condition.
The saved six-gap projection reports nonzero hybrid pitch on that field, but
the station-pose projection was run only on separate influence cases. Run the
existing read-only station projection on the *same* pre-opened combined field,
with unchanged F5 geometry and no new external solve. Compare its
director/section pitch by station with the saved weak hybrid pitch and the
section-fit residual. If the mismatch persists, the one-sided F5 bond cannot
validate the hybrid's added pitch channel; specify a physically matched
two-sided reference before any accuracy ranking. If it vanishes, review the
six-gap reduction/projection discrepancy before changing the law. Either
outcome leaves G0B open, G1 barred and formal F03 authority unconsumed.

**Outcome and connection decision:** The unchanged F5 pre-opened combined
solid field completed this read-only projection in `5.34 s`. On the six
whole-strip section stations x=`.90,.92,.94,.96,.98,1.00 m`, the fitted
bar-section versus solid-inferred plate-director pitch gaps are
`8.29,6.43,5.21,4.49,4.13,3.91 µrad`; local interior patches give
`8.45,4.86,3.16,2.68 µrad`. The section-fit RMS is `42–83 nm`.
Stress-free and common-rigid projection errors are below `1e-15` and
`6.1e-10`, respectively. This agrees qualitatively with the previously
saved combined-field six-gap P0 hybrid pitch rows
`−7.594/−2.699 µrad`; different pose and weak-row conventions prevent a
direct numeric equality claim. Raw projection:
`B3_GE_E4_PL_F03_C1_F5_COMBINED_STATION_PROJECTION_DEV_V1.json`
(identical local `.qualification/b3-ge-e4-pl/f03-c1-factor5-combined-station-projection-dev-20260927-v1/combined.json`),
SHA256 `D2487D3118CA697515DFDED0CA9D313067D15021556948456C408314650D835F`;
source/deck/FRD SHA256 `505E6331`/`A9D7BA21`/`A4C11D5B` (full
identities in the raw file). This is a saved-field reduction, not a new
external solve or an E4 material-state measurement.

**Resulting action:** Treat the C1 hybrid as a distinct two-sided
director-couple connection. The actual F5 solid is bonded on its top
face only and permits the observed through-thickness pitch difference;
therefore proximity of its tip motion cannot select the hybrid or prove
its sixth channel physically faithful. Before another loaded comparison,
define the intended top/bottom force-pair or equivalent connection work,
including beam-section port, shell director/shear, supports, eccentricity
and reaction recovery. Obtain a matching sided reference with validated
force/moment and virtual-work balance, then compare the hybrid and any
five-field/top-face alternative against their *own* declared physical
connection. Existing F5 same-action and positional evidence remains
valid at its stated level. This decision does not select P0/P1/dual or
relax the registered stability and mesh-ratio requirements. G0B remains
open, G1 barred, and formal F03 authority unconsumed.

**Next bounded sided-reference feasibility (prospective):** On the *same*
saved F5 solid mesh, support and combined pre-opened load, add exactly one
linear averaged pitch equation over the existing bonded x=`.9–1.0 m`
strip. Its beam side is the area-averaged bar top-minus-bottom x-motion
divided by the 100 mm section depth; its plate side is the area-averaged
plate top-minus-bottom x-motion divided by the 35 mm thickness. Keep the
existing shared top-face nodes and all other deck cards. Before solving,
check the discretized equation's reference zero, six rigid motions,
top-fixed director witness, and equal/opposite physical moment work.
Then run only this one external combined case under the existing one-thread,
120 s and 2 GiB development limits. A complete balanced solve measures
how much this *explicitly two-sided linearized joint* changes the existing
one-sided response; a solver or balance failure requires correcting the
external construction. Neither outcome alone qualifies the nonlinear
native hybrid, surface contact, mesh convergence or multiplier policy.

**Resource-limited first outcome and bounded adjustment:** The preflight
passed 543-term integration, rigid-motion errors below `3.2e-15`, a unit
top-fixed pitch witness, and balanced opposite unit plate/bar moments.
The pinned F5 CalculiX run stopped at `33.77 s` when solver RSS reached
`2,181,611,520 bytes`, above the retained 2 GiB cap. No displacement,
reaction or connection response was produced. Preserve
`.qualification/b3-ge-e4-pl/f03-c1-factor5-sided-pitch-dev-20260927-v1/result.json`
(SHA256 `EFDD89F2D66201772CC27EA46DC4D8B7712FB98C7D678A259CF075A1CE2F2211`)
and its logs. This is a resource failure of a wide eliminated equation,
not evidence that the physical pitch law failed. Do not raise the cap.
The generalized runner reproduces the failed F5 generated deck byte-for-byte
(SHA256 `4F38B20D284A90BD3749E45C021240E45BAE5C8EE3A2418086CDB28D861C5222`);
the failure record is also tracked as
`B3_GE_E4_PL_F03_C1_F5_SIDED_PITCH_DEV_V1.json`.
Use the already saved physically identical F2 and F4 one-sided decks to
check the same one-equation construction at smaller matrix sizes, first F2
and only then F4 if F2 is balanced and below the cap. An F2/F4 solve
isolates feasibility and directional work on those meshes; it does not
replace F5 convergence or the eventual sparse native multiplier law. If
either exceeds the cap, stop and redesign the external enforcement rather
than enlarging the resource allowance.

**F2/F4 sided-reference outcome and decision:** The same physical C1
geometry, 35 mm plate, 100 mm bar, support, pre-opened combined load and
shared top-face bond, with exactly one added *linear area-averaged*
through-thickness pitch equation, completed on F2 and F4. The generated
equations have 111/363 terms. Rigid-motion and dual-wrench
preflight errors are below `3e-15`;
the top-fixed pitch witness is `−1`.
F2/F4 solver times are `0.788/19.276 s`, peak RSS
`106,176,512/1,322,917,888 bytes`, and assembled pitch gaps
`5.28e-11/−5.89e-12 rad`. Baseline one-sided versus two-sided
combined-load applied work is `0.0739340872→0.0736359877 J` on F2
(`−0.4032%`) and `0.0742620313→0.0739292397 J` on F4 (`−0.4481%`).
The fitted tip-section y-rotation falls by `1.279/1.392 µrad`.
DAT-recovered component support-wrench discrepancies are at most
`4.95e-4 N`/`3.68e-5 N m` (F2) and
`2.58e-5 N`/`1.86e-5 N m` (F4); these are exploratory printed-output
balances, not the registered final tolerance. Sampled unbonded-face
minimum normal gaps remain `8.52/3.07 nm` and therefore remain
directional, not a contact certificate. The F2/F4 raw result SHA256 values
are `26FA7BDA53E17C776D0A1F76F17ED3CC1DF5A99495CC7D08D6F8CA6A23D8C503`
and `AF630923FA5E30AD262D6CBF99393CE5484160DEB5AFE718C2CA14D1ED1445DF`
under `.qualification/b3-ge-e4-pl/f03-c1-factor{2,4}-sided-pitch-dev-20260927-v1/`.
Identical tracked records are
`B3_GE_E4_PL_F03_C1_F2_SIDED_PITCH_DEV_V1.json` and
`B3_GE_E4_PL_F03_C1_F4_SIDED_PITCH_DEV_V1.json`; generated-deck SHA256
values are `A990414F4280B53CD9868B431AA21C52A9991FD195FF36FE22978E31152049E8`
and `9532351E9F2E04E6473253B61E2FD87115098777E0685CCC22DE2437C750161A`.
The generated decks, stdout, DAT and FRD remain beside them. F5 remains
the preserved resource failure above. Stop this external mesh sequence.

**Interpretation and next action:** The sixth, two-sided pitch work has
a measurable stiffening effect on the *solid* joint; it is not an inert
basis change. It also moves the solid's work farther below the previously
saved native-hybrid work, so the native/solid difference cannot be assigned
to this one constraint alone. The area-averaged linear solid equation is
only a small-motion realization of a two-sided director connection.
Next specify the intended engineering joint as a top-surface positional
bond, a two-sided director-couple weld, or two explicit alternatives, using
the established torque/shear and connection-work requirements. For a
two-sided choice, validate sided interface force and work recovery and
native port matching; for a top-surface choice, revise the continuous
sixth channel or admit a five-field law. The current F2/F4 pair cannot
select P0/P1/dual, certify contact or close G0B. Do not retry F5 without
a sparser external enforcement design and a reason it changes the law
decision. G1 remains barred; formal F03 authority is unconsumed.

Independent read-only mechanics/code review found no blocking equation,
parser or provenance defect in this bounded external diagnostic. It
explicitly limited the initial F2/F4 claim: algebraic opposite moments
and global work change did not validate sided transfer because the
external equation multiplier and per-side forces/work had not yet been
recovered. The subsequent F2 output probe below narrows that limitation;
the native port and G0B remain unqualified.

**Paired-work dual inference and direct-output discriminator:** On the
saved F2/F4 one-sided displacement fields, the new equation gaps are
`4.283573/4.592387 µrad`. With unchanged physical loading and the
linear rank-one constrained equations, the decrease in applied-load work
implies dual moments `69.59/72.47 N m` by
`lambda=(W_one_sided−W_two_sided)/g_one_sided`. The F2/F4 difference is
about `4.1%`; this is an *energetic inference*, not direct CalculiX
multiplier output or per-side traction recovery. Test only whether the
pinned solver can print a force on the F2 equation's dependent node from
an otherwise identical deck. A printed force consistent with
`lambda * coefficient_dependent` would independently support the dual
interpretation and enable side-force reconstruction. A missing/zero or
ambiguous force leaves the paired-work inference at its present level;
do not tune the physical law or run another mesh merely for this output.

**F2 direct dual result and sided work:** An output-only F2 rerun printed
`−165.6942 N` at the equation's dependent x-DOF. That DOF carries no
applied load; its equation coefficient is `+2.38095238095238 m⁻¹`, so the
external solver's reaction sign gives `lambda=+69.591564 N m`. The
independent paired-work inference was `+69.591326 N m` (relative
difference `3.4e-6`, consistent with printed-force precision).
The full displacement field and applied-load work are identical at the
saved output precision to the F2 run without the extra output request.
The declared equation's gradient `Cᵀlambda` has zero net force and
`−69.591564/+69.591564 N m` plate/bar moments. The *physical interface
reaction* is `−Cᵀlambda`, hence `+69.591564/−69.591564 N m` on the
plate/bar. On the accepted final displacement field, its separately
partitioned plate/bar work is `+0.0043051578/−0.0043051615 J`, summing
to `−3.67e-9 J` at the printed precision; this is final-state
virtual-work pairing, not accumulated loading-path energy. The
source-bound record is
`B3_GE_E4_PL_F03_C1_F2_SIDED_PITCH_RF_DEV_V1.json`, identical to
`.qualification/b3-ge-e4-pl/f03-c1-factor2-sided-pitch-rf-probe-dev-20260927-v1/result.json`
(SHA256 `C0AFE23A31EFBBCC87F148E41CEAABBB1C9722A867B0CC86348A2B8A66BC23D9`).
F4 has only the paired-work inferred `+72.465921 N m` dual; the same
physical-reaction partition gives `+0.0044901795/−0.0044901791 J`
and a `+4.27e-10 J` sum. This validates the *linear external equation's*
side-force/work accounting at F2 and supports it directionally at F4.
It does not validate the native finite-rotation port or select a
production six-channel connection. Stop the output probe.

Independent read-only review found no blocking defect in the RF sign,
dependent-node admission, or recalculated F2/F4 work values. It cautioned
that the top-face shared nodes are split into *conceptual plate and bar
ports* for equation bookkeeping: this is not a measured contact-traction
field or native B3/E4 interface force. A follow-up review confirmed the
explicit `Cᵀlambda` versus physical `−Cᵀlambda` sign distinction against
both the CalculiX RF and native KKT convention. The F4 dual remains inferred.

**Saved native/external pitch-channel comparison and next action:** On the
existing C1 x=.9–1.0 m single-interval hybrid results, the native pitch
constraint is shell-director minus beam-section rotation, opposite to the
external linear equation's bar-section minus plate-director rotation.
The normalized native line weights sum to one. Superposing its separately
saved tip-Mx and tip-Fz linear cases gives physical *plate pitch-channel*
moments `+80.257910/+75.876099 N m` on F2/F4; the tip-Mx pitch
contribution is negligible at printed precision. The external two-sided
equation gives `+69.591564/+72.465921 N m`, with the F4 value still
inferred from paired work. These are directionally aligned, but the native
six-channel *total* plate interface My is only
`+49.431629/+49.686768 N m` under tip-Fz because other native rows also
transfer moment. The native shell director and section kinematics are not
the solid's through-thickness area-mean traces, and the native cases and
external combined-load case use distinct section idealizations. Thus the
comparison is neither a relative-error estimate nor a basis for choosing
P0/P1/dual or declaring the hybrid connection physically qualified.
Independent read-only review confirmed the signs, normalization and this
restriction against the saved results and source. No new solve was run.

The decision-changing next test is at the *continuous work-law* level:
hold the reference geometry, eccentricity and physical virtual fields
fixed, and compare the complete six-channel native port work (including
position/offset contributions) with the explicitly declared two-sided
director-couple joint. Exercise supported torque, transverse shear and
compensated pitch, and distinguish a law mismatch from a projected-row
resolution failure by checking continuous gap before weak rows. A mismatch
in continuous work calls for a targeted law correction; matching work
permits the registered growing-space stability and mesh-ratio assessment.
The one-sided top-face positional bond remains a separate comparator.
Formal F03 authority is unconsumed; G0B remains open and G1 barred.

**Native full-wrench reference check:** A new bounded reference-state test
uses a straight native B3 half-cell trace, the actual six-channel hybrid
Jacobian and nonzero force/moment duals in all six rows. Independent
resultant summation of `−Cᵀlambda` over shell nodes gives exactly the
expected opposite force and three moments about the physical top-face
connection center; moving the origin to the shell reference surface adds
the `17.5 mm` eccentric lever arm. A common rigid virtual field confirms
opposite beam/shell work when the native B3's retained half-cell frames
rotate with its nodes; omitting those rotations produces a false beam-side
moment. The focused test passed `1/1` after this extension.
This establishes the candidate's complete six-channel *reference rigid*
wrench/work interpretation. It does not validate loaded finite-rotation
work, torque/shear response, the two-sided engineering idealization or F03.
The next continuous-law discriminator must use supported torque/shear and
compensated-pitch fields with the actual native retained-coordinate port.

**Next saved-field discriminator (prospective):** The completed F4 sided
solid case has a vanishing *one-equation area-mean* pitch gap, but that
does not imply a locally closed director/section pitch trace. Reuse the
unchanged F4 deck and FRD through the existing station-pose projector,
with reference and common-rigid preflights, at the five F4 bond stations.
If the local pitch mismatch persists, treat the single external equation
as insufficient longitudinal resolution for this law and require a
segmented sided comparator before accuracy ranking. If it is locally
small relative to the one-sided F4 projection and fit residual, proceed
to native complete-port transfer/work and growing-space assessment.
Either outcome leaves the native E4/B3 versus solid idealization and
formal acceptance unresolved; no F5 retry, resource change or new
external solve follows from this read-only projection.

**F4 saved-field projection result and decision:** The existing projector
completed on the *same* one-sided and one-equation two-sided F4 solid
geometries, supports and combined load; no external solve was launched.
Reference gaps are `1.19e-15` and common-rigid errors `6.00e-10` in both
projections. Whole-strip fitted bar-section minus solid-inferred plate-
director pitch at x=`.900,.925,.950,.975,1.000 m` is
`8.132,5.975,4.717,4.123,3.840 µrad` for the one-sided bond and
`3.722,1.417,0.085,-0.597,-0.860 µrad` after the single sided equation.
Local three-station projections are `7.387,3.836,2.711` versus
`2.915,-0.715,-2.095 µrad`. The sided equation's own assembled mean is
`−5.89e-12 rad`, so it closes its declared *one* mean but leaves a
signed local variation. The fitted section RMS is about `39–65 nm` on
the sided run; these pose projections remain model reductions, not
measured E4 director states or contact tractions. Source-bound raw records
are `B3_GE_E4_PL_F03_C1_F4_ONE_SIDED_STATION_PROJECTION_DEV_V1.json`
and `B3_GE_E4_PL_F03_C1_F4_SIDED_STATION_PROJECTION_DEV_V1.json`, SHA256
`ADEB37A1204A4A793179DD29152A649CC97862990BA1187EC78960A39E3D6D3F`
and `EB5F44D7F0B6652B0722C341B3F34AECE90790A76724D5CFF1D5F5048520C273`.
The single area-mean external equation is therefore not a locally matched
six-channel sided reference; it cannot rank native P0/P1/dual or complete
physical transfer. A later *bounded F4 only* segmented sided comparator
may be justified if it tests whether local mismatch comes from equation
resolution rather than the two-sided law; it must preserve the same model,
load and resource limits, and assess each equation's dual/work and global
balance. Do not infer a production multiplier policy from this external
row-count experiment. G0B remains open; G1 barred; F03 authority unconsumed.

**Bounded F4 split-sided follow-up (prospective):** Use the same pinned F4
deck, solver, physical load, shared top-face nodes and 120 s/2 GiB/one-
thread limit. Replace the single added area-mean pitch equation with two
independent equations on x=`.90–.95` and `.95–1.00 m`; each must pass the
same rigid-motion, unit-couple, top-fixed-pitch and unique-dependent-node
preflights. Keep the original one-equation generated deck byte-identical
in its default path. If the two-row solve completes with balanced work
and support reactions, project its saved full field onto the same five
stations and compare the local pitch spread with the one-row case. A
substantial reduction isolates equation resolution as the main bounded
cause; a persistent spread points to solid-to-native pose reduction or
the continuous law and calls for reviewing those before more rows. A
resource/solver failure is retained and does not trigger a cap increase.
This experiment cannot select a native multiplier space or close F03.

**F4 split-sided outcome and terminal action for this slice:** The two
independent equations have 207 terms each, distinct interior dependent
nodes, unit opposite plate/bar My, zero common-rigid work to `1.8e-15`,
and top-fixed-pitch witnesses `−1`. The final source-matched run completed
under the unchanged cap in `23.46 s`, peak solver RSS `1,308,680,192`
bytes, with residuals `−1.62e-11/+2.46e-11 rad`. Its applied-load work is
`0.073773739207487 J`, compared with `0.0739292397 J` for the one-row
two-sided case and `0.0742620313 J` for the one-sided bond. Its printed
support-wrench discrepancies are at most `1.44e-4 N` and `4.90e-5 Nm`;
sampled unbonded-face normal gaps are positive with a `0.513 nm` minimum,
which remains a directional pre-opened check, not contact qualification.

The same five whole-strip projected pitches after two equations are
`3.231,1.006,0.072,-0.201,-0.355 µrad`, versus
`3.722,1.417,0.085,-0.597,-0.860 µrad` after one equation. The three
local projections change from `2.915,-0.715,-2.095 µrad` to
`0.660,-0.741,0.144 µrad`; the largest local magnitude falls by about
`75%`. The output-only reaction run has identical full FRD displacement
values at printed precision and identical applied work. Printed
dependent-node forces and coefficients give equation duals
`+71.10075/+3.76924 Nm`. Applying the *physical* `−Cᵀlambda` partition
gives plate/bar final-state virtual-work pairs
`+0.004430966/−0.004430965 J` and
`+0.000232291/−0.000232291 J`, with pair sums about `1.15e-9` and
`−9.25e-11 J`. These are equation-work partitions, not measured contact
tractions or integrated path energies.

The split resolves a substantial part of the local averaged-pitch
discrepancy, but the nonzero whole-strip endpoint gap and solid-to-E4/B3
pose-fit differences remain. Stop this external row-count sequence.
Next compare the declared continuous native work and physical supported
torque/shear transfer, then assess growing native spaces and ratios with
the reviewed mixed-system norms. Do not infer a production multiplier
space from two external equations. Formal F03 authority is unconsumed;
G0B open and G1 barred.

Final runner `scripts/b3_e4_f03_ccx_sided_pitch_reference.py` reproduces
the historical F2/F4 single-equation deck text exactly. The initial
split run and its output remain preserved, but the canonical split result
is the final-source run
`B3_GE_E4_PL_F03_C1_F4_TWO_INTERVAL_SIDED_DEV_V2.json`
(SHA256 `9EC49035630C123E84BEB9F1F12F18CD9C443B64A15CC5DB0E8B7FB615976918`),
with generated-deck SHA256
`5A678DAEC5FF004D0309359464487865F9ADF2FD556A335F540BC1FA55FBD6FF`.
The final-source output-only record is
`B3_GE_E4_PL_F03_C1_F4_TWO_INTERVAL_SIDED_RF_DEV_V1.json`
(SHA256 `266A52E614E0EA0319818CA656759AD9D0EAD687B8979B849FF0A8C43655C3A2`),
and its matched station projection is
`B3_GE_E4_PL_F03_C1_F4_TWO_INTERVAL_SIDED_STATION_PROJECTION_DEV_V2.json`.
Generated decks, solver logs, DAT and FRD are retained in the versioned
`.qualification/b3-ge-e4-pl/f03-c1-factor4-sided-pitch-two-intervals-*`
directories. This is Level-A development evidence, not independent G0B
review or external-reference acceptance.

Independent read-only mechanics/code review of the F4 split runner and
V2/RF records found no blocking equation, sign, work or provenance issue.
It confirmed both dependent nodes are distinct, unloaded and absent from
the other equation; it independently recalculated both side-work pairs.
The reviewer identified one P3 labeling defect: the runner's module text
and result limitation said "one additional" for the two-interval mode.
That wording is corrected prospectively. The numerical records remain
bound to the exact runner source at commit `7e2f3b7f`; no numerical input
or operator changed, and the solver was not rerun for a wording repair.

**Independent G0 design decision:** A separate read-only mechanics review
finds it defensible to *designate* the native six-channel candidate as an
explicitly two-sided director-couple joint for development, while keeping
the one-sided top-face positional bond as a distinct comparator. The
top-face law's exact force/pitch gauge cannot justify an independent sixth
channel. This is a declared engineering idealization, not physical
validation or an accepted default. The contrary evidence is retained:
residual F4 pose-fit/end effects, a linear solid sided equation rather
than a native E4/B3 state, and `1.2–2.5%` native torque-work movement under
x16 m8→m16 multiplier refinement despite negligible quadrature effect.
The minimum decision-changing check is complete *continuous loaded*
native gap and `−Cᵀlambda` side work, including offsets and retained B3
frames, on controlled supported torque, transverse-shear and compensated-
pitch fields. A mismatch revises the law or trace; a match permits the
registered normed growing-space and mesh-ratio assessment. No P0/P1/dual
selection follows from the current small residuals, rank or external
row-count result. F03/G0B remain open, G1 barred, formal F03 execution
authority unconsumed.

**Next native loaded-port discriminator (prospective):** The existing
supported KKT cases store weak rows, total interface work and pointwise
position-gap bounds, but omit the *continuous director pitch* and each
basis action's beam/shell work. Add read-only recovery to the same
bounded native operator: sample reference-linearized local pitch using
the actual B3 half-cell port and E4 director at line quadrature, and
partition `−Cᵀlambda` work by six-row basis with all retained B3
coordinates. First exercise one small Q4 C1 supported torque/opening
fixture with unchanged section, supports and load. If weak constraints
close but continuous pitch remains material, interface resolution must
be examined before law acceptance; if both close but physical torque
partition still differs from the declared two-sided reference, review
the shell/section idealization. A work imbalance or sign failure is a
mechanics defect to fix before more meshes. A passing small fixture
only authorizes the registered growing-space/ratio assessment; it does
not select a multiplier space or close F03. Keep existing resource caps.

**Small loaded native outcome:** On the unchanged Q4 C1 x4/y4,
B3-12, m2 supported reference-linear KKT, all three P0/P1/dual families
complete separate +100 Nm tip torque and −1000 N tip-z opening. The new
unprojected pitch sampler agrees with the actual C1 director/retained-port
derivative in a focused test; the three focused mechanics tests pass.
Torque-case continuous pitch is below `1e-17 rad`. In opening, the weak
mean pitch is below `3e-20 rad` while the pointwise maximum is
`1.852/0.998/1.327 µrad` for P0/P1/dual and RMS is
`0.774/0.460/0.545 µrad`. Maximum sampled position gaps are
`0.155/0.103/0.117 µm`. Each six-row basis's physical `−Cᵀlambda`
beam/shell work sums to within `2.8e-17 J` and its global wrench to
within `3.1e-12` in the saved units, including retained B3 coordinates;
basis shell work sums to the previously reported total. This is a
balanced *linear loaded* result, not finite-rotation physical fidelity.
The source-bound raw record is
`B3_GE_E4_PL_F03_NATIVE_LOADED_CONTINUOUS_X4_M2_DEV_V1.json`, SHA256
`CCB70EEE675F2D114F510C2C6072B37BDB0DAAB334292E2398408AFAC533FFF5`.

**Next fixed-primal discriminator:** Hold the exact x4/y4 Q4, B3-12,
section, supports, two loads and three bases; increase only multiplier
intervals from m2 to m4 in the existing bounded runner, with the same
continuous-gap and basis-work recovery. If pointwise pitch decreases
while basis work/wrench remains balanced, attribute part of the m2 gap
to discrete line resolution and move to reviewed growing-space norms and
the already registered ratios. If it does not decrease or work fails,
review trace representability or the physical law before more rows.
Either outcome leaves the finite loaded two-sided reference and G0B open;
do not automatically run m8 or a finer shell.

**Fixed-primal discriminator outcome:** The identical x4/y4 Q4,
B3-12, supported two-load fixture completed with m4. The row counts
grow from 12 to 24 for P0 and 18 to 30 for P1/dual. In the opening
case, the pointwise maximum continuous pitch falls from
`1.852/0.998/1.327` to `0.683/0.603/0.721 µrad` for P0/P1/dual;
maximum position gaps fall from `0.155/0.103/0.117` to
`0.109/0.0938/0.0988 µm`. The maximum per-basis side-work sum stays
below `1.4e-16 J` and side-wrench imbalance below `6.5e-13` in saved
units. Opening work changes by `−0.391/−0.127/−0.226%` and torque
work by `−3.231/−1.172/−1.288%` for P0/P1/dual. Therefore discrete
line resolution explains part of the pointwise pitch gap, but work
movement remains material, especially under torque. This neither
selects a multiplier space nor validates the physical two-sided law.
The m4 source-bound raw record is
`B3_GE_E4_PL_F03_NATIVE_LOADED_CONTINUOUS_X4_M4_DEV_V1.json`, SHA256
`2890DF180868A0FB076E9EBD34A47C55AC40FB0E47B0BF708B8A12C6C1E8A648`.
Stop this fixed-primal refinement sequence. The next decision is whether
the declared two-sided physical transfer survives a matched sided
reference and the registered growing-interface-space mixed-norm/mesh-ratio
assessment; no G0B conclusion follows from these linear loaded cases.
Independent read-only review found no blocking code or mechanics defect in
the sampler, basis split or paired interpretation. Here “continuous gap”
means unprojected *reference-linearized values sampled at fixed line
quadrature*, neither the supremum along the line nor a loaded finite-rotation
gap. Algebraic side balance establishes native bookkeeping, not external
physical fidelity. The reviewer recommends testing the declared two-sided
torque/shear/compensated-pitch work with actual retained ports alongside the
registered growing-space mixed-norm and reciprocal-ratio assessment; revise
the law/trace if transfer mismatches before selecting a space.

**Next finite-state work discriminator (prospective):** The reference-state
six-channel wrench check and the separate finite pitch-face-pair identity do
not yet check all six actions together at a nonzero E4/B3 configuration.
On the existing small C1 fixture, use nonzero supported shell/retained-beam
states and all six nonzero dual channels. Independently assemble the spatial
face-force work, eccentric lever arms, material-frame gap correction and
two-sided director couple, then compare with the native finite-chart first
variation and check opposite global wrenches. A discrepancy revises the
continuous law or coordinate pullback before more meshes; agreement supports
only this declared work representation and permits the matched physical
reference and growing-space studies. It does not validate a one-sided bond,
finite loaded equilibrium, or a multiplier policy. Preserve existing
virtual-work criteria and resource limits.

**Finite-state work outcome and review:** On the small supported C1 fixture,
one nonzero E4 total configuration and native B3 retained state, with all
six multiplier channels nonzero, pass the independently assembled spatial
face-force, eccentric-frame and director-couple virtual-work identity at
`1e-11` relative / `1e-12` absolute test tolerances. The global shell/beam
wrench sum passes `1e-10` absolute. The physical KKT action is explicitly
`−Cᵀλ`; the first test wording treated `Cᵀdual` as the reaction, and was
corrected after independent read-only review without changing the law.
The reviewer confirmed the derivative decomposition and actual retained
B3 port use, while noting that constructed global wrench cancellation is
an internal sign check, not an independent finite-state rigid-motion test.
The separate existing finite-chart screen supplies that common-rigid test;
it was rerun with the new work test and both passed. Four focused tests
pass with JIT disabled and one BLAS thread. This supports
the declared two-sided law's finite-state work representation only;
independent loaded physical fidelity, growing-space stability, the exact
line-space choice, F03 and G0B remain open, and G1 remains barred.

**Next growing-space mode discriminator (prospective):** The existing
drill-eliminated native retained KKT shows a line-dual-dominant P0 minimum
falling on x8/y4 m4→m8, while P1/dual minima remain beam-kinematic. That
single shell grid cannot tell whether the P0 trend persists through a
systematic physical/interface refinement or reflects its fixture. Reuse
the *same* exact-drilling Schur and declared physical/retained/dual norms
on x4 m2/m4 and x16 m8/m16, bracketing the saved x8 m4/m8 case. Preserve
the actual indefinite tangent, all six rows, 1900-row/120-second limits,
work/Schur/rank checks and physical-mode decomposition. A persistent
line-dominant decline calls for an interface-resolution/locking review
before P0 selection; a nonpersistent decline sends the x8 diagnosis back
to mesh/trace interpretation. Neither outcome alone proves uniform
inf-sup, physical fidelity or G0B acceptance. Do not add a fourth level
automatically.

**Three-level drill-quotient outcome (27 September):** The existing x8
m4/m8 result is bracketed by new source-bound x4 m2/m4 and x16 m8/m16
outputs, all using the same actual native indefinite tangent, exact
free-drilling elimination and declared physical/retained/dual diagnostic
norm. P0 minima are `0.0151967→0.0152498` on x4,
`0.0152313→0.0122832` on x8, and `0.0152550→0.00155703` on x16.
At x16 m16, the weakest vector's declared metric share is `99.844%`
line dual and `0.155%` physical shell; P1 and dual P1 minima remain
near `0.0152–0.0153` and about `98.4%` beam kinematic. All six x16
line sets retain full normalized rank, the Schur reconstruction error is
`9.24e-16`, and transpose-work discrepancies are below `1e-17 J`.
The x16 cases use 1,694–1,748 of the 1,900-row cap, one BLAS thread,
and finish in `74.81 s` inside the 120-second limit. The x4 case
finishes in `23.19 s`. Raw SHA256 identities: x4
`810C46470C02CB9FA3F3FFDD892EA07CE2869DE8D896F87063BC892550EF0EFF`,
x16 `7867179F8E2F913758CECCB7A6AE9F57EACC0136D1C247665C3231B6D37EDA69`;
their paths are `B3_GE_E4_PL_F03_C1_DRILL_QUOTIENT_X4_DEV_V1.json` and
`B3_GE_E4_PL_F03_C1_DRILL_QUOTIENT_X16_DEV_V1.json`. The x8 V2 source
predates parameterization; the only runner changes are bounded shell-level
selection and matching output labels. The result supports a growing P0
line-dominant weak-mode concern, not a continuum inf-sup constant or a
failure verdict. Interpret its physical mode, loaded transfer and norm
sensitivity before revising an interface policy; do not select P1/dual
solely because their diagnostic minima are larger. F03/G0B remain open.
Independent read-only review found no blocking arithmetic/source defect and
verified rank, Schur, transpose-work and weakest-SVD residuals across all
18 cases. It confirmed the x8 predecessor used the same mechanics/norm
sources despite subsequent additive diagnostics and a center refactor.
The next bounded check is the P0 m8/m16 weak dual's longitudinal/channel
shape and matching shell/retained-B3 response/work, compared with the
already observed loaded torque-transfer drift. This distinguishes a
supported physical line action from a high-frequency or norm-dependent
mode before any P0 resolution-policy change; P1/dual's beam-dominated
*minimum* does not rule out their own line-specific modes.

**Selected P0 weak-mode interpretation:** A single x16/m16 P0 extraction
reproduces `β=0.001557025359` in `65.57 s` and saves the R-normalized,
sign-arbitrary native KKT coordinates. The 16 integrated Fz actions
alternate in sign under a smooth central envelope; Fz contributes
`0.998232` of the unit mode metric, and its integrated resultant divided
by the sum of absolute cell actions is `1.90e-6`. The physical KKT
reaction `−Cᵀλ` does `0.00155340 J` shell work and `0.000001197 J`
native-beam-coordinate work on this weak vector. Thus the mode is a
high-frequency, nearly self-equilibrated transverse line action with a
small physical shell response under the declared metric. It is not a
tip-like physical resultant or a demonstrated locking failure.
The raw `B3_GE_E4_PL_F03_C1_P0_X16_M16_WEAK_MODE_DEV_V1.json` has SHA256
`359915B5C105A9ECA168A1F5AB256871A5DF5C2095CD0C67BF0C99287709D48A`.
Its `line_basis_intervals_m` metadata incorrectly repeats the parent
`[.9,1.0]` interval for all weighted patches; the numerical vector is
unchanged. Use the separate
`B3_GE_E4_PL_F03_C1_P0_X16_M16_WEAK_MODE_INTERVAL_CORRECTION_DEV_V1.json`
for the 16 actual P0 supports. An independent cheap reconstruction verified
all 16 quadrature supports, 96 rows and `.00625 m` basis integrals.

The saved x16/m16 loaded P0 material duals have the same basis masses.
Under the same declared line norm, the weak/loaded dual absolute cosine
is `1.73e-11` for tip Mx and `0.351` for tip Fz; loaded Fz carries
`3.96e-22` and `0.177` of total line metric respectively. These are
diagnostic vector alignments across impact-checked source revisions, not
physical participation factors. The weak Fz mode cannot be assigned as
the cause of the observed torque-work shift. Under tip Fz, x16 m8→m16
changes total work by `−0.238%` and physical shell work by about `−1.11%`;
the aligned x4/m2→x8/m4→x16/m8 opening work changes more gradually.

**Next norm discriminator (prospective):** Test this *same* x16/m16 P0
actual tangent once under an independently derived finite-width P0 L2
force/moment-density norm while retaining the H^(-1/2) result and all
primal scales. P0 cell-integrated actions divided by their basis length
give constant physical density, so its exact L2 Gram is diagonal with
cell lengths; keep the existing force/moment characteristic-length scale.
If the alternating Fz weak mode persists, review P0 trace resolution and
supported opening work; if the weakest mode changes materially, revise
the stability interpretation and norm contract before any P0 policy.
This alternate norm is a sensitivity diagnostic, not a replacement for
registered acceptance, an inf-sup bound or a multiplier selection.

**P0 norm/physical-action result and decision:** The analytic P0 L2
line-density comparator passed its independent quadrature test (`1/1`).
It is a six-resultant *line-density* norm with the already declared
`.1 m` moment-to-force length, not an independently derived surface
traction norm. The selected x16/m16 actual KKT uses the unchanged E4
Schur, native B3 tangent and six-channel rows; changing only the line
Riesz block gives `β=2.678405239e-6` rather than `0.001557025359`
under H^(-1/2). The two R-normalized dual shapes have absolute cosine
`0.999999985` under either line norm. L2 assigns `0.9999973` of the
mode norm to line dual, with `0.9998286` of the total mode norm in Fz.
The 1,742-row KKT retains rank `96/96`, drill/Schur errors
`1.23e-15/9.24e-16`, SVD defect `2.48e-16` and transpose-work error
`5.1e-21 J`; the run took `63.87 s`, one BLAS thread, below the retained
caps. Raw L2 result:
`B3_GE_E4_PL_F03_C1_P0_X16_M16_L2_MODE_DEV_V1.json`, SHA256
`00B2FC989584D2538B3E6E323764BCBF9839967406B1F5F91B9796D293EBE430`.
All underlying fixture/operator/norm-source hashes match the H^(-1/2)
extraction; only the runner's selected line norm and corrected support
metadata differ. Independent read-only review found no blocking defect.
It confirms the large beta ratio is norm normalization, not a physical
stability deterioration or a new mode.

The saved H^(-1/2) mode's physical shell z-cut reaction matches the
independently expected continuous-Q4/P0 rule
`−[A₀/2,(A₀+A₁)/2,…,(A₁₄+A₁₅)/2,A₁₅/2]` at all 17 bond cuts:
maximum difference `5.12e-10 N` (`9.17e-14` relative); the L2 mode also
matches. Alternating neighboring P0 Fz actions therefore cancel at shared
shell trace nodes. This is a weak *dual* action, not proof that the primal
solution locks. Existing supported x16 m8→m16 loaded work changes are
P0 `−0.238%` opening and `−2.536%` torque, P1 `−0.117%/−1.269%`,
dual P1 `−0.092%/−1.190%`; P0 physical shell work changes about `−1.11%`
in opening. The H^(-1/2) weak dual aligns with the loaded opening dual
(`0.351` absolute line-metric cosine) but essentially not the loaded torque
dual (`1.73e-11`); alignment is descriptive, not a load participation
factor. Hold P0 selection and distinguish supported physical convergence
from multiplier oscillation in the registered ratios and matched two-sided
reference before any resolution-policy or law change. F03/G0B remain open;
G1 remains barred.

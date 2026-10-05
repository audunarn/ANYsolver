# Restricted CalculiX nonlinear axial material counterpart

This is an implemented development candidate for the required CalculiX
counterpart, not qualification or E04 external-row closure. Roof response,
capacity, general finite-port beam moments and aggregate scientific acceptance
remain open. No numerical execution was performed by its implementation owner.

The runner imports the existing restricted-patch constants and immutable factory
without importing ANYsolver or changing that fixture. It retains the exact
shell coordinates, two Q4 cells, .002 m thickness, two beam edges at z=.01 m,
.01 x .004 m centroidal rectangles, E=210 GPa, nu=.3 and eight absolute force
targets `.05,.15,.35,.6,1,.6,.2,1` times 400 N. The native v3 input is actual
public recovery, not an analytical stress replacement.

## Adopted reduced beam contract

On the admitted straight identity-frame, pure-extension, elastic subspace,
each native GE half-cell has potential
`Psi=EA/(2*ell)*(uR-uL)^2`, with ell=.5 m. Its forces and work therefore match
SPRING2 with global directions n1=n2=ex and `k=EA/ell`. Four SPRING2 halves
retain their actual beam offset coordinates. This stiffness is a derived
elastic half-cell reduction, not a connector penalty. It does not represent
general GE rotations, shear, bending, torsion, fibre stresses or spectra.

Two CPS4 elements represent the independent plane-stress material patch.
Original shell nodes have only uy fixed and ux fixed at x=0. Original CPS4 z
is not constrained or tied by added equations; CalculiX's expansion supplies
its own plane-stress constraints. Beam nodes have uy/uz fixed and their x=0
ux fixed. The four nonroot point pairs use exact scalar equations ubx-usx=0.
On this fixed-rotation restricted subspace the finite pose bond reduces
exactly to equal translation; no affine approximation of a rotating roof is
claimed. NLGEOM, U1 and RIGID BODY are not used.

The official [CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf) supplies
SPRING2's force law in section 6.2.41; section 7.122 requires real spring data
with a decimal point. CPS4 expands to C3D8, producing eight integration points
per element. Thickness is supplied through SOLID SECTION. PLASTIC data is
von Mises yield stress against equivalent plastic strain: points `(1e6,0)`
and `(2e6,.01)` give the admitted first-branch hardening H=1e8 Pa. It is not
total-strain hardening or smoothing. Actual PEEQ must remain below .01 and
become positive in the full history.

The actual [spring input reader](https://raw.githubusercontent.com/Dhondtguido/CalculiX/master/src/springs.f)
consumes only the first 20 characters of each real field with F20.0. The first
bare-spring run exposed an over-width `.17e` literal whose exponent was
truncated, producing stiffness 1.68 N/m instead of 16.8 MN/m despite exit zero.
The analytical control correctly rejected its 11.90476 m extension. That raw
failure is retained. The corrected stiffness literal uses `.13e`, retaining
its decimal point and full exponent inside 20 columns. Every generated numeric
field is checked against the same width limit before deck delivery. This is
an input-format repair, not a stiffness calibration or physical change.

## Controls, accepted path and actual output

The bare spring control independently checks extension F/k and unloaded-root
reaction. The bare elastic CPS4 control checks
`epsilon=F/[width*t*E/(1-nu^2)]`, with expected axial/transverse stress.
Full execution requires completed pinned-executable evidence from both
controls, bound to the exact frozen fixture signature and generated control
deck SHA256. Its first endpoint separately checks the combined shell-plus-two
beam analytical stiffness. Controls use a conservative 1% screen and independent
print uncertainty; they do not qualify a general spring or shell formulation.

Every step requests STATIC,DIRECT with increment and duration both 1. Loads
are absolute CLOAD targets, and all eight steps remain in one input deck so
plastic history is uninterrupted. The STA parser retains every accepted
increment, attempt, iteration count and total/step/increment time. Exact
one-update-per-target correspondence is reported only when the accepted
inventory actually has one full increment per native target. A different
accepted path remains explicit partial evidence; no physical tuning is applied
to force an endpoint match.

The primitive v3 controls completed, but the original full-v3 deck stopped
at step 6, iteration 4 on the default divergence check; that failure remains
retained. The optional full-only `--iteration-diagnostic` inserts TIME
INCREMENTATION controls I0=25, IR=25, IP=25, IC=24. These are nominal input
settings, not a demonstrated effective iteration cap or guarantee that the
ordinary residual criterion stays active. Remaining active iteration
values and increment factors retain their documented defaults; all ten integer
and eight factor fields are explicit, with unused fields set to zero.
STATIC,DIRECT, single-increment targets, material, geometry,
loading, FIELD tolerances and output checks are unchanged. The original
default deck is byte-for-byte unchanged, while the optional deck has a distinct
hash and explicit diagnostic-only status. Existing exact v3 primitive control
decks remain the prerequisites. This option diagnoses iteration control;
it cannot close qualification or acceptance even if all endpoints complete.

The source-v4 focused checks passed 21 tests. The actual full-v4 diagnostic
returned exit 201 after five accepted steps. Step 6 recorded an unsuccessful
`1U` attempt with 28 iterations; CVG force residuals cycled between about
1915% and 2800%. Stdout confirmed the requested I0/IR/IP=25 and IC=24.
The nominal IC=24 was therefore not enforced as a hard execution cap in this
run. Iterations 25–28 also reached IP=25, so a late residual criterion switch
is possible; no accepted endpoint resulted. The originally intended
maximum-24/ordinary-residual execution contract was not demonstrated.
Current upstream source tests iteration greater than IP for the late switch;
the summary's conservative possible flag uses iteration greater than or equal
to IP and does not establish activation. Normalized CVG percentages do not
prove the internal divergence predicate or whether a switch actually occurred.

Failed executions can emit a lightweight CVG/STA diagnostic summary with
observed maximum iteration, nominal IC/IP, `budget_exceeded`,
`late_residual_switch_possible`, accepted-step prefix, unsuccessful attempts
and failed-step force-residual range. This summary never parses complete
DAT/FRD results or recovers success from a failed job. Terminal status stays
NUMERICAL_NON_SUCCESS. Missing trace evidence is represented as unavailable,
not an invented zero-iteration result. The original v4 source snapshot and
raw logs/STA/CVG remain unchanged. No rerun, enlarged budget or modified
diagnostic option is authorized by this result correction.

DAT requests include U and RF at every declared node, and actual S/E/PEEQ at
all shell integration points. Six stress and tensor-strain components are
retained. Engineering shear is twice the printed tensor shear. Actual sigma_zz,
eyy, shear strains and shear stresses are checked; ezz is free under plane
stress. Uniform exx and affine nodal extension are checked against actual
displacement. Actual original shell uz must also satisfy the existing 1e-10 m
admission threshold, even though the deck relies on automatic CPS4 constraints.
The parser requires all 16 material points at every printed time, then selects
ordered total-time endpoints 1 through 8. Duplicates, incomplete
components, unknown sets, unexpected points, nonfinite/underflowing values,
unordered times and missing quantities are errors. It never substitutes
elastic stresses, inferred PEEQ or nodal-averaged stress for actual plastic
integration-point data.

RF denotes external forces, including applied loads; it is a reaction only at
an unloaded support. The complete RF inventory is retained, but no full support
wrench is inferred from it without a validated transfer derivation. General
beam moment channels and beam fibre stresses are explicitly unsupported.
The actual axial RF values at unloaded roots 1,4,101,104 are summed against
the total applied force, with their own independent print bounds. This axial
reaction check is reported separately from material axial balance and work.

## Printed precision and response screen

Primary formatting sources are
[printoutnode.f](https://raw.githubusercontent.com/Dhondtguido/CalculiX/master/src/printoutnode.f)
and [printoutint.f](https://raw.githubusercontent.com/Dhondtguido/CalculiX/master/src/printoutint.f).
Nonzero DAT values have independent half-last-decimal bounds from their actual
scientific literals. Stress bounds remain component-specific: sigma_yy does
not inherit sigma_xx's exponent or bound when unloading produces different
stress magnitudes. Under the known normalized scientific format,
`+/-0.000000E+00` has zero decimal-formatting uncertainty. That statement does
not establish absence of arithmetic error or underflow before printing.
Generic fixed-decimal zero retains its decimal bound; a nonzero literal that
underflows binary64 is rejected. Missing scientific exponents are unsupported.

A threshold is certified only if `abs(residual)+print_bound<=threshold`.
If `abs(residual)-print_bound>threshold`, it is a measured mismatch; the
remaining interval is insufficient precision. Existing native balance
thresholds are unchanged. DAT material precision can leave the external
1e-4 N axial balance and .01 Pa uniformity unresolved even when actual response
agreement is close. That limitation is preserved as a non-success for those
checks, while collecting all eight actual endpoints. Status becomes
PARTIAL_EVIDENCE rather than a qualified pass.

Endpoint virtual work uses actual shell sigma_xx and total extension, plus
`sum(k*(uR-uL)^2)` from the exact derived elastic spring law and actual nodal
extensions. Applied work is F*u. This is not stored energy or accumulated
plastic dissipation, and the runner does not use half of F*u as nonlinear
energy. Independent uncertainty is propagated through each product; endpoint
virtual work retains the existing 1e-8 J threshold.

The prospectively conservative response screen compares axial strain,
sigma_xx and sigma_yy against actual native v3 recovery, with a 1% criterion.
Denominator floors come from the exact first-load combined elastic solution
and its axial/transverse stresses. Independent print bounds must resolve that
criterion; passing uses the complete uncertainty interval. This is not a
previously accepted nonlinear scientific threshold. Measured differences,
floor values, bounds and criterion flags are saved, and aggregate acceptance
remains open. Actual PEEQ is preserved and checked for branch/activity/history;
no unsupported cross-formulation PEEQ equality is scored.

## Bounded commands and evidence

The root orchestrator launches numerical jobs serially under the existing
600 s/2 GiB resource budget. The runner also enforces a subprocess timeout no
larger than 600 s and numerical thread environment values of 1. It verifies
the explicit CalculiX executable SHA256
`27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f` before launch.
No dependencies, product kernels, Git state or previous evidence are edited.
Calling without `--exe` prepares a deck with DECK_PREPARED status only.

```text
<python> scripts/r8_e04_ccx_restricted_membrane.py --mode spring-control --exe <pinned-ccx> --output <new-spring-dir>
<python> scripts/r8_e04_ccx_restricted_membrane.py --mode shell-control --exe <pinned-ccx> --output <new-shell-dir>
<python> scripts/r8_e04_ccx_restricted_membrane.py --mode full --exe <pinned-ccx> --spring-control-json <new-spring-dir>/status.json --shell-control-json <new-shell-dir>/status.json --native-input <native-screen-v3>/native.json --output <new-full-dir>
```

The executed diagnostic added `--iteration-diagnostic` to the full command in
a fresh output directory. This describes the retained v4 invocation, not
authorization for another numerical run. The controls' governing
definitions are in the official 2.23 manual's TIME INCREMENTATION section
(PDF pages 443–444). No FIELD card or physical tolerance change is introduced.

Each output directory must be new. Deck, runner, imported fixture and actual
executable identities are recorded. The pinned historical native v3 source
SHA is checked when its status predates explicit fixture signatures; future
signed evidence must match the frozen fixture identity. Raw DAT/STA and logs,
parsed inventory, partial parser prefix, actual observables, comparison and
status/errors remain available after failure. The focused tests cover decks,
actual inventory rejection, analytical controls, accepted paths, uncertainty
counterexamples and a failed execution with retained raw logs. Source-v4's
21-test pass and failed full-v4 evidence remain preserved. After this result
correction final source-v5 passed23focusedchecks(.42s). Offline actual v3/v4 summaries verify five accepted steps and the v4 nominal-budget overrun. No physical execution was repeated for this reporting correction.

The inverse-response discriminator is a separate prospective case. It preserves
all eight accepted-state targets and the physical model, but prescribes shell
UX at tips 3 and 6 from pinned native-v3 actual engineering axial strain times
L. Beam tip UX remains dependent through the original equations. Each step uses
BOUNDARY's default modification semantics, preserving roots and transverse
restraints; inverse decks contain no CLOAD. The original force decks, including
the consumed full-v3/v4 failures, remain unchanged. Inverse evidence cannot
complete the force case, close E04/G4D, or establish qualification.

Before full inverse execution, an independent one-step inverse elastic control
prescribes epsilon0=20/[2EA+width*t*E/(1-nu^2)], derived analytically without
native fitting. It retains the plastic law and requires actual PEEQ=0 at every
point, measured tensile actuator force 20 N, actual analytic membrane stresses,
root reaction balance and endpoint virtual work. Original exact spring/shell
control evidence remains prerequisite. An exact completed inverse-control deck,
fixture and executable binding is additionally required for full inverse history.

Only inverse decks tighten FIELD entries RN/RP/RL to 1e-10 and CN/Czero to 1e-8.
The eight fields are RN,CN,q0,qu,RP,epsilon,Czero,RL; q0,qu and epsilon remain
blank/default. The primary parser is
https://raw.githubusercontent.com/Dhondtguido/CalculiX/master/src/controlss.f.
STATIC,DIRECT retains one increment per target; accepted STA inventory is still
checked. No iteration diagnostic, substep replacement or geometry change is
combined with this case.

For the declared raw nodal RF convention, the transpose of each beam UX = shell
UX map transfers beam-tip force to its shell actuator coordinate. Thus each
actuator force is RF(shell tip)+RF(dependent beam tip), including each raw entry
once. Roots remain separate fixed coordinates. The independent elastic control
must demonstrate this convention; a different CCX RF convention fails the
control instead of selecting a fitted transfer. Endpoint actuator virtual work
is the measured actuator force times actual tip displacement, summed across the
two tips. Target force is used for response comparison only. This is endpoint
virtual work, not integrated plastic energy or a full support-wrench claim.

Full inverse comparison screens measured actuator force and actual sigma_xx/
sigma_yy against native endpoints using the prospective 1% response screen and
exact elastic load-scale floors. Imposed strain is never scored as independent
response accuracy. Actual CCX PEEQ versus actual native alpha mean/min/max
values, differences and independent CCX print bounds are retained; their
scientific acceptance remains pending. PEEQ activation, first-branch bounds and
per-point history monotonicity are separately checked. Physical plane-stress,
force and endpoint-work thresholds stay 0.01 Pa, 1e-4 N and 1e-8 J, with
independent printing uncertainty; insufficient precision is explicit.

Preparation/execution uses --mode full --inverse-elastic-control for the first
analytic control, then --mode full --inverse-response --native-input <v3 JSON>
--inverse-control-json <completed inverse-control status.json>, together with
the existing --spring-control-json/--shell-control-json and optional pinned
--exe. Full native source, fixture, endpoint dimensions and material branch are
validated before writing the inverse deck; payload/status and prescribed-motion
hashes are recorded. A fresh output directory is required. One-step DAT/STA
inventory is admitted explicitly only for the analytic control. Successful
inverse controls use COMPLETED_INVERSE_CONTROL; full inverse results remain
PARTIAL_INVERSE_EVIDENCE or INVERSE_RESPONSE_SCREEN_FAILED. Failed executions
remain NUMERICAL_NON_SUCCESS with raw logs and partial prefixes.

The orchestrator executed 38 focused checks successfully (0.49 s). The analytic
inverse control completed with a measured 20 N actuator force and passed force,
reaction, endpoint-work, thickness and prescribed-boundary checks. Its original
log parser falsely rejected an intermediate Newton `no convergence` report;
that failure remains preserved. Re-adjudication used the unchanged completed raw
execution with the repaired parser, without repeating the physical run.

The full inverse history completed all eight one-increment endpoints. Maximum
normalized force/stress difference including independent print uncertainty is
8.580e-7; maximum actual native-alpha/CCX-PEEQ statistic difference is 3.170e-13.
All 16 unloading-thickness checks pass; maximum actual absolute Szz is
9.401e-8 Pa. Twenty balance checks pass and four remain print-precision limited;
uniform-stress precision also remains insufficient. These are partial development
results, not scientific acceptance of material-state equality or closure of E04.
The original force-controlled failures and G4D remain open.

Evidence is retained in `.qualification/b3-ge-e4-pl/
r8-ccx-inverse-material-dev-20261005-v1`: exact executed v1/v2 sources, failed
initial adjudication, repaired control adjudication, complete inverse raw output,
source checks, execution records and summary-v3.json. Full execution took
0.317 s with sampled process-tree peak 27.7 MB; one-CPU affinity was set before
execution, declared numerical pools were one, and sampled numerical/unresolved
thread maximum was one. This is resource evidence, not a performance gain.
Supporting independent OpenAI Read review found no unresolved defect; required
different-model-family acceptance is not supplied by that review.

The analytic inverse control additionally checks actual IP ezz against
-nu/(1-nu)*epsilon0 at the existing 1e-10 strain threshold. For full inverse
history, unload-thickness-diagnostic.json retains all 16 actual step-5-to-6
increments, compares Delta ezz with -nu/(1-nu)*Delta exx with independent print
bounds and the same 1e-10 threshold, and reports actual PEEQ before/after/change
and its printed bounds. Thickness mismatch remains non-success; actual history
agreement is reported for scientific review without inventing a state-equality
gate from merely monotone PEEQ.

Every inverse endpoint additionally verifies each actual printed tip UX (nodes
3 and 6 separately) against its pinned prescribed motion, or the analytic
control motion, at the unchanged 1e-10 m displacement floor with independent
print bounds. Opposite tip errors cannot cancel through an averaged strain.
A mismatch fails; an uncertainty interval crossing the floor cannot certify
execution. Records/status label this imposed_boundary_verified, explicitly not
independent strain response agreement. Completed inverse-control authority also
requires this verified execution flag.

The saved inverse-control-v1 process exited 0 and printed ordinary Newton
`no convergence` at iteration 1, followed by `convergence` at iteration 2 and
`Job finished`. The prior terminal-log screen incorrectly rejected that progress
message. The corrected screen rejects nonzero exit, *ERROR, FATAL, exhausted
cutbacks and a missing completion marker; intermediate Newton nonconvergence is
not a terminal error. Strict complete accepted STA and actual DAT inventories
remain mandatory after the process/log screen. The original v1 raw failure and
source snapshot remain retained; this parser correction does not itself claim
that control evidence passed its mechanical checks or authorize another run.

# B3-GE / E4-PL / B2 active state

Updated 28 September 2026 for Revision 7. This is the short working record. The
prior full version is preserved in Git at 69224fba; the historical checkpoint,
complete programme, registrations, failures and evidence retain their meaning.
ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1 applies prospectively.

## Decision sought

Deliver the experimental multi-element point-connected GE/B2 workflow while
resolving a defensible six-channel native line law and growing multiplier space.
G0B/F03 remain open; G1 acceptance and production qualification are barred.
Formal F03 execution authority is unconsumed. There is no release or speedup
claim. The factor-4 Fy fallback script remains dirty and unrun.

## Delivered behavior and evidence

- ANYsolver commits d2b05423, a2bc9a3f and b6d2b8a9 provide the sparse GE development
  owner: multiple Q4/S3 shells and native B3 members, point connections,
  retained variables, reference-linear and short finite elastic solves,
  reactions, atomic stepping, cancellation, checkpoint/restore and continuation.
  Eligible unchanged reference-linear cases reuse one factorization. Small
  existing JSON checkpoints retain V1 decoding; model-sized states use a
  bounded V2 binary-array format. Digest-valid but mechanically false states
  are rejected, including extreme finite loads that formerly overflowed
  the equilibrium norm.
- The separate B2 development profile handles compatible 1/10/100 loads with
  selected recovery and factorization reuse. Bounded Q4/B2 point-panel and
  dense-oracle parity exist. Commit 92423213 rejects B2 outputs whose finite
  binary64 rounding loses more than the declared relative precision, including
  an independently checked subnormal case. Wider B2 conditioning,
  mass/prestress and scale qualification remain open.
  A separate fixed-magnitude, nonproportional mixed-wrench check over three
  constant-area rectangle aspects agrees with an independent rational
  cut-wrench/work oracle and root/free balance. This samples one physical
  direction; F09 range admission and G0B remain open.
- ANYfem commit c7035a7 provides a separate experimental GE-panel format,
  save/reopen and headless restore/continue. Ordinary project formats retain
  their existing route.
- Development installed wheels have SHA-256
  92F2E4DB51BBFCAA7F1AB5A07E03900209F601BFA17F036E0B8136E5FF778A88
  (ANYsolver) and
  C7E9D005DFEDDDC6D23C1D6757E29B3F314A7E94F614C98E0EEA76C87236D467
  (ANYfem). Actual installed imports passed 61 solver and 3 consumer checks.
  Windows/Python 3.14.2, one OpenBLAS thread
  and NUMBA_DISABLE_JIT=1 were effective. Wheel bytes, build/install/test logs,
  imports, dependencies and manifest are preserved under
  .qualification/b3-ge-e4-pl/r7-integration-dev-20260928-v4/.
  These development wheels do not satisfy G6.
- A read-only independent integration review found no confirmed owner,
  checkpoint, B2-batch or ANYfem input-consumer defect, but v4 omitted exact
  test nodes. Supplemental installed evidence v5 binds the same wheel hashes
  to named 31 solver and 3 consumer passes, commands, imports and one-thread
  settings. Finite restart supports final-state continuation; the checkpoint
  alone does not independently replay every historical increment.
- Reference equilibrium is screened by tangent-relative, unit-covariant
  residuals per element and after assembly. This is a roundoff screen, not
  an absolute physical force limit or G0 stress-free qualification.

## Mechanics uncertainty and next discriminator

The saved off-ratio Fy/rotation diagnosis showed alternating force/couple
cancellation. A smooth loaded Fy pair passed supported equilibrium but did not
excite that least mode or select a law. The factor-5 CalculiX Fy run timed out
without a physical result. Historical classical axial, Q6/finite-pad, F5 and
native six-channel references remain distinct. Do not launch the prepared
factor-4 fallback merely because it exists.

The private L1 probe, extended in commit 76180114, uses an objective
reference-offset SO(3) Log pose gap,
physical E4 projected-tangent/director trace and retained B3 half-cell port.
Its reference, first variation, local point-work Hessian at nonzero multiplier,
objectivity and chart checks pass. A bounded two-segment probe composes four
interior L1 work stations and exact derivatives of that discrete weak action
through E4 and native retained B3 ports. Independent review found missing
reference-length and port-correspondence guards; these now reject changed
geometry or an undeclared offset/wrong port. Continuum quadrature, large-origin
accuracy, physical transfer and multiplier stability remain open. Its shell-frame
translation differs from the saved candidate's
beam-frame translation; constrained zero sets can agree while multipliers and
off-constraint work differ. The law must be chosen and derived.

The independently read-only reviewed prospective draft at
docs/agent_plans/B3_GE_E4_PL_G0_F03_PROSPECTIVE_ASSESSMENT_DRAFT.md states
prerequisites for a reference-relative compliance test: physical stationary
reduction, positive supported work, exact gauge, same-law converged reference
and work-preserving action injection. Its reference, numerical floors and
thresholds are not frozen; formal F03 assessment is barred. Rank or one
quotient cannot select a multiplier space.

The bounded translation-frame discriminator now shows identical constrained
first virtual work under the derived dual map and balanced eccentric wrenches,
but different fixed-multiplier curvature off the constraint. Retain the
shell-frame pose-joint convention as the explicit L1 development candidate;
freeze its dual/work convention before any formal F03 assessment. This result
does not select a production line law or multiplier space. The next comparison
must use its declared weak work with growing candidate spaces, physical
transfer and mixed-system stability; the three-node probe is not a policy.
An existing bounded test already verifies exact native-retained condensation,
including the interface action on cell rotations, for the earlier local-
translation law and a supported Q4 panel. A no-JIT straight-beam check at 4/8
half-cells also found an invertible indefinite retained block and positive
supported reduction; a JIT-enabled attempt exhausted its 600 s ceiling before
returning a matrix. These facts do not establish positivity, nullspaces or a
same-law reference for integrated L1. Carry its retained trace action through
the reduction before interpreting a compliance quotient.
Independent review of the prospective contract requires a new L1-specific
p-only stationary-reduction/parity proof, a whole-space work-preserving
reference injection, exact gauge inclusion, and explicit virgin zero-multiplier
scope. The draft now records these prerequisites; formal assessment remains barred.
Immediate bounded design question: can the L1 work act only on supported
physical/cell-rotation coordinates after exact resultant elimination, and can
complete six-channel growing P0/P1/dual candidate spaces resolve it without
an unsupported mode or locking? A small coupled p-only parity/positivity check
and one macroelement space comparison distinguish an invalid reduction, an
underresolved discrete space, and a law-level work defect. Positive parity
allows a same-law reference design; a failed reduction or physical work check
requires correction before ratios. Surviving spaces proceed to the registered
seven ratios, physical transfer and convergence; no single quotient selects one.
The first p-only check found the actual Q4 tangent contains existing PL drill
completion, while its reported physical component has zero drill rows. Keep
actual-matrix parity distinct from physical-work stability; do not count
completion alone as beam torque-transfer evidence.
The completed bounded 2/4-edge L1 design check found an exact alternating
shell-normal zero-action row in the consistent full-P1 dual's virgin
reference-linearized work on these straight half-cells. The two mixed
six-channel spaces have full numerical local rank in unscaled SI coordinates:
P1 translation/twist with edge-P0 pitch/normal represents the alternating
field, while edge-P0
translation/twist with two-edge pitch/normal omits its alternating action.
Both preserve the tested shear and native torque work without shell-drill
work. These are local action results, not mixed-system stability or selection.
On one supported virgin Q4/native B3 fixture, all 18 L1 nodal dual actions
vanish on the 72 generalized resultants and act on retained cell rotations.
Resultant-only stationary reduction matches full-retained compliance to
1.4e-12 relative error. The stationary-reduced supported physical block is
positive on this fixture, but the actual full retained tangent is indefinite
and includes PL drill completion. The separately exposed drill-free physical
component has an exact drill gauge and positive quotient on this fixture; the
18 tested diagonal coordinate-basis compliance actions differ by up to 3.45%
from those of the operative tangent. Neither result
certifies physical stability. The full-P1 dual as constructed cannot advance
without a derived remedy for its exact null; do not select either mixed space
from rank. Physical transfer and locking still require a same-law reference
and the growing-space envelope. No formal F03 run has occurred.
The targeted two/four-edge A/B KKT screen now holds the 0.5--1 m eccentric
line, full panel, supports and physical Fy/torque actions fixed. Equilibrium,
weak compatibility, interface virtual work and spatial wrench balance pass.
A/B Fy load-displacement work differs by about 0.009%; B torque work is
3.95%/2.31% below A at two/four edges. On the actual PL response, shell
completion contributes 8.8--10% of Fy work and 0.16--0.25% of torque work.
Freezing every free drill coordinate reduces Fy compliance by about 95%, but
adds kinematic supports and is not a stabilization-parameter sensitivity.
Independent read-only review found no blocking input or KKT defect and warned
that two-level partial refinement and balanced assembled work cannot certify
physical transfer. The exact-source, one-thread result is preserved in
[the development evidence](B3_E4_F03_L1_AB_MATCHED_LOAD_DEV_V2.json).
Decision: retain A/B as development candidates, exclude the present full-P1
dual with its reference-linearized null, and do not select a line law or
multiplier space. The next discriminator is an independently constructed,
work-preserving same-law reference for the unchanged physical supports and
actions, with physical transfer, locking and drill/completion interpretation;
if that map cannot be derived, obtain focused mechanics review of the missing
equation. No further classical axial refinement or automatic mesh sweep.
The A/B multiplier fields nest exactly on the unchanged 0.5--1 m line at
2/4/8 edges: their complete sampled quadrature work maps commute with the
injection, including the actual four-edge native gap Jacobian. A subsequent
same-law screen refined the entire Q4 panel and native beam together at those
three levels, holding supports, material, offset and Fy/torque actions fixed.
All supported KKT solves, work partitions and spatial balance checks passed.
For A, Fy load-displacement work was 0.04514/0.04948/0.05080 N m; the A/B
torque-work gap fell from 3.95% to 2.38% to 1.00%. The shell-completion share
of Fy work fell from about 9.97% to 2.76% to 0.72%. Yet the final 4-to-8
change remains about 2.7% in Fy work and 2.4% in A torque work; this is not
a converged reference. The source-bound one-thread results are preserved in
[the whole-panel development evidence](B3_E4_F03_L1_WHOLE_PANEL_DEV_V1.json).
Matched uncoupled controls on those same grids give shell-only Fy work
0.05898/0.06659/0.06901 N m and shell-completion fractions
13.0%/3.71%/0.98%. The native-only torque work is invariant at
0.00742857 N m and matches the independent uniform-GJ torsion oracle.
The coupled Fy shift follows the shell-only trend, though that does not
uniquely allocate coupled error; native beam discretization alone cannot
explain the coupled torque trend on this fixture. The source-bound outputs
are in [the matched controls](B3_E4_F03_L1_UNCOUPLED_CONTROLS_DEV_V1.json).
One-direction Q4 checks around the eight-edge shell-only control changed Fy
work from 0.069010 to 0.069714 N m (+1.02%) when x was doubled, and to
0.069030 N m (+0.029%) when y was doubled. The remaining shell-only change
is predominantly longitudinal on this fixture. The source-bound results are
in [the directional evidence](B3_E4_F03_L1_SHELL_DIRECTIONAL_DEV_V1.json).
The directed coupled x-refinement used that same physical line, loads and
supports at 16 line edges/32 native half-cells while retaining the nine-node
transverse shell grid. A/B Fy work was 0.051162/0.051175 N m, an A increase
of 0.71% from eight edges versus the shell-only x increase of 1.02%. Their
torque-work gap fell from 1.00% to 0.27%, but A torque work still changed
1.29%. Shell-completion share of A Fy work fell to 0.20%. Equilibrium,
compatibility and integrated work remain satisfied. The source-bound result
is [the directed coupled evidence](B3_E4_F03_L1_LONGITUDINAL16_DEV_V1.json).
This supports a shell-resolution explanation for much of the Fy trend; it
does not prove convergence, physical connection fidelity or uniform stability.
The bounded dense shell fixture cannot represent another full refinement.
The replaceable L1 local operator now reaches the experimental sparse owner;
small sparse/dense and linear lifecycle parity pass. External physical
transfer and independently reviewed F03 floors remain separate.
The first product-private L1 local operator is now extracted. It returns the
six gaps, their 21-coordinate Jacobian, multiplier-work gradient/Hessian and
nine native retained gather slots without a model-wide dense derivative or
the development Context's 120-second lifetime. Independent read-only review
found and then confirmed repair of a large-origin low-part loss in the work;
the added sub-ULP gap/work check and 44 focused probe/port/local tests pass.
The extracted operator is now connected through a replaceable elastic sparse
assembly seam. No multiplier policy is selected and F03/G0B remain open.
The experimental owner now assembles an explicitly mapped, four-edge L1
material line with two-point Gauss work and either complete A or B six-channel
multiplier space. The bounded Q4/native B3 panel passes sparse/dense solution,
integrated action, force/moment balance, linear checkpoint/restart and precise
negative checks. A reviewer found a finite-checkpoint restore bypass and a
point-only checkpoint-identity regression; both were repaired with regression
checks. This route has matching shell edges and beam half-cells only; it is a
replaceable development integration, not qualified nonmatching line coupling,
multiplier selection, or F03 acceptance. The bounded next discriminator held
the 0.5--1 m line, supports, material and Fy/Mx actions fixed, tested
two/four/eight-edge parity and extended one full-panel level beyond the dense
fixture cap. It did not authorize an open refinement campaign.
The planned sparse-owner batch is complete at two, four, eight and sixteen
line edges. At two/four edges, its A/B physical load works agree with the
earlier bounded dense actual-PL oracle to about `1e-12` relative; at eight,
the largest relative discrepancy is `3.5e-7`. The full 16-edge panel uses
512 Q4 and 16 native B3-GE elements, 3940/3920 mixed rows, at most 291 MB
observed process RSS and 36.2 s for both A/B candidates. The sampled RSS
and measured elapsed time are below diagnostic ceilings; this is not a
process-peak memory measurement. Each unchanged operator is factored once.
From eight
to sixteen edges A's Fy work changes `+0.738%` and Mx work `-1.141%`;
B changes `+0.747%` and `-0.409%`. At sixteen edges B differs from A by
`+0.025%` in Fy work and `-0.266%` in Mx work. Compared with the earlier
dense 16-edge longitudinal-only result, the full sparse 16-edge result
differs in Fy by about `0.025%` and Mx by about `0.15%`. This comparison
also changes assembly route, so it does not isolate transverse refinement.
See the four source-bound runs:
[N02](B3_E4_L1_SPARSE_OWNER_N02_DEV_V1.json),
[N04](B3_E4_L1_SPARSE_OWNER_N04_DEV_V1.json),
[N08](B3_E4_L1_SPARSE_OWNER_N08_DEV_V1.json), and
[N16](B3_E4_L1_SPARSE_OWNER_N16_DEV_V1.json).
Decision: sparse integration and the prior reference are consistent, and the
remaining resolution trend appears chiefly longitudinal on this fixture. No same-law limit
or physical fidelity is established; stop further automatic refinement and
advance the matched torque/shear transfer reference and independently reviewed
growing-space/mixed-system stability contract before multiplier selection.
An isolated wheel built from the clean `fa9d9e4d` source archive passed seven
fresh-process installed checks for both A/B weak-line candidates, the sampled
work oracle, negatives and restart. Actual package import, wheel hash,
dependency identities and effective one-thread OpenBLAS settings are in
[the installed development report](B3_E4_L1_INSTALLED_DEV_V1.json). This is
installed wiring evidence, not G0/G2 qualification or final-platform CI.
An inert folded S4 flat-web/T CalculiX deck and action-work reader now exist
for plate/web Fy and web torque. Its clamped-root option matches the declared
six-DOF support type but lacks verified rotational reaction output; the hinged
option has a complete force-lever support wrench but is not a B3 clamp match.
Saved S4 FRD and separate solid RF files validate grammar only. No new solver
comparison or interface-sided traction has been established. Proceed with
independent F01-F13 and GE/B2 lifecycle work that does not depend on this
decision. Preserve all seven ratios, growing spaces, three refinement levels,
physical transfer/locking and the registered G0-G6, F01-F13, V01-V28 and
B01-B18 scope. None of F01-F13 is fully accepted yet.

Next bounded external-route discriminator: determine whether the inert folded
S4 flat-web/T deck can produce and parse actual clamped-root Fy/torque work
and support output under the pinned CalculiX binary. Competing explanations
are an untested output/parser route and a valid but mechanically unmatched
reference. Run only the smallest fixed deck as a smoke, first checking the
binary identity, thread setting and resource bounds. A parsing failure calls
for a targeted output-contract repair; a passing smoke permits a separately
designed geometry/load/section-matched comparison, not an F03 score or a new
refinement series. Rotational reaction and seam-sided work remain explicitly
unverified even if the smoke passes.
The first actual clamped flat-web/Mx smoke completed in 0.24 s but its parser
correctly rejected the generated deck: Windows text-mode output changed the
LF bytes after their hash was recorded. The generator now writes exact ASCII
bytes, and 11 focused tests pass. A fresh pinned CalculiX 2.23 run completed
and parsed the same smallest deck; the loaded action work was `0.001579051 J`
and the force-balance residual was below `8.1e-7 N`. CalculiX reported one
CPU for assembly, stress and factorization. This validates the external output
route only. The current flat-web/T geometry and section are not matched to
the native square B3 fixture; clamped rotational reactions and internal seam
tractions are still unavailable. Do not compare the work against native L1 or
advance F03 from this smoke. Both raw runs and their source-bound hashes are
retained in [the smoke record](B3_E4_F03_CCX_FOLDED_SMOKE_DEV_V1.json).
Independent review of the prospective F03 contract found the stationary
reduction and exact-gauge quotient sound under its stated assumptions, but
requires an explicit support-preserving physical-field map `T_h` and a frozen
same-law reference-error rule. The draft now records both as open
prerequisites; no formal assessment has started.
Next matched-geometry discriminator: the old folded S4 smoke has a 1 m-wide
plate and a web centroid/section unlike the native B3 fixture. A new bounded
`native_line_geometry` deck sets the plate to 1 x 0.2 m, puts its reference
nodes at the physical top face with CalculiX shell OFFSET=0.5, and places the
0.01 x 0.2 m web centroid 0.1175 m above the E4 midplane. Before any response
comparison, run its four-edge clamped flat-web Fy/Mx output path. A missing
or ambiguous face displacement/reaction means repair the reference mapping;
a passing route permits construction of the same-section native B3/E4 model.
Neither outcome scores L1 or selects a multiplier space. The T variant remains
a separate engineering model until an admissible matching beam section exists.
The four-edge flat-web external Fy/Mx deck and the independently constructed
native B3/E4 counterpart both execute. Independent read-only review found no
geometry, shell-offset sign, root-support or applied-resultant mismatch.
Calculated action works are external `0.000689073/0.001878843 J` and native A
`0.000591246/0.001447212 J` for plate Fy/web Mx; native B is
`0.000591260/0.001451488 J`. Thus native A is about 14.20% and 22.97% lower
in the two one-level works. External cross work is about `-6.652e-5 J`, versus
native A about `-1.109e-5 J`; both routes pass their own reciprocity checks
within output/solve precision. See the versioned [paired development record]
(B3_E4_F03_FLAT_WEB_MATCHED_DEV_V1.json) and preserved raw output. These
differences are not an F03 score: S4 welded-web deformation, native B3 section
idealization, shell formulation and line transfer remain entangled. The next
bounded discriminator is an uncoupled plate/web section control or a verified
sided-work reference, not automatic mesh refinement or multiplier selection.

## Execution boundary

Revision 7 permits experimental integration during open G0, at most three
workers and one heavy numerical job at a time. New bounded diagnostics may use
at most 100,000 rows, 600 seconds, 8 numerical threads and 8 GiB per process
tree after verifying effective settings. Historical one-use executions are
not replayed. The complete release still requires the external references,
practical scale, installed-platform checks and independent acceptance.

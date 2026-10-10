# Finite V2D shell against a fixed planar rigid patch

## Current development scope

Opt-in profile: `S3_V2D_FIXED_PLANAR_RIGID_COROTATIONAL_PENALTY_STATIC_DEV_V0`.
It composes the existing ordinary force/displacement driver with exact elastic
NativeParity S3 V2D owners and a fixed finite planar triangulated tool. Native-TL
companion S3 is excluded. Existing affine rigid and paired finite profiles keep
their defaults and checkpoint contracts.

The current installed public producer completed press/slide/open/recontact at
explicit tolerance1e-11, with four snapshots/history rows and two owner states.
Independent saved-field assessment passed the original equilibrium, wrench,
complete force/work, pressure, support, integration and physical-gap criteria.
Actual active stage2 and open stage3 prefixes each passed public advancement,
followed by separate rich and bare terminal restores. Trial rollback, checkpoint
refusal and affected affine lifecycle checks passed. Earlier caller, stopping,
arithmetic and test-setup failures remain retained. Staged source checks are not
an installed whole-suite pass. No engineering acceptance or release.

Evidence: `C:/ANYworkspaceWork/contact_finite_v2d_rigid_patch_delivery_20261009`;
current private artifact `built-install-v9.json`, 654 payload files; wheel SHA256
`8d826bc86358e7a0a46ff836753ab97884739a3e2a59d738d32746ba5f4a8f75`.
DEV480/90 protected reserve is
parent-owned; no closed balances are pooled.

## Physical fixture and law

First fixture:4shell nodes /24structural coordinates /2V2D source triangles /
2fixed tool triangles. Tool variations are exactly zero. Counts describe the
fixture, not universal mesh qualification. Source reference x=0.10-0.95m,
y=0.13-0.98m, z=0.0350002m; thickness0.05m /reference offset0.01m. Bottom skin is
`X+u-0.035 Exp(theta)e_z`. Fixed tool rectangle before seed rotation:
x=0.18-1.10m, y=-0.02-1.10m, z=0. Both share an initial0.5rad y rotation about
(0.6,0.6,0), preserving0.2um clearance. All6coordinates at node1 are physically
clamped to this seed; all18coordinates at nodes2-4 are unknown. No hidden gauge
or stiffness. The initial common frame is not relative finite-motion evidence.
A disposable0.08rad relative-pose discriminator passed; it is not a new trajectory.

`ContactInteraction.normal_law='penalty'` explicitly selects enforcement.
The generic settings `enforcement_solver='nested_augmented'` are dispatch/runtime
requirements here; this manager has no AL multipliers or monolithic AL solve.
Shared P1 energy is `E=k/2 sum_i min(W_i,0)^2/S_i`, k=1e6. Every face contribution
is accumulated globally into S_i/W_i before normalization and differentiation,
retaining support derivatives/cross-face coupling/allpositive supports.
Gap positive means separation; safety limit is-50um.

Four cumulative stages press/slide/open/recontact apply the declared incremental
physical loads to nodes2/4. This is force-controlled slide, not prescribed20mm
motion. Force/moment scales are separately1e-4N /1e-4Nm. No friction, curved/free
tool or material widening.

The example explicitly requests residual tolerance1e-11. With18 free coordinates,
the conservative `sqrt(18)*tolerance` L1 allowance is below the1e-10N/Nm raw budget
implied by the1e-4 force/moment scales and1e-6 equilibrium criteria. Independent
per-pose gates remain mandatory. The original default-stop route completed but
failed independent equilibrium. A1e-12 request retained8 accepted partial poses
before minimum-increment refusal inside slide; neither attempt is promoted.

## Work, enclosure and state

Physical-coordinate derivatives use additive-chart mapA; spatial-spin force uses
mapB. Tangent is `B.T H A + D(B.T f)`, including director work. A/B must not be
identified; a1rad chart counterexample passed. Existing total-angle1.2rad,
local-rotation0.1rad and local-deformation/edge0.01 limits remain.

Fixed-plane height conversion is `g=Nt.(x-t0)*|Ns|/(Nt.Ns)`. Directed interval
boxes include endpoint, Exp and path-curvature errors; positive reference/mutual
charts are required. Older allcorner bound remains a safe conservative fallback.
Alltime positive P1 support has quantified area above the actual productioncutoff.
Each potential pair needs represented overlap /strict separation /strict opening
throughout every slab. Endpoint-only proofs are insufficient. Exact artificial
internal-diagonal touch may conservatively refuse although endpoint neighbour
ownership permits it; broader topology capability stays open.

Fresh seeds require near-zero nonnegative clearance. Restart negative geometry
within50um is permitted only after ordinary model/analysis/typed-owner validation.
Pending checkpoint managers cannot evaluate/advance. No incoming state is migrated,
resealed or stripped. Existing V2D global18 COROTATIONAL +local18 constitutive
contracts apply. Active2 advanced through stages3/4 and open3 through stage4;
terminal0 restores were checked separately. Terminal displacements matched the
fresh run at rtol1e-8/atol1e-12, supported forces at rtol1e-7/atol1e-12, and both
typed owners passed the existing model-bound validator without resealing.

## Public usage and checks

`examples/general_contact_finite_v2d_rigid_patch.py`: `--through-stage`(2/3/4; default4),
`--output`, `--restart`. New output path required. Actual returned suffix poses,
material records/history/diagnostics/terminal checkpoint are saved. Earlier poses
are not reconstructed from terminal state. Prepared exact private-artifact jobs
run through the existing guarded Python314 bootstrap after parent adoption.
Stage1 is refused before solve: the ordinary driver's load-factor1 sentinel
means the complete programme, so it cannot produce a genuine stage1 prefix.
Use stage2 for an active restart prefix and stage3 for an open prefix. The earlier
stage1-request artifact actually ended at stage4 and is retained as a semantic
NONPASS, not an advancement witness.

Independent saved oracle imports no production contact kernel: P1/P1 polygon
integration and independent first-order dual arithmetic, exact degree2 polynomial
integration with separate order4/8 Duffy controls(1e-7 allocation). Complete force
work1e-6 and additive tangent1e-5; independent Decimal Rodrigues/rational plane
bounds for safety and strict opening. Fresh structural reassembly checks separate
free force/moment equilibrium and wrench1e-6. Penalty relation1e-8 is labelled
penalty, not AL NCP. Tests retain exact node IDs and actual output dependencies.

Saved mechanics passed on all four installed fields: maximum normalized free
force4.0452e-8, moment2.0682e-10, pressure relation2.6641e-13, complete force/work
3.6186e-13 and support1.3953e-15. Minimum independent gap is -0.4131um, within the
-50um limit; the release field has a strict positive lower bound0.1755um.
The same-law affine corner-gap arithmetic avoids global-coordinate subtraction
cancellation and is bound into this profile's restart identity. Earlier prototype
checkpoints are not silently migrated. The uniform-Y null direction is checked
as absolute invariance under the original force/moment scales, not as relative
tangent PASS. Active nonzero tangent probes passed both original step sizes;
the open branch is recorded separately as zero response.

The two installed restart cases and five final safety/compatibility cases passed
with no errors or skips. Cancellation was triggered after actual material and
contact trials; committed store, input checkpoint, contexts and hooks rolled back.
Corrupt rich checkpoint/null input and a finite committed-coordinate mutation
were refused. Exception evidence covers these checkpoint/refusal/context paths;
it does not establish arbitrary candidate-exception safety. The old affine force
and lifecycle/restart case passed on the new artifact.

All21 current new-family obligations have successful staged evidence, combining
source-overlay checks reused by impact with installed caller/saved/restart/safety
checks. This is not one installed whole-suite run. Extra numerical arithmetic,
null-invariance and legacy checks are recorded separately in the raw handoff.
Broad cut-front
stability, continuum qualification, C0-C9/strong gates and independent engineering
acceptance remain open. Author verification cannot establish acceptance/release.

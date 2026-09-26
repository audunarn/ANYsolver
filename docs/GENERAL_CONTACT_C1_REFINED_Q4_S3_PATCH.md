# C1 development profile: multiple Q4 pressure faces against S3

The current augmented static profile is
`Q4_S3_PATCH_REFINED_NODAL_PRIMAL_MORTAR_AUGMENTED_STATIC_DEV_V1`.
The earlier `...DEV_V0` results below are historical source-bound development
evidence. V0 produced spurious tangential work when partial overlap changed
at a uniform physical gap; it is not an accepted frictionless sliding profile.

The profile admits a conforming source patch of at least two qualified Q4 faces against an
explicit S3 V2D target patch. Source Q1 pressure nodes are shared by material
node identity. The projected augmented normal law uses the same physical Q4
skin and S3 side/offset work maps as the one-Q4 route. Pair-local weighted-gap
and support derivatives assemble into the shared pressure space. The complete
residual is retained for both-body reactions; the tangent evaluates only
physical coordinates reached by the solver's reduced unknowns.

For each supported source pressure mode, let $w_i$ be its weighted gap,
$s_i>0$ its reference support, $g_i=w_i/s_i$ its normalized gap and
$p_i=\max(0,\lambda_i-\epsilon_n g_i)$ its projected pressure. The V1
normal residual acts through $b_i=dw_i-g_i\,ds_i=s_i\,dg_i$:

\[
R_c=-\sum_i p_i b_i.
\]

The tangent differentiates both the projection and $b_i$, including mixed
weighted-gap and support derivatives. This removes boundary-overlap work
from a uniform-gap tangential translation while retaining the changing
projection in the consistent, generally nonsymmetric tangent. Static and
path profile versions were incremented together; restart rejects an old
contract. The independent skew partial-overlap oracle checks normal wrench,
zero frictionless lateral work and a smooth-branch directional tangent in
`tests/test_general_contact_skew_partial_work.py`.

On source `136f81539ec6859517b17cb20a498a7fb263f09d`, the affected
source-controlled suite passed 46 tests; two opt-in coupled checks were
skipped. A separate eight-step path with eight Q4 pressure faces and two
nonmatching S3 target faces completed press, 50 mm slide, full opening and
recontact under the unchanged 50 µm physical gap budget. Final minimum gap
was −1.832 µm and normal force was 0.0223588 N. A six-step open checkpoint
resumed through recontact and produced an exactly equal final checkpoint.
The old-profile checkpoint was rejected by contract identity. These are
local development results; pressure-space stability on partial contact,
independent assessment and C1 engineering acceptance remain open. Raw runs
are under `C:/ANYworkspaceWork/general-contact-evidence` with the
`c1-eight-q4-normalized-*` prefix.

An offline wheel from clean commit `d1e8393be709af5779fa840c59655226833c2088`
was installed into an isolated target. Import origin was asserted there, and
the installed eight-step example produced checkpoint bytes identical to the
source run. The wheel was not published.

The skew partial-overlap oracle now exercises two, four and eight Q4 source
faces. It checks the independent constant-traction force and moment, paired
wrench and the rank of physically supported pressure modes. The eight-face
mesh has 16 supported modes; two nodes lie on a source strip entirely beyond
the target. The supported Gram remains positive definite, but its condition
depends on cut support. This fixed-pose evidence does not establish coupled
pressure-space stability or mesh/enforcement convergence.

One skew corner approach exposes the current profile's resolution boundary.
Uniform strips in x leave every normalized pressure-mode gap positive while
the independently checked physical gap closes near the target edge. A
two-dimensional local Q4 grid represents an active pressure mode there, but
the existing whole-face conservative gap lower is much looser than the
planar overlap gap: −131.44 µm versus approximately −35.18 µm in the
retained pose. The 50 µm swept-path gate correctly stops the present route
under its current certificate. An overlap-aware static bound and a matching
conservative swept certificate require separate derivation and tests before
this case can be admitted as a coupled path. The fixed-pose observation is
not an accepted solution.

The first admitted coupled case has two adjacent Q4 source faces and two
nonmatching S3 target faces. Direct local work matches whole-patch projected
normal residual to a maximum absolute difference of (5.6\times10^{-13})
on a smooth active pose. A local directional tangent check gave relative
error (2.0\times10^{-8}) over the tested perturbation. The public reduced
tangent, opening, pressure sharing, force and moment balance, explicit
resource rejection and restart identity have focused tests in
`tests/test_general_contact_q4_s3_refined_patch.py`.

The opt-in two-control static test (`ANYSOLVER_LONG_CONTACT=1`) completed a
small corner closure in 124.59 s on the local host. Six source pressure nodes
were active, the conservative whole-face lower gap was approximately
−0.129 mm within the declared 5 mm **development** gap budget, and the
version-2 checkpoint was emitted. The test is skipped by default because of
its measured cost. The first whole-route probe, before reduced-coordinate
pair-local differentiation, was stopped after more than three minutes with
no terminal result. It is retained as an interrupted resource observation,
not a mechanics failure or a measured speed comparison.

The corner-closure example prescribes a source material node inside the fixed
target's overlap, 50 µm beyond the target skin. It therefore tests routing,
reaction balance and restart, but cannot serve as a mesh-converged zero-gap
augmented contact benchmark. A graded 2×2 source patch exposed persistent
multiplier updates at this imposed interference. A separate fixed-pose test
of the actual multi-Q4/S3 kernel matched independent Q1 support and weighted
gap integrals: refining a 4×4 source to 8×8 changed a weak-open corner into
one active pressure node. A feasible off-contact loading case is needed for
coupled pressure and enforcement convergence.

The ordinary nonlinear force route now admits the exact multi-Q4/S3 profile.
`examples/general_contact_refined_q4_s3_force.py` starts the source and target
skins in contact, clamps the source left edge, and loads two right-edge nodes
outside the overlap. At full load, one cutback produced accepted factors
0.25, 0.5, 0.75, 0.875 and 1.0. Six pressure nodes were active and the
conservative lower-gap magnitude was 26.2 µm under the explicit 50 µm
budget. Source/target force and moment balance was within 3×10⁻¹¹ in SI
units. The opt-in integrated regression passed in 137.66 s. This feasible
case supplies a development baseline for coupled refinement; one mesh and
one normal stiffness do not establish convergence or C1 acceptance.
An offline wheel from source `29dfa8d4` (SHA-256
`CBB5628888F5E94B5F9787AE6430D9B8BCBA4A4D3DF312BB6135A7241CA1512D`)
ran the same example from an isolated installation. The complete 623-byte
source and installed outputs were identical (SHA-256
`D559C85E4F3A8840F442DA14BAD066D6B211B384A80E5728C3EF714CD0F13E75`).
This verifies packaging for this development example only.
Ordinary augmented force and displacement histories now retain compact
per-increment gap, pressure activity and integrated wrench summaries. The
feasible force path's five records and checkpoint copy passed an integrated
test; an existing ordinary displacement path also passed after this change.
At 10× normal regularization the feasible two-Q4 case still met its gap
budget, but contact force changed by 22% and active pressure nodes changed
from six to two. The fixed 0.02 Pa multiplier-change threshold represented
about 20 µm of normalized weighted-gap change at 1000 N/m³ and 2 µm at
10000 N/m³, so the two cases do not isolate stiffness alone. A matched
0.002 Pa attempt at 1000 N/m³ was stopped after more than ten minutes
without a terminal result. Two-Q4/four-Q4 source-mesh responses at 1000 N/m³
differed by 0.068% in z-force and at most 0.263% in the dominant moments,
but this does not establish coupled convergence while enforcement changes
remain so large. Response convergence remains open.

This profile requires explicitly dimensioned Q4 area and weighted-gap
tolerances, triangle and energy-evaluation budgets, and augmented-pressure
controls. It does not admit penalty enforcement or the separate
`projected_matching` gap selector. Existing one-Q4 and refined-S3 profile
identities remain separate. The current public route has not been exercised
at the 361-source-node resolution used by the independent fixed-pose Q4/S3
pressure test; numerical pair-local Hessians are costly at that scale.

This is **implemented and locally tested development work**. An opt-in
two-step active split-restart case passed: all six pressure nodes were active
at the checkpoint, and the uninterrupted and resumed final checkpoints were
equal. It took 578.30 s on the local host. The first candidate checkpoint
at −0.0150 m was still open; that failed active-state gate is retained.
Coupled mesh/enforcement convergence, partial-contact pressure stability,
complete-route resource scaling, independent review,
and C1 acceptance remain open. The standalone
`examples/general_contact_refined_q4_s3_path.py` completed from both source
and an isolated wheel installation built from commit `2a76cd33`. The wheel
SHA-256 is
`C67027ECC86461E864B40DAAD0A67E89231A04EF0D222D75F8CAE4BF44D51F18`.
The installed import origin was asserted and the complete 600-byte source and
installed outputs were identical (SHA-256
`729FC7E0002613F0B3A1931C81E88F1B423F9B23292917C3A69908E15C84C49C`).
This checks packaging for that exact development case, not a supported release.
Raw results are retained under `C:/ANYworkspaceWork/general-contact-evidence`
with the `c1-multi-q4-*` and `c1-refined-q4-s3-*` prefixes.

## Tight-gap four-phase development path

`examples/general_contact_refined_q4_s3_tight_path.py` uses two connected
Q4 source faces against two nonmatching S3 V2D target faces. The source
bottom and offset target top skins begin 15 mm apart. A two-control path
presses by 15.01 mm, slides 50 mm while pressed, opens to the initial
normal separation and recontacts. Each segment uses two accepted steps.
The normal law is projected augmented, with an explicit 50 µm independent
gap budget (0.001 times shell thickness), 1000 Pa/m normal regularization
and 0.02 Pa pressure-update tolerance. All controls and supports are in
the example; no hidden rigid stabilization is added.

The eight-step development probe completed in 114.09 s. Six shared Q1
pressure nodes were active at press, both slide states and recontact.
The conservative lower gaps at the four phase endpoints were −15.716 µm,
−15.854 µm, +15 mm and −15.854 µm. Opening had zero contact force;
the terminal source normal contact force was 0.005229 N. Every accepted
step met the same 50 µm gap gate. Raw per-step values and the two earlier
failed approach probes are preserved in the evidence directory under
`c1-refined-path-*`.

The opt-in `tests/test_general_contact_refined_q4_s3_tight_path.py` runs
the uninterrupted path, splits after the slide, resumes from the version-2
checkpoint and compares final displacements, paired contact wrench,
normal multipliers and complete checkpoint. It passed 2/2 checks in
246.94 s with `ANY_RUN_C1_REFINED_TIGHT_PATH=1`. This is an implemented,
locally tested coupled path. Pressure-space stability on partial contact,
mesh/enforcement convergence, independent assessment and C1 engineering
acceptance remain open.

The source state at `5041e939e179f50b92f37a4512200ce035fcde36` built a
no-isolation wheel offline, then installed it without dependencies into
an isolated local target. The wheel SHA-256 is
`B833F1D19F422630210CE2429E0213639B4EF6A5CF39DD901A34B92910F33B7F`.
The example asserted its `anysolver` import origin for both source and
installed runs. Their complete 923-byte outputs matched byte for byte
(SHA-256 `ED04F5477C7E6448CC9D32FC816732D7792B3B402E9E0853DC00CBAA9FFEAC07`).
Build, installation, origin and run logs are retained in
`C:/ANYworkspaceWork/general-contact-evidence` with the
`wheel-5041e939` and `c1-refined-tight-example-*` names. This verifies
package routing for the narrow development example; no publication or
engineering acceptance is implied.

## Underresolved weak-open pose

A two-Q4/two-S3 fixed structural pose now reproduces a supported but
weak-open corner. Its actual overlap sample is −100 µm, beyond the
50 µm physical budget, while all six normalized weighted gaps are
positive, all numerical pressures are zero and the projected augmented
update changes no multiplier. The conservative whole-face lower bound is
−360 µm; the diagnosis requires the violating physical sample as well as
the bound, so bound looseness alone cannot trigger it. The coupled path
reports `contact_pressure_space_underresolved` if it equilibrates at such
a pose. Earlier swept-path admission can still stop a trial before an
equilibrated pose is available, with its separate gap failure reason.
An injected failure at the path transaction boundary returned no accepted
step or checkpoint, and the resolved two-step press retained its prior
force and gap values. Four focused checks passed; the injected check
verifies rollback and reporting, while the physical fixed-pose check
verifies the classification conditions.

This diagnostic preserves the primal Q1 pressure space, the 50 µm gate
and restart format. It does not repair the unresolved corner or establish
pressure-space stability. The fixed-pose focused checks are in
`tests/test_general_contact_q4_s3_refined_patch.py`; raw values and the
reporter correction are retained as `c1-refined-weak-open-pose-*.txt`.

# C1 development profile: multiple Q4 pressure faces against S3

`Q4_S3_PATCH_REFINED_NODAL_PRIMAL_MORTAR_AUGMENTED_STATIC_DEV_V0`
admits a conforming source patch of at least two qualified Q4 faces against an
explicit S3 V2D target patch. Source Q1 pressure nodes are shared by material
node identity. The projected augmented normal law uses the same physical Q4
skin and S3 side/offset work maps as the one-Q4 route. Pair-local weighted-gap
and support derivatives assemble into the shared pressure space. The complete
residual is retained for both-body reactions; the tangent evaluates only
physical coordinates reached by the solver's reduced unknowns.

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

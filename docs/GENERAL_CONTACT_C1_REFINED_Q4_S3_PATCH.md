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

# GE-B3 reference-factor spectrum correction — 2026-09-07

Baseline `cc2f50c5d50e3467a26d71e1d7276f06412ac4dc`, tree
`86c3993c075905000c533cac8006668a5597276c`. This adds two private modules,
a numerical probe and tests. No existing source, mechanics, section law,
quadrature, tolerance, state schema, selector, default or old evidence changes.
It is development evidence, not independent review or qualification.

## Genuine diagnostic failure

Three one-macro, 24-coordinate straight reference problems used L=2,
h=2/slenderness, EA=12/h^2, shear=(5/6)*EA/2.6, bending stiffness1 in
both planes, line mass1, bending rotary inertia h^2/12. Torsion stiffness2
and axial rotary inertia h^2/6 are explicit diagnostic choices, not a claim
of a calibrated square-section Saint-Venant constant. Slendernesses were
100, 10,000 and 1,000,000. These are tiny correctness checks, not a large
mesh, timing benchmark or qualification campaign.

The initial suite had **two failures and one pass in 1.62 seconds**.
At 10,000 the dense signed pencil returned first bending squared frequency
0.9762482577773519 instead of the retained-factor value near
0.7346938662, a frequency difference of about 15.27%. Its normalized
global backward residual was only 1.40e-13. That residual did not establish
low-eigenvalue forward accuracy. At 1,000,000 it raised
`stationary full-pencil eigenpair residual failed` before creating a raw
comparison record. That absent record has not been fabricated. The two
existing raw records, failed test source and failed probe source are preserved.

The failure is in numerical extraction from this reference pencil, not a
reclassification of earlier beam or shell evidence. No formal request was
consumed. No failed process was automatically retried.

## Numerical successor and native boundary

`_native_reference_factor_spectrum.py` retains both factors throughout:

1. Global QR of the exactly massless trace columns supplies their equilibrium
   map without forming a Schur difference of large stiffness matrices.
2. QR of the mapped kinetic rows gives a mass-whitening triangular factor.
3. SVD (`GESVD`) of the whitened strain rows extracts singular values before
   squaring, instead of extracting tiny eigenvalues from normal equations.

Arrays are owned and immutable, rank usability and finite-value checks fail
closed, and full factor residual/mass orthogonality retain the 1e-11 target.
Cancellation is checked. No numerical inertia, clipping, inertial-cell
condensation, empirical coefficients or stiffness regularization is introduced.
The generic kernel represents positive-semidefinite REFERENCE energy only.
It cannot independently establish the physical origin of supplied factors.

`_ge_beam3_virgin_reference_modes.py` supplies that native boundary: it requires
exactly fresh V4 states and zero total displacement, captures native model and
inertia ownership with the existing guards, builds factors, and verifies their
consistency with the native reference pencil. Loaded, displaced, post-commit
and history-bearing states are not silently routed into this solver. The
preserved signed prestressed solver is unchanged and its negative modes remain
intact. Neither new API is publicly exported or selected by an existing alias.

## Checks and limitations

An independently reconstructed rational **discrete** thin-limit check sets
the two unit-cell rotations equal to their transverse slopes and condenses
the two free nodal traces from the endpoint-moment complementary potential.
The resulting matrices in mid/tip translation coordinates are

`K=[[96/7,-30/7],[-30/7,12/7]], M=[[2/3,1/6],[1/6,1/3]]`.

Their exact squared eigenvalues are 36/49 and36 in each bending plane.
This is not the continuum Euler spectrum: a one-macro discretization remains
coarse. All three slenderness samples pass the frozen 2% frequency comparison
with this asymptotic discrete reference. The moderate-slenderness comparison
also agrees with the dense path. The actual native virgin adapter reproduces
the factor improvement, preserves input states, rejects nonvirgin inputs,
detects model mutation and preserves the six free-body modes for the moderate
curved/coupled fixture. A proper coordinate rotation also passes there.

The new kernel initially passed 16 checks in 1.51 seconds; native integration
passed 24 in 6.25 seconds. The final suite passed **51 tests in 62.32 seconds**:
12 kernel, four slender-diagnostic, ten native-adapter, 23 unchanged loaded-modal
and two prior engineering checks. Those last two exercise all five frozen
straight prestress cases from the preceding checkpoint.
The separate static suite passed 17 checks in 0.37 seconds: six new,
six prior straight-prestress and five prior loaded-modal checks.

Two executions produced byte-identical numerical comparison records and native
reference records (six pairs). At slenderness 1,000,000 the first bending
squared frequencies are approximately 0.7346933362 and 0.7347786383. The
factor approach materially improves accuracy, but that small artificial split
still exceeds the 1e-11 invariant target. We do NOT infer extreme-contrast
covariance, rank/coercivity, general locking freedom or full qualification from
the 2% engineering check or small backward residual. Ordinary SVD still has
absolute-accuracy limitations. [LAPACK's relative-accuracy discussion](https://netlib.org/lapack/explore-html/d6/d22/dgejsv_8f_source.html)
informs the next numerical investigation; no Jacobi driver or its truncation
options were adopted in this checkpoint.

## Preservation and next work

All 19 selected files (11,201 bytes), including the failed sources and available
raw failure diagnostics, were archived exclusively and byte/hash verified:

`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-reference-factor-spectrum-20260907-dd98fb29ba34`

The canonical inventory binds all six implementation/test source files and
the repeated outputs in
`docs/reference_cases/ge_beam3_reference_factor_spectrum_evidence.json`.
Only verified relay duplicates are removed; original temporary outputs and
historical archives remain. The old failed third raw record remains absent.

Independent review remains PENDING. Installed-wheel validation of these new
modules, stronger relative accuracy, prestressed high-contrast conditioning,
broader straight/curved engineering qualification, general nonlinear-section
parity and objective beam-shell connections remain open. This is not a public
release, default activation, buckling-factor authorization or completion claim.

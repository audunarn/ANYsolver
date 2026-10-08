# C1 shallow Q4/S3 patch handoff candidate

`examples/general_contact_q4_s3_tight_path.py` exercises one planar Q4
source face against two nonmatching S3 V2D target faces through the ordinary
nonlinear static contact path. The physical source bottom and target top skins
include their distinct 50 mm thickness and S3 reference-surface offset.
The path presses, slides 50 mm, opens and recontacts. It uses explicitly
selected primal-mortar penalty contact, a 1000 Pa/m normal regularization,
a 2 µm numerical difference step and an explicit 50 µm independent physical
gap budget (`10^-3` times the shell thickness). These are case settings, not
universal recommended defaults.

A bounded exploratory run of the same mechanics completed all four phases.
The maximum recorded penetration was 32.6 µm, below the 50 µm gate.
All four Q4 source pressure nodes were active during press, slide and
recontact; the open phase had zero active pressure and zero normal force.
Integrated normal forces were approximately 0.01167 N at press and 0.01130 N
at slide/recontact. The model reported a version-2 contact checkpoint.
Raw phase output is retained at
`C:/ANYworkspaceWork/general-contact-evidence/c1-q4-s3-tight-first.txt`.

The opt-in coupled test
`tests/test_general_contact_q4_s3_tight_path.py` ran one-shot and split
continuations through the four-phase path. It passed in 455.89 s on the local
host. The resumed final displacement agreed within `rtol=1e-7, atol=1e-9`;
integrated contact force agreed within `rtol=1e-6, atol=1e-8 N`.
The raw test output is retained at
`C:/ANYworkspaceWork/general-contact-evidence/c1-q4-s3-tight-restart-first.txt`.
The long test is opt-in with `ANY_RUN_C1_TIGHT_PATH=1`; the default suite
checks the case declaration and reports the long test as skipped.

From clean source commit `04a66553`, an offline no-isolation wheel was built
and installed without dependencies into an isolated target. The wheel SHA-256
is `3e22075d21d8d58d9dd5e9d822bb3e646320445305e27148f26713678cb1b687`.
The example ran through explicit source and installed import paths; the
complete 1,070-byte outputs matched byte for byte, with SHA-256
`66c427824dd619c03c8ac798eec403e8fbb30a4fd06f8c88f680040dbf994ca0`.
Build, install, import-origin and run logs are in
`C:/ANYworkspaceWork/general-contact-evidence` with the `04a66553` suffix.
The wheel was not published.

This is a **development handoff candidate for the stated shallow, guided
path**. It does not resolve the retained weak-open counterexample, prove
pressure-space stability or admit arbitrary partial contact and finite
sliding. General C1 acceptance still requires the registered mesh,
enforcement and integration refinement, independent review, verification of
the final qualified installed profile and a supported capability decision.

## Independent Q4 pressure-resolution control

`tests/test_general_contact_q4_s3_corner_pressure.py` evaluates a square Q4
source patch against two S3 target faces at a fixed pose. The prescribed
affine gap is (g(x,y)=-0.0001+0.001(x+y)) m. Its physical minimum is
−0.1 mm at the corner, so a 0.05 mm independent gap budget must reject the
coarse state. For a uniform Q4 cell of width (h), direct integration of the
corner Q1 pressure basis gives normalized weighted gap
(-0.0001+2(0.001)h/3) m. The independent pointwise penalty reaction at
1 MPa/m is (1/6) N.

| Q4 divisions per edge | Corner weighted gap | Active pressure nodes | Integrated reaction |
|---:|---:|---:|---:|
| 1 | +0.567 mm | 0 | 0 N |
| 4 | +0.0667 mm | 0 | 0 N |
| 8 | −0.0167 mm | 1 | 0.0651 N |
| 12 | −0.0444 mm | 1 | 0.0772 N |
| 16 | −0.0583 mm | 3 | 0.1221 N |

The measured corner gaps match the independent basis integral. Every mesh
has full reported pressure-gradient rank, including the two meshes that miss
the corner contact entirely. Refinement recovers activity and moves the
integrated reaction toward (1/6) N, but the 16-division response remains
about 27% low. Full rank and a passing shallow guided path therefore do not
establish pressure resolution for localized partial contact. The raw probe is
`C:/ANYworkspaceWork/general-contact-evidence/c1-q4-s3-corner-pressure-probe-refined.txt`;
the focused test output is `c1-q4-s3-corner-pressure-focused-first.txt` in the
same evidence directory. Uniform refinement through 16 divisions has not
resolved this localized response to the prospective 2% level.

A nonuniform Q4 mesh with 16 cells from 0 to 0.1 m in each direction,
followed by cells to 0.2 and 1 m, concentrates pressure resolution around
the active corner. Its 361 source pressure nodes and 648 face candidates
produce 0.165731 N and ±0.00415107 N m. The independent affine pointwise
references are 1/6 N and ±1/240 N m, giving 0.562% force error and 0.374%
moment error. Independent tensor-Q1 cell integrals match every reported
support and weighted gap; an independently assembled Q1 Gram matrix maps
the pressure coefficients to the production nodal reactions within the
focused test tolerance. The Gram matrix is positive definite. The reported
pressure-gradient condition is about (1.09\times10^5), so full rank alone
is not a mesh-independent stability result.

This passes the prospective 2% integrated response target for **one fixed
pose** after targeted mesh refinement. It does not establish convergence
under further refinement, gap enforcement in a coupled solve, pressure-space
stability across partial contact, a complete-route resource budget or
independent C1 acceptance. The registered test is
`tests/test_general_contact_q4_s3_corner_pressure.py`; retained outputs are
`c1-q4-s3-graded-pressure-moment-first.txt` and
`c1-q4-s3-graded-gram-first.txt` in the evidence directory.

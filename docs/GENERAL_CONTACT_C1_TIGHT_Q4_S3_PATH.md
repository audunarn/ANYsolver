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

This is a **development handoff candidate for the stated shallow, guided
path**. It does not resolve the retained weak-open counterexample, prove
pressure-space stability or admit arbitrary partial contact and finite
sliding. General C1 acceptance still requires the registered mesh,
enforcement and integration refinement, independent review, installed
artifact verification and supported capability decision.

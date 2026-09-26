# C1 development: mixed force and displacement shell-contact path

`ContactPathNodalForce` adds explicit translation-force values, in newtons,
at a `ContactPathProgram`'s waypoints. Force values and displacement targets
interpolate at the same accepted path steps. A segment may change force
while its displacement controls remain fixed. All force histories begin at
zero, use unique physical node/DOF identities, and are bound into the
version-2 contact-path restart contract. Programs without forces retain
their previous contract and history shapes.

At each Newton candidate the reduced equilibrium residual includes the
current external nodal force. Accepted support reactions subtract that
force from the complete internal/contact residual. The history records
nodal force values and a **trapezoidal approximation** to their incremental
work; this is a path diagnostic, not an exact nonlinear energy integral.
No structural or contact state commits until the complete equilibrium,
augmentation and physical-gap checks pass.

`examples/general_contact_refined_q4_s3_mixed_path.py` starts two connected
Q4 source faces 40 µm above two nonmatching physical S3 V2D target faces.
The target is fixed, the source's left edge has z supports, and two left
source x coordinates are prescribed. A force of −0.05 N on each right-edge
node presses the source; the x controls then slide it 50 mm. Unloading to
zero gives a positive 40 µm gap and zero contact force. Reloading restores
contact. There is no prescribed normal overlap or hidden stabilizing
spring. The normal law remains the declared projected augmented Q1 mortar
profile with a 50 µm independent gap budget.

The first 5 mm-gap probe stayed open under 0.1 N total load, as its
measured deflection was only about 56 µm. That result is retained as
`c1-mixed-path-press-first.txt`. With the declared 40 µm initial gap,
the eight-step path completed in 67.66 s (`c1-mixed-path-four-phase-first.txt`).
At the four phase endpoints its active pressure count was 2, 2, 0, 2;
conservative lower gaps were −15.736 µm, −12.811 µm, +40 µm and
−12.811 µm. The source normal contact forces were 0.001067 N,
0.000609 N, 0 and 0.000609 N. Every accepted step met the same 50 µm
physical-gap budget. The source example completed with the same phases
(`c1-mixed-path-example-source-first.txt`).

The opt-in `tests/test_general_contact_mixed_path.py` checks stage
interpolation, legacy contract identity, per-step paired force/moment,
external-versus-support vertical balance, work signs, exact split-restart
checkpoint replay and rejection of a changed force history. It passed
3/3 in 160.95 s with `ANY_RUN_C1_MIXED_PATH=1`
(`c1-mixed-path-full-split-first.txt`). The previous displacement-only
two-step press retained its exact gap and force outputs
(`c1-mixed-path-no-load-press-regression-first.txt`).

This is implemented, locally tested development work. The contact
pressure space still needs partial-contact stability and coupled
mesh/enforcement convergence. The local test does not provide independent
engineering acceptance, and application integration remains open.

Clean source `f466eec2ec110554e98d680ee7a9274155249327` built an offline no-isolation wheel, installed it
without dependencies into an isolated target, and asserted that `anysolver`
was imported from that target. The wheel SHA-256 is
`6CA3D97EF99D4557A5FF84178ABD3A8D417045800854456ABF5F87BA1FE1CE45`.
The complete 1,003-byte source and installed example outputs were
byte-identical (SHA-256
`CF90DB1E471A42885FFE1484A555606FE06C67982281D064ABA9A8593115DDBB`).
The build, install, import-origin and run logs are retained under
`C:/ANYworkspaceWork/general-contact-evidence` with
`wheel-f466eec2-*` and `c1-mixed-path-example-*` names. The wheel was
not published; this checks package routing for this development case.

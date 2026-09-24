# General-contact capability ledger

This ledger reports the new opt-in subsystem only. The historical rigid-sphere
impact API has a separate contract. Status terms are deliberately distinct:
**implemented**, **locally tested**, **independently accepted**, and
**released**. A local passing test does not confer engineering acceptance.

| Profile and geometry | Analysis and lifecycle | Status | Evidence and dependency |
|---|---|---|---|
| Planar qualified E4-PL Q4 skin against one fixed rigid plane; midsurface/top/bottom; frictionless penalty mortar | Nonlinear static force or displacement control; version-2 penalty checkpoint under von Karman kinematics | Implemented, locally tested | `tests/test_general_contact_plane.py`, `examples/general_contact_planar_plate.py`; corotational restart, independent review and registered numerical qualification open |
| Planar S3 V2D physical skin against one fixed rigid plane; S3 reference-surface offset and P1 pressure | Von Karman nonlinear static force/displacement control; state-free version-2 checkpoint | Implemented, locally tested exploratory slice | `tests/test_general_contact_s3_plane.py`, `examples/general_contact_s3_plane.py`; see [S3 plane limits](GENERAL_CONTACT_C1_S3_PLANE.md) |
| Explicit planar Q4/S3 pair with fixed projected overlap; physical midsurface/top/bottom and S3 reference offset; guided uniform normal translation only | Von Karman nonlinear static force/displacement control and frictionless penalty; version-2 checkpoint for state-free penalty | Implemented, locally tested exploratory slice | Q4/Q4 force/displacement and restart, S3/Q4 force and restart; Q4/S3 and S3/S3 local force maps in `tests/test_general_contact_pair.py`; see [guided pair limits](GENERAL_CONTACT_C1_GUIDED_PAIR.md) |
| One planar Q4/S3 face per side with projected overlap, uniform facewise tangential translation, nodal normal displacement and fixed actual rotations; physical offset couples | Explicitly selected von Karman nonlinear static penalty route, force/displacement controls and version-2 checkpoint | Implemented, locally tested development profile; C1 still open | Q4/Q4 coupled press, lateral displacement and restart; S3/Q4 coupled press; independent quadratic/subdivision gap controls. Q4/S3 partial-contact 10 µm gate failed under stiffness refinement. See [restricted sliding limits](GENERAL_CONTACT_C1_RESTRICTED_SLIDING.md) |
| Explicit planar Q4/S3 patches with shared integration-side nodal pressure support across multiple faces; restricted bodywide tangential translation and nodal normal displacement | Explicitly selected von Karman nonlinear static penalty route, force/displacement controls and version-2 checkpoint | Implemented, locally tested development profile; C1 still open | Q4 against two Q4 target faces: coupled press, lateral drive and restart; Q4 against two S3 target faces: coupled press; two S3 integration faces: local force/rank only. See [patch sliding limits](GENERAL_CONTACT_C1_PATCH_SLIDING.md) |
| Q4/S3 shell pairs, nonmatching overlap, finite sliding, augmented normal law, analytic obstacles | Nonlinear static and restart | Open | C1; paired-shell formulation and state work required |
| B2/B3 round centreline tubes | Static frictionless contact | Open | C2 |
| Straight/curved native B3-GE contact with retained internal coordinates | Native static owner | Open | C3 |
| Automatic pairing, triangulated obstacles, boundaries and self-contact | Static | Open | C4 |
| Coulomb friction, swept beam sections, nonlinear material combinations, arc length | Static and history | Open | C5 |
| Shell/classical-beam impact and free rigid bodies | Transient Newmark profile | Open | C6 |
| Native finite-velocity B3-GE | Contact-free Lie-group midpoint profile | Open | C7 |
| Native and coupled impact | Common-stage transient contact | Open | C8; requires C7 |
| ANYfem/ANYstructure adapters, representative workflows and scale evidence | Installed applications | Open | C9 |

The working branch is `codex/general-contact-core`, started from ANYsolver
`be41a77a62e1cd7e1767bda6e955253af0819f91`. C0 was committed as
`31e60277`. A disposable C0 candidate wheel built from that commit as
`anysolver-0.4.7-py3-none-any.whl` (SHA-256
`1d192e7b13171465928eac9156ece96bbedb4bcc1a0c895611594543c1980f66`)
and its isolated installed copy ran the guided-plate example with the expected
0.4 N reaction. The focused and legacy regression outputs are retained in
`C:\ANYworkspaceWork\general-contact-evidence\restart6.txt` and
`C:\ANYworkspaceWork\general-contact-evidence\regression5.txt`. This is a
packaging smoke check, not release qualification.

Unsupported contact combinations fail in validation or solver preflight.
The exact admitted C0 profile and its limitations are in
[GENERAL_CONTACT_C0.md](GENERAL_CONTACT_C0.md).

The current restricted sliding development candidate at source `93c22002` was built
and run from an isolated installed wheel (SHA-256
`a726f4731db41705efa6315f780aafe7ffd1f670d422494f18e78544fc0d5359`).
The installed example output is retained at
`C:\ANYworkspaceWork\general-contact-evidence\c1-quadratic-example-installed.txt`.
This smoke check does not promote any C1 row to independent acceptance or release.

The multi-face patch candidate at source `1ab13962` passed 81 affected local
tests, then ran its lateral example from an isolated installed wheel (SHA-256
`c02feb2ae8490db23cf6c0680d4f9f8ec5fdf2e7275378eddc57a3e04e064fd3`).
The test and package outputs are retained under
`C:\ANYworkspaceWork\general-contact-evidence` as
`c1-patch-regression2.txt`, `wheel-1ab13962-build.txt`,
`wheel-1ab13962-install.txt` and `c1-patch-example-installed.txt`.
This remains local development and package smoke evidence.

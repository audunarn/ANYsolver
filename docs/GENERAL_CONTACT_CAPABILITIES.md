# General-contact capability ledger

This ledger reports the new opt-in subsystem only. The historical rigid-sphere
impact API has a separate contract. Status terms are deliberately distinct:
**implemented**, **locally tested**, **independently accepted**, and
**released**. A local passing test does not confer engineering acceptance.

| Profile and geometry | Analysis and lifecycle | Status | Evidence and dependency |
|---|---|---|---|
| Planar qualified E4-PL Q4 skin against one fixed rigid plane; midsurface/top/bottom; frictionless penalty mortar | Nonlinear static force or displacement control; version-2 penalty checkpoint under von Karman kinematics | Implemented, locally tested | `tests/test_general_contact_plane.py`, `examples/general_contact_planar_plate.py`; corotational restart, independent review and registered numerical qualification open |
| Explicit planar Q4/S3 pair with fixed projected overlap; physical midsurface/top/bottom and S3 reference offset; guided uniform normal translation only | Von Karman nonlinear static force/displacement control and frictionless penalty; version-2 checkpoint for state-free penalty | Implemented, locally tested exploratory slice | Q4/Q4 force/displacement and restart, S3/Q4 force and restart; Q4/S3 and S3/S3 local force maps in `tests/test_general_contact_pair.py`; see [guided pair limits](GENERAL_CONTACT_C1_GUIDED_PAIR.md) |
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

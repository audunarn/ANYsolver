# C1 development profile: projected augmented normal contact

`PLANAR_Q4_S3_MULTI_CONTROL_AUGMENTED_PATH_DEV_V0` extends the restricted
multi-face Q4/S3 static path with a projected augmented normal law. Select
`ContactInteraction(normal_law="augmented", normal_stiffness=..., gap_tolerance=...)`,
set a dimensional `ContactSolverSettings.pressure_tolerance`, and pass the
`ContactPathProgram` through `solve_static_nonlinear`.
`validate_general_contact` reports the distinct augmented patch capability
profile before analysis ownership is selected.

The integration-side P1/Q1 nodal pressure space has stable material-node
identities. For positive separation gap (g), fixed multiplier estimate
\(\lambda\), and pressure-per-length regularization \(\epsilon\), the inner
equilibrium uses \(p=\max(0,\lambda-\epsilon g)\). The outer iteration projects
\(\lambda^+=\max(0,\lambda-\epsilon g)\) on supported pressure nodes and
sets it to zero where overlap has disappeared. Inner iterations evaluate
material candidates from the same committed origin. Material state commits
only after force equilibrium, prescribed-control consistency, independent
gap certification and the explicit pressure-change tolerance all pass.

The pressure tolerance is in pressure units; the gap tolerance is in length
units. `maximum_augmentations` bounds work and reports failure when exhausted.
The checkpoint binds the law, both tolerances, the augmentation limit, the
path and the pressure-node multiplier estimate. Only this contact path owner
admits the augmented law. Penalty analyses retain their existing contract.

The admitted geometry and materials are the same planar, fixed-rotation,
elastic, frictionless multi-face shell profile as the penalty path. The
augmented law does not make a kinematically forced penetration feasible:
a prescribed average downward motion across a fully supported contacting
patch exhausted its bounded augmentation sequence in the exploratory
`c1-augmented-press1.txt` and `c1-augmented-press2.txt` evidence. The
corner-driven case has a deformable contact region and completed with active
pressure, nonzero reaction and split/restart agreement. Neither case is an
independent engineering acceptance.

Run `python examples/general_contact_mixed_path.py --augmented` for the
corner-driven demonstration. Focused checks are in
`tests/test_general_contact_patch_mortar.py` and
`tests/test_general_contact_patch_sliding.py`. Warped shells, rotations,
general finite sliding, friction, automatic pairing and dynamics remain open.

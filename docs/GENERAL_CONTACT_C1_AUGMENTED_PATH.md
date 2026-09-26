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
pressure, nonzero reaction and split/restart agreement. A four-phase
corner-driven Q4/two-S3 path now presses, slides 0.1 m, opens and recontacts.
The open phase has a positive 1 µm independent gap, zero contact force and
zero multiplier norm; restarting from that phase reproduces the final
displacement and contact reaction. Its focused source check is
`c1-augmented-four-phase-restart-final1.txt`. These remain development results,
not independent engineering acceptance.

Run `python examples/general_contact_mixed_path.py --augmented` for the
corner-driven press demonstration, or use `--augmented-cycle` for the full
four-phase path with integrated contact forces, generalized control reactions,
gap diagnostics and checkpoint output. Focused checks are in
`tests/test_general_contact_patch_mortar.py` and
`tests/test_general_contact_patch_sliding.py`. Warped shells, rotations,
general finite sliding, friction, automatic pairing and dynamics remain open.

An isolated wheel from source `55d94daeb1f629067b1b0a111734f13b5999de34`
(SHA-256 `5c38a199e03a26263a3925a97d2aeb66983c5d2ebfd3e983dfdd630f83d4cc45`)
imported from its installation target and completed the `--augmented-cycle`
example with four accepted phases (`c1-augmented-four-phase-example-installed-55d94dae.txt`).
No package was published. This checks the installed workflow, not engineering
acceptance.

## Optional active-set secant predictor

`ContactSolverSettings(augmentation_acceleration="active_secant")` enables a
development-only predictor for the outer augmented iteration. The default
remains `"none"`, and penalty contact rejects the option. Within one physical
increment, the predictor fits the residual of the projected multiplier map
on an unchanged active set of at most four pressure nodes. It requires more
samples than active unknowns, a well-conditioned fit with a small residual,
positive predicted pressures and a bounded step. A failed safeguard uses the
ordinary projected update. After any prediction, the solver re-equilibrates
and applies the original pressure-update tolerance and independently checked
physical-gap tolerance. A prediction never commits material or contact state.
The option is bound into contact-path restart identity; changing it rejects a
checkpoint. The default no-acceleration restart contract is unchanged.

The two-Q4/two-S3 mixed force path exposed a slow projected multiplier mode:
the two-active-node secant map fitted from a failed 16-update run had
eigenvalues 0.63276 and 0.97732. With the same 10000 Pa/m regularization,
0.0002 Pa update tolerance and 16-update cap, the optional predictor completed
the press in five augmentations (one prediction), with final update
1.72×10⁻¹⁰ Pa and conservative lower gap −7.452 µm. The unaccelerated case
stopped at its cap. The strict eight-step press, slide, open and recontact
cycle completed; a split after step four reproduced its accepted history and
changing the acceleration option was rejected on restart. Retained outputs
are `c1-mixed-active-secant-first.txt`,
`c1-mixed-active-secant-cycle-first.txt`, and
`c1-mixed-active-secant-restart-first.txt` under
`C:/ANYworkspaceWork/general-contact-evidence`. A maintained opt-in test uses
`ANY_RUN_C1_ACTIVE_SECANT=1` in
`tests/test_general_contact_mixed_path.py`.

These are developmental solver results. The predictor does not repair an
underresolved pressure space or qualify mesh, integration, enforcement or
engineering response convergence. The full C1 and programme gates remain
open.

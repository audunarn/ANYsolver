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

## Refined Q4/S3 active-set pivot (development)

The refined augmented Q4/S3 shell patch also admits the explicit
`augmentation_acceleration="active_secant_pivot"` option. It requires
`augmentation_pivot_max_pressure_pa` and
`augmentation_pivot_difference_step_m`. Both are positive dimensional bounds;
there is no automatic choice. Set `maximum_augmentations` to at least 15 so
the single pivot trial leaves enough iterations for verification and the
subsequent secant fit. The option retains the active secant predictor.

After a fixed-multiplier equilibrium, one guarded attempt forms the constrained
structural/contact Schur response of two to four active pressure nodes. It
enumerates nonnegative complementarity subsets and proposes a pivot only when
one subset is locally feasible, its pressure is below the stated cap, and the
geometry derivative has unchanged overlap topology. The attempt is bounded by
the existing geometry-evaluation budget. The solver then re-equilibrates the
proposal, checks the active set, independent physical gap and improvement in
the projected pressure change, and resets the secant history. A rejected
nonlinear proposal restores the structural and control iterate and resumes
ordinary projected updates. Failure to form the geometry or constrained solve
is reported explicitly. No pivot state is committed before the original
augmented acceptance tests pass.

In a developmental eight-Q4/two-S3 strict press, with a 20 Pa pivot cap,
0.1 µm difference step, 16 augmentation limit, 0.0002 Pa pressure tolerance
and 50 µm gap budget, the public path accepted the press at augmentation 15.
One pivot and one subsequent secant proposal were applied; the final pressure
change was 1.08×10⁻⁶ Pa and the independent lower gap was −0.500 µm.
A checkpoint after the open step reproduced the same contact state on resume.
With a 2.5 Pa cap, the candidate was declined; the unchanged 16-update limit
then stopped the press and retained only the previously accepted open step.
The earlier unaccelerated and active-secant-only failures remain valid evidence.
Development outputs are `c1-eight-q4-production-pivot-first.txt` and
`c1-eight-q4-production-pivot-restart.txt`, with the declined-cap control in
`c1-eight-q4-production-pivot-low-cap.txt`, under
`C:/ANYworkspaceWork/general-contact-evidence`. This is neither mesh
convergence nor independent engineering acceptance.
The runnable source example is
`examples/general_contact_refined_q4_s3_eight_q4_press.py`; installed-package
verification of this option remains open.

## Opt-in roundoff support for multiplier transfer

`augmentation_support_resolution="roundoff"` is a separate developmental
profile for refined Q4/S3 augmented contact. It requires an explicit
`augmentation_support_force_budget_n`; the default remains `"exact"`.
The fixed-multiplier contact residual and tangent retain all represented
overlap work. Only the outer augmented update treats a pressure node as
algorithmically unresolved when its positive reference support is at or
below machine epsilon times the patch's total reference support. Before
resetting that node's multiplier, the solver directly compares the local
contact residual for the ordinary projected update and the reset update.
Exceeding the stated force budget stops the increment explicitly. Results
report the support floor, affected material node IDs and reset force changes.
The option is part of the restart contract and has its own profile identity.

This rule addressed a known first sliding step in the eight-Q4/two-S3 case:
two departing edge pressure nodes had supports around 8×10⁻¹⁹ m² and
retained multipliers of roughly 9 and 18 Pa while their contact-force
contribution was near numerical resolution. The exact-support run stopped
after 16 augmentations. With a 10⁻⁸ N reset budget and all other gates held
fixed, the opt-in run accepted step 3 after 13 augmentations, with a
−2.186 µm independent lower gap and 4.48×10⁻⁹ Pa final pressure change.
Its largest reset force difference was 3.21×10⁻⁹ N. The accepted press
state was identical before sliding. Raw development output is
`c1-eight-q4-first-slide-roundoff.txt` under
`C:/ANYworkspaceWork/general-contact-evidence`. This known case does not
qualify the method across meshes, overlap transitions or installed packages.
The source example reproduces the bounded first-slide profile with
`python examples/general_contact_refined_q4_s3_eight_q4_press.py --first-slide --roundoff-support`.

The eight-Q4/two-S3 continuation also completed its second 25 mm slide under
the same settings after fixing adaptive Q4 overlap integration. Clipping had
produced one tiny fan triangle whose area-scaled error allowance was below
floating-point quadrature noise; equal root-fan shares preserve the declared
global area and weighted-gap budgets. At the accepted 50 mm position, the
independent lower gap was −1.832 µm and two pressure nodes were active.
Complete unloading at that position opened to +40 µm with zero force and
exactly zero stored normal multipliers. Raw development output and accepted
restart checkpoints are under `C:/ANYworkspaceWork/general-contact-evidence`
as `c1-eight-q4-second-slide-fanfix.txt` and `c1-eight-q4-open-zero.txt`.

Reloading from that open checkpoint accepted the half-load step, then stopped
at the declared 16-augmentation limit on final recontact. Its gap stayed
within the 50 µm budget, but the pressure update was 0.01575 Pa against the
0.0002 Pa criterion. The guarded smooth pivot declined across a projection
signature change. Disposable collinear predictors reduced the update to about
0.0016 Pa without meeting the unchanged gate. These probes were not added to
the solver. The failed source-bound traces are
`c1-eight-q4-recontact.txt` and
`c1-eight-q4-recontact-aitken-two-probe.txt`. This refined eight-Q4 path is
therefore a completed-step development subset, not a completed C1 handoff or
engineering qualification.

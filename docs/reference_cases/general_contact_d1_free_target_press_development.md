# Deformable-target Q4/S3 press: bounded development

An eight-Q4 source with distributed 0.3 N full load was pressed in three
increments against the two-S3 target. Target nodes 51 and 54 were fully
clamped and nodes 52 and 53 were free. The ordinary nonlinear static route
used the existing 1e−5 Pa multiplier tolerance, 50 µm gap tolerance and
seven-augmentation limit.

The first [raw development run](../../reports/general_contact_d1_free_target_8q4_press_dev_20260927.json)
(SHA256 `fa38d8c51fb38b415caf464c7ba31ec05a817c9167a5ae61b165c2a553ad8a07`)
accepted the opening step and stopped at the next contact step with
`maximum_augmentations_reached`. At that step the independent gap was
−0.334 µm, within tolerance; scaled pressure rank was 18/18 supported
modes, with two active modes. The final multiplier change was
3.265e−5 Pa, above the unchanged 1e−5 Pa criterion. Two supported-Schur
proposals predicted zero residual on the active modes, but subsequent
equilibration reduced the actual projected residual by only 0% and 7%,
below the required 25% reduction. They were rejected as
`nonlinear_verification`; no proposal was silently accepted. The pressure
Gram condition was about 10.94 after scaling.

The governing question is whether one bounded relinearization after the
nonlinear verification failure improves the pressure response without
changing mechanical inputs, tolerances or augmentation count. A separate
development run may set `augmentation_schur_maximum_relinearizations=1`;
it must report its actual proposal, re-equilibration and accepted-step
trace. A failure does not justify automatically increasing the limit.

The [one-relinearization run](../../reports/general_contact_d1_free_target_8q4_press_relinearize1_dev_20260927.json)
(SHA256 `8d52e516052de8b6ff7c5eb7d56c4e5a9f3923ccda1718b77288c33990ea7d3d`)
again accepted only the opening step and stopped at the same contact step
with the same 3.265e−5 Pa final change. It formed one correction, but the
subsequent re-equilibration rejected it as `nonlinear_verification`;
neither supported-Schur proposal was accepted. This falsifies the simple
stale-linearization remedy for this path. The next bounded distinction is
path resolution: use six rather than three force increments with the same
full load, geometry, seven-augmentation limit and pressure/gap criteria.
If activation still fails, inspect the coupled active-pressure response
instead of automatically increasing budgets.

The [six-increment run](../../reports/general_contact_d1_free_target_8q4_press_6steps_dev_20260927.json)
(SHA256 `9ae4d8eae8e9c74e88f3319e98531fba30a2c326a085aac313f7936ebf2ef7f1`)
accepted two opening steps and stopped at first contact (step 3). Its
final pressure change was 2.521e−5 Pa, still above 1e−5 Pa; gap was
−0.0371 µm, pressure rank 18/18, two active modes and both Schur proposals
were rejected. Halving the load increment did not remove the convergence
failure. The next investigation should compare the **predicted equilibrated
gap response** with a genuinely re-equilibrated small pressure perturbation
on this specific two-mode branch. This distinguishes a response-map error
from large-step nonlinearity or the safeguard's 25% merit requirement.

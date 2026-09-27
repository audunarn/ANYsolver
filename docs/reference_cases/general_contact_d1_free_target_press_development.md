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

The subsequent read-only review found a more direct distinction: the
ordinary inner Newton stop admitted about 1e-6 N residual, comparable to
the force change induced by the proposed pressure correction. A rejected
proposal reported 6.92e-7 N residual, so its projected pressure residual
was evaluated from an inexact mechanical state. With only the inner
equilibrium tolerance tightened to 1e-10, the same model, pressure/gap
criteria, Schur bounds and seven-augmentation limit completed its
[three-step development run](../../reports/general_contact_d1_free_target_8q4_press_inner1e10_dev_20260927.json)
in 85.24 s. Its contact steps used three augmentations each, with final
pressure changes 3.01e-11 and 5.24e-11 Pa and equilibrium residuals
1.22e-14 and 1.67e-14 N. The independent gap minima were -0.325 and
-0.958 micrometres, within the unchanged 50-micrometre gate; source and
target normal forces were equal and opposite. This is development evidence,
not free-target coupled acceptance. The first successful report did not
retain Schur application counts; a separate 1e-8 comparison records them.

That [1e-8 comparison](../../reports/general_contact_d1_free_target_8q4_press_inner1e8_dev_20260927.json)
also completed in 83.21 s. Both contact steps took three augmentations;
each accepted one Schur proposal with zero rejected proposals. Their
pressure changes, residuals, forces and gaps agree with the 1e-10 run
to the reported digits. The high inner residual floor, rather than a
pressure-response rank defect or activation switch, explains these
specific rejected proposals. Future coupled cases must set an inner
equilibrium target commensurate with the contact force scale. This result
does not establish an automatic general scaling rule or a qualified
free-target loading path.

The bounded [eight-Q4 free-target full cycle](../../reports/general_contact_d1_free_target_8q4_cycle_inner1e8_dev_20260927.json)
(SHA256 `b932e1520c113a39587522a9126b9183c83777f0c98cfccde4d55064de0f4570`)
then completed all 12 steps in 219.73 s under the same explicit 1e-8
inner tolerance, 1e-5 Pa pressure criterion, 50-micrometre gap criterion
and seven-augmentation limit. The source/target normal forces balance
to reported precision. Active pressure counts are positive during press
and slide (steps 2–7), zero at complete opening (steps 8–10), and positive
again after recontact (steps 11–12). Maximum reported penetration is
0.958 micrometres; maximum multiplier change is 3.821e-6 Pa and maximum
equilibrium residual is 1.666e-11 N. Six Schur corrections were accepted
and none rejected. This is a useful **locally tested** deformable-target
cycle, still without a registered response reference, mesh/enforcement
refinement or independent acceptance.

A [fresh-model six/twelve split restart](../../reports/general_contact_d1_free_target_8q4_split_restart_inner1e8_dev_20260927.json)
(SHA256 `4f483f38c0c1e27bf36fedae6da511b64a31ce5ced74d9f4a2550db95a77081f`)
completed in 286.70 s. Its resumed twelve steps reproduced the saved full
cycle's normal force, minimum gap and multiplier-change scalars exactly
at every step; step number, active count and scaled pressure rank also
matched. All gap/pressure gates passed and maximum source/target force
imbalance was 5.43e-20 N. The prefix checkpoint's canonical JSON hash is
`b1c300ffd1109ab11dcd3166cf8def67ccdd9ae5ff19064842e8c03d4de7b2a2`.
The report's `all_step_identities_match` flag compares step numbers,
active counts and pressure ranks; the original full-cycle summary did
not retain full pressure vectors or feature identities, so exact vector
identity is not established by this development comparison. Independent
response qualification and installed free-target verification remain open.

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

The next mechanics question was whether the mixed source/target tangent
previously checked at an admissible but unequilibrated pose also agrees
at an actual free-target equilibrium. A separately saved [three-step
press pose](../../reports/general_contact_d1_free_target_8q4_press_pose_dev_20260927.json)
(SHA256 `05b2fce85013d6db44b2db9235687993f55247757f3c5425d1371da9a6d213a2`)
reproduced the earlier press mechanics and retained final displacement
and pressure vectors. Its replay has zero constraint and pressure-state
error, one active mode and 46 reduced structural coordinates.

The first [mixed tangent development run](../../reports/general_contact_d1_free_target_8q4_equilibrium_tangent_dev_20260927.json)
(SHA256 `22f27dd499c94ed0180f152becd22277e324f5ea1c4f76112e9f37930678b3f5`)
is retained as **inconclusive**: a second-order negative one-sided
8e-7 m stencil changed the active pressure branch and produced 0.232
relative mapped-contact error. Its 4e-7 m stencil kept active/support,
overlap and projection branches and had 9.59e-12 mapped-contact error.
The follow-up [4e-7/2e-7 m development comparison](../../reports/general_contact_d1_free_target_8q4_equilibrium_tangent_smaller_dev_20260927.json)
(SHA256 `4fb996763ad472e4e3ca810cab5c3075104c127da4eaf87f91ac416d001926b5`)
kept all 16 pair branches at both steps. Across 40 reduced force and six
moment rows, the largest isolated mapped-contact force and moment errors
were 9.59e-12 and 1.10e-10, with nontrivial actions of about 108 N/m
and 5.99e-5 Nm/m. This supports the selected smooth branch at the
equilibrated pose; the first crossed-branch result remains failed
development evidence. Neither run is a registered, independently reviewed
complete-tangent gate.

Independent read-only scrutiny found no stencil or structural-subtraction
flaw in this bounded probe. It confirmed the actual equilibrium residual,
second-order backward stencil, both free target and source directions,
40/6 force/moment split and branch checks. The reviewed claim is limited
to the selected fixed-multiplier elastic smooth direction: element states
are rebuilt from fresh elastic initial states, and multiplier-update,
other directions, nonsmooth crossing and complete C1 qualification were
not checked.

## Fresh-model restart pressure identity

The original uninterrupted eight-Q4 full-cycle summary retained contact
forces, gaps and pressure-change scalars but not its pressure vectors. The
fresh-model split report did retain ordered source pressure IDs and vectors
for all twelve steps. A new uninterrupted replay from the current development
branch compared those complete algorithmic pressure states with the split
report and the original full-cycle scalars. It completed all twelve steps in
217.78 s. Every step, active count and ordered pressure ID matched; maximum
pressure-vector, normal-force, gap and multiplier-change differences were
exactly zero in the saved numerical values. All declared gap and pressure
gates passed. The raw [identity comparison](../../reports/general_contact_d1_free_target_8q4_state_identity_dev_20260928.json)
has SHA256 `760f93bac7604a37055d8c229a4cf96139b852e19428a4a6651e57895efa0563`.
It binds the retained split report (SHA256
`4f483f38c0c1e27bf36fedae6da511b64a31ce5ced74d9f4a2550db95a77081f`)
and original full-cycle summary (SHA256
`b932e1520c113a39587522a9126b9183c83777f0c98cfccde4d55064de0f4570`).
The first command used an unrelated editable ANYsolver installation and
failed at import before a solve; its log is retained separately. The replay
used the isolated worktree source path.

This is development evidence for restart multiplier identity in this elastic
fixture. It is not an independent response reference or full physical-state
identity assessment. Mesh/enforcement refinement, installed free-target
verification and C1 acceptance remain open.

## Sixteen-Q4 source refinement attempt

A single sixteen-Q4, three-step press kept the same two-S3 target, supports,
distributed 0.3 N load, 1e−8 N inner equilibrium setting and unchanged
contact gates. It accepted two steps, then stopped at step three with
`maximum_augmentations_reached`. The [raw failure](../../reports/general_contact_d1_free_target_16q4_press_inner1e8_dev_20260928.json)
has SHA256 `c1d9e39a4bda80a3d75b454fb0c597b95f9627ebd4211d6fd3537f0654fd63e1`.
At rejection, force equilibrium was about 2.09e−13 N and the physical gap
was −1.64 µm, within the declared 50 µm budget. Scaled pressure rank was
34/34, but the final projected multiplier change was 7.33e−4 Pa against
the unchanged 1e−5 Pa gate. Two bounded Schur proposals predicted residuals
below 3e−11 Pa; after nonlinear re-equilibration their actual projected
residuals rose to about 1.52e−3 Pa, so both were correctly rejected.
The accepted second-step contact force was 6.48462e−5 N; an unaccepted
third-step force is not a response result. The failure is a pressure
consistency/acceleration issue for this path, not a demonstrated pressure
Gram rank, gap or force-equilibrium failure. It does not establish a
sixteen-Q4 mesh response or justify relaxing the augmentation budget.

Read-only diagnostic review found that the active Schur response is dominated
by a weak opposing-pressure mode. The full proposal intentionally deactivates
one pressure mode; its predicted and actual candidate active sets agree, but
its finite-step gap response does not. The next bounded diagnostic is one
small admissible fraction of the saved proposal at the augmentation-two
equilibrium, with a fresh mechanical equilibration and comparison of measured
gap change to the local response matrix. Small-fraction agreement would
implicate finite-step curvature or the planned branch transition; mismatch
on the unchanged original branch would implicate the response derivative.

# Prepared batched finite-inertia independent review

## Source disposition

No consequential equation or work-map blocker found in the unwired kernel `9ee021df59f5974092e94a002ed6da8b8143e0a9ed891982992a60e50d194682`. This is source clearance for a bounded local comparison, not permission to claim completed verification or trajectory savings.

[Candidate](../../src/anysolver/_ge_beam3_centered_batched_finite_inertia.py):100–128 collects original active velocity columns and three left spatial configuration columns. The body/spatial rotations, full section mass and centroid cross-coupling, centrifugal terms, nonsymmetric velocity/configuration product rules and moving work-map contribution `dd × f` reproduce [the original scalar derivative](../../src/anysolver/_ge_beam3_p5/inertia.py):93–116. Nodal frame trace rows/columns remain exact zero. Base station order and T/M/p/R/P/H accumulation remain unchanged. Validation uses the original finite-array/proper-frame/positive-section helpers plus bounded prepared station metadata; outputs are finite checked and read only. There is no owner, dispatch, compensated momentum-pair or 24-to-42 extension change.

The test's literal station virtual-work oracle contracts spatial force/couple with interpolated virtual translation/spin before generalized assembly; it does not use candidate derivative arrays. The finite differences perturb the actual velocity and left cell configuration at two distinct intervals. These are local derivative checks, not an independent continuum oracle. Kernel timing is balanced scalar/batch/batch/scalar on one declared pose, excluding preparation; any later timing result must remain kernel scoped.

## Consumed V1: NONPASS retained

[Inputs](native_inertia_batch_v1_20261001.inputs.json) SHA `aa82033132eecab24554534c5df7dbb7ae54966e57763a58d712f9c6e9e0c111`, test `184c3a0d42cadbfba7a2e1f8530e92c8fb8c6e87ff0aea4f90605a149cca1a8b`, raw `183f01c7b193863bb46eb97869843a92b6209cf74f801b64738c24e8b969bbc0`, resource `cafaa5d76e95efb29883c1dd56a7c2c1fcfc89d4108b221ebe505f755cba7376`. All 451 actual source bindings and postverification flags match; effective environment and criteria equal the frozen input. Exit 1, completed in 4.075327 s / 196.435968 MB, within 180 s / 1 GiB; zero physical timesteps.

Rest, finite off-axis and fast finite cases pass. Base energy/M/p/R/P/H are identical across all four saved cases; resolved derivative differences are at most 2.35746e-16 relative. The translation case remains UNASSESSED because the relative dv comparison fails: scalar norm 8.99154877e-17, batched norm 8.98706409e-17, difference 4.69096942e-18 (maximum entry 2.50492564e-18), giving 0.0521708722 against a cancelled denominator. With uniform translation, zero angular velocity/acceleration and the actual isotropic translational mass block, the physical first velocity derivative is analytically zero; body momentum terms cancel. This saved discrepancy does not demonstrate a mechanical equation defect. V1 nevertheless remains NONPASS under its literal criterion.

Virtual work, both finite-difference intervals, negative controls and balanced timing are unissued. A separately frozen analytic-zero arithmetic-scale comparison may address this named cancellation case while retaining the resolved relative gates. No wiring readiness, speedup, native temporal qualification, C7 acceptance or release follows from V1.

Review used source and stdlib saved-data/hash arithmetic only; no solver imports, kernel evaluations or test replay.

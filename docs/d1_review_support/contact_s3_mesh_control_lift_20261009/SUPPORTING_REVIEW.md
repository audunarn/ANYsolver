# Supporting read review — control lift

9 October 2026. Safe reconciliation checkout only; no numerical execution or product edits. This is same-family supporting scrutiny, not engineering acceptance.

## Source path before author admission delta

The existing seed is formed in reduced coordinates by `_control_projection_seed` and admitted before the structural/material/contact candidate: `static_path.py:907-925` maps `start_q` and seed through the same `T,u0`, calls `manager.admissible_step_fraction(start_u,seed_u)`, reaches a cancellation safe point, and accepts only exact fraction `1.0`. The mesh manager's shortening predicate checks both the proposed first→candidate and physical committed→candidate chords with normal and friction certificates (`s3_friction_mesh_monolithic.py:81-92`); it does not commit friction history. Nondefault predictor enters restart contract and result identity (`static_path.py:663-664,1915-1916`). This supports the intended admission-only lift if the three gates remain narrow.

Current pre-edit refusals are `core.py:698-725`, `s3_patch_static.py:423-428`, and `static_path.py:435-443`. Core has no friction argument, so its predictor acceptance can only recognize the exact mesh monolithic prerequisite; the public path must require exact `S3MeshMovingNormalFrictionSettings` together with the mesh profile. One-pair moving friction and other enforcement/analysis routes must remain refused. Existing old-none checkpoints must fail the nondefault predictor restart identity rather than be resealed.

Author source and installed evidence are pending. No new coupled behavior can be inferred from the seed alone; accepted all-facet hard closure/open and friction state gates remain decisive.

## Three-file admission delta

`core.py:701-730` adds the exact S3 mesh monolithic baseline profile to predictor eligibility only with monolithic enforcement, physical sides, S3 Jet2 and whole-face certificate. The `ContactSolverSettings.path_predictor` enum still limits nondefault selection to `control_projection_dev`. Core remains the normal prerequisite; it does not receive the friction subtype. `s3_patch_static.py:423-430` relaxes its monolithic predictor refusal only for the mesh profile; the one-pair monolithic profile still refuses. `static_path.py:435-444,504-505` admits nondefault predictor only for the exact mesh friction subtype, and separately refuses a mesh monolithic public path without that subtype. No seed/work/history implementation changed. The existing committed-to-seed normal and friction certification, cancellation point, and explicit nondefault restart identity remain on the path.

The source-tier `outputs/unit.json` records normal prerequisite admission, force-context and one-pair subtype refusal before material, full 0.39 m chord certification, and unchanged history. It is not installed coupled evidence. I found no concrete admission bypass in this three-file delta. The old-none checkpoint rejection, actual phase-three response, and final installed refusal/state results were not yet present at this read.

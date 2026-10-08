# Isolated batch-wheel development routing review

**Scoped installed development PASS.** The actual public native example completes two steps from the new isolated batch artifact. This verifies delivery/routing of the changed package, not C7 qualification or release.

## Frozen artifact and effective route

[Input](native_inertia_batch_installed_v1_20261001.inputs.json) SHA `a310af3c2791ae61ab0e1f5cd96233f87fb522a8bb150f14345feba992927214` binds 456 source/build/example/harness records. Independent stdlib hashing verifies every record against the current main bytes, then all **447 package Python files** against both the wheel members and isolated target. Wheel and target contain exactly those 447 package Python files. This includes reviewed batch `9ee021df59f5974092e94a002ed6da8b8143e0a9ed891982992a60e50d194682` and centered dispatch `86d340b182d21880b1a255b1f59d75f385903e229d62c63cc245e87a18fe636f`.

Wheel SHA `0a51e63e54d0e678f31016b41363d9c8b17d92db65d15456895abfbfb00551b5`; target `C:/ANYworkspaceWork/general-contact-native-batch-dev-20261001/target`. Build/install use the source-bound copied package, no build isolation, and pip --no-index/--no-deps/--target; no global installation or accepted-target alteration. The unchanged [installed harness](native_beam_installed_development_entry.py) selects target before importing anysolver, checks every final imported solver module lies under target, and rechecks bound main bytes after execution. The successful terminal harness asserts the captured actual example owner has unchanged default stage tolerance 1e-11. This setting assertion is in the executed harness; the summary does not dump the owner itself. Final observed NumPy and SciPy BLAS pools both have one thread.

## Saved result and limits

Only `examples/native_contact_free_finite_velocity_dev.py` is selected, with no pytest fixture or unchanged beam-contact example replay. Actual output has epoch 2, time 0.002 s, energy 0.038688671541026703 J and profile `GE_BEAM3_NATIVE_CONTACT_FREE_FINITE_VELOCITY_DEV_V2`; restart_supported is true, production_qualified false, status DEVELOPMENT and acceptance EXTERNAL_FULL_C7_OPEN. The restart flag describes the existing implementation; this example run does not execute a new restore control or independently renew temporal accuracy.

Supervisor completed exit 0 in **18.2687137 s / 142.454784 MB**, within 180 s / 1 GiB. [Summary](native_inertia_batch_installed_v1_20261001.summary.json) SHA `29ba74e5bfc459c892010d91abfd09e668089653718ccc6be6f42fb52605a3cc`; resource `f2b6491445193b30b97680f82152af28e0c3831167a4ee150ce051a5a77c8068`; log `0d7cca136efa2c7a3c6666176389618a2c2f7f3f7643392a5ec6f138844e0ac8`; task entry `392e6b188db5ebb4068e413ae70c2d1c5fd75c1dcb4868f0fc4dfed634d7233e`.

The affected mechanical/work boundary is independently supported by [local kernel](native_inertia_batch_v2_20261001.review.md), [balanced route](native_inertia_batch_route_v1_20261001.review.md) and [exact principal-spin](native_principal_spin_v1_20261001.review.md) reviews at their explicit scopes. This installed routing result does not broaden them into general nonprincipal finite-motion/spatial/impact acceptance, long-run affordability or release. All earlier failed evidence and the old accepted artifact retain their dispositions.

Review used source, saved artifacts and stdlib zip/hash checks only. No installation, example execution, production import or solver/test replay was performed by the reviewer.

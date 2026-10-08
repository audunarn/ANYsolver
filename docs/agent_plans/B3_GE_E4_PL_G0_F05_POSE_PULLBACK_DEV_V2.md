# G0 F05 yielded Q4 and actual pose-chart pullback, development v2

26 September 2026. F05 remains open. The registered Q4 v1 proof established
the fixed-predecessor deformation-map derivative, but it did not exercise the
shell port's additive rotation chart or the pose joint's mixed residual and
tangent on that yielded configuration. The competing explanations for any
combined discrepancy are the local algorithmic return-map derivative, the
deformation-map curvature, the pose/chart pullback, or an assembly sign/index
error. A total combined norm alone would not distinguish them.

Run one bounded 24-DOF Q4 plus 6-DOF beam pose and 6 multiplier development
fixture. Reuse the v1 geometry, three-layer J2 material, sealed loaded
predecessor and smooth plastic trial. Add an eccentric nonzero-multiplier
joint at Q4 node 2 with both ports in actual additive charts. Assemble the
Q4 algorithmic force/tangent and exact pose-port residual/tangent in the
same 36 coordinates. Compare the joint first variation to an independent
SciPy Rotation/closed-Jacobian oracle, and compare combined and separated
directional derivatives against central differences of that oracle's
residual and fresh fixed-predecessor local force. Use two adjacent steps
below 1e-5 relative error, active-mask agreement at endpoints and midpoints,
and byte-identical predecessor before/after. Retain any failed result.

A passing result supports this single Q4/point-pose developmental pullback.
It cannot admit the elastic-only variational adapter, establish a continuous
beam-shell connection law, prove restart/rejection ownership, or accept F05,
G0B, or G1. A material-only failure directs return-map investigation; a
joint-only failure directs chart/pose investigation; an isolated combined
failure directs assembly/index investigation. No formal F03 authority or
frozen Q4 v1 raw root is reused.

## Bounded result and decision

The source-tree run passed using Python 3.14.2, NumPy 2.4.6, one BLAS thread,
`PYTHONPATH=src;.`, `python -B`, and `NUMBA_DISABLE_JIT=1`. JIT suppression
was needed to avoid this checkout's unusually slow local package import;
the result is therefore a non-JIT development diagnostic, not an installed
artifact or performance claim. The exact source and seven mechanical hashes,
run settings and import path are in
`../reference_cases/b3_e4_g0_f05_pose_pullback_dev_v2_manifest.json`; full
measurements are in
`../reference_cases/b3_e4_g0_f05_pose_pullback_dev_v2_result.json`.
The unmodified raw files remain at `%TEMP%/b3_e4_g0_f05_pose_pullback_dev_v2b/`:
manifest SHA-256 `691bd4442b1e9a26feb8a9fba7bc69d5c18ca33648d54a7c3ca045182b969b7f`,
result SHA-256 `c0a2e298f3dc15fb021a9a5a0caaf95218be5d707a0b8ea3141c35c0cdfbd90d`.

All 12 material stations updated from the sealed predecessor; maximum `alpha`
went from `0.00399618` to `0.00425528`. Independent pose first-variation
relative error was `2.42e-16`. The nonzero joint cross-block norm was
`3.24e6` in mixed SI rows/columns, so this fixture actually exercised the
shell/beam/multiplier coupling. Across two directions and the three registered
steps, worst material, joint and combined relative derivative errors were
`8.86e-7`, `2.06e-8` and `8.86e-7`. Each direction had an adjacent passing
pair; its sampled active mask stayed fixed at both endpoints and midpoints
for every step. The complete accepted predecessor stayed byte-identical.

This closes only the stated development discriminator: a yielded Q4
algorithmic response composes correctly with one actual nonzero eccentric
pose-chart action in this fixture. The smooth material branch is sampled,
not proven continuously over the intervals. Direct mixed owner state,
attachment lifecycle, more port geometries, independent mechanical review,
and formal F05/G0B acceptance remain open. Do not relax the elastic-only
variational adapter guard based on this result.

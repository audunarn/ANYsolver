# Native replay integral — development source review, 2 October 2026

Reviewer: read-only OpenAI worker `native_integral_review`, independent of the
author of this change. Optional lower-tier workers were previously unavailable;
this is not cross-family, human or engineering acceptance. No reviewer edits or
numerical executions. Base `bd8d3ad0` plus the source snapshot in the companion
replay-owner evidence package.

No blocking source finding in the changed integration algorithm:

- Global refinement removes the parent contribution/error before replacing it
  with children. Absolute componentwise errors accumulate across current leaves.
  Final recomputation also handles children certified entirely open.
- Exact-open query elimination checks every saved pose, after whole-history
  affine/monotone gap, swept target ownership and source-orientation checks.
  Previously active points retain replay of history and released storage.
- Axial refinement regenerates angular front partitions; axial quadrature splits
  at every historical endpoint gap root.

Limits: Gauss4/8 differences are estimates, not rigorous error bounds. Endpoint
partitions do not explicitly resolve internal stick/slip fronts. The reviewer did
not rerun or independently inspect the supplied numerical evidence. The lead
ran the independent force, two-step directional tangent, discrete release,
resource and initialization/rollback checks: seven passed in62.11s. No native
C5 acceptance or installed-artifact claim follows.

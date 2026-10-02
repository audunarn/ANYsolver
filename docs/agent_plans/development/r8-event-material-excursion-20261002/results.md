# Bounded coupled material unload/reload — 2 October 2026

Experimental evidence; no aggregate scientific gate closes. Product source unchanged
from solver 33f7ba7c. Installed wheel SHA256
`96e63373eeeb5d65c83797b0aa2987c264146dd620cfd9103fb358b70554079b`.
Model and authentic force seed are bound by the regression artifact and fixture README.

Diagnostic completed in 16.20 s. Installed standing regression: **1 passed in 14.62 s**,
supervised 16.65 s, peak process-tree memory 174796800 bytes. Actual BLAS pools:
one thread; JIT disabled. Limits remain 600 s / 1 GiB. No new wheel or wider campaign.

Targets: −66, −68, −66, −68 µm. Actual controlled forces respectively:
−487.8589663834, −487.0911366314, −467.1596155715, −487.0911366348 N.
Worst equilibrium ratio 8.84e−10; gaps below 1.8e−17.
Return increment has zero beam dissipation; reload has 4.32e−16 J,
so is not described as exactly elastic. Accumulated beam/shell histories do not decrease.
Restoration at the first −68 µm endpoint followed by both steps gives exact
checkpoints and separately compared high/low material fields.

Independent saved-data review found no discrepancy; its interpretation limits are
retained. This is a local displacement excursion, not full signed reversal,
global energy balance, −500 N completion, capacity, or independent mechanics acceptance.
Historical failures and formal F03 authority remain unchanged.

Archive: `installed-excursion-v1.zip`, SHA256 `1a86c2736110586572080aa00b53157872b3a23e9335e0f6e16594410bc914f0`.
Contains runners, module/test identities, raw fields/checkpoints, logs, whitelisted
execution metadata and review. No environment maps are included.

## Bounded forward branch

From the saved first −68 µm endpoint, exactly two new prescribed steps −70/−72 µm
passed with unchanged 20 Newton / 12 backtrack limits and the same installed wheel.
Supervised runtime 9.36 s; peak process-tree memory 167313408 bytes. One thread,
JIT off, 600 s / 1 GiB. Each step was also executed from an independently restored
owner, giving exact checkpoint bytes. No new controller, interpolation or root search.

| Target | Actual controlled force | Equilibrium ratio | Constraint gap |
|---|---:|---:|---:|
| −70 µm | −485.6516744897 N | 4.55e−10 | 9.83e−18 |
| −72 µm | −483.4305131328 N | 1.22e−9 | 2.35e−17 |

Beam incremental dissipation is 1.7968e−7 / 1.8084e−7 J. Beam and shell accumulated
histories do not decrease, including the separately checked seed-to-first-step change.
The observed branch continues to soften in controlled force magnitude. This does
not prove stability, a first limit point, uniqueness, or capacity. It does not close
the original −500 N force-controlled history. Plastic paths cannot be substituted
merely because a later displacement-controlled state might reach the same load.
The prescribed two-step batch is complete; no automatic further extension.

Raw continuation archive `continued-branch-v1.zip`: SHA256 `224de336eee5b549b3828a9d21d6ec40d07b989fdbbf6fdcdb8dcfc2df11835c`.
The original diagnostic's strain/resultant/plastic arrays are rounded paired sums;
checkpoint equality is exact, while separate high/low field assertions belong to
the standing local-excursion regression above.

Independent read-only result review confirms positive plastic evolution in both
new steps: maximum beam accumulated increments 1.4394e−7 / 1.4486e−7 and shell
alpha increments 6.0122e−7 / 6.1103e−7; minima zero. Saved primary/restored arrays
agree. Both continuation owners started from the same restored −68um checkpoint,
so this is deterministic restored continuation, not an uninterrupted-versus-restored
comparison across the original force history. Decreasing force magnitude here is
not material unloading. Maximum load, stability, unique branch selection and the
possibility of −500 N elsewhere remain undetermined. Review performed no solves.

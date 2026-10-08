# G0 F06 bounded loaded shell/beam chart rebase feasibility

21 September 2026. This v2 registers the same exploratory mechanical
check after v1's import-only setup failure, not
an accepted-state rebase operation or F06/G0B pass. Source:
`scripts/probe_b3_ge_e4_pl_g0_f06_loaded_rebase_v2.py`.
Freeze its source and review independently before one execution under
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f06-loaded-rebase-v2/`.
Use a separate writable Numba cache and one BLAS thread. Pin the exact
source commit, fixture/source hashes, imports, dependencies, and raw files.
Require the entire tracked worktree clean at that commit before the
exclusive root is created, so the shell kernels and retained beam code
used transitively by the fixture cannot change at an unchanged HEAD.
Preserve all four case records and typed failures, without a same-root retry.
The v2 runner builds the equivalent reference model directly using the
native production definitions. This avoids importing the unrelated
test-module chain, including its `docs.reference_cases` dependency.
The original v2 import-only preflight of that test chain was manually
interrupted after prolonged import CPU activity; it created no evidence
root and ran no fixture. The self-contained fixture uses the same
beam sections, element count/reference geometry, loads, shell geometry,
supports, and target history as the reviewed existing coupled-mode
fixture. No numerical case or evidence root existed for v1; its frozen
source and setup incident remain retained.

Use the existing real Q4 and S3-V2D variational-shell/native-retained-B3
coupled fixture, each with straight and curved beam, through two accepted
loaded increments (`cursor=2`). Require nonzero shell rotation,
nonzero joint multipliers, nonzero native beam residual, and nonzero
shell conjugate displacement work. Freeze the accepted state/checkpoint
bytes throughout.

For shell nodal poses `(X+u, Exp(theta) Q_a)`, compare the existing
total-increment representation `Q_a=I, theta=state.shell_u.rotation`
with an alternate description `Q_a'=Exp(theta) Q_a, theta'=0`.
Translations and every physical native B3 frame, cell rotation,
resultant and material predecessor stay fixed. Evaluate both descriptions
using the chart-aware complete Procrustes Q4/S3 shell deformation map,
the actual shell element's local residual and algorithmic tangent from
the same accepted predecessor, and the native B3 retained assembly.
Obtain shell spatial rows via the actual left-Exp differential, including
the second-chart correction. Compare its spatial tangent by transforming
each chart's tangent columns to physical spatial increments.

Evaluate the objective point joint from the two reconstructed *physical*
poses and the same accepted multiplier. Reassemble external dead loading,
the shell, native beam, and joint spatial contributions; compare the
supported reactions and entire loaded residual with the actual coupled
owner response. Register each normalized error with floor `1` in its
native unit, threshold `1e-9`: shell local deformation, positions,
physical rotations, shell spatial residual/Jacobian, shell conjugate
work, point gap/wrench/Jacobian, supported reaction, full loaded residual,
repeated native beam residual, and sampled material state. Check the
accepted descriptor and checkpoint remain byte-identical.
The material-state check includes nonzero layer strain and stress for
both topologies, not only elastic zero plastic history. The aggregate
force/moment/Jacobian norms are **numeric same-unit coordinate parity
screens with floor 1**, not dimensionless physical error measures.
Separate force, moment and virtual-work scaling remains required for
full mechanical F06 acceptance.

This will show only that a loaded state has two locally equivalent
representations under the proposed chart-aware port. The current
bounded coupled owner stores total additive shell rotations, and does
not support a rebase operation or checkpoint decoding into another
chart. A passing probe must not be described as F06 completion.
F06 still needs an owned atomic rebase of actual connected beam/shell
states, changed charts through trial/restart, reactions and loads across
charts, noncommuting large rotations, and independent mechanics review.

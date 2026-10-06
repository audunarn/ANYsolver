# Experimental Q4 native physical-fibre BL5 material workflow

The explicit `BL5_NATIVE_FIBRE_MATERIAL_V1` identity selects the existing native
physical-fibre material/history driver with Q4 BL5 director-bond lines. It retains
all 42 local B3 coordinates and the existing constitutive and attachment laws.
The selected model contains at least one physical-fibre member; existing native
fibre families and generalized members may share the line. The shell is flat Q4,
with the algorithmic pullback, and is elastic or uses the existing isotropic J2
curve. The new identity selects the existing native force/moment retained scales.

The selected route is bounded force-controlled nodal dead translations. It uses
the existing local material candidates, atomic accepted histories, physical-fibre
and generalized recovery, and model-bound binary checkpoint/restore mechanism.
Q4 J2 histories use the existing native-shell framing, with a selected-policy line
admission check. Model identity includes the material policy, section definitions,
shell curve and retained-scale descriptor. Historical policies and checkpoint
identities retain their existing meanings.

Staged and external loads, displacement/arc controllers, spectra, loaded chart
rebase, and S3 plastic BL5 are refused for this new identity. The earlier native
elastic policies continue to enforce virgin elastic histories and positive yield
margin at every native station/fibre.

This is a DEV implementation candidate and is not qualified. The initial 500 N
bending controls exhausted unchanged backtrack/cutback limits under an incorrectly
bound workstation dependency graph; both numerical failures are preserved. They
have not been replaced by a different fixture or accepted as formulation failures.
Corrected exact-CI admission/refusal controls pass. One same-law bending prefix
at 500 N factors `.01`, `.1`, `.2` advances
through native fibre yield onset with unchanged physical checks; its Q4 shell
remains elastic, so this prefix does not satisfy simultaneous material activity.
One same-law continuation towards factor `.65`, chosen from recovered shell
equivalent stress, accepted `.25625` and `.284375` and then exhausted the unchanged
backtrack/cutback controls at `.3125`. Shell history remained elastic. The actual
accepted `.284375` fixed-predecessor tangent passes through finite rotational,
retained force/moment and multiplier updates, with consistent branch masks and
both finer directional errors below `1e-5`. Snapshot, native local-guard refusal,
cancellation-before-trial and fresh restore controls pass on that prefix.
The captured rejected `.3125` Newton trial has decreasing actual merit at
amounts `1e-4`, `1e-5`, `1e-6`, below the final historical dyadic amount.
Its complete weighted directional derivative errors are `2.76e-4`, `2.91e-3`,
`9.74e-3`; they do not pass `1e-5`, and their deterioration under smaller
differences remains unresolved. The rich direction changes constitutive branches
and cannot establish a smooth tangent. A new-policy safeguarded quadratic
candidate reached smaller descending steps but exhausted the same 24 Newton
iterations at `.3125` (equilibrium ratio `.0712213640`). Its exact source and
failure are preserved; its product dispatch was removed. At that checkpoint the
driver retained historical dyadic backtracking. The global equilibrium obstruction was unresolved;
no limit-load or formulation failure conclusion follows from these controls.

The runnable example deliberately reports a **partial fibre-active control**:
`.01`, `.1`, `.2`, fresh byte-equal restore, then matching continuation to
`.25625`. An isolated installed wheel completes this public workflow with the
exact CI dependency graph. Source checks verify typed rejected-candidate,
after-assembly cancellation and local programming-error atomicity. New-policy
checkpoint admission refuses support moments, retained loads and external,
staged or chart envelopes before publication. Signature refusal tests do not
claim valid historical envelope replay. Historical native elastic refusal,
generalized BL5 and finite POINT checks are selected by impact.

The initial installed partial report mixed `.2` material maxima with `.25625`
load, equilibrium and generation fields. That reporting defect is preserved in
the consumed V1 evidence. The corrected example reports all observables from
the continued accepted state; a focused installed regression observes the actual
solve results and verifies that the report agrees with the final state.

Both strict full `(.5, 1.)` lifecycle cases remain in the product test file,
without skips or expected-failure markers. Their full material milestone is
unmet; selected partial checks are not a full-file, CI or qualification pass.
The original mixed fixture's generalized member remains elastic (`1e20`
generalized yield strength). Yielded generalized/native simultaneous activity
still requires evidence. The boundary-informed candidate below observes
same-increment shell/fibre advancement on an accepted partial prefix; its full
material lifecycle gates remain unmet.
Full material, chart, physics, stability,
resolution, consumer, scale and programme obligations remain open.

Public source example: `examples/stiffened_shell_native_fibre_bl5_material.py`.
Focused source tests: `tests/test_stiffened_shell_native_fibre_bl5_material.py`.
Raw evidence: `.qualification/b3-ge-e4-pl/r8-native-fibre-bl5-material-dev-20261006-v1/`.

## Boundary-informed force trial candidate (DEV)

Only the explicit native material BL5 identity uses this internal proposal.
The coupled cell already computes `T^-1 L` for its compliance. An owned immutable
payload captures current station strains and their derivatives from that same
solve, bound to the actual cell, accepted origin, state and generation. For each
physical fibre, existing yield and table boundaries are
`e_boundary = z_origin +/- (a-p_origin + flow(a)/E)`, where `a` is the accepted
accumulation or a subsequent table knot. The first positive crossing predicted
by the current affine material branch supplies an amount.

The proposal adds a propagated binary64 multiply/add rounding bound, followed
by an outward `nextafter`. Half an ULP bounds each update operation; the bound
uses the full `[0,1]` correction range and the captured station derivative,
rather than a fixture-specific slack. This is a local force-chart proposal,
not an exact global geometric event. The full first trial is preserved. After
its rejection the next amount is at most `.5`, using the guarded boundary when
smaller, followed by deterministic halves. Every candidate still requires the
existing strict actual `max(relative equilibrium, scaled gap)` merit decrease.
The 13-candidate budget, 24-Newton limit at the test control, physical acceptance
`1e-8`/`1e-9`, laws, retained coordinates and checkpoint identity are unchanged.
No additional material response or local compliance solve is introduced.
Trial payloads are never checkpointed; they are calculated before rejected
candidates invalidate parent recovery. Legacy policies retain their historical
trial sequence, response bytes and private `Evaluation` type/fields.

The one changed-source screen restored the original `.284375`, generation 5,
checkpoint and pending controller. It accepted the controller's represented
`.31250000000000006` at generation 6 after five Newton iterations, equilibrium
`6.99675e-11` and gap `1.06984e-17`, then stopped via cancellation. This is a
narrow convergence result, not completion of the full material gate.

The two unchanged strict `(.5,1)` lifecycle cases were then run once. The elastic
shell case accepted both loads but failed its first `h=1e-4` branch-consistency
assertion: positive/negative material activity differs. No smooth tangent error
was computed. The J2 case accepted `.5`, `.75`, `.875`, then exhausted the
unchanged backtrack/cutback controls at `.90625`. Its final boundary proposal
was absent and all 13 historical dyadic amounts were used; tiny-event proposal
starvation therefore does not explain this terminal rejection. Failed-trial
residual/tangent and final equilibrium/gap were not serialized by that cohort,
so no governing-cause conclusion follows.

The J2 prefix has actual simultaneous advancement: at `.75`, five shell layer
inventories and four physical-fibre station inventories advance; at `.875`,
fourteen shell layer and four fibre station inventories advance. At `.875`,
shell alpha maximum is `4.4809561e-6` and fibre station alpha maximum is
`4.6869135e-5`. The generalized member remains elastic under its original
`1e20` strength. Full material lifecycle, smooth tangent and global continuation
remain unresolved. Six selected historical native-elastic/generalized/POINT
checks passed. Post-terminal schema and one-shot-iterable ownership repairs pass
15 focused helper/admission checks; no scientific cohort was repeated.

No candidate wheel was built: the required full cohort failed. The older
`ca2503...` installed evidence binds older source only. New source, progressive
accepted checkpoints, test/resource/import records, failed harness attempts and
preservation hashes are under the raw root's `boundary-candidate-v5/` directory.
The candidate remains partial and unqualified; aggregate material/connection,
chart, scientific and programme authorities remain open.

# Parent review of initial candidate — actionable requirements

R1: press/release/recontact currently uses three fresh independent models. This
cannot test opening/recontact state transfer. Use one public load_program with
three fixed stages (or supported sequential restart continuation) and inspect
accepted snapshots for closed/open/closed on that actual path. Reuse existing
NonlinearLoadProgram/NonlinearLoadStage. Assert map and equilibrium at accepted
states using actual nonlinear internal/contact force, never tangent-times-u.

R2: cancellation currently cancels after two iteration callbacks (may precede
any accepted increment), then solves a DIFFERENT fresh model. That does not prove
accepted-state preservation or same-model reuse. Capture at least one genuinely
accepted state first (progress increment event or checkpoint), inject cancellation
in the next trial, inspect committed state/checkpoint/snapshots at the relevant
state owner, assert contact scope cleanup and re-use the SAME model. An isolated
reference fresh solve is a comparator, not evidence of preserved state by itself.
Rejected trial also needs comparison to last accepted snapshot/checkpoint and
ideally re-evaluated equilibrium, not only MPC compatibility and final gap flag.

R3: _committed_snapshot shallow-copies value references; derivative helper does
not restore baseline despite doc claim. Use an owned deepcopy and explicit restore
for each +/- evaluation; verify baseline unchanged. Assert active-pressure mask
or pressure branch margins for every perturbed contact evaluation (minimum_gap
alone plus tangent success does not prove same branch). Keep fixed3steps.

R4: virtual work uses actual internal force, but the reported diagnostics helper
is LINEAR K u-F with signature unlike the initial call. Do not present it as a
nonlinear accepted-force oracle or recompute wrong residual with tangent-times-u.
Use actual accepted nonlinear residual f_int-F_ext and existing nonlinear result
buckets; for independent transfer use slave residual (including beam applied
load), production T mapping, and separate analytic sum N_i[F,M+r cross F]. Beam
internal force alone may have vanishing net wrench and make global tests weak.
Require nonzero force/couple and individual attachment force/couple transfer.

R5: initial interpolated_negative uses two weights(1.4,-.4): algebraic extrapolation
outside Q4 edge, not quadratic interpolation. Label only as algebraic compatibility
control or omit extra case; do not call it a quadratic on-edge record. Existing
standard tests already cover quadratic negative weights; do not expand mesh.

R6: finite-MPC guard DOES exist in general_contact/static_path.py around950:
finite path requires zero-offset selector constraints, no weighted MPC rows,
no repeated columns. Parent inspected it. Preserve it; static unchanged-source
review is permitted evidence, not an executed refusal test. Do not claim the
restriction is only an absence of any finite-rotation coupling source.

All within original plan and budget. Same implementation owner should repair,
then rerun only affected inputs and supply honest handoff/remaining criteria.

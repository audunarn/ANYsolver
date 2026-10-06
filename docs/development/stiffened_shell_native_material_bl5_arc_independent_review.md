# Independent native-material BL5 arc review

## 2026-10-06 — source-only mathematical and connected-code assessment

Repository: `C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001`; baseline `4305f789`. Non-author OpenAI Read review. Only ordinary source/scoped Git reads and this report write were performed. No interpreter, AST, compile, import, test, build, numerical or external job was run. Implementation remains with its assigned author. Root owns contracts, integration and acceptance. This supporting review does not establish different-model-family independence.

### Conclusion and concrete finding

The existing metric, full retained bordered equations, accepted-predecessor trial evaluation and isolated replay/publication architecture are compatible with a bounded native-material BL5 development route. The candidate supplies explicit admission and new controller identities rather than converting every native-history owner into an arc owner. No constitutive, retained-coordinate or atomic-publication defect was established by these source reads. This is inspection only; compatibility is not caller verification or capacity qualification.

A concrete unrun-test defect was returned to root: `exact()` in `tests/test_stiffened_shell_native_material_bl5_arc.py` directly compares `left.beam_generalized_material == right.beam_generalized_material`. `_stiffened_shell_generalized_recovery.py` defines generalized station recovery with multiple ndarray fields. Fresh replay builds distinct arrays, so generated tuple/dataclass equality reaches an ambiguous multi-element array truth value. The comparison must use explicit element/station/scalar identity checks and array equality for local strains/resultants, frames, plastic strains and their low parts. This is a source-bound test-harness problem, not a measured mechanics failure. Its repair and execution were not verified at this report's inspection cutoff.

### Coordinate, metric and linearization contract

Let the actual mixed Newton columns be `x=(q_shell, beam nodal poses, retained cell rotations/resultants, multipliers)`, with equilibrium `R(x,a)=0` and dead-load direction `p`. The existing general sparse border solves

`[J  -p; Dg  0] [dx; da] = -[R; g]`

on all free mechanical and multiplier columns. `_stiffened_shell_displacement_corrector.py` `bordered_path_correction` uses a general sparse solve; it does not invert an assumed SPD tangent or statically eliminate the retained coordinates. The physical-row zeros in retained/multiplier columns do not remove those columns from equilibrium. An indefinite retained native block is therefore compatible. An algebraic mechanism that makes the full border singular remains a real failure; adding metric penalties, artificial mass or SPD symmetrization would change the contract.

The baseline `PhysicalChordMetric` measures

`d² = sum_i w_i (|du_i|²/L² + 0.5 |R_i-R0_i|_F²)`.

The frozen tangent plane is

`g = sum_i w_i (du_i·v_i/L² + 0.5 (R_i-R0_i):(skew(omega_i) R0_i)) - radius`,

with `sum_i w_i (|v_i|²/L² + |omega_i|²)=1`. The predictor is oriented through one usable free translation, solves the full homogeneous equilibrium border, and is normalized only in this physical nodal seminorm. `path_row` maps shell spatial-spin gradients through the transpose of the actual exponential-chart differential; beam spin increments are spatial-left increments already. The retained and multiplier path-row entries are zero. No further chart Hessian is required for this scalar Newton row; the equilibrium tangent must continue to be the driver's actual update-column derivative.

`FinitePointDriver._advance` stores retained cell rotations in `state.cells` and retained generalized resultants in `state.resultants`. `q` after the nodal range intentionally remains zero. Thus the affine replay guard `q[nodal:]==0` does not discard retained mechanics: cells/resultants are serialized, replayed and participate in the full tangent. This initially suspected obstruction was resolved by source representation inspection.

### Adopted metric limit and counterexamples

Root explicitly adopted the unchanged full-frame metric for this DEV candidate. Pure shell normal spin `R=Exp(theta*n) R0`, with unchanged position/director, contributes `2*w*(1-cos(theta))>0`. The five-row BL5 law leaves that normal spin independent. The metric is therefore an objective full-frame seminorm, **not** a position/director quotient or gauge-invariant arc step measure. The candidate capability descriptor, example and unrun normal-spin/objectivity regression now state this distinction. No stiffness or attachment law change is needed to use that explicitly adopted algorithmic metric.

Radius is a tangent-plane projection, not exact accumulated path length or a proof of capacity. Explicit weights/characteristic length must retain their dimensional and mesh interpretation; the example's chosen equal weights are not scientific quadrature or inferred mass. A free translation whose tangent vanishes makes the orientation border unusable even if another branch coordinate would work. Positive selected-coordinate progress can likewise refuse a local coordinate turning point. These are admitted local-controller limits, not proof that the physical equilibrium branch ends. Rotation chords outside the existing local pi/2 domain remain refused.

### Material, seed, identity and atomic-state seams

The candidate `is_native_material_bl5_arc` checks a constructed finite BL5 line owner and the explicit native material policies. Native-history packing remains separately identified by `uses_native_material_history`; broad history recognition does not itself confer arc admission. New Q4 and S3/mixed native arc kinds/policies derive from the corresponding displacement mechanical identity, while old POINT V1/V2 and generalized coupled BL5 identity branches remain explicit. The new unrebased BL5 chart identity is distinct from native POINT chart identity.

Trials and cutbacks capture one unchanged accepted `parent`, shell origins and native beam origins. Each `_assemble` uses those origins with the trial pose/cell/resultant state and `base+a*p`; rejected candidates do not become a constitutive predecessor. Native accepted and origin histories preserve both high/low parts via the existing model-bound beam-history codec. S3 accepted/predecessor blobs, predecessor shell coordinates/anchors and Q4 accepted/predecessor arrays are bound through the existing displacement mechanical layout.

Ordinary nonadaptive force and fixed-translation endpoints are intended seeds. Staged/external/adaptive/event/rebased seeds remain excluded; loads must be affine nodal dead translations, with no rotational, retained or multiplier RHS. Arc prefixes bind the original seed digest, immediate predecessor digest, generation, load direction/base, metric, orientation, radius and control bounds. New BL5 prefixes require the new chart identity and retain the existing positive-coordinate-progress rule. There is no nonlinear material-law upgrade during replay.

`validate_endpoint` rebuilds isolated mechanics, replays the original material predecessor, checks the unchanged equilibrium/constraint limits and compares authoritative histories. Publication builds recovery before acquiring the final commit lock, then rechecks open owner, expected driver/generation, predecessor digest and physical/material witnesses. Cancellation safe points bracket publication/commit. Fresh restore uses that publisher and requires an untouched owner. Live state is replaced only after successful validation. Trial scratch recovery and caches are not accepted history; public recovery is constructed from the validated accepted state. No concrete defect was found in these connected seams.

### Necessary verification still missing

All candidate tests/example are unrun. They propose all-S3 and mixed ordinary/fixed-translation seeds, Q4 native policy variants, exact fresh restore/continued checkpoint bytes, native and S3 history comparisons, retained state, malformed history/policy refusal, cancellation before/after accepted prefix and at commit, and explicit metric semantics. Injected `ArcSelectionFailure` tests transactional propagation only; it does not demonstrate a genuine nonlinear cutback or a turning point.

Before a caller claim, fix the generalized recovery comparison and execute the complete affected workflows under separately granted authority. Named recovery presence alone does not establish positive S3 and specifically physical-fibre histories; direct family-filtered cumulative-history assertions are needed if yielded arc history is claimed. A discriminating full retained directional check must compare the actual equilibrium/path row and augmented correction in a smooth material branch with the same accepted predecessor, including shell exponential-chart and beam left-update columns. Verify retained/multiplier metric zeros while their equilibrium coupling remains present. Preserve branch inventory and existing tolerances.

Required impact controls include legacy POINT arc policy/restart/progress and generalized coupled BL5 arc identity, actual nonlinear failed/cutback state invariance, cancelled complete prefixes, fresh corrupt/mismatched restore, and controller/load/metric mutation refusal. Existing helper formulas or new unrun tests do not establish these outcomes. Source/wheel/import binding, mesh/unit/stability/external-reference checks, different-family scientific review, G4D/full programme and release remain open. User capacity intent requires later registered physical branch evidence; this local DEV extension cannot supply it by capability wording.

The final handoff state is **inspection only / source candidate implemented but unverified**. Preserve this dated finding and any later repair/evidence as a separate dated disposition; no execution authority was consumed or renewed here.

### Inspected worktree SHA256 bindings

- src/anysolver/_stiffened_shell_arc_metric.py: f0455d02762967e7e04179e214d7622543cdd0ab53c4afb4dc8f321e322ece1c
- src/anysolver/_stiffened_shell_arc_trial.py: 3363e64fae192eea7f6e9c79b632258da2ffedef828a40a2d6716acb3195f17b
- src/anysolver/_stiffened_shell_arc_control.py: 1046b50d8a8aa846856a7c21e3d2517410d43d8b6bf2cd64225835909ae39c22
- src/anysolver/_stiffened_shell_arc_checkpoint.py: 30d5fc11c18e115403e30a1333ff47d7b226286f1719513095111ce6b5e31083
- src/anysolver/_stiffened_shell_arc_publication.py: 40fd75ed8e5082af4db599a479a7f8e2e307f4b5eb594f6328819d8f8626a1fe
- src/anysolver/_stiffened_shell_affine_endpoint.py: 5c8bf8f980fc440f63cb1ac5dca83de4d96cfcb0c5b675b8aa7a7cf2cabd50b5
- src/anysolver/_stiffened_shell_ge_experimental.py: fbc26f1c95f432928c423ebc3886d12f2d33e6f86b9229a28676cde07b2491b2
- tests/test_stiffened_shell_native_material_bl5_arc.py: 0fc2f4c4814d01db847140d5a1d6fffdbc397184468998b23c846f4317352c74
- examples/stiffened_shell_native_material_bl5_arc.py: 2e1e92a33b67fadfa531ea8e9603e7c11e5fdb7fd941161fb1c16bf68bb071ea

## 2026-10-06 — focused source-repair closure

This dated entry preserves the original cutoff findings above and records their later source disposition. The exact frozen test SHA256 inspected is `0fc2f4c4814d01db847140d5a1d6fffdbc397184468998b23c846f4317352c74`; author source-handoff document SHA256 is `53ccbdea2dfebf38775f22cf151f2dacdac060ebe68860c8727c4bbac1453be6`. Both were independently read/hashed. No interpreter, AST, numerical import, compile, test, build or installed check was run during this closure.

The generalized-material equality defect is resolved **by source inspection**. `exact()` now calls `_exact_value` for generalized records and all shell/fibre/line-work records. The helper handles ndarrays with `assert_array_equal`, dataclasses with exact class checks and recursive fields, and tuple/list contents with strict-length pairing. This traverses the current exported records' station/member identities, frames, strain/resultant/plastic arrays and high/low parts rather than invoking generated ndarray-bearing dataclass equality. It does not have a general dictionary branch; no dictionary-containing recovery record was established in the inspected comparisons, and this closure does not claim a universal recursive comparison framework. Its success on actual restored results remains unmeasured.

The positive-history assertion gap is partly and accurately addressed in the intended fixtures. Mixed translation uses the previously demonstrated biaxial/continuous-P1-coarse definition. It requires positive actual S3 recovery alpha at the loaded predecessor. Both translation fixtures require positive physical-only `beam_origin_fibres` accumulation components from the model-bound history packer, rather than generalized/physical aggregate observations. The accepted arc payload's predecessor arrays are compared exactly to the captured seed histories. Force seeds and the other P0 fixture have no false simultaneous-yield premise. This adds direct assertions for the claimed loaded mixed S3/physical history and translation physical-fibre history; it does not assert that every fixture yields S3 or that plastic history grows during the arc step. None of these assertions has executed.

`test_actual_update_path_row_and_full_retained_border` adds two distinct proposed controls. First, its central difference uses `driver._advance` at a perturbed state for the same frozen tangent plane and compares the scalar path derivative with `row @ step`. The direction includes shell/beam rotations and retained/multiplier increments; the test requires cells, resultants and multipliers to change while the path-row retained/multiplier tail is zero. This is source-level coverage of the actual update-coordinate **path row**, not a measured equilibrium tangent.

Second, it assembles the actual full mechanical/constraint matrix at the predecessor and manufactures `residual=-(J*expected-p*amplitude)` and `gap=-row*expected`. The general bordered solver must satisfy the full free equilibrium rows and scalar border at the unchanged tolerances. This is an **algebraic full retained bordered-system consistency check**. It does not finite-difference the assembled equilibrium residual, verify the constitutive Jacobian, establish symmetry/inertia, inventory smooth material branches or qualify a limit point. The path row and matrix are even sampled at different states for this manufactured linear system; that is legitimate for this algebraic check and must not be represented as an actual Newton-step derivative oracle. The broader same-predecessor smooth-branch equilibrium/Jacobian directional check requested in the original review remains open.

The existing normal-spin/objectivity regression and public capability/example wording retain root's full-frame metric decision. It remains a nodal-frame seminorm with explicit caller weights, not a director quotient or gauge-invariant capacity prescription. The numerical selection failure remains explicitly injected, so a genuine nonlinear cutback/turning-point regression is still absent. Legacy identity/regression execution, atomic/refusal/restart execution, artifact binding, physical mesh/unit/stability checks, independent different-family scientific assessment and all capacity/programme/release gates remain open.

No new consequential product defect was discovered in this focused delta. Handoff remains **source repairs inspected; candidate and tests unverified**. The closed source defect and newly supplied assertions do not constitute runtime passes or whole-Jacobian qualification, and this entry grants no execution authority.

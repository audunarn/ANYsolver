# Saved native supported-tangent assessment

Status: **implemented source candidate, UNRUN**. No interpreter, collection,
model construction, numerical assessment, build or installation has run for this
slice. It grants no execution authority. The prior 600 s screen allowance and
351.9606696 s remainder concern previous screen verification, not this assessment.
The source is `examples/stiffened_shell_native_fold_assessment.py`; its main entry
refuses execution. The focused tests are also **UNRUN**.

## Question and bounded evidence

The proportional screen's g13/g14/g15 load-factor reversal is a turning
**candidate**. This tool asks whether the actual supported equilibrium tangent,
oriented by increasing physical shell tip-z, also brackets a load-factor tangent
sign change. It reads only the three binary and complete owned JSON packets in
`r8-native-proportional-capacity-dev-20261006-v1/installed-v1`; their exact sizes
and SHA256 values are pinned in `SAVED`. The artifacts come from candidate
`151cb3d4`; wheel `6464174e…` and 430-module parity are existing provenance, not
newly verified by this source-only deliverable. A future supervisor must retain
the frozen artifact/runtime bindings. No old turning, Fy, body, modal, native80,
pressure or F03 campaign is reopened or copied.

Each endpoint uses a fresh public owner, full saved public recovery comparison
and byte-identical checkpoint restoration. There is no continuation or load
solve. The work is bounded to one sparse supported border per endpoint, one
accepted assembly and four directional trial assemblies per endpoint: three
border solves and fifteen assemblies in total. The tool creates no output files;
the authorized supervisor must preserve its returned structured report and
failure diagnostics. Input bytes/packets and accepted public state/checkpoint
are compared after assessment and before each owner closes.

## Actual mixed coordinate contract

The reused symbols are `driver._increment_origin`, `driver._assemble`,
`driver._advance`, `owner._free`, `owner._coordinate_scale`,
`owner._constraint_scale`, `owner._K`, `owner._shell_index`,
`corrector.bordered_path_correction`, `physical_frames`,
`_ge_beam3_pose_joint._exp_terms`, `require_director_chart`,
`NativeDirectorChordMetric.tangent_norm_squared`, and `_material_observables`.
This is an example-level private verification seam, not a new solver API.

`_assemble` supplies the original nonsymmetric mixed Jacobian J in the driver's
update columns. Shell rotations use additive exponential coordinates; native
beam and cell rotations use spatial-left increments; retained resultants and
constraint multipliers use direct increments. All native retained coordinates
and multiplier rows remain present. Supports use the existing free numbering.
No condensation, global dense inverse/nullspace, SPD assumption or transpose
averaging occurs. The point-buckling `capture` operator is not substituted:
its conservative coordinate form requires work transformations before any
equivalence claim. No such equivalence is asserted here.

Let q denote these mixed update coordinates, p the full dead-load pattern and
lambda the physical proportional factor. The supported directional equation is

```text
J t − p a = 0,
(e_tip-z / L) t = 1,
a = d(lambda)/d(xi), xi = z_tip/L, L = 2 m.
```

The sparse bordered system is `[J,-p; e_tip-z/L,0]`. Fixed coordinates remain
zero; retained variables and multipliers remain unknowns. The progress row must
be a declared **free physical translation**, not a retained/algebraic coordinate,
and its orientation is fixed +1. An algebraically invertible border with the
wrong physical row is refused. The tool reports both dimensionless
`d_factor_d_tip_over_length` and `d_factor_d_tip` in 1/m. This is a slope with
respect to physical tip progress, not a global arc-length slope.

Existing work-dual scaling is used only as invertible diagonal row/column
transformations. With c the owner's reference coordinate scales,
E=max((|K_reference| c) c), S=(c,E/constraint_scale), D=S/E, the solve uses
`D J S`, `D p`, and `(e_tip-z/L) S`, then returns `t=S y` in original columns.
Positive reference/unit scales do not imply a positive mechanical operator.
E is fixed by the model reference, not fitted to observed slopes or peak values.
Original unscaled equation and compatibility vectors are retained, with free-row
indices, reference denominators `1/D`, unknown scales, physical-control residual
and mixed tangent values. Fixed-row derivatives are reaction derivatives and
are excluded from the supported equilibrium residual test, while remaining
visible in the original vector. Nodal translation equations use N; rotation
equations use N m; retained/multiplier channels retain their original work-dual
units and the declared reference denominators rather than a mixed-unit raw max.

The inherited original-equilibrium reference ratio limit is 1e-8 and
compatibility/control limits are 1e-9. These are not fold singularity criteria.
The physical tangent norm maps additive shell spin through the actual exponential
Jacobian before using the frozen position/director metric. An unmeasured or
nonfinite physical direction is refused. No metric mass or spectral assertion
is inferred.

## Directional consistency and exclusions

Actual `_advance` central checks use the registered fixed pair h=1e-5 and 1e-6
in dimensionless tip progress. Each perturbed evaluation holds the actual
accepted load fixed; material predecessors remain the same accepted origins.
The tool compares that mechanical residual derivative with `Jt` and reports the
analytic unit-factor load derivative `−p` and affine path derivative `Jt−pa`
separately. The latter can be zero and is not a relative-error denominator.
For both h differences and their plateau difference, the mechanical ratio is
`||D difference||_free / ||D p||_free`, where p is the frozen full unit-factor
load, D is the declared reference row scale, and free excludes fixed reaction
and multiplier rows. This denominator is positive by physical-load admission
and does not depend on observed slope magnitude. Absolute work-scaled errors
are retained separately. Compatibility errors keep their original row-reference
ratio `max|D_constraint difference_constraint|`; no load denominator is invented
for unloaded constraint rows. Both mechanical relative and compatibility
reference ratios must meet the registered elastic 1e-6 finite-difference
criterion; endpoint and linear-border limits remain separately 1e-8/1e-9.
The tool retains both h records and their plateau, with per-pair activity and public-state/
checkpoint preservation witnesses. No step retry, parameter sweep, floor or
tolerance tune is provided. This one actual mixed direction at each saved state
does not prove the whole Jacobian; the old unrelated direction oracle is not
reused as evidence. All these checks remain **UNRUN**.

Nonelastic history or active update refuses the initial elastic screen.
Perturbed material updates are also refused. Zero accumulated history and zero
trial update do not prove an elastic yield branch or a positive yield margin;
those branch/margin captures are explicitly UNESTABLISHED, and
`elastic_branch_proved` remains false. Chart,
native increment and BL5 domain failures are explicitly inconclusive. Singular
or nonfinite supported borders use the existing solver failure semantics;
unsupported models/loads/physical progress rows are refused. Unexpected restore,
programming or accepted-state mutation errors propagate and owners close finally.
All original residual vectors, control and scaled witness scalars, relative
references, FD/plateau errors and physical norms must be finite. Overflow or NaN
refuses evidence even when every assembled input or returned solve value was
finite; comparisons with tolerances alone cannot supply this check.
A low backward residual is **not** a forward slope accuracy certificate near an
ill-conditioned border. No pivot/spectral threshold is invented, and reported
signs are not certified against forward error.

## Meaning of the result and independent controls

Supported sign brackets return only `CANDIDATE`. Simple/first fold, continuity,
stability, instability and capacity claims remain false. A flat degenerate turn
can have the same sign pattern. G4D physical acceptance, full-Jacobian/forward
slope accuracy, same-law external/reference and refinement evidence, and F03
remain **OPEN**. There is no new scientific acceptance or release claim.

The source tests derive exact small scalar folds, embed one in an indefinite
nonsymmetric algebraic saddle, and check metre/millimetre covariance. Other
controls reject load-reversal-only diagnosis, orientation flips, algebraic
progress, missing-load and unsupported/pitchfork/degenerate null borders. The
u⁴−lambda control preserves `CANDIDATE` while denying simple-fold claims. A
mocked wrong correction confirms that original equation/constraint witnesses
cannot be hidden by a claimed scaled solve. These tests are independent analytic
controls of the caller's mathematics; their tighter 1e-14 tolerances concern
well-conditioned toy equations, not a new panel acceptance gate. They are UNRUN.

The intended next action is independent source review and, if the task owner
grants fresh bounded authority, execution of this exact saved-state assessment.
No source-only pass or physical interpretation is claimed in this handoff.

The augmentation follows the equilibrium/continuation distinction described by
[NOX and LOCA](https://trilinos.github.io/nox_and_loca.html) and section 7.11 of
the [Trilinos overview](https://docs.trilinos.org/files/TrilinosOverview.pdf).
These references motivate the bordered equations; they supply no panel fold
acceptance or equivalence of this mixed operator with a conservative operator.

# Selected Q1 pressure knots on a refined Q4/S3 patch

**Status:** opt-in development candidate, 28 September 2026. C1 pressure
stability, installed-package qualification and independent acceptance remain
open.

## Interface and method

The existing refined Q4-source/S3-target augmented mortar route admits a
fixed pressure subspace with `ContactSolverSettings`:

```python
q4_source_pressure_basis="selected_q1_knots_dev"
q4_source_pressure_knot_columns=(0, 1, 3, 4)
```

Knot columns refer to the declared ordered Q4 source strip. They must be
strictly increasing structural-node columns from zero through the last
source cell. The resulting pressure basis is nonnegative, partitions unity,
has one stable material-node mode per selected knot on each strip row, and
remains fixed during the analysis. It interpolates linearly in ordered
reference face index between selected nodes. The original fine Q4 geometry,
common-refinement integration, physical-gap certificate and both bodies'
work maps remain in use. A quadrature refinement does not add multipliers.

Admission is limited to 2–128 ordered Q4 source cells against the admitted
refined S3 target, projected augmented normal contact, the Jet2 Q4/S3
derivative and exact pressure support. The selected knot list, basis version,
fine source IDs, mode IDs and full interpolation matrix are bound in restart.
An incompatible knot selection rejects the checkpoint. The option changes
neither the default fine pressure basis nor the historical macro-pair route.

## Evidence

The [pressure-space screen](reference_cases/general_contact_d1_pressure_space_screen_development.md)
motivated structural-node-aligned local knots, but uses a fixed-geometry
linearized model. Independent read-only scrutiny found no defect in its
mixed Q1 integration, constrained pressure solution or L2 comparison; it
did not assess this production implementation as accepted mechanics.

`tests/test_general_contact_pressure_basis.py` directly compares transformed
fine-face Q1 work with independent piecewise Q1 shape values, checks mode
rank and positivity, and verifies exact equivalence with the old macro-pair
transform where their knot selections coincide. The selected-manager test
checks admission, mapped active contact, a smooth-branch directional tangent,
mode identities and a changed-knot restart contract. The two focused basis
test files passed 34/34 in 9.16 s after the implementation.

The bounded ordinary nonlinear static four-Q4/two-S3 press with selected
knots `(0,1,3,4)` completed two force steps in 36.0 s. At the terminal
state it has eight supported pressure modes, scaled rank eight, two active
modes, −4.09 µm minimum gap against the declared 50 µm budget, 0.0320099 N
paired normal force on opposite bodies, 1.24×10⁻¹⁵ N equilibrium residual and
3.42×10⁻¹¹ Pa final multiplier change. A fresh model replayed the terminal
checkpoint exactly. Separately, a one-step checkpoint resumed through the
remaining load step to the same final displacement and checkpoint as the
uninterrupted solve; changing the knots rejected restart. The complete
development report and log are
`reports/general_contact_d1_selected_knots_4q4_split_restart_dev_20260928.json`
and its `.log` companion.

## Limits and next checks

The four-Q4 case demonstrates routing and local mechanics only. It does not
establish that the selected basis approximates the full pressure field in a
general moving-front problem. The 128-Q4 pressure comparison was in a
linearized source-only model and does not measure nonlinear whole-route
speed. A larger coupled run requires a registered pressure/response question,
independent mechanics reference, resource rationale and unchanged gap,
pressure and equilibrium gates.

A second bounded four-Q4/two-S3 coupled development press used the same
0.3 N distributed load and mechanical inputs with fine Q1 (10 modes) and
selected knots `(0,1,2,4)` (8 modes). Both two-step solves completed with
full scaled support rank and physical gaps of −0.606 and −0.597 µm. The
selected field differs by 0.608% in nodal pressure L2 and 0.0296% in
displacement L2 from the fine *discrete* field; the integrated normal force
differs by 3.92×10⁻⁵ N. The selected run took 61.7 s versus 58.8 s for the
fine run on this small scene. These timings show no speedup and cannot
separate run variability from method cost. The raw comparison is
`reports/general_contact_d1_selected_vs_fine_4q4_distributed_dev_20260928.json`
with a `.log` companion.

Next test a registered larger coupled moving-front fixture only after
specifying which pressure or integrated-response discrepancy this small
case cannot discriminate, its independent reference and a bounded runtime.
The fine discrete field is not a continuum pressure oracle. No existing
formal evidence is retroactively changed.

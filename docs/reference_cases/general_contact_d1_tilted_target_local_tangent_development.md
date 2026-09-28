# Finite-area tilted-target local tangent screen

**Status:** development only, 28 September 2026. This checks local contact
work maps at a disposable pose. The tilted target is not an equilibrated
structural solution or a new admitted geometry profile.

## Question and setup

The flat, fixed-target full-press pose has negligible tangential contact
action for an x-direction perturbation. Starting from the saved eight-Q4
distributed full-press pose and multipliers, tilt the physical S3 target by
`dz/dx = 1e-5`, then translate all its physical nodes in x. Hold multipliers
fixed. Compare the complete mapped force and moment tangent against symmetric
differences at 1 µm and 0.5 µm. The source spans eight Q4s; target overlap is
0.9 m², with eight pressure modes active in the tilted candidate.

The first exploratory report,
`reports/general_contact_d1_tilted_target_local_tangent_dev_20260928.json`,
is a **probe defect**: it selected only target-x tangent output rows but
compared that truncated action with the full finite-difference wrench. It
reported force relative error approximately 1.0. The diagnostic was changed
to retain all physical output axes; no contact kernel or law was changed.

The corrected raw report is
`reports/general_contact_d1_tilted_target_local_tangent_full_axes_dev_20260928.json`.

| Quantity | 1 µm step | 0.5 µm step |
|---|---:|---:|
| Observed pressure/support/overlap branch | same | same |
| Mapped force action | 0.1091294758 N/m | 0.1091294759 N/m |
| Force relative directional error | 3.39e-10 | 1.92e-9 |
| Mapped moment action | 1.66001e-8 N m/m | 1.66001e-8 N m/m |
| Moment relative directional error | 6.17e-8 | 1.26e-7 |

The candidate minimum physical gap is -4.497 µm. The saved flat-pose pressure
replayed exactly before tilting. All measured directional errors are below
1e-5, and mapped actions exceed the probe's predeclared force and moment
floors. The moment action is only 1.66 times its floor, so a stronger
independently specified action scale may be useful for qualification.

This establishes one smooth local force-and-couple direction with meaningful
tangential geometry action. It does not check full coupled equilibrium,
support reactions, every tangent direction, one-sided branch derivatives or
the target's structural boundary conditions. Any formal complete-tangent
claim needs an independently reviewed case with a physical load/support path
and frozen inputs.

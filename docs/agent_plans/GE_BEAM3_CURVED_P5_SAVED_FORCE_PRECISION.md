# P5 saved-state precision audit and representation next step

Parent `9891ffae9eb1c177d3b1bc62d7ca395f077af4a4`, tree
`148f2b6b98ad87945be4054f90e4cf32203be0c6`.
Three added research paths: this note, the saved_force_precision module,
and its tests. No existing mechanics, coefficient, tolerance, reference,
default, state record or raw evidence is changed.

## Independently reconstructed translational force

The immutable centered-chord failure supplies binary64 reference/current
coordinates and cell rotations. Bind the initial and failed_last records by
their existing byte counts/SHA-256 before interpretation. Do not resolve a
local stationary system, compute a global Newton correction, rerun the arch
or manufacture a new accepted state.

For this uncoupled, elastic section only, the axial/shear matrix is
diag(1000,400,400). At fixed cell rotation U, define

`z = U^T (x_right-x_left) - (X_right-X_left)`.

The axial/shear contribution to the partial mixed potential is quadratic in
z. Rotational endpoint work has no translation derivative, and the uncoupled
curvature/moment term is independent of z. With reference derivative a and
j=norm(a), its chord stiffness is

`F = integral_half [400 I/j + 600 a a^T/j^3] dxi`.

The endpoint forces are `[-U F z, +U F z]`. This follows directly by varying
the quadratic energy; no production AD, geometry, mechanics, section response,
SO(3) kernel or cached stiffness is imported. Equal transverse shear moduli
remove reference roll from this particular expression. Reconstruct the exact
Q2 derivative of the represented reference nodes and independently solve P8
for the same eight-point Gauss rule, at 60 and 90 decimal digits. Reject plastic
or coupled section records rather than extending this special identity to
unsupported cases.

This is an ideal orthonormal reference-metric reconstruction, not a bitwise
reproduction of the rounded production frame construction and Gauss nodes.
The stored rotation entries are interpreted exactly as represented, without
orthogonal projection. Agreement between precisions is not a rigorous interval
bound or a full local/global equilibrium proof. Curvature, moments, rotational
residuals and internal stationarity are not independently checked here.

Separately add the saved binary64 element translations with exact Fractions.
That isolates scatter addition without changing the represented local forces.
The free translational norm excludes both clamps and the controlled crown-y
DOF; it is not substituted for the solver's full residual norm.

## Result

| Diagnostic | Value |
|---|---:|
| Saved free translational norm | 1.3856836165577859e-11 |
| Exact-scatter translational norm | 1.3856836165577859e-11 |
| Independent 90-digit translational norm | 1.3857759207352440e-11 |
| Largest scatter rounding difference | exactly zero |
| Largest independent/stored force-component difference | 1.1044340062356716e-13 |
| Largest 60/90-digit force-component difference | 4.6493491128917962e-57 |

The canonical diagnostic is 879 bytes, SHA-256
`C9BE3C28148B7B33469429F504FC41228086488869A165D5E45C8194C5B1E62F`.
It is reproducible stdout diagnostics, not a promoted qualification aggregate.
The failed solver and its original final residual remain unchanged.

Exact scatter cannot remove this failure: its translation values are already
exact sums of the saved binary64 element contributions. The independently
reconstructed metric/force also leaves the represented-state residual above
1e-11. The observations make another summation-only correction unpromising;
they do not prove that the nonlinear physical problem lacks equilibrium.

Eleven small tests passed in 0.55 seconds. They cover all degree-0 through
degree-15 moments of the independently generated Gauss rule, analytical
straight-bar force and energy derivative, exact rational rigid motions,
reference covariance, reversal, repeatable saved-state diagnostics,
inapplicable-section/input mutation rejection, and standard-library-only
imports. No resource-heavy worker or nonlinear solve was executed.

## Next implementation boundary

Investigate compensated trial coordinates or an authoritative reference-plus-
displacement representation. The current controller adds small corrections to
absolute positions and stores only the rounded sum. A successor must preserve
the small displacement contribution through chord evaluation, not merely
rearrange an already rounded absolute chord.

Before assembled execution, independently test exact addition/cancellation,
the first and second variations of the same potential, common rigid motion,
load work, connectivity transport, field recovery, commit/discard and replay.
Any low part or displacement field is numerical state, not a new physical DOF;
it must be hash-bound and validated, with a distinct research state schema.
Do not retrofit missing low parts into the preserved failed state or claim it
was an accepted state. Preserve the historical direct/centered profiles.

Keep the global 1e-11 equilibrium threshold and all iteration/resource bounds.
Only a tested, clean frozen successor may request a new bounded two-state
comparison. Do not launch the full onset wave or relax a threshold to obtain
a pass. This audit does not close the broad GE-B3 qualification, material,
mass/dynamics, restart, packaging or objective beam-shell connection gates.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

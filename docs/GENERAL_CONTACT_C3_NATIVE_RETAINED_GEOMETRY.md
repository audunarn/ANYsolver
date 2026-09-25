# C3 native retained round-station geometry

`native_retained_station.py` is an internal geometry and virtual-work map for
an explicitly declared circular section on a native B3-GE half-cell. It uses
the same physical centerline map as the existing native line-load work. For
cell `c`, local coordinate `t`, current nodal high/low positions `x`, retained
cell rotation `U_c`, and curved-reference half-cell lift `h_c(t)`:

```text
r(t)       = (1-t) x_c + t x_(c+1) + U_c h_c(t)
x(t,alpha) = r(t) + U_c R_ref(xi) [0, a cos(alpha), a sin(alpha)]
```

The first reference-frame axis follows the oriented tangent; the other two
define the round section. The radius `a` is explicit and positive. The station
belongs to one open half-cell; element ends and the shared cell boundary are
rejected until their physical ownership rules are implemented.

The contact position varies with the authoritative nodal translations and
the retained cell rotation. At a fixed pose, a left spatial rotation
variation gives `delta x = delta theta × U_c(h_c + rho_ref)`. The 24-column
geometric Jacobian includes that internal block. Its 42-column generalized
embedding sets the final 18 constitutive/resultant columns exactly to zero.
Nodal rotation columns are zero at fixed retained cell rotations; the native
structural equations couple those rotations rather than a contact geometry
shortcut. This map must be assembled with the full structural and contact
blocks before any future condensation.

Five focused tests passed (`c3-native-retained-station-first.txt`): straight
and curved virgin positions, internal motion at fixed external nodes,
directional virtual work, rigid covariance, rejection of ambiguous features,
and Gauss-integrated centerline work matching the separate native line-load
gradient. The checks cover a material station and its local work map. They do
not establish a search bound, surface integration, contact law, nonlinear
analysis owner, shell coupling, history, restart, native dynamics, or C3
engineering acceptance.

## Exact physical Q2 half-cell for beam pairing

`native_retained_curve_cell.py` represents each physical native half-cell by
its current endpoints and midpoint. The native reference lift is quadratic
in half-cell parameter, so these three positions reconstruct every
interior centreline point exactly. The 9×42 map differentiates all three
positions with respect to authoritative nodal translations and the owning
retained cell rotation. Its pullback maps an arbitrary curve-position
potential gradient and Hessian to the 42 native coordinates, including the
second variation of the midpoint's rotated lift. Algebraic
constitutive/resultant columns remain zero until the coupled structural
assembly supplies their interactions.

The map passed four focused tests and nine affected station/cell checks
(`c3-native-retained-curve-cell-final.txt`): exact curve reconstruction,
fixed-node internal motion, virtual work and second directional derivative,
rigid covariance and foreign-reference rejection. It is a work-map
foundation for distributed line-to-line pairing; it does not declare
point-contact or admit a native beam pair.

The existing Q2/Q2 distributed pair potential now has an explicit
`reference_arc_measure="quadratic"` mode. It uses the actual reference Q2
arc-speed at every source integration station. The default `"straight"`
mode and its prior route remain unchanged. A constant-gap parallel-line
case matched a separately integrated curved reference arc length and a
directional force check; the affected classical pair suite passed 7/7
(`c3-native-pair-curved-measure-final.txt`). The first affected run exposed
two tests calling the existing private `_direction` signature; that
signature was preserved, and its failing log remains at
`c3-native-pair-curved-measure-affected.txt`.

`native_retained_cell_pair.py` composes that symmetric distributed potential
with two retained Q2 half-cell maps. It returns an 84-coordinate residual and
tangent, including cross-beam blocks and each selected cell's rotated-lift
second variation. It checks all four half-cell combinations with conservative
gap certificates. Only one declared pair may contact; a possibly active
undeclared pair raises an error instead of being dropped. The restricted
ownership makes this an internal integration kernel, not a complete native
beam-pair route.

An interior crossing with curved native beam A gave nonzero retained-cell
work, reciprocal body forces and a balanced global-origin wrench. A combined
two-beam energy perturbation checked the coupled tangent; rigid covariance,
resource exhaustion, undeclared-pair rejection and live-definition mutation
also passed. The affected native/classical pair group passed 11/11
(`c3-native-retained-cell-pair-affected.txt`). The first focused run exhausted
a 16-level gap-certificate depth budget in a geometrically separated cell
(`c3-native-retained-cell-pair-first.txt`). A bounded diagnostic measured
that the declared 28-level budget completed that 0.1 mm certificate within
231 cells (`c3-native-retained-cell-pair-depth28.txt`); the four focused
checks then passed (`...-third.txt`). This is a resource setting for the
development scene, not a universal recommendation.

`native_retained_pair_static.py` adds a separate internal two-beam native
static owner. It instantiates two exact generalized B3-GE definitions through
the existing native model owner, retains every cell rotation and algebraic
coordinate, assembles both 42-coordinate contact blocks and their off-diagonal
coupling into one structural Newton system, and applies the native spatial
rotation correction on each diagonal block. It keeps committed material
histories fixed during trials. Initial penetration and undeclared cell
proximity fail explicitly; accepted targets require coupled equilibrium and
the declared endpoint gap. A finite path-gap certificate bounds both beams'
nodal and retained rotational motion during backtracking.

A two-beam crossing activated its selected distributed cell pair under a
0.02 N dead load at the tip of beam B. The development case completed two
targets with a conservative lower gap around -0.247 mm under an explicit
1 mm gap budget. Its retained-cell contact work, off-diagonal tangent,
reciprocal force, coupled equilibrium and smooth directional derivative
passed. Initial interference and failed-target accepted-prefix preservation
also passed. The focused owner tests passed 3/3
(`c3-native-retained-pair-static-third.txt`); the affected native/classical
pair group passed 18/18 (`c3-native-retained-pair-static-affected.txt`).
The first case used an initial 40 mm clearance and stayed open at 0.02 N;
a bounded activation diagnostic identified the 30 mm clearance used in the
registered development fixture (`c3-native-retained-pair-activation-diagnostic.txt`).
The first owner tangent test perturbed a fixed root coordinate and failed in
test setup; the corrected direction passed. Both failures remain in the
evidence directory.

The two-beam owner still admits only disjoint beams, one selected half-cell
pair and dead-force control. It has no durable contact checkpoint, automatic
multi-cell feature ownership, beam–shell interaction, general rigid tools,
friction or public C3 admission. Its swept check is a bounded fixed-pair
path-gap control, not a complete event-placement method.

## Retained round-centreline/plane penalty kernel

`native_retained_line_plane.py` adds a separate **line** penalty specialization
for the declared round radius against one fixed analytic plane. It uses
`g = n·(r-p) - a`, positive on separation, and integrates
`0.5 epsilon_line min(g,0)^2` over reference arc length. The line stiffness
has units N/m². It is not a surface-pressure or endpoint regularization.

The centered half-cell lift is quadratic in cell parameter at fixed retained
rotation, so the plane gap is quadratic. The kernel finds every interior
zero and integrates only the closed intervals. Four- and eight-point Gauss
rules drive an adaptive estimate for potential, force and tangent under
explicit dimensional tolerances and a finite visited-interval budget. Budget
exhaustion raises `MemoryError` without dropping contact.

It returns potential, a 42-coordinate residual and tangent, opposite beam
and plane forces/moments about the global origin, an independent quadratic
minimum gap, and integration counters/errors. Retained internal rotation
blocks include the curvature-lift second variation. The final 18
constitutive/resultant rows and columns are exactly zero.

The first focused run failed before mechanics because a NumPy quadrature
scalar crossed the exact station constructor; its log is retained as
`c3-native-retained-line-plane-first.txt`. Converting that internal value to
a binary64 scalar produced three passing kernel tests
(`c3-native-retained-line-plane-second.txt`). The final affected station and
line-kernel set passed eight tests (`c3-native-retained-line-plane-final.txt`):
analytic straight full/partial line force and energy, opening, curved retained
virtual work and smooth tangent, common rigid transformation, paired wrench,
and explicit integration-budget failure.

## One-beam retained static development owner

`native_retained_static.py` composes the existing native model owner and
retained generalized nodal-force equations with this plane kernel. It admits
exactly one generalized B3-GE beam and one fixed plane. All 42 local
generalized coordinates, including both retained cell rotations and 18
constitutive/resultant coordinates, remain in the coupled Newton solve. The
contact tangent receives the same spatial rotation correction as the native
structural tangent. Material history origins remain fixed during Newton and
backtracking; accepted history advances only after the coupled equilibrium
and declared endpoint gap checks pass.

The owner rejects initial interference, bounds iterations and backtracking,
and returns the last accepted target on failure. A curved clamped beam loaded
toward a supporting plane completed with 0.005804 N integrated contact
reaction, 0.178 mm maximum penetration against an explicit 1 mm development
budget, nonzero contact work on retained cell rotations, and a coupled
directional tangent error below 1e-8. The affected geometry, kernel and owner
tests passed 13/13 (`c3-native-retained-static-final.txt`). A failed second
target preserved the accepted first target, and a foreign element identity
was rejected.

The owner has a distinct versioned accepted-target checkpoint. Its current
fixed-plane swept candidate uses checkpoint V2, superseding the earlier
development-only V1. It binds
the native model/program/support identity, contact geometry and all numerical
settings. Resume authenticates the external bytes and replays every accepted
mechanical/material state against its prior committed history, coupled
equilibrium, endpoint gap and integrated contact summary. Full and split
continuation produce identical checkpoint bytes. Changed contact settings,
tampered records and live definition mutation are rejected. A failed later
target retains the last accepted checkpoint. See the runnable internal example
at `examples/general_contact_native_retained_plane.py`.

The affected 16 geometry/kernel/owner checks passed
(`c3-native-retained-checkpoint-final.txt`), and the example completed its
split restart (`c3-native-retained-checkpoint-example.txt`). The first
checkpoint development run failed when the native support identity, already
canonical bytes, was passed to the JSON canonicalizer; the final binding uses
its SHA-256 value. That failure is retained in
`c3-native-retained-checkpoint-first.txt`.

## Conservative trial-path gap bound

For each native Newton or backtracking update, the one-beam owner now bounds
the physical plane gap throughout the retained-coordinate path. Nodal
translations vary linearly in the line-search fraction. Each retained cell
rotation follows the owner's SO(3) exponential update. The normal-gap change
per unit fraction is bounded by the largest nodal normal translation plus
the rotation-angle norm times the maximum reference half-cell lift. At an
interval midpoint, the kernel evaluates the exact quadratic minimum over
both cells; subtracting half the interval's Lipschitz allowance and a
roundoff allowance gives a conservative lower bound. Intervals are bisected
until the declared penetration budget is certified. A finite explicit
interval budget triggers trial cutback or solve failure.

A curved-beam test holds both trial endpoints clear while retained rotation
drives the intermediate path through the plane; the bound rejects it. A
shorter safe path passes. The current V1/V2 candidate's affected 17 checks
passed (`c3-native-retained-swept-v1-final.txt`), and the full/split example
still matched (`c3-native-retained-swept-v1-example.txt`). The path check covers this
fixed-plane owner and its actual interpolation only. It does not establish
general first-contact event placement, moving obstacles or paired-body
swept search.

This remains an internal development route only. It has no complete
first-approach event control, prescribed-motion tool, endpoint caps, multiple
beams, beam–shell coupling, friction or admitted public C3 profile. The
existing native context has its own 120-second execution limit. These checks
do not qualify engineering contact or the general restart contract.

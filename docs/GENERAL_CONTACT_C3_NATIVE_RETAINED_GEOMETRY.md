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
pair and dead-force control. It has no automatic multi-cell feature
ownership, beam–shell interaction, general rigid tools,
friction or public C3 admission. Its swept check is a bounded fixed-pair
path-gap control, not a complete event-placement method.

The selected-cell two-beam development owner now uses profile
`NATIVE_B3_GE_SELECTED_CELL_PAIR_STATIC_DEV_V1` and a separate versioned
accepted-target checkpoint. It binds the native model, program and support,
selected contact identity, gap, equilibrium and path budgets. On resume it
replays each accepted mechanical/material state from the preceding committed
history, rechecking coupled equilibrium, the conservative endpoint gap and
the integrated contact summary. A failed later target returns the last
accepted checkpoint. Full and split continuation generated identical bytes;
changed line stiffness, wrong external hash, a forged contact summary with
recomputed envelope hash and live definition mutation were rejected.
The revised initial-gap diagnostic says the conservative lower bound is
uncertified; it no longer states that physical penetration was proven by a
negative bound.

The affected native/classical pair group passed 21/21
(`c3-native-pair-checkpoint-affected.txt`). The standalone internal example
`examples/general_contact_native_retained_pair.py` completed contact and
split restart (`c3-native-pair-checkpoint-example.txt`). The first checkpoint
test run failed only because its fixture expected the old diagnostic text;
that log is retained at `c3-native-pair-checkpoint-first.txt`.

The checkpoint remains specific to the restricted selected-cell route.
Automatic multi-cell feature ownership, beam–shell interaction, friction,
native impact and independent C3 acceptance are still open.

## Two-cell union search development

`native_curve_union.py` is a local geometric step toward contact across the
whole two-cell target beam. It requires the target cells' persistent material
node identities and verifies that they share one declared junction; matching
coordinates alone do not create shared feature ownership. At a source
station it compares the closest point on both target cells. A tie at their
shared physical junction has stable ownership. Equal-distance remote
minima are rejected as ambiguous.

For a source subinterval, the quadratic Bezier controls conservatively bound
the reach from its midpoint. Distance to the target union changes by no
more than that reach; the difference between the two target distances
changes by no more than twice it. These bounds certify open support, fully
active support with one target owner, or an unresolved interval. Unresolved
support is returned explicitly for further integration refinement; finite
depth/cell budgets fail rather than dropping it. The search alone does not
produce contact forces or resolve a switching interval's tangent.

Three focused tests passed (`c3-native-curve-union-final.txt`): a target-cell
ownership switch at the shared junction, an open case, a narrow contact
pocket, remote equal-distance ambiguity, explicit resource failure and
rejection of coincident cells without a shared material identity. The
preceding source-only and identity-check logs are retained. The subsequent
whole-pair development kernel below handles only certified cell ownership.
General switching-boundary derivatives, search scaling and C3 acceptance
remain open.

## Restricted whole two-cell beam-pair potential

`native_retained_whole_pair.py` integrates a symmetric half-weighted line
penalty over all four physical half-cells of two native beams. It skips only
certified-open source intervals from the two-cell union search. For an
interval with a certified target owner, it integrates the closest-point
distance jet and its first and second derivatives. The 36 curve-position
gradient and Hessian pull back to both 42-coordinate retained beam systems,
including midpoint rotation curvature and cross-beam blocks. Reference
Q2 arc speed sets the line measure. Eight- and sixteen-point Gauss rules
are compared under dimensional energy, force and tangent error budgets.
Unresolved integration and finite search/integration budgets fail explicitly.

The union search's Lipschitz ownership bound remains conservative near a
shared junction. For **collinear, forward-ordered straight target cells**,
the kernel also proves ownership from the junction half-space: a source
point on one side is at least as close to the corresponding cell as to the
other, and the source Bezier hull bounds the entire integration interval.
If the source crosses that junction, the exact Q2 axial polynomial splits
integration at each interior Voronoi root. Each resulting interval must
still pass the half-space certificate. Curved or ambiguous target ownership
fails. This development route is not connected to the native static owner
or public admission.

The first parallel full-length run failed on a conservative false ownership
alarm (`c3-native-whole-pair-first.txt`); a bounded diagnostic identified
the narrow intervals and projected points
(`c3-native-whole-pair-ownership-diagnostic.txt`). A rigid-transformation
check then exposed roundoff at the junction (`c3-native-whole-pair-fourth.txt`);
the half-space test now admits only roundoff-sized boundary differences.
The focused search/kernel set passed 8/8 after that final numerical bound
(`c3-native-whole-pair-final.txt`), including total force/moment balance,
energy/tangent directional checks, role exchange, common rigid motion,
opening and resource failure. The affected native curve/selected-pair/static
set passed 22/22 (`c3-native-whole-pair-affected.txt`). These are development
checks, not full C3 qualification or evidence of nonlinear static coupling.

The next interior-motion slice moved a beam's middle node axially while its
physical ends remained aligned. This made each source beam cross the other
beam's interior target junction without opening contact. The full-length
potential remained 0.04 J and normal body forces were ±4 N; body exchange
gave the same potential (`c3-native-whole-pair-crossing-third.txt`). The
affected native curve/selected-pair/static set passed 23/23
(`c3-native-whole-pair-crossing-affected.txt`). The
first crossing run found a separate unresolved support edge when the whole
beam was translated axially (`c3-native-whole-pair-crossing-first.txt`). It
failed explicitly as a possible contact missed by quadrature.

For straight affine source cells and collinear straight target cells, the
kernel now splits each source interval at axial target-feature transitions
and every real root of squared distance to the finite target segment minus
squared combined radius. The squared distance is quadratic on each such
interval. Open intervals are certified before quadrature; active intervals
are integrated with the existing dimensional error budgets. This resolves
the translated parallel-beam fixture that previously failed. Its energy
agreed with an independent scalar integration of the finite-segment gap;
forces and moments balanced, role exchange agreed, and a moving-boundary
energy/tangent check passed (`c3-native-whole-pair-support-final.txt`, 8/8).
An isolated narrow pocket smaller than the original Gauss-node spacing was
also found by the exact partition. The straight certificate rejects poses
whose coordinate roundoff exceeds the declared geometry tolerance. The
affected native tests passed 25/25
(`c3-native-whole-pair-support-final-affected.txt`).

This is a straight-profile support result, not a qualified general endpoint
law. Genuine endpoint force regularization, curved support boundaries,
arbitrary whole-beam sliding, retained rotational work in this whole-pair
route and C3 qualification remain open.

The two-beam retained static owner now admits the exact whole-pair kernel
under separate `NATIVE_B3_GE_WHOLE_CURVE_PAIR_STATIC_DEV_V1` and checkpoint
schema identities. It binds both beam and material-node identities, keeps
the existing 84-coordinate coupled assembly and spatial tangent mapping,
and records the whole-pair energy, gap and resource/error fields. The
historical selected-cell target-1 checkpoint remained byte-for-byte
identical after this change (SHA-256
`7ba6c34566ec72a09daedeed8ec3de1d18269ed595c7203b4a5e9e75063610ec`,
5469 bytes; before/after logs retained). The whole-pair open-contact solve
completed with split restart, and a fabricated active affine pose produced
nonzero work on both beams, a cross-beam tangent and a passing directional
coupled tangent check. The affected selected/whole/kernel set passed 21/21
(`c3-native-whole-owner-affected.txt`).

A loaded, clamped whole-pair solve encountered an unresolved curved support
edge at its second target (`c3-native-whole-owner-active-target-probe.txt`).
It returned failure with the first accepted target and its checkpoint
unchanged. This is a current geometry-kernel limit, not an accepted active
whole-beam static solve. The next C3 work must resolve curved partial
support and target ownership before this route can be promoted.

The revised development kernel first certifies open source subintervals
from the Q2 Bezier hull and the closest-distance Lipschitz bound. Where
target squared distance is strictly convex in station, a bound on the gap's
second derivative can certify monotonicity and isolate one activation root.
Exact target-endpoint projection cuts split tangent discontinuities before
Gauss integration. The straight-support specialization retains its original
exact active/open partition. The kernel now reports integration cells
checked and carries `NATIVE_RETAINED_WHOLE_Q2_PAIR_DEV_V1`; the whole-pair
owner/checkpoint likewise use V1. Earlier V0 evidence remains historical.

Three bent fabricated poses previously rejected by the kernel now evaluate
(`c3-native-whole-curved-support-probe-feature-split.txt`). For one partial
contact pose, potential agreed with an independent polyline-distance
integration (`c3-native-curved-partial-oracle-first.txt`). The loaded solve
still does not produce an accepted active target. Its first Newton trial
crossed the obstacle by a large amount
(`c3-native-whole-loaded-candidate-diagnostic.txt`). Exact contact
geometry/resource failures in candidate evaluation now cause bounded
backtracking rather than terminating immediately; mutation errors still
propagate. The nine allowed trial cuts were insufficient for the registered
large-load case, leaving the first accepted target and checkpoint intact
(`c3-native-whole-first-backtrack-diagnostic.txt`,
`c3-native-whole-iteration-diagnostic.txt`). The smaller-load diagnostic
also shows tiny accepted increments and subsequent gap/geometry rejections
(`c3-native-whole-small-load-diagnostic.txt`). Load-path subdivision and
general curved ownership remain open. The affected set passed 22/22
(`c3-native-curved-support-final2-affected.txt`). The terminal whole-pair
result now reports rejected trial counts and the last dimensional gap or
geometry reason; the registered large-load case reported six geometry
rejections and three gap rejections at its final iteration
(`c3-native-curved-cutback-diagnostic-result.txt`). The historical
selected-cell checkpoint hash still matched
(`c3-native-curved-support-selected-checkpoint.txt`).

The V2 development kernel adds a finite-precision contribution bound for
integration cells that can no longer be bisected in binary64. It requires
strict target-station convexity, a positive certified distance, and a
coordinate-roundoff bound within the declared geometry accuracy. Q2 shape
and derivative bounds, reference arc speed and the projection curvature
bound give dimensional upper limits on omitted energy, curve-position
force and tangent. A cell is omitted only if all three fit the remaining
global error budgets; the reported error totals include those limits and
`bounded_omission_cells` counts the events. The whole-pair owner/checkpoint
use V2 to distinguish this numerical method. This bound does not replace
independent gap checking or establish a retained-coordinate tangent error
bound after pullback.

The direct parallel-line bound check and its far-origin/nonconvex rejection
passed (`c3-native-tiny-cell-bound-final.txt`); affected kernel and owner
sets passed 9/9 and 11/11 respectively
(`c3-native-tiny-cell-focused.txt`,
`c3-native-tiny-cell-owner-affected.txt`). In an observed contact candidate,
two bounded omissions consumed at most 2.44e-19 J, 1.21e-16 N and
1.50e-13 N/m of the declared curve-position budgets
(`c3-native-tiny-cell-activation-observation.txt`). An explicit 0.0, 0.1,
0.2, 0.3 load path accepted through 0.2 but hit the native context's
120-second deadline before finishing 0.3
(`c3-native-tiny-cell-load-03-first.txt`). Full path completion and
resource performance remain open. The selected-cell checkpoint hash stayed
unchanged (`c3-native-tiny-cell-selected-checkpoint.txt`).

The whole-pair static owner's swept-path checker now first uses both
endpoint conservative gap bounds and the physical path-speed bound to
certify a safe interval without another contact evaluation. Uncertified
intervals retain midpoint evaluation, subdivision and the existing finite
interval budget. Focused safe and penetrating-path checks passed, as did
the affected selected/whole owner set (13/13;
`c3-native-swept-endpoint-affected.txt`). The selected-cell target-1
checkpoint remains 5469 bytes with SHA-256
`7ba6c34566ec72a09daedeed8ec3de1d18269ed595c7203b4a5e9e75063610ec`.
On one bounded 25-second continuation observation at the 0.3 target,
swept-check contact evaluations fell from 24 in four checks to 15 in five
checks (`c3-native-whole-03-profile-first.txt`,
`c3-native-whole-03-profile-after-endpoint.txt`). The samples performed
different total work and neither completed the target, so they do not
establish a whole-route speedup or active-contact acceptance.

An opt-in active whole-pair static regression now follows the explicit
0.0/0.1/0.2/0.3 force path with 0.13 m beam separation and -0.05 N terminal
nodal load. It reached contact equilibrium at target 0.3, with a conservative
gap lower bound of -0.000996694 m against the declared 0.001 m development
budget. The test checks nonzero contact potential, paired force and moment
balance to 1e-8 in their respective units, and byte-identical accepted
checkpoints for full and split continuation. The registered run passed in
172.09 s (`c3-native-whole-active-restart-first.txt`); set
`ANYSOLVER_LONG_CONTACT=1` to include it. A nearby, simpler path at
0.102 m and -0.002 N instead exhausted the integration-interval budget
(`c3-native-whole-near-contact-probe-1.txt`), retained as a distinct
failure. These development results do not admit the general C3 profile;
complete curved ownership, practical resource use, beam–shell coupling
and independent qualification remain open.

The nearby failure is now localized: its source half-cell is straight and
its two straight target half-cells meet at a small kink. Generic union
search returned hundreds of individually unresolved intervals, including
an open region near source station 0.183, and integration exhausted its
declared interval budget. The failure now reports source/target cells,
station interval, visited count and allocated tolerances
(`c3-native-whole-near-contact-probe-2.txt`,
`c3-native-whole-near-capture.txt`). A piecewise-straight two-segment
support and ownership partition is the next development candidate;
no tolerance or contact was silently discarded.

Run `examples/general_contact_native_retained_whole_pair.py` from an
installed checkout or with `PYTHONPATH=src` to reproduce the restricted
active path and its checkpoint continuation. The example completed and
reported 1.136742774e-7 J contact potential, equal/opposite transverse
forces of 0.000652809 N, equal/opposite moments about the origin of
0.001300055 N m, and checkpoint SHA-256
`932efcb531cdb6113950ecb7b0e1770644332f8068accd2e8124c838d6eb9b5c`
(`c3-native-whole-active-example.txt`). These are integrated line-contact
reactions for the declared 0.05 m round centreline radii, not section
surface pressures.

The V3 restricted whole-pair kernel adds an exact piecewise-straight
support/ownership partition for a straight source half-cell and two
straight target half-cells that may meet at a kink. It splits at finite
segment projection transitions, zero-gap roots and equal-distance roots;
only intervals certified active with an owner are integrated.
When both target segments project to their persistent shared junction,
that material feature has one deterministic owner. Other ambiguous ties
fall back to the existing bounded general route. The independent union
search and its conservative gap report remain in use. The V2 machine-cell
omission bound and numerical tolerances are unchanged. This change has a
distinct whole-pair kernel, static-owner and checkpoint V3 identity; V2
checkpoints are not resumed under V3.

The previously failing 0.102 m/-0.002 N near-contact path now completes
in 22.75 s, with 2.22047e-8 J contact potential and conservative gap lower
bound -0.00061256 m against the explicit 0.001 m budget
(`c3-native-kink-near-load-third.txt`). The first candidate exposed a
second, opposite-direction shared-junction branch
(`c3-native-kink-near-load-first.txt`,
`c3-native-kink-near-load-second.txt`); those failures remain recorded.
An independent finite-segment scalar integral, material-node identity
check, virtual-work derivative and tangent check passed. The oracle was
split at a short endpoint projection transition after its initial
under-resolved integral disagreed (`c3-native-kink-piecewise-focused-first.txt`
through `c3-native-kink-piecewise-focused-fifth.txt`). The affected kernel
and owner set passed 19/19 with the opt-in long test skipped
(`c3-native-kink-v3-affected-first.txt`). The V3 long full/split restart
test passed separately in 93.48 s
(`c3-native-kink-v3-active-restart.txt`). The selected-cell checkpoint
remains 5469 bytes with its original SHA-256
(`c3-native-kink-v3-selected-checkpoint.txt`).

The standalone V3 example completed with 1.136742774e-7 J potential,
conservative gap lower bound -0.000996694 m and 1872 integration
evaluations, with checkpoint SHA-256
`2e3f5d298ac6cb3639115266b86ac72ad4b1fc016680ff6af103be8951fa496c`
(`c3-native-kink-v3-active-example.txt`). This is a development result;
curved multi-pocket support, resource scaling, beam–shell coupling and
independent C3 qualification remain open.

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

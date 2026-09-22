# F03 registered saved-state spatial residual study

This implementation contract follows the independently reviewed design
`B3_GE_E4_PL_G0_F03_SPATIAL_RESIDUAL_DESIGN.md`, SHA
`de19c34fc19c713593ecd2d8a4bdd269ab35338900f93b80fdcf7e4aee5ed7f1`.
It studies the original classical n12/n16/n24 states, using the accepted
exact represented-pose diagnostic. It does not solve a new equilibrium,
change a physical state or qualify a native formulation. G0B stays open.

## Frozen inputs and mechanical conventions

Bind the complete original Ritz, saved-audit and exact-pose inventories,
with all their source, case, environment and failed-decision identities.
The exact-pose source is `d0b6d0902360210f78e06b45f7bbabb030ea4022`;
its registration, adjudication and 25-file completed inventory hashes are:

- `0371cb7e2e3d6cf68f54e215fb455ba2bce8ec7e59b57c2144ebe0ec023d85d7`
- `557ec2d058db562e0d1991c1929b475e9d86d5f9a7ba4109fdbcbabedbdb7b18`
- `e7f0b5c8a8a403d7785ddba793e8061628b8b1b163ba4251338b63c3f0e5de0a`

Read original q/eta and original functional/reaction records without
alteration. Use the exact pose record only after binding it to those same
q bits and its complete parent diagnostic. Preserve the original
FAILED_EVIDENCE, saved-audit FAILED_NUMERICAL_SCREEN, and physical HOLD.

`_b3_e4_f03_spatial_contract.py` freezes the original binary64 expressions
for material, geometry and scaling constants. Its complete definition
record belongs in registration. Exact rational algebra starts after those
expressions: lift the computed plane-stress tensor, thickness, EA, GAS,
EI, J, U0 and E0 separately. Do not re-associate arithmetic or impose
gamma=1. The engineering shear strain is u_x,y+u_y,x; stress outputs are
membrane resultants Txx/Tyy/Txy in N/m.

The cosine convention is omega=binary64(2*math.pi/L0), NumPy
cos(omega*s), with primitive sin(omega*s)/omega. Its constant and cosine
amplitudes are F0/L0 and F0/(4*L0). Do not set the endpoint sine to zero
or replace represented omega by a nominal exact multiple of pi.

Use the reviewed positive shell adjoint A*mu, physical moment component,
and root atom containing -eta exactly once. Reconstruct N/Q/M, density
and atoms from exact pose polynomials with the fixed material constants.
Record this reconstruction alongside the original functional; it does not
replace that record or its acceptance decision.

## Independent implementation and integration

Compile the shell displacement into exact tensor Legendre coefficients
from q and (1-X^2)P_i(X)P_j(Y), X=x-0.5, Y=2y. Construct stress and
divergence coefficients independently of the old basis/element operators.
Evaluate the resulting polynomials stably in the Legendre basis.
Compile exact beam polynomial antiderivatives for density and
s*d_theta; combine their interval values with the analytic cosine
primitive. No old shell/pose operator, projection, Green norm or global
equilibrium/stiffness routine may be called.

Use exactly 45 rationally defined rectangles, indexed 9*j+i bottom-to-top
and left-to-right. Fixed clipping/indicator branches come from each
cell's exact midpoint. Boundary evaluation retains that cell's one-sided
branch. Integration nodes are interior tensor Gauss nodes. Convert exact
cell bounds to binary64 for the fixed affine quadrature map; retain the
exact coordinates in registration. Never choose a new host or branch
from a deformed coordinate or a numerical residual.

Evaluate both orders 48 and 64 on every cell, free-edge segment, supported
edge segment, and the beam trace. Process one cell at a time; no array of
all quadrature-point-by-global-coefficient derivatives is allowed. The
registered polynomial degree bound is (52,48) for residual squares at
n24: density d_theta has degree at most 24, its primitive degree 25,
and the x times primitive term degree 26. Squaring gives x degree 52;
the largest shell y degree gives the other bound 48. Agreement of the
non-polynomial terms is an empirical numerical
consistency test, not a certified integration error bound.

The 27 tests are fixed: three rigid tests, left/right translation-x,
translation-y and origin-rotation lifts, then 18 supported fields in
component/i/j order with i,j=0,1,2. Scale translations and supported
fields by U0, rotations by U0/L0. Parent-side test construction and exact
pad traces use direct monomial moments, independent of the area-adjoint
implementation. Retain three work routes:

1. Cellwise area load work, with line/root/tip contributions separate.
2. One-dimensional density/trace work plus both endpoint atoms.
3. Beam weak work: distributed-load work minus N/Q/M internal work
   minus eta dotted with the root trace.

Routes 2 and 3 independently check density and endpoint signs. Also
verify supported-test integration by parts, rigid force/moment balance
with gamma, and all six lifting-reaction identities including free-edge
and volume corrections. Direct boundary stress alone is not the recovered
reaction. Compare reconstructed and original reactions descriptively.

## Complete output schema

Every case preserves both quadrature rules in order 48,64. The checker
freezes exact JSON keys and dimensions before source registration. Required
arrays include:

- Per cell: load wrenches by line/root/tip; residual force, origin moment
  and squared integral; each test's load-channel, strain and volume work.
- Per free edge: force, origin moment, squared traction integral, and
  all test works, for bottom 9 segments followed by top 9 segments.
- Per supported edge: force/moment and test works, left5 segments followed
  by right 5 segments, split at the same five y intervals.
- Per beam rule/test: density/atom trace contributions, load/internal/root
  weak-work parts, and their total. Retain unscaled physical rigid-wrench
  and six-reaction quantities in N/Nm as well as scaled work in joules.
- Exact reconstructed functional coefficients and atoms, original-data
  discrepancies, and frozen geometry/material identities.
- One-sided cell limits at each face's two corners and midpoint, in face
  order left/right/bottom/top. Preserve 45x4x3 coordinates, stress, stress
  divergence, line/root/tip area loads and total residual. Adjacent
  cells own separate limits; no averaging at a jump or corner.

One-sided samples are descriptive. No chosen sample value influences a
cell integral. Report totals and normalized V_K/B_E maps without treating
them as percentages of solution error. No Green norm or spatial error
estimator is introduced. Strong L2 defects need not decrease under
energy-space convergence.

The raw schema is `f03_spatial_residual_integrals_v1`. Per-rule arrays are
exactly the following, in the component/measure orders stated above:

| Array | Shape |
|---|---|
| cell_load_wrenches | 45 x 3 load channels x 3 wrench components |
| cell_residual_wrenches | 45 x 3 |
| cell_residual_squares, cell_shell_energy | 45 each |
| cell_load_work | 45 x 27 tests x 3 load channels |
| cell_strain_work, cell_volume_work | 45 x 27 each |
| free_wrenches | 18 x 3 |
| free_traction_squares | 18 |
| free_work | 18 x 27 |
| support_wrenches | 10 x 3 |
| support_work | 10 x 27 |
| trace_work | 27 x 3 (line, root, tip) |
| beam_weak_work_parts | 27 x 3 (load, negative internal, negative root) |
| beam_energy_load_root_work | 3 (energy, load work, root work) |

One-sided arrays have prefix shape 45 x 4 faces x 3 locations. Their
remaining shapes are coordinates (2), stress (3), divergence (2),
load_channels (3 x 2), and residual (2). Exact coordinates must match the
registered cells; all values are finite. Within each cell/edge, its wrench
must equal its corresponding rigid-test work divided by the test scales.
This check prevents opposing local errors from disappearing in a global sum.

The functional has 3 x (n+1) canonical rational density coefficients,
2 x 3 atom coefficients and one gamma, exactly 3*n+10 rational pairs.
Cosine has three finite numeric amplitudes. Parent descriptions contain
density_difference (n+1 x 3), atom_difference (2 x 3), and old_reactions
(2 x 3). The checker binds these bit-for-bit to the original arrays and
the exact functional reconstructed from the accepted pose. It validates
the pose through `exact.from_record`, including polynomial content.

Validate finite values, complete dimensions, nonnegative squared
integrals and elastic energies, and exact copied input identities.
Derived arithmetic must also remain finite; NaN/overflow is evidence
failure, never a passing comparison. JSON output
is bounded at 32MiB per case before read/parse. Rational strings use the
already reviewed canonical reduced syntax, positive denominators and
4096-character per-integer ceiling; the case checker freezes their exact
count and layout. Initial test failures and aborted runs remain preserved.

## Numerical gates and execution

The design's unchanged numerical-identity limit is 1e-10. Work comparisons
use max(E0,abs(left),abs(right)); physical force/moment differences use
fixed F0 and F0*L0, regardless of the size of the measured resultant.
Apply 48/64 comparisons to every scalar integral entering
the checks and every cell/edge squared integral, retaining both signed
values. Squared cell and edge floors are F0^2/L0^2 and F0^2/L0. Fixed
normalized scalar floors are 1. No tolerance or third quadrature rule may
be selected after a failure. There is no physical upper limit for V_K/B_E.

After synthetic tests, independent code/mechanics review and a clean
source freeze, the sole registered command will be:

    python scripts/b3_e4_f03_spatial_residual.py --run-all --root .qualification/b3-ge-e4-pl/f03-spatial-residual-v1

Three serial children, five environment thread caps "1" and integer-one
threadpool observations; 900s and 2GiB sampled child RSS per case, and a
3600s launch cutoff. No competing scientific runs or automatic retries.
Use the existing process supervisor and exclusive registration/child
markers. Freeze all source/dependency/environment/input identities.

The child performs one spatial material/geometry/state compilation and
two complete fixed-rule integrations. Its raw results are checked once
in the child and once by the parent receipt reader; the parent does not
repeat tensor-field recovery or quadrature. Both checks validate the
small exact beam functional, input copies and raw integral identities.
The registration includes the exact successful-case call inventory:
three exact-pose decodes, three functional reconstructions (one spatial
construction and two bindings), two functional-binding checks, two raw
integral adjudications, and four reaction recoveries (two rules in each
adjudication). The last count measures calculations, not unique outputs.
Field/test/trace calls and point counts are fixed in `work_counts()`.
Per complete case there are 291,676 shell-field points and 288,540 area-
adjoint points, including 540 one-sided samples. Failed/incomplete cases
do not receive this complete-case count as a claim of executed work;
their child markers, phases, failures, time and memory remain recorded.
Zero new equilibrium solves, element stiffness assemblies, old numerical
verifications, projections and Green-norm evaluations are required.
Do not label this new recovery work as zero work.

Terminal precedence is FAILED_EVIDENCE, FAILED_EXECUTION,
FAILED_NUMERICAL_IDENTITY, then PASSED_SPATIAL_RESIDUAL_DIAGNOSTIC.
All three receipts are required for a canonical final decision. Unexpected
programming/ownership/memory errors propagate with partial evidence; they
are not converted into ordinary numerical nonconvergence. A passing
diagnostic validates its reconstruction/integration and descriptive maps,
not physical reference convergence or native coupling qualification.

Require independent raw postreview and an immutable completed inventory.
Any revised approximation space needs separate derivation, review and
registration. This contract does not select such a space, increase the
Ritz degree, permit a new equilibrium or close G0B.

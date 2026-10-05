# Actual hemisphere endpoint work against an infinite cylinder — development

`CLASSICAL_B2_B3_HEMISPHERE_SUPPORT_CYLINDER_STATIC_DEV_V1` is implemented and
installed-tested. Independent engineering acceptance, application admission and
release remain open. Run `examples/general_contact_hemisphere_cylinder.py`.

Select `beam_end_cap_work="hemisphere_support_dev"` explicitly. Declare round
radius, hemisphere end caps, separate line stiffness (N/m²), endpoint stiffness
(N/m), dimensional gap tolerance below both radii and integration/path controls.
The admitted route is scalar-elastic concentric classical B2/B3, a fixed infinite
cylinder, and ordinary nonlinear static force/displacement control. Actual B3
curvature and all endpoint-tangent node contributions are retained. Material-node
incidence determines genuine physical ends; a midnode or junction is not a cap.

## Geometry and work

For the literal nonzero cylinder axis a, use P=I−aaᵀ/(aᵀa), q=c−O and the actual
outward unit tangent d. If (Pq)·d≤0, the closest hemisphere point lies on its sphere:
g=|Pq|−R−Ro. Otherwise minimize |Pq+RP(e cosθ+f sinθ)|−Ro on the physical rim, with
e/f perpendicular to d. A quartic proposes stationary roots; exact rational Sturm
counts and one-root intervals check representation and refinement correspondence.
All represented stationary candidates are compared. Missing roots, unresolved
stationarity, nonunique active minima or unresolved near-zero rim signs reject.
Open nonunique minima return explicitly zero cap penalty work. The sphere Hessian
is selected at the C1 seam; one-sided checks apply there.

Existing Jet2 differentiates the physical rim chart and implicit station:
H=Hxx−HxθHθx/Hθθ. It retains B3 midnode work, complete beam blocks and fixed-body
wrenches. Line and endpoint penalties remain distinct. Exact literal-axis projected
Bernstein controls prevent false clearance at large axial offsets. Only this new
profile uses the matching exact-axis radial line work; historical literal-projector
line routes remain unchanged. Conjugate sphere gaps preserve near-activation signs.
Finite representation and exterior endpoint restrictions remain explicit.

Affine static nodal paths use exact curve regularity and conservative full-radius
curve envelopes, spatial subdivision and temporal speed bounds. A full sphere
encloses each hemisphere, so this check may reject feasible hemisphere-only paths;
it cannot admit a path merely from endpoint sampling. Exhausted bounds fail/cut back
under inherited controls. This is not a dynamic path or collision-time guarantee.

## Composition and state

`MULTIPLE_EXPLICIT_B2_B3_HEMISPHERE_SUPPORT_ANALYTIC_CYLINDERS_STATIC_DEV_V1`
composes fixed cylinder/plane/sphere children through the existing multiple-rigid
owner. Each child retains its own work, path/gap checks and restart contract.
Old plane/sphere profile identities stay unchanged. New geometry, stationary-root
and enclosure revisions bind checkpoint compatibility. Rejected candidates clear
temporary caches; cancellation/exception replay and split restart are checked.

## Verification actually performed

Source: 54 geometry/legacy sphere checks, 14 independent static checks and four
mixed-obstacle/example checks pass. The fresh private wheel ran 139 successful
checks plus two obsolete cylinder-rejection expectations. After updating only
those test expectations, both pass; an installed lazy no-contact check also passes.
Reuse the unaffected 139 results: **142 installed cases verified across two runs**.
The first run took **54.672 s / 201,551,872 B** peak process-tree memory; the second
**3.672 s / 324,493,312 B**. JIT is disabled; effective Numba and numerical pools
use one thread. All **513 package Python files / 243 loaded solver modules** match
candidate bytes. Wheel SHA256:
`f2308eb56cad3d4d6aa4531a55cbdc376de4201c92e6c750216dc0098de489ba`.

Independent circle minimization and direct polynomial/SciPy line integration
check gaps, energy, both-body work and complete directional tangents at the 1e−5
development target. Tests include both ends, curved B3 rim work and midnode cross
blocks, rigid covariance, huge axial offsets, activation signs and active ambiguity.
Actual B2/B3 force/displacement responses match independent axial stiffness and
contact balance within 1e−6, with separate reaction/energy checks and physical gap
within the explicit 1e−5 m fixture budget. Mixed plane/sphere/cylinder B3 solves,
per-body wrenches, split/incompatible restart and real interruption replay pass.

[Evidence](d1_review_support/contact_hemisphere_cylinder_20261004/summary.json)
and the external raw root `C:/ANYworkspaceWork/contact_hemisphere_cylinder_20261004`
retain source01 tangent cancellation, source06 wrong test attribute and installed01
obsolete admission failures. Supporting source review identified rounded-projector
and root-completeness defects; their corrections are checked by independent test
oracles. Supporting same-family review is not independent engineering acceptance.

Remaining: translating/free/capped cylinders, beam-pair and finite-face cap work,
native endpoints, friction/spin, dynamics, mesh/enforcement qualification and full
C0–C9 completion. No performance savings, publication or default change is claimed.

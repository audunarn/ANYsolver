# C2 development slice: distributed classical B2 beam-pair contact

This opt-in profile admits two disjoint, straight-reference classical B2
cells with explicitly declared round centreline radii. It integrates
frictionless line contact between the actual deformed segments through von
Karman nonlinear static force or displacement control. The accepted
potential is a symmetric half-weighted sum of the two directional line
potentials; both bodies' residual and tangent blocks are derivatives of that
same potential. B3 beam pairs and multi-cell assemblies remain open.

```python
ContactDefinition(
    surfaces=(
        ContactSurface("a", (first_beam_id,), beam_radius=0.01),
        ContactSurface("b", (second_beam_id,), beam_radius=0.01),
    ),
    rigid_bodies=(),
    interactions=(ContactInteraction(
        "a_b", "a", "b", normal_stiffness=None,
        line_stiffness=1.0e4, gap_tolerance=0.004,
    ),),
)
ContactSolverSettings(
    pair_motion="general", line_integration_relative_tolerance=1.0e-7,
)
```

Each radius and gap tolerance is in metres. `line_stiffness` has units N/m²
and is distinct from surface-pressure and endpoint-point regularization.
The optional endpoint caps from the beam-plane profile are not admitted in
this pair slice. The two selected cells may not share a material node.
Admission is limited to scalar elastic B2 sections, isotropic elastic
materials and von Karman structural kinematics.

For source arclength (s_0), deformed centreline (x_A), closest target
point (x_B^ast), and (R=r_A+r_B), one directional potential is

\[
\Pi_{A\to B}=\frac12 k_l\int_{A_0}
\langle R-\|x_A-x_B^\ast\|\rangle^2\,ds_0.
\]

The profile assembles \(\frac12(\Pi_{A\to B}+\Pi_{B\to A})\). It partitions
each source segment where the closest target feature changes or the gap
crosses zero. Each active interval uses 8- and 16-point Gauss controls,
recursive refinement and a finite subdivision budget. The smooth-branch
tangent includes the derivative of the interior closest-point projection.
An exhausted integration budget fails explicitly. The separately reported
gap minimum is the exact segment-to-segment distance minus the combined
radius; it does not depend on quadrature points.

A swept check bounds relative material-point motion over each linear solver
trial. Its speed bound is the largest relative displacement among the four
node pairs, and its recursive interval bound uses exact segment distance at
the endpoints and midpoint. An uncertified path is cut back or stopped, even
when its endpoint gaps are positive. The finite subdivision budget is
explicit in `ContactSolverSettings`; it is not a global collision guarantee
for arbitrary motion paths.

[The crossing example](../examples/general_contact_round_beam_pair.py)
drives one B2 through distributed contact with a supported B2 and reports
the paired wrenches, exact gap and integration counters. Focused controls in
`tests/test_general_contact_beam_pair.py` cover an analytic parallel-line
potential, a crossing independent integral, near-parallel contact, smooth
tangent, role exchange, rejected initial interference, through-crossing
sweep and coupled static restart.

This profile is **implemented and locally tested**, not independently
accepted. It does not yet cover B3 pairs, multiple cells, endpoint or
junction contact, coincident/multiple closest points, self-contact,
line-to-shell contact, friction, finite-rotation kinematics or automatic
pairing. Mesh, integration, enforcement and resource scaling qualification
remain required for C2 acceptance.

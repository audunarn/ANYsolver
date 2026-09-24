# C2 development slice: classical round beam against a fixed plane

This opt-in profile places a declared round centreline tube on exact classical
`BeamElement` (B2) or `QuadraticBeamElement` (B3) elements. It admits one selected
beam surface against one fixed analytic plane through von Karman nonlinear static
force or displacement control. A B3 reference cell must satisfy the existing
straight, midpoint-node structural contract; its *deformed* centreline is
quadratic. Admission currently requires a concentric scalar elastic section
and an isotropic elastic material; generalized sections, fiber plasticity,
eccentric B3 sections and other constitutive families await separate checks.
The profile has been implemented and locally tested, but C2 and its
engineering qualification remain open.

```python
ContactSurface("beam_tube", (element_id,), beam_radius=0.01,
               beam_end_caps="none")
ContactInteraction("line_plane", "beam_tube", "plane",
                   normal_stiffness=None, line_stiffness=1.0e4,
                   gap_tolerance=0.002)
ContactSolverSettings(pair_motion="general")
```

The declared `beam_radius` is in metres. `beam_end_caps` must be either `none`
or `hemisphere`. The optional cap profile requires a separate positive
`endpoint_stiffness`. Set the surface-pressure `normal_stiffness` to `None`;
it is never reinterpreted as line stiffness. `line_stiffness` has line-law
units **N/m²**: the line
reaction is N/m and the reference-length potential is
\(\frac12 k_l\int\langle-g\rangle^2\,ds_0\). Endpoint stiffness has point-law
units **N/m**: each owned cap contributes
\(\frac12 k_e\langle-g_e\rangle^2\). These are numerical regularizations,
not inferred section dimensions or material moduli. Results label the two
stiffnesses, energies, line length, endpoint count and integrated wrenches
separately. The line and point features transfer forces to the beam's
authoritative translation coordinates; the frictionless centreline profile
has no section-rotation couple.

The line kernel uses the actual interpolated B2/B3 deformed curve. Against a
fixed plane, its centreline gap is linear or quadratic in element coordinate.
The kernel partitions the line at every physical contact root, integrates
the active polynomial with three-point Gauss quadrature per interval, and
computes its exact interior/end minimum independently of those integration
points. Residual and smooth-branch tangent differentiate the same discrete
potential. A linear trial displacement makes every material-point plane gap
affine in path fraction; the accepted endpoint minima therefore certify the
entire represented increment. An unresolved gap causes solver cutback or an
explicit stop, without silently dropping a cell.
The fixed infinite plane checks every selected cell directly; no BVH or
automatic pairing is claimed. `maximum_candidate_pairs` caps the number of
selected cells and rejects a larger definition before assembly.

`hemisphere` assigns a point spring only to a genuine end node of the full
classical-beam mesh, and only when the plane approaches that cap's outward
half-space. A shared beam junction never receives an endpoint spring. The
distributed side line and the endpoint are distinct integration features.
The cap switch is nonsmooth at a tangent approach and has not been qualified
there. The point spring is a regularized feature force, not a Hertz pressure
model.

The runnable [B3 example](../examples/general_contact_round_beam_plane.py)
prescribes midpoint displacement and reports an interior contact interval,
paired beam/plane forces, exact minimum gap and a version-2 checkpoint. Local
controls in `tests/test_general_contact_beam_plane.py` cover B2 uniform
penetration, an independently integrated B3 partial-contact reference, local
directional tangents, B2/B3 coupled solves, common-rigid-translation wrench
invariance, endpoint ownership, material admission, initial
interference rejection and restart definition binding.
A narrow B3 interval case admits a declared 10 µm gap budget
(\(10^{-3}\) of its 10 mm radius) at −8 µm minimum gap, while a 5 µm
budget stops before the last increment. This is a controlled sensitivity
check, not mesh or regularization convergence.

This plane profile does not admit line-to-shell pairs or beam pairs. A
separate [two-cell B2/B2 development profile](GENERAL_CONTACT_C2_BEAM_PAIR.md)
handles distributed line-to-line contact. Both profiles still lack general
finite sliding between curved bodies, native B3-GE, friction, corotational structural
kinematics, a moving plane, automatic search or measured beam-pair scale.
The `none` cap policy supplies no end-on point force. A complete C2 delivery
requires physical endpoint and near-parallel pair cases, mesh and enforcement
refinement, independent review, and installed-package evidence.

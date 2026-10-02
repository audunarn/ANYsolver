# E04 roof candidate — geometry prepared, mechanics unexecuted

`stiffened_shell_e04_roof.py::build` defines a new elastic comparison candidate.
It uses SI dimensions inspired by the [Kratos hinged cylindrical roof example](https://kratosmultiphysics.github.io/Kratos/pages/Applications/Structural_Mechanics_Application/Examples/Hinged-cylindrical-roof-snapthrough.html),
which references Sze, Liu and Lo (2004). Two rectangular longitudinal stiffeners
and explicit supports are added here. The published bare-roof response is **not**
an oracle for this different model. External comparison remains open. Installed native development screens now
complete seed/arc/restore and a coarse ascending/descending trajectory.

The generator defines the geometry, linear isotropic modulus/Poisson ratio,
section dimensions, centroid offsets, node/cell ordering, full-pose point-pair
locations, restrained translations and central downward-load node. Straight side
edges restrain all three translations, rotations remain free, and curved ends
are free. Section properties must be taken about each bar centroid; the point
connection already carries the eccentric lever arm. No second offset or plate
effective-flange contribution may be added. This is a nodal point-bond model,
not a chain advertised as a bonded line. Density is not specified for this
static candidate. No extra geometric imperfection is included yet; nominal roof
curvature is not an imperfection operation.

Meshes 8x8, 16x16 and 32x32 have respectively 64/256/1024 Q4 facets and
8/16/32 B3 cells across two members. All Q4 facets are planar. The physical
reference metric assigns half its weight to normalized shell-area measures and
half to normalized beam-length measures. This allocation is fixed across meshes.
The shell weights are area-lumped and B3 length weights use Simpson lumping.
They reproduce uniform measures and converge for the checked affine field;
they do not exactly integrate squared general quadratic beam fields or prove
mesh-independent nonlinear continuation trajectories. Force-like algebraic
variables must not enter that metric.

## Required next implementation

The default owner still rejects nonflat geometry. The explicit development
`CURVED_Q4_POINT_REFERENCE_V1` policy now admits elastic planar Q4 facets and
full-pose nodal points through the existing algorithmic pullback. Shell nodal
rotations are global incremental rotations; facet reference normals remain in
geometry. Local rigid-motion, derivatives and eccentric work, plus a bounded
curved control's finite solve/restart, have installed evidence. This is not an
E04 roof solve. A separate low-load control remains nonconvergent with no commit.
See [scope and evidence](../agent_plans/development/r8-curved-reference-20261002/results.md).
The separate elastic point arc/checkpoint route now has bounded installed
lifecycle evidence. Next construct this actual roof owner and establish a bounded
seed/continuation screen before selecting its capacity bracket.
Do not select an artificial J2 law or replace six-channel points with BL5 merely
to pass the current controller's material predicate.

After admission, define the matched CalculiX model and verify its connection and
section idealization before executing E04. Register an ascending-to-descending
bracket around the first load maximum, compare physical forces/displacements,
retain turning-point restart, and apply the programme's existing refinement and
5% nonlinear-reference criteria. No load maximum or descending extent is yet
known for this new stiffened model; do not infer either from the bare roof.
An equilibrium failure alone cannot locate the maximum. The separate required
stress-free-imperfection and stability obligations remain open.

## Development checks

`tests/test_stiffened_shell_e04_geometry.py`: four checks passed through the
existing bounded source runner (`e04-geometry-v2`, 2.41 s supervised). They cover
facet orientation/planarity, frames, centroid offsets, support/load inventory,
positive owned reference measures, an analytic affine-field refinement identity
and continued rejection by the current flat owner. They are not numerical
capacity or external-reference acceptance. Independent source review found no
geometry/unit defect and identified the frame/admission seam above.


## Actual native development screens

`definition(case,density_kg_m3=...)` adapts the geometry through the public facade
with explicit centroidal rectangle stiffness and separate density input.
`scripts/r8_e04_native_roof.py` runs the bounded installed screen under the task
supervisor.4x4/8x8 seed10N paths and final restore pass. A4x4seed100N/24arc.003
trajectory samples2206.307N at9.439mm and descends to1374.343N at15.178mm.
[Actual results,raw evidence and limitations](../agent_plans/development/r8-e04-roof-20261002/results.md).
This establishes a development bracket; external mapping,three-level capacity
convergence,turning-point restart,imperfection and stability remain open.

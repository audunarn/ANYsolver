# Elastic sphere stiffened-panel initial state (2026-10-20)

Declared benchmark case and delivered initial state for candidate
`0.4.7+contact.candidate.20261020.s6`. The authoritative case and acceptance
criteria live in the active living note
`C:/ANYworkspaceWork/contact-incremental-delivery-20261020/elastic-sphere-panel-initial-v1/PLAN.md`;
this document describes the delivered construction and workflow.

## Case

- Hollow deformable elastic sphere, 1 m outside diameter, 10 mm wall,
  represented as a faceted elastic S3 shell skin (162 nodes, 320 triangles,
  fixed case data in `examples/elastic_sphere_stiffened_panel_mesh.py`).
- Clamped 5 x 5 m x 10 mm panel (10 x 10 Q4 shell grid) stiffened on its
  underside by four upright 150 x 10 mm flat bars at 1 m spacing
  (10 beam segments per bar), beam centroids at z = -0.080 m, plate
  midsurface at z = 0, plate top at z = +0.005 m.
- All six DOFs clamped on the four plate edges (Integrated edge translations
  + CL edge rotations, 40 edge nodes each).
- Gravity 9.81 m/s^2; both bodies purely elastic
  (E = 210 GPa, nu = 0.3, rho = 7850 kg/m^3, yield stress 0, no hardening).
- The 10 m drop of the sphere onto the panel is retained as the target; it
  is NOT executed by this candidate.

## Construction

- The panel is built from the canonical ANYmesher neutral stiffened-panel
  geometry through public solver APIs (`generate_stiffened_panel_mesh`,
  `FEModel`, public element/section/constraint services). The generator's
  legacy 235 MPa material is explicitly replaced by the elastic case material
  before assembly; no penalty connection or invented inertia is used.
- The upright 150 x 10 mm flat bar is installed through the canonical public
  section constructor `StiffenerCrossSection.from_geometry("T-bar", 0.150,
  0.010, 0.0, 0.0)` — a zero-flange rectangular upright web under the
  canonical thin-wall convention — which provides the exact area
  (0.0015 m^2), bending inertias (Iy = 2.8125e-6 m^4, Iz = 1.25e-8 m^4),
  extreme-fibre distances (c_y = 0.005 m, c_z = 0.075 m) and the canonical
  thin-wall open-section St Venant model J = h*t^3/3 = 5e-8 m^4 with its
  torsion modulus. J is the canonical thin-wall section model for the open
  rectangular web, not the exact 3D rectangular-torsion value. The beam
  elements carry this canonical section before any assembly; no section
  formula is overridden by hand. The physical shape is a 150 x 10 mm flat
  bar, not a flanged T.
- The bars sit below the plate (beam neutral line and tie eccentricity at
  z = -0.080 m through the mesher's centroid placement parameter, which
  locates only the neutral line; the physical section metadata stay
  h = 0.150 m, t = 0.010 m) through the interpolating beam-shell MPC with
  rotating eccentricity preserved.
- The sphere is fixed explicit case data, not a new generic mesher: a
  frequency-4 icosphere on the midsurface radius 0.495 m, closed with two
  faces per edge, outward winding, radius deviation below 1e-12 m. It is
  built as default S3 shells with per-triangle outward reference normals,
  carries no supports, keeps all DOFs deformable, uses no mass rescaling,
  and is never statically solved.

## Delivered initial state

`examples/elastic_sphere_stiffened_panel.py` (CLI: `--output <path>`):

1. builds panel and sphere and verifies every element carries the declared
   elastic material;
2. solves the PANEL ONLY gravity equilibrium (corotational kinematics,
   work-conjugate rotating-MPC tangent, initial four-way gravity partition (existing adaptive stepping), max 20 Newton
   iterations, tolerance 1e-8);
3. recovers per-node support reactions with the same public corotational
   work-conjugate element force law as the solve (the interpolated beam-shell
   MPC contributes no element force; its constraint force enters through the
   solver's rotating-MPC slave-to-master imbalance transfer), compares the
   recovered named support resultants with the solver-recorded per-step
   resultants (agreement tolerance 1e-9 relative), and checks the global
   force and moment balance against 1e-8 * max(1, 2198*9.81) N and
   1e-8 * max(1, 2198*9.81*5) N m;
4. checks the raw unconstrained translation mass of each body per axis
   against its reference (sphere: rho*t*faceted area; panel: 2198 kg) within
   relative 1e-10;
5. places the stress-free sphere at rest with a 10 m clearance between the
   lowest point of its outer surface (outside radius 0.500 m; midsurface
   radius 0.495 m) and the equilibrated panel top at the impact centre
   (x = y = 0), i.e. sphere centre z = equilibrated panel top + 10.0 + 0.500;
6. writes the case metadata, mesh/node/element/support sets, physical
   masses, runtime identity, accepted panel nodal fields and sphere pose as
   one JSON document with `status=initial_state_prepared` and
   `impact_status=unsupported`. The exported mesh data is the real model
   inventory, not a documentary claim: reference node coordinates and
   element connectivity/type/body sets for both bodies (sphere in local
   coordinates plus its pose), the actual support node ids, and the
   verified bar layout (beam neutral lines at y = -1.5, -0.5, 0.5, 1.5 m,
   z = -0.080 m; plate midsurface nodes at z = 0).

The unconstrained sphere is never solved under gravity: no supports are
invented for it. Mass references are reported distinctly: the assembled
faceted FE skin mass (rho*t*faceted area), the smooth midsurface shell
reference (241.707384343 kg) and the hollow-solid volume reference
(241.715604844 kg) are different quantities; only the faceted value is the
assembly target. The panel target is 2198 kg (plate 1962.5 kg + bars
235.5 kg).

## Impact is unsupported

The gravity-driven impact with both bodies deformable has no admitted
solver route in this candidate. Any impact request is refused clearly:
`request_impact()` raises `ImpactUnsupportedError`, and the CLI `--impact`
prints a refusal document (`status=impact_refused`), writes no output file
and exits 3. No impact history, transient checkpoint or restart is produced
or implied. The analytic free-fall quantities in the output document
(1.427843123 s, 14.007141036 m/s, 23.7115 kJ) are labelled planning
references, not solver results.

## Checks

Focused appended coverage in `tests/test_elastic_sphere_stiffened_panel.py`
(candidate selectors in `scripts/contact_candidate_slice2.json`): fixed
sphere case-data topology, exact metadata/supports/unconstrained sphere,
exported-mesh geometry (real node coordinates, element connectivity and
body sets for both bodies, bars at y = -1.5, -0.5, 0.5, 1.5 m and
z = -0.080 m, clamped-support nodes on the plate edges), per-axis masses
against both references, completed panel gravity solve with the fixed
settings, global force/moment balance tolerances with recovered-vs-recorded
support-resultant agreement, sphere pose and placement, and the impact
refusal (exception and CLI exit 3 with no output file). One session-scoped
fixture performs the single panel gravity solve and shares the verified
payload across the checks.

## Measured initial-state result

Local Python 3.12.13, JIT disabled, one thread: all nine case checks and 14
candidate-tool checks pass. The module CLI writes a complete initial-state JSON.
The assembled panel translation mass is 2197.9999999999995 kg per axis;
the faceted sphere is 237.14289586353 kg per axis, matching rho*t*facet area.
The faceted sphere is about 1.89% lighter than the smooth-shell reference;
this is a reported discretization difference, with no mass or density scaling.
Centre panel displacement is -0.000598370542 m. Global force imbalance is
4.826253e-7 N (limit 2.156238e-4 N), and moment imbalance is 2.156873e-10 Nm
(limit 1.078119e-3 Nm). Recovered and solver-recorded support resultants agree.
The initial four-way partition uses the existing adaptive solver: actual
accepted load factors are 0.25, 0.625 and 1.0, each with three Newton iterations.
The configured relative tolerance remains 1e-8; recorded residual norms have
force units and are not an absolute 1e-8 N criterion.

`panel.mesh.nodes` holds reference SI coordinates; `panel.mesh.elements`
contains element types, body labels and connectivity. `panel.nodal_fields`
contains [ux, uy, uz, rx, ry, rz], with translations in metres and rotations
in radians. Sphere coordinates are local to its reported centre; its initial
stress, velocity and spin are zero. The JSON is an initial-state report,
not a transient restart file. No impact result is claimed.

The s6 bundle uses the existing Contact candidate workflow to cold-install the
same wheel bytes on Windows and Ubuntu. Installed results and final bundle
identity are recorded in the slice-6 delivery receipt referenced by the contact
handoff. No broader qualification follows this slice automatically.

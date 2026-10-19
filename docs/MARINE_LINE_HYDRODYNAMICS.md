# Coupled line hydrodynamics — development, unqualified

`anyloads.marine_line.LineHydrodynamics` stores explicit constant normal and
tangential drag, added-mass (Ca) and fluid-inertia (Cm) coefficients and drag
diameter. `line_morison_force` returns lump forces and analytic partials. No Cm
default is inferred from Ca: a model author must declare the intended pressure
gradient/inertia convention. This follows the standard cross-flow split in
[OrcaFlex's public line theory](https://www.orcina.com/webhelp/OrcaFlex/Content/html/Linetheory,Hydrodynamicandaerodynamicloads.htm).

For unit current segment axis t, Q=ttᵀ and P=I−Q. Relative velocity is the combined
prescribed wave/current velocity minus structural velocity. Normal drag is
½ρCd_n Dℓ |P u_rel| P u_rel; tangential drag is
½ρCd_t πDℓ |Q u_rel| Q u_rel. Fluid inertia is
ρV(Cm_n P+Cm_t Q)a_fluid, and structural added-mass force is
−ρV(Ca_n P+Ca_t Q)a_structure. Fluid acceleration retains the public environment's
fixed-spatial partial-time convention. There is no second current-force term.

Each segment contributes two endpoint lumps: ℓ is half its **current** length,
V is half its **reference** displaced volume. Adjacent segment axes stay separate
at a bent node. Reference structural mass and submerged weight remain owned by
the existing mechanics assembler; the hydrodynamic primitive adds no buoyancy.
Line hydrodynamics assume exclusion from BEM. A mooring line and a rigid Morison
member may not share a persistent physical ID; `mooring:` contribution IDs are
reserved for diagnostics when a mooring assembler is present.

Set `MooringLine.hydrodynamics` to one immutable section per segment and supply
an explicit public `AiryEnvironment` to `MooringLineAssembler.environment`.
Density, still-water level and selected nonzero gravity must agree. Only fully
submerged centerlines inside the environment domain are admitted. The inner
serialization API is `marine_mooring_hydrodynamics_v1`; old mechanical-only line
data remain `marine_mooring_v1`. The new version cannot be stripped without
schema refusal. Model/result body and node layout remains unchanged.

The sparse assembler composes force partials with fluid spatial gradients,
current-length and unit-axis derivatives, then the public endpoint work map.
Body kinematic/geometric corrections use the total endpoint mass/damping/force.
The common Newmark/Newton driver reevaluates at the immutable actual step time
and counts added mass once in both consistent initialization and the effective
mass operator. Separate normal drag, tangential drag, fluid inertia and structural
added-mass components sum to the actual force. `relative_drag_power` is relative
fluid-to-structure dissipation. `added_mass_kinetic_energy` is an instantaneous
diagnostic, included in total line kinetic energy; orientation-dependent mass
must have its orientation power accounted for before claiming conservation.

Development checks cover independent force derivatives on all finite body/node
columns, closed-form projected drag/mass, short coupled trajectories, force sums,
step-time forcing, immutable serialization and ownership/domain refusals.
They do not establish W6 acceptance. Partial wetting, seabed contact/friction,
staged coupled static equilibrium, catenary/mesh/time refinement, full-six BEM
source admission and independent scientific qualification remain incomplete.
ANYmarine admission of the new hydro input schema is a subsequent application
slice; the existing mechanical mooring example remains supported.

# Native distributed Morison development route

API `marine_morison_development_v1` is an unqualified engineering candidate.
It implements the adopted ANYmarine prescribed external-force contract; it does
not establish W3/W4 scientific acceptance, source exclusion or release readiness.
Optional dependency: the tested ANYloads marine API (`marine-morison` extra).
Dry models and base solver imports do not require ANYloads, Qt or Capytaine.

`MemberEndpoint` binds a persistent body id and BODY point. `MorisonMember`
binds two endpoints, the public ANYloads `MorisonSection` and
`HydrodynamicOwnership`, and a Gauss order from 2 through 16 (default 4).
Both endpoints may belong to one rigid body or different bodies. The resulting
straight member interpolates their point velocities and physical accelerations.
It is a load carrier; it introduces no structural stiffness or axial constraint.

`MorisonMemberSetContribution` binds canonical model bodies, immutable members
and an ANYloads `AiryEnvironment`. Its time comes from immutable
`StepInformation`; untimed evaluation is refused. Gravity is selected separately
through the native model. Named `morison_members_development` model serde stores
the actual wave component phases/current profile/section/ownership/attachments
and quadrature controls; it cannot load arbitrary code or erase subclass physics.
Model and contribution owner refuse repeated physical member ids, even across
different provider ids. A stateless provider refuses unexpected committed history.

The density law is evaluated by ANYloads: transverse Froude–Krylov inertia,
transverse relative added inertia and one combined wave/current relative drag.
Fluid acceleration is fixed-spatial Eulerian partial time derivative. The
structural acceleration contains chart/geometric bias exactly once. This
prescribed law adds no variational kinetic-energy or empirical inertia terms.
Potential-flow ownership permits drag-only correction. Duplicate full inertia,
drag or buoyancy declarations are refused by the owning ANYloads record.

The admitted wetting approximation is flat still water/bed with wet centreline
clipping and nominal full circular section. It does not describe partially wet
circular sections, wave stretching, water entry/slamming or seabed contact.
Gauss intervals split at wet limits and current-profile knots. Open nodes stay
inside each active interval. Horizontal segments on a boundary are inclusively
wet; exact endpoint/plane and horizontal/plane events are reported. No smoothness
claim is made at a wet-topology transition.

Quadrature parameters, moving parameter derivatives, weights and weight
derivatives are array batches. Force evaluation and integration use array
contractions, without Python records or loops per Gauss point. Boundary/interval
and member metadata remain outside that requirement. Endpoint follower tensors
are contracted before broadcasting, avoiding a points-times-layout-squared
temporary. This describes the implemented data path, not measured performance.

The external covector is the weighted integral of `J(s).T f(s)`. Total analytic
`K=-dQ/dq`, `C=-dQ/dqdot` and `Ma=-dQ/dqddot` include both endpoint charts,
finite rotations, follower axes, length weights, fluid spatial gradients,
structural acceleration bias and moving wet/profile integration boundaries.
Moving quadrature parameters change derivative sampling locations, without
redefining a material point's physical velocity or acceleration. Diagnostics
store per-member covectors, component/drag-attribution sums, wet lengths,
branch events, relative drag power, ownership and effective quadrature controls.

Focused development tests use analytic uniform-current force/mass, vertical
Airy-force integrals, moving bed/SWL buoyancy, physical endpoint reactions and
virtual work; finite differences check q/v/a derivatives for fixed finite-rotation
one-body and cross-body cases. Native checks are limited to three steps and
cover initial added mass, synthetic coupled-fluid plus Morison/drag correction,
stateless history, rechart and cancellation. These tests do not validate arbitrary
quadrature resolution or full rotating-axis energy/free-decay mechanics. The
existing full scientific/legacy gates and independent assessment remain pending.

ANYmarine now persists the optional native member/environment declaration, admits
it through this public compiler, edits existing numeric values, runs an isolated
worker and displays member centrelines with producing-snapshot body transforms.
The standalone wave preview has separate inputs and does not configure these
mechanical forces. Real BEM mesh omission
and equilibrium/buoyancy ownership evidence remain required before source admission.
Evidence is in `C:/ANYworkspaceWork/anymarine-evidence/morison-native-*`; the
single living plan/checkpoint stays in `C:/Github/ANYmarine/TASK.md`.

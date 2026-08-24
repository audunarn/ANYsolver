# ANYsolver finite-element solver

`anysolver` is a headless structural FE solver for beam,
shell, stiffened-panel, and cylindrical-shell analysis. It is an engineering
solver with an explicit qualification scope, not a general-purpose CAD,
contact, or fracture platform.

Install the released package with:

```powershell
python -m pip install ANYsolver
```

For coordinated local development across sibling repositories, install the
checkouts first:

```powershell
python -m pip install -e C:\Github\ANYmaterial
python -m pip install -e C:\Github\ANYmesh
python -m pip install -e C:\Github\ANYfileIO
python -m pip install -e C:\Github\ANYsolver
```

### Release order for the 0.3 line

ANYsolver 0.3 depends on compatible extracted packages. Publish them to the
same target index in this order:

1. `ANYmaterial` and `ANYmesher` (either order).
2. `ANYfileio`, which depends on both.
3. `ANYsolver` 0.3.x, which depends on all three.

Apply that order separately to TestPyPI and PyPI. The compatible sibling
releases are available on PyPI. The publish workflow checks the selected
target index and refuses to build or upload ANYsolver unless
`ANYmaterial>=0.1,<0.2`, `ANYmesher>=0.1,<0.3`, and
`ANYfileio>=0.1,<0.3` can already be resolved there. CI also uses pinned sibling
source checkouts to exercise the exact compatibility graph.

ANYsolver uses the neutral mesh, panel-generation, quality, and section APIs
available in ANYmesher 0.1 and retains compatibility with the additive 0.2
line. The strict `<0.3` cap prevents an unqualified major contract change.
The endpoint compatibility job exercises pinned 0.1.0 and 0.2.1 installed
wheels on Windows AMD64 CPython 3.13; that focused job is not a wider platform
or interpreter qualification claim.

Core analyses and the solver-owned generated-geometry workflow are available
directly from `anysolver`; the lightweight normalized flat-panel and cylinder
facade is exposed through `anysolver.runtime`:

```python
from anysolver import (
    FEModel,
    GeneratedGeometryFEMConfig,
    LoadCase,
    run_generated_geometry_fem,
    solve_linear,
)
from anysolver.runtime import (
    LightweightFEMConfig,
    resolve_runtime_analysis,
    run_production_fem,
)
```

The runtime facade applies its normalized axial force, bending moment, shear
force, torsional moment, and pressure inputs to the generated model. Set
`LightweightFEMConfig.follower_pressure=True` only for nonlinear static or
arc-length analysis using the `static only` or `nonlinear static` runtime
path; incompatible linear, stepwise eigenvalue-buckling, transient, collision,
and structured-capacity paths return an explicit `invalid_follower_pressure`
status. Arc length retains the requested von Karman or corotational
kinematics. Production runtime failures remain failures rather than being
replaced by an estimator.

Application integrations should use `resolve_runtime_analysis(config)` to
reflect the solver's effective nonlinear/material/control/kinematics choices;
the normalization helpers with leading underscores are implementation details.

The generic `GeneratedGeometryFEM*` names are the preferred workflow API.
Historical `AnyStructureFEM*` aliases remain available only for downstream
compatibility. Material selection is owned by `ANYmaterial`; the root-level
`dnv_c208_steel_properties()` and `dnv_c208_steel_curve()` names are temporary
compatibility imports over its canonical table and validation.

The source code and tests are authoritative. Generated reports under
`reports/` are dated evidence snapshots and must be regenerated after solver
changes before making release claims.

## Functional overview

Production four-node shell selectors use the qualified E4-PL formulation by
default. TRI3, TRI6, Q8, and Q8R remain on their established implementations.
The explicit legacy-Q4 rollback is deprecated during the 0.4.x burn-in and is
scheduled for removal no earlier than 0.5.0; see
[the E4-PL migration guide](docs/E4_PL_MIGRATION.md) for diagnostics, rollback,
and release gates.

| Area | Implemented functionality |
| --- | --- |
| Model | Six DOFs per node; SI units; materials, density, nodal mass, shell/beam topology, supports, and MPC constraints. `audit_constraints()` reports equation provenance, feasibility, structural rank, dependency depth, and independent DOFs before assembly. |
| Materials | Constitutive objects, elastic reductions, Hill-48 yield data, and DNV curves come from `ANYmaterial`; ANYsolver owns their use in element integration and nonlinear solution. Orthotropic shells support material direction/angle and Hill-48 plasticity; orthotropic beams use local material axes and an explicit section torsional rigidity. |
| Shells | 3- and 6-node triangles; 4-node MITC-style and 8-node Mindlin-Reissner quadrilaterals; isotropic, rotated orthotropic, or pre-integrated generalized `A/B/D/As` section stiffness. Generalized sections retain membrane-bending coupling and recover exact strains/resultants without inventing ply stresses. |
| Beams | 2-node and straight-sided 3-node Timoshenko beams with axial, biaxial bending, direction-dependent shear, torsion, consistent/lumped mass options, geometric stiffness, optional fiber-section plasticity, or a fully coupled local 6x6 generalized section law. |
| Coupling | Coincident or eccentric beam-shell kinematics through explicit interpolated MPC transformations. |
| Loads | Nodal force/moment, dead or current-area follower shell pressure, in-plane edge loads, acceleration/gravity, prescribed displacement, load combinations, proportional and staged nonlinear loads. Follower pressure includes its exact, generally nonsymmetric external-load tangent. |
| Linear analysis | Static single- and multiple-RHS solves, reactions and MPC-force diagnostics, free-free rigid-body nullspace handling, sparse factorization reuse, and post-solve affine-constraint residual checks. |
| Modal and mass | Consistent mass assembly, point masses, model mass/inertia properties, constrained and free-free vibration modes. |
| Buckling | Linear eigenvalue buckling for beam axial force and shell Mindlin initial-stress resultants, including sparse shift-invert and repeated-mode diagnostics. A follower-load stiffness can be included when its constrained tangent is symmetric; a general nonsymmetric follower eigenproblem is outside scope. |
| Nonlinear static | Incremental Newton solution, adaptive stepping, force or displacement control, dead or follower pressure, von Karman or opt-in corotational kinematics, rotated or consistent corotational tangent, layered shell J2 or orthotropic Hill-48 plasticity with safeguarded local solves and consistent tangents, beam fiber plasticity, stage-boundary commits, true preload/restart displacement control, and simplified element erosion. |
| Continuation | Bounded Crisfield-style spherical arc-length tracing through a first limit point and a guarded descending branch, including current-area follower pressure and its load tangent. |
| Dynamics | Newmark or HHT-alpha implicit transient response, Rayleigh damping, prescribed shell pressure patches, selected/envelope history storage, and memory preflight. |
| Impact/contact | One rigid sphere with frictionless penalty contact against shells and opt-in beam-axis segments; event substepping, Aitken relaxation, nonlinear material response, and engineering damage/erosion options. |
| Imperfections | Stress-free eigenmode, member-bow, plate-wave, flange-twist, explicit, and composite imperfection fields. |
| Initial fields | Element-local shell membrane/bending stress or membrane/curvature prestrain, arbitrary configured beam-fiber stress/prestrain distributions, zero-external-load equilibration, admissibility checks, and provenance kept separate from geometric imperfections. |
| Workflows | Normalized generated geometry to static/prestress/buckling; traceable static-to-buckling-to-imperfect nonlinear-capacity workflow. |
| Interchange | `ANYfileio` owns SESAM/CalculiX parsing, validation, neutral semantics, and guarded writing. ANYsolver retains only neutral-record-to-`FEModel` adapters and the legacy compatibility imports introduced for the 0.2 line. |
| Results | Result provenance; unified elastic or committed shell-layer/beam-fiber stress recovery; Gauss-point membrane-force and bending-moment resultants for generated-geometry prestress; guarded Zienkiewicz-Zhu-style patch recovery for qualified shell neighborhoods; selected recovery; reaction filtering; validation diagnostics; deterministic baselines; benchmarks; and generated qualification reports. |
| External verification | Reproducible CalculiX model flattening, opt-in isolated execution, solver provenance, and tolerance-controlled analytical comparison, using `ANYfileio` for deck writing and FRD/DAT parsing. Deck-only reports remain explicitly `not_executed` and make no numerical-agreement claim. |

`StructuralMaterial` is a runtime-checkable, ANYmaterial-owned protocol containing
`name`, `density`, `elastic_symmetry`, and
`elastic_compliance_matrix()` in engineering Voigt order
`[11, 22, 33, 23, 13, 12]`. `FEModel.register_material()` accepts compatible
external objects through that contract;
`FEModel.add_orthotropic_material()` constructs the canonical
`OrthotropicMaterial`.

ANYmesher owns neutral mesh topology, numbering, quality and coupling records;
this package converts them into solver elements and exact constraints.
ANYfileio owns SESAM and CalculiX syntax; this package converts neutral records
to FEModel objects and retains execution and validation evidence.

Every production solver uses the same fixed/MPC preflight. Invalid or cyclic
systems fail before assembly or factorization. Linear, modal, buckling,
nonlinear, arc-length, transient, and impact results include a normalized
constraint residual diagnostic. Modal and buckling modes correctly verify the
homogeneous variation equations when the base model has prescribed offsets.

`ResourceConfig(solver_threads=N, assembly_threads=M)` now applies scoped
native and Numba limits. Native pools are restored even after exceptions, and
parallel Numba assembly suppresses nested BLAS/OpenMP pools to one thread.
Diagnostics record requested limits, active runtime pools, the selected sparse
backend, and any limiter/backend fallback. Omitting the resource policy retains
the backend's existing unrestricted default.

`GeneralizedShellSectionProtocol` and `GeneralizedBeamSectionContract` are
likewise solver-owned structural interfaces. The built-in
`GeneralizedShellSection(A, B, D, As, ...)` accepts pre-integrated laminate or
homogenized shell stiffness, while `GeneralizedBeamSection(stiffness, ...)`
accepts a coupled 6x6 sectional law. They may be attached directly to elements
or supplied inline/by name through generated geometry. Optional section mass
data override the legacy homogeneous mass construction; otherwise the attached
material, thickness, and legacy section geometry continue to define mass.

For shells, `material_direction` is projected into the shell plane and then
`material_angle_deg` is applied right-handed about the positive shell normal;
without a direction, the angle starts at shell-local x. For beams, material
axes 1/2/3 are beam-local x/y/z. Orthotropic beam sections must provide a
positive `cross_section["torsional_rigidity"]` in N*m^2; isotropic beams retain
`G*J`.

Implemented does not automatically mean qualified for every geometry or load
regime. The live capability matrix is produced by
`write_production_readiness_artifacts()` and the verification manifest.

## Production scope

The qualified target is thin flat or cylindrical shell structure, with beam
stiffeners/girders represented through the documented coupling, inside the
verified mesh, material, distortion, eccentricity, and load ranges.

Important limits:

- no arbitrary CAD topology or automatic general-purpose meshing;
- no arbitrary 3-D anisotropic material law, ply-stack integration, ply stress
  recovery, tension/compression-asymmetric composite failure, or progressive
  composite damage. Pre-integrated linear shell `A/B/D/As` and beam 6x6
  section laws are supported, including their elastic couplings;
- Q8R is experimental: its hourglass stabilization is not qualified for thin
  bending and it is deliberately excluded from nonlinear batch acceleration;
- the 3-node quadratic beam is straight-sided; curved members must be
  represented by straight beam segments until a true curved formulation is
  implemented;
- the shell initial-stress operator covers the in-plane `N`, `M`, and `H`
  stress moments acting on Mindlin midsurface translations and director
  gradients; it does not add drilling, transverse-normal-stress, or a
  geometrically exact finite-rotation shell/director formulation;
- current-area follower pressure is supported in nonlinear static and
  arc-length analyses, with its exact load tangent. Linear/dead pressure
  remains the default. Linear buckling rejects a constrained nonsymmetric
  follower-pressure pencil because general complex nonconservative
  eigenanalysis is not implemented;
- no general shell-shell, body-body, frictional, rolling, or self-contact;
- no fluid-structure interaction, cavitation, or water-entry model;
- no cohesive cracks, remeshing, material separation, or fracture-mechanics
  claim—the erosion models are engineering screens;
- no unrestricted deep post-buckling or automatic bifurcation branch switching;
- the consistent corotational tangent includes frame derivatives and is
  selected automatically for follower pressure, but its numerical
  frame-sensitivity evaluation is costlier than the rotated tangent used by
  default for ordinary corotational solves;
- material-history-aware recovery requires retained, matching committed
  nonlinear layer/fiber states; missing or invalid state is reported and the
  affected components fall back explicitly to elastic reconstruction;
- for legacy isotropic plastic histories, `von_mises` retains the established
  return-mapped shell in-plane or beam-fiber scope. Orthotropic results keep
  `von_mises` as the conventional invariant of the physical stress, including
  matching elastic transverse shear/torsion reconstruction, while
  `equivalent_stress` and `hill_utilization` remain explicitly scoped to the
  Hill-return-mapped components. `mixed_reconstruction_von_mises` and recovery
  provenance identify that mixed constitutive scope;
- the guarded patch-recovery fit is qualified only for locally planar,
  consistently oriented, homogeneous, full-integration Q4 or Q8 shell
  neighborhoods. Discontinuities remain separate, and the optional normalized
  stress-L2 discrepancy is a diagnostic—not an energy-norm error estimate;
- initial stress/prestrain fields are qualified only in element-local reference
  coordinates with `kinematics="von_karman"`. Shell fields use the documented
  membrane/positive-face-bending convention, and beam fields require a
  configured fiber section. Input stress must be admissible for the supplied
  hardening state; equilibration may redistribute it and does not reconstruct
  the manufacturing history. A field-bearing restart also requires its
  matching converged displacement vector;
- the analytical plane-stress tangent is branch-consistent. The numerical
  derivative remains an oracle and automatic invalid-row fallback; local
  yield-residual nonconvergence fails closed;
- no unverified material laws or distortion ranges;
- orthotropic and generalized-section shells use the general
  element/nonlinear paths and report deterministic fallback diagnostics;
  generalized beams use the general element path, while the existing
  accelerated shell kernels remain isotropic homogeneous-section only;
- generalized-section recovery is resultants-only. CalculiX export rejects
  these sections because the current deck mapping cannot preserve their
  coupling; use analytical or a dedicated section-capable reference model;
- SESAM `FEModel` export remains outside the supported interchange gate;
- CalculiX comparison requires a compatible local executable and an explicit
  execution request. Deck generation alone is a reproducibility handoff, not
  external numerical evidence.

Use `validate_production_model()`, the analysis-specific preflight checks, and
the generated production-scope artifacts before production use.

## Documentation map

- [`ARCHITECTURE.md`](docs/ARCHITECTURE.md): package boundaries, analysis flow, and
  invariants.
- [`THEORY.md`](docs/THEORY.md): implemented formulations and validity limits.
- [`ARC_LENGTH.md`](docs/ARC_LENGTH.md): continuation controls and use.
- [`NONLINEAR_PERFORMANCE.md`](docs/NONLINEAR_PERFORMANCE.md): nonlinear assembly,
  sparse backend, threading, and diagnostics.
- [`QUALITY_CONTROL.md`](docs/QUALITY_CONTROL.md): verification commands, evidence
  hierarchy, and current checked status.
- [`reference_cases/README.md`](docs/reference_cases/README.md):
  local CalculiX/PrePoMax reference-case layout.
- [`MIGRATION.md`](MIGRATION.md): source provenance, inclusion boundary, and
  import changes.
- [`extract_mat_mesh_io_performance_review.md`](reports/extract_mat_mesh_io_performance_review.md):
  current extraction, assembly, nonlinear, MPC and buckling performance evidence.
- [`femaster_adoption_review.md`](reports/femaster_adoption_review.md): clean-room
  FEMaster concept review, constraint/thread implementation, and the gated CSR
  prototype measurements.

## Basic verification

From the repository root:

```powershell
python -m pytest tests -q -p no:cacheprovider
python run_qc.py --no-save
python scripts/run_fe_verification.py
```

The last command regenerates the canonical JSON and Markdown evidence under
`reports/verification/`. Its default external-reference mode generates
handoff decks with status `not_executed`; that status is not a pass or a claim
of numerical agreement. To execute the comparisons, provide a compatible
CalculiX executable on `PATH`, through `ANYSOLVER_CALCULIX_EXECUTABLE`, or with
`--calculix`, and run:

```powershell
python scripts/run_fe_verification.py --execute-calculix
```

An external case becomes passing evidence only after isolated execution,
successful FRD/DAT parsing, and every declared comparison meeting its
tolerance.

# ANYsolver finite-element solver

`anysolver` is a headless structural FE solver for beam,
shell, stiffened-panel, and cylindrical-shell analysis. It is an engineering
solver with an explicit qualification scope, not a general-purpose CAD,
contact, or fracture platform.

Install the released package with:

```powershell
python -m pip install ANYsolver
```

For coordinated local development with ANYstructure:

```powershell
python -m pip install -e C:\Github\ANYsolver
```

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
compatibility. Material selection is centralized in
`dnv_c208_steel_properties()` and `dnv_c208_steel_curve()`; the runtime facade
uses the same canonical table and validation.

The source code and tests are authoritative. Generated reports under
`reports/` are dated evidence snapshots and must be regenerated after solver
changes before making release claims.

## Functional overview

| Area | Implemented functionality |
| --- | --- |
| Model | Six DOFs per node; SI units; materials, density, nodal mass, shell/beam topology, supports, and MPC constraints. |
| Shells | 3- and 6-node triangles; 4-node MITC-style and 8-node Mindlin-Reissner quadrilaterals; stiffness, mass, pressure, and stress recovery. The shell initial-stress operator includes membrane, bending, and second stress moments acting through the implemented Mindlin translation/director field. Q8R reduced integration is experimental and outside the qualified thin-bending/nonlinear-batch scope. |
| Beams | 2-node and straight-sided 3-node Timoshenko beams with axial, biaxial bending, shear, torsion, consistent/lumped mass options, geometric stiffness, and optional fiber-section plasticity. |
| Coupling | Coincident or eccentric beam-shell kinematics through explicit interpolated MPC transformations. |
| Loads | Nodal force/moment, dead or current-area follower shell pressure, in-plane edge loads, acceleration/gravity, prescribed displacement, load combinations, proportional and staged nonlinear loads. Follower pressure includes its exact, generally nonsymmetric external-load tangent. |
| Linear analysis | Static single- and multiple-RHS solves, reactions and MPC-force diagnostics, free-free rigid-body nullspace handling, and sparse factorization reuse. |
| Modal and mass | Consistent mass assembly, point masses, model mass/inertia properties, constrained and free-free vibration modes. |
| Buckling | Linear eigenvalue buckling for beam axial force and shell Mindlin initial-stress resultants, including sparse shift-invert and repeated-mode diagnostics. A follower-load stiffness can be included when its constrained tangent is symmetric; a general nonsymmetric follower eigenproblem is outside scope. |
| Nonlinear static | Incremental Newton solution, adaptive stepping, force or displacement control, dead or follower pressure, von Karman or opt-in corotational kinematics, rotated or consistent corotational tangent, layered shell J2 plasticity with a safeguarded local solve and analytical consistent tangent, beam fiber plasticity, stage-boundary commits, true preload/restart displacement control, and simplified element erosion. |
| Continuation | Bounded Crisfield-style spherical arc-length tracing through a first limit point and a guarded descending branch, including current-area follower pressure and its load tangent. |
| Dynamics | Newmark or HHT-alpha implicit transient response, Rayleigh damping, prescribed shell pressure patches, selected/envelope history storage, and memory preflight. |
| Impact/contact | One rigid sphere with frictionless penalty contact against shells and opt-in beam-axis segments; event substepping, Aitken relaxation, nonlinear material response, and engineering damage/erosion options. |
| Imperfections | Stress-free eigenmode, member-bow, plate-wave, flange-twist, explicit, and composite imperfection fields. |
| Initial fields | Element-local shell membrane/bending stress or membrane/curvature prestrain, arbitrary configured beam-fiber stress/prestrain distributions, zero-external-load equilibration, admissibility checks, and provenance kept separate from geometric imperfections. |
| Workflows | Normalized generated geometry to static/prestress/buckling; traceable static-to-buckling-to-imperfect nonlinear-capacity workflow. |
| Interchange | Pure-Python SESAM formatted FEM record/document parsing, guarded round-trip writing, supported semantic import to `FEModel`, coordinate transforms, beam orientation, and SIF shell-stress reading by load case. |
| Results | Result provenance; unified elastic or committed shell-layer/beam-fiber stress recovery; Gauss-point membrane-force and bending-moment resultants for generated-geometry prestress; guarded Zienkiewicz-Zhu-style patch recovery for qualified shell neighborhoods; selected recovery; reaction filtering; validation diagnostics; deterministic baselines; benchmarks; and generated qualification reports. |
| External verification | Reproducible CalculiX input generation plus opt-in isolated execution, FRD/DAT parsing, solver provenance, and tolerance-controlled analytical comparison. Deck-only reports remain explicitly `not_executed` and make no numerical-agreement claim. |

Implemented does not automatically mean qualified for every geometry or load
regime. The live capability matrix is produced by
`write_production_readiness_artifacts()` and the verification manifest.

## Production scope

The qualified target is thin flat or cylindrical shell structure, with beam
stiffeners/girders represented through the documented coupling, inside the
verified mesh, material, distortion, eccentricity, and load ranges.

Important limits:

- no arbitrary CAD topology or automatic general-purpose meshing;
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
- with an active plastic constitutive history, `von_mises` covers the
  return-mapped shell in-plane or beam-fiber stress components. Transverse
  shell shear and beam shear/torsion remain elastic reconstructions and are
  exposed separately through `mixed_reconstruction_von_mises`, rather than
  being presented as a hardening-curve-consistent equivalent stress. A purely
  elastic nonlinear state keeps the full mixed elastic value as its primary
  equivalent stress;
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

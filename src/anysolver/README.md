# ANYsolver finite-element solver

`anysolver` is a headless structural FE solver for beam,
shell, stiffened-panel, and cylindrical-shell analysis. It is an engineering
solver with an explicit qualification scope, not a general-purpose CAD,
contact, or fracture platform.

The source code and tests are authoritative. Generated reports under
`reports/` are dated evidence snapshots and must be regenerated after solver
changes before making release claims.

## Functional overview

| Area | Implemented functionality |
| --- | --- |
| Model | Six DOFs per node; SI units; materials, density, nodal mass, shell/beam topology, supports, and MPC constraints. |
| Shells | 3- and 6-node triangles; 4-node MITC-style and 8-node Mindlin-Reissner quadrilaterals; optional Q8R reduced integration with stabilization; stiffness, mass, pressure, geometric stiffness, and stress recovery. |
| Beams | 2-node and 3-node Timoshenko beams with axial, biaxial bending, shear, torsion, consistent/lumped mass options, geometric stiffness, and optional fiber-section plasticity. |
| Coupling | Coincident or eccentric beam-shell kinematics through explicit interpolated MPC transformations. |
| Loads | Nodal force/moment, shell pressure, in-plane edge loads, acceleration/gravity, prescribed displacement, load combinations, proportional and staged nonlinear loads. |
| Linear analysis | Static single- and multiple-RHS solves, reactions and MPC-force diagnostics, free-free rigid-body nullspace handling, and sparse factorization reuse. |
| Modal and mass | Consistent mass assembly, point masses, model mass/inertia properties, constrained and free-free vibration modes. |
| Buckling | Linear eigenvalue buckling for beam axial force and shell membrane-resultant prestress, including sparse shift-invert and repeated-mode diagnostics. |
| Nonlinear static | Incremental Newton solution, adaptive stepping, force or displacement control, von Karman or opt-in corotational kinematics, layered shell J2 plasticity, beam fiber plasticity, staged loads, and simplified element erosion. |
| Continuation | Bounded Crisfield-style spherical arc-length tracing through a first limit point and a guarded descending branch. |
| Dynamics | Newmark or HHT-alpha implicit transient response, Rayleigh damping, prescribed shell pressure patches, selected/envelope history storage, and memory preflight. |
| Impact/contact | One rigid sphere with frictionless penalty contact against shells and opt-in beam-axis segments; event substepping, Aitken relaxation, nonlinear material response, and engineering damage/erosion options. |
| Imperfections | Stress-free eigenmode, member-bow, plate-wave, flange-twist, explicit, and composite imperfection fields. |
| Workflows | Normalized generated geometry to static/prestress/buckling; traceable static-to-buckling-to-imperfect nonlinear-capacity workflow. |
| Interchange | Pure-Python SESAM formatted FEM record/document parsing, guarded round-trip writing, supported semantic import to `FEModel`, coordinate transforms, beam orientation, and SIF shell-stress reading by load case. |
| Results | Result provenance, element and nodal stress recovery, selected recovery, reaction filtering, validation diagnostics, deterministic baselines, benchmarks, and generated qualification reports. |

Implemented does not automatically mean qualified for every geometry or load
regime. The live capability matrix is produced by
`write_production_readiness_artifacts()` and the verification manifest.

## Production scope

The qualified target is thin flat or cylindrical shell structure, with beam
stiffeners/girders represented through the documented coupling, inside the
verified mesh, material, distortion, eccentricity, and load ranges.

Important limits:

- no arbitrary CAD topology or automatic general-purpose meshing;
- no follower-pressure tangent unless separately implemented and verified;
- no general shell-shell, body-body, frictional, rolling, or self-contact;
- no fluid-structure interaction, cavitation, or water-entry model;
- no cohesive cracks, remeshing, material separation, or fracture-mechanics
  claim—the erosion models are engineering screens;
- no unrestricted deep post-buckling or automatic bifurcation branch switching;
- no unverified material laws, residual-stress fields, or distortion ranges;
- SESAM `FEModel` export and external-solver execution/comparison remain outside
  the supported interchange gate.

Use `validate_production_model()`, the analysis-specific preflight checks, and
the generated production-scope artifacts before production use.

## Documentation map

- [`ARCHITECTURE.md`](ARCHITECTURE.md): package boundaries, analysis flow, and
  invariants.
- [`THEORY.md`](THEORY.md): implemented formulations and validity limits.
- [`ARC_LENGTH.md`](ARC_LENGTH.md): continuation controls and use.
- [`NONLINEAR_PERFORMANCE.md`](NONLINEAR_PERFORMANCE.md): nonlinear assembly,
  sparse backend, threading, and diagnostics.
- [`QUALITY_CONTROL.md`](QUALITY_CONTROL.md): verification commands, evidence
  hierarchy, and current checked status.
- [`../tests/reference_cases/README.md`](../tests/reference_cases/README.md):
  local CalculiX/PrePoMax reference-case layout.

## Basic verification

From the repository root:

```powershell
python -m pytest tests -q -p no:cacheprovider
python run_qc.py --no-save
python scripts/run_fe_verification.py
```

The last command regenerates the canonical JSON and Markdown evidence under
`reports/verification/`. External-reference decks are handoff artifacts unless
matching external-solver results have actually been executed and compared.

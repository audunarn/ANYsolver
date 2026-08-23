# Changelog

## Unreleased

## 0.3.0 - 2026-08-23

- Preserve the corrected published-2025 S4 reference, nullspace proof, geometry
  handoff, and qualification scaffold as dormant release evidence. The legacy
  S4 remains the production default and improved-S4 activation remains
  unavailable under the recorded restrictions; no gauge constraint, invented
  stiffness, dispatch route, or activity-policy change is introduced.
- Widen the declared ANYfileio consumer range to `>=0.1,<0.3`, add pinned
  source compatibility cells for the 0.1 and 0.2 public contracts, and align
  the publication dependency gate. Installed-wheel, index-resolver, and
  publication qualification remain separate release gates.
- Widen the declared ANYmesher consumer range to `>=0.1,<0.3`, add CI coverage
  for pinned 0.1.0 and 0.2.1 endpoints, preserve the public neutral panel, mesh,
  quality, and section contract, retain the strict 0.3 cap, and align CI and
  publication dependency gates with the declared metadata.
- Complete the Sol Ultra `performance_2` campaign with qualified static/arc
  persistent nonlinear state transactions, compiled canonical-curve Hill-48 batches,
  orthotropic/generalized S4 kernels, revision-cached corotational block
  transforms, large-selection isotropic S4 recovery, and direct reduced
  elastic nonlinear-impact assembly. Unsupported formulations, curves, state
  layouts, impact plastic/fiber history, small recovery selections, affine
  constraints, and damage/state scopes retain explicit scalar or
  full-coordinate fallbacks with reason diagnostics.
- Add conservative opt-in impact tangent/factorization reuse, compact lazy
  contact records, and revision-guarded incremental damage K/M updates. A zero
  reuse budget remains the full-Newton oracle; contact, convergence, plastic,
  damage, deletion, time-step, and line-search changes force a refresh. Damage
  plan setup is gated by projected future events and retained-memory headroom;
  invalidation returns to the exact rebuild and never scales point masses.
- Add the optional caller-owned `AnalysisSession` for bounded K/M/constraint,
  reduced-matrix, output-row, and factorization reuse across repeated linear,
  modal, buckling, transient, and capacity work. Linear transient loads are
  preprojected once and selected history output avoids full-vector
  reconstruction when recovery does not require it. Explicit solver,
  assembly, and recovery thread scopes remain independently controlled and are
  restored after each call.
- Release 0.2.0 extraction boundary: material behavior now comes from
  `ANYmaterial`, neutral geometry/meshing from `ANYmesher`, and SESAM/CalculiX
  parsing and writing from `ANYfileio`. ANYsolver retains solver-specific
  FEModel adapters, MPC elements, boundary interpretation, external execution,
  comparisons, and the 0.2.x legacy import facades. Deterministic FE baselines
  remain unchanged.
- Add dependency-free generalized section contracts: pre-integrated shell
  `A/B/D/As` with membrane-bending coupling and optional areal inertia, plus a
  coupled beam 6x6 stiffness and optional mass-per-length law. Generated
  geometry accepts inline or named definitions; recovery exposes exact
  generalized strains/resultants, nonlinear shell acceleration falls back
  deterministically, and unsupported CalculiX/fiber/plastic mappings fail
  closed.
- Add a dependency-free structural material contract and homogeneous
  orthotropic engineering materials for shells and beams. This includes
  projected shell material directions/angles, explicit orthotropic beam
  torsional rigidity, generated-geometry and CalculiX shell interchange, and
  deterministic fallback from isotropic accelerated kernels to general
  assembly.
- Add material-axis Hill-48 shell plasticity with directional-strength
  hardening, consistent tangent plus numerical oracle/fallback, stored physical
  stress recovery, labelled Hill equivalent stress/utilization, orthotropic
  beam-fiber longitudinal yielding, and damage/contact integration. General
  anisotropy, laminates, ply failure, and shear/torsion plastic interaction
  remain outside scope.
- Add an exact constant-stress analytical/CalculiX orthotropic S4 reference
  deck, perfect-plastic Hill behavior when no hardening curve is supplied, and
  current-strength Hill utilization with physical-stress recovery provenance.

## 0.1.3 - 2026-07-28

- Complete the generated-geometry runtime bridge: apply configured shear force
  and torsional moment, pass current-area follower pressure only to supported
  nonlinear static/arc-length paths, retain the selected corotational
  kinematics in arc length, and fail closed for incompatible follower paths.
  Runtime prestress recovery now consumes matching committed nonlinear
  histories and exposes Gauss-point membrane/bending resultants plus recovery
  provenance.
- Correct nonlinear display recovery so plastic-history von Mises values use
  only the return-mapped shell in-plane or beam-fiber components, while purely
  elastic nonlinear states retain their full equivalent stress. Preserve
  combinations with elastically reconstructed transverse shear/torsion as a
  separately labelled model-scope diagnostic.
- Add the public `resolve_runtime_analysis()` contract so application GUIs can
  reflect normalized nonlinear/material/control/kinematics selections without
  importing private runtime helpers.

## 0.1.2 - 2026-07-28

- Add opt-in executable CalculiX reference validation with isolated case runs,
  stale-output protection, timeouts, solver version/hash provenance, ASCII
  FRD/DAT parsing, tolerance-controlled comparisons, and preserved evidence
  semantics. Deck-only generation remains explicitly `not_executed`; stale
  non-executed legacy reports are regenerated deterministically, while invalid
  executed evidence is preserved and rejected for diagnosis.
- Add current-area follower pressure and its exact, generally nonsymmetric
  external-load tangent to nonlinear static and arc-length solves. Extend
  shell initial-stress stiffness to the Mindlin translation/director field
  using membrane, bending, and second stress moments, and add the qualified
  thin-ring pressure-buckling gate.
- Add an opt-in consistent corotational tangent through the full
  pull-back/frame/rotate-forward chain rule. `auto` retains the lower-cost
  rotated tangent for ordinary loads and selects the consistent tangent for
  follower pressure.
- Unify nonlinear stress recovery around committed shell-layer and beam-fiber
  histories, matching solution displacements, objective corotational frames,
  component-level provenance, and explicit elastic fallbacks. Add guarded
  full-integration Q4/Q8 patch recovery that separates discontinuities and
  labels its optional surface-stress L2 indicator as non-energy-norm.
- Add shell membrane/bending stress and prestrain fields plus beam-fiber
  initial fields, with zero-load equilibration, immutable field provenance,
  exact load-stage boundary commits, and persistent plastic history through
  multi-stage displacement control.
- Replace the default finite-difference plane-stress algorithmic tangent with
  the analytical consistent derivative of the discrete return map. Retain the
  representable-step numerical tangent as a qualification oracle and guarded
  invalid-row fallback, add a safeguarded local consistency solve with
  fail-closed residual checks, and add constitutive and full-Newton
  parity/performance evidence.
## 0.1.1 - 2026-07-25

- Correct the layered-shell membrane/bending coupling tangent and keep the
  accelerated plastic shell path consistent with the scalar return mapping.
- Fail closed for curved B3 members, experimental Q8R qualification, unsupported
  DNV-RP-C208 thickness rows, and path-dependent staged displacement control.
- Include point masses in reported mass properties, make buckling constraints
  call-order independent, and correct CalculiX gravity export.
- Remove quadratic model-construction and beam/shell coupling lookup scaling,
  safely reset precomputed incoming elements, cache recovery operators and
  topology signatures, defer optional acceleration imports, and use lower
  PyPardiso thresholds only for compatible retained patterns.
- Preserve straight-sided B3 midpoint geometry through adaptive cylinder
  refinement and reconstruct complete elastic layer states after accelerated
  nonlinear solves.
- Add explicit runtime exports, generic generated-geometry API aliases, and
  package-root arc-length exports.
- Adopt the pure-solver test files from ANYstructure (triangular shell
  backend, local patch transition, geometry panel).

## 0.1.0 - 2026-07-22

- Transfer the qualified beam/shell solver from ANYintelligent into its own package.
- Add the headless runtime meshing and analysis facade formerly embedded in ANYstructure.
- Publish the Python import namespace as `anysolver` without a legacy `fe_solver` shim.
- Preserve SESAM interchange, verification, qualification, benchmark, and baseline workflows.

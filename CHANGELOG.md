# Changelog

## Unreleased

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

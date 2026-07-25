# Changelog

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

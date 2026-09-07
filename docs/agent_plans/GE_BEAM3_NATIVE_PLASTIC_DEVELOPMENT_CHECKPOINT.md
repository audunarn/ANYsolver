# GE-B3 native retained-plastic development checkpoint

## Status and authority boundary

The directed-hardening cell now has an immutable private runtime port and a
native retained-resultant beam potential. Two curved macros pass a seven-step
plastic loading/unloading/reversal funnel at section contrasts 1 and 1e12.
This is development evidence, **not production qualification**. Independent
review is **PENDING**. B2/B3, Q4/S3, the accepted straight-only GE-B3 route,
public aliases, defaults, releases, and historical failures remain unchanged.

Base: `d90cad2e319a60a8984f750ec99779aba7127399`, tree
`fc8978e4fc2866167b717a6da9590c86badd437e`.
Private ID: `CANDIDATE_GE_BEAM3_RETAINED_DIRECTED_PLASTIC_V1`.

## Implementation

- `_ge_beam3_station_resultant_cell.py`: private port of the verified research
  constrained station-resultant conjugate. Uses standard-library Decimal,
  no research imports, immutable captured coefficients and origins. The
  response is byte-identical to the research implementation in port tests,
  including paired-history continuation.
- `_ge_beam3_retained_plastic.py`: `Pi(q,p;origin)=p.k(q)-Psi*(p;origin)`.
  It retains all 18 external DOFs, six cell rotations, six cell forces, and
  twelve endpoint moments per macro. Objective kinematic equations and their
  analytic first/second variations are unchanged from the elastic retained
  operator. There is no nested local condensation. Compatibility includes
  both gradient parts; compliance low parts are exposed as `hessian_low`.
  Recovery returns high/low physical fields, paired plastic history, frames,
  and formulation provenance. No fibre stresses or mass are fabricated.
- The two-macro research driver reuses only standalone capture, DOF/support
  layout, and geometric advancement from the elastic context. It never uses
  that context's elastic assembly, recovery, checkpoint, or restore for
  plastic state. It keeps origins fixed across Newton trials, validates
  final-state replay from those origins, and publishes proposed mechanical
  and material state together only after equilibrium/compatibility pass.

The cell backend is bounded to 60-second cooperative compilation/response
checks and 32 active-set updates. The tiny global probe has a 120-second
cooperative deadline, bounded Newton/backtracking, and model identity guards.
These are not formal process-tree watchdogs. No resource request was consumed;
all runs were small correctness tests, not benchmarks or large-model tests.

## Separate test inventories

- Operator first: 13 passed, 1 failed, 4.100 seconds. The high-contrast test
  incorrectly assumed elasticity: 15 stations genuinely yielded. The old
  elastic-only operator correctly rejected it. That behavior remains an
  explicit regression; a separate high-yield fixture checks the elastic limit.
- Operator corrected fixture: 15 passed, 4.018 seconds.
- Force first: 2 failed before mechanics, 1.648 seconds. The test fixture's
  material registry still owned the replaced elements' old sections. The
  ownership guard correctly rejected it; only fixture registration was fixed.
- Force corrected fixture: 2 passed, 6.667 seconds.
- Final development cycle A: 20 passed, 11.243 seconds, no skips.
- Final development cycle B: 20 passed, 11.283 seconds, no skips.

The final cycles contain 18 byte-identical JSON pairs. Coverage includes
native/research port equality, paired-history continuation, full potential
directional residual/tangent checks, symmetry, finite rigid-motion objectivity,
recovery, elastic limiting behavior, genuine plasticity, immutable response
arrays, rejected inputs, two-macro load reversal, and commit-point interruption.
Recovered original section equations, station compatibility, forces, curvature,
plasticity, and work are checked at every accepted step.

Targets are `(0.25,0.5,1,0.5,0,-0.5,0)` with tip-force pattern
`(0.4,-0.005,0)`. Both contrasts complete all seven targets. The largest
observed equilibrium/compatibility norm is `2.6373267283388525e-12`, below
the unchanged `1e-11` gate. Newton uses four or five iterations per target.
This small funnel does not prove mesh convergence, locking freedom, general
plastic material parity, arbitrary load paths, or postbuckling qualification.

Archive: `C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-native-plastic-development-20260907-f735654c1c60`.
70 content files, 4,345,071 bytes; manifest 11,213 bytes, SHA-256
`2b8ac8e84a487428e011a2d300793325847db0170578e63fe4b5724490e8feca`.
The canonical development record binds the source files, inventories, and
paired-output hashes. Initial test failures and original pytest outputs remain.

## Next step and unresolved work

Implement a model-bound native retained-plastic state/controller, preserving
the distinction between each accepted increment's origin and proposed final
history. A restart must bind both, reject foreign/rehashed malformed state,
and reproduce final-state recovery without applying plasticity twice. Do not
reuse or silently translate the historical V5 or elastic-retained capsules.
Keep global commit atomic and test cancellation, rejected steps, cutback,
load reversal, restart continuation, and model/material mutation.

The research driver is not that production state controller. Full objective
nonlinear/fibre section protocols, loads and load tangents, modal/prestressed
modal/buckling/postbuckling parity, broad straight/curved/slenderness campaigns,
installed-wheel checks, independent review, and objective eccentric/curved
beam-shell connections are still outstanding. No default activation or
qualification claim is authorized by this checkpoint.

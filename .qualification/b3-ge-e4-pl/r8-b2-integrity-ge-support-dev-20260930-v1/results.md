# Installed B2 integrity and matched GE support — development result

The consolidated candidate passes **134/134 installed checks**, two public GE
reference-linear examples, factorization reuse, exact snapshot restoration and
the unchanged **1e-10** equivalent-support role criterion. This is Level-A
development evidence, not M2/M3/F10/F11/F13 or aggregate qualification.

## Changes and interpretation

- Single-Q4 B2 now shares the panel's guarded affine-work projection and
  row-scaled equilibrium/gap checks. Tiny force/moment loads cannot be accepted
  as zero through a fixed unit floor. Typed unrepresentable-work failures are
  preserved; programming errors propagate.
- B2 panel batch inventory owns the original case-ID/load-reference pairs before
  callbacks. Caller coordinate mutation, equivalent signed offsets, rebuilt
  section/geometry/attachment/support dependencies and prescribed-support
  reaction/work checks are covered. Existing panel projection arithmetic is
  unchanged after extraction; this is not a new mechanical operator.
- The new public 16-Q4/8-B3/80-row BL5 strip fixes shell-root poses and beam
  nodal root components0..4. Normal spin is free. Beam supports carry ground
  reactions; they are not concentrated endpoint transfer into the shell.
- One own-factor compensated-residual correction resolves the v6 retained-force
  and multiplier precision failure. The optional second correction and physical
  gates remain bounded and unchanged. The corrected public solution matches
  the independently saved root-tie counterfactual in nodal, retained rotation,
  retained resultant and weak-multiplier roles, each below1e-10. No private
  oracle factor is used by the public solver. This supports roundoff allocation
  for this check, not physical qualification of either connection law.
- Finite GE solving and checkpoint-restoration bodies are unchanged. Fresh
  reference-linear results may differ in last bits; saved snapshot arrays still
  restore exactly. Added cancellation and typed/programming-failure checks
  preserve generation and accepted bytes, with one cached factor across loads.

## Exact artifact and observed execution

Solver wheel SHA-256:
`942460a11d45ffe3dea3f32cae457f75d7c5ca283a60bce6a8f01041b817fb96`.
Unchanged consumer:
`e3f755fe24f67b99f3e353b5f05461f607d5e9c8feb12d5fb6025689b7bfe49e`.
All386 solver/97 consumer Python modules match source, wheel and site;271 actual
loaded package modules are installed-site imports. See v7 identity/import files.
Python3.14.2, one effective numerical thread, JIT off. Tests took36.39s;
supervised route47.594s,273481728bytes observed process-tree peak RSS. These
are observed check costs, not a benchmark or development-speed claim.

The global pytest temporary-directory cleanup emitted an ignored permission
error after all assertions and process exit0. Raw diagnostic is retained;
foreign/global temporary directories were not altered and tests were not rerun.

## Retained failures and limitations

V1 was built but untested and includes its cache-permission build failure.
V2 failed on irrelevant metadata before testing; v3 failed on a missing isolated
fixture before testing. V4 passed59 tests but its example failed on reused-owner
restoration. V5 failed a harness qualification-enum assertion after the corrected
example completed. V6 completed both examples but failed1e-10 role parity:
retained2.40366e-10, weak multipliers7.75813e-9. V7 passed all134 checks and
public predicates. No earlier full-route failure is relabeled as success.

Manifest, raw versions, byte-verified input ZIPs and four distinct wheel hashes
preserve exact identities. The parent root-tie reference is immutable evidence
in `../r8-bl5-port-boundary-decision-dev-20260930-v1/`.

One extra backsolve plus compensated residual work is incurred per normal GE
reference-linear RHS. Its large-model cost remains unmeasured. Physical torque/
shear/reference agreement, growing-space stability, multiplier selection,
remaining foundations, full consumers/platforms/scale and release stay open.
Formal F03 remains unconsumed. No main merge or publication follows.

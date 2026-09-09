# P5 native integration audit and rotation-chart bridge

Parent `3223440f52530f1015a7daa91f9e72a63d2467d3`, tree
`a55a2f94e7efb80bd4746c90c14fa6e090c928fd`.
The full goal remains a qualified straight/curved production beam plus an
objective beam-shell connection. Research feature coverage is not equivalent
to native integration or qualification. Preserve accepted P3/P4, all P5
evidence, B2/B3/Q4/S3 mechanics and public defaults/aliases.

## Observed integration map

| Requirement | Existing authority/interface | Missing P5 integration |
| --- | --- | --- |
| Finite rotations | `_native_rotation_state.py`: node-shared matrices, generation/token checks | Map each node operator through its element-owned curved material triad; do not exponentiate accumulated coordinates |
| Scalar nonlinear dispatch | `nonlinear_element_evaluation.py`: `evaluate_nonlinear_element` passes an active native view | Private P5 adapter and full `NonlinearStateStore` transaction integration |
| Residual/tangent | P5 mixed/compensated probes return spatial-increment derivatives | Pull back force and Hessian to the solver's committed-base incremental chart |
| Material history | P5 directed-hardening probe with fixed per-station origins; assembly atomic/replay probes | Model-bound native station schema, accepted-origin replay and global state commit; general section adapters |
| Static assembly/line search | `nonlinear_static.py`, `nonlinear_state.py`, `arc_length.py` | Actual P5 scalar calls and accepted/rejected-step tests, including compensated coordinates |
| Mass/modal | Full-inertia and algebraic-trace research pencils | Native mass policy and supported modal assembly; no hidden cell-spin static elimination |
| Prestressed modal/buckling | P5 current tangent/spectral research; `current_state_tangent.py`, `buckling.py` | Qualified current-state route and state identity, not P3 reference Euler authority |
| Recovery/restart | Research station fields and accepted-origin codecs | Native provenance/section recovery and serialization/restart integration |
| Public selection/package | P3 `ge_beam3_element.py` and exact `ge-beam3` selector | Separately qualified P5 formulation/activation; do not overwrite P3 authority |
| Beam-shell connection | Existing P3 joint rejection | Objective finite-rotation shared-rotation/MPC/eccentric attachment qualification |

The current P3 facade explicitly wraps accepted straight P2 mechanics. Its
public authority is limited; it is not the P5 curved/material-history element.
The inherited branch contains eight earlier GE-B3 source additions. This
step itself adds only research bridge, test and audit paths.

## First concrete bridge: fixed native rotation chart

For each node the solver holds committed Vc and varies dtheta in
V=Exp(dtheta) Vc. The actual element frame is Q=V R0,node. P5 supplies spatial
force f and symmetric zero-chart energy Hessian H after local stationarity.
Let A be identity on translations and the spatial left Exp Jacobian on each
nodal rotation block. The force derivative in spatial coordinates is

    Kspatial = H - blockdiag(0, skew(f_rotation)/2).

The solver-chart quantities are

    g = A^T f
    J[:,k] = A^T Kspatial A[:,k] + (dA/dtheta_k)^T f.

Omitting either the BCH correction or the Jacobian derivative is incorrect
away from zero increment. Compute Exp, its first and second variations with
the existing analytic Jet2 kernel; derive A and dA from derivatives of R R^T.
No numerical frame differentiation in the implementation. Directional finite
differences are tests only.

Use the real `NativeRotationStateStore` and its active token, validating it
before and after evaluation. Request the view in explicit connectivity order,
use authoritative trial coordinates/matrices, and keep origins fixed for all
local evaluations. This bridge returns trial station candidates but commits
neither the native store nor material state. No missing origins are fabricated.

Use the preserved compensated local kernel with explicit zero coordinate-low
parts for these ordinary-coordinate tests, retaining local force-accuracy
checks. This does NOT transport nonzero lows through the native store, qualify
fine-mesh accuracy, or supersede the preserved compensated32/onset evidence.
That coordinate-interface gap remains open. Source local solve limits remain
25 updates/64 evaluations and relative rotation/increment guards remain 0.9 pi.

## Verification and boundary

Test analytic chart derivatives, nonzero-increment work/gradient/tangent,
elastic and active-plastic fixed-origin branches, local Schur symmetry,
noncommuting committed rotations, shared native nodes/material triads, and
stale/foreign/discarded-token rejection before mechanics. Compare the same
native trial under different accumulated bookkeeping coordinates. No candidate
field or store/material origin may be silently committed.

These are small compatibility correctness tests, not an independent mechanics
oracle, full solver transaction, native element or qualification wave. No
source/default/API/package changes or resource execution occur. Next must
connect the verified chart and station-state protocol to actual scalar solver
transactions under a private successor identity, then cover the remaining
requirements above. Optional transient extensions do not replace that work.

## Restart-safe checkpoint and measured verification

The preserved unfinished bridge was recovered after restart at the parent
above. Added 21 focused compatibility tests; no existing tracked source,
mechanics, historical test, evidence or authority input was edited.

- Initial focused smoke: 18 passed in 2.35 seconds, before adding the three
  zero-chart/shared-node/local-failure checks. No failures occurred.
- Final small regression: 78 passed in 4.48 seconds, comprising the 21 bridge
  tests plus the existing native rotation store, nonlinear mixed probe and
  compensated mixed probe suites. This is a separate run, not an additive
  count with the earlier smoke.
- Command: Python 3.13 `-B -m pytest -p no:cacheprovider` on
  `tests/test_ge_beam3_curved_p5_native_chart_probe.py`,
  `tests/test_native_rotation_state.py`,
  `tests/test_ge_beam3_curved_p5_nonlinear_mixed_probe.py`, and
  `tests/test_ge_beam3_curved_p5_compensated_mixed.py`, with `-q --tb=short`
  and a fresh external temporary basetemp. All four numerical-library
  thread environment variables were one. No resource request was consumed.
- Shared-node coverage assembles two curved macrocells with element-owned
  material triads, checking one authoritative nodal operator and assembled
  directional work/tangent. It does not qualify a beam-shell joint.
- No tolerance was relaxed. Directional checks use 1e-7; work, symmetry and
  invariant comparisons use the frozen normalized 1e-11 convention.

This is same-author compatibility evidence, not an independent review, an
accepted qualification aggregate, or permission to expose curved/history
mechanics through the public P3 selector. Keep the production gate closed.
Next: a private model-bound station-state adapter through the actual scalar
`NonlinearStateStore` dispatch, testing global acceptance, rejected-step
rollback and accepted-origin replay before extending to solver campaigns.

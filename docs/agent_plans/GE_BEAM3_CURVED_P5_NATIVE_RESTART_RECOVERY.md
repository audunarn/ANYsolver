# P5 native checkpoint continuation and accepted recovery

Parent `e147d5904b185653d38ed8023d3ad881122989ab`, tree
`13ba3f8a4024bfd2839c51e020865124ebaf4bf9`.

## Implementation

Extend the private native-driver candidate through the real
`solve_static_nonlinear(..., emit_restart_checkpoint=True)` and
`restart_checkpoint=...` paths. No replacement continuation driver, solver
monkeypatch, or reclassification of prior evidence is used.

The generic checkpoint normalizer converts dataclasses/arrays to ordinary
JSON and normalizes signed zero. P5 needs exact typed station histories and
accepted-response replay. Its element-owned codec therefore carries the
canonical inner state as ASCII text inside a versioned JSON envelope:
`GE_BEAM3_P5_NATIVE_TYPED_STATE_JSON_V1`. Generic normalization leaves that
text intact. The inner schema reconstructs exact arrays, station/history
dataclasses, finite floats and bounded integers. No payload selects a module,
class, file or callable. The known order and model come from the caller.

Codec bounds: 2 MiB, nesting depth 32, fixed station count/order and exact
keys. Duplicate keys, nonfinite values, noncanonical text, unknown fields,
wrong scalar types, shape/count mismatches and invalid identity are rejected.
Structural encoding is not mechanics acceptance: the model-bound native
validator subsequently replays the accepted solve from its previous origins,
checks the new histories and native pose, and only then permits restoration.
Checksums bind integrity, not authenticity or the complete prior load history.

One production orchestration path changes:
`src/anysolver/nonlinear_restart.py::_state_records` calls an element-owned
serializer only for the exact opt-in native material protocol. Missing or
unsupported serializers fail closed. All non-opted-in elements retain the
existing JSON path. No existing element mechanics or restart schema changes.

The private driver gains a deterministic model descriptor including reference
geometry/triads, section, quadrature, reduction, update, formulation and codec
IDs. Its section descriptor must agree with its actual physical law. Internal
core objects remain outside generic public-attribute serialization. Descriptor
support is not public element factory deserialization or activation.

## Accepted recovery

`recover_native_fields` validates/replays accepted state without advancing
history. It returns ordered station IDs, material strains/resultants, reference
and current frames, lifted current positions, global force/moment components
and explicit formulation/state provenance. Arrays are returned as read-only
copies. The generalized order is `[eps_x, gamma_xy, gamma_xz, kappa_x, kappa_y,
kappa_z]` and `[N, V_y, V_z, T, M_y, M_z]`.

Physical current frames use the recovered cell operator and the registered
reference frame. Current positions use the original objective curved lift,
not a chord substituted for the curved geometry. The current frame transforms
force and moment components; it does not introduce numerical forces into
physical section recovery. The directed-hardening research section supplies
no fibre stresses, so recovery explicitly reports their absence instead of
inventing zero stresses. Every result remains `production_qualified=false`.

## Tests and observed results

The actual curved coupled-plastic case uses two accepted load steps. A split
run stops at load factor 0.5, exports the real solver checkpoint, restores it
into a fresh expected model, and continues to 1.0. It matches uninterrupted
loading byte-for-byte in displacement, typed element state, the complete
canonical solver checkpoint and recovered fields. A fresh Python process
independently repeats the restore/continuation and produces the identical
checkpoint bytes. This is process/determinism verification, not independent
mechanics authorship or general restart qualification.

Other tests cover signed-zero/type preservation, malformed bounded codecs,
mandatory serializer routing, re-sealed mechanical corruption followed by
accepted-origin rejection, read-only recovery, station work conjugacy and
objectivity under a common rigid rotation/translation. The objectivity test
reconstructs the transformed pose from the same fixed material origins; it
does not commit a new material increment or modify the original state.

- Initial native split-continuation smoke: 1 passed in 7.22 seconds.
- Focused restart/recovery suite: 15 passed in 11.48 seconds.
- Final regression: **57 passed in 22.60 seconds** across the new 15 tests,
  13 native-driver/protocol tests, 21 accepted-P3 interface tests and 8 generic
  nonlinear checkpoint tests. Counts from separate runs are not added.
- No test failed and no tolerance was relaxed.

Python 3.13 ran `-B -m pytest -p no:cacheprovider`, `-q --tb=short`, with
OMP/OpenBLAS/MKL/NumExpr each set to one thread and a fresh external temporary
basetemp. The one fresh-process correctness test has a 60-second timeout and
exclusive output creation. Native Newton cases retain at most ten iterations
per step with no load-step cutback retries. No performance/large-mesh/formal
resource request was generated or consumed; no historical run was restarted.

## Boundaries and next work

This is a local, same-author development checkpoint. The private P5 class is
not exported or registered, and the overall straight/curved beam remains
unqualified. Public B2/B3, qualified Q4/S3, P3 mechanics, aliases/defaults,
package versions and historical evidence are unchanged. No push or release.

Still required: broader loading/reversal/cancellation/cutback and control-path
qualification, objective general nonlinear section adapters, native mass and
current-state modal/buckling integration, engineering/locking/postbuckling
gates, package tests and independent review. The preserved onset uncertainty
and coordinate-low interface gap remain open. The objective eccentric/curved
beam-shell connection is still a required, separately unqualified deliverable.
Successful replay of this small native case does not replace any of those gates.

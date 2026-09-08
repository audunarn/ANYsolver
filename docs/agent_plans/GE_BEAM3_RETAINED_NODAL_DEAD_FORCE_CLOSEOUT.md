# Retained nodal dead-force development closeout

Frozen implementation: `1bce83f50770120a5ab84e406c1d5eaa34171304`.
Base: `9a49ea8dc5a6bfc82636f47f2cdd08e8afcad052`.

The private successor adds conservative spatial nodal forces, once-only global
assembly, their exact linear work, and authenticated state/modal replay. Node
moments are not smuggled into a dead-force contract. Its separate schema/policies
prevent cross-load-policy hot restart. Existing distributed entry points retain
their exact Program and serialized bytes. Small shared private hooks reuse the
same Newton, ownership, checkpoint and paired-spectrum algorithms.

No beam or section equation, interpolation, quadrature, numerical coefficient,
tolerance, recovery operator, existing B2/B3/Q4/S3, public selector/default or
package metadata changes. There is still no production FEModel state publication.

## Separate inventories

- Signed axial smoke: 2 tests, 2 scientific files. Analytical tension/compression
  F/EA displacement, nodal work, reaction and current-rest capture passed.
- New complete suite: 22 tests, 19 scientific files. Work derivatives and exactly
  unchanged tangents; straight/curved/shared-node point loading; global force and
  moment balance; checkpoint replay; modal capture/paired modes; cancellation,
  failed iterations, schema, cross-policy and rehashed corruption guards.
- Preserved distributed ports: 6 tests, 18 scientific files.
- Preserved distributed state guards: 22 tests, 5 scientific files.
- Preserved distributed modal suite: 20 tests, 29 scientific files.

All inventories passed. The new rehearsal and both fresh-directory repeats are
scientific-byte-identical. All old port/guard/modal scientific bytes match their
bound archives exactly, including their hashes in the historical manifests.
This comparison does not claim a rerun of every historical beam study.

Maximum point-force balance error: 5.502616243162001e-13. Maximum moment balance
error: 1.7482916089835802e-12. Both pass unchanged 1e-11 gates. The shared-node
case applies the force at node 3 once, not once per adjacent element.

Every child passed clean pre/post guards and reached an empty process tree.
No retry or failure correction occurred. Maximum child time: 52.329425 seconds.
At most three workers overlapped. The two new repeats ran concurrently in
distinct directories and spanned 43.481267 seconds. Each child retained one
numerical-library thread, 24 GiB, 600 seconds and 120-second CPU-inactivity
protection; the wave remained below 1800 seconds.

## Preservation

Archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-retained-nodal-1bce83f-20260908`.
Manifest: 18,379 bytes, SHA-256
`1AE45BA9CCBFF1D2E0AC335359EE7A9161813C8A66CD14282773B481436C6D6F`.
Audit: 14,756 bytes, SHA-256
`6736C207D48B9BDE913A47F5AC46A74B1DF503F7E6CD20ED332BD0025B895359`.
All seven invocation directories, exact source/test/contract, supervisor and
audit are preserved and copy-verified. Originals and prior archives are intact.

## Resume / remaining full goal

All processes are terminal. Next freeze the existing straight prestress/Euler
reference cases through actual nodal-force retained Newton equilibria. The old
spectral fixture manufactured a uniform axial accepted state; the new load path
allows checking the complete programme rather than inferring it from local
assembly. Begin with a small signed-preload funnel before higher refinements;
preserve source fields, independent references and numerical tolerances.

This is not full beam qualification. Broader curved/postbuckling engineering,
nonlinear material/fibre parity, practical scale, FEModel/state integration,
independent review, complete environment graph, installed public selection and
objective finite-rotation shell connections remain required. Do not treat the
private supported-model bounds as the intended final product scope.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

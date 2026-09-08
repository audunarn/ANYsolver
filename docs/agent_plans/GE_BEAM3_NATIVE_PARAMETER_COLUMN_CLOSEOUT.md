# Native generalized analytic load-column closeout

Implementation: `09096dd6b23fa054097628e4025f66ba4f6276d3`.
Tree: `0d7470aa5268f882d357cceb9196bbc30b0d00f0`.
Base: `ea5d57beea0652be67e37596708799e59bea409f`.

Status: `PASS_DEVELOPMENT_ANALYTIC_LOAD_COLUMN_ONLY`.

This adds the analytic load-parameter column needed by a bordered
displacement/arc-length solve. It does not yet implement that continuation
driver or demonstrate a postbuckling branch. Independent review and the full
production beam-and-joint qualification remain incomplete.

## Exact scope and mechanics

Three new paths only: private parameter module, tests, and development plan.
No existing source file, section law, residual, tangent, state store, recovery,
beam/shell mechanics, public alias, package metadata or default changed.

At fixed external nodal pose and accepted material origin, the complete retained
partial load derivative is b=-W_prime_gradient-G_prime. The native general
stationary Jacobian gives y_i_prime=-J_ii^-1 b_i and the condensed load column
b_e+J_ei y_i_prime. The implementation uses a general solve and does not replace
J_ei with a transpose or symmetrize the operator. Rotational rows are mapped
through the actual accepted-origin chart. Proportional nodal couples enter once
globally, including at shared nodes.

This derivative retains curved-reference cell-lift line work and internal
spatial-couple response. Using only the external nodal load vector would omit
these terms. Production evaluation contains no numerical differentiation.
The returned internal sensitivity is diagnostic static data, not a dynamic
reduction or conservative spectral certificate.

The entry requires an active issued trial, exact model/store ownership, matching
trial state and pose, complete element coverage, and validated derivative
patterns. Foreign, stale, altered or absent inputs fail closed; failures discard
the active trial without advancing accepted history.

## Separate execution inventories

| Inventory | Passed | Failed | Scientific files | Supervisor seconds |
| --- | ---: | ---: | ---: | ---: |
| Initial straight smoke | 1 | 0 | 1 | 7.625 |
| Initial rehearsal | 10 | 2 | 9 | 92.414 |
| Corrected rehearsal | 13 | 0 | 13 | 100.242 |
| Frozen cycle A | 13 | 0 | 13 | 103.849 |
| Frozen cycle B | 13 | 0 | 13 | 103.842 |

The initial rehearsal's two failures were test-observation errors: plastic
coverage inspected a live trial view after subsequent perturbation assemblies
invalidated its token. All derivative-error assertions passed before that
assertion. Initial logs and the exact initial three-file source snapshot are
preserved. The correction copies the base trial before perturbing; producer
source is byte-identical to its initial smoke version. It does not change a
formula, fixture, load, coefficient or tolerance.

The corrected inventory also adds an accepted plastic origin followed by
unloading, an exactly zero derivative direction, and a diagnostic file for the
foreign-store rejection. This is a deliberate corrected rehearsal in a fresh
directory, not an automatic retry of a worker or reuse of a result.

The three finite-difference steps remain 2e-4, 1e-4 and 5e-5. All normalized
errors satisfy the unchanged 1e-7 criterion. Largest errors by case:

- Straight elastic: 7.690836071880276e-10.
- Curved plastic: 1.1131487001830365e-10.
- Connected plastic, with a shared-node couple: 6.261325166985734e-10.
- Previously committed plastic origin/unloading: 1.4069285906575938e-9.

The checker re-solves each perturbed native trial at the same accepted origin
and uses a separate closed Rodrigues nodal-work map. This is a directional
development check, not a fully independent mechanics implementation.
Zero direction gives exactly zero column and internal lifts. Accepted history
and committed generation remain unchanged through derivative evaluation.

Both frozen cycles and the corrected rehearsal have byte-identical canonical
scientific outputs. They ran in fresh external directories. Each child had a
600-second wall limit, 24-GiB process-tree limit, one numerical thread and
120-second CPU-inactivity limit. The two frozen replicas overlapped; at most
three were permitted. Every child reached terminal state with no descendants.
The largest observed peak process-tree memory was 245686272 bytes, during the
initial rehearsal. All commands completed in under 104 seconds.

## Audit, preservation and limits

The read-only audit validates the exact three-path Git extent, strict canonical
JSON, XML test inventories, supervisor bounds, deterministic replicas,
initial producer equality and every registered numerical assertion.
The environment guard checks the configured executable/version identities;
complete dependency-file attestation and independent review remain pending.
No prior scientific output is overwritten or reclassified.

Archive:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-native-parameter-09096dd-20260908`.

81 data files (120435 bytes) plus the manifest preserve the five command
inventories, logs, XML, scientific records, supervisor/tool observations, initial
and frozen sources, audit and inputs. Every copied byte count and SHA-256 was
verified.

Manifest: 12627 bytes, SHA-256
`FCD3398B24B4502231FAF6526AECC4EE03FD13E11F9C8619DE527A6AE1EEF433`.
Audit SHA-256:
`BBC21D5EFAAC9FF69EF10FAD4A24D07143037A22200961FA96CABED60DFCE47C`.

Original run directories and historical evidence remain intact. Only the
hash-verified staging duplicate may be removed. Main remains at
09351645ba17a0a5b130a1c7a48007d36dd08ada; the user's untracked ANYmesher
compatibility plan is unchanged. No other repository is edited, and there
is no push, merge, publication or default activation at this gate.

## Next required work

Implement a native signed-load displacement-control programme using the true
bordered Jacobian, this load column, actual state-store transactions and a
complete authenticated path/restart chain. The existing force wrappers and
their 0..1 parameter bounds must not silently be reused as arc-length authority.
Then add objective arc-length continuation and demonstrate limit-point and
postbuckling behaviour against independent references.

Broader supports/initial fields and material adapters, practical-scale
performance, scalable history, physical mass, modal/prestress/buckling,
slenderness and curved engineering qualification, independent review, installed
public integration and objective beam-shell joints remain required. The full
goal remains active and incomplete.

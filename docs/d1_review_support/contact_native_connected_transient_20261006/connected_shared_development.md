# Connected native dynamics and shared controller: development verification

**6 October 2026. Status: tested development; not independently accepted or released.**

The connected retained-coordinate midpoint owner and shared transient transaction
controller now have installed execution evidence. One assembled system includes
shared-node work and all local retained coordinates; this does not establish
contact-free C7 engineering acceptance or C8 contact/impact capability.

## Candidate, artifact and checks

Product candidate: `7986c5bdf04843dd403421e5f42bf399536ab7ab` in
`C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001`, branch
`codex/contact-main-reconcile-20261001`. The subsequent test-only repair replaces
nine assignments to frozen `TransientConfig` with `dataclasses.replace`; all
values, assertions, mechanical inputs and scientific criteria are preserved.
Test SHA256: `98c6e3d93102687829a2518ea581f5ca68b9f3f004107a22f81a6416f212d14f`.
No product payload changed after building.

Private wheel SHA256:
`a9febab4c77ce607c00afe77dd04781b5f6c82e6f53232ec20284d8d1ef516b6`.
All 549 source/wheel/installed product payloads and six wheel metadata records
match; RECORD inventories and hashes were checked. Private install used
`--no-deps --no-index --no-compile`. Completed numerical sessions have 190-196
verified private imports, JIT disabled, Numba one thread and observed pools one
thread. Raw runtime fixtures label themselves "source development only"; actual
recorded imports resolve to the private installation, not the source checkout.

| Coverage | Distinct passing cases |
|---|---:|
| Connected owner assembled mass/maps, rigid reference and global work/tangent | 3 |
| Connected trajectory, physical origin, closed controls, replay/refusal, cutback and state safety | 27 |
| Existing single-native full/split and in-flight cancellation compatibility | 2 |
| Total | 32 |

The actual installed public example completed two steps with the explicit
`NATIVE_CONNECTED_CONTACT_FREE_MIDPOINT_TRAJECTORY_DEV_V1` profile and a 58,749-byte
checkpoint; it reports `engineering_accepted=false`. Fresh split restart and
history checks passed. Legacy saved full and resumed JSON outputs are
byte-identical to the earlier installed workflow; the old saved import hashes,
private origin and effective settings were separately checked without rerunning.
This comparison applies to those fixtures, not universal equivalence.

## Retained failures and repairs

- `connected_shared_workflow1`: 13 passes and one test failure. Direct mutation
  of frozen `TransientConfig` raised `FrozenInstanceError`. The narrowly scoped
  immutable-config repair preserves the original whole-module AST after reversal;
  the affected origin/refusal case then passed in `connected_shared_origin_repair1`.
- `connected_shared_legacy1`: timeout at 40.093736800015904 seconds. Its first case
  had a passing call report, but terminal import/runtime records were absent; the
  second case had no complete call. This partial session is not a complete pass.
  The same two required checks subsequently passed in `connected_shared_legacy_retry1`
  with full metadata, within the original allowance.

The original aggregate audit remains **`PACKAGE_EVIDENCE_FAIL`**, retaining five
historical errors. The separate [current disposition](connected_shared_disposition.json)
records their resolution and verified coverage; it does not erase or reclassify
the original attempts. All raw output and partial records remain available.

## Exact execution accounting

The human's "I authorize" grants the previously requested separate
`C7_CONNECTED_SHARED_DEV` 240-second scope. Twelve terminal jobs, including
build/install, failed and rejected work, consumed **230.89657720038667 seconds**;
**9.103422799613327 seconds remain** in this scope only. Peak process-tree memory:
**169820160 bytes** (about 162 MiB). One numerical job ran at a time, each capped
at no more than 60 seconds and 953 MiB. No other purse was borrowed or renewed.
No live numerical job remains; no further optional repeat is planned.

Raw evidence:
`C:/ANYworkspaceWork/contact_native_connected_transient_20261006`.
It contains immutable authority/base manifest, the exact test-only V3 input
revision, per-job command/input/resource/process/case/import/runtime records,
source review and AST proofs, wheel/private install, aggregate history audit,
`root_connected_execution_disposition.json`, and final tooling-revision hashes.
Runner/audit helper revisions are explicit and grant zero additional execution.

## Remaining obligations and next useful slice

This closes the bounded connected public-controller, restart/safety and legacy
integration checks. It does not execute every prepared owner-only test. The source
review is supporting OpenAI-family scrutiny, not independent scientific acceptance.
Independent deforming and finite-angle connected response, physical support
force/moment/impulse, admitted section/spatial breadth and full C7 qualification
remain open. C8 additionally needs contact coupling at a common shell/native stage.

Next close the connected deforming/support-work mechanics gap using the existing
owner and shared controller, with an independent reference and a bounded connected
implementation outcome. Do not build another time-driver stack or replay the
completed 32 checks. Any further numerical allocation must cover its actual new
scope; the remaining 9.1 seconds is not a forecast that those gates will fit.

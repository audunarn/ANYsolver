# C9 ordinary-static contact export - development evidence

Base d55deab7a70d70463ab3ef8077b1e47c4e5a5b84. Implemented/source and private
installed development-tested, not independent engineering acceptance or release.

`ContactStaticArchive`, serialize/read_static_contact_results and the additive
NonlinearStaticResult.to_contact_archive_bytes preserve every eight-field producer
value: steps, status, displacement, load factor, material states, diagnostics/info,
committed snapshots and full checkpoint. Decoder returns inert records/detached
arrays; it never reconstructs a solver/snapshot/material class. The existing
exact-bit codec/material preflight is shared through narrow internal parameters.
Transient defaults, schema, limits and public behavior remain unchanged.

## Actual checks

- Installed16PASS3.055145399994s/181743616B. Static and affected transient record,
  malformed/schema/resource, pre-copy active-state and variant controls pass.
- Final independent preservation2PASS3.386929499917s/181596160B against the SAME
  artifact. Direct dataclass/mapping/sequence inventories and NumPy dtype/shape/raw
  bytes/Python float struct bits compare to the actual producer, using its own
  committed-state protocol. Deliberate omission/zero/dtype/container defects fail.
  This supersedes the original codec-against-codec preservation comparison.
- Actual ordinary S3 force solve: two accepted steps and two committed snapshots;
  74,798-byte archive, exact eight fields and complete checkpoint. Active gap
  -4.610748106978um in the existing50um fixture. This is consumer integration,
  not new contact mechanics qualification or lifecycle acceptance.
- Explicit installed wire1PASS2.227819300024s/180486144B. Required protected
  installed3 baseline hash489e387da158e8ddd33cdbabe71c8ba7b1459c37ff4daa77c3eecb0459a4acb1;
  before/after6,692bytes, SHA28bba5feb7536a3fc8cfce195dffb801784c9ec6047259262ce8f9147e4c6711.
  Effective baseline path/hash and equality are persisted, not inferred from a
  conditional test pass. Temporary reference alias cleanup changes no production
  import routing. Its earlier provenance NONPASS remains retained.
- Actual producer run235 installed imports, errors[],JITdisabled,Numba1 and
  all3effective pools1. Seven held file hashes match. Root independently hashed
  all537 source/wheel/installed payloads, zero mismatch; artifact
  0c477e4bd8399812523df2ed15aac9062fb17a6dce72b19204f0afc9d70bfd32.

Scoped supporting Read review closed record roles, snapshot pre-copy refusal and
oracle isolation findings. Root required direct preservation and explicit baseline
evidence; this scrutiny does not supply independent engineering acceptance.

## Costs, failures and limits

Eleven additional terminal jobs41.609207399888s; original archive total25jobs
137.750178399612/180s,42.249821600388s remain. All selector/record-role/summary/
reference-provenance failures, prior test hashes and successful artifacts retained.
Five new NONPASS runs; prior archive failures unchanged. One final packaged build;
test-only oracle repairs reused it. No budget renewal/borrowing or frozen replay.

No-contact results/arbitrary material objects are unsupported. Actual physical
producer was elastic; synthetic committed/active-state controls do not qualify
nonlinear material/contact combinations. Raw reactions remain producer generalized
coordinates. Archives confer no restart, source/model admission or acceptance.
Application models/adapters, accepted admission, exports/visualization/installed
application workflows, measured scale and full C0-C9 remain open.

Raw C:/ANYworkspaceWork/contact_transient_archive_20261006: static_worker_handoff.md,
static_summary.json, static_final_hashes.json, preserved prior hashes,
static_payload_parity.json, static_root_payload_parity.json, perjob records,
static_independent_preservation/actual_result.json and
static_explicit_wire_compatibility/wire_compatibility.json.
[Usage guide](../../GENERAL_CONTACT_STATIC_RESULTS_ARCHIVE_DEV.md),
[prior transient evidence](development.md).

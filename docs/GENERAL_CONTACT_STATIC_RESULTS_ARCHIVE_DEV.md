# Ordinary static contact archive (development)

`result.to_contact_archive_bytes()` and `serialize_static_contact_results(result)` export all eight exact `NonlinearStaticResult` fields. `read_static_contact_results(raw)` returns immutable `ContactStaticArchive` bytes, a SHA256, and fresh detached `to_dict()` views. Steps and snapshots retain complete fields as inert record dictionaries; no producer/material object is constructed on read.

The V1 schema reuses the transient exact-bit numeric codec, 16MiB hard byte cap, depth64, node/array caps, strict JSON and declared positive-infinity gap markers. Binary64 negative zero and subnormals are preserved. Unknown objects, active material trials, nonfinite work/reactions, corrupt dimensions and schema/conventions refuse. Known committed `NonlinearStateStore` data uses the same closed preflight before owned materialization; arbitrary material objects remain unsupported. No pickle, dynamic imports from data or callbacks are executed.

Physical contact force/moment units are N and N*m; raw structural reactions remain generalized work-conjugate coordinates and require formulation-owned maps. Existing producer evidence flags and checkpoint payloads are preserved; archive is data export, not restart, admission, qualification or acceptance. Transient schema and wire bytes are unchanged. No-contact ordinary results are explicitly outside this contact archive.

Run `examples/general_contact_static_results_archive.py` for a real S3 finite-tool force-equilibrated solve with committed snapshots and a complete checkpoint. Static path lifecycle diagnostics present in `info` are retained as data; this example does not qualify lifecycle mechanics.

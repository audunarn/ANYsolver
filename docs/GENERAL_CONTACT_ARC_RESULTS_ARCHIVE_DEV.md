# Arc contact result archive V1

`serialize_arc_contact_results(result)` and `result.to_contact_archive_bytes()`
export all ten ArcLengthResult dataclass fields. `read_arc_contact_results(bytes)`
returns immutable ContactArcArchive bytes; every `to_dict()` returns detached
arrays, mappings and inert record_type/fields/summary values. No producer,
material or solver object is constructed. This is export data, not a restart
owner, capability admission, engineering acceptance or release artifact.

The separate closed arc schema preserves displacements, load/peak fields,
accepted step counters/retries/spherical metrics/peak flags/raw generalized
support reactions, full info/contact V1 or V2 histories, committed snapshots and
material data, and the full checkpoint. Exact-bit tags preserve Python binary64,
NumPy dtype/shape/raw bits, negative zero and subnormals. Only declared positive
infinity open gaps are permitted. Unknown/active material data refuses before
copy callbacks. Exact producer fields are exported, not the lossy result summary.

The existing transient/static numeric codec, material preflight and caps are
reused unchanged: 16 MiB hard byte cap, depth64, 200000 nodes and bounded arrays.
Custom byte limits may tighten the hard cap. Unsupported types, corrupt roles,
unknown schemas, malformed dimensions, duplicate fields or invalid digests
refuse. No pickle, evaluation or import selected by data is used. Physical force
is N, moment N*m, gap m, energy J; raw support components remain generalized
work-conjugate values, not automatically physical resultant moments.

The example performs two accepted public affine/preload arc points and consumes
the resulting archive. Development tests compare all producer fields using a
separate recursive raw-value oracle, including exact checkpoint and snapshot
material values. Arc mechanics qualification is outside this export evidence.
Transient and ordinary static schema/wire formats are unchanged.

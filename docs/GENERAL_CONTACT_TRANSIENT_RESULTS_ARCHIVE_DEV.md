# Transient-contact results archive (development)

`serialize_transient_contact_results(result)` or `result.to_archive_bytes()`
exports all current `TransientContactResults` fields as canonical strict JSON
bytes. `read_transient_contact_results(raw)` returns an immutable
`ContactTransientArchive`; `to_bytes()` is exact and `to_dict()` returns fresh
independent arrays/mappings. Contact/free-body records remain inert data with
their original class identity, exact fields and producer summary. No classes
are instantiated from archive names, and no pickle/eval/callback is executed.

Binary64 scalars use exact bits; NumPy numeric arrays/scalars retain dtype,
shape and bits. Negative zero/subnormal values are preserved. Legitimate
positive-infinity gap data is explicit; NaN/negative infinity and infinity in
other fields refuse. Arrays containing infinite gaps use tagged numerical bytes.
Restart payloads and producer evidence flags are retained unchanged. The archive
does not validate or admit a restart and confers no qualification/admission.
Newton iteration counts belong to every accepted step, including steps omitted
by output decimation; their length is not the saved-pose count. Other saved
scalar histories align with saved times. Optional histories may be empty.

The closed V1 schema binds producer field inventory and conventions. Duplicate
JSON/mapping keys, unknown fields/tags/schema, stale conventions, mismatched
dimensions and unsupported objects refuse. The byte cap is16MiB and can only
be reduced via `max_bytes`; nesting64, node200000 and total array-element2000000
bounds apply. Input size and JSON structure are checked before parsing; array
dimensions/encoded length are checked before decoding/allocation. Serializer
preflight refuses oversized data without dropping fields or reducing precision.

Time/gap/work use seconds/metres/joules. Physical contact resultants retain N
and Nm; numerical surface pressure uses Pa, line stiffness N/m2 and endpoint
stiffness N/m. Producer moment-origin/work conventions remain in the summaries.
Structural kinematics and raw constraint reactions use the producer's
generalized work-conjugate chart. Rotational reaction entries require
formulation-owned maps; they are not automatically physical moments.

The example `examples/general_contact_transient_results_archive.py` reuses the
small admitted guided-Q4 fixed-plane impact through activation and release,
saves generalized reactions and exact restart payload, then exports/reads it.
This is producer-consumer development verification, not C6/C9 acceptance.

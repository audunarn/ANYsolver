# Native contact checkpoint-results data reader

The additive public `read_native_contact_checkpoint_results(raw, *, max_bytes,
expected_identity=None)` returns immutable `NativeContactCheckpointResults`.
`to_bytes()` preserves the exact producer bytes; `to_dict()` returns a fresh,
detached JSON data tree. Failures raise `NativeContactCheckpointResultError`.

Only the existing `NATIVE_PHYSICAL_FIBRE_WHOLE_CURVE_PAIR_CHECKPOINT_DEV_V1`
schema and `NATIVE_B3_GE_PHYSICAL_FIBRE_WHOLE_CURVE_PAIR_STATIC_DEV_V1` profile
are supported. This is a DATA reader, not a native restart owner, scientific
validation, application admission or qualification. It constructs no solver,
model, constitutive object or executable record, and invokes no stored callback.

The reader checks canonical ASCII native JSON, exact envelope/record keys, the
unsigned capsule digest and accepted-record chain. It preserves the complete
stored mechanical descriptors, physical-fibre histories and contact summaries.
Shapes and finite numeric/count roles are checked; unknown data is refused.
Digest consistency does not establish physical truth, equilibrium, constitutive
admissibility or correct geometry. `expected_identity` checks a supplied SHA256
identity; it does not independently derive a model/settings identity.

Input bytes are bounded before parsing: a caller may lower the default hard
2 MiB cap, never raise it. The preparse bounds are depth32 and 200000 structural
nodes/separators. Histories are bounded to two body records, at most48 stations
per body and256 four-component fibre rows per station. No precision reduction,
normalization, repair or unsupported-profile fallback occurs. Existing native
producers and transient/static/arc archive wires are unchanged.

Stored field labels `positions`, `position_low`, `conservative_lower_gap_m` and
`minimum_sampled_gap_m` identify length data; `potential_j`/`energy_error_j` are
J, forces N, contact moments N*m. Nodal/cell frames are stored dimensionless
matrices. Retained `resultants` and history rows are preserved as producer
coordinates; the reader does not invent nodal IDs or relabel their generalized
components. Contact moments retain the producer convention, not a new origin
inferred by this consumer.

Run the public example with an explicit existing capsule path:

```text
python examples/general_contact_native_checkpoint_results.py tests/data/general_contact_native_curved_pair_lifecycle_press_v1.checkpoint
```

The example reads at most the reader's hard `MAX_BYTES+1` bytes from the file,
then calls the bounded reader. The extra byte distinguishes an oversized file
without allocating its complete contents. It does not duplicate the limit.

The protected portable capsule is an actual producer input. Consumer tests use
independent direct JSON inventories and raw binary64 comparisons, including
negative zero and subnormals, without mechanical replay. Development verification
and installed-import evidence remain separate from engineering acceptance.

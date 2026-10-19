# Versioned capsule replay

New recovery exports default to `replay_version=2`: schema
`anysolver.recovery_capsule`, version2, runtime `anysolver-results/2`, and
`combination='ordered_float64/1'`. Runtime package2.0.0 admits the paired legacy
version1/runtime1 contract too. Unknown versions, mismatched pairs or unsupported
arithmetic identifiers fail with typed runtime errors.

The existing public `reconstruct_response` and `prepare_response` defaults retain
`combination='legacy_blas/1'`. Passing `combination='ordered_float64/1'` selects
the new row-independent operation: iterate the original active-column order,
materialize each binary64 multiplication and addition separately, then add the
baseline once. No BLAS reduction, GEMM, fused multiply/add, column reordering or
source row pruning occurs. Empty active order preserves the baseline bytes.
PreparedResponse owns immutable baseline/selected buffers and a read-only
`combination` tag. Prepared replay uses that tag; an explicitly requested
different or unknown algorithm is refused.

Binary64 rounding/subnormal assumptions are recorded as operating conditions,
not a certificate for every platform. The source solver's original full
element-vector combination, arithmetic order, scalar/array measures, actual
loads, solve, full backward-error certification, source agreement and canonical
fallback are unchanged. The new operation changes portable replay, not source
physics. The exporter invokes that same runtime operation and compares float64
bits against actual source primitive and displacement fields on every case.
Any difference, signed-zero distinction or refused/nonfinite replay emits the
exact source field as a stored correction. A finite certified source result is
not lost merely because portable replay overflows.

Derived fields receive separate source parity. Inputs are the actual admitted
primitive bits: a matching replay or its exact source correction. Variant
dependencies align by persistent element IDs and native sample order, never
coordinates or averaging. Missing or unsupported dependencies cause an actual
derived field to be stored; unequal derived bits also cause exact correction.
Missing actual fields are listed in per-case `unavailable_components`. Readers
must refuse those components instead of reconstructing invented values from
existing response columns. Missing actual displacements yield
`displacement_portable=null`. A nonportable case requires its explicit source
rows regardless of whether a basis happens to give matching numbers.

Per-case `correction_reasons` maps component keys to short strings, including
`source_bits_differ`, `ordered_replay_refused`, `derived_source_bits_differ`,
`missing_source_dependency`, `unsupported_dependency_layout` and
`source_nonportable`. These are diagnostics, not alternative certificates.
Original case status/certification, `input_index`, route, source provenance,
component units/bases/native shapes and exact-earliest-input tie policy persist.

Principal rank fields are conservatively stored explicitly on version2, with
`spectral_replay_not_certified_portable`. Their descriptors declare stored
availability and explicit reconstruction; version2 does not publish replay
specifications for these fields. Existing standalone/legacy spectral operations
remain available. Ordered primitive replay does not prove LAPACK eigenvalues
bit-invariant across backends. This increases principal storage; compression
cost and performance need separate measurement and acceptance.

Version2 geometry topology uses dense zero-based node indices into `positions`.
`line_to_element` and `triangle_to_element` are one-dimensional integer mappings
into `element_ids`, whose entries are persistent solver IDs. Mapping lengths
match line/triangle counts and all indices are bounds checked. Empty geometry
remains valid for headless use. Legacy version1 keeps its earlier numeric-only
geometry admission behavior.

Producer-used runtime functions, transitive function/global/class bindings,
closed registry and NumPy operations are pinned around case parity and sink
publication. Callback mutation produces typed refusal and the optional terminal
failure notification. This adds output admission without extending a mechanical
trusted scope or changing the original source guards. Replay workspaces,
retained bases/selectors and pending correction rows are included in the source
resource-policy checks. `replay_diagnostics.runtime_guard_checks` records guard
visits; it is not a measured speed or scientific qualification claim.

The certified-vector von Mises helpers delegate to the existing shared formulas
with their original scalar/array conversions and expression order. Canonical
element implementations retain their inherited physical expressions. Version2
corrects source/replay differences rather than asserting those variants have
identical floating-point arithmetic. Explicit `replay_version=1` export retains
legacy replay/parity behavior and limitations; it does not repair old archives.

ANYpost must route version2 response reads through the named ordered operation,
honor global/per-displacement portability and per-case unavailability, prefer
stored corrections before dependencies, and keep original persistent-ID/sample
associations and tie identities. ANYpost integration and cross-platform,
actual-scale and independent scientific acceptance remain separate owner gates.

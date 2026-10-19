# ANYsolver recovery capsule export (contracts v1 and v2)

This document describes the solver-owned capsule exporter and the NumPy-only
`anysolver_results` runtime, as adopted for the ANYpost integration contract
of 2026-10-12 (`C:/ANYworkspaceWork/anypost-20261012/CONTRACT.md`).

## Public solver API

```python
from anysolver import export_recovery_capsule, PatternCase

capsule = export_recovery_capsule(
    evaluator, cases, *, model_identity, mesh_identity,
    geometry=None, solver_identity=None, batch_size=32,
    recovery_execution='auto', replay_version=2)
```

- `evaluator` must be an open `PreparedStaticResponseEvaluator`
  (`prepare_static_response_evaluator(...)`); subclasses and other evaluator
  types are refused.
- `cases` is a finite list/tuple of `PatternCase` instances with unique ids.
  The batch is consumed through the evaluator's certified batch iterator in
  bounded increments (`batch_size`, default 32).  A case that fails
  certification aborts the export with the evaluator's own error; the
  exporter never fabricates a pass.
- `geometry` is an optional mapping of ANY3dView MeshArrays-style names
  (`positions`, `triangles`, `lines`, `triangle_to_element`, `line_to_element`, `node_ids`,
  `element_ids`) to numeric arrays; empty geometry is allowed for headless
  capsules.
- The default returned mapping is capsule v2; `replay_version=1` explicitly
  selects legacy v1 behavior (plain data; no executable
  or pickle payloads) and has passed `anysolver_results.validate_capsule`.
  Its metadata containers reject ordinary mutation and its numeric arrays
  are read-only views over owned read-only buffers. Caller geometry is copied
  once, so later caller/model mutations cannot change the snapshot. Metadata
  serializes to the same finite JSON data; `copy.deepcopy(capsule)` creates
  independent construction data. Editing a construction copy does not admit
  or certify a new case. Version2 declares runtime `anysolver-results/2` and
  `combination='ordered_float64/1'`; runtime package2 also supports paired
  legacy version1/runtime1. See [versioned replay](DETERMINISTIC_CAPSULE_REPLAY.md)
  for exact correction, arithmetic, geometry and operating-condition contracts.

### What is reconstructable

A component is exported on the compiled affine pattern basis only when the
evaluator reconstructed the case on its admitted basis
(`stress_execution='certified_library'` with a non-empty element library and
`source_response.reconstructed` true).  The exported response columns are
exactly the evaluator's library columns (baseline in column 0, zero-subtracted
pattern increments in columns 1..P). Version2 uses ordered binary64 field replay
and compares it against the unchanged source element-vector arithmetic; any
difference retains the exact source row. Legacy1 retains its original BLAS
field-level replay and associated limitations.

Portable basis fields are additionally gated per case by an exact bitwise
parity check: the exporter reconstructs each component with the runtime's own
field-level accumulation and compares it against the evaluator's certified
record.  The certified library itself accumulates at the element-vector level
(`_combine` over the whole local column block), so an active multi-pattern
combination can round differently than the per-field reconstruction; such a
diverging component keeps an explicit stored row with the certified values for
that exact case (the case stays certified and portable, and the stored row
overrides basis reconstruction for that case/component pair).  No tolerance
is relaxed and no value is fabricated.  Nodal displacements use the same
per-case parity gate with `displacement_portable` recorded per case.

Every other certified case (canonical route, certified-vectorized route,
source-agreement or certification fallback) is exported with explicit
per-case stored arrays under `stored`, with its actual route label in
`cases[i]['route']`.  Existing canonical fallback and
`certified_library`/`certified_vectorized` labels are preserved verbatim; the
compact export never relabels an output as a different route.

If a source iterator provides a failed record, its diagnostic/error metadata
and failed `solver_info` are retained with `certified: false`; it never yields
success fields. The current prepared evaluator instead raises on failed
admission/certification/recovery, which aborts the export. An optional
`capsule_failed(record)` sink callback receives the primary failure and input
case identities before that same exception is re-raised. The four existing
successful callbacks remain required and unchanged. A diagnostic callback
failure adds a note to the primary exception instead of replacing it.

Failure records use `anysolver.recovery_capsule_failure/1`, with model/mesh
identity, status, error type/module/message, input identities and diagnostics.
Nonfinite diagnostic floats use explicit `nonfinite_float` tags; engineering
values are never changed. Diagnostic objects that cannot be serialized are
identified explicitly. A sink can preserve this record as a separate durable
failure artifact while refusing incomplete archive publication. Offline
reconstruction admits only completed certified cases, and an aborted export
is never a completed capsule.

### Derived quantities

Derived measures are exported as closed specifications under `derived` and
computed offline by the runtime registry, subject to per-case exact source
parity and stored correction in version2:

- `shell_von_mises` (max of top/bottom plane-stress von Mises with the shared
  transverse shear),
- `beam_von_mises`,
- `equivalent_stress` (copy of von Mises),
- Legacy1 may publish shell principal/rank specifications. Version2 stores
  actual principal ranks explicitly because portable spectral bit equality
  has not been established; standalone runtime spectral APIs remain available.

The formulas live in `anysolver_results.formulas` and are shared with the
solver (`prepared_static_measures` and the von Mises helpers in
`prepared_static_recovery` delegate to them), so in-solver recovery and
offline reconstruction share these reviewed helpers. Canonical element variants
retain their physical expressions; exact derived parity corrects any version2
replay differences. The fake zero Hill
utilisation is not an exported claim: it is never registered as an operation
and never appears in capsule descriptors.  In mixed shell/beam element sets
the derived keys split per variant (`von_mises:shell`, `von_mises:beam`);
`quantity_id` stays the plain quantity name.

### Alignment rule

For every derived key, each input component's association array contains the
derived key's element samples with identical per-element counts (the exporter
guarantees this; `validate_capsule` checks the response/stored/association
structure).  ANYpost resolves dependencies by selecting, for each derived
key, the input samples whose association element ids match the derived key's
association, and calls `derive_field` with aligned 1-D arrays.

### Not exported in v1 (recorded gaps, not claims)

- Portable basis replay for `stress_execution='certified_vectorized'` (its
  grouped affine maps are not converted to capsule columns; those cases are
  stored explicitly).
- Native station coordinates for beam2 section scalars: the source exposes
  none, so the shared sampling rule records an explicit
  `coordinates_unavailable_reason` instead of an invented location.
- Source-exact frames/sampling for element types without a registered
  extraction: the shared metadata records explicit unavailable reasons;
  nothing is inferred from sample counts.

## Lightweight runtime (`anysolver_results`)

NumPy-only package (`src/anysolver_results`), no imports from `anysolver`,
scipy, ANYfem or ANYpost.  Built standalone from
`packages/results/pyproject.toml` (`anysolver-results` wheel); the full
ANYsolver wheel does not package this runtime and instead declares the
dependency `ANYsolver-results>=2,<3` (the solver imports it at runtime for
the shared beam/shell/principal formulas).

```python
import anysolver_results
import numpy as np

anysolver_results.RUNTIME_ID            # "anysolver-results/2"
anysolver_results.validate_capsule(capsule)
active = capsule['cases'][i]['active_indices']
packed = capsule['coefficients'][i, np.asarray(active, dtype=np.intp) - 1]
field = anysolver_results.reconstruct_response(
    responses, packed, active_indices=active,
    combination=capsule.get('combination', 'legacy_blas/1'))
derived = anysolver_results.derive_field(specification, inputs)
```

- `reconstruct_response(responses, coefficients, *, active_indices=None)`:
  `responses` is `(spatial_count, pattern_count+1)` float64 with the baseline
  in column 0 (added exactly once).  `active_indices` are positions in the
  response columns (column 0 excluded); `None` means all pattern columns.
  Case metadata stores the admitted sparse active indices in the same
  convention. Pack only active weights in their recorded order, as above.
  The default is legacy BLAS replay; capsule2 explicitly selects ordered
  arithmetic. Exact source corrections take precedence before reconstruction.
  Returns a read-only float64 array.
- `prepare_response(responses, *, active_indices=None)`: additive
  preparation for repeated reconstruction of one response matrix.  It
  validates the same response matrix and original one-based active column
  indices as `reconstruct_response` and returns a `PreparedResponse` that
  owns immutable float64 copies of the baseline column and the
  original-order selected matrix (`responses[:, active]`, the exact array —
  and memory layout — the ordinary expression materializes, including
  sparse and reversed active orders; an empty active order retains the
  baseline only).  No alias to caller-mutable memory is retained, so the
  caller may mutate or release `responses` afterwards.  `nbytes` is the
  exact total retained numeric bytes (baseline + selected) as a Python int
  for archive cache accounting; the archive owner owns all cache,
  transient-allocation and byte accounting.
- `reconstruct_prepared_response(prepared, packed_coefficients)`: replays a
  `PreparedResponse` with per-request weights, executing precisely the
  selected legacy or ordered algorithm through the same shared arithmetic
  helper (no second numerical implementation),
  and returns a read-only float64 array.  Only objects created by
  `prepare_response` are admitted (exact type/identity check; arbitrary
  archives cannot invent a prepared object); weights are validated for
  shape and finiteness exactly like the ordinary reconstruction.  Ordinary
  and prepared reconstruction are bitwise identical for the same inputs.
- `derive_field(specification, inputs)`: `specification` is the JSON mapping
  from `capsule['derived']` (`operation`, `inputs`, optional `surface`);
  `inputs` maps canonical recovery input names to already reconstructed 1-D
  arrays.  Returns a read-only float64 array.
- `validate_capsule(capsule)`: lightweight shape/identity/status checks;
  typed `CapsuleValidationError` on refusal.
- Errors are typed: `CapsuleError`, `CapsuleValidationError`,
  `ReconstructionError`, `DerivationError`.

## Capsule payload reference

| key | content |
|---|---|
| `schema` | `"anysolver.recovery_capsule"` |
| `version` | `2` by default; explicit legacy `1` |
| `runtime` | `"anysolver-results/2"` paired with version2; legacy `"anysolver-results/1"` with version1 |
| `combination` | version2 requires `"ordered_float64/1"`; legacy1 uses `"legacy_blas/1"` |
| `replay_assumptions` | version2 binary64 operating conditions; no universal platform certificate |
| `model_identity`, `mesh_identity` | nonempty strings (caller-supplied) |
| `solver_identity` | JSON mapping (solver name/version, stress execution) |
| `model_provenance` | JSON mapping with the snapshot content digest |
| `model_recovery_metadata` | shared once-per-model JSON mapping: numeric element local frames and deduplicated native sampling rules (see below) |
| `geometry` | mapping of array names to numeric arrays (may be empty) |
| `patterns` | tuple of pattern names, original order |
| `coefficients` | float64 `(case_count, pattern_count)` |
| `cases` | tuple of JSON mappings: `case_id`, `input_index` (the exact original request position, a non-negative int), `status`, `certified`, `portable`, `displacement_portable`, `route`, `time`, `active_indices`, `provenance` (backward-error disposition, source-response label, load info), optional `reaction_node_ids` for cases that report one |
| `descriptors` | tuple of JSON mappings: `key`, `quantity_id`, `component`, `location`, `unit`, `basis`, `sampling`, `availability` (`stored`/`reconstructable`/`unavailable`), optional `reconstruction` (string when present), `recovery_route`, `tie_policy` (`exact_earliest_input_index` on every available descriptor), optional `element_shapes`, `stored_case_count`, `portable_case_count` |
| `associations` | component key -> int64 element id per flattened sample (repeated element ids permitted) |
| `responses` | component key -> float64 `(spatial_count, pattern_count+1)` |
| `stored` | component key -> `{case_indices: int64 array, values: float64 (stored_case_count, spatial_count)}` |
| `derived` | derived key -> `{operation, inputs: {canonical name: component key}, optional surface}` |

Stored outputs override basis reconstruction for those exact case/component
pairs; ANYpost must prefer `stored` rows for the cases they list. Version2
case admission also honors `unavailable_components` and
`displacement_portable` before considering replay. Its short
`correction_reasons` explain retained source rows without carrying value lists.

### Shared model recovery metadata (`model_recovery_metadata`)

The optional header key `model_recovery_metadata` carries the shared
once-per-model recovery geometry, captured before any case is processed from
the snapshot's private captured recipe owners (`capture:
"prepared_static_snapshot_private_recipe_owners"`) — never from the mutable
live model, so later model mutations cannot change it.  It is finite plain
JSON only: no factorisations, stiffness matrices, executables or owner
objects.  Anything the source does not expose exactly is recorded with an
explicit unavailable reason; nothing is inferred from sample counts.

- `frames`: `{convention, transform, elements}`.  `convention` is
  `local_axes_as_columns_in_global_coordinates` and `transform` is the
  matching identity (`frame @ tensor_local @ frame.T == tensor_global`;
  `frame.T` maps global components to local).  `elements` maps element id to
  the source-exact 3x3 local frame as nested JSON lists — bitwise the frame
  the element's own recovery uses (the S3 triangle frame from the owner's
  captured coordinates and reference normal; the beam rotation from the
  owner's captured axis — the end-node chord for quadratic beams — and
  orientation).
- `sampling_rules`: deduplicated shared rule table keyed by content
  (`rule-0`, `rule-1`, ...).  Each rule has a `kind`, a
  `coordinate_system`, `order: "source_native_station_order"` and either the
  native station `coordinates` (with `station_count`) plus optional
  `weights`, or an explicit `coordinates_unavailable_reason`.  Registered
  kinds: `triangle_gauss_stations` (natural triangle (r, s) coordinates and
  weights, the same station table the stress recovery loop consumes, in
  native order), `beam_natural_xi_stations` (natural xi stations: the
  generalized-section quadratic beam samples its own Gauss table in source
  order, the generalized-section beam2 samples its fixed interpolation
  stations (-1, 0, 1)) and `element_section_scalar` (ordinary beam2/beam3:
  one scalar section envelope per element; the source exposes no native
  station coordinates, so the reason is explicit — a centroid is never
  invented).
- `element_bindings`: element id -> `{element_type, frame,
  frame_unavailable_reason?, sampling_rule, sampling_unavailable_reason?,
  sample_count}`.  Elements without a captured private recipe owner, a
  registered source-exact frame extraction or a registered native sampling
  extraction carry the corresponding explicit unavailable reason.

Element-field descriptors reference these shared tables compactly through
their `metadata`: `sampling_rules` (the shared rule ids that govern the
descriptor's elements) and `local_frames:
"model_recovery_metadata.frames"`.  Stored element components additionally
keep their per-element source shapes in `element_shapes` (the native record
shape, e.g. `[7]` per shell sample vector or `[n, 3]` native principal
triples recorded on the shared binding); per-rank principal components
export one scalar per native row.  No per-case duplication of frames or
rules exists anywhere in the capsule.

### Envelope tie policy (`input_index`, `tie_policy`)

The solver's source envelope reducers (`static_envelopes.EnvelopeReducer`
and the prepared canonical `EnvelopeAccumulator`) retain, for equal minima,
equal maxima and equal absolute maxima, the exact earliest original
`input_index` of the governing case — irrespective of update, reduction or
subset traversal order.  The capsule exports the exact original request
position of every case as `cases[i]['input_index']` (a non-negative int,
also present on failed and non-certified records), and every available
descriptor declares `tie_policy: "exact_earliest_input_index"` so a consumer
computing envelopes from capsule data reproduces the solver's governing-case
identity, including tie breaks.  The prepared envelope result diagnostics
carry the same `tie_policy` label.  Unavailable descriptors carry no values
and therefore no tie policy.

### Admission contract details

- A certified case must carry a completed status from the ANYpost set
  `completed`, `complete`, `success`, `succeeded`, `ok`, `converged`; a
  certified failure status is refused.
- Descriptor keys are unique, and `(quantity_id, component)` pairs are unique
  across descriptors so reader queries by quantity/component are unambiguous.
- `reconstruction` is an optional v1 descriptor extension: a capsule without
  it is admitted, and a present value must be a string.
- Optional per-case `active_indices` are validated on admission like a
  reconstruction request: one-based response column positions in original
  order, unique and within `1..pattern_count`.
- The v1 extension keys `cases[i]['input_index']` (non-negative int) and
  the available descriptors' `tie_policy` string are admitted as plain
  data by the structural validation; their tie-policy semantics are a
  solver contract documented above, not a runtime check.
- Oversized plain integer indices (e.g. `2**100`) and numeric coercion
  overflow are refused with the typed `ReconstructionError` (or
  `CapsuleValidationError` during capsule admission), never a raw
  `OverflowError`; the original active order is never reordered.


### Descriptor basis and reconstruction semantics

`basis` is the physical coordinate basis of the quantity, following the
solver's canonical quantity descriptors: `global` (nodal displacements and
reactions), `element_local` (tensor and vector components resolved in
element axes), `principal` (descending principal-stress eigenvalue ranks,
scalar per sample, surface preserved in the component name) and `invariant`
(coordinate-free scalars such as von Mises measures). Unclassified solver
fields carry `unclassified` together with their unclassified unit.

`reconstruction` is the recovery mode and is reported separately:
`compiled_affine_pattern_basis` (portable response columns),
`derived_from_reconstructable_inputs` (closed derived-operation registry) or
`explicit_per_case_values` (stored rows). A component is `reconstructable`
when response columns or a derived specification exist; per-case `stored`
rows still override reconstruction for the exact cases they list.

Principal validation first retains the finite-tensor check, accepts exact symmetry directly, and otherwise uses the unchanged allclose tolerance. Symmetrisation and eigvalsh expressions are unchanged. Expected ValueError/LinAlgError from principal derivation are chained as DerivationError; cancellation, resource and programmer errors propagate. Pools still join per call; no persistent/session pool API is introduced.


### Explicit native recovery after numerical affinity refusal

`prepare_static_response_evaluator(..., stress_execution='certified_library',
numerical_affinity_fallback=True)` opts into source-native recovery only for
finite additivity, homogeneity, or rigid-offset residuals above the unchanged
library tolerance. The default is `False` (exact bool); canonical and vectorized
selectors do not admit this option. Type, shape, nonfinite, constant, derived,
executable-authority, and resource failures remain fatal. All original twelve
probe evaluations and original baseline/pattern column validations still run.
A rejected element owns its immutable source recipe and refusal diagnostics;
it has no admitted response columns or advertised qualified basis.

Cases still pass the existing source ingress, load, solve, backward-error,
certification, and canonical fallback transactions. Qualified elements retain
original full-vector GEMV recovery. Rejected elements recover their actual
certified state using the source-native recipe in bounded owned scopes. Numeric
publication merges actual rows without retaining case-by-element dictionaries.
A component namespace intersecting a rejected element is stored as complete
explicit source rows; unaffected namespaces may retain qualified bases. Derived
native VM/equivalent values remain available and stored. Fully native cases are
not portable; mixed cases preserve remaining qualified replay eligibility.

`source_response.native_affinity_fallback_elements` and
`native_affinity_refusals` preserve element identities and original diagnostics.
`native_affinity_element_cases` counts actual rejected-element recoveries on
numeric, record, and canonical routes; `numeric_element_cases` counts qualified
element GEMVs on numeric publication only. Counters describe performed work,
including work in subsequently cancelled or failed transactions; they do not
certify publication. Reconstructed native cases report
`certified_library_native_affinity_fallback`; canonical cases retain their
original canonical route. Preparation and retained native metadata/scratch
remain subject to the existing resource policy.

Native per-case identities and route labels describe elements actually visited
by that selected recovery/envelope transaction. Model-level refusal metadata
still preserves all rejected library identities. Incremental conservative
native-entry accounting runs before retention; detached immutable DOF mappings
do not retain a shared snapshot-array base. Equivalent-stress namespaces are
stored when their actual VM dependency is stored, even without a direct native
derived-refusal tag. Guard/timing/option diagnostics may differ for an opt-in
with zero refusals; scientific fields and case identities remain unchanged.

Both capsule export functions accept `cancellation_token=None`. A supplied
token is checked outside owned scopes before initial and final publication and
passed to the selected case iterator. The preparation token is not retained.
Normal ArchiveSink cancellation or source refusal preserves the previous
archive and retains a unique failed diagnostic record. Opted-in native export
also checks bounded response authority before further callback processing and
immediately before capsule_end. An arbitrary custom sink can act internally
before its callback returns; source guards cannot undo those external actions.

These changes do not qualify new physics, change the affinity tolerance, or
certify a new combination without source admission. Optional frame metadata is
preserved source provenance, not a runtime coordinate-transformation certificate.

## Authoritative source field observer

`export_recovery_capsule_to_sink(..., source_field_observer=None)` optionally
calls an observer once for each certified case, after actual source recovery
and before per-case replay/parity/encoding. The mapping has schema
`anysolver.source_fields`, version 1, model/mesh identities, `case` metadata,
`fields` keyed by the exact capsule key, `unavailable_components`, and
`excluded_components` (the non-result Hill placeholder). Each field provides
quantity/component/location/unit/basis, actual flat float64 `values`, int64
persistent-ID `associations`, zero-based `native_ordinals` within the source
field of each entity, `layout='source_scalar_rows/C'`, sorted `element_ids`,
`element_sizes`, and exact `native_shapes` per entity (principal rank shapes
omit the rank axis). No averaging, reconstruction or additional recovery is
performed. Ordinals are scalar positions in the source array, not a new
physical quadrature rule.

Numeric arrays use independent immutable bytes backing; mappings and sequences
are read-only proxies/tuples. The exporter retains no observer payload after
the callback. Observer-retained snapshots/storage are caller-owned. Source,
current batch, pending rows, selector/conversion and conservative snapshot
memory are checked before allocation against the source resource policy.
The absent observer route performs no observer snapshot/counting work.
Both source and runtime authority are checked around the external callback;
cancellation is checked before and after it. Original observer exceptions,
including BaseException, propagate through the existing abort/failure-report
path. Invalid payload/resource/authority requests remain typed refusals. No
archive values or replay eligibility are manufactured by this observation.

Observer-only metadata reuse retains at most one current immutable layout per
exact component key, replacing/releasing it when source layout/shape bindings
change. NumericCase stock immutable shape/ID tuples are freshly observed;
record/reaction shapes are rebuilt. Values remain fresh source copies. Retained
metadata participates in the source-policy bound. Read-only NumPy header
changes (dtype/shape) are also checked after callbacks and on static reuse.
If an observer raises while an authority/cancellation check also fails, the
observer's original primary exception propagates with the secondary chained.

Observer array validation also retains the original immutable backing object
and checks C data pointer, exact contiguous strides and read-only flags before
and after callbacks and on static reuse. Batch admission conservatively counts
Python containers/scalars and NumericField metadata as well as array buffers.
An existing primary exception cause is preserved; secondary authority/cancel
failures are added as notes. New observer helpers, globals and class methods
participate in the existing transitive capsule runtime guard.

Observer backing-chain repair: snapshot facts strongly
retain each intermediate ndarray and the terminal immutable bytes. Before and
after observation, and before cached metadata reuse, every base identity, array
header, readonly/nonowning flag and data pointer must still match. Replacing an
intermediate base with ordinary ndarray.__setstate__ is refused while the original
bytes remains alive; callback primary exceptions and existing causes are preserved.
The global helper binding is exposed directly in the metadata loop so the
existing runtime guard captures it. Backing ownership covers the active callback
and current metadata-cache entry; snapshots retained after return are caller-owned.
The previous 6A wheel is superseded. The repaired wheel/sdist and 157 private
installed checks are verified; final independent acceptance remains pending.

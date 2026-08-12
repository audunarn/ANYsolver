# S4 improved geometry-to-FE numeric handoff

## Status and scope

This document defines the permanent neutral input boundary for the improved
four-node shell. It is an FE-model construction contract, not a geometry file
format and not a geometry adapter implementation.

The live compatibility boundary recorded for this branch is:

```text
ANYgeometry public API       >=0.2,<0.3
live package observed        0.2.1
forward geometry document    schema 4
legacy strict document       schema 3, migrated by its owner
```

Schema 4 is the forward document boundary. ANYsolver neither opens nor
migrates schema-3 or schema-4 geometry documents. An ANYgeometry/ANYmesh/
ANYfem adapter resolves the owner records and emits the immutable numeric
handoff described here. The solver can also run a direct FE model with no
geometry provenance.

The production modules implementing this cold boundary are:

- `shell_formulations.geometry_provenance`: shared header, model tables,
  integer shell/member/coupling associations, validation, and fingerprints;
- `shell_formulations.director_field`: supplied-director validation and
  one-time sheet/part/crease-aware numeric reconstruction;
- `shell_formulations.mitc4_plus_d_quality`: FE-scale Q4 geometry/director
  checks and numeric reference fingerprints.

Public element wiring, serialization of an FE model, runtime dispatch, and
`AnalysisSession` integration are coordinator-owned integration work.

## Ownership and runtime boundary

The data flow is one way:

```text
ANYgeometry immutable revision + strict audit + resolved handles
    -> ANYmesh samples surfaces and constructs mesh/source associations
    -> ANYfem assigns FE regions and publishes one immutable FE revision
    -> ANYsolver validates and compacts numeric input once
    -> K, M, KG, residual/tangent, recovery consume arrays and integers only
```

ANYgeometry owns persistent structural identity, topology, support surfaces,
replacement lineage, audit, and document migration. ANYmesh owns node and
element numbering, source sampling, adjacency, crease decisions, and mesh
revision. ANYfem owns FE assignment and adapter construction. ANYsolver owns
the validated director arrays after handoff and the shell formulation.

The following operations are forbidden in shell element, assembly, Newton,
arc-length, material-update, mass, geometric-stiffness, and recovery loops:

```text
face_point / face_normal / surface_normal
closest_uv
resolve_handle / resolve_ref
strict_audit
intersection queries
geometry serialization or migration
ChangeSet callbacks
```

The production handoff modules have no ANYgeometry import. No live geometry
object is stored on a shell, reference record, batch, or analysis session.
Geometry source evaluation is allowed only in an upstream adapter or a cold
compatibility fixture. The analytical FE tangent is derived from FE
interpolation and never from finite-difference CAD normals.

## Model-level provenance header

`GeometryProvenanceHeader` stores the shared metadata once:

```text
source_geometry_model_id
source_geometry_revision
source_geometry_schema
source_geometry_package_version
source_geometry_document_checksum (optional)
source_geometry_audit_status
source_geometry_audit_certifiable
source_geometry_tolerance_summary
source_units
source_local_origin
source_coordinate_transform_fingerprint
source_mesh_revision
source_mesh_generator_version
adapter_marks_mesh_stale
```

The version gate accepts `0.2.x`; the provenance schema gate accepts 3 and 4.
This acceptance does not parse either document schema. The header rejects a
false certification flag for `clean_certifiable`, or a true flag for any
other audit outcome.

The UUID, checksum, units, transform fingerprint, tolerance summary, and mesh
generator version are model metadata. They are not repeated per element.

## Compact model-owned tables

`GeometryProvenanceTables` contains:

- one header;
- a deduplicated entity-kind table;
- compact handles containing only `kind_index`, integer entity ID, and cold
  source state;
- replacement-lineage records;
- support-surface type/fingerprint records;
- explicit attachment/junction intent records;
- one precomputed deterministic SHA-256 fingerprint.

At the adapter boundary, `SourceEntityHandle(model_id, kind, entity_id)`
retains full cross-package identity. `GeometryProvenanceTables.build` checks
every model UUID against the shared header, then strips the repeated UUID and
deduplicates kind strings. A wrong-model handle fails before compaction.

Geometry IDs remain source IDs. They are not FE node numbers or FE element
numbers. Reordering or renumbering the FE mesh does not alter source identity.
A source face normally produces many FE elements, each referring to the same
model-table indices.

The neutral `to_dict()` payload contains no geometry document. It records one
contract marker, the shared header, model-owned tables, and the canonical
fingerprint. `from_dict()` validates this neutral payload and its fingerprint;
it does not call a geometry deserializer.

## Per-shell source association

Each geometry-backed Q4 may store one `ShellSourceAssociation` containing only
integers:

```text
part_handle_index
sheet_handle_index
face_use_handle_index
face_handle_index
support_surface_index
source_face_use_orientation (+1 or -1)
material_region_index
thickness_region_index
mesh_region_index
lineage_index
```

`pack_shell_source_associations()` produces a C-contiguous, read-only
`int64[n_shell, 10]` array. The model UUID and document metadata are absent
from this per-element payload.

For a certified geometry-backed association, part, sheet, face use, and face
must all name active records of the expected kind. A direct FE model carries
no table/association and reports:

```text
geometry_provenance    unavailable
geometry_certification not_claimed
director_provenance    reconstructed, legacy, or user_supplied
```

## Face-use orientation

The source `FaceUse.orientation` is authoritative for:

- the positive shell director;
- pressure side;
- positive and negative shell faces;
- material axes;
- top/bottom recovery.

The adapter checks node ordering against this orientation. It either corrects
node order while building the immutable FE model or rejects the model.
`validate_face_use_orientation()` implements the fail-closed check. The
element hot kernel never guesses, flips, or repairs source orientation.

For numeric mesh reconstruction, `orientation_signs[n_shell]` converts each
connectivity-derived facet normal to its already-validated source side. This
also lets two equivalent elements with opposite local traversal produce the
same physical director.

## Numeric corner geometry

The improved Q4 reference builder accepts numeric data only:

```text
corner coordinates               float64[4,3]
reference corner directors       float64[4,3]
optional source UV               float64[4,2]
optional source tangent 1        float64[4,3]
optional source tangent 2        float64[4,3]
source face-use orientation      integer sign
director provenance              compact integer code
geometry provenance index        compact integer index
```

UV and tangent samples are optional cold qualification evidence. They do not
replace continuum-shell interpolation during analysis. Corner coordinates and
directors are included in the numeric reference fingerprint, so changing
either invalidates reference data.

`SourceCornerSamples` freezes optional `float64[n_q4,4,2]` UV and paired
`float64[n_q4,4,3]` tangent arrays. Tangent pairs must be finite, nonzero, and
linearly independent. These samples remain outside the element hot payload.

## Director provenance and priority

Permanent provenance labels and numeric codes are:

```text
source_surface_exact
source_surface_sampled
sheet_aware_mesh_reconstruction
local_element_reconstruction
legacy_center_frame
user_supplied
```

The production priority is:

1. validated source-surface or sheet-aware corner directors from the adapter;
2. validated sheet-aware mesh reconstruction;
3. deterministic crease-aware local mesh reconstruction;
4. explicit legacy fallback for an old model, with a diagnostic.

A facet-derived director is never labelled as exact source-surface data.
`prepare_supplied_corner_directors()` accepts only finite `(n,4,3)` arrays,
requires unit vectors, checks source orientation and local Q4 compatibility,
and records one compact code per corner. It does not silently normalize bad
input or silently fall back.

## Sheet-, part-, and crease-aware reconstruction

`reconstruct_corner_directors()` is a permanent one-time fallback for meshes
without supplied source directors. Inputs are:

```text
node_coordinates                 float64[n_node,3]
connectivity                     integer[n_q4,4]
part_indices                     optional integer[n_q4]
sheet_indices                    optional integer[n_q4]
continuity_indices               optional integer[n_q4]
orientation_signs                optional integer[n_q4]
crease_edges                     optional node-index pairs
declared_intersection_edges      optional node-index pairs
```

The algorithm is deterministic and linear in Q4 count plus shell adjacency:

1. validate each Q4 with tolerances scaled from its FE edge lengths and
   machine precision;
2. form an oriented facet area normal without using absolute-position cross
   products;
3. build edge adjacency;
4. allow smoothing across an edge only when exactly two Q4s use it, their
   part/sheet/continuity indices match, no explicit crease/intersection blocks
   it, and the oriented normal jump is within the crease angle;
5. build a smooth fan separately for each `(element corner, mesh node)`;
6. average only that fan with area-times-corner-angle weights;
7. normalize and revalidate every element-corner director;
8. freeze the C-contiguous director and provenance arrays.

Boundary and non-manifold edges do not connect smoothing fans. Separate parts,
separate sheets, declared intersections, explicit sharp edges, and declared
continuity splits never average even when they share one global node.

The field is stored as `float64[n_q4,4,3]`, not as one normal per global node.
The same global rotational DOFs can therefore rotate different initial
directors on different shell sides. This preserves the FE kinematic coupling
without erasing a sharp reference-surface discontinuity.

The reconstruction is invariant, to floating-point tolerance, under global
translation, orthogonal rotation, FE element reordering, and FE node
renumbering. It uses no element ID as a geometric key.

## Director and Q4 quality diagnostics

The cold quality records include:

- area and characteristic length;
- minimum and maximum edge length;
- corner angles;
- two-triangle warpage angle;
- director norm error;
- minimum director/facet alignment;
- maximum within-element director spread;
- smooth, angular-crease, declared-crease, region-boundary, boundary, and
  non-manifold edge counts;
- minimum and maximum smooth-fan size;
- smooth-fan component count;
- a numeric reference fingerprint.

These are FE quality measures. Their tolerances are derived from FE dimensions
and machine precision. The source geometry tolerance summary is retained for
provenance only and is never reused as a shell Jacobian, rank, tangent, or
nonlinear convergence tolerance.

## Replacement lineage

Replacement resolution is upstream work. The source adapter may retain a
`ReplacementLineageRecord` as evidence, but a shell association must point to
the selected active descendant. A resolved lineage requires:

- the original record to have `replaced` state;
- one or more active descendants;
- one explicit selected active descendant for this association;
- `resolved_unambiguous` status.

The solver rejects associations retaining:

```text
deleted_without_descendant
unknown
blocked
ambiguous_replacement
deleted, unknown, blocked, or replaced handle state
```

No lineage is resolved during assembly or a nonlinear iteration. If a split
face yields several descendants, the adapter maps every new shell element to
its unambiguous active face before publication.

## Member identity and coupling intent

`MemberSourceAssociation` identifies a physical beam with compact indices for
the source member, optional member-edge use and geometry edge, source part,
and normalized member parameter range. A physical member may span several
geometry edges and several FE beams without losing member identity.

`CouplingIntentRecord` retains explicit attachment and/or junction handles,
their owner-defined kinds, and optional member/face/edge parameters. Coupling
is constructed from this intent upstream. It is not inferred merely because a
beam axis and shell, two shells, or two coincident parts are geometrically
close. `KEEP_SEPARATE` or absent declared intent remains separate.

Groups and tags stay selection/presentation metadata. They are not a
substitute for `Member`, `Attachment`, or `Junction` identity.

## Audit and certification

ANYgeometry `strict_audit()` is run upstream. ANYsolver accepts exactly these
compact outcomes:

```text
clean_certifiable
clean_not_certified
issues_present
unclassified_candidate
audit_not_run
provenance_unavailable
```

Only `clean_certifiable` may set the certifiable flag and support a certified
geometry-ancestry claim. A populated header cannot claim
`provenance_unavailable`; direct FE models represent that case by omitting the
header.

The solver records the outcome. It does not rerun or reinterpret the geometry
audit.

## Stale mesh and cache invalidation

The ownership chain for geometry changes is:

```text
ANYgeometry ChangeSet
    -> ANYmesh/ANYfem resolve, remesh, and remap as required
    -> publish a new immutable mesh/FE revision
    -> construct a new solver model/session
```

`validate_provenance_snapshot()` performs O(1) checks for expected model UUID,
geometry revision, mesh revision, and the adapter stale flag.
`GeometryProvenanceTables.fingerprint` is precomputed once.
`analysis_provenance_fingerprint()` combines it with topology, numeric
corner/director, and material/section mapping fingerprints for coordinator
integration into `AnalysisSession` and nonlinear-plan keys.

A changed mesh revision, topology, coordinates, directors, source orientation,
material/section mapping, mismatched source revision, or stale adapter flag
invalidates the session/reference plan. An active nonlinear solve is never
partially mutated from a `ChangeSet`.

Changed-AABB remeshing remains an ANYmesh/ANYfem integration point. It is not
implemented inside ANYsolver.

## Serialization and memory rules

- Store the source UUID/checksum/header once.
- Store source entity kind strings once in the model kind table.
- Store source support and intent records in model tables.
- Store only compact integer indices per shell/beam/coupling.
- Store directors as C-contiguous `float64[n_q4,4,3]`.
- Store director provenance as `uint8[n_q4,4]`.
- Never put source handles, UUID strings, checksums, Python dictionaries, or
  geometry objects in a compiled element kernel.
- Never claim geometry certification for a direct FE model.

The compact provenance lookup is O(1) during reference-plan construction and
adds no per-iteration work.

## Current upstream activation gap

The read-only sibling snapshot already provides useful pieces:

- ANYgeometry 0.2.1 exposes model-bound `EntityHandle`, structural Part/Sheet/
  FaceUse/Member/Attachment/Junction records, explicit resolution, schema 4,
  and strict audit;
- ANYmesh `Mesh` carries `geometry_model_id`, `geometry_revision`, local face/
  sheet/member element maps, and coupling records;
- ANYmesh structural meshing builds components from persistent Sheet/Member
  ownership plus Attachment/Junction intent rather than proximity;
- ANYfem native meshing publishes generation-tokened component meshes and a
  certification boolean.

The inspected public adapters do not yet publish the complete solver-neutral
payload in this document. Specifically absent from one end-to-end publication
record are:

- package/schema/checksum/audit/tolerance/transform provenance header;
- a distinct published mesh revision in the neutral `Mesh` payload;
- authoritative per-element face-use handle and orientation;
- resolved lineage and support-surface fingerprint tables;
- per-Q4-corner source directors, optional UV/tangents, and provenance codes;
- compact per-element part/sheet/face-use/face table indices;
- a final ANYfem-to-ANYsolver adapter that constructs these tables and wires
  their index plus reference directors onto improved `ShellElement` records.

Until that activation lands, qualification uses synthetic neutral fixtures and
numeric reconstruction. This is a permanent contract test, not a temporary
solver-owned clone of geometry records. End-to-end geometry activation must
remain reported as incomplete until the upstream adapter emits the complete
payload and coordinator wiring consumes it.

## Integration checklist

Before coordinator activation:

1. add immutable optional `reference_directors` and
   `geometry_provenance_index` inputs to improved Q4 records;
2. build model tables once and validate all shell associations in cold model
   construction;
3. prepare supplied directors or reconstruct the numeric fallback once;
4. include table and numeric reference fingerprints in session/plan keys;
5. preserve the face-use sign in pressure, material-axis, and top/bottom
   conventions;
6. keep source tables out of compiled hot arrays except compact integer
   indices needed for reporting;
7. serialize the neutral handoff, not a geometry document;
8. rerun combined native-hybrid activity/deletion and S4 regressions after
   final branch integration.

No geometry certification or end-to-end activation claim is valid until every
applicable item passes.

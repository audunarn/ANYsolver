# GE-B3 G3c physical correction partition recovery V3

## Purpose and preserved incidents

This successor changes only the correction execution and evidence-composition
harness.  It changes no mechanics, state definition, graph, fixture, scientific
assignment, tolerance, public API, default, or 234-assignment rehearsal
inventory.  The accepted predecessor packets and the failed node-157 incident
remain governed by the V1 correction addendum and V2 inheritance revision.

The corrected monolithic `R-GUARDS` rehearsal launched from commit
`4ae10aeb156016cfab730ece84389f624345b6ef` was externally interrupted before
its coordinator could write a terminal process record.  It is preserved only as
process-incident diagnostics at
`rehearsal-r-guards-4ae10ae-interrupted-gyj6_g4t`.  Its closed-world file-tree
inventory has 1,039 files, 67,930,103 bytes, and canonical manifest SHA-256
`22ed29bb4d10fd699c1f75d081de2296d099e75d40f31ef0892504c866663a0f`.
The manifest is the SHA-256 of the canonical JSON list of relative POSIX path,
byte count, and file SHA-256 rows ordered by path.  Nodes 90 through 220 were
launched, nodes 90 through 217 have terminal accepted child process records,
and nodes 218 through 220 contain only incomplete process diagnostics.  There
is no root `process.json`, `scientific.json`, or `receipt.json`.  These bytes are
not scientific evidence and no record from the interrupted wave may be reused.

## Exact guard segments

The unchanged `R-GUARDS` assignment range 90 through 233 is divided into six
ordered, disjoint segments.  Each segment runs in its own fresh exclusive
directory and creates a canonical aggregate only after all of its child
processes are terminal and accepted.

| Segment | Assignment indices | Canonical assignment-slice SHA-256 |
|---|---:|---|
| `R-GUARDS-A` | 90--113 | `6981dc38e504841a158b7f9e747e33cf0e94d7c9736fdee60c276fb12792fd98` |
| `R-GUARDS-B` | 114--137 | `761a4c222e150bccc9f501ebcc64c150855d8d63bee2c30e03c4239355bc95af` |
| `R-GUARDS-C` | 138--161 | `c6f2002fec928892800c1d61b60ea2822e5c8c838a700ce8d6b4dd96a015b518` |
| `R-GUARDS-D` | 162--185 | `1eac165b1ad6a6dae98c5302949738a387d476497b62c3f7482e4408eaaa4b1c` |
| `R-GUARDS-E` | 186--209 | `8046ab0073bf7128568cb62a33e7286432edf18a8ea52f0e0b1940260b059c63` |
| `R-GUARDS-F` | 210--233 | `2bece23cb08bafb2bdee82f97c7245dc03429b4c1e6a65293907bfc0ad69b37c` |

The canonical segment manifest has schema
`GE_BEAM3_G3C_PHYSICAL_CORRECTION_GUARD_SEGMENTS_V1`, binds the unchanged
whole-inventory and rehearsal-partition-manifest hashes, contains the table's
ordered segment IDs, explicit index lists and assignment-slice hashes, and has
SHA-256
`8ae0c6560960ef9bf9035838abb5daae056372d7aae0f9426945330a898bf477`.
Every segment lease, process record, aggregate and receipt binds this manifest
hash and its own assignment-slice hash.

Every segment independently revalidates the clean successor, complete input
DAG, implementation review, seven accepted predecessor evidence descriptors,
the immutable node-157 failure incident, runtime-compatibility record, and
predecessor history packets before launching.  It uses at most three workers,
one numerical-library thread per child, 24 GiB per process tree, 600 seconds per
child, a 120-second inactivity watchdog, and 1,800 seconds for the invocation.
There is no automatic retry.  Failure produces process diagnostics only.

Segment execution is strictly serial.  `R-GUARDS-A` binds the seven inherited
prerequisites.  Each later segment binds those same seven prerequisites plus
every earlier accepted segment in order.  Thus B cannot launch before accepted
A evidence exists, C cannot launch before accepted A and B evidence exist, and
so on through F.  The runner rejects reordered, missing, duplicated or foreign
segment prerequisites before creating output.  At most one segment invocation
is authorized at a time, so the shared three-worker ceiling is never multiplied
across segment coordinators.

Successful segment evidence uses exact schemas, ordered assignment indices, a
closed-world node/file DAG, and terminal
`COMPLETE_GE_BEAM3_G3C_PHYSICAL_CORRECTED_GUARD_SEGMENT_ONLY`.  It retains
`full_g3c_qualified=false` and `production_qualified=false`.

## Inert guard and rehearsal unions

After all six segments have been independently accepted, an inert finalizer
recursively validates their complete evidence DAGs, exact ordered coverage, and
the seven inherited prerequisites.  It performs no mechanics import or child
execution.  It creates the single corrected `R-GUARDS` aggregate with records
90 through 233 and terminal
`COMPLETE_GE_BEAM3_G3C_PHYSICAL_CORRECTED_GUARDS_PARTITION_ONLY`.  Its receipt
binds all six segment descriptors, both preserved process incidents, the two
runtime identities, and the exact current authority.

The existing inert correction-union stage then combines unchanged inherited
records 0 through 89 with the accepted corrected guard records 90 through 233.
Its terminal remains
`COMPLETE_GE_BEAM3_G3C_PHYSICAL_CORRECTED_REHEARSAL_ONLY`.  Neither union
executes or imports mechanics.

The segment and union modes are mutually exclusive and fail before output
creation when their exact argument or prerequisite inventories differ.  Extra,
missing, reordered, duplicated, overlapping, foreign-candidate, foreign-runtime,
self-rehashed, noncanonical, reparse, or hash-mutated inputs are rejected.

## Boundary

This recovery authorizes only the six bounded corrected guard segments and the
two inert composition stages after independent design and implementation
review.  It does not authorize formal G3c, production qualification, selector or
default changes, versioning, publication, or integration.  The interrupted
wave remains an administrative process incident and is not a scientific
result.

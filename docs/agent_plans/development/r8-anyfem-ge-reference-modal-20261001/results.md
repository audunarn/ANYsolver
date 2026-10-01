# ANYfem explicit GE reference-modal inputs — 1 October 2026

Consumer source committed at`f4bb5ed` on its experimental integration branch;
paired solver source at`a9d22b54`. No main changes.

`ExperimentalGEReferenceModalPanel` gives the existing public GE modes operation
a strict, separately selected consumer input record. Supported and explicit
modal-only free-free boundary policies, native inertia, Q4 density, request and
optional model identity survive standalone and native Project save/reopen.
Serialization owns its inputs and does not assemble a global owner or factor.
Absence of a supplied solver identity is explicit; no identity is invented.
When supplied, the canonical binding is checked against the public owner.

The existing Project selector dispatches the new schema to public `modes`.
Unsupported finite/batch controls reject before creating the owner. S3,
material histories, lines, footprints and incompatible policies are excluded.
Results retain the solver's numerical/cancellation status and experimental
meaning. All old schemas, selectors and ordinary static behavior remain.
Shared pure component parsing replaces duplicate shell/beam input decoding;
the consumer contains no new mechanical operator.

Frozen three-file consumer source passed37 focused source checks. The first
source collection used pytest's reserved parameter name `request`; no tests
executed. Its exact snapshots/log/XML remain, followed by a fresh V2 run after
the test-only rename. Product behavior or tolerances were not changed.

Paired installed artifacts: solver wheel SHA256
`4ddde5790ce72697d20425186473d1d5066f84156287d9d9083ea1f059643ccd`,
consumer `57ee44eff01a3453082f1e1a9c528acf9aa2ac35eb2f0a1959d3428b764e4b2c`.
All391 solver and98 consumer Python modules match source/wheel/site byte-for-byte.
New37/37 and legacy149/149 pass with zero errors/skips;275/278 observed imports
are onsite. Effective pools and Numba1/JIT disabled are checked in the actual
process before/after execution. Windows/Python3.14.2,600s/8GiB per process tree,
serial jobs. New supervised wall/peak4.681s/184492032 bytes; legacy
201.131s/205950976 bytes. These are check costs, not a performance claim.

An independent old/current installed control saves and reopens seven legacy
GE input records: point-v1, J2/fibre-v2, Q4-pullback-v3, staged-v4, Q4 and mixed
nodal footprints, and BL5. Every serialized file is byte-identical. The current
control uses274 onsite imports; the unchanged baseline uses273. No numerical
equivalence or qualification is inferred solely from persistence bytes.

Independent source/artifact review finds no blocking issue in this consumer
scope. The standalone public Project example also runs through both policies
on the paired artifacts:275 onsite imports, two requested flexible pairs and
one factorization each; free-free returns six rigid fields, supported returns
zero. Free frequencies55.03428970322184/159.8266970706792Hz, supported
31.160280574040108/160.1090561857179Hz. These are example results, not externally
qualified frequencies. Supervised wall/peak2.085s/162213888 bytes free and
2.091s/162267136 bytes supported. The initial example harness assumed three
pairs despite the declared count2; its assertion failure and exact runner/source
are retained. The repaired harness checks the declared request count; no product,
example or tolerance change. [Example review](example-review.md) is separate
from the unchanged [consumer review](independent-review.md); neither has a
blocking finding in its stated scope. [Raw archive](raw-v1.zip) and
[identity](raw-v1-identity.json) preserve178 files, each reread against its
SHA256 inventory. Archive SHA256
`9bc32f1f3108f6b67861223cd754fb6f3c27299061347986358aee07a9043610`.
Exact sources, artifacts,
failed collection, effective settings and raw records are retained for delivery.
F07/G4B/consumer/engineering-frequency/external/scale and aggregate acceptance
remain OPEN. Modal input persistence is not a complete spectrum or accepted-state
checkpoint. No main merge, publication, legacy equation or authority change.

# Response preparation timings and bounded library scopes

`PreparedStaticResponseEvaluator.diagnostics()['source_response']` now exposes
`preparation_timings` and `preparation_memory_peak_required_bytes`. Timings use a
held native monotonic clock; no tracing, monitoring or profiling hooks are used.
The response authority guard pins the clock alias and source helpers.

The timing phases distinguish snapshot/operator setup, pattern ingress,
load/RHS construction, basis solve, basis certification/publication, recovery
preparation and final accounting. The element-library subrecord separates owned
scope entry/exit, zero-schema recovery, all verification probes, all native
response columns, finite immutable publication and caller safe points. Counters
record schema elements, actual probe/column evaluations, scope counts and maximum
recipe membership. Durations are telemetry, not certificates or tolerance rules.
`preparation_memory_peak_required_bytes` records the maximum existing policy
requirement observed during preparation, including bounded pending tile
containers. Unlimited per-case memory checks retain their original fast return;
telemetry does not add per-field snapshot copies or a new memory limit.

The measured physical development fixture uses 200 independent supported axial
beams, 20 actual dense distributed load patterns, a nonzero baseline and five
combinations, with reactions explicitly unrequested. Original one-recipe scopes
spent 9.0138833 s in entry/exit out of 9.5390807 s library preparation and
15.1372736 s whole preparation. Bounded 64-recipe scopes reduced library setup
to 0.5996477 s and whole preparation to 5.927835 s on that one changed run.
These measurements preceded the additional memory-peak telemetry; final source
performance has not been remeasured. Evidence is under
`C:/ANYworkspaceWork/anypost-20261012/preparation-scale-evidence`.

Both passes retain their original order: zero/schema capture, memory admission,
then all element verification and original baseline/pattern columns. Each of
200 elements still receives all 12 original library probes and all 21 original
columns. No rows, probes, constants, measures or physical expressions are pruned.
The 64-recipe tiles split before the original 128-element caller cadence; token
observations still occur at indices0 and128 on this fixture, outside owned
scopes. Every scope receives all exact recipes, retains full entry/exit authority
and the original per-recipe/native checks. Temporary column publication is
bounded to the tile and stays outside its scope. Stricter transient-container
accounting is preserved rather than reduced to meet a historical test budget.

Original full-vector per-case combination, load/source agreement, solve,
backward-error certification, canonical fallback and replay2 corrections are
unchanged. Original and changed library/force/solution columns, ordinary source
fields, complete capsules and case admission fingerprints matched bytewise;
the two runs each checked 70 source/runtime component arrays. Actual second
caller-boundary cancellation and source-helper/clock mutation tests refuse
without success and leave no owned scope active.

Source snapshot diagnostics now separately time reaction-map capture, affine
compilation and envelope-plan capture. The `affine_recovery.*_seconds` entries
inside `snapshot.phase_timings_seconds` separate native probes, global-vector
allocation, admission, schema, affine comparisons, private owner capture,
verification work, span entry/exit and publication. Counters retain all original
probes and owner comparisons. Internal clocks accumulate nanoseconds; the public
snapshot phase map converts durations to seconds. Earlier development artifacts
had `_ns` suffixes inside that seconds map; those artifact values are seconds.

On the same 200-beam fixture, the first attributed baseline spent4.9099607 s in
400 separate private owner comparisons. Root adopted staging at most64 exact
private recipes with both original scale records, then verifying every record
under a full entry/exit owned scope. All live model/config observations and
native element/amplitude/random probe order remain outside these spans. Saved
records/local vectors preserve original dtype, shape and bytes in alias-free,
immutable buffers. Staging checks the existing resource policy before copying,
including temporary array/Python storage. Pending records are capped at4 MiB;
an oversized individual record uses the original per-call verification path.
Incoming native records are frozen before any prior private verification can
alter a native cache. Publication occurs after successful scope exit. Changed
200-beam preparation measured1.7785658 s, compiler0.4615723 s, with all3200 native
probes and400 owner comparisons in four scopes; complete prior capsule/library/
field fingerprints were unchanged. This timing preceded the subsequently added
publication-helper mutation guard; it is not a final-source performance claim.

Delayed verification pins its executable/helper/global bindings before and after
caller config observations and publication. Helper/checker mutation and
cancellation refuse; no successful snapshot escapes. Aggregate refusal records
retain every defect, but their order can differ when a later native-admission
defect is observed before an earlier staged comparison. Refusal order is
diagnostic, and never a case/tie/field-order guarantee. Tests preserve two defects.

Repeated library memory checks cache only immutable snapshot/operator/factor
storage. Factor-handle identity and actual factor byte count invalidate this
cache, including transition from no factor to a live factor. Dynamic envelope,
pending/numeric buffers and the actual configured limit are checked separately;
unlimited per-case behavior is unchanged.

A separate physical development profile uses1000 beams,20 distinct spatial
frequency patterns (sampled rank20), a nonzero baseline and20 dense combinations.
Preparation measured13.491592 s; auto export3.0594995 s, records3.7700599 s, with
complete capsule fingerprints equal. Its20000 element-case source-vector
oracles consumed0.1139202 s and derived source work0.1660333 s. The original
per-input full-vector oracle, source derived expressions, ingress/certification,
canonical fallback and exact runtime2 storage corrections remain unchanged.
This profile preceded a further checker-code identity refusal guard. It does
not establish final-source timings or linear scaling to100k elements/10k cases.
Full-global probes, live source guards, per-element source oracles, parity and
metadata/storage remain actual-scale risks. `trusted_capture` remains false;
no general shell,100k-element or10k-combination capacity is claimed. Current
evidence is under `C:/ANYworkspaceWork/anypost-20261012/source-scale-readiness-evidence`.

The next source profile attributes most outer export overhead to repeated
native executable/class proof checks. Existing public `batch_size` amortizes
the unchanged per-block checks; no new authority span or skipped guard is used.
On the same1000/20/20 source workload, `batch_size=16` produced two blocks,
20 certified cases and20000 original complete element-vector GEMVs. Auto and
records capsules matched each other and the prior batch1 capsule completely,
including associations, metadata and all field bits. Auto measured0.6293578s,
records1.2097393s and preparation8.0271344s. Process peakRSS was1.355GB; source
memory-policy preparation peak50.583MB, retained snapshot28.998MB, response
bases3.024MB and raw corrected rows2.08MB. These are actual development evidence
at1000 elements; no100k/10k capacity or linear scaling is established.

Numeric publication now directly consumes each original per-element `_combine`
result. The grouped trial did not remove the original oracle and only computed
an alternative already checked against it. Its removal changes no source field
bits or certification. Diagnostics label `numeric_vector_execution` as
`original_element_gemv`; `numeric_grouped_trial_tiles`,
`numeric_kernel_fallback_tiles` and `grouped_trial_seconds` are zero because no
alternative is attempted. Zero does not certify a grouped-kernel equivalence.
Actual primitive/displacement/derived replay corrections remain unchanged.

Staging accepts the same Mapping and float ndarray type families as the original
classifiers, normalizing them outside owned spans to immutable plain mappings
and base arrays with exact source dtype/shape/bytes. Normalized storage is
included before copying. A failed tile flush always clears its queue and
propagates global authority failures without blaming an element or retrying the
failed tile. Memory cache owners are retained by reference and compared with
`is`, with actual operator and factor byte counts included in validity.
The validity stamp also re-reads the snapshot's bounded array/CSR byte counts;
same-owner snapshot CSR growth cannot reuse an underestimated cached base.
Unlimited non-preparation checks retain their existing fast return.

Sink callback grouping and footer replay-guard counts vary with the existing
batch parameter. The public in-memory capsule does not retain those footer
diagnostics; a real public observing sink recorded75 guard checks atbatch16
versus201 atbatch1. All scientific capsule data matched without exclusions.
Stored row counts included all20 cases' axial stress and all six displacement
components. A whole displacement-vector mismatch emits all six rows, including
zeros; raw corrected storage cannot be estimated from UX alone. Next-size
preparation/storage and compressed disk demand require separate bounded
execution authority. Evidence/failures are preserved under
`C:/ANYworkspaceWork/anypost-20261012/source-scale-next-evidence`.

The actual10000 readiness attempt refused during primitive affinity probes and
also exceeded the observed RSS bound; it did not produce an archive or establish
capacity. These failure causes remain separate. Source inspection found that
rigid-mode construction allocated a dense total-DOFs by six-times-component-count
zero grid before skipping supported components. It now allocates the original
full grid lazily on the first unsupported component. All-supported models retain
component observations/metadata and return no candidate columns. Mixed/free
models retain the original width/order/values and numerical operations. Legacy
untransformed compatibility-rank diagnostics retain their nominal6*C value.
Frozen-wheel exact output/diagnostic/model-observation comparisons and a10000
supported-topology allocation guard verify this narrow repair; no repeated
10000 source solve or general performance/capacity claim is made.

# M26 — certified vectorized build in one pipelined pass

2026-10-10. Owner: Claude (Anthropic). Not merged, committed or published.
Pre-M26 comparator: `../../m26-prefix/solver/src` (the source after the opt-in
review, M25o).

## Change

`build_vector_recovery` (`src/anysolver/prepared_static_vectorized.py`) used two
passes over the recovered elements in chunks of `SAFE_POINT_STRIDE` (128): the
first read every element's zero record and schema for the storage estimate, then
`memory_check(estimate)` ran once, then the second pass probed every element.
Each chunk of each pass cost one safe point and one owned-recovery-scope entry, and
both run `require_native_source_authority` (the scope at entry and exit), which
costs tens of milliseconds per call. On the barge (4,245 recovered elements, 34
chunks) that was 68 safe points and 68 scope entries.

M26 pipelines the two passes. Each owned scope probes the chunk whose storage was
checked last and reads the zero records and schemas of the next chunk;
`memory_check` runs between scopes on the running estimate. A build with n chunks
now has n + 1 safe points and n + 1 scope entries (barge: 35 and 35). Every element
still enters two scopes (once read, once probed), so the per-element native scope
work is unchanged; the saving is the fixed cost per scope and per safe point.

The arithmetic is unchanged: each element's zero record is read once and reused
by its probe, probes are per element (random probe seeded by the element id), and
the maps are assembled in the original element order.

## Behaviour changes (documented)

1. **Memory check.** `memory_check` is called once per chunk with the running
   estimate instead of once with the total; the last call receives the same full
   estimate as before. An element's maps are still allocated only after a check
   whose estimate includes them (the M22 F4 property). A model over the budget is
   now refused at the first chunk whose running estimate exceeds it, after the
   earlier chunks were probed, and the refusal reports that running estimate
   (a lower bound of the full requirement) instead of the full estimate. An empty
   union calls `memory_check(0)` once, as before.
2. **Error precedence.** Before, every chunk's zero-record and schema refusals and
   the memory refusal came before any probe refusal. Now a probe refusal in an
   earlier chunk (for example "not affine") comes before a schema or memory
   refusal in a later chunk. Only models with several defects see a different
   first error.
3. **Cancellation granularity.** Each safe point is followed by probing one chunk
   and reading the next, about twice the work per interval of a former pass. Stage
   names: the first safe point is `prepared_response.vector_schema`, the others
   `prepared_response.vector_recovery`. Safe points and memory checks still run
   outside every owned scope.

## Identity evidence

- Cross-version probe `../../evidence/m26_vector_probe.py` (supported mixed model,
  317 recovered elements in 3 chunks: Q4 shells including warped ones, S3
  triangles, beams; pressure and nodal patterns; stress recovery and envelopes;
  lean selected reactions): pre-M26 and M26 JSON identity sections are equal
  (`m26-vector-probe-pre.json`, `m26-vector-probe-new.json`): the vector maps
  (groups, locations, element info, probe count, worst ratio, envelope sources),
  three evaluated pattern cases and the envelope. Run-dependent fields are
  excluded (solver signature, snapshot identity, timings). Schedule on that model:
  safe points 6 to 4, memory checks `[13278976]` to
  `[4156864, 9933728, 13278976]`.
- Barge: see below.

## Tests

`tests/test_prepared_static_response_m26.py`, 9 tests: maps bitwise identical for
strides 1, 4, 7 and 128; schedule (one safe point per chunk plus one, increasing
memory checks, last equals the full estimate); each chunk probed only after its
own check; a refusal at the second check probes only the first chunk; no safe
point or memory check inside an owned scope; empty union. Three schedule tests
fail on the pre-M26 source (`m26-claude-05-tests-on-pre`); the six invariants pass
on both. Regression sets: `m26-claude-01` 140 passed, 1 skipped (opt-in
assessment); `m26-claude-02` 112 of 115 (the three known pre-existing failures);
ANYfem `m26-claude-03-fem` 17 of 17; M26 tests `m26-claude-04-tests` 9 of 9.

## Barge benchmark (epoch m26)

Default mode (trusted capture off), certified vectorized, lean selected reactions
and output, `load_families=nodal,element,pressure`, 300 cases, block 4, 2048 MiB;
primary at even and holdout at odd positions; ABBA order (pre, M26, M26, pre);
system CPU 8-10% (quiet machine). Epoch m26: 650.6 of 1,500 s used (including the
228.9 s preparation profile), 849.4 s left.

| Run | Preparation | Segment after factorization (vector build) | History | Complete |
|---|---:|---:|---:|---:|
| Primary, pre-M26 | 84.26 s | 21.69 s | 19.72 s | 103.98 s |
| Primary, M26 | 83.55 s | 20.40 s | 19.53 s | 103.08 s |
| Holdout, M26 | 80.71 s | 20.37 s | 19.27 s | 99.98 s |
| Holdout, pre-M26 | 82.41 s | 21.39 s | 20.52 s | 102.93 s |

The vector build segment is 1.0 to 1.3 s shorter; whole preparation moves by 0.7
and 1.7 s, within run-to-run noise of about 1 s on the other phases. Peak RSS is
unchanged (1,124-1,135 MiB). Consumed outputs (`cold.selected-histories.jsonl`,
`cold.whole-envelope.jsonl`) are byte-identical between pre-M26 and M26 and to the
M25f default runs, primary and holdout (`../../evidence/m26-barge-summary.json`).

**The gain is about a quarter of the 4-5 s estimated before implementation.** The
estimate came from cProfile cumulative times, which inflate the call-heavy
authority checks several-fold (cProfile: about 50 ms per
`require_native_source_authority`; the measured saving implies about 35-40 ms per
chunk for one safe point plus one scope entry and exit, i.e. roughly 10 ms per
authority call). Lesson: estimate savings in authority-heavy code from unprofiled
timings, not from cProfile.

## Assessment

M26 is output-identical and keeps the M22 memory property, but saves only about
1 s (1.5% of preparation) and brings three small documented behaviour changes
(partial estimate in a memory refusal, error precedence between chunks, coarser
cancellation in the build). **Owner decision 2026-10-10: keep M26.** The remaining vector build time (about 20 s) is per-element work
(probing, zero records, per-element native scope entry), which M26 does not touch.

## Preparation cost map, sampled (M26b)

Because cProfile misled the M26 estimate, preparation was measured again with an
in-process stack sampler (`../../evidence/m26b_sample_preparation.py`: a thread
reads the main thread's stack about every 20 ms; each sample is weighted by the
wall time since the previous one; report `../../evidence/m26b_stack_report.py`).
Run `m26b-sample-prep-weighted`: default mode, M26 source, preparation 83.5 s,
4,229 samples, system CPU 9%. Caveat: samples land where the main thread releases
the GIL (BLAS calls such as `norm`/`dot`), so leaf functions are unreliable (for
example `norm` shows 38.7 s); attribution to long-running ancestors (phases and
large functions) is reliable to about 20 ms. An earlier count-weighted run
(`m26b-sample-prep-default`) is kept; it underweights GIL-holding C calls.

| Phase (inclusive) | Seconds | Main content |
|---|---:|---:|
| Snapshot capture | 60.0 | |
| - envelope recipe capture | 29.3 | Q4 stage compile 27.9 (guarded native recovery 16.3) |
| - load maps | 17.8 | oracle verification 8.3 (native `assemble_load_vector` 7.3), pressure recipe capture 7.1 |
| - stiffness assembly | 8.5 | native assembly under lease |
| - snapshot digest | 2.4 | S7 (owner decision) |
| After the snapshot | 21.5 | |
| - pattern source loads | 13.1 | native pressure kernel, 61 patterns (60 periodic phases + connection) |
| - vector build (M26) | 6.9 | affine probes 4.4, scope entry/exit 1.8 |
| - compiled pressure, solves, other | 1.5 | |
| ANYfem wrapper before the response factory | 1.7 | |

So the segment after factorization (about 20 s) is mostly pattern source loads,
not the vector build, which explains the small M26 gain. What remains is native
element math in pinned files (Q4 stage compile, pressure kernel, assembly) or a
deliberate independent witness (the native pattern loads also certify the compiled
pressure maps; the oracle check verifies the load maps against native assembly).
Remaining levers are owner decisions:

1. Trusted capture opt-in (`trusted_capture=True`, available): removes most of
   the guard overhead in recipe capture (about 13-19 s on the barge, M25f).
2. Pattern source loads from the compiled pressure maps (about 13 s): removes the
   native witness that certifies the compiled maps (the reason S9 was declined in
   M22); would need a replacement witness, for example a few natively evaluated
   phases.
3. Load-map oracle verification by sample instead of full native assembly (up to
   about 8 s): weaker verification.
4. S7 digest by array bytes (about 2 s): provenance format.
5. Parallel preparation (process pool for per-element stage compile and pressure
   evaluation): largest potential, but needs its own authority contract for
   results computed outside the preparing process.


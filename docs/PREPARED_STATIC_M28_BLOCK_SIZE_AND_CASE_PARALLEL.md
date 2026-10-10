# M28 — block size and case-parallel evaluation (study)

2026-10-10. Owner: Claude (Anthropic). Study only; nothing in `solver/src` changed.
Owner request after the M27 recommendation: measure the block size first, then
study case-parallel evaluation for long histories (10,000 cases). Epoch m28 (1,500
s, my allowance).

## Block size

One prepared barge evaluator (product route: certified vectorized, lean, default
mode), the same 300 primary cases evaluated as separate streams with block sizes
4, 16, 32, 64 and 4 again (`../../evidence/m28_block_screen.py`, run
`m28-blocks-primary`, `../../evidence/m28-blocks-primary.json`):

| Block size | History | Per case (incl. stream fixed cost) |
|---:|---:|---:|
| 4 | 19.16 s | 0.0639 s |
| 16 | 15.92 s | 0.0531 s |
| 32 | 15.08 s | 0.0503 s |
| 64 | 14.46 s | 0.0482 s |
| 4 (repeat) | 19.58 s | 0.0653 s |

Per-case records (flattened from the per-block rows) and the whole envelope are
identical for every block size. **The product default is already 32**
(`PreparedStaticEvaluator(batch_size=32)`, used by `iter_batches` when no size is
given); the benchmark harness has used 4 since M8, so earlier per-case figures
overstated the product's per-case cost by about 25%. 64 gains a further 4%.
Process RSS rose by tens of MiB with larger blocks. Not a further lever.

From the 300- and 600-case streams at block 32, the marginal cost is about
0.035 s per case plus about 4.5 s per stream (envelope detach and the harness's
28 MB envelope serialization). Serial projection for 10,000 cases: preparation
about 84 s + 350 s + 5 s, about 440 s.

## Case-parallel evaluation: design studied

Each of K worker processes runs the unchanged product route: it builds the model
from the same fixture, prepares its own evaluator and evaluates a contiguous chunk
of the case list (`../../evidence/m28_case_parallel.py` starting
`m28_block_screen.py` workers). The parent concatenates the per-case records in
case order, offsetting each chunk's input indices to their global positions, and
merges the chunk envelopes station by station with the serial fold rule (a
strictly better value replaces; a tie keeps the lower global input index; the
winner's case id, time and associated fields travel with it). No per-case logic
is duplicated; identity rests on deterministic preparation (equal snapshot digests
across processes, M25-M27) and on per-case results not depending on other cases
in the stream (shown by the block-size invariance and below).

## Identity: all 600 saved cases

Run `m28-caseparallel-600` (+ `-merge2` for the merge after a flattening fix in
the driver): serial stream versus 8 workers of 75 cases.

- Per-case records (case id, time, global input index, output DOFs,
  displacements, selected stresses and reactions, backward error, source label):
  identical digest for all 600 cases.
- Whole envelope: the merged file is byte-identical to the serial file (17,292
  entries).

Cost observations: eight concurrent preparations took 114-124 s each instead of
84 s serial (they contend for memory bandwidth and clock); each worker's 75-case
stream took about 11 s, mostly the fixed per-stream envelope cost; the parent's
pure-Python merge of eight 28 MB envelope files took 14 s. Peak memory of the
process group 9.2 GiB (8 workers plus the parent).

## 10,000 cases

The fixture holds 600 saved cases; the 10,000-case list cycles them (case k is
saved case k mod 600). Per-case cost does not depend on which saved case it is,
and the repeats create exact ties across chunks, which exercises the merge's tie
rule. Runs `m28-caseparallel-10k` (serial, then 8 workers) and
`m28-caseparallel-10k-w4` (4 workers), block 32:

| Route | Wall | Preparation | Cases | Merge | Peak memory (process group) |
|---|---:|---:|---:|---:|---:|
| serial | 465.6 s | 81.8 s | 381.1 s (0.038 s/case) | | about 1.2 GiB |
| 4 workers x 2,500 cases | 289.1 s (1.61x) | 118-121 s each | 154-156 s each (0.062 s/case) | 10.2 s | 4.7 GiB |
| 8 workers x 1,250 cases | 229.7 s (2.03x) | 97-115 s each | 94-98 s each (0.078 s/case) | 13.9 s | 9.2 GiB |

Identity: per-case records of all 10,000 cases identical to the serial stream for
both worker counts; the merged envelope file byte-identical to the serial file
for both.

**Contention limits the gain.** With 4 and 8 concurrent workers each case takes
1.6x and 2.0x longer per worker than serially, and each worker's preparation
takes about 1.4x longer. M29 compared the per-phase timings: every phase slows by
the same factor (1.86-2.02x at 8 workers), Python-heavy application work and
array-heavy recovery alike. That points to a shared memory-system limit (L3 share
per process and DRAM bandwidth on this desktop platform: AMD Ryzen 9 7950X, 16
cores / 32 threads, 64 MB L3 in two 32 MB halves, 127 GiB RAM) rather than to
specific kernels; the cause was not isolated (no hardware counters). System CPU
was 16-21% from other activity during the runs. With 8 workers the time splits into
replicated preparation about 50%, cases about 43%, merge about 6% (the merge is a
pure-Python study script over 28 MB JSON files; an array-based product merge is
expected to take well under a second, not measured).

## Options for a product version

| Option | 10,000 barge cases, 8 workers | Complexity | Identity argument |
|---|---:|---|---|
| A. Independent workers: each prepares from the model and evaluates a chunk; parent concatenates and merges | 230 s measured (2.0x) | low: the solver route is unchanged; new are chunking, envelope merge, diagnostics merge, failure policy | strong: unchanged product route per worker; all workers' snapshot content digests can be required to be equal |
| B. Prepare once, send the prepared state by value to case workers | about 190-200 s estimated | high: export/import of the whole prepared evaluator (several hundred MB, native owners for fallback cases) under the M27 trust requirements | weaker: needs the M27 provenance and transport contract |
| B with M27 parallel preparation | about 150-170 s estimated | highest | as B |
| M27 parallel preparation alone | about 430 s estimated (1.08x) | as M27 | M27 |

Option A needs the model in every worker. At the application level that is the
project and mesh (ANYfem already sends them to its job worker process); at the
solver level it would need a by-value model transport. Memory is about 1.15 GiB per
barge worker.

## Recommendation

1. Build option A as an opt-in at the application (ANYfem) level: worker count
   configurable (4-8 on this machine), default off; the parent requires equal
   snapshot content digests from all workers before merging, concatenates
   histories with global indices, merges envelopes with an array-based
   implementation of the fold rule, merges diagnostics, and on any worker
   failure fails the run (or reruns serially). Measured 1.6-2x for 10,000 barge
   cases on this machine; machines with more memory bandwidth may do better (not
   measured). Workers here were plain subprocesses with `PYTHONPATH` (study
   harness); a product version applies the M27 worker requirements that concern
   start-up, provenance and bounded operation.
2. Profile the per-case path for memory traffic (the envelope fold touches the
   whole 17,292-entry envelope state in every block; the vector maps are large):
   reducing it would speed up serial runs and loosen the contention that caps
   option A.
3. M27 parallel preparation stays lower priority for long histories (about 8% at
   10,000 cases); it matters for short runs and design iteration.

Benchmark harness note: future benchmarks should use the product default block
size 32 (the M8-era harness default 4 overstated per-case cost by about 25%).
Epoch m28: 1,409.3 of 1,500 s used.

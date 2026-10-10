# M27 — parallel preparation study

2026-10-10. Owner: Claude (Anthropic). Study and prototype only: nothing in
`solver/src` changed. The prototype lives in a separate copy,
`../../m27-prototype/solver/src` (M26 source plus the hooks below; the first
version is kept in `../../m27-prototype-v1`). Owner request: "Keep it.
Investigate parallel. Use high effort for external review if needed."

## Summary

- Barge preparation with 8 isolated worker processes: 47.8 s (v1) and 48.4 s (v2
  repeat) against 82-113 s serial in the same sessions (1.7-2.4x), and 1.7x against
  the M26 quiet-machine 83.5 s; one noisy v2 8-worker run took 60.6 s (1.36x).
  16 workers: 44.8 s (v1). Every successful run's consumed outputs are
  byte-identical to the serial route.
- What the evidence shows: identity of the compared results (all 3,185 Q4 stage
  kernels and 194,285 pressure kernel vectors bitwise; barge consumed outputs
  byte-identical in seven runs; small-model digests of maps, snapshot, force
  columns, case results and envelope); eight small-model configurations with
  outputs equal to serial (the normal run plus seven failure and ownership
  checks); and one deliberately unequal negative check showing the witness limit.
- What it does not show: identity for every admissible input, protection against
  caller code that changes both a worker and the parent's expected binding, or
  that the trust argument holds against a hostile startup environment. The
  prototype is not adoptable as is; a product version must meet the requirements
  listed below.
- Independent review (Codex `gpt-6-astra`, high effort, static): round 1 UNSOUND
  for the prototype's general identity and trust claims (measurements and the
  identity of the compared outputs accepted); round 2 on v2 and the rewritten
  report SOUND WITH CORRECTIONS, applied here (see "Review").

## Where the time is and what is independent

From the M26b time-weighted sample (preparation 83.5 s):

| Item | Seconds | Unit of independent work |
|---|---:|---|
| Envelope recipe capture (Q4 stage compile) | 29.3 | per element (3,185 exact Q4 owners) |
| Load maps: oracle verification | 8.3 | per load family (native assembly) |
| Load maps: pressure recipe capture (warm-up) | 7.1 | per element |
| Stiffness assembly | 8.5 | per element, summed in a fixed order |
| Pattern source loads (native pressure, 61 patterns) | 13.1 | per element and pattern, scattered in a fixed order |
| Vector build | 6.9 | per element (certification probes) |
| Snapshot digest, constraints, factorization, other | about 10 | sequential |

The per-element work is Python plus many small NumPy calls in the pinned element
modules and holds the GIL most of the time, so threads would gain little here (the
ANYmesh study measured threads slower than serial for comparable work). Processes
were therefore studied.

## Constraints

- The pinned element and assembly modules are not edited.
- Native cache keys embed `id()` values, so warmed caches must never cross a
  process boundary; only plain numeric results may.
- Generic pickling of native class instances can add `__slotnames__` to the native
  dataclass classes and change their authority facts; no solver object is pickled.
- Windows spawns. `multiprocessing` re-imports the caller's `__main__` in each child;
  ANYfem GUI jobs run in a daemonic `multiprocessing` worker, which may not start
  `multiprocessing` children. Plain `subprocess` workers avoid both.
- Every parallel result must equal the serial one byte for byte.

## Feasibility measurements (epoch m27)

Workers: `python -I` with a package `-c` bootstrap that prefixes `sys.path` with
the parent's package directories, then imports `anysolver`. Messages are pickles of
plain builtins, unpickled with every global refused. Private owners (element,
one-element mesh, material) are rebuilt from a by-value encoding that mirrors
`clone_plain`, including which scalar objects are shared.

Probes (`../../evidence/m27_parallel_stage_probe.py`, runs `m27-stage-probe-01/02`;
`../../evidence/m27_parallel_probe.py`, run `m27-parallel-probe-01`), barge, all
3,185 exact Q4 envelope owners:

| Work | Serial (in-process) | Workers (wall) | Bitwise mismatches |
|---|---:|---:|---:|
| Q4 stage compile, guarded | 28.8 s | 4: 10.0 s, 8: 6.0 s, 16: 4.6-5.7 s | 0 |
| Q4 stage compile, inside the native trusted scope | | 8: 3.8 s, 16: 4.0 s | 0 |
| Pressure kernels, 3,185 shells x 61 synthetic pattern pressures | 8.2 s warm-up + 28.5 s | 8: 7.1 s, 16: 5.2 s | 0 |

- Worker start-up 1.3-2.1 s, concurrent; the pool starts at the beginning of
  preparation, so it overlaps stiffness assembly.
- Peak working set per worker 150-175 MiB (16 workers: about 2.6 GiB extra).
- Guards cost: summed worker compute 35.9 s guarded (16 workers) against 10.8-14.5 s
  in the trusted scope (8 and 16 workers), so guards are roughly 60-70% of the
  compile time. In an isolated worker no object or callback of the caller exists,
  which is why the prototype uses the package's native trusted scope there; this is
  not a proof that no foreign code runs (see the trust boundary).
- Same `anysolver` source digest, NumPy version and BLAS build description in every
  worker (descriptive strings, not an authentication of the loaded binaries).

**Storage estimate.** The recipe `retained_bytes` (a `sys.getsizeof` walk) is not
reproducible across processes: it depends on scalar-object sharing (the codec
preserves it) and on CPython's per-class shared-key dictionary layout, which
depends on the class's history in the process. The snapshot digest excludes it by
design. In the parallel route the parent reports, at capture time, the storage of
the private owners it holds plus the kernel: cold owners for successfully staged
Q4 recipes and for pressure recipes warmed in workers; a Q4 element whose stage
compile declines is warmed in the parent (as in the serial route) before its
storage is recorded.

## Prototype

v2 (`m27-prototype`, after review round 1):

- `prepared_static_parallel.py`: `WorkerPool` (persistent isolated workers,
  length-prefixed plain messages, handshake on first use comparing source digest,
  interpreter, NumPy version and BLAS build description; after an in-band error
  reply every outstanding reply is read before the call fails, while a transport
  exception (for example a closed pipe) quarantines at once and the remaining
  workers are killed without draining; error replies, transport failures and a
  handshake mismatch quarantine the pool and kill its workers, while binding or witness
  mismatches and parent-side exceptions only send that phase to the serial route
  and the pool stays in use; an `Exception` while starting workers kills the ones
  already started; `close()` closes the pipes, waits up to 5 s and kills; reads
  and writes have no timeout), the input codec (plain numeric arrays and exact
  NumPy scalars only; anything else raises and means the serial route; staged
  kernel arrays and pressure results are transported by `dtype.str` without a
  dtype gate), and the worker loop. Worker stderr is discarded.
- Option `preparation_workers` (default 0 = unchanged serial route) on both
  evaluators. Each preparation creates and privately holds its own pool and passes
  it explicitly; the base evaluator sets the context variable to that pool or to
  None around its own capture, so a nested preparation (for example started from
  a progress callback) never adopts an outer pool. With `trusted_capture=True` no
  pool is created. Statistics (routes, witnesses, fallbacks per phase) exist only
  when a pool was created and only on the response evaluator; a start failure or
  trusted-capture suppression leaves none, and some inapplicable exits (no
  pressure owners in workers) record no route.
- Envelope recipes (`capture_owned_local_recoveries`): the parent builds the cold
  private owner and identity first and encodes the worker payload from that owner
  (one capture for both sides); each result must name the digest of the payload it
  was built from; the first element of each worker chunk is recomputed serially and
  compared at the byte level (pickled representation, so `-0.0` and NaN payloads
  count).
- Pressure recipes (`capture_pressure_recipes`): Q4/S3 owners with a scalar probe
  are rebuilt and warmed in their home worker and stay there; the parent keeps the
  cold clones they were encoded from and the payload digests.
- Pattern source loads: requests are keyed by (packet index, ordinal in the
  packet's pressure list); each result names its owner's payload digest, which must
  match; the native return must be an `ndarray` and its dtype, shape and bytes are
  transported by `dtype.str`, shape and bytes; one entry per worker is recomputed in
  the parent and must match type, dtype, shape and bytes. `evaluate_load_vector`
  keeps its loop, checks and scatter order and only takes the kernel output from
  the table.
- An exception in the parent's parallel machinery (not cancellation or interrupts
  raised in the parent) during payload building, worker calls or result
  validation, a witness or binding mismatch, follower or tuple pressure: that
  phase runs the serial route. Workers catch every exception, including an
  interrupt or `SystemExit` raised inside a worker, and report it in-band, which
  quarantines the pool and also leads to the serial route. v2 defect: an exception
  raised inside the pressure witness itself (rather than a mismatch) is not caught
  and aborts preparation.

v1 differed in: payloads encoded from the live model (a second capture), results
keyed by element id, pressure vectors coerced to float, float witnesses compared by
value, the pool adopted from an ambient context variable, no quarantine.

## Evidence

Small model (`../../evidence/m27_e2e_small.py`, run `m27-e2e-small-01`, v1, 4
workers): snapshot content digest, pattern force columns, vector maps, case results
and envelope identical to serial.

Failure and ownership checks, v2 (`../../evidence/m27_failure_checks.py`, run
`m27-failure-checks-02`, small grid model with Q4, S3, beams, pressure and nodal
patterns and envelopes, 2 workers). Outputs (maps, snapshot digest, force columns,
case results, envelope) were equal to serial in the first eight rows; the last row
is a deliberate negative check. The harness's per-scenario flag checked outputs
and routes only; the nested inner result (equal) and the killed first worker (exit
code 1) were recorded but not part of the flag, and the injected stage failure
happens before any transport, so partial replies and draining are not tested:

| Scenario | Route taken | Result |
|---|---|---|
| normal | workers for all three phases; 2 stage and 2 pressure witnesses | equal |
| injected stage failure | stage serial | equal |
| tampered owner digest in a pressure result | pattern loads serial | equal |
| tampered witness pressure vector | pattern loads serial ("pattern witness differs") | equal |
| worker killed before the pattern loads | pattern loads serial (pipe closed) | equal |
| nested preparation in a progress callback (`preparation_workers=0`) | inner serial, outer workers | both equal |
| `trusted_capture=True` with workers requested | no pool | equal |
| start failure of the second worker | no pool; first worker killed | equal |
| tampered **non-witness** pressure vector | workers | **outputs differ (undetected)** |

The last row is the limit of a sample witness: it detects divergence on the
sampled inputs only (the first entry of each worker chunk), not a wrong result
elsewhere, even a systematic one that spares the sampled inputs (for example one
affecting only S3 elements or a pressure range). The parallel route's correctness
therefore rests on workers running the same code and numerics (trust boundary
below), not on the witness.

Barge end to end (prototype, default mode, certified vectorized, lean, 300 primary
cases; `../../evidence/m27-barge-summary.json` for v1, `m27v2-barge-summary.json` and
`m27v2-primary-w8b` for v2):

| Run | Preparation | Envelope capture | Load maps | After factorization | Complete |
|---|---:|---:|---:|---:|---:|
| v1 serial | 95.7 s | 33.6 s | 22.7 s | 21.7 s | 119.3 s |
| v1 8 workers | 47.8 s | 5.9 s | 12.8 s | 14.6 s | 67.5 s |
| v1 16 workers | 44.8 s | 5.1 s | 12.4 s | 12.7 s | 64.4 s |
| v1 serial | 113.3 s | 40.0 s | 23.2 s | 30.9 s | 137.0 s |
| v2 8 workers (noisy: untouched phases also 40-70% slower) | 60.6 s | 7.6 s | 16.7 s | 16.1 s | 80.8 s |
| v2 serial | 82.3 s | 29.6 s | 17.6 s | 20.8 s | 103.8 s |
| v2 8 workers, repeat | 48.4 s | 5.9 s | 12.7 s | 15.0 s | 68.3 s |

All seven runs' consumed outputs (`cold.selected-histories.jsonl`,
`cold.whole-envelope.jsonl`) are byte-identical to each other and to M26. Both v2
8-worker runs took the worker route in all three phases with 8 stage and 5
pressure witnesses and no fallback (route records in their `stages.jsonl`,
`preparation_end`; the repeat is run `m27v2-primary-w8b`, preparation 48.41 s,
workers ready after 12.9 s). Machine load varied (system CPU 10-14%). Ratios
against same-session serial runs: 8 workers 2.0-2.4x (v1) and 1.7x (v2 repeat),
1.36x for the noisy v2 run; 16 workers 2.1-2.5x (v1). Parent peak RSS 1,169 MiB (serial 1,125 MiB); workers add 150-175 MiB
each.

Still serial with 8-16 workers (about 45 s): stiffness assembly about 8.6 s,
load-map oracle verification about 8 s, vector build about 7 s, the parent part
of the pattern loads, constraints, snapshot digest, factorization, ANYfem wrapper.
Moving stiffness assembly and the oracle check to workers is estimated (not
measured) to save up to 12-16 s before transport and assembly overhead.

## Trust boundary

The serial route admits results computed by authenticated package code in the
preparing process. The parallel route instead relies on workers computing with
the same code and numerics, isolated from the caller's in-process state:

1. **What isolation gives.** No caller object, callback or class crosses the pipe;
   caller monkeypatches in the parent are not inherited; the bootstrap is the
   package's own `-c` code, not the caller's `__main__`.
2. **What it does not give.** `-I` still runs site processing of the installation
   (`.pth` files, `sitecustomize`), and the bootstrap's path list is derived from
   parent module attributes when the pool starts. Startup code of the environment
   can therefore run in workers, as it did in the parent. A product version starts
   workers with `-I -S` and an explicit path list recorded at import (package,
   dependency and NumPy directories), and treats the installed environment as part
   of its trusted base.
3. **Same code and numerics: what the handshake checks.** The current
   `anysolver/*.py` file digest (computed on the first handshake, not at import),
   interpreter path and version, NumPy version, BLAS build description. It does not
   authenticate the loaded dependency closure (`anymaterial`, NumPy/SciPy binaries)
   or the effective numerical runtime state (BLAS thread limits, floating-point
   control settings). A product version records digests of the loaded package and
   dependency files at import, compares them in the handshake, and compares the
   effective runtime state reported by the worker.
4. **Results.** Plain arrays and scalars decoded by the parent, each bound to the
   payload it was computed from; a witness sample checks for systematic divergence
   only. A restricted unpickler is not a protocol validator (it does not bound
   sizes or validate schemas, and extension-registry opcodes bypass `find_class`
   for cached entries); a product version uses a bounded, schema-validated codec.
5. **The parent keeps order and assembly**: recipe order, admission, the
   `evaluate_load_vector` loop and scatter order, the authority checks around it,
   the snapshot digest.

Caller code that runs in the parent during preparation (progress callbacks) can
reach the pool object. v2 binds every result to its payload digest, so replacing a
worker's owner (for example with its own `pressure_owners` message) is detected
while the parent's expected digest is unchanged, and killing workers only causes a
fallback. A callback that changes both the worker's owner and the parent's expected
digest (`pool.owner_digests`, reachable in the parent) is **not** detected unless
the witness samples that element. The supported threat model for caller code
during preparation therefore has to be defined for the product version, with the
expected bindings and the acceptance helpers out of caller reach or revalidated
after every callback boundary (requirement 3).

## Observable differences of the parallel route

Outputs of all successful runs and positive comparisons are identical (the one
unequal result is the deliberate negative check). Differences:

- `retained_bytes` of parallel-captured recipes is the parent's cold-owner storage
  at capture time (smaller than the serial estimate); memory checks and
  diagnostics see that number. Worker memory, payloads and the pressure table are
  outside the library estimates; a 2048 MiB limit does not bound the process
  group.
- Parent owners of successfully staged Q4 recipes and of pressure recipes warmed in
  workers start cold (a Q4 element whose stage compile declines is warmed in the
  parent). Staged Q4 recipes never use their owner for recovery. A cold pressure owner warms on its first native evaluation in
  the parent (the pattern witness warms a few during preparation, after their
  `retained_bytes` were recorded).
- Work order: envelope admission for all elements runs before any capture; Q4 cold
  clones and worker compile run before the serial captures of other element types
  and the witness captures; eligible pressure warm-ups run in workers before the
  parent's serial captures of other pressure elements; the pattern witness runs
  before the first packet's family and refusal checks. A model with several
  defects can report a different first error, and an error inside the parallel
  machinery means a serial rerun of that phase, whose genuine error is then raised.
- Warnings and other stderr output of native code in workers are discarded.
- Cold versus warm and repeated-call equivalence of the admitted kernels is
  observed (all comparisons equal) but not established from their source.
- Owners in the parent and in workers are keyed by the element's internal id; the
  prototype relies on internal ids being unique and consistent with the mesh keys
  and does not validate it.

## Review

Codex `gpt-6-astra`, effort high, static bundle
(`../../evidence/m27-review/codex-review-1.md`), verdict **UNSOUND** for the
prototype's general identity and trust claims; the measurements and the identity of
the compared outputs were accepted. Disposition:

| # | Finding | Disposition |
|---|---|---|
| 1 | `-I` keeps site processing; "no caller code in workers" too strong | report corrected; product: `-I -S`, import-time path list |
| 2 | handshake does not authenticate loaded code or numerical state; digest timing misstated | report corrected; product: import-time dependency digests, runtime state comparison |
| 3 | ambient pool adopted by nested preparations; owners keyed by id | ambient adoption fixed in v2 (explicit, private pool; context set to None for nested captures; checked); id keying of owners remains (see observable differences) |
| 4 | pipe protocol desynchronised after a partial failure | fixed in v2 for transport failures and error replies (all replies consumed, quarantine); binding and witness mismatches fall back without quarantine |
| 5 | start-up and shutdown could leak or hang | partly fixed in v2 (an `Exception` at start, close with kill; checked); interrupts at start, blocking reads/writes and buffered close remain; product requirement 4 |
| 6 | codec loses structured dtypes, metadata, scalar subclasses | v2 input codec transports only plain numeric arrays and exact NumPy scalars, else serial; staged arrays and pressure results have no dtype gate (product requirement 5) |
| 7 | pressure vectors coerced to float, witness coerces too | fixed in v2 (type, `dtype.str`, shape, bytes transported and compared) |
| 8 | table keyed by element id | fixed in v2 (packet index and ordinal) |
| 9 | worker payload and parent identity captured separately | fixed in v2 (payload encoded from the parent's cold owner; digest binding) |
| 10 | fallback does not cover all exceptions; trusted capture still batched | fixed in v2 except exceptions inside the pressure witness (abort); no pool with trusted capture; order differences documented |
| 11 | restricted unpickler is not protocol validation | documented; product: bounded schema-validated codec |
| 12 | witness tuple equality compares floats by value | fixed in v2 (byte-level comparison) |
| 13 | diagnostics incomplete (pressure witnesses, fallbacks, start-up timing) | partly fixed in v2 (routes, witnesses and fallbacks per phase; start-up timed from the bootstrap); no statistics after a start failure, on the base evaluator or for some inapplicable exits (product requirement 1) |
| 14 | memory and observable-difference statements incomplete | report corrected |
| 15 | recommendation overstated; "only processes", "70% guards" | report corrected |

Round 2 (`../../evidence/m27-review/codex-review-2.md`): SOUND WITH CORRECTIONS.
Applied in this report: the callback threat-model gap (both binding sides
reachable), the quarantine scope, the witness-exception defect, the remaining
start/shutdown gaps, owner id keying, dtype gates on output paths, the temporal
provenance contract, sample-witness wording and scenario counts, headline numbers
per worker count, diagnostics gaps, further observable differences, and the test
requirements below.

Round 3 (`../../evidence/m27-review/codex-review-3.md`): SOUND WITH CORRECTIONS,
four wording corrections (draining only after in-band error replies; owners of
declined Q4 stage compiles are warmed in the parent; interrupts inside workers
become error replies; one unqualified identity sentence), applied here without a
further review round.

## Requirements for a product version

1. **Option and diagnostics.** `preparation_workers` (or a `ResourceConfig` field),
   default 0. Preparation-level diagnostics independent of pool construction:
   requested and effective workers, suppression or start-failure reason, and an
   explicit route (workers, serial, skipped, not applicable), witness count and
   fallback reason for every phase, on both evaluators.
2. **Provenance and numerical state over time.** Workers start with `-I -S` and an
   explicit path list; trusted origins of the interpreter, package and dependency
   files are recorded at import together with digests of the loaded files, and the
   relation between the recorded files and the executed modules is defined. The
   effective numerical state (BLAS thread limits, floating-point control settings,
   NumPy error policy) is pinned in workers and revalidated in the parent at each
   phase that uses worker results, not only at the handshake.
3. **Caller code during preparation.** A defined threat model for caller code that
   runs between phases (callbacks): expected bindings, the pool and the acceptance
   helpers out of caller reach or revalidated after every callback boundary; the
   new helpers in the authority tables; every request and reply correlated with
   the preparation and a request id; a non-reentrant protocol.
4. **Bounded operation.** Timeouts on start-up, writes, reads, draining and
   shutdown; cancellation safe points while waiting; cleanup on every unwinding
   path including interrupts; workers killed on cancel or parent exit (Windows job
   object); quarantine on any failure that invalidates worker trust or protocol
   state; a memory policy for the process group.
5. **Codec and outputs.** A bounded, schema-validated message codec (no pickle)
   with size limits; a supported-output contract for staged kernels and pressure
   results with dtype validation on every array path; unique capture handles (or
   validated internal-id uniqueness and mesh-key consistency) for owners.
6. **Fallback semantics.** Every exception from the parallel machinery, including
   inside witnesses, sends the phase to the serial route; cancellation and
   interrupts propagate; a defined contract for warnings (worker stderr), first
   error with several defects, and mutation during preparation.
7. **Kernel equivalence.** Cold versus warm and repeated-call equivalence of every
   admitted kernel established from its source (or measured per release) before it
   is moved to workers.
8. **Tests as enforced gates** (assertions and a failing exit status): handshake
   refusal; partial, malformed and stale replies; draining after an error reply;
   hangs and cancellation; witness mismatch and witness exceptions; binding
   mismatch and coordinated parent-state tampering; worker crash; start failure
   and interrupts at start; nested preparations; follower and tuple pressure; codec
   boundaries; duplicate occurrences and owner-id invariants; stage-declined
   routes; cold versus warm repeated evaluation; identity on small models and on
   the barge.
9. **ANYfem.** `subprocess` workers from the daemonic GUI job worker, with a policy
   for their CPU and memory.
10. **Later.** Stiffness assembly and oracle verification by element blocks summed
    in the serial order (estimated up to 12-16 s more on the barge, before
    transport and assembly overhead; needs whole-model by-value transport), and
    combining the trusted capture opt-in with workers.

## Recommendation

Parallel preparation is worth building: 1.7-2.4x on barge preparation with 8
workers in quiet same-session comparisons, with byte-identical outputs in every
successful run and identical results in every positive comparison made (the one
unequal result is the deliberate negative check). The prototype demonstrates
feasibility, not the final contract. Build the product version against the
requirements above, default off, with its own independent review before it is
enabled anywhere.

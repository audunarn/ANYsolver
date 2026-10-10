# M31 — further identical-result per-case levers

2026-10-10. Owner: Claude (Anthropic). Not merged, committed or published. Owner
request: "Step 1, then independent review" (step 1 of the M30 "Further levers"
list). Pre-M31 comparator: `../../m31-prefix` (solver and ANYfem sources). The independent
review of M30+M31 and the fixes made for it (M31b) are at the end; where this report
describes M31 before the review, that section says what changed.

## Profile that selected the items

cProfile of 320 barge cases on the M30 code (`m31-case-profile`, real time about
half the profiled time):

| Item | Profiled | Cause |
|---|---:|---|
| ANYfem `wet_element_pressures` | 2.77 s | Python loop per wet element: fluid side (439k calls), centroid/normal copies (508k calls), sorting the element ids; the pressure formula itself 0.06 s |
| `copy.deepcopy(self._operator_info)` per case | 1.42 s | the nullspace component lists (node ids), about 4,500 objects per case |
| response authority check (`_require_open`, about 3 per case) | 1.27 s | class-state and callable checks |
| `require_native_source_authority` (about 3 per block) | 1.16 s | |
| packet storage estimate per case | 0.60 s | recursive size walk over the pressure dict |
| lean selected reactions | 0.60 s | all constrained nodes combined, then 3 kept |
| envelope fold | 0.42 s | |

Not done: the authority checks. "Same checks, cheaper" is not possible without
editing the comparator in the pinned `boundary.py`, and "fewer checks" is the
authority-model change declined in M30. The envelope fold is now small.

## Changes

| Item | Change | File |
|---|---|---|
| ANYfem wet loop | prepared contexts cache, per wet set, the sorted element ids, centroid array and per-element geometry (built from the same calls the uncached path makes) and fill a fluid-side cache on each element's first non-zero pressure (M31b: only where computing a side cannot warn or raise, and cleared when what computes it changes); arithmetic and accumulation order unchanged; bytes reserved like the M30 wet cache; cleared with it; the non-prepared path is unchanged. (M31 shared the cached read-only arrays with the returned records; M31b returns fresh writable arrays again and gives the solver path a pressures-only accumulation) | `fem/src/anyfem/solve/prepared_static.py`, `fem/src/anyfem/solve/build.py` |
| Operator info copy | `_plain_deepcopy`: the same result as `copy.deepcopy` for plain records (memo and aliasing as deepcopy, a tuple of unchanged items returned itself, atomic values returned), with C-speed copies of flat lists of atomic values; anything else is handed to `copy.deepcopy` with the same memo | `prepared_static.py` |
| Packet storage estimate | closed form for an int-keyed dict of floats (each entry 128 + 64 + 64, as the walk computes); every other shape takes the walk | `prepared_static_loads.py` |
| Lean selected reactions | only kept nodes are combined; the same values in the same first-appearance order. **Reverted in M31b** (review finding 6) | `prepared_static_vectorized.py` |

## Verification

- `tests/test_prepared_static_response_m31.py` (15): `_plain_deepcopy` against
  `copy.deepcopy` (types, atomic identity, fresh containers, aliasing pattern;
  nested, shared, tuple, NumPy, OrderedDict, NaN/-0.0 samples and the real
  operator info of a grid and a free model); storage estimate against the pre-M31
  walk (plain, tuple, NumPy-scalar and empty pressure maps); lean reactions
  against the pre-M31 function (weighted MPC and free models, all and some nodes).
- ANYfem `tests/test_prepared_static_wet_cache.py` (+2): the prepared wet
  pressures equal the uncached path for four drafts and two wet loads per case,
  twice (pressure bits, element order, geometry); geometry built once; the
  fluid-side cache holds only loaded elements; a dry case evaluates no fluid side;
  accounting and clearing.
- Suites: regression set 187 passed, 1 skipped (`m31-claude-01`); base suites 112
  of 115, the three known failures (`m31-claude-02`); ANYfem prepared-static plus
  the wet-pressure suite 97 of 97 (`m31-claude-03-fem`).
- Barge 10,000 cases serial (`m31-barge-10k-serial`): per-case records identical
  to M28 (all 10,000), envelope byte-identical; 296.7 s in total (preparation
  82.1 s, 20.3 ms per case); the run shows signs of a slower machine (unchanged
  phases slower than in M30), see the paired comparison.

## Paired comparison (epoch m31, M31 before the review)

The same 2,000 barge cases (the cycled list's first 2,000), block 32, ABBA order
on a quiet machine (system CPU 7-10%), pre-M31 source (`m31-prefix`) against M31
(`m31-ab-pre-1/2`, `m31-ab-new-1/2`):

| ms per case | pre-M31 | M31 |
|---|---:|---:|
| total (`next(block)`) | 21.95 / 22.44 | 17.05 / 16.41 |
| outside the solver phases (ANYfem wet loop) | 8.41 / 8.55 | 4.65 / 4.54 |
| recovery (lean reactions) | 8.32 / 8.62 | 7.69 / 7.35 |
| certification (operator-info copy) | 1.33 / 1.37 | 0.85 / 0.76 |
| solve, load evaluation | 3.67 / 3.68 | 3.65 / 3.54 |

About 5.5 ms per case less (25%); histories and envelope byte-identical between
pre-M31 and M31. Projection for 10,000 barge cases serial: about 82 s preparation
+ 167 s + 5 s, about 255 s (M28 465 s, M30 about 311 s).

## Linux

WSL Ubuntu 24.04, Python 3.12.3, numpy 2.4.3, scipy 1.16.3 (`../../evidence/linux-m31`):
regression set 187 passed, 1 skipped; base suites 112 of 115 (the three known
failures); ANYfem 91 of 97. The six ANYfem failures are all in
`tests/test_wet_pressure.py`, run on Linux for the first time here, and come from
the Linux test environment, not from the code: five need the optional `shapely`
package for two-plate geometry (`planar_backend_unavailable`) and one needs
`platformdirs`; the Windows environment has both and the file passes there. The
M31 prepared wet-pressure tests pass on Linux.


## Review (Codex round 1) and fixes (M31b)

Independent static review of M30+M31 by Codex (gpt-6-astra, reasoning high,
read-only, bundle `../../evidence/m31-review/review-bundle-1.txt`): **NOT OK**, one
BLOCKER, seven SHOULD-FIX, one NIT (`codex-review-1.md`). Disposition:

| # | Finding | Fix (M31b) |
|---|---|---|
| 1 | BLOCKER: the empty-matrix backward-error test raises before comparing (`np.linalg.norm` of an empty vector) | Not so on numpy 2.4.3, where `norm(ord=inf)` uses `initial=0` and returns 0.0 (`empty-norm-2.txt`); older numpy 2.x raises the same `ValueError` in both functions. The test now compares outcomes (value, or exception type and message, and the warnings) under six NumPy error states |
| 2 | cached fluid sides ignore what produced them (surface, fluid-side function) | the wet caches are keyed by (surface id, object identity) and hold the surfaces; every use compares all surface fields (interior point as bytes) with the state the entries were built from and drops all kept entries on a difference. The fluid-side cache is cleared when anything that computes a side changes: the bindings `build.fluid_sign` and `wetfield._fluid_sign`, their code and defaults, and the module bindings their code names (compared by identity). A side is reused only where computing it cannot warn or raise: NumPy's default error state, and finite centroids, normals and interior points below 1e150 in size (the difference and dot product of the rule cannot overflow; underflow is not reported in that state); otherwise it is computed per case as on the uncached path |
| 3 | the trusted backward error is recognised through a mutable module binding | the original is the function captured at import (`_ASSEMBLY_BACKWARD_ERROR`); any other function, including a rebound `assembly._backward_error`, is called as is |
| 4 | a norm cached at preparation and a matrix changed in place | the norm data is computed per block after its solve (response path: at the block's first certification and again after any canonical solve inside the block); only the evaluator's own code runs between that and the certifications; the operators are read-only CSR (`_immutable_csr`) |
| 5 | prepared wet records share cached read-only arrays | `wet_element_pressures` returns fresh writable arrays on every path again; the solver path uses the same accumulation core and reads only the pressures |
| 6 | lean reactions skip additions that can raise under `np.errstate` | reverted to the pre-M31 function |
| 7 | the chunk order changes which floating-point condition comes first | chunked order only under NumPy's default error state, silenced; every condition that state reports leaves a non-finite value, and then the pre-M30 column order is evaluated again, so warnings and exceptions are those of the pre-M30 code; any other error state takes the column order directly |
| 8 | memo value `None` treated as missing in `_plain_deepcopy` | a distinct sentinel |
| 9 | M30 report count | corrected (172 passed, 1 skipped, `m30-claude-01d`) |

Also: the norm data takes the maximum only of finite row sums, as the original
does; the evaluation keeps one finiteness pass over the vector-map values (a
second pass in the first M31b draft cost about 1 ms per case).

Tests (M31b): `test_prepared_static_response_m30.py` now 93 (outcomes under six
error states for eight matrices including overflowing, NaN, subnormal and empty
ones; injected and rebound implementations; vector maps under non-default error
states and with overflowing, NaN and inf inputs, against the pre-M30 function
including its finiteness check; a running evaluator in which every certification
equals `assembly._backward_error` at call time and the norm is computed once per
block, and again after a forced canonical solve); `..._m31.py` now 13 (memo
`None`, explicit and planted by an item's `__deepcopy__`; the lean-reaction test
removed with the change); ANYfem `test_prepared_static_wet_cache.py`
now 13 (surface identity and content keys, a moved interior point and a changed
fluid side, both fluid-side bindings rebound, changed code of the fluid-side
function, reuse only under the default error state and bounded coordinates, fresh
writable arrays not sharing memory with the cache, solver loads equal to the
uncached path, a reduced reserve). Mutation check
(`../../evidence/m31-review/mutation-check-2.txt`): twelve of thirteen mutants
re-introducing a reviewed defect fail a test; the thirteenth (the unconditional
maximum) cannot be observed with numpy 2.4.3.

Suites (Windows): regression set 255 passed, 1 skipped (`m31b-claude-01c`); base
suites 112 of 115 (`m31b-claude-02c`), the three known failures, which also fail
with the pre-M30 and pre-M16 sources (`m31b-known-failures-m30-prefix`,
`m31b-known-failures-m16-baseline`); ANYfem 106 of 106 (`m31b-claude-03d-fem`,
after the fluid-side reuse conditions).

Barge, the same 2,000 cases (`m31b-barge-3/4`; not an ABBA pair): histories and
envelope byte-identical to pre-M31 (`m31-ab-pre-1`); also after the fluid-side
reuse conditions (`m31b-barge-5`, 18.2 ms per case, phases within the noise of
3/4; `../../evidence/m31-review/barge-identity-2.txt`).

| ms per case | pre-M31 | M31 | M31b |
|---|---:|---:|---:|
| total | 21.95 / 22.44 | 17.05 / 16.41 | 17.87 / 17.60 |
| recovery | 8.32 / 8.62 | 7.69 / 7.35 | 8.73 / 8.66 |
| outside the solver phases | 8.41 / 8.55 | 4.65 / 4.54 | 4.18 / 4.14 |
| certification | 1.33 / 1.37 | 0.85 / 0.76 | 0.89 / 0.87 |

The lean reactions are given back (recovery as before M31); the pressures-only
accumulation makes the ANYfem part a little faster than M31. Projection for
10,000 barge cases serial: about 82 s + 177 s + 5 s, about 264 s (M28 465 s, M30
about 311 s).

Linux, final M30+M31+M31b sources (WSL Ubuntu 24.04, Python 3.12.3, numpy
2.4.3, scipy 1.16.3; `../../evidence/linux-m31b-final`, summary in
`../../evidence/m31-review/linux-m31b-summary.txt`): regression set 255 passed, 1
skipped; base suites 112 of 115 (the same three known failures); ANYfem 100 of
106, the six `test_wet_pressure.py` environment failures described above (five
`planar_backend_unavailable` without `shapely`, one missing `platformdirs`); all
M31b tests pass.

## Review round 2 (Codex) and fixes (M31c)

Codex round 2 (bundle `../../evidence/m31-review/review-bundle-2.txt`, review
`codex-review-2.md`): **NOT OK**, six SHOULD-FIX, no BLOCKER. Round-1 findings 1,
3, 5, 6, 8 and 9 resolved; 2, 4 and 7 partially. Disposition:

| # | Finding | Fix (M31c) |
|---|---|---|
| 1 | the surface and producer checks ran before the pressure source, which can run caller code, so a side could be reused after a change inside the same request | the reuse decision and the surface-state check are made after the pressure source and the geometry-token check; from there to the end of the sign loop only this module's code and, when sides are reused, the original fluid-side functions run |
| 2 | identity of the producers does not make a replaced function safe to skip (closure state, a warning per call, a replaced `numpy.dot`) | sides are reused only while the whole chain is the original captured at import: both bindings, their code, defaults and closures, the module or builtin binding of every name their code uses and, for a module, its attributes of those names (`numpy.asarray`, `numpy.dot`); and only for plain `WetSurface` records with a `str` name and fluid side and a float64 interior point. A replaced function is called every time, with fresh writable arrays, as on the uncached path |
| 3 | NumPy's default error state does not imply round to nearest (directed rounding can overflow to a finite value) | the chunked vector-map order and the reuse of sides also require a run-time check of round to nearest without flush-to-zero or denormals-are-zero in the calling thread |
| 4 | retained selections and fingerprints not charged to the reserve | each kept entry is charged with the kept selection tuple and its content fingerprint, the geometry record also with its own record and fluid-side state; a test checks the exact charge of each entry |
| 5 | the test comparator ignored warnings on success | warnings compared on both branches; a regression test of the comparator |
| 6 | evidence missing from the bundle; "nine matrices" | the final Windows records (with source digests matched against the reviewed files) and the baseline runs of the three known failures are in E; eight matrices |

Round-1 finding 4 (partially resolved): the norm data is now used only for a CSR
matrix whose data, indices and index pointers are immutable bytes-backed buffers
(`_immutable_csr`, as the evaluator holds its operators) and are the very objects
it was computed from; anything else takes the original function. (M31d: the
"no longer matters" of this paragraph was too strong; see round 3.)

Lifecycle wording: the M30 rule "a failed case clears everything" covers failures
while a request is resolved. Other failures (cancellation, the request iterator,
later stages) leave the kept entries in place, which is safe because every use
rechecks what they depend on.

Tests (M31c): `test_prepared_static_response_m30.py` 95 (comparator, immutable
buffers and replaced parts, floating-point environment, the evaluator's operators
qualify for the shortcut); ANYfem `test_prepared_static_wet_cache.py` 16 (changes
made by the pressure source within a request, unusual surface records, exact
charges; reuse is now observed by poisoning the kept sides, since wrapping the
function disables reuse). Mutation check
(`../../evidence/m31-review/mutation-check-3.txt`): 19 of 20 mutants fail a test,
the remaining one is the unobservable maximum above.

Suites (Windows, final source): regression set 257 passed, 1 skipped
(`m31c-claude-01`); base suites 112 of 115, the three known failures
(`m31c-claude-02`); ANYfem 109 of 109 (`m31c-claude-03-fem`). Barge 2,000 cases
(`m31c-barge-1`): histories and envelope byte-identical to pre-M31, 17.2 ms per
case (recovery 8.3, outside the solver phases 4.2, certification 0.85).

Linux, final source (WSL Ubuntu 24.04, Python 3.12.3, numpy 2.4.3, scipy 1.16.3;
`../../evidence/linux-m31c`, summary `../../evidence/m31-review/linux-m31c-summary.txt`):
regression set 257 passed, 1 skipped; base suites 112 of 115 (the same three);
ANYfem 103 of 109, the six `test_wet_pressure.py` environment failures (five
`planar_backend_unavailable` without `shapely`, one missing `platformdirs`).

## Review round 3 (Codex) and fixes (M31d)

Codex round 3 (bundle `../../evidence/m31-review/review-bundle-3.txt`, review
`codex-review-3.md`): **NOT OK**, six SHOULD-FIX, no BLOCKER; round-2 findings 1,
3, 5 and 6 resolved, 2 and 4 partially. Disposition:

| # | Finding | Fix (M31d) |
|---|---|---|
| 1 | immutable bytes and unchanged array objects do not fix how the bytes are read (`data.dtype = int64` in place) | each part is compared by object, buffer owner, data address, dtype, shape and strides at every certification |
| 2 | the chunked vector maps change the call sequence of a replaced `np.matmul` | the chunked order also requires the NumPy functions both orders call (and its guard uses) to be the ones loaded at import; otherwise the column order calls them exactly as before |
| 3 | fingerprinting an unusual record (a `str` subclass whose `__str__` raises) runs code the original path does not | the fingerprint accepts exact plain types only and returns nothing for any other record; a selection with such a record is neither cached nor reused (the original path runs, with no new calls) |
| 4 | a closure-backed wrapper installed before import becomes the trusted chain | the chain is captured only if each function is the one its module defines, has no closure, was compiled from that module's file, and the module attributes its code names belong to that module's package; otherwise sides are never reused. The trust root is stated below |
| 5 | the cached row sums do not record the floating-point environment | the norm shortcut requires the standard environment (and the library bindings as loaded) when the norm is computed and at every certification |
| 6 | a state changed by the pressure source could be retained uncharged (a large interior point) | the post-source state must equal the state the entry was built and charged for, else nothing is reused or stored; the interior point must be a float64 array of shape (3,) |

Supported contract (trust root; narrowed by the owner in M31e, see below). The shortcuts trust the code as loaded: the
library bindings they and the original code name (NumPy functions, the SciPy CSR
methods of the row sums, the fluid-side functions of ANYfem and ANYloads) are
captured when the modules are imported, as the solver's response authority
captures its own functions (`_RESPONSE_FUNCTIONS`). Replacing a captured binding
later turns the affected shortcut off and the original path runs, calling the
replacement as the original code does. Outside the contract, as for the existing
authority model: forging library functions before these modules are imported (the
capture checks module, source file and closure, not provenance beyond that),
replacing library internals the code does not name, rebinding the private
trust-root names of these modules, writing memory through ctypes, and changing the
floating-point environment of library worker threads. The owned project and mesh
are the evaluator's private copies (M20); owned geometry changes are also caught
by the geometry token.

Floating-point probes against real mode changes
(`../../evidence/m31-review/fp_probe_check.py`, results `fp-probe-windows.txt`
and `fp-probe-linux.txt`): both probes are true under round to nearest and false
under round down, round up, round toward zero, flush-to-zero and
denormals-are-zero (Windows `_controlfp_s`; Linux `fesetround`, rounding only),
and true again after restoring.

Tests (M31d): solver M30 file 102 (reinterpreted and reshaped parts, another
floating-point environment between norm and certification, four replaced NumPy
functions, a replaced `np.matmul` that warns per call); ANYfem wet-cache 21
(unusual records run no new code and are not cached, a record changed by the
pressure source is neither reused nor retained, replaced guard functions, a chain
installed before import is not trusted; the stand-in surfaces of the M30 tests are
now real `WetSurface` records). Mutation check
(`../../evidence/m31-review/mutation-check-4.txt`): 27 of 28 mutants fail a test,
the remaining one is the unobservable maximum.

Suites (Windows, final source): regression set 264 passed, 1 skipped
(`m31d-claude-01`); base suites 112 of 115, the three known failures
(`m31d-claude-02`); ANYfem 114 of 114 (`m31d-claude-03-fem`). Barge 2,000 cases
(`m31d-barge-1`): histories and envelope byte-identical to pre-M31, 18.0 ms per
case (single runs of the same source vary between about 17.2 and 18.2 ms).

Linux, final source (`../../evidence/linux-m31d`, summary
`../../evidence/m31-review/linux-m31d-summary.txt`): regression set 264 passed, 1
skipped; base suites 112 of 115 (the same three); ANYfem 108 of 114, the six
environment failures of `test_wet_pressure.py` (five `planar_backend_unavailable`
without `shapely`, one missing `platformdirs`).

## Review round 4 (Codex) and the owner's contract decision (M31e)

Codex round 4 (bundle `../../evidence/m31-review/review-bundle-4.txt`, review
`codex-review-4.md`): **NOT OK**, eight SHOULD-FIX, no BLOCKER. All six round-3
findings resolved; the import-time trust root judged reasonable and consistent
with the existing authority model; counts, digests, barge identity and Linux
results confirmed against the evidence.

All eight findings were of one kind, introduced by the wording of the round-4
prompt ("the same calls into replaceable bindings"): a function replaced after
import (monkeypatched) sees other calls than from the original code, because a
cache or vectorisation calls it a different number of times (`np.any`,
`copy.deepcopy`, `builder.wet_element_pressures`, the code of a captured SciPy
method, NumPy functions while the wet geometry is built), plus three smaller
items.

Owner decision (2026-10-10, "Proceed as recommended"): **replacing library or
module functions after import is outside the supported contract.** That covers
monkeypatching NumPy, SciPy, `copy` or ANY* module functions, or replacing their
code. Results are specified for the code as loaded. The binding checks added in
M31c/M31d stay as defence in depth: they turn a shortcut off when they see such a
replacement, but do not promise call-for-call equality with the original code.
Inside the contract, and covered by the guards and tests: any NumPy error state
and floating-point environment set by the caller, caller code at the supported
extension points (pressure sources and fields, the request iterator, an injected
`owner._backward_error`), changes to wet-surface records and to matrix parts.

Round-4 dispositions:

| # | Finding | Disposition |
|---|---|---|
| 1 | NumPy functions replaced while the wet geometry is built or reused | outside the contract (replacement after import) |
| 2 | the code of a captured SciPy method replaced | outside the contract |
| 3 | `np.any` replaced (vectorised compact maps) | outside the contract |
| 4 | `copy.deepcopy` replaced (plain deepcopy) | outside the contract |
| 5 | `builder.wet_element_pressures` replaced (pressures-only accumulation) | outside the contract |
| 6 | the certification shortcut calls `np.ndim`, which the original does not | fixed: the shortcut reads the solution's `ndim` only for an exact ndarray and otherwise takes the original |
| 7 | a replaced fluid-side callable is inspected (`__code__`) before it is rejected | fixed: the two bindings are compared by identity with those captured at import before anything of them is read |
| 8 | the pressure source got an owning centroid array where the original passes an (n, 3) view of a new array | fixed: the cached path passes the same kind of array (a view of a fresh copy; an empty set as `np.array([]).reshape(-1, 3)`), checked by a probe test |

Tests (M31e): solver M30 file 103 (no `np.ndim` call); ANYfem wet-cache 23 (a
replaced callable is not inspected; the pressure source sees the same array kind
on both paths). Mutation check (`../../evidence/m31-review/mutation-check-5.txt`):
30 of 31 mutants fail a test, the remaining one is the unobservable maximum.

Suites (Windows, final source): regression set 265 passed, 1 skipped
(`m31e-claude-01`); base suites 112 of 115, the three known failures
(`m31e-claude-02`); ANYfem 116 of 116 (`m31e-claude-03-fem`). Barge 2,000 cases
(`m31e-barge-1/2`, epoch m31e): histories and envelope byte-identical to pre-M31;
19.1 and 18.5 ms per case on a busier machine (system CPU 12-13 % against 9-10 %
before; the unchanged recovery phase rose likewise), so about 18 ms per case
stands.

Linux, final source (`../../evidence/linux-m31e`, summary
`../../evidence/m31-review/linux-m31e-summary.txt`): regression set 265 passed, 1
skipped; base suites 112 of 115 (the same three); ANYfem 110 of 116, the six
environment failures of `test_wet_pressure.py` (five `planar_backend_unavailable`
without `shapely`, one missing `platformdirs`).

## Review round 5 (Codex) and fixes (M31f)

Codex round 5 (bundle `../../evidence/m31-review/review-bundle-5.txt`, review
`codex-review-5.md`): **NOT OK**, three SHOULD-FIX and one NIT inside the contract.
All eight round-4 dispositions hold (the five replacement scenarios confirmed
outside the contract, the three fixes confirmed); the contract judged clearly
stated. Disposition:

| # | Finding | Fix (M31f) |
|---|---|---|
| 1 | an immutable matrix whose data were replaced by complex values: the norm preparation converts (and warns) once more than the original | the norm shortcut only for float64 data and int32/int64 indices and index pointers, whose conversion cannot warn; anything else takes the original |
| 2 | the floating-point probes round, so they trap when the caller has unmasked the hardware inexact trap | contract made precise: the floating-point environment of the contract is the rounding mode and the denormal handling; hardware floating-point exception traps stay masked (NumPy reports conditions through status flags and its error state, and the probes cannot detect a rounding mode without rounding) |
| 3 | a kept surface enlarged in place and then replaced stays referenced, beyond its charge | kept entries are revalidated at every request boundary (any kept surface whose state changed drops all kept entries); the fingerprint now also refuses records it cannot bound: an interior point that is a view of another buffer, attributes beyond the record fields |
| 4 | NIT: comment "a failed case clears everything" | now "a request-resolution failure clears everything" |

Floating-point probe check extended (`fp_probe_check.py`, results
`fp-probe-windows.txt`, `fp-probe-linux.txt`): API return codes and the control word
read back for every mode (FTZ-only and DAZ-only labelled by their `float.h`
constants), and in every mode the changed paths compared with their originals in
full: backward error (four matrices, the block path against `assembly._backward_error`),
vector maps (two inputs, one overflowing, against the pre-M30 order) and the ANYfem
wet pressures (four cases, the cached path against the pre-M31 prepared path).
Windows: all seven modes detected by both probes, changed = original in all 10 checks
in every mode.

Tests (M31f): solver M30 file 104 (conversion that could warn); ANYfem wet-cache 26
(a changed and replaced surface is not kept past the request boundary, checked with a
weak reference; view-backed interior point and extra attribute not kept). Mutation
check (`../../evidence/m31-review/mutation-check-6.txt`): 34 of 35 mutants fail a
test, the remaining one is the unobservable maximum.

Suites (Windows, final source): regression set 266 passed, 1 skipped
(`m31f-claude-01`); base suites 112 of 115, the three known failures
(`m31f-claude-02`); ANYfem 119 of 119 (`m31f-claude-03-fem`). Barge 2,000 cases
(`m31f-barge-1`): histories and envelope byte-identical to pre-M31; its timing (25.0
ms per case) is not usable, the machine was under other load (all phases slower
alike, including unchanged ones). The costs M31f adds were measured directly
(`../../evidence/m31-review/m31f-overhead.txt`): about 1-2 microseconds per request
or per block. (Corrected in M31g: these were complete helpers measured once, not a
before/after difference, and they run more than once per request; see round 6.)

Linux, final source (`../../evidence/linux-m31f`, summary
`../../evidence/m31-review/linux-m31f-summary.txt`): regression set 266 passed, 1
skipped; base suites 112 of 115 (the same three); ANYfem 113 of 119, the six
environment failures of `test_wet_pressure.py`. The probe check on Linux: all four
rounding modes detected by both probes (return codes 0, `fegetround` read back),
changed = original in all 10 checks in every mode.

## Review round 6 (Codex) and fixes (M31g)

Codex round 6 (bundle `../../evidence/m31-review/review-bundle-6.txt`, review
`codex-review-6.md`): **NOT OK**, four SHOULD-FIX and one NIT inside the contract.
Round-5 findings 1, 2 and 4 resolved, 3 partially. Disposition:

| # | Finding | Fix (M31g) |
|---|---|---|
| 1 | a pressure record whose field returns an ndarray subclass that runs code (and changes a surface) while it is iterated, after the reuse decision | sides are reused only when the magnitudes are a plain float64 ndarray, whose iteration runs no code; otherwise the loop computes every side as the original does. The ANYloads sources (value, expression, code, table) return such arrays (`np.asarray(..., dtype=float)`), so only a custom pressure record reaches the other branch |
| 2 | the request iterator ending, failing or being closed skipped the boundary revalidation | the end of the request iteration (normal end, failure, close of the source) is a request boundary: the kept entries are revalidated there too |
| 3 | a record dictionary enlarged and emptied again keeps its larger allocation under an unchanged field fingerprint | the fingerprint includes the sizes of the record dictionaries (surface, reference, region) |
| 4 | the boundary scan could raise on a damaged discarded record (an attribute deleted) | records are read only through their instance dictionaries after checking exact types and exactly the field names under plain `str` keys; nothing of a record runs and nothing raises; such a record is not kept |
| 5 | NIT: the M31f overhead figures were complete helpers measured once, and the helpers run more often than stated | replaced by `m31g-overhead.txt`: each helper's cost with how often it runs; an upper bound for what the review fixes add, under 0.1 ms per case for the barge's few wet loads (largest: the sign-reuse guard, about 14 microseconds per wet load and request) |

Contract, made precise: of the evaluator's owned copies (M20), only the wet-surface
records may change (in place, or replaced in the owned project's list); the owned
regions, mesh tables and project settings are fixed after preparation (the owned
geometry is also checked by its token).

Tests (M31g): ANYfem wet-cache 31 (a custom pressure record turning a surface while
its magnitudes are iterated; the actual request iterator ending and failing after
changing and replacing a kept surface, checked with a weak reference; an enlarged and
emptied record dictionary; a damaged discarded record). Mutation check
(`../../evidence/m31-review/mutation-check-7.txt`): 38 of 39 mutants fail a test, the
remaining one is the unobservable maximum. Probe check rerun on the final source:
Windows all seven modes, changed = original in all 10 checks in every mode.

Suites (Windows, final source): regression set 266 passed, 1 skipped
(`m31g-claude-01`); base suites 112 of 115, the three known failures
(`m31g-claude-02`); ANYfem 124 of 124 (`m31g-claude-03-fem`). Barge 2,000 cases
(`m31g-barge-1`, system CPU 10.5 %): histories and envelope byte-identical to
pre-M31, 18.25 ms per case (recovery 9.0, outside the solver phases 4.25,
certification 0.91).

Linux, final source (`../../evidence/linux-m31g`, summary
`../../evidence/m31-review/linux-m31g-summary.txt`): regression set 266 passed, 1
skipped; base suites 112 of 115 (the same three); ANYfem 118 of 124, the six
environment failures of `test_wet_pressure.py`. Probe check on Linux: all four
rounding modes detected, changed = original in all 10 checks in every mode.

## Review round 7 (Codex): one fix, one open decision

Codex round 7 (bundle `../../evidence/m31-review/review-bundle-7.txt`, review
`codex-review-7.md`): **NOT OK**, two SHOULD-FIX and one NIT. All round-6 findings
resolved (the overhead note partially).

- Finding 2 (fixed, M31h): an interior point whose dtype is a float64 dtype carrying
  metadata compares equal to float64 but can hold any payload; the fingerprint now
  accepts only NumPy's own float64 dtype object (identity). Test: such a record is
  not kept past the request boundary (ANYfem wet-cache tests 32, all passing).
- Finding 3 (NIT, fixed): call counts in `m31g-overhead.txt` corrected (a selected
  surface is fingerprinted three times per wet load; the response path prepares the
  norm again after each canonical solve inside a block) and the workload assumption
  of the estimate stated.
- Finding 1 (open, owner decision): a custom pressure field that changes a
  surface's face reference *during* a request, between two wet loads with the same
  selection. The pre-M30 prepared path memoised the wet-element set per request,
  keyed by surface ids, but only when the entry fitted its cache reserve; so its
  result under such a change depends on the memory reserve (memoised: both loads on
  the old face; not memoised: the second load on the new face). The current code
  always re-resolves after a change (the result of the uncached path). Matching the
  pre-M30 path exactly would mean reproducing its per-request reserve accounting.

Owner decision (2026-10-10, "Proceed as recommended"): **wet-surface records may
change between requests; changing them while a request is resolved (from a pressure
source or a custom pressure record) is outside the supported contract.** Between
requests includes changes made by the request iterator, progress callbacks or other
caller code that runs between resolutions. The checks made after a pressure source
(M31c, M31g) stay as defence in depth; their tests compare with the uncached path.
Finding 1 is thereby outside the contract; no code change. The contract statement in
the code: `_PreparedLoadContext._wet_key` and the reuse decision in `build.py`.

Verification after M31h (final source): ANYfem wet-cache tests 32; mutation check
(`../../evidence/m31-review/mutation-check-8.txt`) 39 of 40 mutants fail a test, the
remaining one is the unobservable maximum. Windows: regression set 266 passed, 1
skipped (`m31h-claude-01`); base suites 112 of 115, the three known failures
(`m31h-claude-02`); ANYfem 125 of 125 (`m31h-claude-03-fem`). Probe check on Windows:
all seven modes detected, changed = original in all 10 checks in every mode. Barge
2,000 cases (`m31h-barge-1`, epoch m31h, system CPU 10.0 %): histories and envelope
byte-identical to pre-M31, 18.24 ms per case (pre-M31 about 22.2, M28 38).
Linux (`../../evidence/linux-m31h`, summary `../../evidence/m31-review/linux-m31h-summary.txt`):
regression set 266 passed, 1 skipped; base suites 112 of 115 (the same three); ANYfem
119 of 125, the six environment failures of `test_wet_pressure.py`; probe check: all
four rounding modes detected, changed = original in all 10 checks in every mode.

## Review round 8 (Codex) and fixes (M31i)

Codex round 8 (bundle `../../evidence/m31-review/review-bundle-8.txt`, review
`codex-review-8.md`): **NOT OK**, one SHOULD-FIX; all round-7 dispositions hold
(the mid-request case confirmed outside the contract).

| # | Finding | Fix (M31i) |
|---|---|---|
| 1 | a geometry-only entry (admitted when the wet-element entry did not fit) keeps the selected surfaces alive without charging their storage (a surface dictionary enlarged before admission) | the kept selection's surface records are charged with every entry of the wet set (`_kept_bytes`), whichever entry is admitted |
| NEEDS | non-canonical immutable matrix parts: the eager row sums would rewrite them (`sum_duplicates` on read-only buffers raises) even for non-finite data, where the original returns early | checked and confirmed (original `inf`, block path raised); the norm shortcut now requires canonical format and consistent index pointers, computed afresh with SciPy's own `csr_has_canonical_format` (its cached flag can be stale after a part is replaced); about 0.5 ms per check at 1.8 million non-zeros, once per norm preparation |

Tests (M31i): solver M30 file 107 (non-canonical parts with finite and non-finite
data, a stale canonical flag); ANYfem wet-cache 35 (geometry-only admission of an
oversized surface, released after replacement, weak reference; a request source whose
`close()` changes and replaces a kept surface, with and without a failing cleanup).

## Review round 9 (Claude; owner: no further Codex reviews)

The owner stopped the Codex reviews after round 8 ("If more is needed, have a round
yourself"). My round: the complete product diff against the pre-M30 snapshot
(7 files), each changed path read against the code it replaces, inside the contract.

- `prepared_static.py`: `_certified_backward_error` follows `assembly._backward_error`
  step for step (conversion, the three finiteness checks, residual, the row-sum
  check, the 1-D norms, the denominator rules); only the row sums come from the block's
  norm data, admitted for a canonical, immutable, float64 CSR matrix with unchanged
  parts, the library bindings as loaded and the standard floating-point environment
  (then and at each certification). The admitted conversion and row sums cannot raise
  or warn, so preparing the norm before the first certification changes nothing
  observable. `_plain_deepcopy` follows `copy.deepcopy` for the exact plain types.
- `prepared_static_vectorized.py`: per element and column the same batched kernel on
  slices with the same strides; under the admitted state every reported condition
  leaves an infinity or NaN (an infinity cannot become finite in a dot product; FMA
  only avoids overflows that would not surface), and then the pre-M30 order reruns.
- `prepared_static_recovery.py` (`_planned_compact`): its input is always a 2-D
  (n, 6) float array built just before; same rows, same order.
- `prepared_static_loads.py`: the closed-form storage size equals the walk's
  128 + 64 + 64 per int-to-float entry; the shared run-time checks.
- `prepared_static_response.py`: the lazy per-block norm, reset after a canonical solve.
- ANYfem `build.py`: the cached path has the same arithmetic and accumulation order as
  the pre-M31 prepared path, the same first error for the same element (a cached side
  came from a successful call with the same inputs), the same kind of arrays for the
  pressure source and fresh writable arrays in returned records; the uncached path's
  records still alias the mesh-cache arrays as before; the solver path adds the same
  floats in the same order.
- ANYfem `prepared_static.py`: keys, fingerprints, revalidation at every request
  boundary (including the end, failure and close of the request iterator), charges and
  drop paths.

Found and fixed: two stale docstrings (`wet_geometry` still described the old tuple
and named the renamed `_signs_cacheable`).

Found and documented (same principle as the owner's round-7 decision): ANYfem accepts
wet surfaces with the same id (`add_wet_surface` does not reject them, and
`dataclasses.replace` keeps the id). With two such surfaces of different content, the
pre-M30 per-request cache, keyed by surface ids only, could serve one selection the
entry of another; whether it did depended on its cache reserve. The current code keys
by surface identity and resolves each selection as the uncached path does. Like the
mid-request case, there is no reserve-independent original behaviour to match.

Known limits, unchanged: the mutation that takes the maximum of non-finite row sums
cannot be observed with NumPy 2.4.3; the declared NumPy 2.0 / SciPy 1.13 floor and
macOS are not tested; the M30 10,000-case evidence is the earlier run.

### Final verification (source after round 9)

- Mutation check (`../../evidence/m31-review/mutation-check-9.txt`): 41 of 42 mutants
  that re-introduce a reviewed defect fail a test; the remaining one is the
  unobservable maximum.
- Windows: regression set 269 passed, 1 skipped (`m31i-claude-01`); base suites 112
  of 115, the three known failures that also fail on the pre-M30 and pre-M16 sources
  (`m31i-claude-02`); ANYfem 128 of 128 (`m31i-claude-03-fem`).
- Linux (`../../evidence/linux-m31i`): 269 passed, 1 skipped; 112 of 115 (the same
  three); ANYfem 122 of 128, the six environment failures of `test_wet_pressure.py`.
- Floating-point probe check: Windows all seven modes and Linux all four rounding
  modes detected; the changed paths equal their originals in all 10 checks in every
  mode.
- Barge, 2,000 cases (`m31i-barge-1`, epoch m31h): histories and envelope
  byte-identical to pre-M31; 18.31 ms per case (pre-M31 about 22.2, M28 38).
  Projection for 10,000 cases serial: about 82 s preparation + 183 s, about 4.5 min
  (M28 465 s).

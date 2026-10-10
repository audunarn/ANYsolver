# M29 — per-case profile of the barge history

2026-10-10. Owner: Claude (Anthropic). Profile and lever measurements only;
nothing in `solver/src` or `fem/src` changed. Owner request: "Do a per case
profile first" (before case-parallel work). Epoch m29 (1,500 s, my allowance):
625.7 s used.

## Method

Product route as used by the barge screen: ANYfem response evaluator, certified
vectorized stress, lean selected reactions, default mode, `load_families`
nodal/element/pressure, block size 32 (product default), requests as
`PeriodicSample` (as the screen's response route).

1. Product phase timers from earlier streams (`m28-blocks-primary` b32, 300 cases;
   `m28-caseparallel-10k` serial, 10,000 cases; worker runs for contention).
2. `../../evidence/m29_case_profile.py` (run `m29-case-profile-2`): one prepared
   owner, 64 warm-up cases, a 640-case stream under the time-weighted stack
   sampler (attribution reliable for long-running ancestors, biased at leaves
   towards GIL-release points) and a 320-case stream under cProfile (function
   detail, inflated Python cost).
3. `../../evidence/m29_levers.py` (run `m29-levers`): unprofiled timings of the
   suspected items on the prepared barge, each with a bitwise-identity check of a
   proposed alternative (random inputs of the real sizes).

The first profile run (`m29-case-profile`, timed out) requested saved cases as
`StaticLoadRequest`, which takes the native load path: 173 of 210 s went into the
native pressure kernel (about 0.3 s per case, 8x the periodic-sample path). Worth
knowing for users of the ANYfem API: requesting saved cases by name is much slower
than requesting periodic samples.

## Where a case's time goes (10,000-case serial stream, 38 ms per case)

| Part (product phase timers) | ms/case | Share |
|---|---:|---:|
| recovery (vector maps, derived, envelope fold, lean reactions) | 16.6 | 44% |
| outside the solver phases (ANYfem load construction, authority checks, glue) | 11.1 | 29% |
| solve (combination and backward error) | 3.6 | 10% |
| certification (backward error) | 3.4 | 9% |
| load evaluation (compiled) | 2.2 | 6% |
| other | 0.2 | 1% |

Prepared data a block touches: vector maps 86.6 MB (the Q4 group is 3,185
elements x 132 outputs x 24 DOFs = 80.7 MB), case workspace 12.4 MB per case,
envelope state 21.4 MB, stiffness 1.23 M non-zeros (26,094 DOFs), snapshot 322 MB.

## Items and measured levers

Unprofiled, per case, barge (`../../evidence/m29-levers.json`). "Identical": the
alternative's results are bitwise equal to the current code's.

| Item | Now | Alternative | Saving | Identical |
|---|---:|---|---:|---|
| Lean reaction maps (`planned_constraint_force_diagnostics(maps_only=True)`) | 11.2 ms | build each compact map with one vectorised non-zero test instead of a Python test per node (`_planned_compact`); support map 0.55 -> 0.09 ms | about 8 ms (estimate: slave/master maps not timed separately) | yes (support map) |
| Vector maps (`evaluate_groups`) | 5.55 ms | cache-blocked: the same per-element product per column, over element chunks so each chunk of the 80 MB map is reused for all columns of the block | 1.8-2.4 ms (chunk 32-512) | yes |
| Backward error (`assembly._backward_error`) | 2.28 ms per call | prepared-route variant with the matrix infinity norm computed once (1.6 ms) instead of `abs(K).sum` per call | 1.7 ms per call; about 1-2 calls per case | yes |
| ANYfem request resolution | 6.6 ms | keep the wet-element cache across cases (fixed owned geometry, checked by the geometry token) instead of clearing it before and after every case | 2.0 ms | yes (load cases equal) |
| `_require_open` (response authority check) | 0.32 ms per call, about 3 per case | check once per block | about 0.6 ms | not applicable (same checks, fewer times) |
| Products with K | 0.71 ms (32 single products) | one product with the 32 columns | about 0.5 ms | yes |

Together about 15-18 ms of 38 ms per case. Not covered: the remaining ANYfem load
construction (about 4.6 ms: wet-pressure expression evaluation and fluid side per
element, per case), the envelope fold (about 2.2 ms), per-block authority and
scope entries.

Two corrections from cross-checking the tools: the sampler attributed 8 ms per
case to the sparse product inside the reaction maps; the product itself costs
0.36 ms (cProfile) and 0.7 ms (direct timing). The time is the Python work around
it, credited to the product because it releases the GIL. And the M28 report's
"memory-bandwidth bound" was too specific: all phases slow by the same factor
under contention (corrected there).

## Projection (estimate)

With the solver-side levers (reaction maps, vector maps, backward error, K
products, authority per block) and the ANYfem cache: about 20-23 ms per case
instead of 38 ms. 10,000 barge cases: about 82 s preparation + 200-230 s, about
5 minutes instead of 7.8 (1.5-1.6x serial). Less memory traffic per case may also
reduce the contention that limits case-parallel runs; not measured.

## Recommendation

Implement the bitwise-identical levers as one milestone, verified like M21-M26
(byte-identical barge outputs, probes, the existing suites):

1. Reaction maps: vectorised `_planned_compact` (largest, simplest).
2. Backward error: prepared-route variant with the cached matrix norm (no change
   to the shared `assembly._backward_error`).
3. Vector maps: cache-blocked `evaluate_groups` (chunk size about 512).
4. Products with K over the block's columns where a block-wide product exists.
5. Response authority check once per block instead of per `_require_open` call
   (authority review needed: same checks, fewer points in time).
6. ANYfem: keep the wet-element cache for the evaluator's lifetime (the M19 lever;
   an ANYfem change).

Then re-measure, including a case-parallel run, before deciding on the ANYfem
case-parallel feature.

# Sol Ultra promotion decision log

This is the release-candidate decision record for the Sol Ultra campaign on
`performance_2`. Decisions are scoped: `promote` means the qualified eligibility
envelope is enabled with its scalar/full-coordinate oracle retained; it does
not mean that adjacent formulations are implicitly accelerated.

The immutable comparison baseline is
`575ddd3fd7712378e6a24b901c647cf101d7b0dc`. The contemporaneous
`origin/main` revision and merge-base are the same commit. The clean qualified
source-candidate SHA must be copied from `sol_ultra_final.json`; it must also
equal the candidate commit recorded by
`sol_ultra_numerical_comparison.json`. The subsequent report-only closure
commit may be a descendant because committing generated reports necessarily
changes branch HEAD. That closure commit must not change production or test
sources relative to the qualified source candidate. A dirty or mismatched
capture does not close the release gate.

## Evidence status

The decisions below use scalar-oracle tests, focused workstream benchmarks,
thread-scaling evidence, and the last completed integrated regression run.
Focused timing is not substituted for the pending matched three-repeat final
report. The last completed integrated full suite before the final release
hardening patches was 736 passed in 371.61 seconds at
`4f35c450071cb1c435f4d4084778aeb4900baa34`. The final committed candidate
must repeat the full suite and independent 13-case numerical comparison.

Measured focused evidence collected during the campaign:

| Scope | Matched evidence | Interpretation |
| --- | ---: | --- |
| Persistent state transactions | 9.08x synthetic transaction throughput; 1.088x real shell batch; 1.056x solver lifecycle | Useful enabling infrastructure, but the standalone lifecycle result does not satisfy the combined state/Hill 2x target. Promotion is therefore limited to the qualified static/arc lifecycle. |
| Hill-48 | 72.7x at 20 points, 454.8x at 256 points, 621.6x at 4096 points; 4.33x static and 6.83x arc-length | Satisfies the constitutive/state target on the qualified canonical-curve path. |
| Orthotropic S4 | 11.571x linear and 127.745x nonlinear focused workloads | Strong qualified batch gain; final full-suite timing remains the regression cross-check. |
| Generalized `A/B/D/As` S4 | 48.421x linear and 50.653x nonlinear focused workloads | Strong qualified batch gain with resultants-only semantics preserved. |
| Corotational block rotations | 1.54x shell and 1.19x beam focused workloads | Promote the direct 3x3 block transform only; broader frame/local-response batching is not justified by this evidence. |
| Impact tangent reuse | 46--59% fewer tangent/factorization operations; 1.26x median end-to-end | Promote as conservative opt-in modified Newton with mandatory refresh triggers. |
| Direct reduced elastic impact | 3.113x assembly, 1.087x end-to-end, 98.97% of full-coordinate assemblies avoided | Promote for the explicitly qualified elastic, zero-affine-offset scope. |
| Compact impact contact records | about 1.05x end-to-end and 5x fewer public-record materializations | Promote as solve-local allocation reduction; public result semantics remain eager at API/save boundaries. |
| Incremental damage matrices | 48.44x steady update, 5.73x amortized; measured break-even at 11 future updates | Promote behind event-density and combined-memory gates only. |
| Repeated static `AnalysisSession` | 2.562x | Promote optional caller-owned reuse with revision/fingerprint invalidation and bounded caches. |
| Large recovery | 6.91x for 200 S4 elements; 17.4% output-heavy workflow improvement | Meets the recovery-phase gate. Selections below 100 elements keep the legacy path. |
| Mature isotropic path | paired measurements within 1% | No material regression was observed in the paired focused audit; the final full report is authoritative. |

The advanced shell scalar-oracle audit reported relative differences of about
`3e-12` or smaller. Final acceptance still uses each metric's gate from the
independent verifier; this aggregate figure must not be treated as a relaxed
matrix tolerance.

## Decision table

| Workstream | Numerical qualification | End-to-end gain | Memory result | Regression result | Decision |
| --- | --- | ---: | --- | --- | --- |
| Persistent state storage | Pass for qualified von Karman static/arc transactions, restart, rejection, cutback, initial-field, and materialization behavior | 1.056x solver lifecycle; enables 4.33x/6.83x Hill workflows | Solve-owned dual contiguous buffers; no mutable constitutive state in a global cache | Focused parity passed; final full suite pending | **promote** for static/arc; **defer** nonlinear-impact state transactions |
| Hill-48 batch | Pass against safeguarded scalar return map for canonical curves, mixed elastic/yielding rows, state, and tangent | 4.33x static; 6.83x arc-length | Immutable curve packs shared per call; bounded persistent point arrays | Isotropic J2 remains separate; final full suite pending | **promote** canonical-curve compiled path; retain scalar/pathological-row fallback |
| Orthotropic S4 | Focused scalar-oracle parity passed for material axes and qualified geometry | 11.571x linear; 127.745x nonlinear focused workloads | Revision-bounded model plan; bounded layer-plan LRU | Mature isotropic paired audit within 1% | **promote** qualified homogeneous orthotropic S4 |
| Generalized S4 | Focused force/tangent/mass/resultant parity passed, including nonzero `B` | 48.421x linear; 50.653x nonlinear focused workloads | Revision-bounded model plan; no invented ply-state storage | Mature isotropic paired audit within 1% | **promote** qualified pre-integrated `A/B/D/As` S4 |
| Rotated corotational | Rigid rotation, force/tangent, objectivity, and scalar rotated-path checks passed | 1.54x shell; 1.19x beam focused workloads | Geometry-reference cache is mesh/revision bounded | Dense consistent-tangent oracle retained | **promote** direct 3x3 block rotations; **defer** broader batched frame/local response and consistent-frame sensitivity replacement |
| Impact tangent reuse | Contact/damage/deletion/plastic/convergence refresh tests passed; zero budget is oracle | 1.26x median end-to-end; 46--59% fewer tangent/factorization operations | Tangent/factorization handle is solve-local | No additional cutback/convergence loss in focused qualification | **promote** conservative opt-in reuse |
| Impact reduced assembly | Elastic direct/full parity passed, including selector and weighted-MPC mappings | 1.087x end-to-end; 3.113x assembly | Existing reduced-map cap and cost gate apply | 98.97% of full assemblies avoided in eligible workload | **promote** elastic zero-affine-offset scope; **defer** plastic/fiber/damage/deletion/affine scope |
| Analysis session | Reuse/no-reuse parity and topology, geometry, material, constraint-structure, prescribed-value, foreign-plan, and close invalidation checks passed | 2.562x repeated static workflow | Bounded plan/factorization/output entries; explicit `close()`/`release()` | One-shot API remains the oracle; final full suite pending | **promote** optional session core; **defer** accepted arc-length tangent retention |
| Transient reduced data path | Algebraic parity passed for preprojected loads and selected rows | Focused data-movement qualification; matched final full-case gain still pending | Selected histories avoid unrequested full-vector retention | Reverse promotion if final matched case regresses by more than 5% | **promote** exact load preprojection/selected reconstruction, conditional on final regression gate |
| Recovery batches | Component, frame, surface, ordering, provenance, serial/threaded, and selection checks passed | 6.91x large recovery; 17.4% output-heavy workflow | 200-element thread audit retained 120,064 bytes; revision-bounded plan | Small selection overhead avoided by gate | **promote** large qualified S4 recovery; keep legacy path below 100 elements and for unsupported formulations |
| Compact contact work | Contact force, ordering, sticky selection, and public-record materialization checks passed | About 1.05x end-to-end | Solve-local arrays; thread-local public-helper buffer | Public result contract unchanged | **promote** |
| Incremental damage matrices | K/M, point-mass, scale reset, invalidation, and fallback checks passed | 5.73x amortized; 48.44x steady update | Gate accounts for plan plus simultaneously retained cached legacy terms and configured headroom | Exact cached-term rebuild remains fallback | **promote** only after 11 projected future updates and combined-memory approval |
| Automatic thread selection | Exact output parity and restoration passed, but scaling did not justify a new default | No repeatable gain; recovery worsened with additional Python workers | One thread avoids nested-pool amplification | All measured relative output errors were zero | **reject** automatic/default scaling; qualify and recommend explicit thread count 1 |
| Experimental CSR linear assembly | Numerical prototype remains benchmark-only | Promotion gate not demonstrated in final campaign evidence | Retained topology has additional memory cost | Qualified COO path retained | **reject** production promotion in this campaign |

## Qualification boundaries

- Persistent state transactions cover qualified von Karman static and
  arc-length shell lifecycles. Nonlinear impact keeps committed/trial
  dictionaries until its checkpoint, cutback, deletion, restart, and saved
  history boundaries are qualified together.
- Compiled Hill-48 accepts canonical ANYmaterial curve packs. Custom hardening
  protocols and invalid/pathological rows use the safeguarded scalar or
  numerical-tangent oracle.
- Orthotropic/generalized batching is limited to eligible S4 formulations.
  Triangles, Q8/Q8R, unsupported material/section laws, and exact initialized
  state overrides remain scalar. Generalized recovery reports resultants; it
  does not synthesize ply stresses.
- Corotational promotion removes dense block-diagonal rotation construction
  only from the ordinary rotated path. The consistent tangent retains its
  chain-rule/frame-sensitivity implementation.
- Direct reduced impact requires Numba, von Karman kinematics, a non-identity
  eligible transformation, exactly zero `u0`, no impact plastic/fiber history,
  and no damage/softening/deletion scope. Cost and retained-map memory gates
  must also pass.
- Damage plans retain cached legacy element terms for exact fallback. Memory
  eligibility is based on the peak combined footprint, not the plan alone.
- `AnalysisSession` is optional, belongs to one live model, rejects stale or
  cross-session plans, and must refresh prescribed-value-dependent `u0` and
  output plans without discarding compatible structural factors.
- Recovery selections below 100 elements deliberately use scalar recovery.
  Larger mixed selections may report a hybrid compiled/scalar backend.
- Q8R acceleration, persistent impact state, upper-triangle-only integration,
  broader corotational batching, retained arc predictor factorization, GPU
  acceleration, and implementation-language changes are outside the promoted
  scope.

Incoming ANYfem-facing functionality is not a performance workstream and is
not replaced by an optimization decision. Prescribed-action capacity,
reaction, affine-constraint, restart, and constraint-audit behavior must be
preserved by semantic merge and included in the final regression and numerical
captures.

## Thread and backend decision

The reproducible thread sweep at
`b3e04c29d3362994eb6fa33cb0a6c95fe530bb9f` measured these warm phase medians:

| Resource | Threads | Warm phase medians |
| --- | --- | --- |
| Nonlinear assembly | 1, 2, 4, 8, 16 | 0.504726s, 0.501583s, 0.498774s, 0.496788s, 0.511014s |
| PyPardiso solve | 1, 2, 4, 8 | 0.016607s, 0.017000s, 0.018343s, 0.017141s |
| Stress recovery | 1, 2, 4, 8 | 0.025861s, 0.050951s, 0.060194s, 0.123027s |

All reference comparisons reported zero relative error and thread scopes were
restored after normal and deliberate exceptional exits. The release decision
is therefore to use one thread for qualification and as the recommended
explicit policy, make no automatic choice from logical-core count, and retain
the existing API behavior when thread fields are omitted. The campaign also
does not lower the global SuperLU/PyPardiso selection thresholds; representative
evidence did not justify a policy change.

## Normalized phase coverage

The full benchmark schema contains every mandated phase, but a null phase is
unavailable, not zero. Baseline coverage was:

| Phase | Cases with a normalized timer |
| --- | ---: |
| Model preparation | 6/16 |
| Constraint-plan construction | 1/16 |
| Linear K assembly | 5/16 |
| Linear M assembly | 4/16 |
| KG assembly | 1/16 |
| Nonlinear local response | 5/16 |
| Reduced-coordinate scatter | 1/16 |
| `T.T @ F` projection | 1/16 |
| `T.T @ K @ T` projection | 1/16 |
| Factorization | 3/16 |
| Linear solve | 1/16 |
| Stress recovery | 2/16 |
| Total wall time | 16/16 |

No baseline full-suite case exposed a normalized timer for constitutive update,
state packing, state commit, state materialization, full-coordinate scatter,
contact search, contact-load construction, full-vector reconstruction, or
history/output storage. Some optimized paths expose related counters/timings
inside result diagnostics, but those values are not interchangeable with the
normalized phase fields. The final comparison must retain explicit `n/a`
entries and must not fabricate a phase speedup.

## Release closure gates

Before changing this document from release-candidate evidence to a closed
release record:

1. Commit the qualified source candidate and verify that the checkout is clean.
2. Run the complete test suite after all release-hardening changes.
3. While the source checkout is still clean, capture the independent 13-case
   candidate artifact. The capture must precede untracked/generated release
   outputs in that checkout so its dirty-state provenance remains false.
4. Capture the immutable baseline and run the numerical comparison.
5. Run both mandated nonlinear assembly commands with ten repeats, then
   generate `sol_ultra_final.json` with the full suite and three warm repeats.
6. Confirm that the numerical candidate SHA and the qualified source SHA in
   the final performance report are identical.
7. Generate `sol_ultra_comparison.md`; investigate any representative
   regression above 5% and revise the applicable decision rather than averaging
   it away.
8. Replace the pending SHA statement at the top with the exact qualified
   source-candidate SHA. If reports are committed afterward, verify that the
   report-only closure commit changes no production or test source.

## Reproduction commands

Run from the clean final `performance_2` checkout in PowerShell:

```powershell
$env:PYPARDISO_MKL_RT = 'C:\Python\Python313\Library\bin\mkl_rt.3.dll'
$python = 'C:\Github\ANYsolver\.venv\Scripts\python.exe'
$baselineRoot = 'C:\Github\ANYsolver\.perf2-worktrees\baseline'
$candidateRoot = (Resolve-Path -LiteralPath .).Path

& $python -m pytest tests -q --basetemp=.pytest_tmp_sol_ultra_final
$dirty = git status --porcelain
if ($dirty) { throw "Qualified source checkout is dirty before numerical capture: $dirty" }
& $python scripts/verify_sol_ultra_numerics.py capture --solver-root $candidateRoot --label candidate --suite full --output .sol_ultra_verify_candidate.json
& $python scripts/verify_sol_ultra_numerics.py capture --solver-root $baselineRoot --label baseline --suite full --output .sol_ultra_verify_baseline.json
& $python scripts/verify_sol_ultra_numerics.py compare --baseline .sol_ultra_verify_baseline.json --candidate .sol_ultra_verify_candidate.json --json-report reports/performance/sol_ultra_numerical_comparison.json --markdown-report reports/performance/sol_ultra_independent_verification.md

& $python scripts/benchmark_nonlinear_assembly.py --nx 20 --ny 10 --repeats 10
& $python scripts/benchmark_nonlinear_assembly.py --nx 20 --ny 10 --repeats 10 --weighted-mpc-rows 12
& $python scripts/benchmark_sol_ultra_performance.py --suite full --repeats 3 --label final --output reports/performance/sol_ultra_final.json --no-markdown
& $python scripts/benchmark_sol_ultra_thread_scaling.py --repeats 3 --output .sol_ultra_thread_scaling.json

& $python scripts/compare_sol_ultra_performance.py --baseline reports/performance/sol_ultra_baseline.json --final reports/performance/sol_ultra_final.json --numerical reports/performance/sol_ultra_numerical_comparison.json --thread-scaling .sol_ultra_thread_scaling.json --decision-log reports/performance/sol_ultra_decision_log.md --output reports/performance/sol_ultra_comparison.md
```

The thread-scaling JSON is a transient generator input to the comparison
report, not a ninth committed release deliverable. The required committed set
remains the eight `sol_ultra_*` artifacts listed in the execution plan.

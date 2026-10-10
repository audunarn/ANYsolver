# M8 source-response development screen

Status: experimental implementation retained; representative response-reconstruction
promotion **NO_GO**. No merge, publication or 10,000-case qualification.

The solver and ANYfem opt-in interfaces work, including the complete 60-phase
clipped-wave pressure library and its independent moment source. However, the
attempted stress-component response shortcut failed an existing numerical gate.
It was removed. Stress-bearing and envelope cases now use canonical direct solves
and staged recovery. Displacement/reaction-only pattern cases can reconstruct
reduced displacement and free-free multiplier responses, with actual equation
certification and actual full-load reaction diagnostics.

The measured improvements below come from bounded batching and amortized block
work, **not from bypassing stress recovery or canonical envelope replay**.

## Artifacts and scope

Worktrees: `C:/ANYworkspaceWork/prepared-static-20261008/solver` at `cff55d95`, and
the sibling `fem` worktree at `3e4eb7f`. These continue the existing M7 candidate;
they are distinct from solver main `da1ba2e9` and FEM main `f74812d` inspected at
M8 start. Main checkouts and their unrelated work were not edited by M8.

The comparator is the frozen M7 prepared implementation under `../m8-baseline/`,
not historical pre-guard or pre-batch timings. Exact commands, import paths,
environment, source hashes, timings, stdout/stderr and test XML are retained in
`../evidence/checks/m8*/`. `../evidence/M8_RESULTS.json` is the aggregate ledger.
All checks used `C:/Github/ANYsolver/.venv/Scripts/python.exe`.

Public additions:

- Solver: `PatternCase`, `PreparedStaticResponseEvaluator`,
  `prepare_static_response_evaluator`.
- ANYfem: `PatternLoadRequest`, `PeriodicLoadSource`, `PeriodicSample`,
  `PreparedStaticResponseEvaluator`, `prepare_linear_static_response_evaluator`.
- Mixed direct/pattern input, sparse named or dense coefficients, private factors,
  supported/free-free mechanics, full-state certification, bounded publication,
  cancellation/close, and existing direct load families remain connected.
- Periodic admission uses safe expression analysis, a declared original grid,
  complete clipped-pressure units and independent connection envelopes. Every
  periodic sample also supplies its original-time canonical load. No phase
  snapping or mathematical-periodicity-as-bit-identity assumption is used.

The source snapshot, full force columns and reduced response columns are owned.
The baseline includes prescribed offsets once. Individually unbalanced algebraic
columns are permitted; physical free-free combinations still require per-body
compatibility. Actual residual certification remains at `1e-10`. No new backend,
native dependency, approximation or hydrodynamic reconstruction was introduced.

## Consequential review findings and disposition

1. **Component superposition is not qualified.** In `m8-solver-05`, the original
   principal-stress same-displacement gate (`rtol=atol=1e-12`) failed for scaled
   response combinations. The mixed beam/shell cancellation diagnostic also
   failed while equation backward errors were about `1e-17`. Same-displacement
   beam shear discrepancies included `2.96e-10`. Uniform all-stress `1e-12/1e-12`
   remains a separate conservative diagnostic, not an invented universal beam
   acceptance criterion. The failed source is preserved verbatim and hash-checked
   at `.prepared-static-evidence/m8-failed-component-response.py.disabled`.
   **Repair:** remove component-column execution and storage; canonical direct
   solve plus staged recovery for all requested stress/envelope cases. No
   tolerances, zero clipping or governing-case rules changed.
2. **Backend layout matters.** The preliminary barge candidate used several RHS
   columns in a replay solve. Its sampled governing identities matched, but
   numerical values differed. Replay now uses one contiguous RHS per solve while
   retaining multi-case ingress/yield blocks. The corrected barge comparison is
   bit-identical, including histories, reactions, envelopes and associated fields.
   Preliminary evidence remains under `m8-barge-response`; corrected evidence is
   `m8-barge-response-final`.
3. **Callback authority:** an application reviewer found a cancellation callback
   inside a trusted preparation scope. Callbacks were moved outside those scopes,
   with authority checks after observation. Hostile-token regressions passed.
4. **Source identity:** sparse/shuffled sampling must preserve original sample
   numbers and full envelope windows. Exact decimal-grid membership replaces
   nearest-phase tolerance snapping. Harmonic-frequency tolerance is explicitly
   classified as admission evidence, not a proof of numerical recurrence.
5. **Resource accounting:** retained Python metadata, array backing buffers and
   pattern case labels are accounted. A large variable packet arriving after
   smaller packets may still be refused if both cannot coexist within the cap;
   `batch_size=1` is the documented workaround. This is a remaining capability
   limitation, not a claim that every individually fitting mixed packet streams.
6. **Executable admission:** reject evaluator subclasses and class, instance or
   global hook replacement before trusted load execution. The registered guard
   also authenticates exact native base evaluators independently of overridable
   `_require_open`. The final focused authority/native-parity check passed 11
   tests. These final authority-only edits were not benchmarked.

Root independently reviewed mechanics, full-load versus reduced-load provenance,
factor ownership, scope changes and the failed numerical evidence. The two
implementation owners cross-reviewed the other repository. Mistral remained
unavailable from the earlier recorded exhaustion; no different-family review is
claimed. No cheap certificate or contender-exclusion bound was enabled.

## Representative supported results

Fixture: `representative_barge2.fixture.json`, SHA256
`0f64d97108bb958f5b16eaee4a603d368b690b3846843208288edc067b911ce5`.
The same fixture hash is recorded by each run.

The model has 4,349 FE nodes and 5,349 elements. The envelope request covers all
physical Q4/beam von Mises locations and all-node reactions, with three selected
element histories and 18 selected displacement/rotation DOFs. Coupling mechanics
remain included. This is not every-output-component qualification.

Both routes used the same saved loads, output request, one effective solver/BLAS/
Numba thread, 1 GiB estimated resource policy and requested block size four.
The direct reference admits one variable packet per block under that policy;
the response candidate admits four accounted packets. Meshing is excluded.
Preparation, factorization, load construction, recovery, envelopes and consumed
output are included. All 61 source columns were prepared, plus the baseline RHS.

| Measurement | Direct M7 | Corrected M8 |
| --- | ---: | ---: |
| Preparation | 87.634 s | 114.691 s |
| First four cases, preparation included | 111.457 s | 128.520 s |
| First four-case history after preparation | 23.816 s | 13.822 s |
| Repeated warm four-case history | 23.959 s | 13.673 s |
| Distinct four-case holdout | 24.117 s | 14.961 s |
| Peak process working set | 1,164.793 MiB | 1,311.461 MiB |

Warm speed ratios are **1.75x** for the repeated history and **1.61x** on the
distinct holdout. Preparation-inclusive first-history execution is **15.3% slower**.
Memory is higher, not 50% lower. The retained force/response library is
21,977,345 estimated bytes. Both routes use one PARDISO factorization; no hidden
stale-handle rebuild was recorded. The response preparation performs one batched
backend solve of 62 RHS columns; its `preparation_solves=62` counter denotes RHS
columns, not 62 factorization or backend-call events.

All 12 observed response-envelope cases replayed canonically; ten also exhibited
a bitwise original-source/reconstructed-force discrepancy. These are expected
conservative fallbacks, not silently accepted periodic equivalence.

The corrected comparison checked 829,188 history binary64 values exactly across
the three histories. Whole-envelope hashes match for all three, covering 17,292
extrema records per history with governing identities and associated fields.

The direct and corrected response process-wall times were 162.876 and 160.530 s,
respectively, including startup/build and three history evaluations. Sampled
process-tree CPU use was 161.375 and 159.563 CPU s. Mean system utilization was
11.05% and 10.31% across 32 logical CPUs. This does not suggest substantial CPU
starvation; it does not prove identical cache or scheduling conditions.

## Separate controls

Numerically corrected, pre-final-authority control histories use independent nonlinear coefficient functions
of time, pressure, translational acceleration and explicitly balancing nodal
loads. A changed-coefficient holdout shifts the time history. The models are
small (48 DOFs; 96 for the two-body control) and do not establish large free-free
model performance.

| Workload | Cases | Cold direct / M8 | Warm direct / M8 | Cold speed ratio |
| --- | ---: | ---: | ---: | ---: |
| Supported selected histories/reactions | 16 | 1.772 / 0.932 s | 1.140 / 0.286 s | 1.90x |
| Free-free whole envelopes + selected histories | 16 | 1.992 / 1.061 s | 1.350 / 0.344 s | 1.88x |
| Free-free changed-coefficient holdout | 64 | 6.040 / 1.766 s | 5.472 / 1.138 s | 3.42x |
| Two disconnected balanced bodies | 16 | 2.167 / 1.163 s | 1.466 / 0.371 s | 1.86x |

All control histories/envelopes are identical to their paired references.
The small 64-case free-free control exceeds the speed threshold, but these are
still canonical stress/envelope solves. It is evidence for batching, not a
qualified component-response or large free-free speed claim. The retained
free-free numerical library stays at 6,142 estimated bytes for 16 and 64 cases;
peak RSS changes from about 183.1 to 184.9 MiB as the effective block grows from
16 to 32. Full accumulator retained bytes were not separately logged by this
screen; 10,000-case boundedness is not claimed.

## Verification and preserved failures

The affected-path integration check `m8-root-final-response` passed
**38 tests**, including the historical response-accuracy regressions, app response
integration, independent constrained-load/ownership/free-body cases and the
existing staged-recovery/block-size/governor check.

After the final authority hardening, `m8-solver-10` passed 11 focused tests
(13 deselected). The broader `m8-root-final-authority` check reached its 26-second
process-tree timeout after 26.0346231 seconds. Its partial log contains 47 progress
dots but no completed summary or XML; it is **incomplete**, not a passing suite.
No failure appeared before timeout. Broad regression of the final hardened source
therefore remains an unmet verification item. This is separate from the scientific
NO_GO of the removed response-component shortcut.

Follow-through on 2026-10-09: `m9-root-final-m8-regression` completed the same
final-source selection: **51 passed**, exit 0, 26.6744898 process-wall seconds.
This resolves the interrupted broad-regression item. The failed M8 timeout remains
preserved and charged; the successful check uses the separately authorized M9
correctness reserve. Scientific/performance disposition is unchanged.

Final solver source SHA256 identities:

- `prepared_static.py`: `9bfd155164823156674ca6b4b1e332e798d390ef615172476253a81298287d70`
- `prepared_static_response.py`: `c4df1e40c70238c96bfa5f5f0fbb61c20687e8eb79ce35eb9f953167d59c5152`

The timed numerical candidate used `a2302b054c154f808f428248b53a7cbe941287073322187be274f24106382e4d`
and `6a3bf434a79cdb156c4282163a1bfe5c12eb9f9e131c8e08cb42a6738d90b602`,
respectively. Timings are evidence for those recorded artifacts; the final
authority-hardened artifact has no measured performance promotion claim.

Earlier broad integration (`m8-root-integration`) executed 138 tests: 137 passed
and one root test incorrectly assumed a returned array was writable. After
correcting the test to exercise its actual read-only/detached contract, the
ownership check passed. A subsequent intermediate expectation about permanently
disabled write flags also failed and was corrected; neither was a product fix.
The unchanged earlier checks are retained, not counted as additional unique
final tests. The application example completed six cases and 32 extrema.

Full command lines and XML counts remain in each run directory. Intermediate
solver ingress failures, periodic-source resolver failures, wrapper-exception
test failures and the scientific component counterexamples are all preserved.
No failed scientific tolerance was relaxed to obtain a pass.

## Budget and disposition

M8 used **540.0326433999871 / 600 cumulative benchmark process-wall seconds**;
59.96735660001286 seconds remain unused. Startup, preparation, warm histories,
the preliminary candidate and the corrected rerun are all charged. Old benchmark
epochs remain closed. Correctness-check budgets are separate and recorded.
Root correctness checks consumed 118.7279141 / 120 seconds; solver-worker checks
104.6395796 / 120; FEM-worker checks 36.4547319 / 120. Remaining allowances are
not pooled or renewed. Failed and timed-out runs remain charged and preserved.

**Supported representative: NO_GO** for the 2x complete-workload or 50% peak-memory
promotion alternatives. **Small free-free control: speed threshold demonstrated**,
without qualifying a representative large free-free workload. **Full source
stress-response reconstruction: NO_GO in this slice** because its numerical gate
failed. The working safe fallback candidate and useful batching behavior remain
available for review; default APIs are unchanged.

No defensible 10,000-case barge projection or measured break-even is established:
only four-case representative histories were affordable, and fixed export costs
and block-size effects matter. A straight extrapolation of those warm totals
would imply hours and cannot justify a 10,000-case run inside the remaining
budget. The small free-free 16/64 lengths do not remove this representative gap.
No further campaign is authorized by this report.

Remaining limits include a representative selected-only comparison, a long
changed-envelope periodic holdout, larger free-free validation, mixed-packet
memory handling and any reviewed stress/contender error bound. Cheap residual
certification, response-output columns and hydrodynamic reconstruction remain
deferred. Preserved failures identify the next numerical problem; more repeated
timing alone will not qualify the removed component shortcut.

## Reproduction

Use the exact `command`, `cwd`, `environment` and `source_sha256` entries in each
`../evidence/checks/<run>/run.json`. Benchmark names are `m8-barge-direct`,
`m8-barge-response-final`, `m8-free-*-primary`, `m8-free-*-holdout`,
`m8-multiple-*-control` and `m8-supported-*-selected`. Do not rerun against changed
source while attributing the result to these recorded identities.

Public usage and fallback contracts: `PREPARED_STATIC_RESPONSE.md` and the sibling
`fem/docs/prepared_static_evaluation.md`; executable example:
`fem/examples/prepared_static_response.py`. Task-local benchmark/analysis scripts
are under `../evidence/`. Source/test ownership and detailed review handoffs are
in both worktrees' `.prepared-static-evidence/m8-*-handoff.md` files.

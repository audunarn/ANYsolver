# Native elastic S3 precision and checkpoint policy — development results

Solver product: `86d3759a2441ab22735c3e195e5bb44ed62beee8`, integration branch
`codex/b3-ge-e4-pl-integration`. ANYfem tests-only:
`2a5352c0adc5fcbce25bbb1484553108c906157f`; runtime remains `a615c4b`.
Level-A experimental implementation; no foundation, aggregate gate or release
is accepted by this record. Scientific criteria and consumed authorities remain.

## Decision and implementation

The unchanged partial-yield pure-fibre S3 fixture stalled at a shell membrane
roundoff floor. A same-fixture development toggle of the existing compensated
translation map completed both monotonic increments. The product now opts into
that complete map, including first/second variations, only for fresh native-fibre
owners containing elastic S3. No element equations, constitutive laws, physical
tolerances, loads, controls, Q4/S3 J2 policies, public selectors or version change.
The variational adapter's default arithmetic remains unchanged.

An initial cross-version check rejected an old mechanically accepted V7 endpoint
under the improved arithmetic. This observation was made through the shell tool;
it is not a separately saved process log. The correction is a distinct V9 stable
native-material schema (and anchored variant) in the existing binary framing.
V7 restores retain legacy arithmetic and checkpoint bytes. Validation tolerances
are unchanged. The actual old-wheel checkpoint and baseline/candidate comparison
are retained; both restore at 5.889190564e-9 and have identical rejected unloading,
accepted prefix and checkpoint SHA `3f2bffc00ca7dc7440541dbbe365e26cf59c702a2baa80109d89395db9701cb5`.

## Combined diagnosis

All numerical diagnoses use the frozen original geometry,1000-N tip load,
targets(.5,1) or the explicitly recorded unloading(.5,1,.5), default12 iterations
and8 backtracks, fixed accepted predecessors. No fixture/controller retuning.

| Case | Observed diagnosis | Development decision |
|---|---|---|
| Elastic pure-fibre S3 | Baseline completed at5.89e-9; stable-map toggle completed at6.32e-11. | Retain complete stable arithmetic, verify actual product. |
| Partial-yield pure-fibre S3 | Baseline first increment failed at2.26e-8 with membrane-force noise and sub-resolution correction; toggle completed both at4.27e-11. | Precision repair is warranted; monotonic product test must genuinely complete. |
| Full-section Q4 yield | Backtracking fails at relative.862; refined linear solves do not repair it and candidates switch yield branches. | Keep failure open; no shell precision or linear-solve claim. |
| Partial-yield S3 unloading | Fails at relative.522, retained(.5,1); beam-tip residual198N, trial branch switches. Equilibrated correction does not help; same-branch directional error7.86e-7 at largest inspected difference. | Preserve atomic failure and investigate admissible stepping; this is not unloading acceptance or complete tangent qualification. |

Toggle results are diagnostic evidence using installed baseline wheelb0f15d3e
with an explicitly recorded runtime hook. They are not installed candidate
qualification or comparable performance samples. Computational weighted row
metrics and near-zero-row backward maxima are diagnostics, not F03 norms or
conditioning acceptance. Saved unload NPZ includes material predecessors,
pattern and factor; its accepted-prefix checkpoint is retained.

## Verification

- Source focused11/11 in71.77s; additional charted/forged V9 controls3/3 in10.64s.
- Candidate wheel SHA `953f20d9a5f0fb7ae0c6c9068d373f7af625c7569ad5962e4e1cf9ea45765555`.
- Installed113/113,407.91s; bounded complete run413.4019197s,246206464B peak RSS,exit0.
- Source/wheel/site equality:385 solver and97 consumer modules;288 onsite imports.
- Actual Python3.14.2,one BLAS/Numba thread,JIT disabled; dependency versions recorded.
- Installed consumer1/1 selected,12 unrelated deselected,2.92s;
  complete run6.1991129s,214282240B,269 onsite imports.
- Consumer wheel unchanged:
  `ff143e5fece9dd4cec261aa69edbec03acc801d3d0bbfcb90cea7519d814f0c0`.

Checks include sub-reference-spacing strains, complete finite-chart map parity,
legacy default response, monotonic elastic/partial-fibre S3 physical equilibrium
and force/moment balance, material recovery, atomic rejected unloading, strict
binary history corruption/JSON/ineligible-schema rejection, actual rebase and
charted V9 restoration, and old-wheel V7 byte/status compatibility. The installed
ANYfem test exercises experimental input save/reopen and elastic S3 continuation.

Independent read-only code/mechanics and artifact review found no unresolved
consequential finding in this slice; see `review.md`. No public native-project
persistence, broad material history, external reference or scale claim follows.

## Retained failures and remaining work

Diagnostic-v1 failed on a helper's incorrect history attribute;v2 repairs that
helper only. Source-v1 retains the newly exposed yielded unloading failure;
source-v2 retains its obsolete V7-only test assertion after introducing V9.
Installed-v1/v2 retain incomplete copied fixture closures;v3 supplies the correct
closure with the same candidate wheel. Failures were not overwritten or counted
as passes. Raw runners, input manifests, logs, states and resource results are
included. Final frozen inputs are archived as `frozen-inputs.zip`.

Yielded unloading, strong full-section Q4 yield, simultaneous active yielding,
line/fibre combinations, full G3 and all remaining programme gates stay open.
No speedup measured. No formal F03 authority consumed, main merge or publication.
Next: prepare the programme's adaptive increment/cutback route with atomic
accepted-prefix ownership and unchanged physical acceptance; retain these fixed
increment failures as independent controls and specify the physical history
comparison before the next numerical batch.

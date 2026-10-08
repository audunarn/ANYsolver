# Optional native adaptive increments — development results

Solver product: `d6397cad2701566350620ccc6e274c4f51f5c808`.
Consumer tests-only: `527a48daaebcbefb1f5494efbfe7375f23be870d`;
consumer runtime remains `a615c4b`. Exact runtime is archived and bound to the installed wheel
in `r8-adaptive-installed-v1/identity.json`. Level-A development; no foundation,
aggregate gate, physical tolerance, release or consumed authority changes.

## Decision and implementation

The unchanged S3 partial-fibre fixture previously failed fixed-step unloading
while switching branches. Test the required increment cutback route without
changing geometry, laws, physical targets, default12 Newton iterations/8
backtracks or acceptance. A complete history supports this route for the case;
a prefix or exhausted budget remains failure, not demonstrated instability.

The existing point owner accepts optional `AdaptiveIncrementControl`. Typed
Newton/backtrack exhaustion halves the interval from the last accepted parent;
hold that step until the target. Retain all accepted midpoints and actual work.
No new line search, automatic growth, constitutive approximation or default
change. Backend, programming, memory, cancellation, ownership and unclassified
local failures propagate without retry.

V10 wraps the physical snapshot and exact targets/controls/limits/cursor/work.
Physical state and controller publish atomically. Stage actual full bytes and
check size before commit; cache them. Rebase retains pending plans. Restore
validates canonical metadata, dyadic decisions and factor history before
existing mechanical validation, without replay. Attempt-budget exhaustion is
terminal for that pending sequence. Work after the last accepted boundary is
reported by the exception, not retroactively added to the accepted checkpoint.

## Physical evidence interpreted together

Unchanged1000-N pattern, cutbacks4/attempts24, one thread/JIT off,600s/8GiB
per serial job. Final installed S3 checks actual import site.

| Case | Observation | Action |
|---|---|---|
| Partial-fibre S3, targets(.5,1,.5) | Completed(.5,1,.75,.5), one rejected unload; equilibrium1.39038e-10, gap7.7983e-18, fibre plastic strain9.93155e-6, last dissipation2.85182e-4J. | Retain controller. Fixed solve at identical accepted increments gives byte-identical physical checkpoint and fibre energies. |
| Full-section Q4, targets(.5,1) | Cutback limit; accepted(.0625,) with fibre plastic strain0; exact prefix restore. | Preserve failed evidence. Elastic prefix does not qualify strong yielding; no automatic budget/fixture/tolerance tuning. |

Installed S3 force/moment discrepancies4.99893e-14/1.07319e-12. Work177
evaluations,36 solves,102 rejected trials. No total-system energy, universal
tangent or broad material-range claim follows.

## Verification and identities

- Source v1 retains array-dataclass equality assertion failure; physical
  checkpoint equality had passed. Corrected v2:10/10; staging/canonical fixes
  v3:11/11; attempt-budget/prepared-cancel additions v4:2/2 selected.
- Installed88/88 in379.38s; bounded387.5329853s/250912768B,exit0.
- Solver wheel `654ff57c2f2f29bf1cd4f24d5049bc17162b4bfc48d23b2fcfe853da80076213`.
- Unchanged consumer wheel `ff143e5fece9dd4cec261aa69edbec03acc801d3d0bbfcb90cea7519d814f0c0`.
- Source/wheel/site equality386solver+97consumer modules;280 suite imports
  onsite;509 frozen inputs archived. Actual Python3.14.2,one BLAS/Numba thread,
  JIT disabled; in-process dependency identities recorded. No speedup measured.
- Old unmodified-wheel V7 restores byte-identically under legacy arithmetic,
  including its original failed unloading status.
- Installed S3 physical screen69.6931254s/161853440B; source80.4722159s/
  162738176B. Execution costs, not paired performance measurements.
- Failed Q4 screen60.4781666s/162369536B;exit0 means a diagnostic record was
  retained, not requested equilibrium completion.
- Installed ANYfem1/1 selected,13 deselected,52.58s; bounded56.2244806s/
  215064576B,270 onsite imports. Existing consumer saves/reopens experimental
  input, cancels at accepted yielded S3, restores V10 and completes direct/
  restored histories with exact reports, checkpoints and fibre energies.
  Consumer change is tests-only; ordinary native persistence stays open.

Controls exercise committed-parent parity, corruption/canonical framing,
changed targets/limits/loads, cancel-before-publish, atomic size failure,
pending rebase, exhausted budgets and unclassified-error propagation. Local
scheduling failures are explicitly synthetic; the physical screens independently
exercise real rejection. Review/dispositions: `review.md`. Failed evidence and
an incomplete archive-helper artifact are retained, never counted as passes.

## Remaining development

Bounded partial-fibre S3 unload now works. Strong Q4, simultaneous yielding,
broader rotation/material histories and full G3 remain open. Return to E01
shell/point transfer and M2 law/interface decision through focused mechanics
review before further refinement. All G0–G6/B2/external/scale/platform/consumer
obligations remain. No formal F03 consumed, foreign F03 edit, main merge or release.

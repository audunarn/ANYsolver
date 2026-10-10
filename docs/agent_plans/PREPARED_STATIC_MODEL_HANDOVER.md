# Model handover — prepared static response reconstruction

Updated 2026-10-09 after M15. State: **candidate implementation with diagnostic
prototypes; not accepted, merged, published or qualified for 10,000 cases.**
User requested this handover. No new audit, tests or benchmarks were launched for it.

## Objective and controlling contract

Build an opt-in source-response reconstruction route for 10,000 arbitrarily
varying quasi-static samples: whole-model stress/resultant and reaction envelopes,
associated components, governing input position/case/time and selected histories.
Supported and free-free models are equally important. All currently supported
ANYfem static load families, including acceleration and independent spatial/time
fields, remain available through direct cases. Default APIs stay unchanged.

Preserve existing scientific tolerances, canonical governing identities,
earliest-input exact ties, bounded transactional output, snapshot/private-factor
ownership and direct fallback. Near ties cannot be treated as tolerance ties.
Backward-error certification does not establish full-load correctness or governor
identity. Response increments must preserve prescribed offsets/initial fields
exactly once and actual constrained loads for reactions. No new mandatory native
dependency/backend/build, approximation, private-pointer inspection or relaxed
identity contract is authorized by the present diagnostic slice.

Authoritative history and adopted plan references are in the existing living note:
[PREPARED_STATIC_IMPLEMENTATION_TASK.md](PREPARED_STATIC_IMPLEMENTATION_TASK.md).
Historical plans are evidence, not fresh execution authority. Read current global
and repository AGENTS.md, ECOSYSTEM_GUIDE.md and ANYopenSoft philosophy before work.

## Exact artifacts and ownership

Task root: `C:/ANYworkspaceWork/prepared-static-20261008`.

| Artifact | Location / identity last verified |
| --- | --- |
| Solver candidate | `solver`, branch `codex/prepared-static-evaluator`, HEAD `cff55d95` |
| ANYfem candidate | `fem`, HEAD `3e4eb7f` |
| Frozen direct comparator | `m8-baseline/solver/src` and `m8-baseline/fem/src` |
| Main start identities | ANYsolver `da1ba2e9`; ANYfem `f74812d` |
| Interpreter | `C:/Github/ANYsolver/.venv/Scripts/python.exe` |

The candidate contains many task-owned untracked M1–M15 product/tests/docs/evidence
files. Existing tracked solver diff is `src/anysolver/__init__.py` (+20 lines).
Preserve all prior work and failed evidence. Main has unrelated dirty work; do not
reset, stash, sweep-stage or modify it. No commit/push/merge is authorized for M15.

Frozen candidate product SHA256:

    src/anysolver/prepared_static.py
    9BFD155164823156674CA6B4B1E332E798D390EF615172476253A81298287D70
    src/anysolver/prepared_static_response.py
    C4DF1E40C70238C96BFA5F5F0FBB61C20687E8EB79CE35EB9F953167D59C5152

Verify only identities relevant to the resumed action; changed inputs invalidate
their affected claims. Do not assume the current main and isolated candidate are
the same artifact.

## What exists and what is blocked

Prepared direct evaluator, response core and ANYfem sampled-periodic adapter
exist in the candidate. Displacement/reaction-only pattern cases reconstruct.
Stress superposition failed the strict historical screen and was removed from
production execution: stress/envelope cases still use canonical direct solve and
staged recovery. Canonical full-load mismatch also forces direct execution.

M10–M14 are test-side proof/diagnostic prototypes, not activated production guards.
They progressed from exact represented-system defect bounds to resident-factor
and signed correlated output bounds, then proved exact primitive allowances.
M14 removed exact selector/power-of-two staged-error allowances on the free-free
fixture, but native backward uncertainty still dominated. Prototypes do not have
complete transitive runtime authority/native admission. Principal stresses, full
reaction/source/offset coverage and whole-model qualification remain incomplete.
Windows longdouble has binary64 precision here; it is not extended precision.

### Latest decisive result: M15

[M15 report](../PREPARED_STATIC_M15_NATIVE_LIMIT.md) and
[owner handoff](../../.prepared-static-evidence/m15-solver-handoff.md).

The unchanged componentwise native residual relation admits a represented
triangular candidate with output error `2^-31 = 4.656612873077393e-10` against a
`1e-12` target. An independent two-case control shows it can admit reversal of
distinct true governors. This is **NO_GO for sufficiency of that relation alone**,
not an observed native solver defect. Actual tighter native behavior remains
**INCONCLUSIVE**. Scalar substitution is exact on the control but is not an
equivalence proof for the executed native solve.

SciPy public resident CSC L/U/permutation exports do not describe supernode
partition. Versioned gstrs uses scalar or vendor TRSM/GEMM paths according to that
partition. Installed SciPy 1.16.3 / OpenBLAS 0.3.29.dev runtime artifacts are hashed;
exact installed DLL-to-source/compiler/kernel mapping was not established. Failed
source retrieval does not prove provenance unavailable. Neither version labels nor
factor values justify a tighter native rounding contract. PARDISO is not covered.

**Stop further interval refinements under the same assumptions.** A useful next
step must establish an independently justified native arithmetic contract or
propose a separately adopted architecture/compatibility decision. Do not simply
reduce gamma, run another fixture sweep, replay only predicted winners or claim
reconstruction speedup with universal canonical replay retained.

## Verification and resources

M15: **7 distinct tests passed**, owner 3 + independent root 4; no failures/skips/
timeouts. They prove model insufficiency, not native qualification.

Raw commands, input hashes, runtime, counts and full logs:

    ../evidence/checks/m15-solver-01
    ../evidence/checks/m15-solver-02
    ../evidence/checks/m15-root-01

M15 correctness process-wall: owner `2.2034979000009116 / 120` seconds; root
`1.445966700000099 / 120`. Combined `3.6494646000010106`. These slice-specific
reserves do not become new benchmark authority.

M8 benchmark ledger remains **540.0326433999871 / 600 cumulative process-wall
seconds**; nominal remainder `59.96735660001286`. No benchmark was run in M15.
Other historical epochs have separate ledgers; never pool them or use the legacy
runner display as the M8 balance. A handover neither renews budgets nor authorizes
a new campaign. No 10,000-case measured qualification or speedup claim exists here.

Use `../run_check.py` for authorized bounded checks, unique evidence paths,
`--kind check --benchmark-epoch m8 --jit 0`, configured interpreter, isolated
solver source/tests, one numerical lane and precise process-wall accounting.
No check is required merely to reproduce already preserved handover evidence.

## People/process state and next action

OpenAI worker `/root/response_solver` completed M15, froze sources and released the
numerical lane. No task-owned numerical run was left active. Other historical
agent names are not proof of active work. Verify process ownership before stopping
or reusing anything. User ended coordination with “Speed up ANYfem meshing”.

Mistral availability is cached unavailable/exhausted; do not repeatedly reprobe.
Root's review is independent of the author but same model family. The required
different-family review remains unmet; no agreement or fallback waives it.

Next authorized activity is to read this checkpoint/evidence and identify a
concrete way past the native-contract obstruction within existing scope. Present
any needed architecture, scientific-contract, release or resource delta explicitly
before adopting it. Preserve the candidate and canonical fallback if no justified
route is available. Avoid restarting the entire investigation or converting this
negative diagnostic into an unexplained claim that response reconstruction itself
is impossible.

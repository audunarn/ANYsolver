# Slice 3 connected implementation assignment

Repository: C:/Github/ANYsolver. Mode: Edit. MaxTurns: 80. The human explicitly
authorized this full outcome on 2026-10-18. Read HANDOVER.md including active §8,
global/repository AGENTS.md and the adopted ecosystem philosophy. Do not launch
workers, change branches/history, commit/push, edit siblings, or touch unrelated
dirty files. Do not import/run retired programme tests or code to obtain evidence.

## Ownership and process

Own the connected inspect/design/implement/debug/check/repair/document loop for
the existing rotating MPC/work-conjugate route: the five source files listed in
HANDOVER §2; the two Slice 1/2 tests; new tests/test_nonlinear_beam_shell_slice3*.py;
and this task directory except original patch/ and supervisor_* files. Additional
shared dependencies need a concise boundary report to Astra before edits. Preserve
original diagnostic files before replacing them. No unrelated source edits.
Give an early progress checkpoint by turn 12 in checkpoint.md, naming findings,
intended repair, actual checks, budget used, remaining work and reserved decisions.
Reserve turns 66–80 for focused verification, repair, documentation and handoff.
Update HANDOVER §8 with actual outcomes. If you cannot finish, save a precise
handoff and stop; do not claim unrun checks. Ordinary compatible choices and
repairs of authorized checks need no serial permission. State scientific or
public-contract changes as proposals for Astra, not adopted changes.

## Exact deliverable and acceptance

1. Preserve identity (HEAD b0202d33, current five-file diff, original tests and
   unrelated dirty status). Run existing test_corotational_work_conjugate.py,
   test_nonlinear_beam_shell_coupling.py and the two test_standard_edge_beam_shell_*
   modules. Historical counts are 22+39; retain full logs and collected identities.
2. Instrument diagnostics with status, requested/achieved lambda, stop/failure,
   accepted snapshots/history, plastic history, cutbacks, reactions, iterations
   and independent reduced residual using copied state. Keep original solve
   parameters for attribution: six initial steps, max_iterations=30, default
   tolerance, repository S355 curve. Run corotational plastic -6k/-10k/-14k per
   loaded shell node, then VK elastic/plastic -6k on candidate and clean HEAD
   under same dependencies. Existing detached clean HEAD worktree location is
   in HANDOVER; if unavailable report rather than mutate unrelated worktrees.
   Residual must be reconstructed at achieved lambda AND requested lambda=1
   without re-evolving the returned state. Verify deep input-state immutability.
   `converged` is true for stopped_at_limit on HEAD: preserve compatibility.
   Partial load + small achieved residual => interpret correctly and classify
   stop; not proof of collapse. Invalid completion, large residual or mixed
   trial/committed state => repair cause and add regression. If this bounded
   batch cannot distinguish explanations, stop that question with evidence;
   do not start another parameter sweep. Continue independent permitted gates.
3. Use existing EP isolation geometry and S355 curve for direct and interpolated
   edge coupling; direct beam has 2 elements and interpolated counterpart 3.
   Pre-yield -2k/node must complete at lambda1, plastic strain zero and match
   elastic control. DC uz=-0.20 at original tip probe: num_steps12, max_iterations40,
   tolerance1e-8; complete, target error<=1e-8m, positive plastic strain. Split at
   uz=-0.10, resume to -0.20 and compare u/lambda/history with uninterrupted using
   existing restart tolerances, no relaxation. Verify rejected steps/cancellation
   leave caller restart inputs and accepted snapshots intact. Independent relative
   residual<=1e-7, existing constraint tolerances, balanced support reactions.
4. Retain linear comparison and run R1–R4 at12k, M1–M4 and P1–P4 at140k with
   explicit completed/target/residual records. Add M4(32,8,32), P4(32,8,48), existing
   R4(32,8,16). R4 within2.3% of matching linear; final refinement change in tip uz
   AND rotation <1%, M4/P4 differences<0.5%; report nonmonotonicity. Failure leaves
   gate open, do not tune physical inputs or criteria.
5. Independent analytical circular-arc reference: L1m W0.1m t0.001m, beam rectangle
   0.01x0.002m, e=0 and0.002m, E210GPa nu0, target30/60deg, shell nx8/16/32 ny2,
   matching and nonmatching beam counts nx and1.5nx. Derive neutral axis, composite
   bending rigidity, concentric radii, consistent end section forces/moments, small
   strain applicability and spatial moment conventions WITHOUT using production
   assembly/MPC to derive oracle. Save analytical_derivation.md early for Astra
   review BEFORE using results as acceptance. Standard classical moment reference:
   https://docs.software.vt.edu/abaqusv2025/English/SIMACAEBMKRefMap/simabmk-c-nlgeocantilever.htm
   Tip displacement/rotation errors<=1%; last refinement changes<=0.25%. Eccentric
   cases required. No reference fitting or post-observation tolerance change.
   Mechanical applicability/load-equivalence choices require Astra adoption.
6. Final regression exact 25 historical modules = targets in
   .development/standard-edge-integration-20261016/integration-checks-20261016/selection.json
   PLUS tests/test_instance_dict_descriptor_layout.py,
   tests/test_general_contact_native_deadline_scale.py,
   tests/test_general_contact_native_replay_diagnostics.py. Add two Slice1/2 modules
   and new Slice3 modules. Use scripts/run_portable_ci.py --development <targets>
   --jit off --timeout-seconds 600 --memory-limit-mib 2048. JIT off, one effective
   numerical thread, retired programme opt-in0; inspect actual runtime records.
   Report true counts including skips/failures; baseline364 is historical, not
   permission to drop selectors. Run final suite only after integrated edits.

## Resource and evidence contract

Shared allowance3600s cumulative measured process-wall, including failed attempts
and timeouts. Reserve last900s for final verification, no exploratory numerical
launch if it breaches that reserve. Individual diagnostic<=120s, regression<=600s.
One task numerical child at a time; no multiplies via delegation. Build a small
reusable task harness recording exact command/cwd, input/source/test hashes,
effective runtime versions/import origins/threadpool/JIT, exit/timeout, precise
process-wall, cumulative used/remaining, counts, full stdout/stderr and JUnit/JSON.
Use evidence/<unique-attempt>/, preserve partial failure output and kill only own
process tree on timeout. Python subprocess timeouts/polling appropriate. Budget
accounting must persist across sessions. Imports/setup/version preflight can be
included in timed harness. Do not run numerical pytest/solves outside harness.

Finish with: actual working result, changed files, exact checks/counts, failures,
budget consumed, numerical tables, remaining decisions/gates and evidence paths.
Worker checks do not establish final acceptance; Astra independently assesses
source/diff/evidence and non-author review. No claims for missing gates.

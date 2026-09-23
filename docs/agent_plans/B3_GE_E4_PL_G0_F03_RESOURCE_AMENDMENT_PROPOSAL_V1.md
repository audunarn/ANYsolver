# F03 scientific resource contract: proposed amendment v1

23 September 2026. **Proposal only; no registered budget is changed by this
document.** Attempt C is a consumed `FAILED_EVIDENCE` run, and its frozen
limits are not retrospectively changed. F03 remains `IN_PROGRESS`, G0B remains
open, and G1 product integration remains barred.

## Evidence that motivates the proposal

The immutable attempt-C archive is
`C:/Github/ANYsolver/.perf2-worktrees/f03-local-scientific-20260923-c`.
Its source commit is `a721400963ccf674f5e78c217447d5ab74cadf03`,
registration SHA-256 is
`f351ce7a6091e5b4e1b332a725e52b4e93156790397144899a2160f2a97b2249`,
and aggregate receipt SHA-256 is
`a37f3a27c0a82558d20844d3222822005278c5b2759f858c6e43a36b40ed0b95`.
The case stderr and terminal records remain in that archive. Read-only saved
operator diagnostics used the isolated installed ANYsolver 0.4.7 environment;
temporary enlarged budgets were passed only to diagnostic calls, not written
into the registered source or archive. They are feasibility evidence, not
qualification or a reinterpretation of attempt C.

| Case | Frozen first failure | Diagnostic measured need/result |
|---|---|---|
| Q1_L0 | Private snapshot omitted terminal-bound logs | Child completed; read-only four-file snapshot now verifies its 39 indexed members and lifecycle hashes. Saved-only numerical adjudication remains unpassed. |
| Q1_L1 | Equilibrium cumulative-bit cap 100 million | 382,986,275 cumulative bits; exact-rational equilibrium checks passed diagnostically. |
| Q2_L0 | Equilibrium cumulative-bit cap 100 million | 442,149,335 cumulative bits; checks passed diagnostically. |
| Q1_L2 | Six-block upper 807,448 exceeds cap 660,000 | Actual six-block nnz 795,024; binding used 110,468,841 bits and equilibrium 3,133,102,967 bits. Checks passed diagnostically. |
| Q2_L1 | Input-sum upper 240,162 exceeds sparse cap 234,772 | Actual KKT has 228,446 nnz, below the unchanged cap. Diagnostic solve and equilibrium checks passed; binding used 145,431,869 bits, six-block upper was 957,640, actual six-block nnz 934,208, and equilibrium used 3,797,130,985 bits. |

The numerical status in this table is limited to the directly invoked saved
equilibrium check. It does not cover the full case producer, all saved
components, cross-case comparison, the physical line-coupling decision, or
G0B. Attempt-C child sampled peak tree RSS was 80.8, 87.8, 180.5, 89.0,
and 113.4 MB for Q1_L0, Q1_L1, Q1_L2, Q2_L0, and Q2_L1 respectively;
those peaks precede the diagnostically completed checks. Diagnostic peak
memory was not recorded. The registered 6 GiB sampled RSS and 1,800 s per
case limits remain mandatory.

The current source shares one `MAX_EXACT_CUMULATIVE_BITS=100_000_000`
constant across several independent checks. The proposed 200-million and
5-billion limits must be **separate** named constants used only by state
binding and equilibrium. The existing 100-million limit remains in force for
all other exact checks until their own measurements justify a change.
Version the case/plan/registration resource contract for the future run and
serialize both new limits under distinct fields, retaining the old limit for
the unchanged checks. Tests must assert both values in case-plan and
registration round trips; a single global change to 5 billion would silently
weaken the state-binding guard and is explicitly excluded.

## Proposed exact contract change for a future registration

| Bound or rule | Frozen attempt-C value | Proposed future value | Basis |
|---|---:|---:|---|
| Physical sparse KKT nnz | 234,772 | **234,772 unchanged** | Check the actual union after bounded sparse addition; Q2_L1 is 228,446, while input-sum counting double-counted overlap. |
| Individual exact fraction bits | 16,384 | **16,384 unchanged** | No observed individual-fraction breach. |
| State-binding cumulative bits | 100,000,000 | 200,000,000 | Largest observed diagnostic use 145,431,869; 37% headroom. |
| Equilibrium six-block nnz | 660,000 | 1,000,000 | Largest observed preflight upper 957,640; 4.4% headroom, while actual was 934,208. |
| Equilibrium cumulative bits | 100,000,000 | 5,000,000,000 | Largest observed use 3,797,130,985; 31.7% headroom. |
| Equilibrium estimated Python work bytes | 4 GiB | **4 GiB unchanged** | Correct the estimate: cumulative bit work is not resident storage. Use the exact formula below and verify actual peak on the next registered run. |
| Other exact-arithmetic limits, physical tolerances, solve limits, process RSS/time | Existing registered values | **Unchanged** | No evidence yet supports changing them. A later failure remains visible and requires its own decision. |

The current six-block estimate multiplies the already complete six-block
inventory by six again and adds twice the *cumulative* bit allowance as if it
were resident memory. The proposed estimate, in **bytes**, is exactly
`1024*(six_upper + 12*(physical_dofs + 3)) + 128*max_fraction_bits`.
`max_fraction_bits` is the unchanged **per-fraction** 16,384-bit ceiling;
the 5-billion cumulative work allowance is not an input to this resident
estimate. For Q2_L1 (`six_upper=957640`, `physical_dofs=1470`), the result is
1,000,820,736 bytes (0.932 GiB), below the unchanged 4 GiB estimate cap.
This accounting does not replace the 6 GiB process-tree RSS limit. Before
authorizing the amended contract, test the formula at the maximum registered
case and independently review its memory rationale and sparse-union checks.

## Acceptance matrix amendment and decision boundary

| Row | Implementation | Qualification / decision |
|---|---|---|
| A/B/C immutable attempt evidence | Recorded | `FAILED_EVIDENCE`; never rerun, erase, or reclassify. |
| Four-file saved lifecycle snapshot | Candidate fix tested on Q1_L0 archive | `IMPLEMENTED_NOT_QUALIFIED` pending committed source, installed regressions and a new case receipt. |
| Actual sparse-union admission | Candidate fix; actual Q2_L1 KKT below frozen cap | `IMPLEMENTED_NOT_QUALIFIED` pending committed source, installed regressions and new case execution. |
| Resource amendment above | Proposed only | `NOT_STARTED` for canonical budget change; requires independent review and explicit authorization because it changes a frozen contract. |
| Five-case scientific and cross-case screen | Runner implemented | `FAILED` for attempt C; a new registration may be prepared only after the amended source/contract is reviewed and frozen. |
| F03 mechanics selection / G0B | Not established | `IN_PROGRESS` / open; G1 barred. |

If approved, commit a versioned budget-contract revision and tests, update the
canonical case plan/resource serialization, run installed regressions, then
freeze a **new** one-use registration. Report any new bound failures rather
than enlarging limits implicitly. No physical acceptance threshold changes.

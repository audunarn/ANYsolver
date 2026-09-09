# GE Beam3 P5 model-transfer checkpoint — 2026-09-05

This is a navigation and continuity record, not scientific evidence or new execution authority. The user requested preservation for a model change. Stop development at this checkpoint and resume from the state below after the switch. Do not restart historical formal runs.

## Exact working state

- Active worktree: `C:\Github\ANYsolver\.perf2-worktrees\ge-beam3-curved-p5-objective-lift-v1`.
- Branch: `codex/ge-beam3-curved-p5-objective-lift-v1`.
- Clean implementation head before this documentation-only checkpoint: `38d6bdaa828088726742882690ad9e56a2cc2088`.
- Implementation tree: `4a02a02dc502b64134c569fefce83aa69c423906`.
- Earlier P5 commits: `83254a43b76c98c738d331ce023026304856480f` (derivation preparation), `1432230440dbb8a81c86822af43bdaabe5afada5` (algebra probe), then `38d6bdaa828088726742882690ad9e56a2cc2088` (finite probe).
- P5 was branched from P4 handoff `b4317fb6153b38045f511ec3245b093f9e6bcb60`, tree `304da60a1bd2d1c9faf28c923a838f3fe566ef8b`.
- Main is clean at `09351645ba17a0a5b130a1c7a48007d36dd08ada`. No push, fetch, merge, tag, release, or publication was performed for this transfer. Prior remote audits are historical, not a fresh GitHub assertion.
- The P5 delta before this note comprises eight research documentation/probe/test paths only. No `src/`, package, workflow, existing element, or default change.
- The persistent overall goal remains active and incomplete. A model handoff is neither success nor a scientific blocker.

## Programme and accepted boundaries

The goal includes straight and initially curved objective spatial beams, six force/moment modes, nonlinear section history and state/restart safety, slenderness, large deflection/postbuckling, loads, mass, modal/prestress/buckling, and eventually objective eccentric/curved beam-shell joints. Do not shrink that goal to the current elastic probe.

Accepted P3 straight standalone closeout is `7aa359c18d1cf5db3dfb84d364afd9870e2da994`, terminal `PROVISIONAL_GO_GE_BEAM3_STRAIGHT_STANDALONE_OPT_IN`, formulation `GE_BEAM3_DC_MIXED_K1_MACRO_V2`. It is local and not integrated into main. Crucially, its class accepts a fixed immutable linear generalized section; nonlinear history-bearing material parity remains outstanding.

Accepted P4 private curved reference-geometry closeout is `e59670ec1e69c0aba4e4027aaa271efa91e46b8d`, terminal `PROVISIONAL_GO_GE_BEAM3_P4_PRIVATE_CURVED_REFERENCE_CORE`. This is geometry/frame authority, not curved mechanics qualification. Valid worktree suffix is `ge-beam3-curved-p4-reference-v1-authority-c1`; the similarly named worktree without `-authority-c1` retains a failed preclaim incident.

The existing `docs/agent_plans/GE_BEAM3_MODEL_HANDOFF_CHECKPOINT_20260905.md` records complete P3/P4 evidence, execution identities, incident history and external paths. Read it together with this successor note; its “next gate” predates the preparatory P5 work now recorded here.

Verified local preservation refs:

- `refs/archive/ge-beam3-p3-straight-optin-accepted-20260905` → `7aa359c18d1cf5db3dfb84d364afd9870e2da994`.
- `refs/archive/ge-beam3-curved-p4-reference-core-accepted-20260905` → `e59670ec1e69c0aba4e4027aaa271efa91e46b8d`.
- `refs/archive/ge-beam3-curved-p4-c5-preclaim-authority-incident-20260905` → `5befff866b25a31151c6d02106cc1b415587c33d`.

P4 cycle JSON intentionally has a nonclassifying BLOCKED sentinel. Its diagnostic checker terminal and canonical adjudication establish the accepted P4 result. Do not misclassify it from that sentinel.

## Current P5 implementation and evidence

Candidate proposal: `CANDIDATE_GE_BEAM3_DC_CURVED_OBJECTIVE_LIFT_V1`. It is **author development only**, not independently reviewed, frozen, formally executed, or qualified.

Read in order:

1. `docs/agent_plans/GE_BEAM3_CURVED_P5_OBJECTIVE_LIFT_PLAN.md`.
2. `docs/reference_cases/ge_beam3_curved_p5_preparation.json`.
3. `docs/reference_cases/ge_beam3_curved_p5_algebra_probe.py` and its test.
4. `docs/agent_plans/GE_BEAM3_CURVED_P5_FINITE_DEVELOPMENT.md`.
5. `docs/reference_cases/ge_beam3_curved_p5_finite_preparation.json`.
6. `docs/reference_cases/ge_beam3_curved_p5_finite_probe.py` and its test.

Verified current file identities:

| Path under docs/reference_cases | Bytes | SHA-256 |
|---|---:|---|
| ge_beam3_curved_p5_algebra_probe.py | 12162 | `677A32A6A1E004071B01619F6403593656A81757B410270A3298CF4A53636DEC` |
| ge_beam3_curved_p5_preparation.json | 3029 | `7CF583FC0E7D583AD04643C25D9AD81A1B45D7765FBCEBD5F31E18BF86B1CB29` |
| ge_beam3_curved_p5_finite_probe.py | 13322 | `F49C85FB7B7C098C9037204920F1682C0CB3BFE3C7920CD81679A9E2CC324470` |
| ge_beam3_curved_p5_finite_preparation.json | 1910 | `8F2CE8DFA99390A7DEE6FB717D61C0DFCF2482C000B85A083EF9BD6DBA727D49` |

Two half cells use the objective lift `r_h=I_c x+U_c(r0-I_c X)` and `Q_h=U_c R0`. There are 18 external coordinates, six internal relative rotation coordinates and 12 material moment coordinates. Reference integrals F/H/J yield the moment-eliminated potential `0.5 z^T F z + 0.5 (Jz+ell)^T H^-1 (Jz+ell)`. The finite probe solves only the six internal rotations and forms a Schur tangent. It includes internal-rotation work of spatial dead distributed force. Recovery obtains physical curvature from moment/compliance, not the zero compatible interior curvature.

Residual and tangent use analytic second-derivative propagation through the unchanged production `_ge_beam3_mixed_ad.py` kernel. This shared kernel is explicitly NOT an independent oracle. Independent equation reconstruction/review remains pending. Stateless elastic evaluations do not establish nonlinear history, commit/discard, or restart parity.

Previously completed test inventories, separately recorded (not rerun for handoff):

- Algebra preparation: 23 passed, 1.64 seconds.
- Finite elastic probe: 18 passed, 3.03 seconds.

Finite tests cover objectivity, coupled reversal/covariance, reference/straight-limit agreement, finite bend/twist, directional derivative checks in a fixed chart, local stationarity, distributed-load work/balance, physical recovery and bounded rejection. These are not engineering qualification or proof of the full slenderness range.

## Immediate unfinished investigation

The next intended step is a small element-level thin-beam conditioning diagnostic, not an assembled benchmark. Suspected risks are cancellation in direct Schur subtraction when axial/shear-to-bending stiffness reaches 1e12, and the fixed absolute internal residual threshold in the finite solver. Neither risk has yet been adjudicated as a defect.

A read-only four-case diagnostic was issued immediately before context transfer, but its output was not retained in the visible context. Do not claim it passed or failed. No implementation change followed it. If needed, repeat only this inexpensive diagnostic, not any historical formal request:

- Straight helper reference, coordinates (-1,0,0), (0,0,0), (1,0,0).
- Section diagonal `(rho^2,rho^2,rho^2,1,1,1)` for rho = 1, 100, 10000, 1000000.
- External displacement mode `uy=(0,0.5,0)` and global `rz=(1,0,-1)`, other entries zero.
- Inspect `0.5 q^T K_condensed q`; the mathematical pure-bending energy is 1.

If evidence confirms cancellation, investigate an equivalent square-root/QR reference condensation that retains energy factors rather than subtracting large matrices. This is a proposed diagnostic direction only, not an approved new formulation or proven remedy. Dense stiffness cancellation may remain even with factors; do not make unsupported thin-range claims. Do not loosen tolerances, empirically stabilize, or change accepted P3/P4 mechanics to hide a failure.

Further work remains on independent integration/reference accuracy, curved engineering cases, slenderness, nonlinear sections/state, mass/dynamics/buckling, packaging and beam-shell connections.

For ordinary focused unit tests, the known environment is:

```powershell
$env:PYTHONPATH='C:/Github/ANYsolver/.perf2-worktrees/ge-beam3-curved-p5-objective-lift-v1/src;C:/Github/ANYfileIO/src'
python -B -m pytest -p no:cacheprovider tests/test_ge_beam3_curved_p5_finite_probe.py -q -x
```

Do not add the active ANYmesh source checkout; concurrent work there must remain untouched.

## Processes, resource authority, and transfer safety

- `Get-Process python,pythonw,git` returned no visible matching process at transfer. Command-line enumeration via CIM was denied by sandbox permissions; it is not claimed as a full system process-tree audit.
- No `C:\Github\.resource-manager\active-lock` was present. The manager listing contained historical released-lock directories, which must not be removed.
- Ledger SHA-256 at transfer: `DB2E78346D6CFDC0C4EAE7133DE354402B540B3E281C2B012291C4547E0EE964`. This checkpoint did not modify the ledger or requests.
- No P5 formal request or execution authority was created. P4 request `173f5eb7c11f42518db832916705f74f` is consumed; do not reuse it.
- `beam_goal_gap_audit` and `beam_transfer_evidence_audit` are completed; `p4_executor_impl` is interrupted. No child agent is running. Their accepted findings are captured in the earlier P4 handoff and here; do not assume a paused agent will continue automatically.
- Accepted raw evidence remains external at `C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-curved-p4-formal-16413b7610f04ec4b19c0bb4f886ec5d`. The previous handoff binds its inventory. This transfer did not rerun or mutate it.
- Heavy/performance tests require the `C:\Github\AGENTS.md` resource request, explicit ledger approval, global lock, and release in finally. Ordinary small unit tests are exempt. Preserve one numerical thread, 24 GiB, 600-second child and 1800-second wave bounds for future formal waves; no automatic retries.
- All work is preserved locally in Git, not newly backed up to GitHub by this checkpoint. On the same machine the next model can use these paths directly. Moving to another machine requires explicit transfer of local branches plus external evidence/ledger, not merely main.
- Do not mark the overall goal complete or activate/default-route/release the curved candidate. Preserve `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

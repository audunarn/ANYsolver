# F03 classical stiffness-versus-trace diagnostic registration

22 September 2026. **Single-use diagnostic, not a physical-reference acceptance gate or authority for the 96-case inventory.** The natural Q4↔CST-CB loaded root moment reversed sign and its absolute difference grew Ny32→64, triggering the registered stop rule. The bounded hand-host, support and signed-work tests, design and independent narrow reviews are recorded in `B3_GE_E4_PL_G0_F03_BOUNDED_TRACE_REACTION_DIAGNOSIS.md` and `B3_GE_E4_PL_G0_F03_STIFFNESS_TRACE_DIAGNOSIS_DESIGN.md`. No old result is reclassified.

## Frozen input and execution

- Exact clean execution source: `ed1b71a0951bbadaaf6682568b60baba55a00e0b` on `codex/b3-ge-e4-pl-integration`. A later documentation-only commit may add this registration; executable bytes in the eight source-hashed runner/module files must be identical. Stop before execution if the checkout is dirty, HEAD source differs, dependency identities change, or a target evidence root exists. Do not amend this registration to accommodate an observed result.
- Runner: `scripts/b3_e4_f03_resource_preflight.py`, `--solve --scaled --loaded-probe --state-payload --law P1`. Use `--topology` to select shell stiffness and `--trace-topology` to select the reference trace. The runner asserts identical node arrays, DOFs and support masks; Q4 and CST-CB remain the only options. `Ks` is built from stiffness topology, `Cs` and pose/gap/bounds from trace topology, `Kb`, `Cb`, load and supports otherwise identical. Mixed pairs are algebraic probes, never physical candidates.
- Physical case: `Ns=128,Nb=512,Nm=64`, Ny32 or Ny64, smooth signed load, P1 line, reference axes and four offsets as frozen by the modules. No new parameter fits or tolerances.
- Environment: Windows 11 build `26200`, Python `3.14.2`, NumPy `2.4.6`, SciPy `1.17.1`, psutil `7.2.2`, same imported module paths/backend as the historical roots; `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=1`, observed one-thread pools. Abort if this identity differs. Per-case supervisor limits: 8 GiB RSS and 900 s. Execute serially, not with concurrent benchmarks.
- Every root is new and immutable under `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/`. Manifest, phase JSONL, stderr, RSS series, result, and `solved_state.npz` are retained including failures. Each child and post-run file hash must equal its manifest. The state payload carries finite contiguous float64 physical `q` and signed `λ`, shape/hash metadata and byte hash. Valid success requires the exact ordered 11 natural or 12 mixed phases, with loaded recovery last; corrupt or missing state is failed evidence. Cancellation/limit failure retains its original root and terminates this diagnostic until independently adjudicated.

| Order | Ny | `Ks` | `Cs` trace | New root suffix |
|---:|---:|---|---|---|
| 0 | 4 | Q4 | CST-CB | `f03-stiffness-trace-smoke-v1` (`Ns=2,Nb=4,Nm=2`) |
| 1 | 32 | Q4 | Q4 | `f03-stiffness-trace-y32-kq-cq-v1` |
| 2 | 32 | CST-CB | CST-CB | `f03-stiffness-trace-y32-kcb-ccb-v1` |
| 3 | 32 | Q4 | CST-CB | `f03-stiffness-trace-y32-kq-ccb-v1` |
| 4 | 32 | CST-CB | Q4 | `f03-stiffness-trace-y32-kcb-cq-v1` |
| 5 | 64 | Q4 | Q4 | `f03-stiffness-trace-y64-kq-cq-v1` |
| 6 | 64 | CST-CB | CST-CB | `f03-stiffness-trace-y64-kcb-ccb-v1` |
| 7 | 64 | Q4 | CST-CB | `f03-stiffness-trace-y64-kq-ccb-v1` |
| 8 | 64 | CST-CB | Q4 | `f03-stiffness-trace-y64-kcb-cq-v1` |

The smoke validates the new child/supervisor/payload path, not natural parity. At each Ny, **run both natural controls and adjudicate their parity before either mixed case**. Historical controls are `f03-classical-cst-cb-y32-q4-v1` (manifest `0402d1452613801896e45b201a4aeddff00666a3ed22d3d4f9b78c127ac18e43`), `f03-classical-cst-cb-y32-v1` (`f9522121ba077c4fe36b6cbd5bfbd5b9ef6544fe0ac942f4df9f49fcbe2e16a6`), `f03-classical-cst-cb-upper-q4-v1` (`1ac115f9e18dfedde87663b67735880be2c26aa3a2ea124fa9eeac682bbc3757`), and `f03-classical-cst-cb-upper-v1` (`b0b01d74271f6c02f7dc664aaea5af9cf4e5a7a7e9a2414f840dc708c4fd38b3`). Read old roots without rewriting them.

## Pre-execution parity and stop rule

Compare every signed one of the 23 channels (two separate energies, tip `u,v,Lcθ`, three station triples and three grouped support `Fx,Fy,Mz` triples) against the matched historical natural control. Require `|new−old| ≤ 10⁻⁸ max(|old|, floor)` **for each channel**. Floors are the already drafted physical scales: `0.001E0` per energy, `0.1U0` per displacement/converted yaw, `0.01F0` per support force and `0.01M0` per support moment, with `F0=M0=10⁶`, `U0=6.802721088435374×10⁻⁵ m`, `E0=F0 U0`. This stringent parity is a runner equivalence rule, not the still-draft 1% physical convergence criterion. Additionally require `|ΔG2|≤10⁻¹⁰`, `|ΔGmotion|≤10⁻¹⁰`, each balance/residual ≤ existing limits, and finite ordered exact field bounds. An old root with failed identity, incomplete phase or changed manifest blocks comparison. Any parity failure stops **before** hybrids at that Ny and preserves all new raw roots; do not relax the rule afterward.

The smoke, natural controls and hybrids each require finite results, free residual ≤`1e-8`, weak residual ≤`1e-9`, global balance ≤`1e-8`, energy identity and net interface work ≤`1e-8 E0`, valid exact-rational bounds and source/phase/payload identities. A run that fails one criterion stays failed. Do not restart or replace a consumed root to make the table complete. The diagonal congruence and chosen sparse backend remain fixed.

## Adjudication

Before interpreting a hybrid, independently reconstruct the physical signed KKT residual, support decomposition and port work from saved `q,λ` and the two declared panels, without refactorizing or replaying the solve. Match the reported left/right/root grouped reactions and all station/gap observables within their algebraic tolerances. Report edge contributions by fixed physical y band and signed port wrench distributions; do not infer a physical traction from multiplier magnitude alone.

For each of the 23 signed channels, use `Y(K,C)` to calculate total `Y(KCB,CCB)−Y(KQ,CQ)`, symmetric `ΔC`, `ΔK`, and signed interaction `I` as defined in the design. Verify `ΔC+ΔK=total` before applying any absolute/floored percent. Report both single-factor paths; separately show the left `Fy` and root `Mz` values, `G2`, energy/work, exact bounds, fill, elapsed, peak RSS and failed work at both Ny. The original draft 1% physical screen remains failed at Ny64 regardless of a successful attribution. A C-dominant result directs a trace/port formulation revision; a K-dominant result directs shell stiffness/support partition analysis. Neither outcome qualifies B3-GE/E4-PL, changes G0B status, authorizes larger inventory or replaces mandatory external references.

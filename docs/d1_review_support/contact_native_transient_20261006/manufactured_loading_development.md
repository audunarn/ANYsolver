# Native manufactured loading: installed development verification

6 October 2026. Solver candidate `fdbae395`; held private wheel SHA256
`6252c0f69bc3f621755216c694c2bf6d3e608f0e032938b4eafa3047e3cdc3cb`.
The separately approved 100-second C7 loading allowance covered these runs.

| Run | Result | Exact process wall | Peak memory |
|---|---|---:|---:|
| Five installed loading/reference/restart checks | 5 PASS | 42.534399800002575 s | 166686720 bytes |
| Actual public four-step CLI | PASS; four accepted steps | 20.591879999963567 s | 147337216 bytes |

Total 63.12627979996614/100 s; 36.87372020003386 s remains **only for this loading scope**.
No old safety allowance was consumed. Each run used the private installed solver;
194 imported modules per run matched its paths/hashes. All 545 held installed
payloads matched the held wheel. Observed JIT disabled, Numba one thread and
every observed numerical pool one thread. These are measured settings.

The independent primitive-ellipse reference covers only a free straight centered
zero-lift beam with common translation and longitudinal principal-axis spin.
Actual force and distributed cell-couple work drive a 0.2512091543634712-radian
angle increment. Worst normalized analytical/work/impulse/stage error was
2.602647347139155e-13. Frozen analytic 0.1%, balance/work 1e-6 and native
stage/endpoint 1e-11 limits passed. Four-step full and fresh split continuation
results and complete checkpoint bytes matched exactly.

This is **tested development**, not independent engineering acceptance or full
C7 qualification. Deforming and nonprincipal motion, connected dynamics, broader
sections and C8 common-stage coupling remain open. The later shared controller
and connected source were not imported or numerically tested by these runs.

Raw evidence: `C:/ANYworkspaceWork/contact_native_transient_20261006/`:
`native_manufactured_loading_installed1/`,
`native_manufactured_loading_installed_cli1/`,
`native_transient_manufactured_loading_root_execution_audit.json`,
`native_transient_manufactured_loading_authority.json` and
`native_transient_manufactured_loading_preparation_v2.json`.
Exact four executed input files are preserved in `manufactured_loading_executed_inputs/`.
The original source snapshot and withdrawn energy-field review finding remain.

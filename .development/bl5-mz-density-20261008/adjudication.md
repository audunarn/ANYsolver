# Matched Mz interface-density comparison — 8 October 2026

This one source-development run reused the exact 1 m specimen, five-channel
weak P0 line, +1 N m work-matched end action and numerical checks of the
previous Mz comparison. The source change exposes accepted multiplier
densities; it does not change either mechanical solve. The continuum uses
`C_ref=beam-shell`, the native owner `C_native=shell-beam`, so the comparable
physical native density is `-lambda_native`. A single result cannot select
P0 or establish mesh-uniform stability.

Both four-edge densities give nearly zero resultant interface force and
+1 N m shell Mz about the same origin. Their Fy force resultants per
quarter-length edge are, in N:

| Edge x range (m) | Resolved continuum | Native equivalent |
|---|---:|---:|
| 0–0.25 | -1.186419412 | -1.887679566 |
| 0.25–0.5 | +6.780194977 | +7.294771048 |
| 0.5–0.75 | -14.001131716 | -12.926503399 |
| 0.75–1 | +8.407356152 | +7.519411917 |

The translation-density L2 difference is 6.572458076 in its own units,
against reference norm 70.890784930. The director-density difference is
0.548143877 against reference norm 0.510603159, assessed separately because
the channel units differ. Both signed actions have the same net Mz (reference
0.999999999971, native 1.000000000000 N m), but different spatial
distributions. Do not collapse these into one mixed-unit quotient or use the
small global residual to choose a multiplier basis.

The previous work-matched comparison found native total work
1.8863005195e-6 J versus continuum 6.4452481344e-7 J, with the difference
primarily in beam-side internal work. The present result proves the two
accepted interface actions are not the same pointwise. It therefore blocks
attributing that work difference solely to the beam material/section or body
operator. The next discriminating calculation would apply one *common*
physical density to both beam bodies and compare their compatible work,
retaining each native half-cell port. The older body-port retry has separate
pending authority and was not run or renewed here. No new external executable,
formal F03, ratio campaign or production acceptance occurred.

The sole attempt completed in 2.8639997 s process wall, sampled 165,920,768 B
peak RSS under the 2 GiB/60 s limit, with effective child CPU affinity [0],
one loaded numerical thread and JIT disabled. Exact source SHA, command,
environment and outputs are in `receipt.json` and `case-v1/result.json`; raw
stdout/stderr are retained. M2/F03/G0 and physical accuracy remain open.

Decision: can the already installed native adaptive owner carry simultaneous
Q4/S3 shell J2 and physical fibre flow in the existing two-stiffener model?
Use EXACT laws/sections/geometry/offsets/supports/point identities from
examples/stiffened_shell_coupled_plastic_history.py. Replace only the second Q4
(2,3,6,5) by oriented S3 (2,3,6),(2,6,5); keep the first Q4. This is an explicitly
new mixed mesh, not rewriting a frozen failed case. Generalized member remains
elastic; physical fibre member retains its existing low-yield fibre law.

One bounded monotonic history: ordinary accepted zero-force reference, direction
150N at each stiffener tip, nominal displacement from reference-linear1500N at
each tip and control beam105 translation z. Existing adaptive6cuts/24attempts,
fixed corrector20/12, one job600s/2GiB/affinity1/pools1/JIToff. No curve/load/budget
sweep and no replay of the prior failed fixed single/quarter histories.

Accepted-step evidence: mandatory equilibrium/constraints, actual per-family
shell-alpha growth and actual fibre plastic increments, nonnegative last-increment
fibre dissipation. Need at least one accepted step with growth in Q4 AND S3 and
physical fibre flow; accumulated yielding alone is insufficient. Preserve every
failure and accepted prefix. Successful monotonic activity permits the declared
unload/reversal extension; failure stops this screen without automatic tuning.

This is Level-A implementation evidence, not aggregate G3, physical capacity,
global energy balance or independent qualification. Existing F03 restrictions and
complete Revision8 scope remain intact. Reuse verified wheel13e6a88c and unchanged
consumer626f27b6 only while all520 product source identities still match.

Mixed screen terminal: nominal history completed, Q4/fibre flow positive, S3
inactive. COMPLETED_ACTIVITY_INCOMPLETE is failed scientific activity evidence;
no numerical equilibrium failure. STOP that mixed loading slice; no load/curve
increase or unload/reversal extension. Root Q4 carries observed yielding.
Next independent required combination: same exact material/section/geometry,
all-S3 mesh also splits firstQ4 (1,2,5,4) to (1,2,5),(1,5,4). This moves the
observed active root into S3, testing formulation coexistence with fibres instead
of driving the distal mixed S3 into yield. Target recomputed from that mesh's
same1500N/reference loading, same20/12 and6cuts/24attempts. Preserve mixed
incomplete criterion; all-S3 success cannot close that mixed row. One all-S3
screen, no further automatic variants if inactive/failure. Activity uses paired
fibre plastic increment AND positive dissipation in the same shell-active step.

All-S3 nominal screen COMPLETED_SIMULTANEOUS_FLOW: S3 alpha grows and actual
paired fibre increments/positive dissipation in same accepted step. Proceed to
ONE signed extension from that accepted nominal checkpoint: (.25nominal,
-nominal,1.1nominal), representing displacement unloading/reversal/reload,
not force1500/375/-1500/1650 endpoints. Same material/model/controller6cuts24
and20/12, no changed budget/laws. Completion requires mandatory physical checks,
monotonic irreversible alpha, nonnegative last-increment fibre dissipation.
Failure preserves prefix and STOP. Restart/consumer parity must verify any
completed history before delivering it as tested behavior.

# Preserved smallest-step directional failure; nonclassifying diagnosis

Corrected candidate d90aa3e253729393d81e8ec13702cf9bb8d26755,
tree 997aa912d1e4c0f4b3003e2bf01c53913c939af3, passed the one-node B2 smoke.
Its separate full development lane ended with 17 passed and one failed in
20.63 seconds; full child 32.34677830000874 seconds, peak 252174336 bytes,
exit 1 and zero remaining processes. Raw files remain in
Temp/anysolver-g3c-owner-development-hno4hsk5, lease SHA-256
c75c20e61b5ab5690ee775a06d6546757d4feaf1b3430343dee0038e21efcfa0.

Actual finite-root loading, fresh native accepted-origin validation and all
state-safety regressions passed. The full KKT directional test failed with
normalized error 2.767173042642239e-7 against 1e-7. The log contains all seven
trial evaluations (centre and three plus/minus pairs), locating the failure
at the final h=1e-6 check. This is a genuine development gate failure, not a
qualified graph or a waived tolerance. No independent full mechanics lane runs
on this failed candidate. The initial failed smoke/review also remain preserved.

Add exactly one nonclassifying diagnostic node and --diagnostic runner lane.
Retain the exact u, multipliers, direction, three h values, source mechanics,
norm and threshold. Report full/native1/native2/B2/joint-support derivatives,
exact assembly decomposition, native internal residual and full Schur errors.
Do not select a favorable h, average away disagreement, alter coefficients,
tolerances or fixtures. Diagnostic PASSED means only that instrumentation
completed; it cannot supersede the failed 18-node development gate.

Command: C:/Python/Python314/python.exe -I -S -B
scripts/run_ge_beam3_g3c_owner_bridge.py --diagnostic.
Run once from the new clean freeze in a fresh exclusive directory. Same accepted
design and complete source/environment lease, one numerical thread, 24 GiB/tree,
600 seconds, 120-second inactivity watchdog, no retry. The diagnostic inventory
is one node, separate from smoke and development inventories. Any correction
must follow evidence and independent review; no existing mechanics are changed
by this diagnostic patch.

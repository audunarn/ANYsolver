# Equilibrium-force controller development gate

Parent bd37aa797ab46d0c56ca57ecbf02e1a9f06f68f8, tree
00727031142324f0d9620a55e8b2fba58ff90ba0. Preserve every previous controller,
mechanical operator, default and qualification packet unchanged.

The new private controller copies the preserved Schur loop and changes only
the captured linear solver, program identity, and diagnostic labels. Use frozen
equilibrium recovery from d4611ac; retain the complete Jacobian, natural-merit
line search, accepted-only history transactions, and 1e-11 residual limits.
No full mixed fallback is available. Do not claim production qualification or
speed improvement from a correctness gate.

Compare the three registered development paths (straight elastic, curved
elastic, plastic load/unload/reversal) against hash-bound archived dense
checkpoints. Do not rerun the dense paths. Compare every accepted mechanical
state, constitutive origin/history, residual, and final physical recovery.
Verify native pause/resume byte identity, cross-backend restart rejection,
cancellation before trial/commit and after factorization, injected solver
failure, frozen-input mutation and iteration exhaustion. Preserve failure logs
before asserting success. Eleven test nodes; three path fixtures.

Run one smoke wave selecting the three path-comparison nodes first. Any failure
stops this candidate and is preserved; do not repeat the same failed path or
relax acceptance. Only after smoke success run the full transaction rehearsal,
freeze the implementation, and run two fresh-directory deterministic cycles.
Every child: one numerical-library thread, 24 GiB process-tree memory,
600 seconds wall and 120 seconds CPU inactivity; each controller retains its
120-second deadline. No automatic retry. All scientific packets between frozen
cycles must be byte-identical; timings remain separate diagnostics.

Independent human/agent review remains pending until actually performed; this
implementation self-check must not be labelled independent review. A passing
development gate permits further bounded integration/performance work, not
public selection, packaging, or completion of the overall GE-B3 programme.

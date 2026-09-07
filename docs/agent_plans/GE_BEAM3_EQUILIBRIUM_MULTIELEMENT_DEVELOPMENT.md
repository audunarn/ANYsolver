# Connected-member force-recovery gate

Parent 84e22d78b04c1941c5dd1124c73ed381b96dcf9f, tree
6cd24fbde0af312fd042fc0617041119b60ea740. No solver or mechanics changes.
Use frozen native equilibrium controller 66774bf and recovery d4611ac.

Freeze three new length-two member cases, declared in the companion test:
two straight macrocells with physical plastic fibres and load reversal; two
curved macrocells fixed at both ends; four curved cantilever macrocells.
The clamped case requires six original compatibility equations to complete
force recovery. All cases use the existing coupled section and four-point
per-half quadrature, unchanged. Do not use finite sample success as general
coercivity, locking, modal, or production qualification.

For each new case compare full dense and equilibrium-recovery paths at every
accepted state, origin/history, and residual, and final physical recovery.
Require the existing 1e-11 comparison/accepted-equilibrium limits. Independently
reconstruct the declared Q2 quadrature load resultant and verify summed support
reactions plus applied force. Require genuine plastic history in the straight
case. Check byte-identical same-backend pause/resume and reject changed support
authority. These are new development paths, not reruns of historical campaigns.

Six test nodes. Run a fail-fast three-node smoke first; any failure stops this
candidate and must be preserved before correction. After a passing complete
rehearsal, freeze and run twice in fresh directories. Canonical packets must
be byte-identical; preserve separate inventories and raw failures. No retry.
Each child: one numerical thread, 24 GiB process-tree memory, 600-second wall,
120-second inactivity. Each controller retains its own 120-second deadline.

No public routing, beam/shell mechanics, default, tolerance, or qualification
record may change. Independent review and production integration remain open.

# F03 cross-case adjudication: next implementation boundary

23 September 2026. This is a handoff design, not a passed gate or a
scientific registration. The preceding child identity, typed cancellation
and read-only single-case replay prerequisites are committed at `d88af7f4`.

The aggregate reader must first reopen the one immutable registration and
require exactly the ordered `Q1_L0`, `Q1_L1`, `Q1_L2`, `Q2_L0`, `Q2_L1` case
bindings and exact plan-archive hashes. First inventory every sealed receipt
and lifecycle. A missing, invalid or incomplete execution follows the
existing precedence immediately. Call `replay_case` with the registered ZIP
hash only for a case with complete successful execution evidence; this
includes numerical `FAILED` or `HOLD` cases that must be independently
recomputed. After all applicable replays, any nonpassing case leaves every
cross-case predicate `NOT_EVALUATED` and sets the aggregate status under
existing precedence. A partial subset cannot enter the settling screen or pass.
Never turn a missing case into a new launch or replacement measurement.

For each case, extract physical `q`, primary shell and beam stiffness blocks,
load and root operators, exact target prolongation, common trace/pose action,
and the saved physical interface functional from **one** retained
saved-evidence snapshot. Bind that snapshot to the same replayed receipt,
registered plan ZIP, evidence/numerical/inverse hashes, and source identities;
recheck those identities on context exit. Use the sealed receipt's ordered
settling values, scales, enclosures and source hashes for all 45 scalars;
never recompute recovery ad hoc. Re-derive each nested prolongation from the
two frozen topologies and compare exact rows, columns and Fraction weights.

Before a nested Ritz claim, verify the common trace/pose action, `C_f P=C_c`,
`P.T f_f=f_c`, and `P.T K_f P=K_c` **separately for primary shell and beam**
using the frozen integration, saved-action and trace tolerances in the
registration. These are saved-block/action comparisons; no element assembly
or equilibrium solve is permitted. The equal-size Q1/Q2 pairs are not nested
and receive none of these Ritz or energy-identity checks.

Apply the frozen Section 6 protocol without changing thresholds:

- For all 45 signed settling channels, each nested transition uses
  `abs(f-c)/max(abs(f),abs(c),1e-3*S) <= 0.01`. On each two-transition chain,
  the last absolute change must be no greater than the preceding change plus
  `1e-5*S`. `Q1_L2/Q2_L1` is the **only gating cross-family pair** and uses
  the same pairwise 1% rule without a nesting claim. Do not emit
  `Q1_L1/Q2_L0` in this aggregate; it has no gating role.
- For a nested transition, use `delta=q_f-P q_c` and
  `distance=0.5*delta.T*K_f*delta`, with `K_f` the sum of the saved primary
  shell and beam blocks. Require nonnegative distance, total-energy
  monotonicity within `1e-10*E0`, and
  `abs((E_f-E_c)-distance)/max(E0,abs(E_c)+abs(E_f)+abs(distance)) <= 1e-10`.
- Build the complete signed functional difference with
  `local_functional.difference` from the two validated saved functionals.
  Evaluate its fixed 48/64 Green observations with explicit union-interval,
  integer-bit, operation and workspace preflights. Require valid finite
  channels, the registered `1e-10` resolution, relative difference at most
  1% using the 1000 N floor, and the last nested difference norm no greater
  than the preceding norm plus 10 N. Apply the 1% pairwise functional rule
  to `Q1_L2/Q2_L1`. A failed observation is not replaced by a clipped norm.

Keep the arithmetic comparator separate from the snapshot reader and the
aggregate receipt writer. Before its one exclusive write, the aggregate
receipt must bind the comparator source identity, ordered case and pair
inventories, budgets and tolerances, source and prolongation hashes, every
case receipt hash, transition and gating cross-family results, explicit
predicate/status precedence, and zero factorization, solve, element-assembly
and recovery work in the cross-case phase. Add bounded synthetic tests for
passing and failing scalar, Ritz and signed-functional channels, stale
evidence, wrong prolongation, incomplete cases, and zero factorization,
solve, element-assembly and recovery calls.
Obtain independent code and mechanics review before committing the aggregate
and before any one-use scientific registration.

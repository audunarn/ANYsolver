# Saved support and local virtual-work checks

This component admits owned saved observations against the existing exact
classical local recovery. It performs no equilibrium solve or norm evaluation.
A component PASSED is neither full saved-recovery acceptance nor physical
qualification. Density/atom/band admission is a separate mandatory component.

`SavedWork` fixes Qp, exact station cuts and lift-family identity. Its finite
float64 arrays own immutable bytes: caller mutation and re-enabling array
writeability cannot alter them. The verifier snapshots the record before
evaluation, recovers q/eta, and calls the independently checked supplemental
support recovery. That helper rebinds its accepted input separately; both
recovery evaluations are counted. No history is replayed or equilibrium solved.

The six saved lift coefficient charts must exactly match the binary64 rounding
of the corresponding exact lift definition. This is a definition snapshot,
not a tolerance on computed displacements. Saved shell/interface work and both
edge routes are enclosed against their exact counterparts. Two-route agreement,
both saved first-free-coordinate residuals, both actual shifted-lift residuals
and their identities are separate checks. Matching saved nonzero residuals do
not waive the required zero-residual check. Work/reaction checks use the held
F0 scale and existing 1e-8 limit.

Both nominal and actual force/moment balances remain gates. The physical
moment defect and represented gamma identity are separate, and the predicted
defect is retained without being subtracted from physical acceptance. The
actual-minus-nominal load differences remain raw exact Actions.

## Complete local virtual inventory

For ni intervals, use the full continuous piecewise polynomial space of degree
d=p+2, with p in {1,2,3}. In deterministic channel order, emit all ni+1 vertex
hats, then each interval's d-1 bubbles
`tau*(1-tau)*P_k(2*tau-1)`, k=0..d-2. Both endpoint hats are included.
There are ni*d+1 tests per channel and 3*(ni*d+1) tests overall. Rows are
local exact tau polynomials with six coefficients; only one complete chart is
constructed at a time. Amplitudes are U0, U0 and U0/ell, applied once.

This is an explicitly new local inventory spanning the admitted trace space.
The earlier global reference used degrees 0..n+2; this does not rename a
smaller fixed list as that global inventory. No scientific registration is
made by implementing the local basis.

For every test, retain/bind the four signed terms in order:

1. Interface density and both endpoint atoms, `<mu,w>`.
2. Beam internal virtual work.
3. Applied load virtual work (subtracted in the defect).
4. Root constraint term `eta.w(0)`.

The defect is term1+term2-term3+term4. Compare all four saved terms and the
saved defect to certified Action enclosures. Independently require the
actual defect to vanish. All use E0 normalization and the existing 1e-10
limit. Work identities do not establish stationarity or multiplier stability.

## Bounds and results

Preflight the full test/comparison inventory before recovery. The aggregate
envelope includes each declared Action operation/bit maximum; runtime totals
are checked as well. Workspace includes saved snapshots, streamed test charts,
retained comparison intervals and the declared nested recovery/support/Action
workspaces. These are conservative caller-budget estimates, not measured RSS.

Missing/malformed inputs and resource violations raise explicit validation
errors. Valid numerical comparisons aggregate with FAILED preceding unresolved
HOLD, and PASSED only if all comparisons and chart parity pass. The result
hash binds the owned saved arrays to exact grid cuts, degree, numbering and
recovered q/eta. Mutable report dictionaries are observations, never reusable
acceptance tokens. Full norm/saved-archive orchestration remains mandatory.

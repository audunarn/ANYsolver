# Independent review: elementary diagnosis, not qualification

Subject `096ec0f00afa4c5eaaecdb4dedc8982f450aee84`, tree
`82f1b11c4ea245c77f89b7e991d4d423ff6f9c6a`.
Reviewer `/root/g3b_independent_review` inspected the actual diagnostic source,
frozen elementary-evaluation source, source-diff extent, bound lease identity,
terminal process record and emitted scalar/identity records. No independent
mechanics rerun or production/source edit was performed.

The source change is diagnostic only: new elementary test, explanatory document
and one runner selection. The diagnostic deliberately reports discrepancies
instead of asserting a qualification pass. It directly calls the unchanged
shared Jet evaluator, and compares value/gradient/Hessian with an independently
authored 90-digit Decimal series, differentiating term-by-term. Forty- and
sixty-term rounded results agree throughout its small-angle grid. The recurrence
and factorial coefficients are correct. The analytic Log(Exp(v)) identity adds
a distinct, non-finite-difference cross-check.

Actual author evidence confirms severe cancellation:

- Log at c=0.9999999: second derivative -1498.359375 versus
  0.266666700952384; first derivative -0.33343326952308416 versus
  -0.3333333600000017.
- Exp cosc at x=1e-8: second derivative -52441378 versus
  0.0027777777762896826; first derivative 0.22054021805524826 versus
  -0.04166666663888889.
- Exp sinc at x=1e-8: second derivative 2 versus 0.016666666654761905.

These are actual source/Jet outputs, distinct from the standalone illustrative
scalar calculations in `G3C_SO3_ELEMENTARY_CANCELLATION_ASSESSMENT.md`.
The mathematical formulas are correct; the binary64 value/derivative evaluation
outside the short series branches is unstable. This supports a numerics defect
diagnosis, but it does not prove that every assembled mismatch has that cause.

The elementary lane completed one nonclassifying node (2.99 seconds pytest),
14.615772500023013 seconds bounded child, 141701120 bytes peak, exit zero, zero
remaining processes. It is not counted together with the component diagnostic,
smoke or failed eighteen-node development lane. Raw directory:
`C:/Users/AudunArnesenNyhus/AppData/Local/Temp/anysolver-g3c-owner-development-b8gsht99`.
Exact lease/process/stdout hashes are in the canonical review. The earlier
2.767173042642239e-7 directional failure remains a failed gate.

## Required next boundary

Freeze a private numerical successor before replacement. Preserve the existing
shared module, retained public mechanics, source contracts, failed evidence and
all thresholds. The current accepted mixed-owner contract binds the old source
and cannot silently authorize a different evaluator hash.

Use an explicit, inspectable private dependency graph: stable scalar/Jet
evaluation and the precise native/local/joint/chart callers that use it, with
static tests that no qualifying private route falls back to the old evaluator
and no public/retained route is redirected. Avoid process-wide monkeypatching,
implicit dynamic code cloning, or rebinding a shared module in qualifying runs.
If unchanged retained source operators are copied into a private namespace,
bind their original blobs and mechanically audit that differences are limited
to authorized imports/evaluation plumbing; preserve the actual local operators,
state schemas and formulation equations.

Require independently bounded series/remainder choices, scalar and full Jet
oracles, both sides of branch switches, same chart-domain guards, then the
component diagnostics and full bridge directional gate at every original step.
Do not select a new series interval solely because it makes this fixture pass.
No tolerance, potential, interpolation, section, quadrature, physical recovery,
public alias or default change is part of this numerical successor.

Acceptance here concerns the accuracy and honesty of diagnosis. Source repair,
new authority, bridge implementation acceptance and full G3c confirmation remain
separate gates. Conventional Q4 finite recovery and B2 clamp-domain recovery
also remain open.

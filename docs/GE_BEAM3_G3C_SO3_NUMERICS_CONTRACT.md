# Private G3c SO(3) numerical evaluator, version 1

Base: 02b9a4ac4dad65a4a9daf12ed9d3f4fc079e316f, tree
c490dc567955e02a161131b48e6c8c043e9ddca8. This two-path contract plus canonical
JSON freezes an isolated numerical kernel and bounded tests, not new mechanics.
Independent accepted design review is required before implementation. Preserve
all inherited files, failed evidence and the accepted diagnostic review. No
existing caller is redirected; graph integration needs a separate exact source
graph/review after this kernel passes. No graph qualification follows here.

## Functions and mathematical invariants

Private module `_ge_beam3_g3c_so3_numerics.py` may import the unchanged Jet2,
unary, sin, sqrt and matrix/arithmetic helpers from the bound shared module.
It must not call its Exp/Log coefficient or rotation entrypoints. Define private
coefficient evaluation and so3_exp/so3_log with the same mathematical maps.
No monkeypatch, global rebinding, dynamic cloning or production import change.
No strain, potential, interpolation, quadrature, material, recovery, alias,
state schema, physical chart limit or existing tolerance changes.

For x=theta squared, A(x)=sin(sqrt(x))/sqrt(x),
B(x)=(1-cos(sqrt(x)))/x with analytic limits at zero.
For 0<=x<=1, degree-16 polynomials have coefficients
(-1)^n/(2n+1)! and (-1)^n/(2n+2)!, n=0..16. Evaluate each polynomial and
both derivatives together by differentiated Horner recursion, then apply the
unchanged Jet chain rule. For x>1 use sin(t)/t and 2*(sin(t/2)/t)^2, t=sqrt(x),
with the unchanged analytic scalar Jet operations. This half-angle expression
avoids subtracting nearly equal cosine/one values. Reject nonfinite/negative
coefficient arguments; actual squared rotation norms are nonnegative.

For F(c)=acos(c)/sqrt(1-c*c), delta=1-c,
a_0=1 and a_n=n*a_(n-1)/(2n+1). On delta<=1/2 use degree 40 and consistent
first/second polynomial derivatives, with first-derivative sign reversed for c.
For c<1/2 use the analytic closed value/derivatives with
s=sqrt((1-c)*(1+c)), angle=acos(c):
F=angle/s, F'=-1/s^2+angle*c/s^3,
F''=-3*c/s^4+angle/s^3+3*angle*c*c/s^5.
Keep the original strict c>cos(0.9*pi) guard. Finite c slightly above 1 from
proper-matrix roundoff follows the analytic continuation series as before;
this is not permission to admit nonphysical matrices to a graph.

so3_exp constructs I+A*hat(v)+B*hat(v)^2. so3_log multiplies the axial
antisymmetric part by F((trace(Q)-1)/2). Reuse existing immutable Jet algebra
without copying or altering its class identity. No finite-difference derivative
is used in the kernel. Full Jet gradient/Hessian validation is mandatory.

## A priori numerical choice

For delta in [0,1/2], a_n<=2^-n, so the omitted second derivative after degree
40 is bounded by 4*sum(n*(n-1)*4^-n,n>=41)<3e-21; value/first tails are smaller.
For x in [0,1], Exp's omitted second tail is bounded by the absolute factorial
series sum(n*(n-1)/(2n+1)!,n>=17)<1e-35; B is smaller. The numerical switches
and degrees come from these interval bounds, not a graph-fit experiment.

Binary64 Horner/recurrence rounding has at most a few hundred scalar operations,
with bounded absolute coefficient sums and no large intermediate terms in the
series regions. A conservative 1e-13 normalized engineering bound remains below
the unchanged 1e-11 invariant gate. Tests recompute tail bounds in high precision
and compare coefficient values/derivatives and full Jets independently.
For closed Log, c in [0,1/2] has s>=sqrt(3)/2, limiting cancellation; for c<0,
the first/second derivative terms have consistent signs. This avoids the
catastrophic near-one subtraction shown in the preserved incident. For closed
Exp x>1 there is no division by a vanishing argument. This is an error-analysis
basis plus executable accuracy gates, not a claim of correctly rounded libm.

## Independent oracle and frozen tests

The separate reviewer authors a Decimal oracle without importing any anysolver
module. It uses independently differentiated series/analytic arithmetic and
high-precision multivariate chain rules. Bind its actual bytes in the clean
implementation lease before tests. No copying production derivative outputs
into expected values. Compare rounded references at two precisions/series
lengths where appropriate and reject unconverged reference values.

Separate inventories: static isolation/authority; scalar accuracy/bounds;
full-Jet SO(3) accuracy/domain. Concrete pytest nodes are frozen before execution.
Cover zero, signed zero, minimum positive subnormal, logarithmic small arguments,
old and new switch values and immediate binary64 neighbours, the complete
relative chart interval, non-axis-aligned seeds, near-limit rejection, and
common rotation magnitudes pi and 1.4*pi. Exp scalar coverage extends through
(2*pi)^2; graph admission itself is not broadened. Use normalized 1e-11 for
coefficient and Jet invariants. Retain every historical directional threshold
and step; no assembled directional test is run by this isolated kernel gate.

Assert all existing files unchanged from the base, module imports cannot route
back to old unstable coefficient/Exp/Log functions, no existing importers target
the new module, canonical JSON rejects duplicate/nonfinite/alternate bytes,
and bindings reject mutation. Re-run the same frozen kernel suite independently
only after the author suite passes. Keep inventories separate from old graph
tests. A failed candidate is preserved and corrected, not retried unchanged.

## Execution, evidence and authority boundary

One isolated Windows child under the existing frozen environment capsule:
600 seconds, 24 GiB/tree, one numerical thread, 120 seconds without CPU/output
progress, exclusive external diagnostics, no retry. Existing limits of at most
three workers and 1800 seconds per wave remain. Validate clean commit/tree,
contract/review/source/environment hashes before NumPy imports and at exit.
Retain stdout/stderr and terminal process/lease with byte hashes. No shared
resource ledger or request is introduced in normal-token mode.

Terminal order: BLOCKED_G3C_SO3_NUMERICS_AUTHORITY_OR_PROCESS,
NO_GO_G3C_SO3_NUMERICS_ACCURACY, then
PROVISIONAL_GO_G3C_SO3_PRIVATE_KERNEL_ONLY. The latter permits preparing the
separately reviewed dependency graph; it is not mixed-owner acceptance, public
replacement, recovery completion, full G3c, release or default authority.

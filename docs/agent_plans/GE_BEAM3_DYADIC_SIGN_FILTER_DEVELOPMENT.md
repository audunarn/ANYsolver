# Outward-dyadic shifted-inertia filter

Parent `7dc6dc9337c07deb66c85b1fcea0ba75c94a868a` preserves the six-macro
loaded-spectrum refinement. This successor changes arithmetic only, retaining
all mechanics, section laws, mass, recovery, root widths, residual checks,
coordinate defaults, deadlines and historical evidence.

## Inclusion invariant

At precision p, each entry is enclosed by integer endpoints [lo,hi]/2^p.
The initial H-shift*M is constructed directly from exact integer ratios of
its binary64 inputs, never from rounded subtraction. Products take all four
endpoint products and round the lower endpoint down and upper endpoint up.
Division uses all four endpoint ratios, only when zero is excluded from the
denominator. Python integer floor division and its negated-ceiling counterpart
provide outward rounding for either denominator sign.

At each symmetric elimination step, the interval matrix encloses the exact
remaining Schur complement. Choose a diagonal whose complete interval has one
strict sign. Its sign is exact. Divide column entries by that pivot enclosure,
multiply outward, and subtract outward from the remaining symmetric block.
Dependency overestimation may make a later pivot inconclusive but cannot
justify a wrong sign. An identically [0,0] remainder proves its full nullity;
otherwise a remainder with no provably signed pivot returns unresolved.

Try p=256 then p=512. If either enclosure resolves every pivot, its inertia
is that of the exactly represented shifted pencil by symmetric congruence.
Otherwise use the retained integer Bareiss implementation. No sign or zero is
guessed; no tolerance or floating-point sign test is introduced by this filter.
The total exact-sign call retains its 30-second bound across both filters and
fallback, with cancellation/expiry checks in every elimination row.
This is not certification of the continuum or pre-rounded mechanical operator.

## Tests and bounded evidence

Initial combined arithmetic/allocation tests: 73 passed in 2.90 seconds.
Independent Fraction endpoint tests cover negative denominators and outward
rounding; rational Schur tests cover indefinite shifted pencils. Subnormals,
hyperbolic blocks, singular matrices, exact cancellation and unresolved
fallback are explicit. These are same-author tests, not independent review.

Measure the same preserved 69-coordinate pencil from six-macro native-1:
434444 bytes, SHA-256 613e1170278556a5c4f07348c5fc1cff5a6433c8672bbf25ddc3fad00ed82277.
Use its saved sixth-root lower bracket, one warm-up plus eleven alternating
pairs of integer Bareiss and filtered exact inertia. Every answer must agree.
Use the existing 180-second/24-GiB/one-thread external benchmark containment.

After successful measurement, run the unchanged six-macro two-state spectral
diagnostic once in a fresh v2 directory under its original time/memory bounds.
Require all ten raw artifacts and backend-neutral scientific rows to match
the preserved v1 result byte-for-byte. Revision metadata may differ. Do not
rerun any nonlinear or continuum equilibrium solve. Only a separately frozen
successor can later admit twelve-macro allocations. No qualification, default,
package or publication authority follows from this arithmetic development.

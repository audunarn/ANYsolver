# P5 curved continuum-reference development — 2026-09-05

Author research successor to `9a08540f24b7cbc5a529624a6f672281eb14d983`.
Earlier implementations, failures, P3/P4 evidence and authorities are unchanged.
This record is not a frozen scientific aggregate, independent review or
qualification authority. No formal resource request or qualification run was
created or consumed.

## Reference problem and separation

The reference is a linear, initially stress-free parabolic cantilever:
`r(t)=(t,h*(1-t*t),0)`, `-1<=t<=1`, with its left endpoint clamped.
The material triad is `(unit tangent, global z, tangent cross global z)`.
The fixed positive-definite 6x6 section uses the existing axial/shear/torsion/
bending ordering, including full coupling. Six tip forces/couples are allowed.

The standalone analytical module imports only `decimal` and `math`. It does
not import the producer, P4 reference frames, NumPy, metrics or quadrature.
Continuum equilibrium gives spatial force `f` and moment
`c+(r_tip-r(t)) cross f`. If B maps these six tip loads to material resultants,
continuum tip compliance is the complementary-work integral `B^T C^-1 B ds`.
This supplies tip displacement and spatial infinitesimal rotation directly,
without a sampled finite-element solution or a fit to the discrete response.

The polynomial/radical integrals are evaluated at 80 Decimal digits. For
`a=2h`, even inverse-Jacobian moments satisfy
`I0=2*asinh(a)/a` and `n*a^2*In=2*sqrt(1+a^2)-(n-1)*I(n-2)`.
For `a<=0.5`, a bounded convergent binomial series avoids cancellation in the
upward recurrence near the straight limit. The series has a 256-term bound
and raises on exhaustion; this is numerical evaluation of the same integral,
not a mechanics or quadrature-policy change. Inputs are binary64 values
converted exactly before Decimal evaluation. Caller precision/rounding does
not affect the result. This is high-precision evaluation, not exact symbolic
proof or an interval enclosure.

Straight diagonal sections are checked against closed Timoshenko cantilever
formulas. A separately coded 96-point continuum quadrature, with direct
analytic frames and cross products, checks heights 0, 1e-100, 1e-8, 0.25,
0.25000001, 0.4 and 0.75 for four sections. Normalized agreement is checked at
1e-11. Both implementations have the same author: neither independent
authorship nor adaptive multiprecision quadrature authority is claimed.

## Discrete comparison

The separate discrete probe partitions the same parabola into 1, 2, 4 or 8
three-node macro elements. It uses the existing discrete half-cell flexibility
without changing it. Known tip loads determine cell force/moment by equilibrium;
adding complementary work gives a 6x6 tip compliance without a large assembled
solve. Shared reference nodes and frames must agree exactly. Existing one- and
two-element assembled solves separately confirm this work-based calculation.

This path does not enlarge the existing chain solver's one/two-element limit.
At most 16 half-cell flexibility calculations occur in one comparison.

At height 0.4 the sampled normalized Frobenius tip-compliance errors are:

| Section | 1 macro | 2 macros | 4 macros | 8 macros | Last refinement order |
|---|---:|---:|---:|---:|---:|
| diag(1,1,1,1,2,3) | 0.0384369 | 0.00992548 | 0.00250480 | 0.000627697 | 1.99656 |
| diag(1e12,1e12,1e12,1,2,3) | 0.0623289 | 0.0160571 | 0.00404944 | 0.00101461 | 1.99680 |
| Existing complete coupled section | 0.0642947 | 0.0168026 | 0.00425538 | 0.00106738 | 1.99521 |
| Complete coupled section scaled by diag(1e6,1e6,1e6,1,1,1) on both sides | 0.0619610 | 0.0160477 | 0.00405428 | 0.00101629 | 1.99613 |

All six individual unit-tip-load response errors are checked, as is the largest
absolute generalized eigenvalue of the compliance error relative to continuum
compliance. This measures worst relative complementary work across combined
tip loads, avoiding domination by the most compliant direction. At eight macros
these worst relative work errors are respectively 0.00158187, 0.00858333,
0.00236761 and 0.00898423. All are below the existing 2% engineering comparison
level for these samples. No domain-wide, finite-state or slenderness-envelope
claim follows; stiffness contrast alone is not a full physical slenderness test.

## Validation and preserved boundaries

- New focused suite: 18 passed in 1.99 seconds.
- Existing nine P5 research suites: 139 passed in 10.89 seconds.
- Tests cover closed straight formulas, direct continuum quadrature, complete
  coupled sections, near-straight numerical stability, convergence, six load
  columns, worst relative work, assembled-solve agreement, deterministic
  repetition, context isolation, invalid inputs and a force/moment map mutation.
- Analytical reference SHA-256:
  `45320782A9F95C85F1EEDDDC7B2E113C48D191FEAA7A764BBF2041DE0A60477A`.
- Discrete probe SHA-256:
  `D4E0B0C25AF869FFBF950090D9E9135C4DCA1298E2FDEC4959CD0A0D0621030F`.
- Test SHA-256:
  `A2CF8109AA970D86A15EF6C13873C9F4FF02203DC57A16B70ACD456165FBF29B`.

Only these research modules, their test and this record were added. No source,
package, workflow, dependency, alias, default, B2/B3/Q4/S3 mechanics, production
recovery or accepted evidence was changed. No release, merge or activation.

## Next unresolved work

This adds a physical continuum convergence check beyond the earlier shared-
metric algebra comparisons. It does not fix the extreme finite coupled local
equilibrium/cutback failure or transfer retained precision into production
state/restart. Reference mass/modal behaviour is a next bounded development
step, alongside resolving that finite-state failure before formal rehearsal.
Independent source/equation reconstruction, nonlinear section transactions and
histories, postbuckling, modal/prestress/buckling, package/solver integration and
objective beam-shell joints remain incomplete. P5 is not frozen or qualified.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

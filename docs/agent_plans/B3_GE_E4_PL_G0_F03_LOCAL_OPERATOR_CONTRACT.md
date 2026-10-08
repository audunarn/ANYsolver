# F03: bounded local-reference operator contract

This contract implements the operator-proof portion of the independently
reviewed `B3_GE_E4_PL_G0_F03_LOCAL_REFERENCE_DESIGN_DRAFT.md`. It is confined
to the classical in-plane finite-pad reference. It does not select a native
attachment, authorize another scientific execution, resolve the existing
physical convergence hold, or permit G1 entry.

The source contract `_b3_e4_f03_spatial_contract.py` continues to define
represented geometry and material constants. Its original binary64
expressions are evaluated first and lifted to exact fractions. In particular,
the held pad inertia `J` differs slightly from the exact geometric moment;
the rigid yaw factor remains `gamma=J_geom/J`. No correction sets it to one.

## 1. Space, numbering and immutable inputs

The bounded implementation uses shared tensor-product rectangular Qp cells,
`p=1,2,3`, with Lagrange nodes `j/p` on each axis. Polynomial degree one is
included for independent patches and counterexamples, not assumed adequate
for a scientific candidate. No hanging node, curved cell, inclined edge or
native Q4/S3 element is admitted by this helper.

The panel is `[-1/2,3/2] × [-1/2,1/2]`. Each axis is a strictly increasing
exact-Fraction partition spanning its panel bounds. Cell, scalar-node and
local scalar-basis order is y then x. Displacement DOFs are component-major:
all `u_x`, then all `u_y`. Shared coordinates on a partition edge have one
global node. Both displacement components vanish on both x edges. A local
free gather uses `-1` only for those prescribed-zero coordinates.

The compilation factory copies caller cuts, creates immutable tuples and
bytes-backed read-only index arrays, and returns a definition-specific grid.
Ordinary direct construction and `dataclasses.replace` fail explicitly;
only the validated factory initializes a grid. Cut inputs must be bounded
lists or tuples: an arbitrary iterable is rejected before consumption.
Geometry, station coordinates and exact evaluation coordinates have a
256-bit bound on each fraction numerator and denominator. These bounds
include the represented-binary64 fixture and the declared synthetic splits.
Derived shared nodes and station events are checked as they are generated;
an input whose derived coordinates exceed the bound fails compilation.

The current topology limits are 257 cuts per axis, 100,000 scalar nodes,
4,096 station intervals and an explicit cumulative trace-incidence budget
(default 1,000,000 entries). These are research safety bounds, not delivered
product limits or a practical-scale qualification. A numerical candidate
must fit the tighter downstream norm and run limits as well.

## 2. Exact cell shell and pad operators

The local membrane uses engineering strain `(u_x,x, u_y,y,
u_x,y+u_y,x)` and the held plane-stress matrix. It is an independent classical
operator; it imports no native element or solver assembly.

For one-dimensional shape functions `L_i` on `[0,1]`, form exact Gram
matrices `M_ik=integral L_i L_k`, `D_ik=integral L'_i L'_k`, and
`B_ik=integral L'_i L_k`. Tensor products with the physical widths produce
the full local stiffness, including both cross-component blocks. The
implementation performs exact integration, then converts each entry to a
fresh finite binary64 array. It does not average a matrix with its transpose.
Exact rigid null vectors, affine energy and physical first/second derivatives
are checked separately from an independently written Gauss integration.

For every cell and each of the four fixed rectangular pads, intersect the
cell with the translated pad at station `s`. With scalar basis `phi(x)psi(y)`,
the contributing moments are

```
I0(s) = integral phi(x) dx
I1(s) = integral (x-s) phi(x) dx
Y0    = integral psi(y) dy
Y1    = integral y psi(y) dy

A_tx,ux    = I0 Y0 / S
A_ty,uy    = I0 Y0 / S
A_yaw,ux   = -I0 Y1 / (J S)
A_yaw,uy   = I1 Y0 / (J S)
```

Limits are exact cell/pad overlaps. The y integration is fixed. The x
integration limits are affine in `s` between consecutive events. Exact
polynomial antiderivatives produce these entries without sampling a native
beam or shell element.

The station partition is the exact union of `0`, `1`, and all interior
`cell_x_edge - pad_x_edge` values. Deduplicate only equal rational numbers.
Every positive interval is retained even if its endpoints round to the same
binary64 number. Local polynomials use `tau=(s-a)/(b-a)` in `[0,1]`.
Differentiate and divide by the exact width **before** coefficient conversion.
Reject an unrepresentable floating response; never delete its interval.

Each local trace has three rows and `2(p+1)^2` columns, with `p+3` exact
coefficients per entry. That size includes the yaw degree `p+2`. Direct
construction validates and tuple-copies the complete layout. Returned
floating evaluations own their arrays. Trace coefficients have an
8,192-bit numerator/denominator bound and a 2,000,000-bit aggregate bound.

## 3. Assembled kinematic proof and the root

Assembly sums local moments through shared gathers. Complete assembled
operator rows, rather than only one rigid displacement field, must have
identical left/right limits for pose and its first physical derivative at
every event. A second derivative may jump. Continuity of the first
derivative is why no new internal beam force atom is inserted at a cell or
station boundary.

There are exactly three root equations, `Au(0)=0`. The root transverse slope
is independently free. Exact rational elimination checks root row rank 3
and rank 4 after adding the transverse-slope row on the bounded shared-grid
fixture. A deliberately too-coarse Q1 grid has root rank 3 but augmented
rank 3, demonstrating that root rank alone is insufficient. Such a space is
inadmissible for the intended scientific approximation.

These finite-dimensional checks do not establish uniform stability or
physical convergence of an arbitrary grid. The smallest member of a future
registered candidate family must pass its own admission checks.

## 4. Full piecewise interface functional

The physical functional contains three density channels, a held-frequency
cosine load term and precisely two endpoint atoms. The density on each
positive interval is represented by six ascending local-`tau` coefficients
per channel (degree at most 5), matching the maximum Q3 trace requirement.
The common cosine frequency is the held binary64 `2*pi`, converted exactly.

Keep the complete mechanical bookkeeping from the reviewed design:

```
density   = (N', Q'+q_load, M'+Q)
root atom = (N(0), Q(0), M(0)) - eta
tip atom  = -(N(1), Q(1), M(1))
```

The total beam-root reaction is `-eta`, not the root atom alone. Partition
edges do not create atoms. Moment channels are intrinsic physical moments;
the norm does not add a lever-arm term `s*F_y`. Sharp-band physical wrenches
remain separate observables with their own common-origin convention.

The functional constructor owns all nested tuples. Input limits are 2,048
intervals and 4,096 numerator/denominator bits per fraction. Exact difference
uses the union partition (at most 4,095 intervals), exact affine polynomial
restriction, and subtraction of coefficients, cosine amplitudes and both
atoms before numerical evaluation. Derived fractions have an explicit
8,192-bit limit and a 32,000,000-bit cumulative bound. A bounds failure is
reported, not repaired by deleting cuts or dropping terms.
Validate union cuts and endpoint/cosine terms first, then each derived
interval and the running cumulative count before retaining that interval.
Polynomial restriction holds only a bounded pair of 3-by-6 interval blocks
transiently; it must not first build an oversized full output.

## 5. Two independent Green calculations

The unchanged full-H1 dual kernel on `[0,1]` is

```
G(s,t) = cosh(min(s,t)) cosh(1-max(s,t)) / sinh(1).
```

Before either calculation, divide each moment operand by the held length
`ell=Fraction.from_float(.46)` exactly once. Force operands remain unchanged.

The binary64 implementation uses fixed Gauss orders 48 and 64. Within an
interval, it integrates both triangles with `s=a+delta*u`,
`t=a+delta*u*v`, Jacobian `delta^2*u`. Between intervals, it accumulates
the factored moments `P_i=integral f cosh(s)` and
`Q_i=integral f cosh(1-s)` using compensated prefix sums. The off-diagonal
squared-form term is `2 sum_i Q_i sum_(j<i) P_j / sinh(1)`.

It includes density/atom cross terms and the exact endpoint Green matrix
`[[cosh(1),1],[1,cosh(1)]]/sinh(1)`. Local hyperbolic and trigonometric
addition formulas preserve the positive interval measure when rounded
global endpoints coincide. Unrepresentable widths fail explicitly. Every
active weighted Duffy Jacobian must be a finite **normal** binary64 number
(at least `numpy.finfo(float).tiny`). Checking only `delta^2 > 0` is
insufficient: quadrature weights can underflow while unrelated contributions
make two orders appear resolved. A subnormal or zero active weight is an
explicit numerical-admission failure, with no adaptive rule or rescaling
fallback. This restriction does not relax any physical acceptance limit.

Return diagonal, off-diagonal, atom-cross and atom-Gram contributions by
channel, absolute-contribution totals, cancellation measures and both-order
results. Reject nonfinite or negative squared norms. Never clip a negative
result to zero. Recognize exact zero from the complete exact representation.
Compute a difference norm directly, without subtracting two large norms.
The absolute-contribution and cancellation metadata are based on completed
interval diagonal/off-diagonal contributions and aggregate atom terms,
with the `1000^2` normalization floor. They do not expose every quadrature
term's cancellation and are not condition numbers or arithmetic error bounds.

For each channel and their sum, require

```
abs(Q64-Q48) / max(abs(Q64),abs(Q48),1000^2) <= 1e-10.
```

The order-64 value is usable only after that check passes. This is a
numerical resolution check, not a proof of small discretization error.

The independently implemented Decimal oracle validates the same physical
mapping but shares neither norm code nor quadrature nodes. It generates
Gauss orders 16 and 24 using 70-digit Decimal arithmetic, half-even rounding,
and a fixed context. It directly integrates every interval pair and the
diagonal triangles, with no prefix algorithm. It accepts at most eight
input intervals, fifteen union intervals and 4,096-bit input fractions.
Signed cross terms and raw results remain visible. It is a synthetic
numerical oracle, not an interval certificate or replacement run adjudicator.

Analytical checks cover constant densities, endpoint Green values, moment
scaling and manufactured C1 piecewise Riesz fields. Cross-method checks must
also cover degree-five densities, both atoms, cosine forcing, differing
partitions, cancellation and distinct intervals with identical rounded
endpoints. The independent oracle must be checked by someone other than its
sole implementer before this operator contract is accepted.

## 6. Honest storage and work boundaries

A physical footprint can touch more cells and unknowns as a mesh is refined.
Its integrated beam energy can couple all active trace coordinates on an
interval. Therefore the topology preflight counts conservative active-DOF
cliques, their union with shell incidence, and the three root constraint rows.
It does not claim linear storage merely because a sparse container is used.

The current bounded symbolic implementation uses row bitsets. Before those
arrays are allocated it checks a conservative CPython storage envelope
against an explicit graph budget, using integer digit and pointer sizes
without constructing the prospective lists or masks. This research diagnostic can itself have
quadratic bit storage; it is not the required scalable native assembler.
It reports scalar node/DOF counts, station intervals, active trace sizes,
shell/beam/primal/KKT nnz envelopes and a conservative dense L/U storage
ceiling. The latter is a ceiling, not measured fill or a factorization.

A numerical registration must additionally bound exact moment preparation,
local dense blocks, aggregate assembly storage, sparse solver workspace,
factor fill, wall time and process RSS. Actual numerical nonzeros and peak
memory must be measured. A preflight budget failure does not authorize a
smaller replacement scientific case or an execution retry.

## 7. Still required before a numerical reference execution

The following remain explicit work; this document does not close them:

- Select and freeze a conforming nested grid/degree family, its physical
  convergence inventory and exact prolongation. The existing physical
  settling criteria, 45 scalar observables and full-functional tests remain.
- Implement the eliminated primal shell-plus-trace beam bilinear form,
  the load functional and the three-root KKT problem. Freeze integration,
  scaling, conditioning and failure criteria before solving a candidate.
- Verify exact work conjugacy, support reaction lifts, stress-jump signs,
  free-boundary terms and endpoint atom bookkeeping on manufactured fields.
- Establish conservative numerical assembly/factorization bounds and
  candidate-specific preflight, with independent raw-output adjudication.
- Independently review the complete protocol, freeze source/runner/case
  identities, and register fresh single-use execution authority.

Old failed or consumed executions and their acceptance limits remain
unchanged. Passing these operator tests is useful implementation evidence;
it is not an external comparison, settled classical reference, native
attachment qualification, or completed G0B.

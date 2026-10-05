# C2 development ingredient: curved B3 pair projection

`beam_curve_pair.py` provides the local distance work map for one quadratic
classical B3 source station against one quadratic B3 target centreline. It is
an internal prerequisite, not an admitted B3/B3 contact analysis.

With the B3 Lagrange curve (y(t)=y_0+bt+ct^2) and source point (x(s)), the
closest target candidates are both physical endpoints and every real root in
([0,1]) of

\[
(x-y_0)\cdot b + [2(x-y_0)\cdot c-b\cdot b]t
-3(b\cdot c)t^2-2(c\cdot c)t^3=0.
\]

The minimum-distance result exposes every equal global minimizer. A work-map
request at a competing branch fails explicitly; no arbitrary root is used.
At a unique smooth interior minimum, the nodal gap gradient is (J^T n).
The Hessian applies the projection Schur complement

\[
H=J^T(I-nn^T)J/r-r_{qt}r_{tt}^{-1}r_{tq},
\]

including the target curve's second derivative in (r_{tt}). At a strict
physical endpoint, the derivative uses that fixed endpoint branch.
The same local result can be laid out in either body's global coordinate
order for a symmetric pair potential.

The focused checks use independent line projection, a symmetric two-minimum
arch, exact endpoints, smooth-branch finite differences, Hessian symmetry,
translation/rotation work invariance and coordinate-order permutation.
`c2-b3-pair-projection-final1.txt` records 3 passing tests. The first run's
role-exchange equality assertion failed because a directional closest-point
query need not give the same minimum after reversing its source station;
that test defect is retained in `c2-b3-pair-projection-local1.txt`.

The next slice must integrate the half-weighted two-direction line potential,
partition/contact-certify active and projection branches, assemble both beam
residual/tangent blocks, certify physical/swept gap and route transactions and
restart through a dedicated B3/B3 profile. These local checks cannot claim
line-contact completeness, endpoint ownership or C2 acceptance.

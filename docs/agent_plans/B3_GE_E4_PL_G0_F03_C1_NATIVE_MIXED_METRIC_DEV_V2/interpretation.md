# Bounded native retained mixed metric: development interpretation

The saved `result.json` is a fixed C1 Q4 x8/y4, native B3-12, m4-to-m8
comparison at the 35 mm thickness. The original E4 trial tangent, complete
retained B3 tangent and six-channel C1 rows form the supported KKT matrix.
Nothing in the auxiliary Riesz metric is added to that matrix. The 1,404
supported primal coordinates include 1,188 shell coordinates and 216 native
beam coordinates (72 free nodal, 36 retained half-cell rotations, 108 retained
resultants). The native resultant block uses the exact positive complementary
Hessian `-K_pp`; it is not interpreted as 18 pointwise resultant samples.

For each family, the row counts remain full after work-norm scaling:

| Family | m4 rows | m4 beta | m8 rows | m8 beta |
| --- | ---: | ---: | ---: | ---: |
| P0 | 24 | 0.00187656 | 48 | 0.00187923 |
| continuous P1 | 30 | 0.00187669 | 54 | 0.00188061 |
| dual P1 | 30 | 0.00187673 | 54 | 0.00188068 |

Here `beta` is the smallest singular value of
`R^(-1/2) [[K,C^T],[C,0]] R^(-1/2)`. It is dimensionless only with the stated
energy-valued primal and dual Riesz metrics. The multiplier metric reconstructs
the physical action density by dividing each integrated row dual by its basis
integral, converts moment density using the fixed 0.1 m length, applies the
family's analytic Neumann H^(-1/2) Gram, and divides by `E*t` to obtain joules.
The B3 nodal H1 field is an auxiliary coordinate norm, not a substituted
physical bottom-surface trace. The E4 drilling chart term is an H1 coordinate
norm scaled by the physical plate bending rigidity; it is not physical
drilling stiffness or a change to the actual tangent.

**The minimum singular value does not distinguish line-space growth.** All six
weakest vectors have about 99.93% of their Riesz norm in the E4 drilling chart
term. The line-dual share is below 0.0051%; the shell physical share is below
0.065%. These modes therefore probe the existing numerical drilling completion,
whose physical norm is not established, rather than the prospective weak line
mode. The slight beta increases cannot select a multiplier or refute the
separate positive broken-trace P0 quotient decline. No new norm coefficient or
projected spectrum is introduced to hide this result. A physical treatment of
the full E4 drilling coordinate and independent norm review are dependencies
before this metric can support a native KKT stability claim.

Numerical checks: every KKT has at most 1,458 rows, the supported Riesz metric
and native complementary block pass Cholesky checks, normalized row ranks are
24/30/48/54, the near-null Riesz norm is 1 to rounding, the scaled residual
agrees with the singular value to about `3.2e-16`, KKT relative asymmetry is
`2.93e-16`, and work transpose defects are at most `1.3e-21 J`. These are
floating point checks. The H^(-1/2) lower/upper matrices are averaged for this
metric; their tiny floating ordering defects are recorded, and the pair is not
claimed as an interval certificate.

The V1 sibling directory is an immutable failed attempt: it records an
`IndexError` in the diagnostic-only shell scaling check and produced no
metric. V2 corrected that shape error only. `manifest.json` records the
generation-time Git HEAD, exact source hashes, runtime, thread setting and
source environment. This is private G0 development evidence, not F03/G0B
acceptance. The registered beam:shell ratios, three refinements, physical
transfer/locking checks, loaded fidelity and independent review remain open.

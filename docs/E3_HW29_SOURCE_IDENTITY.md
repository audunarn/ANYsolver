# E3-P HW29 public-source identity, reopened source gate

## Result

The component `study_e3_p.hw29_linear_isotropic_identity_v1` remains
`BLOCKED_E3_P_HW29_PUBLIC_SOURCE`. The user-supplied 2011 chapter materially
closes the drilling formulation, interpolation counts, skew-coordinate
membrane fields, and quadrature. It still does not print a complete discrete
HW29 shell identity.

This is a narrower source-availability block, not a mechanics failure. Rank,
patch, condensation, material, and recovery qualification remain unexecuted.
The evidence does not support `PROVISIONAL_GO` because five indispensable
rows are still open.

## Supplied-source identities

The complete 22-page chapter was verified as:

```text
Recent Improvements in Hu-Washizu Shell Elements with Drilling Rotation
Krzysztof Wisniewski and Ewa Turska
310978 bytes
SHA-256 E6AFAADE32B33D710D3C038635FE2AD2729E32FB952C5EC6706E68A93A3B1860
```

Every page was text-inspected. The equation-bearing pages 12-17 were also
rendered and visually inspected so that extracted subscripts, signs, matrix
positions, and powers were not accepted blindly.

The complete 11-page paper was verified as:

```text
Degenerated Four Nodes Shell Element with Drilling Degree of Freedom
Fathelrahman M. Adam, Abdelrahman E. Mohamed, A. E. Hassaballa
1235559 bytes
SHA-256 B67AF5A43CB36FEC9E0D8CDAD745B391F9F5FC1861C842A249E2B982BDACD5E8
```

All pages were inspected and its formulation pages were rendered. It defines
a different degenerated shell with an absolute torsional penalty coefficient.
It is background evidence only and cannot supply missing HW29 equations.
Neither PDF, extracted text, nor rendered page is committed.

## Rows now closed by the 2011 chapter

The new source closes these mandatory rows:

- standard Q1 geometry and four nodes times six external DOFs;
- the exact `7+9+2+4+4+3=29` field-count decomposition;
- skew-coordinate construction, center transformations, and selected 7p/9p
  membrane component matrices (Eqs. 26.15-26.34);
- the three-parameter multiplier transformation and
  `T=q15+xi*q16+eta*q17` (Eqs. 26.46-26.47);
- perturbed-Lagrange `gamma=G` (Table 26.1 and the Cook test);
- the complete flat Q1 constraint polynomial, its rotation-only `xi*eta`
  term, and deletion by center linear expansion (Eq. 26.42);
- the rectangular and geometry-dependent hourglass definitions
  (Eqs. 26.43-26.45), including `alpha_HG=10^-3`;
- `2 x 2` Gauss integration for all tested elements (page 17).

The source also distinguishes HW29 from an Allman displacement enrichment:
HW29 uses the rotation constraint with local multipliers, mode deletion, and
gamma stabilization. No E2-A interpolation coefficient is introduced.

## Exact drill and hourglass certificate

For the printed flat convention

```text
c = theta + (u_,eta - v_,xi)/2
```

and bilinear modal coefficients, the independently reproduced rows are

```text
1:       theta0  + (u2-v1)/2
xi:      theta1  + u3/2
eta:     theta2  - v3/2
xi*eta:  theta3
```

The last row has no translation column. Deleting it leaves the alternating
nodal drill vector `(1,-1,1,-1)` invisible to the three multiplier moments.
Pure common drill and translation-only rigid spin give equal and opposite
constant constraints; their combined physical rigid state is exactly null.

The source-defined gamma row was reproduced exactly from

```text
gamma = [h - (h dot S1)b1 - (h dot S2)b2]/4,
h = (1,-1,1,-1).
```

For the unit square, `gamma=(1,-1,1,-1)/4`. For the frozen rational
trapezoid it is `(3/14,-3/14,2/7,-2/7)`. In both cases:

- `gamma dot 1=0`, so a constant drill/physical rigid rotation is not
  grounded;
- `gamma dot h=1`, so the residual alternating mode is energetic;
- `gamma^T gamma` has rank one;
- the normalized printed energy is exactly `10^-3 G V` on `h`.

The accepted E2-A interior bubble contains powers outside
`span{1,xi,eta,xi*eta}`, so it is outside the frozen Q1 displacement space.

## Indispensable rows still open

The 2011 chapter itself identifies the first remaining gap. It prints the 2D
EADG2 mode matrix in Eq. 26.40, but states that the transformation is modified
for shells and defers those details to reference 24. The supplied source does
not provide that shell-specific transformation.

Four additional gaps remain:

- HW29's four assumed shear-stress and four assumed shear-strain counts are
  printed, and ANS is named, but their discrete maps are absent;
- the continuum/partial functional and counts do not give the complete
  discrete HW29 functional with the shell EADG and shear insertions;
- local elimination and scheme U2 are referenced, but the actual HW29 block
  order, invertibility conditions, and condensation equations are absent;
- the complete linear load-work and physical-resultant recovery maps are not
  printed.

The generic exact Schur identity in the oracle remains explicitly marked as
independent algebra. It does not certify the missing HW29 mixed block.

## Boundary retained

The prospective first material scope remains homogeneous isotropic steel with
`G=E/[2(1+nu)]` and no new public field. The 2011 chapter now supports the
`gamma=G` specialization, but the remaining identity gaps stop the material
gate before execution.

A lawful complete 2012 paper or equivalent equation-level source may close
the five remaining rows. Missing formulas may not be imported from the
unrelated absolute-penalty paper or inferred from ranks and benchmarks.

MITC9i remains independent. Production remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`; legacy `ShellElement` remains the
default.

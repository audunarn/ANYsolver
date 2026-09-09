# Equilibrium-first native force recovery

Parent `e68234b63fef958084857e92ccf234e6222fe0d6`, tree
`ce394956e690e372b122e913b4b1fae041ae8bd6`. Preserve the fallback-heavy
controller and its evidence. This gate performs no nonlinear or modal solve.

For the unchanged block matrix [A B; D -C], retain the same geometric Schur
solve. Recover p from B p = b_g - A g instead of subtracting two compliance
actions. If there are fewer geometric rows than force coordinates, use QR
to complete ALL geometric equations with selected original compatibility rows.
QR chooses a numerical equation basis, not a scientific rank classification;
the original complete residual remains the acceptance authority.

References: SciPy's documented full/pivoted QR decomposition and LAPACK's
componentwise error definition:
https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.qr.html
https://www.netlib.org/lapack/lug/node81.html
No library/dependency version change is requested; use the frozen local runtime.

The method must satisfy the existing 1e-11 componentwise backward check without
full-system fallback, zero clipping, equation symmetrization or an added
absolute tolerance. At most three full-defect refinements are allowed with the
same factors. Preserve physical internal rotations and all constitutive laws.

Cases: the three failed initial systems from the previous controller fixtures;
new local trials based on each preserved accepted history; two-macro curved
cantilever and doubly clamped systems, the latter requiring six compatibility
completion equations. Verify complete increments against independent full
solves and one standard-library exact rational solve of the actual 36-by-36
binary64 matrix. The rational witness uses exact Fraction arithmetic and exact
final multiplication, never production mechanics or a floating zero tolerance.

Run the local rehearsal first. Freeze only after it passes, then run two fresh
bounded test cycles and require byte-identical scientific packets. One thread,
24 GiB, 600-second process wall and 120-second activity limits; factor/actions
60 seconds and the small rational witness 20 seconds. No automatic retry.

This is private solver development, not element or production qualification.
Keep the previous controllers, beam/shell mechanics, defaults, aliases and
qualification evidence unchanged. A local pass would permit a separately
reviewed controller comparison, not activation or a general performance claim.

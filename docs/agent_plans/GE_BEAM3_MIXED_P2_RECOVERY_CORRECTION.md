# GE Beam3 Mixed P2 Recovery-Fixture Correction

## Preserved incident

Preregistration commit `448ae38cad85365f0058fca8174fb5a12aa57bbc`
is preserved unchanged.  Its
`RECOVERY_UNIFORM_SHEAR_Y_NATIVE_STATE` fixture incorrectly reconstructed the
force strain directly from nodal translations.  That skips the 18-variable
local stationarity problem required by both accepted mixed equation maps.  The
fixture therefore prescribed zero recovered curvature even though its zero
vertex rotations require the condensed element rotation and endpoint moments
to equilibrate the nonzero shear force.

This is an authority-input defect, not a mechanics defect.  The accepted P1
checker independently solved the local variables and required only activation
of the isolated shear component; it never asserted the invalid P2 constant
strain state.  No production mechanics, coefficient, quadrature, condensation,
tolerance, or candidate identity changes are authorized by this correction.

## Exact manufactured replacement

Replace the invalid fixture, for P2 execution only, with
`RECOVERY_MANUFACTURED_UNIFORM_SHEAR_Y_NATIVE_STATE`.  On each half-cell use

\[
g=1/5000,\quad \ell=1/2,\quad K_s=8750000000/13,\quad D_z=420000,
\]

linear transverse displacement `y=g*x`, and the common vertex rotation

\[
Q^V=R_z(\theta),\qquad \theta=-\frac{\ell^2K_sg}{12D_z}=-25/3744.
\]

For the diagonal section, the exact local stationary solution is

\[
Q^E=I,\qquad m_L=\frac{\ell K_sg}{2}=437500/13,
\qquad m_R=-m_L.
\]

The four sided station records therefore alternate

\[
\varepsilon_{L/R}=[0,1/5000,0,0,0,\pm25/312],
\]

\[
s_{L/R}=[0,1750000/13,0,0,0,\pm437500/13].
\]

The independent correction checker derives these quantities with rational
arithmetic and verifies all three local first variations.  Binary64 comparisons
use the already frozen normalized `1E-11` invariant tolerance; componentwise
relative error is not used for mathematically zero components amplified by the
large axial stiffness.

## Authority and execution boundary

The original case manifest and independent-reference program remain immutable
incident evidence.  The correction overlay supersedes only the named recovery
fixture.  A successor contract binds both original artifacts, this overlay, its
independent rational checker, and an independent review.  P2 scientific
execution remains unauthorized until the candidate implementation is frozen and
a separate execution authorization is issued.

All public selectors, aliases, package metadata, defaults, qualified Q4 and S3
mechanics, legacy beams, and the accepted P1 mechanics remain unchanged.


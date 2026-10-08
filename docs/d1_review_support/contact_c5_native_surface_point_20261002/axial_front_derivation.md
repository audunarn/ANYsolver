# Moving axial contact front — development derivation

Final rectangular-cover trial still fails support128 after80queries/10support panels,
1.52s test call. No successful aggregate/coupled response. Stop rectangular tuning.

On each admitted straight native half-cell, with fixed material angle, the physical
surface is X(t,xi)=L(t)+xi D(t)+R(t)rho. The target plane uses its actual unnormalised
cross product C(t). Define A=C dot (L+Rrho-Y0), B=C dot D. Then physical gap is
(A+B xi)/|C|; xi_f=-A/B when B is resolved nonzero. No planar-normal derivative is
lost: positive |C| cancels only in the zero equation.

N=A'B-AB'; xi_f'=-N/B^2. Stationary fronts satisfy N=0, with
N'=A''B-AB''. At a stationary point xi_f''=-N'/B^2.
Affine target edges give exact C,C',C''. Source arm derivatives are omega cross arm
and omega cross (omega cross arm), with original declared time. Source centreline
translations are affine. native_surface_front.py evaluates these coefficients.

For a fixed angle, endpoint fronts and ALL stationary front values partition axial
material coordinate into regions of constant simple-root topology. Next implement
bounded interval isolation of N, guard B=0 and target area, and order these boundaries.
A bracketed scalar root alone is not complete isolation. Angular changes, front
intersections and degenerate stationary points need their own bounded handling.
Only after that connect curvilinear spatial integration; preserve both-body work,
physical history and the required moving-boundary derivatives. No zero-measure or
small-pulse argument may silently delete finite integration regions.

Executed local geometry check:1pass, pytest3.92s, test0.15s. Saved stationary point
recovered at t=.4999999999950846,xi=.7244843413242319,angle3.1990185900472157;
N=2.78e-17, physical axial gap slope=-.00939936910149583m. Coefficients reproduce
actual adapter gaps and first/second derivative finite-difference controls. This is
not a whole-region certificate or acceptance. Raw failure/success evidence retained.

Source reviewer confirmed formulas and found derived overflow could escape finite input
guards. Added finite-result rejection for axial quotient, N and N-prime;1focused overflow
check passes. B bounded away from zero and complete root isolation remain admission needs.

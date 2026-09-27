# Native B3 / E4 material-line work contract — G0 development derivation

**Status:** Bounded analytical reference for the candidate material-pose line.
It defines neither a selected multiplier space nor a qualified physical bond.
The current gate and evidence inventory remain in
`B3_GE_E4_PL_CURRENT_CHECKPOINT.md`.

## Continuous idealization

At a fixed reference material station `x` on the shell line `y=0`, let
`N_a(x)` and `N'_a(x)` be the admitted Q4 or S3 trace shape and its physical
longitudinal derivative. With shell reference-surface positions `r_a`,
directors `R_a e_z`, and top offset `t=h_s/2`, define

\[
r_s=\sum_a N_a(r_a+R_a t e_z),\quad
d_s=\frac{\sum_aN_aR_ae_z}{\|\sum_aN_aR_ae_z\|},\quad
a_s=\sum_aN'_a(r_a+R_a t e_z).
\]

Let `e_s` be the normalized projection of `a_s` orthogonal to `d_s` and
`R_s=[e_s,d_s\times e_s,d_s]`. The beam axis point and frame
`(r_c,R_b)` come from the actual retained B3 half-cell port, including
its reference lift and one-sided internal coordinates. With beam-bottom
offset `b=-h_b/2`, its physical surface point is `r_b=r_c+R_b b e_z`.

The candidate constrains one **material pose along the center line**:

\[
c_t=R_b^T(r_s-r_b)-e_0,\qquad
c_R=\operatorname{Log}(A_0^TR_s^TR_b),
\]

where `e_0` and `A_0` are fixed reference offsets. Its exact weak work is
`∫(lambda_t·c_t + lambda_R·c_R) dx` over the declared bond. The
correspondence and quadrature segments are fixed in the reference
configuration. This is a two-sided shell-top/beam-bottom **line-pose**
idealization; it does not tie every point across the finite-width face.
Rigid and distributing footprints remain different connection laws.

## Independent flat-reference linearization

For a straight flat reference with `R_s=R_b=I`, zero lift, shell thickness
`h_s=.035 m` and beam depth `h_b=.1 m`, let `u_a,theta_a` be shell nodal
increments, `u_L,u_R` the native half-cell endpoint translations, and
`omega_b` its retained spatial rotation. If `xi` is the beam half-cell
fraction, direct geometric differentiation gives

\[
\begin{aligned}
\delta r_s&=\sum_aN_a(u_a+\theta_a\times t e_z),\\
\omega_s&=\left(\sum_aN_a\theta_{a,x},\quad
                 \sum_aN_a\theta_{a,y},\quad
                 \sum_aN'_a(u_{a,y}-t\theta_{a,x})\right),\\
\delta r_b&=(1-\xi)u_L+\xi u_R+\omega_b\times b e_z,\\
\delta c_t&=\delta r_s-\delta r_b,\qquad
\delta c_R=\omega_b-\omega_s.
\end{aligned}
\]

In particular, the shell yaw channel is a top-line *tangent* variation,
not a direct `rz` tie. The roll and pitch channels use the independent
shell director. This preserves the distinction between director motion
and geometric normal and explains why lateral-force and yaw-moment weak
rows can be linearly coupled. For curved/pre-rotated references, use the
full pose map and chart derivatives; these flat formulas do not replace
them.

For physical multiplier densities `(f,m)` at this reference, the
virtual work is

\[
\delta W=\int_\Gamma
f\cdot(\delta r_s-\delta r_b)+
m\cdot(\omega_b-\omega_s)\,dx.
\]

Thus top-offset force work contributes `t e_z × f` to shell director
moments, and bottom-offset force work contributes `-b e_z × f` to the
retained beam rotation. The yaw couple also acts on shell **translations**
through `-m_z N'_a u_{a,y}` and on shell roll through
`+t m_z N'_a theta_{a,x}`. At finite rotation, the Log derivative and
chart transformation must be applied before displaying physical wrenches;
raw rotation-constraint multipliers are not automatically spatial moments.

## Eccentric patches and checked boundary

The surface separation between reference axes is `t-b=.0675 m`. Equal
shell/beam roll `alpha` closes all six line gaps only if the bonded beam
axis translates `-.0675 alpha` in `y`. Equal pitch closes them only if it
translates `+.0675 alpha` in `x`. Removing that compensation leaves a
`∓.0675 alpha` physical position gap. A matched `z` translation of both
sides also closes the gap; translating only the shell gives the same
`z` gap. A 1,000 N resultant acting through the uncompensated offset
does `±1000(.0675 alpha) J` of constraint virtual work. These are
support-admissible fields on the bounded fixture, not whole-structure
rigid motions.

A shell lateral displacement with slope `gamma` gives continuous
`c_{Rz}=-gamma` and `-100 gamma J` of yaw-couple work for a 100 N m
resultant, even with no shell `rz` increment. A pure `rz` increment has
zero flat-reference line work. A longitudinal gradient of shell
`z` displacement leaves the director-pitch gap zero; this line law does
not force the director onto the geometric surface normal. These facts
identify the coupled force/yaw and transverse-shear terms that a
multiplier space and physical reference must preserve.

Independent geometric rows built from these formulas match the candidate
reference Jacobians for Q4 and both off-edge S3 diagonals: position error
is zero at printed precision and orientation maximum is `2.85e-14`.
The three focused analytic-work tests pass. This verifies the bounded
continuous *linearized* work convention and offset signs. It does not
establish finite-width weld equivalence, shell torque accuracy,
mesh-uniform multiplier stability, loaded nonlinear behavior, or G0B.

The saved F5 shared-face solid model bonds a complete finite face and
therefore is not an equivalent pointwise reference for this center-line
law. A matched two-sided physical comparison must state the shell
director/line-pose meaning and preserve the native half-cell side and
eccentric virtual work before applying an accuracy threshold.

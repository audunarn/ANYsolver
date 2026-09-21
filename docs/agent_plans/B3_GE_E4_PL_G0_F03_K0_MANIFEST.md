# F03-K0: native B3 / physical E4-PL exact-multiplier screen

Status: **DRAFT, NOT FROZEN, NOT EXECUTED.** This is a bounded G0
diagnostic to reject or prioritize multiplier spaces. It cannot select
the production line law or close F03/G0B. The governing plan and
registration retain the complete six-channel, curved, thinning,
director, 1:8 reciprocal and independent-reference obligations.

## Fixed physical model and inventory

Reference beam axis \((s,0,0)\), \(s\in[0,1]\) m, native retained
three-node generalized B3 elements with \(N_b=4,8,16\) half-cells,
two per element. Material \(E=210\) GPa, \(\nu=.3\),
\(G=E/[2(1+\nu)]\). Section inputs are \(A=.01\ {\rm m^2}\),
\(A_y=A_z=.008\ {\rm m^2}\),
\(I_y=I_z=8.333333333333333\,10^{-6}\ {\rm m^4}\) and
\(J=1.6666666666666667\,10^{-5}\ {\rm m^4}\).
The explicit generalized elastic law is
\(\operatorname{diag}(EA,GA_y,GA_z,GJ,EI_y,EI_z)\) in
\([N,V_y,V_z,M_x,M_y,M_z]\) resultant order. Its ellipsoidal
yield and hardening inputs are \(10^{20}\) and \(10^9\) in the
existing section contract; the reference state must remain virgin
elastic. Fix all six physical root DOFs, leave the other native
physical DOFs and all 24 internal variables per B3 element free.
Use the actual retained local residual/tangent and spatial chart
transform, with a separate bounded Context dense **assembly parity**
oracle. Both use the same local constitutive operator; their
agreement is not an independent mechanics/pose qualification.
The reference axis lies on the shell plane in this restricted
screen. An out-of-plane z offset would be invisible to its
tx,ty,Rz linearized channels and must not be described as an
eccentricity check. The native station pose and its derivative must retain each
half-cell rotation and reference lift. A nodal Q2 rotation or
displacement surrogate is forbidden.

Shell panels have \(x\in[-.5,1.5]\) m, \(y\in[-.5,.5]\) m,
two transverse rows, \(2N_s\) x intervals of length \(1/N_s\),
Q4 or consistently split S3-V2D, \(t=.07\) m and the same
elastic \(E,\nu\). Assemble each existing E4-PL element's
**physical in-plane** stiffness block; fix ux and uy only
on the two x-end edges at \(-.5,1.5\) m. Keep both
longitudinal outer-y rails free, so y-separated samples
can transfer physical torque through independent rail
translation. Verify the supported physical shell block
is positive, and perform common rigid/affine patch checks
on its *unrestricted* trace with explicitly mapped boundary
values. Numerical drilling stiffness and shell
director coordinates do not enter this planar screen. For each
\(N_b=n=4,8,16\), take \(N_s=n/2,n,2n\), with both shell
topologies: **18 physical meshes**. The nominal \(N_b:N_s\)
ratio describes beam half-cell to shell-x interval counts,
not the support width or the number of actual sample hosts.
Record nodes, shells, native elements, supported physical/retained
counts, host sizes and peak attachment incidence.

At each \(s\), fixed reference shell samples are
\((s-.2,-.23),(s+.2,-.23),(s+.2,+.23),(s-.2,+.23)\) m.
The shell trace is the actual Q4/S3 host interpolation of the
four translations and the analytic infinitesimal proper-fit
centroid/yaw. The beam trace uses actual lifted positions and
retained cell yaw. The reference offset and relative frame
come from those poses; at every assembled station report
three planar gap components and independently sampled
unscaled six-component reference gaps. The latter three
channels are diagnostic only, not stabilized in this screen.
The runner must construct a separate three-dimensional
proper-Procrustes pose from all four interpolated shell
reference/current sample positions, form the actual point
relative-pose law against the native station pose, and compare
its planar finite-difference variation to the analytic trace.
Returning zeros from the linearized trace is not a reference
gap oracle. No production reference offset may be adjusted
after a trial to force this check to pass.
Directional pose/work probes must separately excite
(i) retained half-cell yaw with nodal coordinates fixed,
(ii) differential ux of the two shell rails, and
(iii) common beam/shell rigid and affine planar fields.
The supported KKT fixture has a fixed beam root and cannot undergo a
nonzero global rigid motion through `Context.advance`. Apply unrestricted
common rigid/affine fields algebraically to the full *unconstrained native
pose map*: transform the reference nodal positions and frames, both
cell frames, and the actual lifted station. Compare this analytic
proper-rotation/pose check to the unrestricted full-column trace map;
it is a kinematic patch check, not a supported constitutive solve or
a finite difference through `Context.advance`. Separately use actual
`Context.advance` for compatible zero-root directions and retained yaw
finite differences. Apply explicitly mapped nonzero boundary values
for the unrestricted shell patch. No claim of an unrestricted native
`Context.advance` patch is permitted because Context admission requires
a supported nonsingular static model.
Use the independent proper-fit pose for finite differences at an off-grid
station on each topology and on both sides of a half-cell
boundary. Verify physical force/moment balance from the
full support and connection maps rather than only
checking the algebraic identity \(q^TC^T\lambda=\lambda^TCq\).
The planar gap is \((c_{tx},c_{ty},c_{Rz})\), with
\(\ell=2b=.46\) m fixed throughout; scale
\(d=(c_{tx},c_{ty},\ell c_{Rz})\) in meters and its conjugate
\(\mu=(\lambda_{tx},\lambda_{ty},\lambda_{Rz}/\ell)\)
so work is unchanged. No current-configuration remapping.

## Five exact spaces and integration

Compare (1) discontinuous P0 on the union, (2) continuous P1
on shell knots, (3) continuous P1 on beam half-cell knots,
(4) continuous P1 on union knots, and (5) elementwise
biorthogonal dual to continuous union P1, with the scalar basis
replicated for each planar gap component. Define shell knots
as the attachment-coordinate host-change points for all four
samples, including S3 diagonal crossings, clipped to
\([0,1]\); beam knots are \(j/N_b\). The union includes
both. Record each basis dimension, near-duplicate gap and
all knot arrays. This definition deliberately differs from
F03-S's unshifted scalar shell grid; those historical
numbers cannot be treated as this system's stability.
The dual functions on each union cell use \((2-3\xi,3\xi-1)\)
as in F03-S and require their exact assembled \(L^2\) mass,
not a diagonal replacement. They share a nodal index across
cells but are generally discontinuous at an interior knot
for adjacent nonshared basis functions; do not call the dual
space continuous or evaluate its knot value without a
declared one-sided convention.

Split four-point reference-arclength Gauss integration on
the union of multiplier knots, native half-cell boundaries,
shell host changes/diagonals and both attachment ends.
At one-sided native half-cell boundaries use the open
interval's own trace; never average the two cell rotations.
Use a separate two-point Gauss integration of the
piecewise-polynomial \(B,M,G\) matrices as an oracle;
record relative differences \(\le10^{-10}\), maximum
and minimum positive segment size, quadrature counts
and reference samples. The smooth external load defined
below is integrated by the same four-point rule and is
not covered by the two-point polynomial oracle.
Use the Frobenius norm of each two-point,
work-scaled \(B S_q\), \(S_q^TG_DS_q\) and
\(M\) matrix as its respective nonzero relative
denominator, and record each absolute error. If any
reference norm is zero or nonfinite, classify the
case as invalid rather than manufacture a floor.
Record the
largest number of active shell/beam physical and
retained columns at a station and the maximum nonzero
columns in one assembled constraint row as incidence.

For supported primal coordinates \(q\), form the physical
gap derivative \(D(s)\) and the exact constraint matrix
\(C=\int \mu(s)^T D(s)\,ds\). Set multiplier mass
\(M=\int\mu^T\mu\,ds\), trace Gram
\(G_D=\int D^T D\,ds\). The raw constraint equation is
\(Cq=0\); the equilibrium equation is \(Kq+C^T\lambda=f\).
Use the *actual* native retained tangent plus physical
shell stiffness, not a penalty or a symmetrized tangent.
Check full row rank after multiplier \(M\) whitening and
declared primal scaling; relative singular threshold
\(10^{-10}\). Record all scaled singular values.
Evaluate the rank associated with \(G_D\) through the
stacked \(\sqrt{w_j}D(s_j)S_q\) trace factor, with the
*same singular-value threshold*: applying \(10^{-10}\) directly
to the squared Gram spectrum would test trace modes only to
\(10^{-5}\). Record trace rank minus row rank
and representative weak physical gap fields. A missing
row or unsupported interface mode is a negative
candidate result, not an execution failure.

Freeze one diagonal primal coordinate scale \(S_q\) for
every measurement. Let \(u_*=f_0L_0/(Et)\), \(\ell=.46\) m,
\(L_0=1\) m: nodal and shell translations scale by
\(u_*\), nodal and native cell rotations by \(u_*/\ell\).
Each native element's 18 resultant coordinates follow the actual
`z + ell` layout: two cell force triplets, each
\((EA,G A_y,G A_z)u_*/L_0\), followed by four endpoint
moment triplets, each \((GJ,EI_y,EI_z)u_*/\ell L_0\).
This is not three alternating force/moment sextuples.
The latter do not enter the reference trace,
but must enter KKT residual and symmetry measurements.
Use \(q=S_q\hat q\), \(\hat K=S_q^TKS_q\),
\(\hat C=CS_q\), \(\hat f=S_q^Tf\).
Apply \(S_q^T\) to every equilibrium/compatibility
covector in both numerator and denominator. The same
scale partitions with native physical/internal blocks
and the shell; \(M\) retains its assembled \(L^2\)
units. For row rank whiten \(\hat C\) with
Cholesky \(M\); report its complete singular spectrum.
This is work scaling for a saddle system, not an
assertion that full retained \(K\) is positive.
The coefficients of the scaled multiplier field
\(\mu\) use \(S_\lambda=f_0 I\), \(f_0=10^6\)
N/m, for a KKT work congruence by
\(\operatorname{diag}(S_q,S_\lambda)\).
Use this same fixed congruence for its singular
ratio, residuals and dense/sparse parity; the
multiplier \(L^2\) mass whitening is a separate
rank diagnostic, not a change of the solved system.

The native retained block \(K_{rr}\) may be indefinite.
If invertible, partition native physical/internal
coordinates and compute, exactly,
\[
K_e=K_{pp}-K_{pr}K_{rr}^{-1}K_{rp},\quad
 C_l=C_p-C_rK_{rr}^{-1}K_{rp},\quad
 C_u^T=C_p^T-K_{pr}K_{rr}^{-1}C_r^T,\quad
S_r=C_rK_{rr}^{-1}C_r^T.
\]
The condensed exact KKT is
\(\left[\begin{smallmatrix}K_e&C_u^T\\C_l&-S_r
\end{smallmatrix}\right]\)
with consistent reduced loads. **Do not drop \(-S_r\).**
For nonzero retained load \(f_r\), the reduced right-hand
side is \((f_p-K_{pr}K_{rr}^{-1}f_r,\,
-C_rK_{rr}^{-1}f_r)\). The registered
straight line loads below have \(f_r=0\);
compare a separately identified manufactured
nonzero-\(f_r\) algebraic case before claiming
general reduced-load parity.
Only after independently verifying that the virgin coordinate
tangent is symmetric within the registered scaled tolerance
may \(C_u^T\) be identified with \(C_l^T\). Do not average
asymmetric tangent blocks or classify a spatial-row Jacobian as a
conservative Hessian merely by naming its blocks.
Compare its solution and multipliers against the full
sparse KKT on a bounded case; require relative solution,
constraint and virtual-work discrepancies \(\le10^{-10}\).
Require work-scaled symmetry skew
\(\|\hat K-\hat K^T\|_F/\|\hat K\|_F
\le10^{-10}\) before conservative eigen/energy
claims, separately for full native K, \(K_{rr}\)
and \(K_e\). Never symmetrize for the actual solve.
Require finite work-scaled
\(\kappa_2(K_{rr})<10^{16}\), elimination
residual \(\le10^{-9}\) relative to the
nonzero scaled block terms, and smallest
eigenvalue of \(\hat K_e\) above
\(10^{-12}\lambda_{\max}(\hat K_e)\).
Report all scales, condition estimates, inertias and
the unsymmetrized residual. These are numerical
screen criteria, not a change to section properties.
If \(K_{rr}\) is singular or \(K_e\) cannot be shown
positive on the supported physical domain, report
PRIMAL_NOT_ADMISSIBLE with inertia/conditioning and
stop mechanical stability adjudication for that mesh.
Do not take absolute stiffness eigenvalues or add
regularization.

Because the full retained \(K\) is saddle, the proposed
positive-primal formula \(C K^{-1}C^T\) is **not**
automatically a mechanical inf-sup norm. On admissible
meshes, report the physical-only floor of
\(C_lK_e^{-1}C_u^T\) relative to \(M\) as a
diagnostic, and separately report the signed spectrum
of the *exact* multiplier Schur
\(C_lK_e^{-1}C_u^T+S_r=C K^{-1}C^T\).
Only call either spectrum signed/eigen or apply a positive
Rayleigh floor after verifying symmetry in the actual
coordinate representation; otherwise report singular values
and nonconservative classification. The same check applies
to the condensed physical \(K_e\) before an SPD claim.
For scaling, use \(E t/L_0\), \(L_0=1\) m, after
the fixed \(\ell\) channel conversion. Neither the
physical-only floor nor row rank alone selects a
space. Require full KKT nonsingularity with scaled
singular/inertia checks and finite solution: after
the fixed \(S_q\) and multiplier mass/force scaling,
the smallest-to-largest singular ratio must exceed
\(10^{-12}\) for a numerical PASS. Bounded
full/condensed solution and work discrepancies require
\(\le10^{-10}\) relative to nonzero physical scales.
Preserve
negative modes and any physical-mode deficiency.
Freeze an energy norm for an actual inf-sup acceptance
in the later full F03 gate after a separate mechanics
review of the retained saddle structure.

## Loads, measures and screen disposition

For each mesh and candidate, apply independently:
(A) smooth beam line force \(f_y(s)=10^6
[1+.25\cos(2\pi s)]\ {\rm N/m}\) and
(B) alternating force \(f_y(s)=10^6(-1)^j\
{\rm N/m}\) on beam half-cell \(j\).
Both act on the actual native lifted translational
trace; all other applied components are zero.
Use the same supported primal map for all candidates.
Normalize displacements and gaps by
\(u_*=f_0L_0/(Et)\), pointwise gap by \(u_*\),
its \(L^2\) norm by \(\sqrt{L_0}u_*\), and
weak residual by
\(\sqrt{(Cq)^TM^{-1}(Cq)}/(\sqrt{L_0}u_*)\).
Normalize free equilibrium by
\(\|S_q^T(Kq+C^T\lambda-f)\|/
\max(\|S_q^TKq\|,\|S_q^TC^T\lambda\|,
\|S_q^Tf\|)\).
Report support reactions, total force/moment about
the reference origin, interface virtual work,
physical shell energy from the active in-plane K.
If the excluded numerical E4-PL blocks are queried,
report their quadratic value as an **inactive**
diagnostic only; exactly zero numerical stiffness
enters the solve, physical energy balance, beta
or KKT. Record
the full physical gap along each interval,
pointwise and weak gaps, multiplier oscillation
and every candidate failure.
Define multiplier oscillation per channel as
\(\sqrt{L_0^2\int|\lambda'(s)|^2ds+
L_0\sum_{\rm interior\ knots}|[\lambda]|^2}/
\max(\|\lambda\|_{L^2},f_0\sqrt{L_0})\),
using one-sided cell polynomial derivatives and
the exact interior jump contributions;
report the derivative and jump parts separately.
The smooth-load pointwise maximum is
\(\max_{s\in Q_{\rm four}\cup\{\text{one-sided knots}\}}
\|d(s)\|_2/u_*\), with physical gap \(d\) scaled
by the frozen \(\ell\). A trend is NONDECREASING
only when both n→2n and 2n→4n changes at
fixed topology/ratio are at least \(-1\%\);
smaller changes are marked INCONCLUSIVE.
Flag alternating-load oscillation when its
normalized value grows by at least twofold
on both size doublings; otherwise report
the numbers without silently classifying a
mode as stable.

Diagnostic thresholds to screen, never to qualify
full F03: separate reference translation and rotation
gaps at every assembled station \(\le10^{-12}\)
in their own units; patch and independent work
gradients \(\le10^{-10}\) relative in
nonzero physical scales; positive \(K_e\);
zero scaled constraint row-rank loss; normalized
free equilibrium \(\le10^{-9}\), normalized
weak residual \(\le10^{-10}\), relative work
error \(\le10^{-10}\). A beta-like
physical-only floor falling by at least twofold
on both size doublings at fixed mesh ratio is
flagged DECAYING, not selected. Alternating-load
multiplier oscillation or smooth-load pointwise
gap that fails to decrease receives
MECHANICS_REVIEW_REQUIRED even if the KKT
is nonsingular. Record all failures and aborted
cases; do not choose a P0/P1/dual winner from
this planar screen. If no candidate passes
its limited mechanical checks, F03 remains
failed/open for formulation revision rather than
advancing G1.

## Freeze and execution requirements still pending

Before executing, bind the exact native/shell/helper
source hashes, reviewer findings, runner hash, dependency
versions, supported sparse backend, hardware, one-thread
settings, time/peak-memory limits, immutable cold
evidence path and process-exit provenance. The first
run must not begin while this section or any
fixture/normalization definition is unresolved.
Keep the native Context's actual 120-second local guard:
construct each fixture within its bound, never tamper
with its start time, and distinguish later sparse-solve
resource limits from operator-evaluation guard failures.
Independent review must adjudicate the induced
multiplier block, units and whether the restricted
planar limit legitimately tests the selected physical
line law. This draft has no execution authority.

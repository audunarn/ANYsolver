# Independent F03 next-experiment mechanics review

Read-only planning review, 21 September 2026. The registered G0B F03
decision remains open. F03-S compared scalar Q2 beam traces, not the native
half-cell position; every candidate left scalar difference modes unresolved,
and union P0's floor decayed under one 1:8 refinement direction. F03-B/v2
verified the native lifted translation, F03-V/v3 verified a single-station
six-component pose and signed torque, and the independently reviewed
F03-P-v4 passed six **shell-only** off-grid load cases. None assembled an
integrated exact constraint against both native B3 and physical shell
stiffness. The v4 JSON alone does not prove its launch environment/exit.

## Smallest useful next executable experiment: F03-K0

Register a **planar, virgin-elastic coupled exact-multiplier screen** before
execution. This is a diagnostic rejection/triage stage, not F03 selection or
G0B acceptance. Use the existing physical in-plane Q4/S3-V2D element
stiffness from F03-P-v4 and one declared native *retained generalized B3*
elastic program with its actual local operator and retained half-cell
variables from F08. Assemble the latter by the independently checked local
sparse seam; do not substitute a public B2 scalar stiffness, Q2 displaced
beam trace, nodal-rotation interpolation, artificial drill spring, or a
penalty constraint. Inspect and record whether the virgin supported primal
operator can be reduced to a positive physical energy operator by an exact
retained-variable Schur elimination. If it cannot, stop this screen with
`PRIMAL_NOT_ADMISSIBLE`, retaining the native saddle form for diagnosis;
never take an absolute value of negative stiffness or silently regularize.

Use the candidate's four moving shell samples at `s±0.2,y=±0.23`, native
lift `r_b=I_c(x+x_low)+U_c L_c`, and reference-derived `e0,A0`. The shell
panel is `x∈[-0.5,1.5], y∈[-0.5,0.5]`, with two transverse cell rows and
uniform x spacing `1/N_s`; the attachment is `s∈[0,1]`. Thus `N_s` means
shell *x intervals along the attachment*, and `N_b` means native B3
*half-cells*, two per three-node element. Use `(N_b,N_s)=(n,n),(n,2n),
(n,n/2)` for `n=4,8,16`, Q4 and consistently oriented diagonal S3-V2D;
these are 18 physical meshes. The y rails remain strictly interior to the
two transverse rows. This first 1:2/2:1 screen has three line refinements;
the registered 1:4/1:8 reciprocal sweep, transverse refinement, curvature,
full vector/director/thickness behavior and mixed Q4/S3 hosts remain for
the complete F03 gate. State the actual sample-host sizes and counts so
the nominal ratio is not confused with the ribbon's physical width.

For each physical mesh compare the five **exact** spaces already defined in
F03-S: discontinuous P0 on the union of beam-half-cell and shell-interface
knots; continuous P1 on shell, beam-half-cell and union knots; and the
elementwise biorthogonal union dual. Apply the *same* scalar multiplier
basis to each of the three planar pose gaps. Choose a fixed physical length
`ell=2b=0.46 m`; let `d=(c_tx,c_ty,ell*c_Rz)` in meters and
`mu=(lambda_tx,lambda_ty,lambda_Rz/ell)` in N/m, so `mu·d` is the original
line work. A restricted planar calculation must still derive these rows
from the six-component native trace Jacobian, then restrict coordinates;
the untested other three rows cannot be declared stable. On every integration
interval split at shell sample-host edges (including S3 diagonal crossings),
beam half-cell boundaries, multiplier knots and attachment ends. Use fixed
reference arc length and four-point Gauss, with a separate midpoint/analytic
piecewise-linear oracle for the reference tangent where applicable. Record
the minimum segment size and quadrature changes, since tiny union intervals
can make a raw unscaled rank misleading.

At reference let `D(s)=∂d/∂q` and `B_ij=∫ mu_i(s)·D_j(s)dL0`, with
`M_ij=∫mu_i·mu_j dL0` and `G=∫D^T D dL0`. The physical primal `K` is
block-diagonal native beam plus physical shell before coupling, with
declared essential supports and exact retained condensation. Freeze the
supported DOF map once per mesh and use it for every candidate. Full row
rank of `M^{-1/2} B K^{-1/2}` at relative SVD threshold `1e-10` is
mandatory. Compute the *mechanical* inf-sup floor as

`beta² = (E*t/L0) min_(v!=0) [vᵀ B K^-1 Bᵀ v / (vᵀ M v)]`,

with `E=210e9 Pa`, `t=.07 m`, `L0=1 m`; after the above channel scaling
this is dimensionless. Report the entire nonzero spectrum, `rank(G)-rank(B)`
and the physical gap fields of its most weakly controlled modes. A missing
row is failure; `rank(G)-rank(B)>0` is a warning requiring an active-mode
test, not automatic rejection, because weak mortar spaces need not constrain
every pointwise trace function. Apply identical smooth unit line loading
and one alternating/high-frequency interface loading at each refinement,
each with line-density `f0=1e6 N/m` in the scaled planar work channel.
Set `u*=f0*L0/(E*t)` (meters). Normalize the pointwise gap by `u*`, its
`L2` norm by `sqrt(L0)*u*`, the weak residual by
`sqrt((Bq)^T M^-1 (Bq))/(sqrt(L0)*u*)`, and the free equilibrium residual
by `||Kq+B^T mu-f||/max(||Kq||,||B^T mu||,||f||)` on the same supported
coordinates. Report multiplier oscillation, both normalized gaps and energy;
a zero **weak** gap is not a zero pointwise gap.

Before running, freeze the exact support map, B3 section/moduli, smooth and
alternating load shapes, sign convention, rank/energy scales, source hashes,
resource limit and cold log path in a new registered case manifest. The
proposed diagnostic predicates are: six reference gaps at every station
`<=1e-12` in their native units; independent patch/work gradients
`<=1e-10` relative for common rigid and affine planar traces; all finite,
positive supported primal eigenvalues; zero multiplier row-rank loss;
normalized free equilibrium residual `<=1e-9`, normalized weak residual
`<=1e-10`; and relative virtual-work error
`<=1e-10`. Flag a candidate as **decaying**, not selected, if its beta
falls by a factor of two or more on *both* mesh doublings at fixed ratio;
report any weaker trend as inconclusive. An oscillatory multiplier or
nondecreasing normalized pointwise gap under the smooth load requires
mechanics review even if beta is nonzero. These are proposed screen rules,
not retroactive G0B acceptance limits; the complete F03 plateau and locking
thresholds must be approved in its manifest before its first execution.

The critical invalid shortcuts are: taking F03-S's Q2/P1 floor as native
B3 stability; using the positive F03-P compliance as evidence of an exact
KKT; assigning shell torque to a numerical drill DOF; omitting the
half-cell midpoint's one-sided traces; calling four moving samples an area
traction; accepting row rank while active difference modes oscillate; and
rescaling `ell`, physical ribbon width or multiplier norms with `h` between
levels. A small supported KKT can pass while the full six-channel, mixed
topology, director/shear, thickness and 1:8 reciprocal F03 gate fails.

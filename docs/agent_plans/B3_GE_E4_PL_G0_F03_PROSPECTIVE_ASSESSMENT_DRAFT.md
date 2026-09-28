# F03 prospective six-channel assessment — mathematical contract draft

**Status:** Development draft, 28 September 2026. It is neither an adopted
replacement criterion nor execution authority. Independent mechanics review,
numerical floors and thresholds are required before a formal F03 run. Historical
F03 registrations, failures and protected evidence remain unchanged. The
Revision 7 development ceiling applies to any later diagnostic.

## Decision and distinct questions

Determine whether an objective six-channel, drill-free material line law can be
enforced by a growing multiplier space without an unsupported interface mode,
locking or incorrect physical transfer. Keep three decisions separate:

1. Which continuous pose/offset work is intended and mechanically admissible?
2. Which discrete interface space resolves that work at each mesh ratio?
3. Does the resulting structure reproduce matched physical transfer and
   response? An interface quotient alone answers neither (1) nor (3).

The current L1 **development candidate** samples the E4 top-line position and
its director/projected-material-tangent triad, plus the actual retained B3
half-cell pose and a beam-local section arm. Its translation gap is

\[
 c_t=R_s^T(r_b-r_s)-e_s,\qquad
 e_s=R_{s0}^T(r_{b0}-r_{s0}),
\]

and its rotation gap is
\(c_R=\operatorname{Log}(A_0^TR_s^TR_b)\),
\(A_0=R_{s0}^TR_{b0}\). This matches the existing point-joint convention,
but **differs** from the saved beam-frame material-line candidate
\(R_b^T(r_s-r_b)-e_b\). Both are objective. When the rotational gap vanishes
and the reference offsets are transformed consistently, they can have the
same constrained zero set. Away from that set, their derivatives, multiplier
bases and work differ. Before accepting L1, derive the full first and second
variations, physical wrench maps and chart transformations for the chosen
convention; compare the alternative at the same constrained physical state.
The bounded local point probe now checks both work Hessians through actual
E4/B3 updates. A two-segment probe composes their discrete quadrature work;
neither establishes continuum line convergence or a production law.

Specifically, with \(Q=R_s^TR_b\) and \(e_b=-A_0^Te_s\), the beam-frame
translation candidate is
\(c_b=-Q^Tc_t+(A_0^T-Q^T)e_s\). At a zero rotational gap,
\(Q=A_0\) and \(c_b=-A_0^Tc_t\), but at the constrained pose its variation is
\(\delta c_b=-A_0^T\delta c_t-(\delta Q^T)e_s\). Thus a beam-frame translation
multiplier also supplies a rotation moment. Its shell-frame dual has
\(f_s=-A_0f_b\) and \(m_s=m_b+(A_0^Te_s)\times f_b\) in the declared Log basis.
Away from the constraint, fixed-multiplier work and curvature differ. This
identity does not select either law or permit mixing their multiplier bases.

## Supported primal operator required before a compliance quotient

For a conservative virgin elastic reference state with zero attachment
multiplier, partition the actual assembled
native tangent between physical nodal/cell-rotation coordinates \(x\) and
retained generalized-resultant coordinates \(p\):

\[
H=\begin{bmatrix}H_{xx}&H_{xp}\\H_{px}&H_{pp}\end{bmatrix}.
\]

If \(H_{pp}\) is invertible on its stated local domain, certify the exact
stationary reduction
\(K_{\rm phys}=H_{xx}-H_{xp}H_{pp}^{-1}H_{px}\).
Here \(x\) includes native retained **cell rotations**, while \(p\) contains
generalized resultants only. Prove that the L1 line action has no \(p\) columns,
then verify its full-retained compliance equals the reduced physical
compliance on a bounded coupled fixture. An existing bounded check for an
earlier law eliminates cell rotations together with resultants; its effective
trace and direct retained-compliance term do not prove this L1 partition.
If it is singular, derive a constrained reduction and its compatibility
conditions explicitly. Include the actual E4 shell block, supports and
physical nullspaces. A drilling spring, invented inertia or global dense
inverse is not an admissible repair.

On the supported physical space modulo *proved* zero-energy motions, require
\(K_{\rm phys}\) to define positive work for this particular conservative
assessment. A failed positivity proof leaves the compliance metric undefined;
it does not, by itself, prove the native mixed formulation has failed. The
line action must annihilate every true unrestrained zero-energy motion; if
\(B_hn\ne0\) for such a motion \(n\), its compliance is unbounded and a
pseudoinverse must not assign it a finite value. The
full indefinite native tangent may compute the same action compliance through
a solve only **after** this reduction, trace restriction and nullspace
equivalence are certified. Plastic active states and nonconservative follower
states are outside this quotient.
Loaded nonzero-multiplier states also lie outside this positive-work quotient
until their \(\lambda\cdot D^2c\) curvature, chart transformations and an
appropriate stationary energy interpretation have been derived separately.

For an integrated line multiplier basis \(\Psi_h\), construct its work map
from the actual E4/B3 pose derivatives and segmented reference quadrature:

\[
B_h=\int_{\Gamma_0}\Psi_h^T D_h\,dL_0,
\qquad \delta W=\lambda_h^T B_h\delta x.
\]

The B3 trace includes nodal and retained cell-rotation variations but no
invented multiplier action on the internal resultant coordinates. Define
physical force/moment and translation/rotation scales once, including beam
section arms, and verify equivalent-unit covariance. Check the transpose map
against integrated interface force, moment about a common origin and virtual
work. Separate exactly unsupported multiplier rows from low but physical
compliance; do not infer either from a raw mixed-unit singular value.

## Reference-relative metric, if the prerequisites pass

With a support/nullspace basis \(P_h\) justified by the physical energy,
define the candidate compliance on the same interface action:

\[
C_h=(B_hP_h)(P_h^TK_{\rm phys,h}P_h)^{-1}(B_hP_h)^T.
\]

Construct a converged same-law reference operator on the **same** geometry,
supports, physical line length, six-channel units and applied multiplier
action. Specify a work-preserving injection \(J_h\) into its interface space,
giving \(C_{\rm ref,h}=J_h^TC_{\rm ref}J_h\). The reference must converge on
the action subspace under at least three systematic levels (a base and two
successive refinements). Those levels are necessary, not sufficient: before a
formal run, freeze a candidate-independent bound on reference-compliance error
in the six-channel physical work norm and an executable rule for establishing
it from those levels or further levels. Two levels or a full-face weld do not
make a same-law reference. The external all-shell
flat-bar/T models are separate engineering-fidelity comparisons unless their
connection and work maps are shown equivalent.

"Work-preserving" has an executable meaning on the **entire admitted**
multiplier-action and physical virtual-field spaces. Here \(T_h\) must be a
specified support-preserving map from every candidate physical virtual field
to a reference physical virtual field on the same material geometry. It must
transport shell position/director variations and native beam pose/retained
cell-rotation variations; the stationary generalized resultants are not
independent physical fields. Derive its interpolation and trace restrictions
from the two discretizations, rather than fitting it to a candidate response.
Then establish \(J_h^TB_{\rm ref}T_h=B_h\), or freeze a uniform bound on
\(J_h^TB_{\rm ref}T_h-B_h\) in declared physical energy and dual-work norms,
including supported nullspaces. Checks on selected patches alone do not
establish this identity. A bounded straight virgin Q4/native-B3 construction
now maps every supported shell nodal coordinate by bilinear interpolation,
native nodal coordinates by station interpolation, and each fine retained
cell rotation from its containing coarse half-cell. Generalized resultants
remain stationary algebraic variables. Together with the complete A/B
multiplier-basis injections, the entire assembled six-channel action satisfies
\(J_h^TB_{2h}T_h=B_h\) to at most \(8.4\times10^{-17}\) absolute on the
tested 2→4 and 4→8 nested straight grids; supported fields have zero fixed
or resultant-row leakage. Its independently derived virgin gap Jacobian
matches the actual connection-update Jacobian exactly at the tested 2- and
8-edge stations. The executable source and focused tests are
`scripts/b3_e4_f03_l1_physical_injection.py` and
`tests/test_b3_e4_f03_l1_physical_injection.py`. This is development evidence
for those grids only: nonmatching ratios, curved references, finite rotations,
physical energy/norm acceptance, reference convergence and independent
review remain open.
The companion actual-operator check
`scripts/b3_e4_f03_l1_physical_energy_map.py` reduces only the stationary
generalized resultants and verifies positive supported virgin operators on
these bounded grids. The maximum generalized energy ratios of the pulled fine
operator to the coarse operator are 13.44 and 20.69 for the E4 shell block at
2→4 and 4→8, and 4.0 for the native beam block at both doublings; minimum
ratios are one within rounding. Whole-space near-isometry therefore cannot
be assumed from exact work transport. These worst-mode ratios do not establish
reference convergence on the multiplier-action subspace and are not F03
acceptance scores. The proposed norm/error contract still requires derivation
and independent review. A separate read-only development review found no
correctness blocker in this bounded map or p-only stationary reduction; it
identified a candidate-independent, uniform same-law reference-compliance
error bound on the full admitted multiplier-action space, with action-gauge
compatibility, as the next indispensable mathematical result. This review does
not accept F03 or set its thresholds. Define
\(J_h\) by physical traction/couple
density, orientation, line measure and units; verify basis-change and
equivalent-unit covariance. An arbitrary rescaling of even one untested
multiplier mode is forbidden because it would rescale the quotient without
changing candidate mechanics.

An independent mathematical review identifies a strict limit on the present
reference evidence. Let \(A_f=B_f^TJ\) be the complete fine-grid action and
\(A_c=T^TA_f\) its exactly transported coarse action. Even for positive
physical operators, with \(G=T^TK_fT\), the compliance difference decomposes as
\[
A_f^TK_f^{-1}A_f-A_c^TK_c^{-1}A_c
=\underbrace{A_f^TK_f^{-1}A_f-A_c^TG^{-1}A_c}_{\text{nonnegative Ritz gain}}
+\underbrace{A_c^T(G^{-1}-K_c^{-1})A_c}_{\text{indefinite consistency defect}}.
\]
The measured non-isometry leaves the second term uncontrolled. More strongly,
three apparently converged levels do not bound the unobserved tail even if
\(G=K_c\): take \(V=\ell^2\), \(K=I\), three nested reference spaces that
contain \(e_1,e_2\) but omit \(e_M\), and the same physical action
\(A(a,b)=a e_1+b(\varepsilon e_2+e_M)\). All three observed compliances are
\(\operatorname{diag}(1,\varepsilon^2)\), while the complete-space compliance is
\(\operatorname{diag}(1,1+\varepsilon^2)\). The relative missed work in the
second action is \(1/\varepsilon^2\), unbounded as \(\varepsilon\to0\).
This is a mathematical counterexample, not a finding that the E4/B3 model has
that hidden mode. It means three-grid agreement, exact work transport, and
the existing 2→4→8 energy maps cannot justify a formal uniform reference
error bound or a candidate score.

The quotient remains a useful diagnostic if its positivity and gauge contract
hold. Formal reference-compliance assessment would require a
candidate-independent same-law enclosure \(L\preceq C_*\preceq U\) on the
complete admitted action space modulo a proved physical gauge, with a
precommitted bound on
\(\sup_{\lambda\notin\ker L}\lambda^T(U-L)\lambda/\lambda^TL\lambda\).
The enclosure needs a guaranteed residual/dual majorant or another proved
tail estimate; differences between a few discrete levels are diagnostics,
not that certificate. If no certificate can be justified, keep the quotient
developmental and independently review a direct physically normed mixed
assessment instead. The separate physical transfer, locking, ratio,
refinement, and mixed-system requirements remain in force.

The bounded straight, supported 2→4 and 4→8 development screen evaluated
this split on the complete A+B density span and each candidate space. The
union has a numerically null coarse action that becomes nonzero after
refinement; A and B separately remain numerically full row rank. This warns
against treating the union's coarse model as an adequate reference and does
not demonstrate an unsupported A or B row. Within each individual space, the
largest Ritz gains are 0.812–0.919 of fine compliance, while the most negative
consistency eigenvalues are −0.748 to −0.946; coarse/fine relative compliance
eigenvalues span 0.312–1.492. Opposing terms can mask error. Independent
read-only review found the split and union basis correct on these fixtures,
but numerical near-nulls are not gauge proofs and these finite-grid spectra
are not a continuum-tail certificate. Further grid sampling is not the next
discriminator. First derive whether a computable nonconforming consistency
bound and guaranteed Ritz-tail majorant are feasible for the declared E4/B3
law. If not, keep this quotient developmental while a physical multiplier
norm and signed mixed-system criterion are prospectively reviewed; neither
route may silently replace registered transfer or convergence checks.

With justified positive supported-space bases \(P_{\rm ref}\) and \(P_h\),
identify \(N_{\rm ref}=\ker(P_{\rm ref}^TB_{\rm ref}^TJ_h)\) and
\(N_h=\ker(P_h^TB_h^T)\). Verify that each reference action annihilates any
unrestrained reference zero-energy motion before assigning finite compliance,
then prove \(N_{\rm ref}\subseteq N_h\). Let \(N_{\rm ref}=\ker C_{\rm ref,h}\)
mean this proved exact gauge, not a
thresholded collection of small positive eigenvalues. Certify the gauge
algebraically or with a justified numerical error bound; retain near-null
positive modes in the quotient and report their uncertainty. The
quotient

\[
q_h=\inf_{\lambda\notin N_{\rm ref}}
\frac{\lambda^TC_h\lambda}
     {\lambda^TC_{\rm ref,h}\lambda}
\]

is well defined on \(\Lambda_h/N_{\rm ref}\) only if every reference-gauge
action is also a candidate gauge action. An extra candidate null direction
with positive reference work gives \(q_h=0\) and is an unsupported mode.
The quotient is diagnostic for relative work compliance, not a complete
mixed-system well-posedness theorem. Retain independent primal equilibrium,
constraint, locking, physical transfer, tangent and solution-convergence
checks across all seven registered ratios and growing spaces.

The independent review must fix, **before candidate scores are examined**,
the physical reference construction, injection, support/nullspace policy,
relative and absolute numerical floors, reference-convergence rule, and
acceptance threshold justified by approximation/engineering requirements and
independent controls. No observed candidate value may set its own threshold.
Binary64 is admissible where a justified error bound supports it; exactness
remains required for a claim that mathematically depends on exact rank.

## Direct physical multiplier norm: reviewed obstruction and conditional route

The same-law reference route above remains mathematically open: no guaranteed
tail/consistency enclosure has been derived for the native E4/B3 pair. A
candidate-independent multiplier norm was examined instead. Independent
mechanics review found a **concrete continuity obstruction for the current
unsmoothed L1 law**, so the norm below is conditional mathematics, not an
adopted F03 criterion or authority to score A/B.

At the straight virgin reference, the shell normal-spin variation contains
the longitudinal slope of top-line lateral displacement. For a segmentwise
constant normal-moment density \(m_z\), its shell work includes
\(m_z\int_a^b\partial_s u_{\rm top,y}\,ds
=m_z(u_{\rm top,y}(b)-u_{\rm top,y}(a))\). An E4/Reissner–Mindlin shell has
an \(H^1\) surface displacement, whose zero-width line trace is only
\(H^{1/2}\); point evaluation on that line is not bounded by shell energy.
The current P0 normal-moment channel therefore lacks a mesh-uniform
work-continuity bound in the proposed global \(H^{-1/2}\) density norm. A
broken native B3 half-cell rotation also cannot simply be treated as a
global \(H^{1/2}\) trace. This is a **law/space regularity finding**, not a
numerical failure of A/B, and neither a small discrete residual nor an
algebraic KKT inertia check repairs it.

One targeted law correction to derive is a *physical positive-width shell
rail*: average top-surface position and director across a frozen transverse
kernel \(\rho_w\), then form the objective projected material-line triad from
that averaged position and director. For
\(\bar u(s)=\int\rho_w(y)u(s,y)\,dy\), Cauchy–Schwarz gives
\(\|\bar u\|_{H^1_s}\le\|\rho_w\|_{L^2_y}\|u\|_{H^1_{s,y}}\). Hence
\(\int m_z\partial_s\bar u_y\,ds\) is bounded for an L2 moment density.
This estimate assumes a fixed product strip inside the physical shell, a
material kernel independent of \(s\), and supported E4 energy controlling
the relevant shell displacement/director \(H^1\) fields. A curved or varying
strip needs its Jacobian and kernel derivatives in the proof. Normalize
\(\int\rho_w\,dy=1\) in material measure to preserve rigid translations;
average the actual top-surface position including thickness/director arm.
The averaged director and its projected longitudinal tangent need uniform
nondegeneracy, and the relative Log needs an admitted chart. An L2 multiplier
pairing also needs a mesh-uniform L2 bound for the *broken native B3 pose*
from its stationary-reduced physical energy.
Positive transverse width alone does not bound the point value of the
longitudinal slope \(\partial_s\bar u(s_0)\) by the shell H1 norm. A
single-station rail operator is a derivative/work prototype only; the
regularity argument applies to its material-line integral against an L2
moment density, with the declared longitudinal measure and segmentation.
An implementation evaluates only a compiled finite-dimensional multiplier
field at quadrature stations: generic L2 equivalence classes have no defined
point values. Quadrature-defined discrete work therefore needs its own
basis, integration-error and mesh-uniform work-continuity checks before the
continuum L2 estimate can support an F03 assessment.
The assumed E4 physical-energy control of shell H1 is **false for the
unrestricted growing P0 yaw space on the tested Q4 family**. With two
transverse cells, nodal lateral profile (1,-1,1) has zero mean on each
cell but average -1/2 over the fixed central strip. On longitudinal cells
of size h, use alternating nodal amplitudes 0,h,0,h,... and a matching
unit P0 yaw density. The genuine membrane shear has zero projection onto
the physical core's element-constant shear-stress mode; remaining transverse
strain gives physical energy O(h²), while integrated rail work stays 0.25
on the fixed half-length line. Actual E4 physical-core energies at
h=1/4,1/8,1/16 are 6.579e9, 1.645e9, and 4.112e8 J. Virgin gaps and
drilling loads vanish. The executable negative case is
test_physical_core_does_not_uniformly_control_alternating_yaw_density;
raw output is retained in
.qualification/b3-ge-e4-pl/r7-f03-growing-rail-dev-20260928-v1/.
This disproves the proposed *physical-core* uniform L2 continuity for that
admitted density family. It does not establish failure of every prospective
space or of the complete connection. The PL term can penalize in-plane curl
through numerical drilling completion, while the drill-only hourglass term
does no work on this zero-drill field. Neither supplies the missing physical
membrane-shear proof. A restricted, still-growing multiplier space needs an
independent whole-space bound and physical transfer checks before use.

In the conditional continuum H1 estimate, uniform width \(w\) gives a factor
growing as \(w^{-1/2}\), so width must be
a declared positive physical connection measure, not a mesh-dependent tuning
parameter. This candidate changes the shell-side trace and must re-pass
objectivity, stress-free reference, derivatives, torque/shear, topology,
work, locking and matched-reference checks. A zero-width law with a smoother
normal-moment space and controlled endpoint/jump terms is another theoretical
possibility; it is not selected. Neither proposal may silently change the
required six-channel physics or substitute a rigid footprint for a line.

The rail is a separate finite-kinematic connection law on E4 nodal
coordinates, not an exact sampling of an existing finite Q4 interior
director field. Q4 E4-PL retains additive von-Karman/Mindlin mechanics; its
corotational wrapper uses physical nodal `Exp(rotation)` to pull the nodal
state into a small-deformation element response, but the owner exposes no
unique finite interior top-surface/director update map. A bounded flat-Q4
check using the actual E4 shape functions and longitudinal derivatives
establishes first-order agreement of the rail top-position and complete
projected frame variations at the virgin state, including the correct
transverse-rotation signs and no drilling term.
Finite agreement with an owner interior field must not be claimed without
first defining that field. The rail instead requires its own finite work,
derivative, physical transfer, chart, polarity, topology and domain checks.

On one material line of length \(L\), let \(\xi=s/L\in[0,1]\), freeze a
positive force scale \(F_*\) and length scale \(\ell_*\), and convert each
six-channel multiplier density through the *actual reference-state dual pose
map* to a spatial force density \(f\) and couple density \(m\) about the
shell rail in the reference configuration. This conversion includes the eccentric lever arm and
the Log-coordinate covector map; a raw rotation multiplier is not necessarily
a physical moment. At the straight virgin reference, the work-conjugate
conversion is
\[
f=R_{s0}\lambda_t,\qquad
m=R_{b0}\lambda_R+(r_{b0}-r_{s0})\times f,
\]
for the virgin pose law's spatial resultant **about the shell rail**. The
shell-side physical residual is \((-f,-m)\); the beam-side residual is
\((f,R_{b0}\lambda_R)\) about the beam port. This follows from the actual
reference pose Jacobian, including the Log derivative, and has been checked
for eccentric, rotated, origin-shifted joints. It is not a finite-motion or
curved-line transport law.
In one fixed reference frame, set
\[
\hat\lambda(\xi)=
\begin{bmatrix}L f(L\xi)/F_*\\ L m(L\xi)/(F_*\ell_*)\end{bmatrix},
\qquad W_*=F_*\ell_*.
\]
Let \(d=r_{b0}-r_{s0}\). For spatial left-multiplicative port variations,
define the reference relative variations **about the shell rail** as
\(\delta u_{\rm rel}=\delta r_b-\delta r_s-\delta\theta_b\times d\) and
\(\delta\theta_{\rm rel}=\delta\theta_b-\delta\theta_s\). They are not the
raw material translation and Log-gap components. The pose-law virtual work
then satisfies \(W_*^{-1}\delta W=\int_0^1\hat\lambda\cdot
(\delta u_{\rm rel}/\ell_*,\delta\theta_{\rm rel})\,d\xi\).
The frame, line measure, units and
support interpretation must be frozen across candidates; a curved line needs
a separately verified objective frame transport. Junction branches and loops
need their own explicitly joined or periodic norm contract.

For a straight line, propose the componentwise spectral dual norm
\[
\|\hat\lambda\|_{-1/2,N}^{2}
=\sum_{k=0}^{\infty}
\bigl(1+(k\pi)^2\bigr)^{-1/2}
\left\|\int_0^1\hat\lambda(\xi)\phi_k(\xi)\,d\xi\right\|_2^2,
\quad \phi_0=1,\quad \phi_k=\sqrt2\cos(k\pi\xi)\ (k>0).
\]
This is a declared Neumann spectral \(H^{-1/2}\)-type norm, not a norm
constructed from the candidate compliance. It is **not suitable as a
six-channel F03 norm for the current unsmoothed law or the proposed rail yaw
channel**. It is retained here solely as a rejected norm design and algebraic
control; do not score A/B with it. Even after width averaging, take
\(\bar u_n=\sin(n\pi s)/(n\pi)\) and \(m_n=\cos(n\pi s)\): shell \(H^1\)
norm and yaw work stay order one while the spectral \(H^{-1/2}\) norm of
\(m_n\) tends to zero. The derivative channel instead needs at least an L2
density norm under the stated rail regularity. Its compatibility with native
broken B3 traces and the other five channels still requires proof. For piecewise
P0/P1 densities, exact polynomial integration gives
the L2 Gram \(M_0\) and the first \(N+1\) Fourier coefficients. In exact
arithmetic, Parseval gives the candidate-independent Loewner enclosure
\[
M_N\preceq M_{\Lambda}\preceq
M_N+\bigl(1+((N+1)\pi)^2\bigr)^{-1/2}M_0.
\]
Any numerical implementation must separately bound quadrature/roundoff and
check that the enclosure is tight enough *before* scoring candidates. This
certifies the proposed norm evaluation, not continuum stability.

For the supported positive virgin physical operator already defined, let
\(C_h=B_hK_{\rm phys,h}^{-1}B_h^T\) on its proved physical support space.
In a common coefficient basis, the direct discrete inf-sup candidate is
\[
\beta_h^2=\inf_{\lambda\ne0}
\frac{\lambda^TC_h\lambda}
     {W_*\,\lambda^TM_{\Lambda,h}\lambda}.
\]
The norm is fixed by physical line density, not by \(C_h\). An analytically
redundant density basis may be quotiented by an exact basis map; a nonzero
physical density in \(\ker B_h^T\) is instead an unsupported interface mode
and must produce \(\beta_h=0\). The upper Gram enclosure gives a conservative
lower bound on \(\beta_h\); its accuracy must be reported. Basis changes and
equivalent units must preserve the result. No threshold is set by the current
A/B values, and finitely many positive \(\beta_h\) values do not prove a
uniform asymptotic bound.

For a *corrected* positive-width rail, a simpler prospective metric uses the
physical six-channel L2 density Gram
\(\lambda^TM_{0,h}\lambda=\int_0^1\|\hat\lambda\|_2^2d\xi\).
Only if the complete shell and broken-beam work maps satisfy mesh-uniform
energy-to-L2 trace bounds on the *prospectively admitted spaces*, test **both**
\[
\beta_{0,h}^2=\lambda_{\min}(C_h/W_*,M_{0,h}),
\qquad
\gamma_{0,h}^2=\lambda_{\max}(C_h/W_*,M_{0,h}).
\]
The second is the work-continuity check that the rejected H^{-1/2} proposal
missed. A meaningful refinement claim needs a prospectively justified common
positive lower bound for \(\beta_{0,h}\) and finite upper bound for
\(\gamma_{0,h}\), not just nonzero finite-grid values. Exact L2 Gram integration is straightforward for piecewise P0/P1
densities, but the multiplier-to-physical-wrench map, E4/B3 trace bounds,
mesh-ratio behavior, tolerances and independent threshold are still missing.
The bounded growing-segment implementation now compiles P0 or continuous P1
coefficients per six-channel component. With station interpolation \(D\) and
reference Gauss weights \(Q\), its raw-coordinate Gram is \(D^TQD\);
two interior Gauss points per segment integrate P0/P1 products exactly.
Its projected constraint rows are \(D^TQ g_6\), conjugate to the same
coefficient vector used for station work. This establishes a finite discrete
pairing only: \(D^TQD\) is **not** \(M_{0,h}\) until the reference-state dual
pose-to-physical-wrench conversion and frozen force/moment scales are applied.
For a proven constant reference dual map \(T\) on a straight rail with
\(N\) sampled Gauss stations,
let \(\mathcal T=I_N\otimes T\),
\(\mathcal S=I_N\otimes\operatorname{diag}(F_*^{-1}I_3,
(F_*\ell_*)^{-1}I_3)\), and
\(Q=\operatorname{diag}(w_iI_6)\). The exact mapped physical L2 Gram is
\(M_{0,h}=L D^T\mathcal T^T\mathcal S^TQ\mathcal S\mathcal T D\).
Its P0/P1 product integrals are exact under that constant-map condition;
the reference line, scales, and shell-rail wrench origin are frozen across
candidate spaces. The current implementation checks equality of sampled maps
only, which does **not** prove constancy between stations: its
returned matrix is a sampled physical **quadrature Gram**, not yet the
exact continuum \(M_{0,h}\). A whole-segment reference geometry/port contract
or controlled map-integration error is required before that identification.
This is a development norm construction, not an accepted F03 threshold or a
mesh-uniform trace result.
The same quadrature is not automatically exact for nonlinear density-gap work;
its integration error needs a separate check. An independent read-only review
found no algebra or factory-ownership defect in this bounded construction.
If this common L2 norm proves too strong for a channel, derive its actual
trace dual *before* inspecting A/B scores; do not tune channel weights to
rescue a candidate. A finite set of positive generalized eigenvalues does
not prove uniform stability or physical fidelity.

### Native broken trace: a conditional mesh-independent route

For the straight virgin retained B3 chain with root translation and rotation
fixed, let half-cell lengths be \(h_i>0\), \(\sum_i h_i=L\). Write nodal
translations \(u_i\), nodal spins \(\omega_i\), and retained half-cell spins
\(\theta_i\). The actual operator's linearized kinematic rows are
\[
z_i=u_{i+1}-u_i-\theta_i\times(h_i e_1),\qquad
\ell_i^-=\theta_i-\omega_i,\qquad
\ell_i^+=\omega_{i+1}-\theta_i.
\]
The native off-diagonal Hessian block agrees with this independent map on
the bounded 4/8/16-half-cell straight fixtures; this establishes the
kinematic identity there, not an energy estimate. Set
\[
A_h=\sum_i |z_i|^2/h_i,\qquad
B_h=\sum_i (|\ell_i^-|^2+|\ell_i^+|^2)/h_i.
\]
Since \(\omega_{i+1}-\omega_i=\ell_i^-+\ell_i^+\) and \(\omega_0=0\),
Cauchy--Schwarz gives \(\max_i|\omega_i|^2\le 2LB_h\) and
\(\sum_i h_i|\theta_i|^2\le 6L^2B_h\). Using
\(u_{i+1}-u_i=z_i+\theta_i\times h_ie_1\) and \(u_0=0\), the piecewise
linear translation satisfies
\[
\int_0^L |u_h|^2 ds\le 2L^2A_h+12L^4B_h.
\]
Thus the broken pose trace is uniformly L2-bounded **if** the actual
stationary-resultant physical energy has an \(h\)-independent coercivity
bound \(q^TK_{\rm phys,h}q\ge c_AA_h+c_BB_h\), with positive physical
\(c_A,c_B\). The cases below establish that inequality for affine-straight
virgin generalized sections; other admitted section/reference families need
their own argument. The finite-grid quotient plateau alone did not prove it.
Curved lifts, nonuniform frames, free components and loaded plastic states
need separate hypotheses; none follows from this straight virgin lemma.

For an **affine straight reference within each three-node element** (constant
Jacobian and frame), virgin zero-resultant state, and **constant diagonal
generalized section**
\(C=\operatorname{diag}(C_t,C_r)\), the local complementary calculation
supplies the missing bound. The cell's station-force constraint is a
quadrature-weighted mean; its minimizing translational force is constant.
Its rotational resultant interpolates as
\(M(t)=(1-t)M^-+tM^+\). With order-four quadrature exact on these quadratic
products, the cell compliance is
\[
H_{\rm cell}=\operatorname{diag}\!\left(
 h C_t^{-1},\;\frac h6
 \begin{bmatrix}2&1\\1&2\end{bmatrix}\!\otimes C_r^{-1}\right).
\]
Its inverse gives translational strain stiffness \(C_t/h\) and rotational
endpoint-strain stiffness
\(\frac1h\begin{bmatrix}4&-2\\-2&4\end{bmatrix}\otimes C_r\).
The latter has weighted eigenvalues 2 and 6; the former has ratio 1 to the
canonical weighted \(A_h\) term. Thus the assembled root-supported virgin
straight operator obeys the required bound with its declared physical
section weights, independently of the number and positive lengths of
affine three-node elements (each with equal half-cell lengths).
The independently assembled closed form matches the actual stationary
native operator on 4/8/16 bounded fixtures to approximately \(10^{-16}\)
relative matrix error. These numerical checks corroborate the local
calculation; they are not the reason it holds for arbitrary positive element
lengths with an affine midpoint and equal half-cell lengths within each
three-node element.

The same virgin affine-straight kinematics admit **constant coupled SPD
generalized sections** by a physically scaled Loewner comparison. If
\(C\succeq\alpha C_{\rm ref}\) for a declared diagonal work-coordinate
reference and dimensionless \(\alpha>0\), then
\(C^{-1}\preceq\alpha^{-1}C_{\rm ref}^{-1}\). Minimization over the
unchanged constrained station-force set preserves this complementary
compliance order, and inversion gives
\(K_{\rm phys}(C)\succeq\alpha K_{\rm phys}(C_{\rm ref})\) on the
supported physical strain space, even with force--moment coupling. This
supplies an \(h\)-independent straight-chain bound whenever the registered
section comparison \(\alpha\) is bounded below. Independent mechanics
review found the derivation valid under these exact hypotheses.
The result does **not** cover a straight but non-affinely parameterized Q2
reference with varying Jacobian, curved lifts, physical fibres, loaded
geometric stiffness, plastic history, or the shell-side rail estimate.
Those require separate derivation and checks before F03 acceptance.

For the virgin symmetric native system, exact stationary elimination of
negative-definite generalized-resultant block \(H_{pp}\) makes the supported
KKT congruent to a physical saddle system with \(K_{\rm phys}>0\). With an
independent multiplier-density basis and full-row-rank \(B_h\), that system
has inertia \((n_x,n_p+n_\lambda,0)\); a zero or unexpected sign requires
investigation. This algebraic check is distinct from the norm-scaled inf-sup
and from solution convergence. At nonzero multipliers, include constraint
curvature and actual chart/load derivatives; the virgin positive-work
argument cannot be reused to label a physical limit-point instability as an
interface defect. Keep physical transfer, locking, seven ratios, growing
spaces, three refinements, and full mixed-system checks mandatory.

Before any formal use, independent review must first accept a corrected
continuous law and a mesh-uniform work-continuity bound, then decide its
correct multiplier norm, numerical floor and prospective stability threshold.
Controls must include constant/linear densities,
checkerboards, exact and near-null actions, basis rescaling, equivalent units,
rigid modes, broken B3 traces and loaded signed KKT counterexamples. If the
trace regularity or threshold cannot be justified, this route stays
developmental and F03 remains open.

## Mandatory adversarial controls and terminal use

The assessment must reject these failure patterns: a raw indefinite matrix
such as \(H=\operatorname{diag}(1,-1)\) interpreted as a positive energy norm
without its physical stationary reduction (the reduced physical block in
this example is positive and must not be rejected merely because \(H\) is
indefinite); a
zero-energy loaded direction hidden by a pseudoinverse; a reference-null
action whose candidate work makes the quotient representative-dependent; and
a full-row-rank candidate whose relative compliance floor tends to zero under
refinement. It must reject an arbitrarily rescaled reference injection or a
thresholded near-null mode that fabricates a gauge. In particular,
\(J=\operatorname{diag}(1,\varepsilon)\) must fail a whole-space work check
even if the registered patch excites only its first component. It must also detect
checkerboards, excessive multiplier density,
locking, artificial drilling transfer and a line law that suppresses admitted
transverse shear. A physically admissible compliant mode is assessed by work,
transfer and convergence, not rejected from one small quotient alone.

Until the prerequisites and independent review pass, the decision is
**F03 open; formal assessment barred**. A failed candidate or undefined metric
remains visible. It does not authorize a penalty substitute, automatic row
deletion, a narrower mesh-ratio envelope or G0/G1 acceptance.

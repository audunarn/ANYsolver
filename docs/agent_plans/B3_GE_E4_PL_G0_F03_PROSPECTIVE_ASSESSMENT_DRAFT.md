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

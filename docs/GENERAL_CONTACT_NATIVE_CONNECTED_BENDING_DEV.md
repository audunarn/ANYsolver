# Connected native transverse bending development reference

**Disposition: V4 successor source prepared; its numerical checks and CLI are UNEXECUTED.**
Historical V3 work/phase2PASS and response1FAIL evidence is retained below.
No production file, existing authority or accepted profile is changed. This is a
new independent check of the existing connected contact-free native route. It
confers no C7 acceptance, general section admission or contact capability.

## Declared fixture and meaningful horizon

Two straight native elements share node30; node IDs are10/20/30/40/50 and four
half-cells have reference length ell=.5m. Positions are
(.25,-.5,.125)+i*ell*(1,0,0), with identity reference nodal/cell frames and exactly
zero half-cell lift. Only the first node has the existing full homogeneous clamp.
The generalized elastic matrix is diagonal
(100000,30000,30000,30,20,10), in the existing section's declared units. The
section class is a generalized law, not a claim about a geometric cross-section.
The independently declared inertia is diag(2,2,2,.02,.01,.01); the planar z spin
uses Jz=.01 and retains positive physical cell inertia ell*Jz. Algebraic nodal
frames have no inertia. There are no loads, damping, contact or hidden supports.

Initial physical displacement is the lowest simple transverse/bending eigenmode
of the independently assembled rest M/K after GLOBAL algebraic frame elimination.
Its tip is positive, maximum nodal transverse displacement is AMP=2^-20m, and its
initial physical velocity is zero. The simple-mode relative spectral gap must
exceed1e-8. This excludes silently selecting a tied eigenvector. Eigenvalues and
inputs have not been evaluated. Independent modal cell angles accompany nodal
translations; rotations are not artificially clamped.

Choose ideal dt=.05/omega1, round DOWN to a dyadic21-bit mantissa, and take four
steps. This yields approximately.2rad of modal phase, not.2rad of physical rotation.
The fixed test requires.199<omega1*T<=.2. Dyadic rounding permits exact four-step
controller timestamps and the fresh4=2+2 restart comparison without a different
integration algorithm. The actual physical angles must remain below.001rad.
The helper independently checks that its prospective energy box implies this
logarithm-branch bound. The small physical angles are explicit; finite-angle
bending breadth remains open.

## Actual affine half-cell work, not a textbook Q2 beam

For cellc let u,w be axial/transverse nodal translations, phi its retained physical
cell z rotation and theta the algebraic nodal z-frame angles. Define

    d=(ell+uR-uL,wR-wL)
    z=Rz(-phi)*d-(ell,0)
    b=(phi-thetaL,thetaR-phi).

These are the native compensated chord strain and signed retained relative-frame
rotations on the declared commuting plane. Reference station measure is fixed.
The local complementary elastic work is

    Psi*=ell*N^2/(2EA)+ell*V^2/(2GA)
         +ell*(ML^2+ML*MR+MR^2)/(6EI).

Its moment inverse compliance is

    (2EI/ell)*[[2,-1],[-1,2]].

Eliminating N,V,ML,MR gives the compatible physical potential

    Ucell=(EA*zx^2+GA*zy^2)/(2ell)
          +.5*b.T*(EI/ell)*[[4,-2],[-2,4]]*b.

Shared theta values are eliminated once globally, with theta0=0, using the
assembled9x9 bending matrix (theta5+phi4). This reference elimination removes
only massless algebraic variables. Production retains all nodal frames,
resultants, physical cell rotations and physical mass. The condensed4x4 cell
angle matrix is SPD under the full first-node frame clamp. Root conjugate couple
is -ML of the first half-cell, even though the clamped frame has zero inertia.

The reference evaluates exact trigonometric planar work and analytic first/second
variations. It avoids axial cancellation using

    zx=-2ell*sin(phi/2)^2+cos(phi)*(uR-uL)+sin(phi)*(wR-wL)
    zy=-ell*sin(phi)-sin(phi)*(uR-uL)+cos(phi)*(wR-wL).

This is an arithmetic rearrangement of the same work, not a strain truncation.
The rest tangent uses g=wR-wL-ell*phi and the same assembled frame elimination.
The generic quadratic bar/Euler beam assumption is not used. Each half-cell has
consistent affine P1 translation mass

    rhoA*ell/6*[[2,1],[1,2]],

and independent cell spin inertia ell*Jz. Zero lift and centered diagonal inertia
remove translation-spin cross mass, not the spin inertia. The work test compares
ALL27 physical coordinates: independent3D P1 node translation blocks and each
cell ell*Rz(phi)*diag(.02,.01,.01)*Rz(phi).T. Translation(kg), spin(kg m^2), and
cross(kg m) errors have separate input-derived scales. Rotated x/y off-diagonal
spin entries also use the positive ell*|Jx-Jy|*max|initial phi| scale so tiny
angles cannot hide an omitted inertia orientation. Algebraic mass is exactlyzero. Reflection
symmetry leaves the other physical directions zero; tests check those full vector
components and frame matrices, rather than imposing extra constraints.

## Independent endpoint, stage and support reference

The reference plane has14 physical coordinates [u5,w5,phi4]. Fix root translations
and solve the12 free midpoint equations, using a bounded20-iteration Newton method
with12 backtracking halvings:

    qstage=q+.5h*v+.25h^2*a
    Mff*a+grad(U(qstage))_free=0
    qnew=q+h*v+.5h^2*a; vnew=v+h*a.

The z rotations commute, so this scalar angle midpoint agrees with the existing
SO3 midpoint chart in the stated plane. This is a verification oracle, not a
second public solver or admission route. Native public solve_transient still
owns all initialization, trial/commit/discard, time/output control and restart.
The independent endpoint acceleration is -Mff^-1*grad(U(qnew))_free. Initial,
stage and endpoint FULL translational/spin accelerations are compared, including
nominally zero components. Native stored algebraic velocities/accelerations are
zero by descriptor convention; they are not derivatives of recovered theta.

At a stage, support translation is the ROOT ROW of M*a+grad(U), including root
consistent-mass coupling to neighboring acceleration. The root frame couple is
-ML. Moment about world0 is ORIGIN cross F plus that couple. Stage impulses are
h*F and h*moment; homogeneous root support work is exactly zero. Endpoint reaction
is checked separately and is not mislabelled an integrated impulse. Independent
momentum is integrated from P1 translation velocity and the actual positive
ell*Jz cell spins. No algebraic inertia or resultant rows become physical loads.

## Explicit nonlinear versus linear model discrepancy

The nonlinear oracle and native response are compared independently at1e-6.
The linear analytic comparator is semidiscrete, not continuum/spatial: it is the
rest lowest mode cos(omega1*t), with its corresponding velocity and acceleration.
The exact linear midpoint phase is2*atan(omega1*h/2) per step.

The helper separately derives a CONDITIONAL exact-real midpoint perturbation
bound. It constructs the rest matrices, frame elimination and inverse blocks as
Fractions. The initial binary64 mode is treated as exact input. Trigonometric
inequalities upper-bound its initial elastic work; Ebox=1.02*that upper bound is
prospective. Every measured reference/native stage must satisfy Ebox and the
planar angle limit. Energy yields bounds A=|zx|, B=|zy| and P=|phi|. Then

    U=A+ell*P^2/2+P*B; W=P*(ell+A)+B
    dX=P^2*(ell+U)/2+P*W
    dY=P*U+P^2*W/2+ell*P^3/6
    rx=(EA/ell)*dX+(EA/ell)*A*P^2/2+(GA/ell)*B*P
    rw=(EA/ell)*A*P+(GA/ell)*dY+(GA/ell)*B*P^2/2
    rphi=((EA+GA)/ell)*A*B+GA*dY.

Scatter these component bounds once per actual cell. The binary modal q and
captured binary omega are not an exact rational eigenpair: add the EXACT rational
component magnitudes of K*q-omega^2*M*q to the forcing enclosure. The modal
midpoint stage amplitude is bounded by1, so this encloses its entire eigen-defect.
It is not substituted by an arbitrary numerical comparison allowance. Separately for axial and
transverse invariant blocks, let s=sqrt(R.T*abs(Mff^-1)*R). The rest midpoint
Cayley map is an isometry in diag(Kff,Mff), and its forced resolvent has norm<=1.
Thus after horizonT, dq_i<=T*s*sqrt(Kff^-1_ii),
dv_i<=T*s*sqrt(Mff^-1_ii). The helper also bounds endpoint acceleration error.
Rational squared comparisons make each square-root and output conversion an upper
bound in exact arithmetic. This is not an interval certificate for native floating
SO3 operations. Numerical reference comparison allowance is separately1e-6 in
fixed coordinates. ACTUAL saved production q/v versus the analytical semidiscrete
mode must satisfy the unchanged.001 response gate. The worst-case nonlinear bound
plus linear phase error is a diagnostic and separate validity/code check; its
magnitude alone is not the response acceptance test. Bound diagnostics are saved
before their assertions, preserving a violated condition without rerunning. No certified floating native
response is claimed from this exact-real bound.

Stage energy checks include the independent oracle and actual stored accounting.
The public total-energy defect must be<=2% of initial independent positive elastic
energy. The linear half-dt phase check is an independent formula check, not an
executed native temporal-refinement or spatial-convergence campaign. Full C7
finite-angle, nonprincipal, nonlinear sections, spatial convergence and continuum
validation remain open.

## Frozen scales and prepared execution

Length scale is AMP; cell-angle scale is maximum absolute initial modal cell angle.
Rate/acceleration scales multiply these by omega1/omega1^2. Fixed force scale is
GA*AMP/ell N; moment scale is GA*AMP Nm; positive energy scale is the independently
computed initial elastic work. Impulse scales multiply N/Nm by actualh. These are
input-derived, never observed-error scales. Virtual directions use those physical
length/angle scales with dimensionless h=(.01,.001,.0001); work has unitsJ, residual
translationsN and rotational rowsNm. The1e-5 gates are dimensionless. Retained
force equations have length units, retained moment equations angle units.

Prepared selectors in tests/test_ge_beam3_native_connected_bending.py:

1. independent mass, complete virtual work/condensed tangent and useful h interval;
2. public four-step response, all stages/endpoints, genuine bending/spin, support,
   impulses/momentum, explicit nonlinear/linear bound and energy;
3. complete fresh4=2+2 checkpoint/journal equality;
4. independent linear midpoint modal phase refinement formula.

An adequate separately authorized execution sequence is four processes bounded
at60s each, one scientific job at a time,953MiB,JITdisabled,Numba/BLAS/native pools1,
with actual process-wall accounting and at least20s final evidence reserve.
A prospective260s ceiling is proposed, not authority and not a cost prediction.
Order local work/linear formulas first, then public response, then restart; stop
and preserve failures on a concrete obstruction. Existing verified549-payload
private installation can avoid a redundant build only after exact product byte
parity is checked. New example/test sources and command hashes must also be bound.
No numerical/import/build/install work has been performed for this slice.

Example after explicit authorization:

    python -m examples.native_connected_bending_dev --steps 4

Optional NATIVE_TRANSIENT_RESULT_RECORD records named public result dictionaries,
metrics and complete checkpoint capsules without printing large arrays. The CLI
is prepared but unexecuted. Independent review and lead acceptance remain separate.

Source review V2 corrects the retained per-element inventory (forces6, moments12),
and tests descriptor resultant rates/accelerations as exactzero separately from
nodal-frame angular rates. Actual AND independent reference stage energies must
satisfy the conditional bound's energy box. V1 snapshots/manifests remain preserved;
all revised numerical checks are still UNEXECUTED. Production formulas and
scientific thresholds are unchanged. Prospective V2 gates actual saved analytic
response, retains the conditional bound separately, and includes the exact
rational binary-eigenpair forcing residual; no executed gate is being regraded.

## V4 explicit arithmetic successor after failed response

The original V3 four-step response was executed and FAILED the1e-6 full acceleration
comparison. The trajectory completed; analytical q/v, support, impulse and energy
metrics were retained. Its raw failed evidence/source snapshots are immutable.
A saved-state-only independent diagnostic attributed initial axial acceleration
error almost wholly to tiny SO3 diagonal coefficient loss; subsequent stiff axial
pose amplification accumulated. The independent oracle, physical inputs, mode,
time/loads/scales and all scientific criteria are unchanged.

The V4 fixture explicitly selects
GE_BEAM3_CENTERED_STABLE_SO3_AND_PRECISE_WORK_DEV_V1 through the existing
arithmetic_policy definition keyword. New STABLE_SO3_V3 definition schema binds
that policy/operator identity in capture/restore and all native/trajectory restart
contracts. Old None and DECIMAL80 precise policies/defaults keep their exact paths.
This new artifact must be verified; the previous installed payload is not the new
implementation. No frozen P5 copied mechanics are edited.

For SO3 U, S=(U-U.T)/2 and c=(trU-1)/2 give the exact identity
D=U-I=S+S^2/(1+c). The near branch c>.5 has denominator>1.5 and a64eps
machine-roundoff orthogonality/determinant certificate with8eps arithmetic margin.
Otherwise use the originalU-I expression, where near-identity diagonal cancellation
is absent. A distorted matrix is not silently projected or normalized. This is an
explicit effective SO3 arithmetic interpretation, not literal rounded-matrix
bit-equivalence. Existing proper rotation and increment/relative log guards remain.

Compose E=exp(eta)-I directly with existing Jet2 Rodrigues coefficients/skew:
Dmade=Dbase+E+E*Dbase. Full frame work uses I+Dmade; strain is
change+Dmade.T*reference_chord+Dmade.T*change, retaining coordinate high/low parts.
The same expressions supply complete value/gradient/Hessian/mixed crossblocks.
Decimal80 scalar work receives the same captured Dbase and addsI only AFTER high
precision conversion; material work and all mechanics/inertia/state transactions
remain unchanged. A scalar-only correction would be inconsistent and is not used.

Additional prepared controls cover zero/arbitrary axes, both sides of the near/far
branch, distorted-base refusal, first/second Jet2 derivatives across usefulh,
definition capture/restore, old-policy byte comparison when an authentic baseline
is supplied, and explicit old/new arithmetic checkpoint incompatibility. These
controls and the V4 frozen response/work/restart require the lead's scoped260s
process-wall ledger; the author has run only stdlib source checks. No claimed
numeric PASS for V4, acceptance or resource renewal is implied by this repair.

## Executed V4/V4a development disposition

Five repaired-package focused checks and actualCLI4 now PASS. The independent
modal-phase check is reused unchanged. Full-state error3.745762628620354e-10 and
exact fresh4=2+2 restart meet the original gates. Authentic legacy definitions
match; policy mismatch refuses without mutation. V3 response and V4 test-only
authentication failure remain retained. 550 payloads/six hashed metadata and
runtime provenance verified. Total charged124.15613109998988/260s, including
conservative5.4186997s prelaunch refusal with missing exact helper-wall evidence.
This is tested development only; no broader C7/C8 acceptance or release.
[Exact evidence](d1_review_support/contact_native_connected_bending_20261006/bending_development.md).

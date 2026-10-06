# Independent physical rigid-footprint contract review V1

Date: 2026-10-06. Supporting independent OpenAI Read review; no numerical imports, runs or product edits. Root owns adoption. This reviews the proposed mathematics and an evolving prototype, not a frozen implementation or qualification. Different-model-family acceptance remains unmet.

## Conclusion and consequential prerequisite

The proposed five-row attachment is a coherent objective rigid-position/director law. Its reference differential and stated symmetric exponential-chart second variations have the correct signs. It releases attachment spin about the physical director while transferring normal torque through noncollinear position arms. **Its buckling pairing with the existing Q4 kernel needs an explicit common second-order shell chart contract before claiming a physical combined second variation.** Correct attachment derivatives alone do not establish this compatibility.

`elements.py:2531–2536,2570–2582` defines the inherited Q4 initial-stress kernel using the LINEAR director field `[u+z*ry,v-z*rx,w]`, with no drilling rows. The new attachment instead uses `Exp(theta_s)n`. A concrete counterexample at reference is `n=z`, `E=[x,y]`, `lambda_d=(ell,0)`: its constraint stress Hessian has `H[theta_sz,theta_sx]=ell/2`, despite a zero normal-spin column in C. A nonzero physical director reaction requires balancing shell first rotational work, but the existing Q4 gradient-product G cannot supply the corresponding exponential-chart contribution. A preload-dependent drilling/tilt coupling can therefore survive in the assembled pencil.

An adoptable completion must derive the shell pullback from the same continuation. In these local coordinates, linear director variables satisfy `phi=n cross d`, so the physical shell first-work gradient `m=(mx,my)` contributes symmetric chart terms `H[z,x]=my/2`, `H[z,y]=-mx/2`. These cancel the matching attachment terms when the physical gradients balance. Derive this from physical stress work, separate numerical PL/drilling stabilization, preserve the existing reference differential, and include each curvature once. Do not automatically infer the correction from total `K*u`. Alternatively, declare and enforce an initial restricted domain excluding unsupported nonzero director prestress; broader bending remains mandatory/open. A scalar total-work oracle with nonzero director reaction is the discriminating control.

## Attachment mathematics

Let `a=Xs-Xb`, `delta_u=us-ub`, `Qb=Exp(theta_b)`, `ds=Exp(theta_s)n`, with owned unit n and orthonormal tangent basis E. The functional is

`ct=Qb.T(a+delta_u)-a`, `cd=E.T Qb.T ds`.

Common finite spatial rotation/translation leaves it invariant. At zero pose,

`Dct=delta_u+skew(a)theta_b`, `Dcd=-E.T skew(n)(theta_s-theta_b)`.

For two directions `(da,sa,ba)` and `(db,sb,bb)`, the proposed D2ct and D2cd match the expansion of `Exp(-theta_b)` and `Exp(-theta_b)Exp(theta_s)n`. They are chart Hessians, not a spatial residual Jacobian. Hemisphere positivity plus `cd=0` gives `Qb.T ds=n` exactly. Normal spin freedom away from reference means rotation about the current director (or right rotation about reference n), not arbitrary additive rotation-vector increments along n.

With work `lambda_t·ct+lambda_d·cd` and exerted actions `-C.T lambda`, shell force is `-lambda_t`, beam force `+lambda_t`; shell direct couple is `-n cross (E lambda_d)`, beam direct couple is `a cross lambda_t+n cross(E lambda_d)`. Common-origin moments balance. Thus lambda_t has units N and lambda_d has units Nm; two raw director multipliers are not a Cartesian couple. The shell direct couple has zero component along n. Tangent basis changes `E->EO`, `lambda_d->O.T lambda_d` preserve work and physical actions for any orthogonal O.

## Adopted domain deltas and representation

Initial inspected prototype `_stiffened_shell_b2_physical_rigid_footprint.py:26,39,104` inherited optional empty patch membership from the old law. Root agreed this NEW family must require nonempty complete, edge-connected Q4 patch cells whose exact vertex union is selected; historical selected-node-only admission remains unchanged. Flat/coplanar and explicit host-director/seam checks, noncollinearity, no overlapping selected nodes, actual endpoint membership and supported-row independence are required. An area/rigidity theorem for unselected interiors is not implied.

Initial lines 78/87/157 used ordinary subtraction/cross products rather than the old law's compensated `_difference`/`fsum` wrench service (`_stiffened_shell_b2_nodal_footprint.py:129–146,238–246`). Root returned this for repair. Preserve cancellation accuracy for representable stored inputs, and refuse overflow, nonfinite products or unrepresentable required output. Compensation cannot reconstruct coordinate separation already rounded away by the caller. Do not impose blanket exactness, absolute floors, or tune tolerances around a specimen.

Root also specifies a separate footprint-only buckling request, rejecting POINT coexistence initially; unsupported pad batches refuse before legacy selection; no new modes admission. New row widths and both physical incidence matrices must propagate through C assembly, compatibility, provenance, recovery and spectral multiplier indexing. Legacy six-row/I defaults, POINT and old footprint request semantics remain unchanged.

## Required bounded developer controls

- Independent scalar attachment work differences against C and all mixed Hessian entries, including translation/beam rotation and shell-spin/tilt; step plateau and physical units.
- Finite common rigid path: `H[v,v]+gradient·qddot=0`, including translational centripetal acceleration. Isolated `H[v,v]=0` is not the objectivity test.
- Total physical shell-plus-attachment stress work with nonzero director multiplier, distinguishing the missing chart term above; constituent decomposition and exactly-once assembly. Include bending/director-couple cases, not only membrane or zero-multiplier fixtures.
- Normal spin path and zero normal direct couple; independent force-arm normal torque, common-origin balance, virtual work, basis rotation/reflection, node/member reversal, reference datum change and severe representable cancellation. Physical release does not remove the existing Q4 drilling stabilization or establish its qualification.
- Actual complete-patch, coplanarity/director, seam, overlap, collinearity, unsupported POINT/batch/modes and nonrepresentability refusals. Full physical KKT and full indefinite descriptor/QZ comparison; no condensed constraints or artificial inertia. Preserve failure/cancellation and repeated request/cache behavior.

Strict zero transverse-shear prestress, actual native Q4 N/M with homogeneous `N*h^2/12`, full physical member Green stress, zero prescribed u0 and Cartesian dead forces with rotational RHS zero remain governing boundaries. These do not by themselves resolve the shell chart prerequisite. Broader S3/line/interior/footprint breadth, external comparisons, refinement/spectral accuracy, installed qualification and full F12/B14 remain open. No tests ran in this review.

## Source bindings

Initial physical-footprint source actually inspected for the equations and admission findings: SHA256 `82EF69E80D8141A8AA2D239A47DC2AD9042D36F1713D4A6D2662F6655A23B031`. The owner was editing concurrently. Later hash capture was `B764FFEE6171526BBA8CF61DA359298A35D490A1B91CA5C94D652ECAAAB44C86`; repairs at that later binding were not independently re-reviewed here.

Other inspected source hash captures: nodal-footprint `5C8943D1857EF60FEDCBE3E28B768A6189D9A8C6ADBA0E17D2CFDF039D5B87A7`; Q4 panel `587DCE7B688DEB6DFB190D1E40C268E71CD83897638FC341DE772C3B51198683`; reference-buckling `D9564E411B0FB189A3D5D7F9E1C4F1B7C54AA087B91D433FE457A87E76B2B854`; inherited elements kernel `32967DD7CF4EE47D2439D4833844E0C10886C2880768F218D468844D9DA671B9`. Panel and buckling captures are evolving integration evidence, not a frozen verified slice.

## Same-review resolution of the shell chart prerequisite

Root subsequently proposed the physical tangent pullback `beta(theta)=n cross (Exp(theta)n-n)`, with `Dbeta=I-nn.T`, and correction `sum_i m_i·D2beta(theta_i)` added once to the existing tensile-sign Green G. This is a mathematically coherent completion for the declared flat Q4, fixed plane-stress, exactly-zero-Q domain. No theoretical obstruction remains to bounded developer checks of this completed contract; implementation and scientific verification remain outstanding.

The finite interpolation must be explicit:

`chi(xi,eta,z)=sum_i Ni(X_i+u_i)+z*sum_i Ni Exp(theta_i)n`.

Here nodal directors are rotated first and then interpolated. `Exp(sum_i Ni theta_i)n` is a different nonlinear field and generally creates mixed-node chart blocks; it does not justify a sum of node-local beta Hessians. Interior interpolated directors need not be unit; this declared isoparametric field is the continuum approximation being tested.

Source confirms the first-work map: `e4_pl_element.py:_compatible:2092–2099` has zero membrane rotational columns and the standard bending rotation-gradient map. `_stationary_blocks:2219–2235` couples recovered physical resultants through this same compatible map and excludes the sixth drilling slot. Thus, under exactly zero Q, `m_i` can be derived from the native recovered M through the matching bending map and quadrature. Physical director polarity, curvature order/sign and local/global transformations must be applied consistently. This uses physical stress recovery, excluding PL and drilling stabilization; it is not an inference from total K.

The independently defined frozen stress field `sigma_alpha_beta(z)=N_alpha_beta/h+12*z*M_alpha_beta/h^3` and scalar work `integral .5*sigma_alpha_beta*(chi_,alpha·chi_,beta-delta_alpha_beta)` produce the existing N/M/N*h^2/12 gradient-product terms plus this beta chart correction at reference. Four face points and two thickness points are sufficient for this prescribed quadrature and the quadratic thickness integrand. The normal component of D2director has no reference first work under in-plane plane stress and Q=0, so the tangent pullback suffices. This conclusion does not extend to nonzero shear, warped/variable reference directors or a different director interpolation.

Under a common finite rigid path, all nodal rotations and positions yield `chi(t)=R(t)chi(0)+t(t)`; scalar Green work is invariant. Its second path derivative must include the first gradient contracted with translational centripetal acceleration. Proper global frame re-expression conjugates the Hessians and preserves work. For equilibrium cancellation, compare the PHYSICAL shell first-work gradient with pad director work; numerical stabilization remains separately visible, so zero total spin coupling must not be demanded where a declared numerical contribution remains.

Required closure controls are the scalar Hessian oracle for coupled N/M, the actual native `m·delta-theta` variational identity, global-frame/director reversal, and a combined nonzero pad-director reaction example exposing both missing and double-counted chart corrections. Existing POINT and old footprint policies must retain their existing operators. E4-PL source binding for this derivation: SHA256 `A21FBCF391A6D62392F1120BBEB96F3A00ACF798ED9EB28A5676EC91EDA0604F`. No numerical control has run in this review.

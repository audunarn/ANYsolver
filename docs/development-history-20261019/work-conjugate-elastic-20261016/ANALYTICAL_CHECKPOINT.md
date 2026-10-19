# ANALYTICAL CHECKPOINT — work_conjugate_elastic_dev_v1

Date: 2026-10-16. Owner: Mistral (single connected implementation owner).
State at checkpoint: source inspection of the local laws and the corotational map
complete for Beam2 and structurally complete for Q4; no edits yet; no numerical
commands run (CONTRACT_ADOPTED.md absent). This checkpoint is delivered before
further inspection consumes budget, per brief.

## 1. Verified local elastic potentials (existing laws, unchanged)

### 1.1 Beam2 (elements.py:4577 `BeamElement.compute_nonlinear_response`)

Non-fiber, non-generalized branch (the elastic Beam2 law), with `u_loc = T u`
(`T` from `_beam_frame_and_transform` on reference coordinates):

- `eps = du/L + (dv^2 + dw^2)/(2 L^2)`, `N = EA * eps`
  (elements.py:4640-4646 region), `d_eps` its exact gradient.
- `F_loc = K_noax @ u_loc + N * L * d_eps`
- `K_loc = K_noax + EA*L*outer(d_eps,d_eps) + string terms`, `string = N/L`
  added symmetrically on ((1,7),(2,8)) pairs.

Verified potential (gradient and Hessian checked symbolically against the code):

    Pi_beam(u_loc) = 0.5 * u_loc^T K_noax u_loc + 0.5 * EA * L * eps(u_loc)^2

- Gradient: `K_noax u + EA*eps*L*d_eps = F_loc` (exact).
- Hessian: `K_noax + EA*L outer(d_eps,d_eps) + N*L Hessian(eps)`; the code's
  string terms are exactly `N*L*Hessian(eps)` on the (v,w) blocks. Exact match.
- `K_noax` is the linear stiffness (Euler/Timoshenko bending with shear
  correction `ky,kz`, torsion `GJ`) with axial row/col 0 and 6 zeroed
  (elements.py:4615-4620); the von Karman axial term replaces the linear axial
  block. Shear is therefore inside the potential. The law is a strict
  potential gradient: `f_local = grad Pi`, `K_local = Hessian Pi` (symmetric).

### 1.2 Q4 shell (elements.py:2872 `ShellElement.compute_nonlinear_response`)

Elastic shortcut branch (`not constitutive_plasticity and not has_initial_field`,
elements.py:2965-2975): `N_res = memb_strain @ (h C_el)^T`,
`M_res = curvature @ (h^3/12 C_el)^T`, `C0 = h C_el`, `C1 = 0`,
`C2 = h^3/12 C_el`. Per Gauss point (elements.py:2952-2963):

- `theta = Gw @ u_loc` (transverse deflection gradients),
- `memb_strain = B_m u + [0.5 t0^2, 0.5 t1^2, t0 t1]` (von Karman),
  `B_eff = B_m + B_nl` with `B_nl = [t0*Gw0; t1*Gw1; t0*Gw1 + t1*Gw0]`
  — this is exactly `d(memb_strain)/du_loc`.
- `curvature = B_b u_loc`.

Force/tangent assembly by `_jit_integrate_nonlinear_response`
(elements.py:3150-3170 call; core at elements.py:1330-1520) with `B_s`
(transverse shear, `D_shear = shear_elastic * 5/6 * h`), drilling
stabilization `B_d` with `drilling_stiffness = drilling_modulus * h *
drilling_stabilization` (elements.py:2923-2934; drilling force/tangent at
elements.py:1434, 1502 — linear stabilization `0.5*k_drill*(B_d u)^2*detw`),
and the von Karman geometric stiffness carried by `N_res` through `Gw`.
Hourglass stabilization applies only to 8-node reduced elements
(elements.py:3179); the qualified Q4 (4-node) takes `K_hg = None`, so the Q4
potential is:

    Pi_Q4(u_loc) = sum_gp detw * [ 0.5 e^T (h C_el) e + 0.5 k^T (h^3/12 C_el) k
                                   + 0.5 k_drill (B_d u)^2 ]
                 + sum_gp_shear detw_s * 0.5 g^T D_shear g

with `e = memb_strain(u)`, `k = B_b u`, `g = B_s u`. Gradient:
`B_eff^T N + B_b^T M + B_d^T k_drill B_d u + B_s^T D_shear B_s u`, matching the
integrator structure. Remaining verification (during implementation, no
numerics): read the integrator core lines to confirm the assembled `K_loc`
is the exact symmetric Hessian (skew check in the fixed criteria will decide;
a nonsymmetric local elastic tangent would be a STOP gate, since local laws
must not change).

## 2. Corotational map and the work-conjugate derivation

Existing map (corotational.py, unchanged): for element DOFs
`u = (t_i, theta_i)`,

- `R_rig`: shell — `_shell_center_frame(deformed) @ reference.frame.T`
  (translation-dependent); beam — `_beam_rigid_rotation` (axis alignment +
  mean axial twist; translation- and rotation-dependent).
- Pull-back (corotational.py:225-285): both categories reduce to one form,
  verified algebraically:
  `d_trans_i = R_rig^T (x_i - x̄_def) - a_i`, `a_i = X_i - X̄` (for shells this
  is exactly `R_rig^T t_off_i + (R_rig^T - I) a_i` since
  `t_off_i + a_i = x_i - x̄_def`), and
  `d_rot_i = phi_i = Log(R_rig^T exp(theta_i))`.
- Existing Jacobian pieces (corotational.py:583-644):
  `D = ∂d/∂u|_frame` (translations: `(delta_ij - 1/n) R_rig^T`; rotations:
  `J_r^{-1}(phi_i) J_r(theta_i)`), `U = ∂d/∂omega` (left-increment frame
  rotation; translations `R_rig^T skew(x_i - x̄_def)`, rotations
  `-J_l^{-1}(phi_i) R_rig^T`), `G = ∂omega/∂u` (central differences of the
  frame extraction; shells: translations only; beams: translations+rotations).

Full deformation Jacobian (the B of the contract):

    B = ∂d/∂u = D + U @ G

The old consistent tangent differentiates `f = E(omega) f_local(d(u))`; its
rotational output `R_rig m_local` is a rotated covector, not the work-conjugate
generalized force — the incompatibility recorded in
.development/rotating-offset-20261016/COMPATIBILITY_DECISION.md.

New profile (contract formula, exact potential structure):

    Pi(u) = Pi_local(d(u))
    p = B^T f_local                (f_local = element response at d)
    K = B^T K_local B + sum_a f_local[a] * Hessian(d[a])

`p` is the exact gradient of `Pi` and `K` its exact Hessian whenever the local
law is a potential gradient (verified for Beam2, section 1.1). `K` is
therefore symmetric without symmetrization (Hessian of a scalar), which is the
skew criterion; it is NOT the old Jacobian symmetrized, corrected, or offset
— the force output itself changes through the optional adapter.

### 2.1 Result/reaction convention (declared)

- `p` translational blocks are physical spatial forces at the nodes
  (translations are physical coordinates).
- `p` rotational blocks are covectors conjugate to the additive rotation
  vector `theta_i` (global rotation-vector coordinates). They are NOT physical
  spatial moments.
- Physical spatial moment at node i for diagnostics:
  `t_i = J_left(theta_i)^{-T} p_rot_i`. Derivation: a spatial spin increment
  `omega` gives additive increment `delta theta_i = J_left(theta_i)^{-1} omega`
  (from `exp(theta + d) = exp(J_l d) exp(theta)`), and invariance of the
  power gives `t_i = (J_left(theta_i)^{-1})^T p_rot_i`.
- Resultant identities (exact for a rigid-motion-invariant potential):
  `sum_i p_trans_i = 0`, `sum_i (x_i × p_trans_i + t_i) = 0` (common-origin
  moment). These are the 1e-10 physical identities of the fixed checks.
- Rigid invariance of `Pi` holds because frame extraction is exactly
  equivariant (shell frame rotates with Q; beam alignment+twist invariant), so
  `d(Q u) = d(u)` and `d(rigid u) = 0` on nonzero deformed states.

## 3. Intended implementation

1. New private module `src/anysolver/corotational_work_conjugate.py`:
   `work_conjugate_element_response(...)` computing `d`, `f_local`, `K_local`
   (tangent always — consistent tangent mandatory), `B = D + U G` reusing
   corotational.py pieces, `p = B^T f_local`, and the Hessian term
   `G2[:,j] = (q(u+h e_j) - q(u-h e_j)) / (2h)` with
   `q(u) = B(u)^T f_local_frozen` (f_local frozen — this is exactly
   `sum_a f_local[a] Hessian(d[a])`); `K = B^T K_local B + G2`. FD step and
   all scales frozen in FROZEN_CASES.md before any run.
2. `src/anysolver/corotational.py`: expose the profile through
   `corotational_element_response(..., force_profile=None)`; default None
   preserves current behavior exactly; profile routes to the new module.
3. `src/anysolver/nonlinear_static.py`: plumb public option
   `corotational_force_profile='work_conjugate_elastic_dev_v1'` through
   `solve_static_nonlinear` → owned config → the assembly dispatch at
   nonlinear_static.py:1507. Validation before iteration: profile requires
   kinematics='corotational' and resolved tangent 'consistent'; rejects
   follower pressure/loads, applied moments beyond ordinary dead forces,
   initial stress/prestrain fields, plastic history (hardening curve or
   nontrivial committed states), checkpoint/restart reuse; profile identity
   included in prepared-state signature so incompatible prepared state is
   invalidated.
4. Tests `tests/test_corotational_work_conjugate_profile.py`: fixed checks per
   brief (Beam2, Q4, shared-node Beam2+qualifiedQ4; poses 0/15/30 deg + one
   mixed-axis total 30 deg; undeformed/bending/mixed states with nonzero local
   moments not parallel to deformational rotation, phi<=0.01 rad, strain<=1e-3;
   perturbations 1e-4/1e-5/1e-6 at two adjacent fixed steps with committed
   state restored per evaluation; independent energy from the same local laws
   and Q4 quadrature including shear/drilling; gradient and tangent actions
   <=1e-6; resultant/moment identities 1e-10; skew <=1e-6 without
   symmetrization; rigid-zero and superposed-rotation invariance on nonzero
   deformed states; solve_static_nonlinear loading-unloading, rejected trial,
   cancellation after accepted state, same-model reuse).

## 4. Actual edited files (at checkpoint)

None yet. Planned edits are listed in section 3. Existing dirty files
(elements.py, assembly.py and the other baseline entries) are not touched;
shared-file edits will preserve pre-existing hunks.

## 5. Concrete risks

- Q4 local tangent symmetry: if `_jit_integrate_nonlinear_response` returns a
  nonsymmetric elastic `K_loc`, the skew criterion fails and the local law
  would have to change — that is a STOP gate, not a redesign invitation.
- Nested finite differences (G inside B inside the Hessian term): roundoff
  floor vs 1e-6 action tolerances; mitigated by frozen step sizes; the
  Beam2/beam branch has analytic D/U and only G by FD.
- Beam twist and translation-dependent shell frame are inside B via G; any
  error there shows up as gradient mismatch — the energy-gradient check is the
  discriminator.
- Cost: Hessian term needs 2*n_dofs B evaluations per element tangent
  (each B contains the FD frame sensitivity). Acceptable for the fixed small
  models; this is a dev profile, not a performance claim.
- solve_static_nonlinear integration surface (option plumbing, prepared-state
  identity, load rejection points) is not yet fully read; remaining
  inspection is bounded to nonlinear_static.py option/validation regions and
  the prepared-state signature mechanism.
- The profile must not change frame extraction, local laws, or the generic
  differentiation framework; all derivative pieces already exist
  (corotational.py:583-644) and are reused, not modified.

## 6. Remaining work

1. Read `_jit_integrate_nonlinear_response` core (elements.py:1330-1520) to
   confirm symmetric elastic `K_loc` and the exact force structure.
2. Read nonlinear_static.py option/validation/prepared-state regions
   (~4906-5360, prepared_static signature) for integration points.
3. Freeze FROZEN_CASES.md (fixtures, poses, scales, perturbations, tolerances,
   fixture source hash) BEFORE any numerical run.
4. Implement section 3; focused tests; run fixed checks through
   .development/work-conjugate-elastic-20261016/check.py only after
   CONTRACT_ADOPTED.md exists (parent Astra writes it; I must not).
5. Docs appends + living note append + HANDOFF.md.

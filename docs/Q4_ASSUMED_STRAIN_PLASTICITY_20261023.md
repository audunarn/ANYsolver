# Qualified Q4 plastic shells: assumed-strain layered plasticity (2026-10-23)

Module: `src/anysolver/_q4_assumed_strain_plasticity.py`. Tests:
`tests/test_q4_assumed_strain_plasticity.py` (slow mesh/step sweep with
`ANYSOLVER_RUN_SLOW_TESTS=1`).

## Problem

The qualified (E4-PL) Q4 shell is the inherited compatible von-Karman shell plus
the constant elastic delta `Cr = K_qualified - K_compatible`. With the hybrid's
assumed generalized strain `E_hat = B + dE` at the 2x2 Gauss points, the
membrane/bending part of `Cr` is exactly `Cr_mb = -sum_g w_g dE_g' D dE_g`
(hybrid stress/strain orthogonality `sum_g w_g E_hat_g' D dE_g = 0`): an
elastic relief of the parasitic in-plane-bending and bending strain of the
compatible element. The historical route evaluated layered plasticity at the
compatible strain and kept this relief elastic. Once layers yield, the element
tangent becomes indefinite. On the clamped 1 x 1 m plate (t = 3 mm, 50 kPa,
DNV C208 curve, yield 30 MPa) main converged to spurious mechanisms: +203 mm at
n = 8 and -42.8 mm at n = 16, against about 39 / 36 mm from the legacy element
and 35.4 mm from CalculiX 2.23 (S4, n = 64).

## Formulation

Supported plastic elements evaluate the layered return map at the assumed
layer strain `eps_hat = eps_c(u) + dE u` and use the force (`Cr u` added as
before)

    F = F_el(u) + Cr u + dE_m' A eps_nl + B_nl' A dE_m u
        - sum_g w_g (B_eff + dE)' [N_p; M_p](eps_hat)

with `F_el` the inherited elastic kernel, `A = h C`, `[N_p; M_p] = sum_l w_l
[1; z_l] C eps_p`. This is the von-Karman-consistent assumed-strain layered shell
`sum_g w_g (B_eff + dE)' N_hat` plus the unchanged shear, drilling and
stabilisation parts. The tangent is exact and symmetric:

    K = sum_g w_g (B_eff + dE)' D_t (B_eff + dE) + K_geo(N_hat) + K_rest.

The plastic tangent term is gated on the algorithmic state (`C_t != C` or
`eps_p != 0`), not on the plastic-strain value alone, so a point that reverses
back to `eps_p == 0` on the plastic branch keeps its exact tangent.

Stability statement: positive semidefiniteness of (qualified elastic Hessian -
the model's elastic Hessian), here `K_rest` (hybrid transverse shear plus
stabilisation, checked PSD on square and skewed facets), is a *sufficient*
condition for the elastic relief not to destabilise yielded layers. It is not
necessary, and geometric (compressive) stiffness can destabilise the response
independently, as it physically should.

## Scope and refusals

* Covered: qualified Q4, isotropic von Mises layered plasticity, planar facet,
  no generalized section, no active initial field. One kernel
  (`kernel_batch`) serves the assembly plans, the reference batch, the scalar
  element route and the committed current-tangent replay.
* Refused with `UnsupportedQ4PlasticRouteError` (typed, no silent fallback to
  the historical compatible-strain plastic route): Hill48/orthotropic
  plasticity, generalized sections with a hardening curve, warped facets,
  reduced integration, and states with an *active* initial field. "Active" uses
  the shared predicate `initial_field_state.state_has_active_initial_fields`,
  which also selects the scalar initial-field override in the assembly plans.
  Scalar and batch evaluation therefore agree: all-zero, provenance-free fields
  are ignored by both and active fields are refused by both. Use
  `formulation='legacy'` for these elements, or an elastic material.
* Not covered: a plastic-law version tag on persisted plastic states. Historical
  plastic Q4 histories (compatible-strain law) restored through checkpoints or
  `initial_element_states` are consumed without detection; see Open items.

## Validation (C1 = clamped plate above; ccx = CalculiX 2.23 S4 n = 64)

| n | steps | legacy [mm] | new [mm] | new vs legacy | new vs ccx | legacy vs ccx |
|---|---|---|---|---|---|---|
| 4 | 1 / 5 / 20 | 42.459 / 41.844 / 41.826 | 43.900 / 43.679 / 43.658 | +3.4 / +4.4 / +4.4 % | +24 % | +18..20 % |
| 8 | 1 / 5 / 20 | 38.974 | 38.127 | -2.2 % | +7.8 % | +10.2 % |
| 16 | 1 / 5 / 20 | 36.380 / 36.378 / 36.378 | 36.216 / 36.215 / 36.215 | -0.45 % | +2.4 % | +2.8 % |
| 32 | 5 | 35.177 | 35.128 | -0.14 % | -0.7 % | -0.6 % |

Every case completes; step-count spread is 0.55 % (n = 4) and below 0.003 % (n >= 8).
The previous plastic-deficit attempt (acd343203) stopped at load factor 0.596
(n = 8) and 0.854 (n = 16). Converged C1 n = 4 tangent: lowest eigenvalue 780 N/m,
no negative eigenvalue (legacy 783). Bending-dominated cases (t = 10 mm / 25 kPa,
t = 20 mm / 100 kPa) agree with main within 0.0-0.2 % at n >= 8. The membrane case
t = 3 mm / 10 kPa is within 0.44 % of legacy and 0.1-1.1 % below main at n >= 8.

## Contract changes

* Elastic materials: untouched and bit-identical (displacement hashes of five
  elastic von-Karman/corotational cases unchanged).
* Plastic-capable Q4 before yield: changes by the von-Karman cross terms,
  about 1e-10 to 2e-9 relative in the checked cases (zero for linear kinematics).
* `layer_strain` / `layer_stress` of plastic Q4 states hold the assumed-strain
  values (consistent with the qualified element's mixed stress recovery);
  `kinematic_layer_strain` (scalar route) keeps the compatible kinematics.
  The state schema is otherwise unchanged.
* Hill48/orthotropic plastic Q4, generalized sections with hardening and
  active initial fields now refuse instead of running the unstable form.

## Open items

* No plastic-law version tag on persisted Q4 plastic states. A tag plus one
  refusal point needs changes to the packed state store
  (`ShellStateBatch` sidecars are kept only from seeds), the compact-state key
  whitelist and the sealed/checkpointed state digests. That is more than a few
  lines, so it is deferred to an owner decision.
* Extending the route to Hill48 (material-frame return map at `eps_hat`) and to
  active initial fields (constant layer offset; the derivation holds) is
  possible but not built or verified.

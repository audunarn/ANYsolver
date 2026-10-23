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
  plasticity (with or without a hardening curve; the inherited kernel is
  perfectly plastic for Hill48 without a curve), generalized sections with a hardening curve, warped facets,
  reduced integration, and states with an *active* initial field. "Active" uses
  the shared predicate `initial_field_state.state_has_active_initial_fields`,
  which also selects the scalar initial-field override in the assembly plans.
  Scalar and batch evaluation therefore agree: all-zero, provenance-free fields
  are ignored by both and active fields are refused by both. Use
  `formulation='legacy'` for these elements, or an elastic material.
* Not covered: a plastic-law version tag on persisted plastic states. Historical
  plastic Q4 histories (compatible-strain law) restored through checkpoints or
  `initial_element_states` are consumed without detection; see Known limitations.

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

* **Single elastic law (owner decision 2026-10-23).** Planar isotropic qualified
  Q4 elements WITHOUT a hardening curve also run the assumed-strain kernel, with
  the return map skipped. Elastic initial fields enter as the same constant layer
  offset as in the inherited kernel. The compensated direct elastic increment
  route and the batch-B elastic fast path are retired for these elements; they
  remain in use for legacy shells. The owner waived elastic bit-identity for
  qualified-Q4 NONLINEAR elastic results. Measured on the clamped C1 plate,
  elastic (t = 3 mm, 50 kPa, 20 steps; ccx elastic 11.78-11.81 mm):
  * von Karman: n = 4 / 8 / 16 / 32: 15.114695 -> 15.114311, 12.078385 ->
    12.067263, 11.879723 -> 11.878586, 11.835173 -> 11.834981 mm
    (-2.5e-5 / -9.2e-4 / -9.6e-5 / -1.6e-5, toward ccx);
  * corotational: n = 8 / 16: 12.085591 -> 12.093734, 11.884699 -> 11.886467 mm
    (+6.7e-4 / +1.5e-4, slightly away from ccx).
  Linear analyses (stiffness matrices and linear static solves) are bit-identical,
  as are all non-qualified-Q4 elements (beams, legacy shells, S3).
  Curve and no-curve elements agree to 5e-16 before yield. A mixed mesh equals
  the pure meshes to 1e-9 in both kinematics, so the earlier two-law interface
  effect is gone.
  Cost against main, elastic C1, 20 steps, wall time per process: von Karman
  n = 8 1.62 -> 1.85 s, n = 16 4.50 -> 5.93 s; corotational n = 8 30.2 -> 22.1 s,
  n = 16 115.4 -> 85.8 s.* Plastic-capable Q4 before yield (hardening curve present, never yielded):
  the response changes by the von-Karman cross terms
  `dE_m' A eps_nl + B_nl' A dE_m u`. At a fixed displacement these terms are
  the whole force difference against main (to 1e-14). The size depends on the
  rotations:
  * small rotations: about 1e-10 to 2e-9 relative (n = 4, t = 10 mm, p = 1-2 kPa;
    corotational);
  * large deflection, clamped plate t = 3 mm at 50 kPa (w about 12-15 mm; curve
    scaled by 100 so it never yields): change in centre deflection 2.5e-5 /
    9.2e-4 / 9.6e-5 / 1.6e-5 at n = 4 / 8 / 16 / 32, max |du| / max |u| 6e-5 /
    5.1e-3 / 2.0e-3 / 4.3e-4 (the largest share is in-plane). It is the same
    for 1 and 20 steps and does not grow with refinement (peak at n = 8).
    At n = 8 it is small against the discretisation error vs CalculiX
    (+2.2 %);
  * t = 3 mm / 10 kPa n = 16: 2.9e-4; t = 10 mm / 25 kPa: 2.5e-5; t = 20 mm /
    100 kPa: 1.7e-6.

  With the single elastic law (above) the same shift applies to elastic
  materials, so a plastic-capable element before yield is identical to the
  same element with an elastic material. Dropping the cross terms is not an
  option: the plastic tangent then loses positivity.

  **Accepted exception A4, owner approval 2026-10-23,** for the measured size:
  up to about 1e-3 in the centre deflection and about 5e-3 in the in-plane
  max |du|. Against the elastic CalculiX answer for this plate (11.78-11.81 mm),
  the shifted value moves slightly *toward* the reference at every mesh
  (n = 4/8/16/32: 15.114695 -> 15.114311, 12.078385 -> 12.067263,
  11.879723 -> 11.878586, 11.835173 -> 11.834981 mm; 20 steps, alpha = 0).
  Side observation: main's 1-step solve of the never-yielding n = 32 case
  returned w = 115 mm with alpha = 1.4e5 (a spurious state); the branch gives
  11.9 mm.
* `layer_strain` / `layer_stress` of plastic Q4 states hold the assumed-strain
  values (consistent with the qualified element's mixed stress recovery);
  `kinematic_layer_strain` (scalar route) keeps the compatible kinematics.
  The state schema is otherwise unchanged.
* Hill48/orthotropic plastic Q4, generalized sections with hardening and
  active initial fields now refuse instead of running the unstable form.

## Membrane-plastic case t = 3 mm / 10 kPa (C4), centre deflection [mm]

| n | steps | new | legacy | main | ccx S4 n32 / n64 | ccx S8R-4L n48 / S8R-8L n32 |
|---|---|---|---|---|---|---|
| 8 | 1 / 5 / 20 | 8.558 / 8.562 / 8.555 | 8.596 / 8.598 / 8.591 | 8.654 / 8.659 / 8.650 | 8.587 / 8.731 | 8.344 / 8.205 |
| 16 | 1 / 5 | 8.542 / 8.542 | 8.565 / 8.566 | 8.574 / 8.575 | | |
| 32 | 5 | 8.598 | 8.609 | 8.607 | | |

The new route lies within 0.44 % of legacy at n >= 8 and 1.1 % below main at
n = 8. The reference band (S8R 8.21-8.34 mm to S4 8.59-8.73 mm) contains all
three formulations. Main is closer to S4 n64; the new route sits between S4
and S8R. All three converge to about 8.60 mm at n = 32.

## Cost

C1 n = 16, 1 step, profiled to load factor 0.6 (300 Newton iterations each):
the committed assumed-strain route took 59.1 s against legacy 12.3 s, 35.8 s of
it in multi-operand `np.einsum` contractions (`B_hat' Dp B_hat`, the cross-term
tangent, the geometric terms). These are now staged as matrix products (owner
approval 2026-10-23; rounding differs from the first assumed-strain commit at
about 1e-15 relative). Measured with other jobs running: 57.7 -> 25.5 s to load
factor 0.6 and 69.1 -> 30.8 s to load factor 1, with the same Newton iteration
counts and the same centre deflection to 2e-16.

## Known limitations

* **Historical plastic histories are not detected.** Plastic Q4 states
  written by the historical compatible-strain law and restored through
  `initial_element_states` (ordinary restart, explicit seeds, arc-length seeds)
  or through a mixed persistent state store are consumed without detection and
  reinterpreted by the assumed-strain law. Codex rates this a high-severity
  restart correctness risk. A single refusal point at ordinary-restart migration
  was tried and withdrawn: plastic result states written by this version
  (for example the displacement-control beam-shell resume fixtures) are also
  unsealed by the time they reach that point, so the two laws cannot be told
  apart without a persisted plastic-law version tag. A tag needs changes to the
  packed state store (`ShellStateBatch` sidecars), the compact-state key
  whitelist and the sealed/checkpointed state digests. A law-version tag is the
  proper fix. It is an open HIGH follow-up.
* Orthotropic elastic and generalized-section qualified Q4 elements keep the
  historical elastic law (the kernel is isotropic only).
* Hill48/orthotropic plasticity, active initial fields and generalized sections
  with hardening are refused rather than supported.
## Open items

* Plastic-law version tag and refusal of historical plastic histories (HIGH,
  see Known limitations).
* Extending the route to Hill48 (material-frame return map at `eps_hat`) and to
  active initial fields (constant layer offset; the derivation holds) is
  possible but not built or verified.

## Qualification and merge (2026-10-23)

* Qualified at TARGET_SHA 5c34dc2e4 (product-source digest f2acc4da71e0...): 68/68 matrix cells PASS with
  exceptions. A9 cost 2.0x legacy (plastic, C1 n16 to load factor 0.6) and 1.25x base (elastic nonlinear).
  Report: `C:\ANYworkspaceWork\codex-q4-qual-notes\03_FINAL_REPORT.md`; evidence root
  `C:\ANYworkspaceWork\qualification-evidence\Q4_R4\f2acc4da71e0`. Owner decisions closed 2026-10-23
  (`C:\ANYworkspaceWork\qualification-plan\DECISIONS_LOG.md`). Merged into local main (not pushed).
* Exceptions:
  * W1: owner, 2.5 % allowance at n = 8 for the in-plane displacement change. The measured pointwise in-plane
    difference is 2.0 % of the base peak; the centre deflection changes by -0.092 %.
  * C4: OD-Q4-1, the legacy 1 % rule plus the S8R band replaces the 0.6 %-of-base rule.
  * A8: inventory differences granted by the coordinator; test changes are listed in the plan document table.
  * H1: historical plastic history accepted as a documented HIGH limitation.
* Open follow-ups:
  * Public stress recovery review (option A accepted and documented).
  * Plastic-law version tag (HIGH).
  * Governed mixed-mesh manifest successor record (EXCEPTION).
  * Descriptor-shear gate follow-up for the S3 impact.
* Waiver: elastic bit identity is waived for qualified-Q4 NONLINEAR elastic results (sizes above). Linear
  analyses, legacy Q4, S3, beams and native on/off are bit-identical.
* Source-binding records: none rebound. The governed manifest (`e4_pl_q4_source_binding_20261019.json`)
  is the documented exception; no other binding was mechanical.

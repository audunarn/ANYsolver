# D2 finite-penalty radial independent review — 30 September 2026

## Disposition

The named finite-law radial spatial discriminator is **NONPASS** against its unchanged development targets. The coupled mechanics completed two accepted steps and preserved its complete 432-state checkpoint, but the target displacement at `(0.6, 0.85)` exceeds 2%. Seven of eight saved-data checks pass. Separately, the original v1 process exits 1 at a known postprocessing type error after saving the mechanical result; that failure remains retained. The later assessment completes extraction and exits 0 while explicitly retaining `development_checks_met=false`.

This independent review inspected source and saved evidence and reconciled identities, arithmetic and result fields. It executed no solver, test, numerical case or replay and edited only this note. No production change, criterion relaxation, new D1 claim, D2 scientific acceptance, release or application admission follows. Prior point-load/spatial failures remain unchanged. No demonstrated production defect or universal formulation failure follows from this one response discrepancy.

## Fixture and reuse boundary

The adapter `d2_projected_penalty_radial_dev.py` reuses the existing literal radial builder, public path solve and recovery. Its module-local factory substitution preserves model geometry, source/target material and physical skins, uniform source forces, radial boundary traces and analytic reference. It replaces the interaction with `normal_law=projected_penalty`, regularization 1e7 Pa/m and existing D2 settings; the original factory is restored in `finally`. No production source patch or D1/monolithic admission occurs.

Frozen geometry is 12×12 Q4 source cells and 12×12 target cells represented by S3 faces, target right edge 1.297 m and lower edge -0.113 m. The actual guided scalar coefficients are source 1602.5641025641025 N/m and target 3163.400547104653 N/m. The target MIN3 P1 energy correspondence has maximum relative error 4.492e-16. Physical clearance is 7.741263872132846e-6 m and reference total force 0.020435219974701022 N. Fine Q1/Jet2, exact support, nested enforcement, `overlap_local_dev` and `d1_interior_profile=false` are explicit. The actual result reports `Q4_S3_PATCH_REFINED_PROJECTED_FINITE_PENALTY_STATIC_DEV_V0`.

The retained `RadialTwoBodyReference` is an independent hard-contact continuum obstacle solution, not an exact finite-penalty solution. Its operator freezes the actual guided MIN3 coefficient, with source-only uniform load and radial Dirichlet traces. Thus response differences combine finite-penalty, spatial/operator and boundary-trace effects. Reference evaluation uncertainty is included; it does not supply a uniform nonlinear/model error bound or an exact finite-law KKT criterion.

## Mechanics, postprocessing and saved assessment

The original helper incorrectly indexes `independent_gap_lower_m` as a dictionary at line 77, although the retained recovery returns a scalar. Its log records `TypeError: 'float' object is not subscriptable`. Complete mechanics and diagnostics were saved beforehand. New exclusive saved-data outputs recover wrench, physical bins and summary without repeating the coupled solve.

The saved wrench recovery uses `semismooth.linearize(..., tangent=False)` at `z=pS`. At the same represented pose, `-z Dg = -p(DW-g DS)`, pulled back through the same structural map, equals the finite-law residual. This permits residual/work recovery; it does not assert equality of fixed-z and finite-law tangents or hard-contact complementarity. Complete joint free dimension is 242, and both bodies' fixed/control/MPC reaction actions and physical contact moments remain represented.

| Quantity | Saved result | Target | Disposition |
|---|---:|---:|---|
| Total physical force relative error | 0.0120551583631 | 0.02 | PASS |
| Source maximum accounted displacement error | 0.00189640487625 | 0.02 | PASS |
| Target maximum accounted displacement error | 0.02125079997997 | 0.02 | NONPASS |
| Independent physical gap lower bound | -1.294781342e-7 m | ≥ -5e-5 m | PASS |
| Physical-bin uncertainty-accounted L1/L2 error | 0.0120551587536 / 0.0122913798221 | 0.02 | PASS |
| Maximum full both-body wrench diagnostic | 2.894e-11 | 1e-6 | PASS |

The failing target sample has actual displacement -1.302844452819455e-6 m and reference -1.3311320742768099e-6 m. All six displacement samples retain their literal coordinates. The assessor uses `(abs(actual-exact)+e)/(abs(exact)-e)` and rejects a nonpositive denominator, preserving conservative reference uncertainty accounting. Bin uncertainty budgets pass; bins sum exactly to the reassembled force and the reassembled/saved force defect is 1.301e-16. All 169 pressure/support rows are present; minimum support is 0.0017361111111110774 m² and pressure is nonnegative. Actual projected nonpotential work labeling remains intact.

Supervisor records: original process 759.8793698 s / 480.17408 MB, exit 1; saved wrench 77.1754899 s / 447.561728 MB, exit 0; saved bins 84.76124 s / 447.0784 MB, exit 0, each under 900 s / 4,000,000,000 bytes. Summary extraction 1.6292577 s / 163.790848 MB, exit 0 under 180 s / 1,000,000,000 bytes. These terminal/resource facts do not change the failed response criterion.

## Fixed-geometry derivation scrutiny

`D2_FINITE_PENALTY_FIXED_GEOMETRY_BOUND_20260930.md`, SHA256 `4d9b164b914a4e796eb3a67e056b9de6170be5d8d02e0743a87de4479edf876e`, has no mathematical blocker within its stated assumptions: positive common measure, nonnegative partition-of-unity hats, exact integrals or consistent positive quadrature, frozen matching/normals/skin maps and independently coercive structural stiffness.

Weighted Jensen gives `k sum(J_i(d)^2/S_i) <= k integral(d^2)` for any active subset. With `S` in m², `J` in m³ and `k` in N/m³, the quadratic form has units N·m. Scalar nodal partitions imply `norm(G_i)^2 <= 2 S_i^2`; each row stiffness norm is at most `2 k S_i`, tending to zero with its positive support. The pressure bounds are support-weighted/L2; a pointwise coefficient bound additionally needs bounded pointwise gap. Zero support is outside the division formula and no positive-row floor/removal is licensed.

The derivation correctly retains prescribed pressure rows while reducing displacement columns, includes the constraint-transform norm factor and requires independent structural SPD. It does not prove uniform structural coercivity, mesh-family conditioning or inf-sup stability. The exact moving tangent adds geometry terms and a generally nonsymmetric `(DS).T B` contribution. Accordingly the bound proves no general moving SPD, pointwise physical-gap accuracy or success for this radial response test, and cannot regrade its NONPASS.

## Identities and remaining scope

The frozen `.inputs.json` binds four adapter/builder/reference files and 70 `general_contact` files, all still matching after the run (zero mismatches). This is partial source provenance, not a complete wheel/source manifest: generic nonlinear/restart/structural modules and all transitive recovery helpers are not independently listed there. The development record identifies the source checkout import, and unchanged-production checkpoint context remains separate. No installed-artifact claim follows.

Raw SHA256 identities:

- Inputs: `09da4408c82c5103c8da75f28be53df4eb1e070e787223bc241c6ff237d28c67`.
- Executed radial adapter/snapshot: `a5f4e4e706766168934e80e845e85113f1b34cb80a3827ff5132b15fc64e6bc0`.
- Radial mechanics v1: `a49b9238be5e2abdd77ba4e3e47116115bcb0dc8e58053552a9ec9706c7101fa`.
- Wrench v1: `4305d73c6186fbdc9fa85f87b7c5c2b08747fdb5336fe1bdeca17997f961b6c3`.
- Physical bins v1: `fb8d195144adb8a298027f22d5618c38db3b373a4f86d10acc48eebc7f82f59f`.
- Summary v1: `1b1db36c1af4bd482e793736bdb03b2df09c2079ab6b7cd82f6aa80f0e5c8bca`.
- Executed saved-data assessor/snapshot: `077e6bb1f3dfc4040b62e9aed83367b18e1e15da13f86aa1a4a1900c27ef6c5d`.

Wrench/bins and summary reference the exact same retained radial hash; the executed assessor snapshot matches its recorded identity. Original logs/resources/trace and every failed record remain preserved. The evidence establishes completed finite-law mechanics with adequate represented gap and balance for this guided flat case, but does not close the named 2% target-response discriminator, arbitrary partial-boundary accuracy, continuous collision, moving stability or D2 acceptance. Any next diagnostic must address the remaining combined response uncertainty without treating this failed case as a pass.

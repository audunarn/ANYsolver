# D2 radial kappa=1e8 independent review — 30 September 2026

## Preflight disposition

The fixed-geometry preflight provided a scoped no-blocker for one newly authorized coupled radial discriminator at 1e8 Pa/m under the unchanged 2% response, 50 micrometre physical-gap and 1e-6 balance targets. The actual coupled run is now **NONPASS — time limit exceeded**, without a final result. Its response/gap/balance cannot be assessed. Preflight eligibility remains a regularization-sensitivity finding, not moving-contact solve success, renewed execution authority or D2 acceptance.

The independent reviewer inspected the parameterized helper, frozen records, uncertainty algebra and source identities. No numerical run, test, solver or evidence replay was executed; this note is the only write. The kappa=1e7 radial target-response NONPASS and original postprocessing failure remain retained. Earlier scientific, installed and release boundaries remain unchanged. The previously reviewed fixed-geometry Jensen derivation is not re-adjudicated here.

## What the comparator discriminates

`d2_radial_finite_reference_dev.py` integrates both-body Q1/P1 support/work independently of production contact. Structural K, binary geometry, constraint/free bases, radial trace values, loads and clearance are declared shared owner inputs. The convex fixed-normal problem uses `g=g0+A y/S`, `p=kappa max(-g,0)`, residual `K y-f-A.T p` and active tangent `K+kappa A_active.T diag(1/S_active) A_active`. Energy safeguards belong to this fixed-geometry reference; they do not assume the actual moving work is a potential.

The preflight and coupled freeze preserve the same 12×12 source/12×12 target mesh, target right edge 1.297 m/lower edge -0.113 m, scalar source/target operators, source-only uniform load, two radial trace controls, sample locations and clearance as kappa=1e7. Coupled geometry metadata, path program and settings are identical to that previous freeze; only interaction regularization changes to 1e8 Pa/m. Existing projected-penalty D2 profile/nested route remain selected, with `d1_interior_profile=false`. No production equation, default or scientific criterion changes.

The reference explicitly records `same_penalty_model=false` when comparing its kappa=1e8 prediction with the saved kappa=1e7 nonlinear pose. This comparison is sensitivity between two laws, not a same-kappa agreement gate or a regrade of old evidence. Hard-contact continuum fields remain the response comparator. The preflight can identify finite regularization bias within the frozen spatial operator; it cannot independently separate the subsequent moving-geometry/structural nonlinear contribution or prove continuum accuracy.

## Uncertainty and eligibility

The finite solver uses a fixed 0.08 N residual scale, relative solve tolerance 1e-11 and bounded 40 Newton iterations. Full/free/pressure dimensions are 2028/242/169. Actual shared structural SPD is checked. The checked inverse and exact-rational supplied-binary-XY contact coefficient envelopes propagate support and normalized-gap errors through the active tangent. Active/inactive signs are resolved under the resulting envelope. Shared material, structural/model and moving-geometry uncertainty are explicitly excluded.

Recorded inverse residual bound is 1.124e-9, coefficient perturbation factor 7.939e-8 and maximum pose uncertainty 6.297e-14 m. Sample upper errors add solution and analytical evaluation uncertainty to the numerator and subtract reference evaluation uncertainty from the reference denominator. The uncertainty-accounted predictions are:

| Quantity | Conservative preflight result | Unchanged target |
|---|---:|---:|
| Source maximum sample error | 0.001907961 | 0.02 |
| Target maximum sample error | 0.019132144 | 0.02 |
| Integrated force relative error upper bound | 0.009895510 | 0.02 |
| Clipping-independent physical-gap lower bound | -1.580174e-6 m | ≥ -5e-5 m |

The floating common-polygon minimum is -4.254798e-8 m. Candidate eligibility uses the more conservative full-coverage nodal lower bound from nonnegative Q1/P1 partitions, subtracting solution uncertainty; it does not depend on unbounded floating clipping error. Force uncertainty is 6.929225e-6 N. Active tangent condition is 5334.94, versus structural condition 115.21. Increased regularization can affect the actual nonlinear solve cost and convergence; the 900 s/4 GB cap remains an empirical requirement, not a reference prediction.

The preflight completed exit 0 in 6.9967775 s / 212.70528 MB under 180 s / 1,073,741,824 bytes. Its candidate eligibility is development-only. Complete actual force/response/gap/balance and recovered physical-bin evidence are still needed before a coupled disposition; no exact hard-contact KKT criterion should be substituted for the finite law.

## Frozen identities

Preflight inputs and coupled inputs each bind 433 package source hashes. Both sets match current source, with zero mismatches. Bound preflight input/helper identities, coupled helper identities and summary evidence hashes also match. This resolves the prior radial freeze's partial package provenance for the new candidate; it remains a source-checkout experiment, not an installed-wheel claim.

- Parameterized fixed-reference helper/snapshot: `c875c9c0fb6e0ce96bc0ca0b6d1832ee5f66029f156f297f5678c82b0b0995a0`.
- Fixed-reference k1e8 result: `f2c47a919d66d933230c5997a70c16e1e690d73b9cc8cb0c00c33eff88ccdd13`.
- Fixed-reference k1e8 inputs: `baf30863693fed65d8ee578f8ebd6bd51a4299671132fdff9d7875436554a4a7`.
- Fixed-reference k1e8 summary: `5a12320a33d4ebc277318a07351130ea5dc2035948053c69415c0701268bba0f`.
- Coupled k1e8 inputs: `860a152277d9618feb7a9659c6b71b9c45788c990e1f6f4a12f19fd09ba0a004`.
- Coupled k1e8 executed adapter/snapshot: `548986b5442941efd7d326c9798418a1bb878446cfd6a808dae20e5be51120df`.

Preflight records source HEAD `23e845e131a8ea0c3457d10d9355ecdd5d1dd28e`. The coupled snapshot restores its module-local factory in `finally`, preserves exclusive outputs and fixes the known scalar-gap indexing error without repeating or replacing the kappa=1e7 result. It preserves the response gates; final independent uncertainty accounting and complete balance belong to the saved-data assessment.

## Coupled result — retained timeout

The lead-owned run terminated at the frozen time boundary. `d2_projected_penalty_radial_k1e8_v1_20260930.resource.json` reports `time_limit_exceeded`, supervisor exit 15, 900.0605029 s and 486.518784 MB under the declared 900 s / 4,000,000,000 byte limits. Memory did not reach its cap. The command selects `--normal-regularization 1e8` and the exclusive new candidate output. Its log is empty; no solver failure reason can be inferred from it.

The retained trace contains 21 events, nine swept begins and nine swept ends, all nine admissible. The last end is at 618.9197463 s (call 9, 16.5953493 s); no `trace_end` exists. Admissible trial sweeps do not establish accepted-step completion, nonlinear equilibrium or final scientific postchecks. No final `.json` was written. Therefore no complete checkpoint, response, physical-gap, force/moment or saved-data assessment is available for this candidate; none is reconstructed or substituted from the preflight.

Frozen input/snapshot hashes still match. All 433 frozen package files and bound helper files match current source with zero mismatches. The frozen effective import is `C:/ANYworkspaceWork/ANYsolver-general-contact/src/anysolver/__init__.py`, using `C:/Python/Python314/python.exe`, regularization 1e8 Pa/m and the existing projected-penalty D2 profile. This remains a source experiment rather than installed-artifact evidence.

Additional retained SHA256 identities:

- Supervisor resource: `15bfe837737241ec35af63cfc25b28453c2b83476def359d44ebc5fcc0d45022`.
- Empty log: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Incomplete trace: `fc5f59883b69b18d5c65dfc6768aaa011f0c393085ad5e176eb3bc8b87913f19`.

The 900 s execution is consumed. The lead decision stops the large radial branch, retaining kappa=1e7 target-response NONPASS and kappa=1e8 TIMEOUT separately. Neither result demonstrates universal finite-law failure; the latter also cannot distinguish slow convergence from costly uncompleted work. No numerical rerun or larger cap is authorized or implied by this review.

## Subsequent scope boundary

A tractable fixed-target partial-boundary guided-shear fixture with an independent finite-penalty ODE would be a new method-specific response row, not a replacement for either radial record. Its contract must bind the scalar structural reduction, actual partial contact domain, physical skins, boundary conditions, load and finite law. A continuum pointwise ODE is a response comparator; it is not automatically an exact oracle for discrete weak nodal averages. Prescribed-row pressure, full constraint reactions and represented physical-gap checks must remain visible, with fixed scales through any opening state. A new result could close only its own declared row, without proving general 2D spatial accuracy, moving stability or repairing the radial NONPASS. This note neither authors nor executes that fixture, and it performs no D6 contract assessment.

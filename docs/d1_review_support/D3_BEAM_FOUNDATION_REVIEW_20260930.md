# D3 beam/fixed-plane foundation — independent review

2026-09-30. **Scoped local development PASS; no scientific acceptance or installed promotion.** Source/evidence inspection only: no reviewer solver run, test reproduction or production edit.

## Equations and fixture

The independent [reference](d3_beam_foundation_reference.py) has consistent Timoshenko signs and units: downward w/rotation are positive, Q=S(w′−θ), M=Dθ′, M′=−Q, and Q′=k(w−c)₊−q. Line k has units N/m²; contact reaction is qL−Q(0). Its dimensionless generators, clamped w/θ and free-end M/Q conditions are consistent. Open-branch polynomial extrema and a positive active-branch velocity lower estimate check the declared single active interval [a,L], subject to numerical transfer accuracy.

The [test](../../tests/test_general_contact_beam_foundation_dev.py) uses concentric elastic B2 von Karman sections, a fixed analytic plane, explicit radius/line stiffness, no end caps, planar guidance and actual clamping. The reference uses the same reference-length line law and declared shear factor. Trapezoidal nodal forces total qL exactly; these dead nodal loads converge to uniform continuum loading but are not an exact distributed-load equivalence on every structural/contact interpolation. Refinement therefore includes loading and centerline discretization. The small-motion reference does not qualify finite rotations or a general tube/surface model.

## Numerical reference resolution

The new Decimal80 control independently rebuilds the ODE, evaluates its exponential by Taylor scaling/squaring, and solves the end M/Q two-by-two system at the returned binary64 front. Matrix multiplication, generator signs, scaling and resultants-to-SI conversion are correct. For k=10⁴ and 10⁵ it passed front residual <10⁻¹⁰ (dimensionless), end residual <10⁻⁶⁰, reaction agreement <10⁻⁹ relative and tip agreement <10⁻¹⁰ relative. [Inputs](d3_beam_reference_resolution_v1_20260930.inputs.json) SHA256 `913c0fc0b381749055cf861b9625082d468d08bef436031902cb5342beae90d4`; [log](d3_beam_reference_resolution_v1_20260930.log) and XML record 2 PASS, 5 deselected; resources: 3.412494 s / 213.496 MB under 180 s / 1 GiB.

This is independent numerical agreement for two inputs, materially below the local response gates. It is not outward certification: the float front is reused, no independent root bracket or rounding/tail/squaring enclosure is issued, and the end residual follows a solved boundary system. It does not certify arbitrary expm conditioning, geometries or active intervals.

## Actual retained responses

| B2 cells | k (N/m²) | Reaction error | Tip error | Minimum gap |
|---:|---:|---:|---:|---:|
| 16 | 10⁴ | 0.351447% | 0.00144845% | −5.88193 µm |
| 32 | 10⁴ | 0.0882358% | 0.000355158% | −5.87093 µm |
| 64 | 10⁴ | 0.0224386% | 0.0000791938% | −5.86816 µm |
| 64 | 10⁵ | 0.0223990% | 0.0000257493% | −1.85566 µm |

[V1](d3_beam_foundation_v1_20260930.log) retains 2 PASS (reference check plus 16-cell solve). [V2](d3_beam_foundation_v2_20260930.log), SHA256 `cfe4340a1cb8dfc9e48b7260eb1926088d5cdac07bcefa8a0e818885fbb06b99`, records only three new cases PASS, two older checks deselected, 6.131316 s / 262.492 MB. Prospective 2% coarse / 0.1% finer response gates and 10 µm gap gate pass. Reaction/response trends support this declared local refinement discriminator; they establish neither universal convergence order nor a hard-contact limit. Saved clamp-plus-contact force balances differ from the 0.001 N applied total by less than 7.0e−10 N.

## Identities and limits

- Reference SHA256: `41ad204330260ab61fb81567df679745fa4f62814abeb88b8d6714313bdf66b5`.
- Current test SHA256: `db6dfbc6bd8449e2d7b6ae64335b0e09b675c507bc3cfae954f409832501dcfe`.
- Beam-plane owner SHA256: `c435ec5b12c3aa664fbff5c187168bd38ee17b44ecbe6ec7c98f4b4e11436522`.

All 440 current reference-control bindings match. Older solve freezes retain their test snapshots; only the live test differs through added controls, while reference and production bindings remain unchanged. Actual imports/threadpools are recorded in each raw log. No thresholds were retrospectively changed. General beam contact, nonmatching beam/shell response, crossings, finite/native dynamics, broader D3 acceptance, installed handoff and release remain open.

## Addendum: multiple explicit beams/fixed rigid bodies

**Independent disposition: scoped local integration PASS.** The new manager constructs and validates one existing single-pair owner per sorted interaction, then sums residual, complete tangent and potential at the same authoritative global displacement. Per-pair dimensional line stiffness and gap budgets remain; aggregate gap status is their conjunction, and wrenches sum about the same global origin. The common admissible fraction is the minimum child fraction followed by a recheck of every child at the actual common endpoint. No new contact law or pressure state is introduced.

Admission requires at least two explicit round-beam/fixed-plane, sphere or infinite-cylinder interactions, ordinary force/displacement control and nested line-penalty enforcement. Caps, moving bodies, unsupported laws, unused declarations, duplicate (element, named rigid body) pairs and aggregate candidate overflow fail closed. Each child also retains its original beam/material/geometry validation. Two conditional core dispatch additions leave single-pair and multiple projected-shell routing intact. Sorted child restart contracts retain separate stiffnesses, budgets and body identities; no state is manually reconstructed or rebound.

[Inputs](d3_multiple_beam_rigid_v1_20260930.inputs.json) SHA256 `50296a890e5c756622edd553934d2ad70267812501110da0a128a90117099990`; [log](d3_multiple_beam_rigid_v1_20260930.log) SHA256 `5c58a2ed053118cd55cf0f08db304dd0305fe13c36cfa9af5646f1104e17c6c0`. XML records 9 PASS, no failures; resources record 4.453116 s / 263.193 MB under 180 s / 1 GiB. All 441 bound files match, with actual imports and one-thread numerical libraries retained in the log.

The independent two-plane B3 scalar potential uses the original midpoint shape 4s(1-s), analytic active roots and reference-length integration; its signs, dimensions and work derivative are consistent. It checks aggregate energy/work and directional tangent, while separate unequal gap budgets exercise conjunction. The imposed cylinder/plane case independently predicts 100 N and 0.05 J on the cylinder with the plane open. The actual public force case has both pairs active; fresh-model JSON prefix restart reproduces full displacements within the declared tolerance, preserves per-pair reporting, and changed line stiffness rejects the authentic prefix. Negative admission cases and the existing shell analysis-control dispatch check also passed. Coupled force magnitudes are integration outputs, not an additional independent continuum oracle.

Exact source identities: manager `bd5aa455e7cffff0a0a4887383958473e81e1ca83e969ea6e56d2a6d96d741ce`; core `c8e050702a184a4815df6beded12442cea5a912677d1ab13042d9abe9f7ce818`; test `192a97fd650c7c4b1cffc7a0ecb2bca05e93dac7bd634d27741a86e089e72e54`. Existing single-pair kernels remain unchanged. This evidence does not establish complete checkpoint byte parity, a coupled sphere/displacement lifecycle, moving/capped interactions, generic simultaneous-contact scientific accuracy, installed handoff or broader D3 acceptance. No reviewer run, kernel edit or changed tolerance was performed; the prior foundation review retains its original source/evidence scope.
## Addendum: order, source example and displacement residual units

**Scoped local delta PASS; V2 test NONPASS retained.** V2's named-order check verifies identical aggregate R/K/results and sorted restart contracts after reordering interactions/bodies. Its source example check runs the new public-import [example](../../examples/general_contact_multiple_round_beam_tools.py) in a subprocess and verifies completed status, profile, two pair records and gap gates. Both checks passed. The [guide](../GENERAL_CONTACT_C2_MULTIPLE_FIXED_TOOLS.md) accurately marks the route as development-only and retains original child geometry/material restrictions; this is a source-checkout example, not installed qualification.

The V2 displacement solve completed and passed status, active-pair, per-pair gap, control-displacement and opposite-force checks, then failed a dimensionally incorrect assertion comparing force-valued residual_norm directly to dimensionless 1e-8. The V2 evidence remains NONPASS. The exact V2-to-V3 test delta only divides residual_norm by fixed positive Fref=hypot(10,12)=15.620499351813308 N. Reported residual approximately 6.2804e-8 N therefore gives 4.0206e-9, below the unchanged 1e-8 relative gate. This fixed reference is stricter than the driver's lambda-scaled reference for this final state; production and solver gates are unchanged.

[V3 inputs](d3_multiple_beam_rigid_v3_20260930.inputs.json) SHA256 `05e7f1169459268a2f054bc48817d9baeca5942c238b308aa8215574240bccdd`; [log](d3_multiple_beam_rigid_v3_20260930.log) `ba8256c7c52ebecc6b954a184b6faa0ab33b23d90fc85c8924f07695f6eccbf7`. Only the previously failed displacement test ran: 1 PASS, with the two passed V2 additions excluded; 3.708747 s / 259.756 MB under 180 s / 1 GiB. All 442 V3 bindings match. V2's sole current mismatch is the test's isolated unit correction; its original source snapshot is retained.

Final test SHA256 `9070aa53a4bb88d2f502959e7031d6d786cbeab91c6306d29e8f6208141e7aac`; example `9daf746bb00ae3adf19ba361b9a26b9f5141289b58f7ce65774358c93c5553c6`; guide `7559874fbaf6de77ad1b79cf33db42b0be128a999da6ab52cde0098cde7752a7`. This adds a locally tested ordinary displacement fixture to the preceding scope; coupled sphere lifecycle, complete restart byte parity, general scientific accuracy, installed admission and release remain unestablished. No reviewer numerical run or source change was performed.
# D2 multiple projected pairs: independent development review

2026-09-30. Read-only inspection of composition, admission, global assembly, results and restart ownership; no source edits or numerical executions. **No remaining concrete composition-code blocker was found after the corrections below. The supported local evidence closes the named operator, displacement-path/restart, ordinary displacement-publication and bounded active ordinary-force checks.** No scientific acceptance, installed admission, D2 completion or release follows; the previously accepted artifact is unchanged.

## Reviewed source and composition

| Current file | SHA256 |
|---|---|
| [multiple_projected_pairs.py](../../src/anysolver/general_contact/multiple_projected_pairs.py) | `c42f072d4a6173305a2628d971073757e7f9f2981584f0d19d96a789db508f02` |
| [core.py](../../src/anysolver/general_contact/core.py) | `9cd9844f92e6ca4938bb0b4dd8c4d589801389e760a33835f1beaeddff900a31` |
| [static_path.py](../../src/anysolver/general_contact/static_path.py) | `44b11ab1cecdc020a6c1ef71a7e40f166f0656c94e0502fdeb5ad212f02c353e` |
| [nonlinear_static.py](../../src/anysolver/nonlinear_static.py) | `d42289776ddee3285691588028838513a0c1e855ea16e77deb50eed6df2e5525` |
| [focused test](../../tests/test_general_contact_multiple_projected_pairs.py) | `4e1ff0718e3f079404f7e8057a3831851f8cbf1a566bcca148fe251f956de02e` |

Each explicit shell child undergoes existing projected-law validation and retains its work, full global coordinate force/tangent map, own dimensional gap gate and restart contract. The aggregate adds these operators on the same authoritative DOFs. Its active count/storage/wrenches are sums; gap success is the conjunction of child decisions, not a comparison of one minimum gap against a fabricated common tolerance. Sorted interaction identities and nested contracts bind each pair. Pure projected pressure remains pose-derived with zero multipliers and no committed contact history. Aggregate Cartesian candidate counts and source-node pressure counts are conservative; duplicate unordered element/material-side pairs and shared source/target material nodes within a pair reject before solving. This is explicit composition, with no automatic/self-contact, rigid-body or augmented-law admission.

Independent integration oracle: uniform gaps give `p=300/200 Pa` over `.81 m²`, upward source forces `243/162 N`, opposite target forces and moments about the same global origin. Downward actuator reactions are `−243/−162 N`. Normal directional checks include both bodies; child law/work arithmetic is reused by source impact, not newly qualified for arbitrary geometry. The added shared-source fixture has adjacent represented areas `.81/.09 m²`, hence `243+18=261 N`; it does not assert general spatial accuracy or coverage.

## Findings, corrections and retained evidence

1. Multi-pair `contact_scope` originally dropped `analysis_control`, allowing direct unsupported-control activation. It now forwards the actual control through aggregate validation; the negative arc-length scope check passed.
2. Ordinary result publication originally required nonexistent aggregate scalar `gap_tolerance` and `stiffness`. The manager now supplies per-pair enforcement settings, and the ordinary driver preserves them without inventing common values. Existing single-pair reporting remains on its original branch.
3. Nested child NumPy scalar values blocked standard JSON export. The new aggregate payload now converts `np.generic` values with `.item()` through dictionaries/lists/tuples. This preserves the issued float64/int/bool certificate values; it is a result-shape adapter, with no change to child kernels, legacy result APIs or scientific data.

| Evidence | Disposition |
|---|---|
| [V1 log/resource](d2_multiple_projected_pairs_v1_20260930.log) | Three focused controls PASS; path assertion NONPASS from expecting an extra initial history row. Raw failure retained; 22.179 s/349.753 MB. |
| [V2 log](d2_multiple_projected_pairs_v2_20260930.log) | Correct actual accepted history `[12,0,12]`, actuator sign and authentic open fraction `2/3`; affected path/restart test PASS, 29.681 s/362.938 MB. Final displacement, history and complete material states agree after public emitted-root write/read/resume. |
| [V3 log](d2_multiple_projected_pairs_v3_20260930.log) | Unsupported-control test PASS; ordinary fixture NONPASS before candidate solve because the existing continuation driver requires a nonzero proportional load. No driver relaxation. |
| [V4 XML/resource](d2_multiple_projected_pairs_v4_20260930.xml) | Previously failed ordinary displacement test PASS with explicit downward unit reference load, distinct stiffnesses/tolerances and independent `729 N` contact force; 13.249 s/341.570 MB. |
| [V5 resource](d2_multiple_projected_pairs_v5_20260930.resource.json) | **NONPASS timeout**, 180.044 s/416.600 MB, supervisor exit15. Log has one completed-test marker, but no final XML or two-case PASS. Ordinary force completion is unestablished; timeout alone identifies no production defect. |
| [V6 log/resource](d2_multiple_projected_pairs_v6_20260930.log) | **NONPASS**, 11.196 s/336.822 MB. Public force solve completed and gap passed, but both-pair activation assertion failed: a physical tip excursion does not imply weak nodal activation. |
| [V7 log/resource](d2_multiple_projected_pairs_v7_20260930.log) | **NONPASS**, 12.936 s/337.576 MB. Completed solver status preceded nested NumPy-bool JSON extraction failure; no later physical assertion PASS is inferred. |
| [V8 log/resource](d2_multiple_projected_pairs_v8_20260930.log) | Previously incomplete active ordinary-force check **PASS**, 13.171 s/337.506 MB, two active modes per pair, lower gap `−10.5345323 µm`, opposite full force/moment wrenches. Frozen per-node force `0.066422064777328 N`; this is an API/integration check, not independent response accuracy. |
| [V9 log/resource](d2_multiple_projected_pairs_v9_20260930.log) | New pure nested JSON-contract check **PASS**, 3.115 s/212.402 MB. No mechanics replay after the export adapter; final owner/test match the retained V9 snapshots. |

All retained processes used the stated 180 s/1 GiB caps. Current aggregate arithmetic is unchanged from the V1 snapshot; changes are actual-control validation and result publication/export. No-contact execution constructs no contact manager; these hooks supply no new no-contact mechanics evidence or timing claim. V5's shared-source completed marker remains explicitly distinct from a whole-run PASS.

## Force-fixture discriminator and scope

The saved [structural preflight](d2_multiple_projected_pairs_force_preflight_v1_20260930.json) and [independent Q1 weighting](d2_multiple_projected_pairs_force_weighted_preflight_v1_20260930.json) discriminate V6 correctly: final-cell unit-force displacement is `.001248+.000624xi m/N`; far-mode weighted `xi=2*.8/3` gives `.0015808 m/N`. A `105 µm` tip therefore gives only `88.667 µm` weak excursion. V8's prospectively derived load instead predicts `105 µm` maximum weak excursion and `124.342 µm` physical excursion, retaining the `100 µm` clearance and `50 µm` physical-gap budget. No cap or tolerance changed, and V5–V7 remain failures. This closes the named active force-route exercise; it does not repair/regrade prior radial or point-load spatial failures, qualify arbitrary pair networks or establish full D2 acceptance.

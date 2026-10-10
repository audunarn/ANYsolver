# S3 physical-side orientation: supporting source review (2026-10-08)

Scope: source-ready, same-family OpenAI review of the opt-in S3 chart orientation, example and tests. No numerical jobs were run. This report is supporting scrutiny, not independent engineering acceptance.

## Source findings

- **No consequential defect found in the reference chart construction.** The desired raw chart normal `role × side_sign × physical_director` gives −z for both faces of the matched lower-source/upper-target physical pair. When the raw reference normal has the opposite sign, `_physical_side_adapter` exchanges local corners 1 and 2 in its material node IDs, immutable reference positions and corresponding three-row sparse work-map blocks together (`src/anysolver/general_contact/s3_patch_static.py:88-108`). The structural element, physical director, side offset, material node and element IDs remain unchanged. `MovingS3PatchPrimalMortarPenalty` uses sorted unique material node IDs for source pressure and target geometry (`src/anysolver/general_contact/s3_patch_mortar_energy.py:138-154`), so local winding does not rename pressure unknowns. Automatic source selection uses unsigned reference median face area and retains the coarse lower body's role (`src/anysolver/general_contact/automatic_domain.py:282-283,345-358`).

- **Covariance has a specific domain.** The algebraic row-permutation identities for scalar work, residual pullback and tangent action hold after both ±director declarations yield the *same physical skin map and directed chart*. They do not compare the new valid +z chart to the historically invalid +z legacy chart, whose raw normal has the opposite signed gap. `tests/test_general_contact_s3_physical_orientation.py:308-353` checks equality of the actual matched reference positions/work maps, tilted-pose P1 scalar support and weighted gaps, contact residual, directional tangent action and two finite differences. `tests/test_general_contact_s3_physical_orientation.py:380` checks historical +z legacy refusal. Coupled structural parity is tested separately by the staged ± lifecycle (`tests/test_general_contact_s3_physical_orientation.py:290-303`); it is not inferred from contact covariance.

- **Admission and compatibility appear narrowly scoped.** Public validation requires a contact path, native S3 physical top/bottom faces, projected penalty, Jet2 S3, whole-face gap route and nested enforcement (`src/anysolver/general_contact/core.py:607-621`). Direct patch construction additionally requires the refined projected S3 route and rejects augmented law (`src/anysolver/general_contact/s3_patch_static.py:211-220`). Friction is refused before path work (`src/anysolver/general_contact/static_path.py:410-415`), and static solves without a path refuse the selector (`src/anysolver/nonlinear_static.py:7919-7926,8021-8024`). The default `legacy` value is omitted from the shared automatic settings contract (`src/anysolver/general_contact/core.py:27-34`), patch and path restart settings; the nondefault value is included. Checkpoint contract validation precedes `model.apply_boundary_conditions()` (`src/anysolver/general_contact/static_path.py:588-617`). The source-ready tests include an actual historical checkpoint/identity read, selector mismatch, unused route, friction and precancellation checks (`tests/test_general_contact_s3_physical_orientation.py:356-390`). These are source observations; the tests had not run at review time.

## Limits and recommendation

Release the reserved bounded development discriminator only after the lead checks effective runtime/artifact identity and the tests' actual outcomes. The S3 whole-face swept lower bound still uses floating midpoint/normal controls and a 128ε heuristic, without directed finite-precision enclosure of sparse mapped endpoints (`src/anysolver/general_contact/s3_pair_static.py:133-169`; `src/anysolver/general_contact/s3_patch_static.py:883-889,1027-1052` in the preorientation source). Accepted-pose rational checks and matched contact-map covariance do not qualify every solver trial or arbitrary finite rotations. A refused trial in the new source test ends beyond the gap budget; it demonstrates endpoint refusal, not an isolated interior crossing with admissible endpoints (`tests/test_general_contact_s3_physical_orientation.py:343-346`). No acceptance or release conclusion follows from this review.

## Lead late V2 admission disposition

A direct multiple-beam transient branch bypassed shared core validation; V1's
all-transient refusal claim was unmet. Lead inspected/adopted an admission-only
transient.py guard and actual public legacy-valid fixture test with inventory,
manager and boundary mutation traps, preserving wrong-type/default behavior.
Focused V2 refusal and current CLI pass. V2 changes only transient.py vsV1;626
other payloads identical, including the four reviewed static contributors.
Lead independently inspected627 payloads/4083 private imports and all saved
job/input/runtime/results, zero discrepancies,102.68246909997833s exact. Twelve
passing cases plus current CLI; old prefix failure and V1 incomplete claim remain
preserved. Supporting V1 review above retains its scope; this is lead development
closure disposition, not independent engineering acceptance or release.
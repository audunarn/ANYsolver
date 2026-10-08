# Prescribed translating planes — development result

Parent `9ef78d5b`, isolated `codex/contact-main-reconcile-20261001` worktree.
[Scope and prospective checks](../C6_TRANSLATING_PLANES_SLICE_20261002.md).
Implemented and installed-tested; no C6 engineering acceptance or release.

## Physical and lifecycle result

Named immutable physical-time histories translate fixed-normal planes through the
shared elastic classical B2/B3 Newmark driver. Single/multiple pair geometry,
distributed line work, actual mass, individual gap budgets and complete relative
Hermite/Bernstein path bounds remain authoritative. Combined tool/load knots are
landed on with explicit arithmetic resolution checks. Old fixed profiles and
static `path_translation` contracts remain unchanged.

Results separate nodal input work from per-body prescribed tool input
`-integral F_rigid dot dpoint`; embedded integration discrepancies are reported
separately. Temporal support roots partition work integration and a conservative
geometry screen guards zero-rule intervals. Floating roots and embedded estimates
are not certified continuum work error bounds. Limits fail before physical commit;
temporary quadrature poses restore on exit. V5 restart binds motion/settings and
each body's accumulated work/error. New tool profiles reuse accumulated Newmark
acceleration updates to avoid position-subtraction amplification at short steps.

Eighteen new checks cover independent scalar forced Newmark/impulse and polynomial
tool work on B2/B3, elastic energy time refinement, opening/recontact through
velocity knots, named multiple tools, deforming B3 partial contact and momentum,
relative polynomial extrema, missed/grazing pulses, knot feasibility, large-epoch
nearest ownership, active split restart, incompatible/tampered checkpoints,
quadrature exhaustion, cancellation and exception cleanup. Six installed CLI
variants exercise fixed and translated examples. Toy gap budgets are not
qualification settings or application recommendations.

## Terminal evidence

Installed package `C:/ANYworkspaceWork/contact-translating-plane-package-20261002-v3`:
**100 passed**, one coherent final run, **19.386 s / 313475072 B** sampled tree peak.
Limits: 180 s / 999292928 B. All **452** source/wheel/site Python modules match;
211 imported solver modules resolve to the isolated installed site. Effective
JIT off and BLAS/Numba thread count 1 are checked before and after execution.
Wheel SHA256 `036bf3061074a9636ffd19561dbaaa3429927868286b6b9c8be3389018165897`.

The selection includes all translation, multiple-plane, single-plane, complete
beam-time-bound and static multiple-beam fixtures; named old Q4-load and S3-history
restart checks; and all six beam CLI variants. This is focused compatibility,
not the full release or no-contact performance campaign. [Guide](../../GENERAL_CONTACT_C6_CLASSICAL_BEAM_DEV.md).

## Retained failures and independent scrutiny

| Evidence | Actual disposition |
|---|---|
| Source v1 | 8 pass / 2 fail: real missed pulse-work error; independent cubic fixture coefficient defect separately corrected |
| Source v2 | 2 corrective passes |
| Source v3 | 10 pass / 1 fail: misplaced test assertion, corrected without kernel change |
| Source v4 / v5 | 4 / 1 passes: pulse, deforming/multiple tools and scalar energy refinement |
| Source v6 / v7 | 2 review counterexamples fail, then 4 corrective passes: unreached knot and minimum-step roundoff |
| Source v8 / v9 | 1 nearest-knot override failure, then 4 corrective passes including distinct near-terminal time |
| Installed v1 | Superseded build only, no tests executed |
| Installed v2 | 96 pass / 3 fail: roundoff-sized terminal steps; supervisor display failed decoding retained Unicode output |
| Source v10 | 17 pass / 1 fail: 1.388e-9 acceleration restart discrepancy exceeds unchanged 1e-9 comparison |
| Source v11 | Restart discriminator passes after accumulated acceleration reuse |
| Installed v3 | 100 passes; all above affected paths checked on final artifact |

Mistral's initial Read review identified pulse aliasing and time-grid risks; its
follow-up reached its limit without a final assessment. OpenAI's bounded Read
review identified the three knot counterexamples and decimal-ceil inconsistency.
Lead checked source/equations and ran the retained discriminators before final
installed execution. [Source adjudication](source-review-adjudication.md) records
review limits; none of these model reports confers independent science acceptance.
Raw logs, fixtures, wheels, identities and final candidate bytes are in `raw.zip`.

Finite rotation, free rigid inertia, caps, radial/beam-pair/shell impact, friction,
nonlinear materials and broad temporal/enforcement qualification remain required.
Accepted static subsets are unaffected; application admission stays false.

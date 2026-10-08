# C5 S3 pressure/history development slice — 2 October 2026

## Result and scope

Fixed-material S3 friction now participates in the ordinary nonlinear static path:
shared mortar pressure, both-body physical work, pressure/frame tangent coupling,
accepted-step history, release/recontact and bound split restart. The independent
retained-history rigid-spin counterexample is reproduced and corrected. This is
development evidence, not general C5 scientific acceptance, application admission
or release. D2–D8 and all required C0–C9 outcomes remain active.

The explicit profile is `S3_FIXED_MATERIAL_PRESSURE_COUPLED_STATIC_DEV_V1`.
It uses elastic S3 V2D, the declared normal penalty law, fixed material quadrature
and one containing target facet for each entire source facet. Weights must sum to
the source reference area. Physical opening releases traction; partial cuts and
leaving the declared facet fail. No moving-partner/facet-transfer, moving-overlap
friction integration, beam/native friction, plastic material or arc-length claim.

## Executed checks and identities

Parent `fdcfa9894e0f731d6da49743371cd7c922d432a6`; candidate source hashes are in
the retained source manifest. Final installed wheel SHA256:
`b796c57516600cfb3546a5cf210b55f623136cb7ade9bb673e446beaff160c6b`.
455 source/wheel/site Python modules match byte-for-byte; all 236 solver imports
are from the isolated installed site. Python3.14.2, actual JIT off and BLAS/Numba
threads1 are recorded, checked before/after execution.

Final coherent installed selection: **23 passed**, 32.8714166 seconds elapsed,
176373760 bytes sampled process-tree peak RSS, under180s/999292928B.
Artifact and scripts: `C:/ANYworkspaceWork/contact-friction-static-package-v2-20261002`.
Selection: the three friction test files and the standalone installed example.
Source v6:21 passed in26.81s (supervisor28.3829603s/182382592B); subsequent targeted
cut-face correction passes. These are development runs, not a full release suite.

Checks include independent uniform pressure/traction, slip pressure cross derivative,
smooth directional force derivative, both-body balance, real structural tangential
response, stick/slip/reversal/open/recontact, positive dissipation, identical split
history, changed-friction checkpoint rejection, invalid candidate with unchanged
history, real-token cancellation/context cleanup, and the runnable example.
The retained nonproportional-slip check independently constructs a common physical
spin and verifies zero work and force invariance across commit at unchanged pose.

Run scripts, fixture hashes, XML inventory, imported paths, full identities,
execution records and failures are retained in raw.zip. The runtime is measured;
no balanced twofold speedup or no-contact regression claim follows from it.
Reduced-column differentiation follows the existing constraint transformation
contract and retains full physical force/reaction rows. All standalone derivative
checks use complete authoritative columns.

## Retained failures and decisions

- v1:3 failures; unsupported use of Jet2 with the unprojected penalty profile.
  Candidate v2 explicitly selected the supported projected finite-penalty law;
  no historical normal profile/default was changed.
- v2:2 local passes/1 integrated rejection at a stick/slip branch. Complete force
  differencing was replaced by the existing traction chain derivative plus bounded
  geometric/pressure derivatives; generalized branch selection is explicit.
- v3:coupled solve completed, but a test incorrectly demanded tangential strain
  after opening and zero-slip recontact. The discriminator now observes the actual
  sliding increment snapshot with its original1e-7 threshold. v4:3 passes.
- Independent review found omitted transport of retained elastic history in the
  local work map. The frozen counterexample measured0.20000000000004547 of spurious
  common-spin virtual work and failed. Adding that transport, with a separate
  relative-increment derivative to avoid double counting, closes the targeted
  rigid-spin/unchanged-pose commit test.
- v5 exceeded the180s shared development limit when the old full S3 normal test
  module was added. No terminal pass verdict; no cap increase or formulation
  conclusion. v6 confines execution to the changed friction behaviour.
- Initial installed artifact:22 coherent passes,32.4228015s/176889856B. A source
  cut can leave all fixed quadrature points inside while invalidating their full
  reference-area support. Its separate pre-guard test failed; whole-facet support
  and area-weight checks were added. Final artifact has23 coherent passes as above.

## Independent scrutiny and remaining work

Bounded Mistral Read first failed sandbox executable access; the authorized
escalated call executed source inspections but exhausted6 turns without an
assessment. It is incomplete review evidence. No repeated larger retry was used.
Separate OpenAI Read scrutiny found the retained-history defect, reviewed its
correction and then the full-facet guard; no further concrete blocker was found
within this fixed-material development scope. The reviewer performed no edits or
numerical runs. The final guard is checked at candidates; it is not a general swept
full-facet coverage certificate. Source review is not engineering acceptance.

Next: deformable-target, nonproportional/changing-normal coupled discrimination,
then persistent material-surface correspondence and history under quadrature
repartition/facet crossing, with production derivatives and C5 numerical acceptance.
Friction/normal-result recovery and general capability admission must follow those
mechanics. Existing no-contact regression and scientific/release gates remain.

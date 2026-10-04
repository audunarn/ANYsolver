# Opt-in fixed-plane hemisphere support review

Read-only supporting source assessment, 4 October 2026. Repository: `C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001`. Scope: `beam_hemisphere_support.py`, `beam_hemisphere_plane.py`, related `core.py` setting/dispatch and necessary inherited geometry/work symbols. No numerical execution, test duplication, repository edits, Git mutation or engineering acceptance. Policy remains revision `2026-09-24.2`.

## Reconciled findings

### P2 — different obstacle family admission: resolved

The lead corrected the initial compatibility-gate finding during this review. Current `validate_hemisphere_plane_contact` delegates to `validate_general_contact` with `beam_end_cap_work='owned_point'`, retaining common selector and analysis-control checks. Current `contact_scope` also validates the requested analysis control before selecting the manager. The earlier silently ignored beam/S3/acceleration selectors and invalid analysis-control findings are therefore resolved by source inspection.

The replacement delegation introduces a narrower admission problem: the new validator has no explicit `body.kind == 'plane'` / fixed-body check. A correctly formed one-body sphere or cylinder definition can pass generic validation through the radial-ends profile, then be reported valid with the new fixed-plane hemisphere profile. `HemispherePlaneManager` subsequently rejects it through its inherited plane-only constructor validation. This is validation/runtime admission disagreement, rather than actual sphere execution.

Require a fixed plane explicitly, or preserve `validate_beam_plane_contact` issues in addition to the delegated generic compatibility gates. A discriminator must use a properly formed `RigidContactBody(kind='sphere', normal=None, radius=...)` or a valid cylinder, not a malformed plane descriptor relabeled as a sphere. Relevant symbols: `beam_hemisphere_plane.validate_hemisphere_plane_contact`, `core.validate_general_contact`, `core.contact_scope`, `_BeamPlaneManager.__init__`.

Final reconciliation: current `validate_hemisphere_plane_contact` explicitly appends an invalid-profile issue when `body.kind != 'plane'` or `body.path_translation is not None`. This closes the different-obstacle-family admission defect while retaining delegated generic compatibility gates. Source inspected directly; the lead reports nine passing source03 checks, including correctly formed sphere, analysis-control, acceleration and beam/S3-selector mismatches. This reviewer did not execute or independently accept those tests.

### P3 — candidate indexing before validation: resolved

`HemispherePlaneManager.evaluate` calls `_end_ownership_admissible(u,u)` before inherited `_BeamPlaneManager.evaluate` checks vector size/finiteness. The override indexes `start[cell.dofs]`; a too-short displacement raises `IndexError` instead of the inherited explicit invalid-displacement `ValueError`. Validate size/finiteness first, or factor/share the inherited check. This affects malformed-input behavior, not the admitted physical work law.

Final reconciliation: current `evaluate` now checks the flattened candidate's size against `total_dofs` and requires all finite values before calling `_end_ownership_admissible`. Invalid vectors raise the explicit `ValueError('hemisphere plane displacement is invalid')` before curve indexing. The source change closes this finding.

## Mechanics assessment

`hemisphere_plane_work` represents a hemisphere oriented by the actual B2/B3 centreline endpoint tangent v. With unit plane normal n, positive endpoint height h, and beta=`n·v/|v|`, its support gap is `h−r` for beta<=0 and `h−r*sqrt(1−beta²)` for beta>0. The branch, tangent coefficients, cross-product discriminant, rim support point and conjugate gap expression match that equation. B3 midnode tangent terms are seeded, so the rim contribution includes the necessary force couple.

At beta=0 the gap and first derivatives agree. The Hessians differ; selecting the sphere Hessian is a permissible one-sided member of the generalized Hessian of the C1 piecewise-smooth energy. It does not claim a unique classical Hessian at the seam. At the parallel-rim singularity the positive-height domain makes the penalty locally open, so zero pressure permits the supplied plane-height derivatives without inventing a force. The helper correctly refuses zero tangent and nonpositive height.

`HemispherePlaneManager.evaluate` adds `ke*g*gradient` and `ke*(gradient*gradientᵀ+g*hessian)` to all relevant translational node DOFs. It accumulates physical moment from the same nodal forces at current positions. Under rigid rotation of all involved nodal positions this is the cap support force's skin-point moment; reporting a force only at the cap centre would omit the rim couple, but this implementation retains it. The fixed plane's equal/opposite resultant and moment are reported. Both are source-derived observations; runtime balance remains to be measured by the lead's tests.

The line contributor retains its reference-length N/m² law, while the cap retains N/m. The opt-in profile/restart identity is distinct from the legacy owned-point law, and `_line_definition` disables legacy cap work before adding support work, avoiding duplication. No empirical stiffness relation or blending appears in the inspected implementation.

## Swept path and restart assessment

`_minimum_gap` computes the exact quadratic B3 plane-height minimum in the material interval, normalizes by the literal normal norm using an outward lower bound, then subtracts the radius. This is the conservative whole-centreline radius envelope, rather than only the new hemisphere support minimum. For affine structural increments and a fixed plane, every centreline station's plane height is affine; if the envelope is admissible at both states it remains admissible throughout. Every oriented hemisphere lies within its endpoint radius ball, so no separate cap-orientation temporal gap sweep is needed for this envelope-bound scope.

The overridden `_end_ownership_admissible` replaces ownership rejection with `regular_curve_path` over each full selected physical curve. That existing exact Bernstein certificate covers intermediate tangent collapse, rather than merely checking the endpoint states. The positive-height helper restriction is compatible with the admitted envelope states because `gap_tolerance < radius` implies centreline height is strictly positive. Trials violating the envelope may still fail the helper during raw evaluation; the admitted swept-state claim is narrower than arbitrary candidate evaluation.

`restart_contract` records the distinct work selection, hemisphere geometry revision, conservative envelope revision, all-material-node topology revision, actual selected physical ends, separate stiffnesses and swept subdivision bound. I found no changed-physics collision with the legacy profile in those recorded fields. It should continue to name the conservative envelope clearly in user-facing results when presenting minimum gap; it is not an exact material-section skin-gap profile.

## Scope limit

This remains a frictionless centreline-envelope plus actual-tangent hemisphere-support spring. It supplies no material section rotation DOFs, spin velocity, cap surface material labels or friction history. It must not be promoted as the new complete material round-surface/friction profile or as C0–C9 acceptance. The centreline-tangent choice is explicit here and mathematically supports this narrow model; a section-oriented surface profile requires the authoritative section-frame work map described in the earlier `source_review.md`.

All actionable findings from this supporting review are closed by inspected source changes. No further equation, force-couple, swept or restart defect was identified within the reviewed scope. Other runtime fixture failures and their retained logs belong to the lead's execution evidence and were not reclassified by this source reconciliation. The lead owns execution, test evidence, reconciliation and acceptance.

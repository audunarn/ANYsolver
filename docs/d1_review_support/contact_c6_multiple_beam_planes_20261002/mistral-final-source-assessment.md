Review complete. Both batched reads are used; here is the final assessment.

## Findings on the three asked properties

**1. Per-pair acceptance against own limits — holds.**
`_beam_complete_path_gaps` (transient.py:725-741) iterates every child of `MultipleBeamRigidManager.pairs` (or the single manager) and gates each pair independently: `admissible = admissible and bounds.lower_gap >= -child.gap_tolerance` — each pair's own registered tolerance, not a shared one. The step acceptance gate (transient.py, converged branch) requires **both** `contact_result.gap_tolerance_met` (which `MultipleBeamRigidResults.gap_tolerance_met` defines as `all(...)` over pairs) **and** `beam_path_admissible`. Since `lower_gap` is a certified convex-hull lower bound with outward one-ULP padding (beam_temporal_bounds.py `_outward`), true gap ≥ lower_gap, so no inadmissible pair can pass. The transient `_admit` gate restricts rigid bodies to `kind == "plane"`, so every child is a `_BeamPlaneManager` with the point/normal/radius/cells attributes `beam_hermite_gap_bounds` requires — no radial-child attribute mismatch is reachable in this profile.

**2. True aggregate split budget — holds.**
`remaining = controls.maximum_beam_swept_subdivisions` is decremented by each pair's `bounds.subdivisions` and passed as the next pair's cap, so total splits across all pairs in one enclosure call cannot exceed the control. `beam_hermite_gap_bounds` counts one subdivision per heap pop (each pop is one binary split), returns `subdivisions` exactly, and on exhaustion **raises** `BeamHermiteGapBoundsError` explicitly (with the unresolved interval in the message) — it never returns a silently widened or unenclosed bound. Budget exhaustion therefore fails closed, not open.

**3. Restart binding of changed multiple-pair definitions/settings — holds.**
`_restart_analysis_contract` (transient.py:295-347) binds `allow_multiple_beam_planes_dev` as a distinct controls key, and under `allow_classical_beam_dev` binds `beam_swept_gap_tolerance_m` and `maximum_beam_swept_subdivisions` — exactly the two controls the aggregate path gate consumes. `MultipleBeamRigidManager.restart_contract` (multiple_beam_rigid.py) includes the profile, `composition_revision`, one child contract per interaction **name** (pairs canonically sorted by name in `_parts`, so reordering cannot alias), and `aggregate_candidate_limit = settings.maximum_candidate_pairs`. Any change to the pair set, a pair's child contract, the aggregate candidate limit, or the multiple/classical flags changes the analysis fingerprint and rejects the checkpoint.

## Verdict

**No counterexample found** for the asked properties.

## Exact review limits

- Read in full: `beam_temporal_bounds.py` (221 lines) and `multiple_beam_rigid.py` (154 lines).
- `transient.py` (1401 lines): lines 1 through the `_beam_complete_path_gaps` body and the step loop through the acceptance block (~line 1290) were read; the final tail (~lines 1290-1401 — post-acceptance checkpoint emission and the non-converged cutback branch after the Newton loop) was truncated and **not** read. I therefore did not verify whether an inadmissible beam path or a raised `BeamHermiteGapBoundsError` triggers a cutback versus aborting the solve — but both fail closed, so no acceptance bypass exists in what was read.
- Child managers' own `restart_contract` bodies (`beam_plane.py`, `beam_radial.py`) were not read; per-pair contract completeness is attested only through the multiple manager's composition of them.
- Per the task constraints: source reasoning only, no numerical runs, no edits, no nested workers.

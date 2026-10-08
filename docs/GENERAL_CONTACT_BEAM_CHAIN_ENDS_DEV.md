# Physical endpoints of classical beam chains

4 October 2026. **Implemented and installed-tested development; no independent
engineering acceptance, application admission or release.** Profile:
`CLASSICAL_B2_CHAIN_ROUND_TUBE_PHYSICAL_ENDS_CONSISTENT_STATIC_DEV_V1`.

## Use and scope

Select connected, nonbranching classical B2 chains, up to sixteen cells per side
within the existing pair-candidate cap. Both surfaces declare an explicit radius
and `beam_end_caps='hemisphere'`. Specify distinct `line_stiffness` (N/m²),
`endpoint_stiffness` (N/m), dimensional gap tolerance below the combined radius,
`pair_motion='general'`, `beam_chain_tangent='consistent_dev'` and an explicit
line integration tolerance. Existing elastic isotropic scalar-section/von-Karman
restrictions remain. No new stiffness recommendation or hidden stabilization is
introduced. One-cell physical-end routes and historical uncapped routes remain.

The [example](../examples/general_contact_beam_chain_ends.py) presses nonmatching
4/3-cell bars together through ordinary `solve_static_nonlinear`. `--cells` and
`--target-cells` select two to sixteen cells. It returns integrated reactions,
separate line/point storage, dimensional gap and a restart checkpoint. The
capability report retains `admitted_for_application=False`.

## Work and material features

The distributed potential remains the symmetric half-weighted nearest-curve line
potential. The existing consistent sparse assembly retains moving nearest-owner
boundary terms and cross-cell blocks. Physical-end springs are added to that
complete system, including both interacting bodies.

All classical material-node incidence defines genuine ends, including unselected
cells and B3 middle-node attachments. For each genuine cap, exact rational
squared-distance comparisons select the closest opposing curve feature. One
owned end/interior spring uses the complete reduced projection Hessian. Strict
clamps from two adjacent selected cells to the same material node have identical
point work: one source cap may contact this represented junction. Shared identity
does not follow from coincident coordinates alone.

Active distinct nearest ties, projection equalities, zero ownership and
nonphysical selected-boundary clamps reject explicitly. Active cap/cap choices
must be reciprocal nearest physical ends; one full spring is counted once.
Nonreciprocal choices reject instead of changing energy multiplicity during a
closed partner switch. This is the declared outward-hemisphere point penalty,
not continuous hemisphere integration or a Hertz-pressure model.

Results identify source material nodes, target feature/node and tied element
IDs. Full body forces/moments use authoritative coordinates and global-zero
moment origin. Point and line regularization storage remain separate.

## Trials, state and restart

Every affine static trial requires physical-curve regularity, whole-chain gap
admission, endpoint nearest-feature/ownership and line-projection checks. Bounds
use exact rational/Bernstein operations; finite unresolved subdivisions fail or
cut back, with no sampled-success certificate or dropped candidates.

Endpoint certificates run on common intervals across all physical ends. Each
end must be wholly open or have fixed nearest feature and ownership; potentially
active cap partners must match in both directions. Separate per-end certificates
are insufficient. Opening may permit changes. The pairwise line-plateau safeguard
is conservative and may reject an unresolved nonowner configuration; general
closed switches and dynamic trajectories are not admitted by this row.

Point work is disposable/stateless. Existing structural transactions own physical
commit/discard. Restart binds both chains, physical ends, represented junctions,
line/point laws, consistent tangent revision and numerical controls. Changed
definitions/topology/law/settings reject. Rejected candidates and actual
exception/cancellation runs preserve reusable physical origin and checkpoints.

## Evidence and remaining programme

[Evidence](d1_review_support/contact_chain_endcaps_20261004/summary.json) retains
candidate hashes, source parent, installed wheel and complete failed outputs.
Forty-two installed checks pass in 31.572 s with 336,089,088-byte peak process-tree
RSS under 180 s/953 MiB. JIT is disabled; actual pools/Numba threads equal one.
All 215 loaded solver modules and 498 installed package files match source.

An independent P1 two-bar energy/reference includes axial strain energy and
analytically integrated line/endpoint penalties. Matching 2/2 and 8/8 meshes and
nonmatching 4/3 meshes agree within 9.266e-15 relative displacement against the
1e-6 code-verification target. This verifies that discrete fixture, not arbitrary
beam accuracy or mesh/enforcement qualification. Coupled tangents/virtual work,
moving line-owner blocks plus cap work, shared-junction mapping, body exchange,
connectivity/order/covariance, force/displacement, active JSON restart, changed
definitions, cutback, exception/cancel reuse, example and inherited cases pass.

Ten measured runs/70 raw records retain a confounded nearest-tie test fixture and
the review-found swept reciprocity defect. The latter was reproduced before
correction; common all-end interval proof now rejects activation and finds a
valid prefix. External 1045-assertion geometry checks are supporting only, with
uninstrumented memory. Same-family source scrutiny is not independent engineering
acceptance. No general speedup or completion forecast is claimed.

B3 curved endpoint/target work, generalized closed feature transitions,
mesh/enforcement and independent engineering acceptance remain required. Native,
friction, dynamics, application/release and full C2/D3/C0–C9 completion remain open.

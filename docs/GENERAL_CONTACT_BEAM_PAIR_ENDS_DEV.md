# Two-body physical beam-end contact

4 October 2026. **Implemented and installed-tested development; no independent
engineering acceptance, application admission or release.** Profile:
`CLASSICAL_B2_B2_ROUND_TUBE_PHYSICAL_ENDS_PAIR_STATIC_DEV_V1`.

## Public use and boundary

Select one classical B2 per surface, an explicit round radius, and
`beam_end_caps='hemisphere'` on both surfaces. The pair uses explicit penalty
`line_stiffness` in N/m², `endpoint_stiffness` in N/m, dimensional `gap_tolerance`
below the combined radius, `pair_motion='general'` and an explicit line integration
tolerance. Existing elastic isotropic scalar-section/von-Karman restrictions apply.
Both bodies use their structural displacement unknowns. There are no hidden
springs, mass or damping. Shared material nodes are not admitted by this row.

The [example](../examples/general_contact_beam_pair_ends.py) pushes two axially
guided bars together. It uses ordinary `solve_static_nonlinear`, returns separate
line and endpoint storage, integrated forces/moments and a restart checkpoint.
The public validator/capability report describes executable scope and retains
`admitted_for_application=False`. Historical uncapped routes keep their dispatch,
law, profile and checkpoint identity.

## Discrete work and ownership

The distributed potential is the symmetric half-weighted sum of directional
line potentials using the actual B2 curves and reference lengths. Its exact
rational partitions and analytic derivatives reuse the consistent chain kernel.
Projection-clamp plateaus with active positive line measure reject explicitly.

Genuine ends use incidence of every classical material node, including unselected
elements and B3 middle-node junctions. A selection boundary cannot create a cap.
For a source physical end, the closest target coordinate is resolved by the
actual segment. Its outward cap owns contact only when separation dotted with
the source outward tangent is strictly negative. Active endpoint projection or
ownership equalities reject; an owned clamp to a nonphysical target end rejects.
Open features permit those changes.

Each owned end/interior feature contributes `.5*ke*min(g,0)**2`. A reciprocal
end/end feature contributes one full spring. It is not counted twice or half
weighted in addition to the line potential. This declared point penalty is not
integration over a continuous hemisphere and does not predict Hertz pressure.

The point residual is `ke*g*Dg`; its tangent is
`ke*(Dg outer Dg + g*D²g)`. Interior projection response is eliminated through
the complete reduced distance Hessian, including target-coordinate motion.
Both-body residuals, cross blocks and global-zero moments use the same work.
Fields report surface, element and material-node identities, target coordinate,
gap, feature ownership and endpoint force. Line/point storage remain separate.

## Path, state and restart

Exact rational rectangle minimization covers all four segment edges and any
interior stationary point, including parallel/near-parallel geometry. Outward
conversion supplies a conservative whole-pair gap. A Lipschitz bound uses every
cross-body endpoint relative velocity; gap, physical-curve regularity, endpoint
projection/ownership and distributed-line plateau certificates cover the affine
static trial path. Finite unresolved subdivision returns non-success/cutback.
Samples alone never certify opening or a hidden crossing. This is not a dynamic
trajectory or unrestricted feature-transition guarantee.

Endpoint work is disposable/stateless. Existing structural transactions own
increment commit/discard. Restart binds the profile, physical-end material nodes,
both surfaces, line/endpoint laws and integration/swept controls. Changed topology,
law or controls reject continuation. Exceptions/cancellation leave the model
reusable from its physical origin.

## Retained evidence and next obligations

[Evidence](d1_review_support/contact_beam_pair_endcaps_20261004/summary.json) binds
the candidate file hashes and installed wheel. Thirty installed checks passed in
6.650 s with 328,585,216-byte peak process-tree RSS under 180 s/953 MiB;
JIT disabled and actual numerical pools/Numba threads equal one. All 243 loaded
solver modules and 496 installed package files match source. The independent
two-bar displacement error is 1.084e-15 against the 1e-6 development target.

Checks cover independent line/point potential, full coupled directional work and
tangents, body exchange/connectivity/covariance, unique cap forces and wrench,
force/displacement control, fresh active JSON restart and incompatible law,
topology/settings, actual exception/cancel restoration, hidden gap/collapse,
non-dyadic finite-normal ownership roots, selected-cut rejection and the reviewed
intermediate line-plateau counterexample. Inherited no-cap/no-contact routes pass.

Ten runs/63 raw records retain the initial scalar-oracle quadrature and API-field
test defects. Supporting source review identified the intermediate plateau path
gap; its correction and isolated manager regression are retained. Same-family
scrutiny is not independent engineering acceptance. No speedup claim is made.

B3/chain physical ends, resolved closed cap transitions, mesh/enforcement
qualification, finite rotation, friction, native contact, dynamics, application
admission and independent acceptance remain required successors. Full C2/D3 and
C0–C9 completion are not established by this bounded slice.

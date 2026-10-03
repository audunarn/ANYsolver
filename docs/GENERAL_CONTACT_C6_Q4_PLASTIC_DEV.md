# Q4 plastic plane impact — bounded development profile

Status: implemented and source-tested development; engineering acceptance and
release remain open. This profile does not expand accepted D1/D2 shell capability.

Use `solve_transient_contact` with the existing `TransientConfig` and explicit
`ContactTransientSolverControls(allow_q4_plastic_dev=True)`. Optional
`save_q4_material_history_dev=True` saves accepted material states at output times;
`element_states` supplies the final accepted states. Both controls enter restart
identity. Defaults and historical elastic profiles remain unchanged.

The profile requires exact qualified Q4, an isotropic DNV material curve, positive
definite reduced mass, and one guided fixed-plane penalty interaction. It retains
three Lobatto layers and the existing von Karman structural route. It does not
admit S3, beams, free rigid bodies, prescribed-tool motion or load histories.
`LinearHardeningCurve` is unsupported by the existing Q4 return map; no fallback
or constitutive-kernel modification is provided.

Dynamic checkpoint V7 includes an owned material packet. The packet binds model,
full pose, complete element IDs and layer count, validates the accepted return-map
parent through the public Q4 boundary, and checks constitutive semantics even when
unkeyed hashes are recomputed. Restore precedes initial equilibrium checking;
resuming does not commit a second same-pose return map. Rejected candidates and
exceptions retain the physical committed origin. Exported state mutation does not
alter checkpoint content. Static checkpoint schemas remain unchanged.

Run `examples/general_contact_q4_plastic_impact_dev.py`. Its affine deviatoric
membrane and rigid normal modes are uncoupled. The DNV plateau yields during
contact and subsequently unloads. The independent reference solves the two
piecewise-affine Newmark equations directly and never calls production material,
contact or solver kernels. Separate physical-mode mass and force checks verify
the reduction. Compact accepted states expose plastic strain and alpha; the
example labels inferred stresses explicitly.

Source checks cover trajectory/material history, an active yielded split,
incompatible settings and material corruption, cancellation/exception, a forced
rejection after a yielded commit, and existing elastic/tool restart contracts.
These do not establish impact-induced yielding, hardening, nonproportional loading,
plastic work balance, mesh/time refinement or complete C6 acceptance.

Evidence and installed status: [slice record](d1_review_support/C6_Q4_PLASTIC_SLICE_20261003.md).

## Opt-in pressure-mode events

`q4_plane_event_subdivision_dev=True` selects a separate development profile for
guided Q4/fixed-plane elastic or DNV plastic impact. The actual normalized nodal
pressure gaps determine branch events; physical corner-gap checks remain separate.
Positive endpoint-duration proposals are equilibrated from the same committed
origin using acceleration-primary Newmark equations. Every proposed endpoint is
reequilibrated and its complete represented Hermite path is checked for every
pressure mode. Hidden crossings without a usable endpoint bracket cause bounded
cutback. This does not certify the exact continuous trajectory.

Controls are explicit: `plane_event_time_tolerance_s`,
`plane_event_gap_tolerance_m`, `maximum_plane_event_endpoint_evaluations`,
`maximum_plane_event_stage_evaluations` and the existing localization/cutback
limits. Stage/query budgets are shared across retries from one committed origin.
Failed query attempts are counted; candidates never commit material history.
`plane_event_stage_evaluations`, `event_endpoint_evaluations` and
`localized_contact_event_times` report work and represented event times.
The event time list also records certified gap-band arrivals at nominal endpoints;
it is not a list of exact continuum roots. An arbitrary truncated END inside that
band does not become a restartable localized boundary.

Elastic event packets use V8, plastic event packets V9. They bind event controls
and validate pressure support, normalized gaps, rates and departure phase against
restored coordinates; V9 retains the full accepted material parent. Old schemas
and defaults remain unchanged. Load history, moving tools, free bodies, S3 and
beams remain outside this particular event profile.

Run the example with `--events --dt 3e-5 --end .003`. Its energy diagnostic uses
the fixture's independently specified mass, elastic storage, plateau dissipation
`20*volume*alpha`, contact storage and zero external work. It does not generalize
that formula to arbitrary hardening/nonproportional paths. Source and isolated
installed development checks pass; engineering acceptance remains open.
[Event evidence](d1_review_support/C6_Q4_PLANE_EVENT_SLICE_20261003.md).

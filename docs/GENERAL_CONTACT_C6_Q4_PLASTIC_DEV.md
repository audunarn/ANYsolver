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

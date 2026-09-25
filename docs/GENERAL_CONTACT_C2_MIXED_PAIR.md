# C2 development profile: mixed classical B2/B3 contact

`CLASSICAL_B2_B3_ROUND_TUBE_DISTRIBUTED_PAIR_STATIC_DEV_V0` admits one
straight-reference B2 cell and one straight-reference B3 cell with declared
round centreline-tube radii. Contact is frictionless. It uses a symmetric,
half-weighted sum of the two directional distributed line-penalty potentials.
The B2 line is represented exactly in the quadratic curve kernel by tying its
virtual midpoint to the average of its two real end nodes. Residual and tangent
are pulled back through that same linear map. The B3 uses its actual deformed
quadratic centreline.

Use `examples/general_contact_round_b2_b3_pair.py` with explicit
`line_stiffness`, dimensional `gap_tolerance`, integration tolerance and
gap-certificate budgets. Both beams must be separate, elastic, concentric,
von Karman classical cells without endpoint caps or shared material nodes.
Force and displacement control use the ordinary nonlinear static route;
version-2 restart binds the mixed profile, definitions and numerical settings.

The focused mixed-pair checks cover an independent parallel-line energy and
force reference, B2 nodal-force mapping, paired wrench, smooth-branch
directional tangent, role exchange, an active displacement path and split
restart. The first mixed tangent trial exposed an existing near-endpoint
projection classification failure for a slightly tilted straight target; the
roundoff-aware feature classification is now exercised by that check. The
affected B2/B3 pair group passed 25 tests after the fix.

The example uses a 15 mm gap budget for a 50 mm beam radius. This is a
development setting and does not meet the programme's prospective
thickness/radius-scaled qualification budget. Mixed curved-target active
interval completeness, endpoint ownership, multi-cell beams, mesh and penalty
convergence, installed-package verification and independent acceptance remain
open. The profile is implemented and locally tested only.

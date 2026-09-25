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
The example's `--radius-scaled-gap` option commands 40 micrometres of closure
and checks a 50 micrometre gap budget for the declared 50 mm radius.

The focused mixed-pair checks cover an independent parallel-line energy and
force reference, B2 nodal-force mapping, paired wrench, smooth-branch
directional tangent, role exchange, an active displacement path and split
restart. The first mixed tangent trial exposed an existing near-endpoint
projection classification failure for a slightly tilted straight target; the
roundoff-aware feature classification is now exercised by that check. The
initial affected B2/B3 pair group passed 25 tests after the fix.

The first 50 micrometre trial then exhausted the curved-target interval scan
near a narrow open interval adjacent to contact. The retained captured pose
showed that its full-source-speed bound could not certify the open interval.
The updated scan computes the minimum distance between each uncertain source
interval's chord and the complete quadratic target by partitioning target
projection branches and checking their polynomial extrema. It subtracts the
maximum source-to-chord deviation and floating-point guards before declaring
an interval open. Independent sampled-distance controls, the captured pose,
the radius-scaled integrated path and the affected B2/B3 group passed 33 tests.
The integrated path reported a conservative lower gap of about -40 micrometres
within its 50 micrometre budget, nonzero contact and equal/opposite body forces.

The example's default remains the original 15 mm development gap setting.
The single radius-scaled path is a development check, not mesh, integration or
penalty convergence. General curved-target active-interval completeness,
endpoint ownership, multi-cell beams, refinement and independent acceptance
remain open. The profile is implemented and locally tested only.

Source `f5b7bd70a46d386ceec4154ef3ab8c2d9afa36cd` built an offline,
dependency-free-installed wheel (SHA-256
`1D79E74ECF84D4D1D3DBDB64D54445593F861B5F18C071AE432BBC41D5EBAE13`).
The installed import origin was checked, and the example's source and installed
outputs were byte-identical (SHA-256
`CD53FB37764490B12095608018AF0E004172091A81C575943D290D13539FC3AF`).
This verifies package routing for this development slice; no package was
published.

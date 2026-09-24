# General contact C1 development slice: S3 V2D against a rigid plane

The opt-in frictionless plane mortar now admits planar S3 V2D shells alongside
the earlier qualified Q4 profile. This extension is **implemented and locally
tested**, without independent engineering acceptance. The validator reports
`PLANAR_Q4_S3_RIGID_PLANE_PENALTY_MORTAR_V0` whenever the selected surface
contains S3; all-Q4 selections retain their previous profile identity.

S3 geometry comes from its physical reference director and
`material_surface_offset_from_reference`. Its top, bottom or midsurface
selection can therefore differ from the mesh reference surface. The P1
pressure functions use positive reference support over the S3 Hammer rule.
The contact residual and tangent act on its original displacement and
rotation degrees of freedom. Initial overclosure is rejected; the independent
vertex-gap check and affine swept trial bound remain in force.

This profile supports `von_karman` force and displacement control and the
state-free version-2 penalty checkpoint. It does not admit corotational S3
contact, warped Q4, moving planes, friction or impact. The plane is infinite
and fixed.

Run the [S3 physical-skin example](../examples/general_contact_s3_plane.py).
Its 0.05 m shell has a 0.01 m reference-surface offset; the mesh lies at
z = 0.035 m so the physical bottom skin initially touches z = 0. The 0.3 N
guided load yields a 0.3 N reaction and a -0.6 micrometre penalty gap.

Focused checks are in `tests/test_general_contact_s3_plane.py`: the coupled
reaction, offset force couple, local tangent and checkpoint continuation.
Independent review and registered engineering qualification remain open.

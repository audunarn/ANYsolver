# Native swept-round/S3 material-point development

The existing native field is r=(1-t)xc+t xc+1+Uc*lift and R=Uc R0(xi).
The new station helper exposes section-frame/position first and second rotational
variations using existing Jet2 with only three local rotational seeds. Section
frame is not mislabelled as a sheared swept-surface normal.

A distinct local native–S3 point contribution seeds15physical coordinates, then
maps to42native coordinates plus authoritative S3 DOFs. Gap uses actual surface
position and target skin plane. Normal penalty uses explicit Pa/m and reference
area; friction uses the same gap pressure and the existing objective Coulomb law.
Derivative includes frame/history transport, normal-pressure coupling, geometric
work and native chart-to-spatial connection. No surface quadrature is supplied by
this kernel; its positive area weight is caller-declared.

Eleven unique focused checks pass: section-frame/position second derivatives,
spatial covector tangent, fixed-centreline spin torque in stick/slip, actual gap
pressure, both-body tangents, wrench/rigid transport, nonzero-history tangents,
foreign partner/definition/first-touch/interior rejection and resource preflight.
All used180s/953MiB/JIToff through the portable development runner. See results.json
for source digests/resources and the retained logs. No installed/analysis or C5
acceptance claim follows.

Next: implement conservative whole-path gap/target-ownership certification using
actual native spatial increments and affine shell path. Reuse existing native/S3
Lipschitz geometry ideas with the full surface arm, not centreline lift alone.
Certify closed/open persistence; hidden opening/facet excursions cause subdivision
or explicit rejection. Then integrate a distinct surface-friction profile into the
existing retained owner with atomic accepted history/restart. Preserve its normal
line profile. No permanent attachment or generic FEModel insertion.

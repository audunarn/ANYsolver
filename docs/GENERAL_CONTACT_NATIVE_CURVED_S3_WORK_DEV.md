# Curved native material contact with S3 — development

The existing retained multiple-S3 owner admits the exact
`NativeCurvedMaterialS3Work` adapter under its own
`NATIVE_B3_GE_CURVED_MATERIAL_PATCHES_S3_STATIC_DEV_V1` profile. One/two native
beams and one to eight explicitly paired S3 interiors retain native internal
coordinates and all structural/contact blocks. The shell route remains elastic
small-rotation S3 V2D with its authoritative physical offset map. Mixed straight,
line and curved profiles are rejected. The straight activation controller is not
admitted into this curved profile.

[Example](../examples/general_contact_native_curved_material_s3.py) constructs one
curved elastic B3-GE and a deformable S3 top skin. The explicit law is
1e7 N/m³, gap tolerance30um, integration1e-10J/1e-8N/1e-6N/m,64intervals,
128path intervals. These are fixture controls, not application defaults. The
first-contact solve passes within120s; the three-target programme is continued
in bounded checkpoint stages. Do not infer that one uninterrupted cycle meets
the120s owner limit.

## Work and geometry

The shared curved Gauss8/16 axial/angular integrator retains actual fixed source
reference area. An18-coordinate local map includes both source stations, source
section rotation and all three target corners. Target-normal first/second
derivatives contribute shell/shell and native/shell blocks; the affine physical
skin map retains offset couples. Only the native42×42 block receives the
once-spatial conversion. Circular mapped-gradient bounds and whole-band axial
variation retain complete root-band error budgets. Quadrature differences are
estimates, not rigorous integration certificates.

The actual represented first corner anchors the target plane. Exact binary
partition-of-unity arithmetic preserves high/low relative positions. Whole
curved orientation and circumscribed skin-gap/rim bounds require complete
containment. Finite clipped overlap and physical rim contact remain unadmitted;
the circle bound can reject a physically safe selected arc.

Whole-path admission follows authoritative native translation/left-Exp and
affine shell increments. Target quadratic cross-product controls, with
product-conditioned arithmetic padding, bound orientation/area. Source
Bernstein-control rates include twice the physical half-cell lift. Moving-normal
and inward-edge rates bound gap and rim over the complete path. Unresolved
controls reject. Cancellation reaches the proof; coordinated physical commit
remains in the shared driver. Initial gap fractions and cheap geometry preflight
are proposals/screens; endpoint, work, path and equilibrium gates remain.

## Evidence and limits

Local independent quadrature, both-body wrench, smooth mixed tangent,
large-origin cancellation, axial fronts and endpoint-safe hidden target collapse
are checked. First coupled contact passes; installed artifact and restart stages
are recorded in the linked current ledger. Failed interval-budget, loose-bound
and initial gap-fraction candidates remain in raw candidate10 evidence.

**Independent engineering acceptance: no. Release: no.** Broader sections,
materials, pairings, finite overlap, convergence, friction, native dynamics and
application admission remain required by the full programme. Same-family
supporting scrutiny does not establish independent acceptance.

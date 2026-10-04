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

The example defaults to the first bounded target. Continue its unchanged
three-target definition through actual saved checkpoints:

```powershell
python examples/general_contact_native_curved_material_s3.py --checkpoint-out active.checkpoint
python examples/general_contact_native_curved_material_s3.py --through-target 2 --restart active.checkpoint --checkpoint-out open.checkpoint
python examples/general_contact_native_curved_material_s3.py --through-target 3 --restart open.checkpoint --checkpoint-out recontact.checkpoint
```

These commands use the package selected by the environment; the development
checks bind their imports explicitly to the recorded installed wheel. Each
subsequent stage requires the immediately preceding checkpoint. Local checks,
first contact, installed CLI recontact and staged exception/cancellation total
19 passes in five bounded jobs. All523source files/227imports match; JIT0/pools1.
The combined opening batch exceeded120s and remains NONPASS. Its real opening
checkpoint was validated by the completed recontact run, not retrospectively
counted as a passed batch. No uninterrupted-cycle120s claim follows.
[Exact source, wheel, fixture and resource identities](d1_review_support/contact_native_material_s3_20261004/curved_s3_summary.json),
[supporting scrutiny](d1_review_support/contact_native_material_s3_20261004/curved_s3_review.md).

## Multiple connected facets

`--two-facets` constructs two connected S3 triangles sharing an edge and a free
vertex. A single retained curved beam has two explicit source material selections,
native xi `(-.9,-.1)` and `(.1,.9)`, assigned to the left and right facet.
Native xi spans `[-1,1]`. The central interval and section end regions are
deliberately unselected. Each represented patch must remain fully inside its
own facet; this example does not implement contact across their common rim or
union-based projection. The normal law and dimensional controls are unchanged.

Both pair residuals and all native/shell blocks assemble into the same retained
system before solving. Their common free target vertex can couple the reactions.
The source patch selections and facet identities bind restart; a single-facet
checkpoint is incompatible with this mode. The default one-facet model and its
checkpoint identities remain unchanged.

**Independent engineering acceptance: no. Release: no.** Broader sections,
materials, pairings, finite overlap, convergence, friction, native dynamics and
application admission remain required by the full programme. Same-family
supporting scrutiny does not establish independent acceptance.

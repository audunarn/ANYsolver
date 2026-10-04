# Retained native material patch / deformable S3 — development

Source candidate `46ea65f6`, 4 October 2026. One strictly interior straight
B3-GE half-cell material patch now couples to one elastic S3 top physical skin
through the existing retained native/shell static owner. All 42 native and 18
shell coordinates remain; moving target normals and offset work are included.
This is implemented and installed-tested development, not engineering acceptance.

Run `python examples/general_contact_native_material_s3.py` in the reconciled
checkout. The example presses, opens and recontacts, reports both body wrenches
about the global origin, normal storage, continuous patch gap and checkpoint.
The experimental modules expose `NativeMaterialS3Patch`,
`NativeRetainedMaterialS3Work` and `NativeRetainedRoundS3Analysis`; public generic
FEModel/native insertion and application admission are unchanged.

## Work, geometry and transactions

For the admitted straight reference,
`x(t,alpha)=(1-t)*p0+t*p1+Uc*R0*rho(alpha)`.
The potential is `0.5*k*integral(min(g,0)^2 dA0)`, with explicit `k` in N/m³ and
fixed reference measure `radius*|reference chord| dt dalpha`. Axial active
integration is analytic; bounded angular Gauss8/16 controls energy, force and
tangent. Anchored trigonometric projection resolves near-extremum arithmetic;
unresolved queried angular boundary/extremum activation rejects before quadrature.
This does not prohibit first touch along a certified path.

S3 corners use the formulation-owned small-rotation map
`x_ref+u+physical_offset*(theta cross reference_director)`. This profile does not
introduce finite-rotation shell directors. The 60-coordinate derivatives include
target-normal changes, both-body blocks and physical section couples. Exactly
one native chart-to-spatial conversion occurs inside the shared area integral.
Reported shell orbital moments use physical corners, avoiding offset double count.

The existing native state owner, shell constraints and checkpoint chain are
reused. Candidate poses require positive reference orientation and whole-patch
rim clearance. The actual exponential native/affine shell trial path includes
material radius in gap and edge lever bounds; source orientation and reference
S3 orientation are certified separately. Bernstein controls conservatively
bound reference-normal positivity across the whole shell path. An unresolved
certificate rejects; safe paths can consequently require subdivision.

Physical commit follows all equilibrium/gap/path checks and checkpoint staging.
Cancellation or exception during staging retains the accepted native/shell prefix.
Definitions, numerical revision and settings bind restart; incompatible continuation
rejects. Both existing friction entry points explicitly reject this normal-area
owner. No friction history, transport or dynamics admission is implied.

## Evidence and remaining limits

Independent direct area quadrature checks energy, force and moment on full/partial
branches. Native finite section rotation, scalar virtual work, complete contact
and assembled-owner tangents, both-body wrench, hidden normal/edge crossings,
hidden reference inversion, rollback, split/open restart and the example pass.
The coupled fixture has nonzero deformable-target response. Normalized global
force/moment defects are about 1.24e-12/1.11e-12; owner directional errors are
2.18e-10/3.73e-10, against unchanged 1e-6/1e-5 development gates.

Explicit penalties 1e6/1e7 N/m³ give gaps 31.093/11.439 micrometres within the
unchanged 50 micrometre fixture budget; reaction changes 2.108%. Enforcement,
pressure/spatial convergence and engineering response acceptance remain open.
Only one beam, one S3 top skin and one strictly interior straight untwisted
half-cell material patch are admitted. Caps, interfaces, curved reference,
multiple bodies/patch unions, friction, native dynamics and nonlinear-material
qualification remain required programme work. No free-rim continuum admission.

39 installed checks: 73.466 s, 349569024 B peak process-family memory.
517 package files and 222 imports match source; JIT disabled, numerical pools1.
[Raw identities, review and retained failures](d1_review_support/contact_native_material_s3_20261004/README.md).

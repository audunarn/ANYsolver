# C6 flexural B3 / deforming-S3 continuation

From `d8a79a76`, this continuation exercises the existing shared impact route
with real B3 bending rotations, quadratic interior motion and a deforming target.
Solver code, defaults, admission, schemas and all540 package payloads are unchanged.
The held private wheel is reused; no new build/install or full-control replay.
This is development verification, not full C6 engineering acceptance.

## Working outcome and independent references

The actual model frees beam z/ry and uses its physical Q2 rotary inertia. Other
beam axes and all target rotations are explicitly constrained. There is no beam
uniform-motion MPC. The initial bowed normal rate and compatible rotation rate
produce measured nonzero bending, rather than a sheared curve with rotations fixed.

Independent references use their own Q2 beam strains/three-point integration,
physical Q2 translation/rotation mass, native S3 lumped translation mass and
quadratic gap roots/exact square primitive. The selected S3 V2D response is small
strain, even through the assembly's `von_karman` selector. For this virgin,
normal-only, zero-rotation fixture, the independent MIN3 reference derives its
barycentric gradients, rotational shear columns and Hammer trace relaxation;
it does not call the production shell operator or read its relaxation factor.
Its energy is compared separately with the source-justified linear recovery.

## Actual installed evidence

- Final coupled control PASS6.5700783s/181956608B; actual public example
  PASS3.1699141s/162795520B. Three prior successful development checkpoints remain.
- Coarse10us:181states/39active, then opening. Seven accepted states have interior
  contact while BOTH genuine endpoints are open. Interior gap at the first such
  state is-0.142771um versus endpoint gaps+3.499878um/+3.654875um.
- Actual midpoint/chord difference5.919269um; beam ry up to5.606214e-5rad.
  Maximum spatial-MEAN curvature2.242462e-4/m, not a local maximum-curvature claim.
  Bending storage1.257159e-9J versus shear storage2.857595e-10J.
- Own MIN3 relaxation factor0.0001371240515586434; shell potential agrees with
  the qualified linear recovery within5.049e-28J. Independent physical nine-chart
  mass relative discrepancy3.470e-16; rotary mass is positive.
- Independent contact potential error<=8.059e-19J. Structural/contact virtual work
  and directional tangents pass1e-5 at h1e-7/3e-8/1e-8; contact-H error<=3.498e-10.
- Complete B3 node inventory, including node6, enters both-body inertia/internal/
  support/contact force and moment recovery. Separate0.5N/0.25Nm normalized errors
  <=4.164e-17/1.388e-17 against1e-6. Exact active B3 split restart passes.
- Fine5us temporal control PASS7.6325432s/182693888B:361states/78active, then opening.
  Independent energy defect improves0.0220794% to0.0060105% (ratio0.272223),
  both below the unchanged1% criterion. Minimum gap-5.492427um against10um.

## Identity, review and remaining scope

Raw `C:/ANYworkspaceWork/contact_c6_beam_s3_20261006` contains uniquely named
`flexural_completed_handoff.md`, `flexural_completed_summary.json`,
`flexural_completed_source_hashes.json` and all five new input/runtime/resource
records. Earlier manifests/handoffs/artifacts/failures remain intact.

Root `root_flexural_installed_audit.json` verifies the reused wheel
`d5d46ced9e0a4882edf7106afe7134fbd132820a170dc660714fde30930ce5a8`, all540
payloads, seven held source hashes and227 actual installed imports for each final
control/example/refinement. JITdisabled, Numba1, native pools1; errors0.
The final reporting-only rename describes spatial-mean curvature; executed raw
records retain their original key and mathematical definition. Numerical code
and gates are unchanged, so no reporting-only solve was repeated.

Supporting source scrutiny confirmed the equations and independent references.
A suspected missing B3 node6 was adjudicated from Git/source hashes: the helper
was already corrected in `d8a79a76`, and its recorded executed hash matches the
complete-node implementation. Existing affected balance evidence applies.
Same-family supporting review does not confer independent engineering acceptance.

SAME original C6 purse:108.78753899980802/180s used,71.21246100019198s remaining,
17terminal jobs including prior failures/build/install. This continuation adds
29.9044983s in five jobs; no other authority is borrowed or renewed.

Rotation-free target admission remains unchanged. General shell rotational/
algebraic work, nonlinear materials/friction, physical boundaries, multiple faces,
spatial/enforcement convergence and broader C6/C0-C9 acceptance remain required.

[Public usage and derivation](../../GENERAL_CONTACT_BEAM_S3_TRANSIENT_DEV.md).

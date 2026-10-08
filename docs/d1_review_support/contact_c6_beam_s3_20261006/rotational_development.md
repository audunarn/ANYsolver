# C6 beam/S3 rotational descriptor development

Implemented and tested as a distinct opt-in development profile. Independently
accepted: NO. Released: NO. Full C6/C0-C9 remains incomplete.

## Mechanics and public outcome

`allow_rotational_beam_s3_dev=True` selects
`ELASTIC_B2_B3_AFFINE_ROTATIONAL_S3_ENDPOINT_HERMITE_DEV_V1` and V18 restart.
The shared driver solves complete structural/contact endpoint equilibrium with
actual physical mass and a declared algebraic null basis. Physical acceleration
is Newmark; algebraic velocity satisfies the TOTAL tangent equation. Null
acceleration is explicitly the finite endpoint-velocity secant numerical record,
not a continuum C2 DAE derivative. V18 binds its previous accepted velocity and
actual last duration and validates that relation before assembly on resume.

The physical S3 skin uses its existing affine work map, including eccentric
rotational couples. All-coordinate endpoint Hermite controls pass through the
same map and are conservatively bounded for gap, orientation and rims. This
certifies the represented segment, not a nonlinear algebraic lift. Minimum-gap
touch within dimensional arithmetic uncertainty refuses; no blanket C2 or
one-sided full-line resolution claim is made.

Public records preserve geometric `shell_moment` and separately expose nodal-work
moment, their affine-rotation discrepancy, origin and rate/path semantics. Both
report and mechanics use prepared geometry; director/offset/operator mutations
refuse. The inert archive knows this exact new record type; old producer fields
and wire semantics remain intact.

## Actual evidence

- Source first3PASS10.943873s. First installed job6PASS/1FAIL14.494485s;
  incorrect test-only stiffness-assembly import failed before the restart
  discriminator. That NONPASS is retained; the affected repaired selector passed.
- Final installed restart1PASS3.427913s/182898688B; public example
  PASS3.239805s/163553280B; protected legacy wire1PASS2.380162s/181252096B.
- Actual B3 impact:181states/39active, then opening. Exact active split restart
  matches displacement history and full checkpoint. Minimum gap-5.483061um
  against10um; final gap+24.093226um.
- Independent Q2 beam/affine-skin line potential and uniform-rotation MIN3 shear
  energy give energy defect0.0220794% at10us, decreasing to0.0060105% at5us,
  both below1%. The prior independent physical mass chart is reused by impact;
  actual shell rotation rows remain zero, without fabricated inertia.
- Rotational contact work/tangent errors over h1e-7/1e-8/1e-9 are at most
  3.830e-9/2.716e-9 against1e-5. Independent line potential error<=8.427e-19J.
  Algebraic residual<=1.573e-16 and nodal-work wrench error<=1.111e-16 on
  separate0.5N/0.25Nm scales against1e-6. Normalized affine moment discrepancy
  <=4.989e-9 in this impact.
- Actual target rotation<=6.670e-7rad, rate<=4.536e-4rad/s; contact couple
  <=3.985e-10Nm and trapezoid rotational work-1.341e-16J. This is tiny-angle
  nonzero rotational work, not broad rotational-impact acceptance.
- Hidden represented target motion, operator/profile/initial-rate refusal,
  cancellation, exception and rejected-path retry controls pass. Re-checksummed
  null-acceleration corruption refuses. Protected V17 source generated a prefix
  that the current V17 path resumes; new settings do not alter its identity.

## Identity and disposition

Final wheel `6ed957410d9de13c02d0070d56ff9d0b6004f2f4036a768060f86265ee501fa7`.
All541 source/wheel/installed payloads and seven final hashes match. All541 Python
ASTs excluding docstrings match the first numerical wheel `252e1e46...`;
the six valid installed controls therefore remain applicable after the precise
touch-docstring repair. No failed job was regraded. Fresh installed restart,
example and wire controls observe228/228/223 solver imports, errors0,
JITdisabled/Numba1/two native pools1.

Raw `C:/ANYworkspaceWork/contact_c6_beam_s3_20261006` retains all versions,
failures and input/runtime/resource logs. See `rotational_worker_handoff.md`,
`rotational_final_summary.json`, `rotational_final_source_hashes.json`,
`root_rotational_installed_closure_audit.json` and root source/review audits.
The root byte-comparison diagnostic confused Git LF with wheel CRLF; its failed
record is retained, and `root_rotational_impact_reuse_correction.json` proves
protected-wheel byte identity and normalized Git-source equality. No mechanics
criterion or tolerance changed. Supporting source review is not independent
engineering acceptance.

SAME C6 purse169.8124641997274/180s,10.1875358002726s remaining,27terminal jobs;
all failure/build/install/repair costs count. No authority renewed.

Uniform, freely solved target rx/ry MPC traces were exercised. Arbitrary traces,
general initial/preloaded states, full-line one-sided activation, finite rotation/
angular momentum, nonlinear DAE lifting, friction/materials, true rims/multiple
faces and wider spatial/enforcement/impact acceptance remain required.

[Usage and contracts](../../GENERAL_CONTACT_BEAM_S3_TRANSIENT_DEV.md).

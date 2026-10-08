# C6 beam / deformable-S3 development evidence

Development candidate from `78e6a6cd`; full C0-C9 remains incomplete. Product
profile `ELASTIC_B2_B3_DEFORMABLE_FIXED_DIRECTOR_S3_NEWMARK_DEV_V1`, opt-in
`allow_deformable_beam_s3_dev`, checkpoint V17. This is not engineering acceptance.

## Integrated outcome

The ordinary shared Newmark driver reuses the existing moving-normal B2/B3 line
potential and complete S3 physical-skin work map. Both bodies move. Model-owned
constraints enforce exactly zero S3 rotations/rates; actual reduced physical mass
must be positive definite. No hidden mass, damping, spring or changed line law.
The complete represented cubic path encloses both bodies, physical gap, true rim
clearance and target normal/orientation. Unresolved bounds cut back or refuse.

## Observed installed results

- Ten focused controls PASS in14.707883500028s, peak190201856B; separate actual
  unequal-target public example PASS in2.92151s.
- Actual B2 and B3 uniform-normal impact:181states,32active, separation/release;
  minimum gap-4.983568um against10um. B2 final opening24.350308um.
- Independent scalar discrete Newmark response: relative displacement1.3953e-13,
  velocity2.2163e-13; normalized momentum6.0759e-12.
- Continuous flight/sine/separation reference: dt10us to5us reduces normalized
  gap error2.9638e-4 to6.9516e-5; kinetic-plus-contact energy defect0.029213% to
  0.0070375%, both below1%. At doubled line regularization and5us, energy defect
  0.013979%. No general deforming-shell stored-energy claim follows.
- Actual unequal target translations differ; per-body inertia/internal/support/
  contact wrench errors<=2.002e-16 on separate0.5N/0.25Nm scales versus1e-6.
  B3 uniform physical-wrench errors<=1.388e-17.
- Exact accepted-grid B2 split restart, settings incompatibility, in-flight cancel/
  exception/rejected-path retry, zero-rate/rotation and mass/profile refusals pass.
  B3 has actual public impact and local work/tangent/path checks; exact B3 split
  restart is not claimed from B2 evidence.
- Complete hidden beam and target motion, normal-collapse/rim refusal and operator
  mutation controls pass. Supporting review found a missing shell CSR binding;
  it was repaired and tested before source hold.
- Installed smooth-branch work/tangent checks over h=1e-7/1e-8/1e-9 PASS in
  2.824441s. Maximum relative tangent1.061e-9/work6.566e-10 against1e-5.
  This follow-up changes only its test; product/artifact hashes are identical.
- New inert known contact record exports; the protected legacy transient fixture
  wire is byte-identical, SHA256 `28bba5feb7536a3fc8cfce195dffb801784c9ec6047259262ce8f9147e4c6711`.

## Artifact and reproducibility

Raw evidence: `C:/ANYworkspaceWork/contact_c6_beam_s3_20261006`, including input
hashes, complete logs, runtime/import records, resource records and retained failed
source runs. Private wheel SHA256:
`d5d46ced9e0a4882edf7106afe7134fbd132820a170dc660714fde30930ce5a8`.

Root filesystem audit `root_final_installed_audit.json` independently confirms
all540 source/wheel/installed payloads, six final held hashes and actual installed
imports:228controls/221derivative/227example, errors0. Effective JITdisabled,
Numba1 and both native pools1. Full producer record inventory is unchanged.
`held_source_hashes.json` binds the first installed controls;
`final_source_hashes.json` binds the changed-test-only follow-up and unchanged
five other files. Unaffected installed evidence is reused by impact analysis.
SAME180s purse:78.8830406999914s used/101.1169593000086s remaining,12terminal
jobs including all failures/build/install. No older authority is renewed.

Failures remain nonpasses: initial wrong mass-profile routing, a split endpoint
that was not the identical accepted time, final-step truncation and test refusal
regex mismatch. Their source/log identities are retained. No tolerance changed.

[Usage and bound derivation](../../GENERAL_CONTACT_BEAM_S3_TRANSIENT_DEV.md).
General finite rotation, friction, nonlinear materials, multiple surfaces/caps/
physical boundary contact, spatial convergence, broader impact acceptance and
application admission remain required elsewhere in the full programme.

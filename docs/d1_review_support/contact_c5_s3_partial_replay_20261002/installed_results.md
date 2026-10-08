# Installed partial S3 material replay — development evidence

2 October 2026. Source checkpoint `ec5bc0ad9a4d7b8aa461f9b993185764417c7fa4`.
No engineering acceptance, application admission, publication or release.

Artifact: `C:/ANYworkspaceWork/contact-friction-partial-replay-package-20261002`.
Wheel SHA256: `db4bc12dfb5194cc1ebf4b4f49787217d73a87efff0ce3ba17dc11905e330735`.
All459Python modules match source, wheel and installed site. Verified imported
ANYsolver modules lie under that site:229in focused checks,241in example.
Python3.14.2; actual JIT disabled, NumBa1thread and measured BLAS pools1thread.
Full dependency identities, selected commands, checksums and logs are in
[raw index](installed_raw_index.json) and [verified archive](installed_raw.zip).

## Executed checks

- Build/install:15.679s,129015808B sampled process-tree peak.
- Twelve focused physics/state checks:14.87s pytest,16.713s process,193466368B.
  Independent partial force/boundary tangent, arbitrary material history, atomic
  invalid work/pressure restore, geometry/nonfinite rejection, actual prepared
  pressure/work maps, both-body tangent, thin mixed-stick/slip canonical retry,
  cancellation/exception rollback, shared retry budget and pressure-ramp work.
- Standalone example first press and real checkpoint:1check12.33s pytest,
  20.480s process,191516672B. Controlled node motion with source normal deformation
  and target in-plane motion solved through the ordinary nonlinear static driver.

Every run used180s/999292928B limits. All13checks passed, no skips; manifests verify
459source modules and actual installed imports. Source scientific results and
source full/split workflows are reused only within their documented scope. The
installed example smoke run covers its first press, not all five phases or restart.

## Runnable example

[general_contact_s3_partial_friction.py](../../../examples/general_contact_s3_partial_friction.py)
uses explicit physical skins, finite normal penalty, Coulomb regularization,
material replay and bounded event/integration settings. With this installed wheel:

```powershell
python examples/general_contact_s3_partial_friction.py --max-load-factor 0.2 --checkpoint-output press.json
python examples/general_contact_s3_partial_friction.py --restart press.json --checkpoint-output final.json
```

The default runs press/slide/reverse/open/recontact; it can take several minutes.
The example and smoke-test hashes are separately bound in example-identity.json;
they were added after the wheel's source checkpoint. No package version is promoted.

Remaining: general temporal/spatial refinement, released-storage accuracy (4vs32
change7.9%), coupled trajectory refinement, independent scientific assessment,
finite rotations/warped shells, swept beam/native friction and broader C0–C9.
Total-dissipation convergence does not establish convergence of every work quantity.

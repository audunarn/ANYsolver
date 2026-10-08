# Connected S3/tool reference invariance - 6 October 2026

Required development control over the existing fixed planar connected two-S3 /
nonmatching tool profile. Question: preserve actual coupled response, physical
wrenches and work under exact reference-frame change and material renumbering?
Four solved cases: baseline, cyclic reference-axis permutation plus dyadic shift,
numbering only, and their composition. The normal changes from z to x; all six
physical coordinates, directors, loads and constraint subspaces transform.
No contributor/geometry/driver/law changes or new artifact were required.

## Verified result and limits

Final installed test PASS1 (four coupled solves),6.337499000016s,
peak164872192B. Root checked the actual executed test hash, all222 installed
imports/errors0 and effective JIT0/Numba1/three native pools1. All543 existing
source/wheel/installed payloads remain exact. Reused artifact:
C:/ANYworkspaceWork/contact_transient_archive_20261006/native_reader_installed1;
wheel2a1cca8e20055337f164dce87a6557c4031e5556b114cf9573c71dfaf2047f9d.
This does not provide incidental V19/C6 verification or consume C9 authority.

- Response covariance <=2.721215823240e-12 on10um scale; gate1e-6.
- Each source/tool shifted-origin wrench <=1.584136261004e-11;
  force/moment separately0.15N/0.15Nm; gate1e-6.
- Support/load/contact equilibrium <=8.238966325054e-12; same separate gates.
- Worst physical gap -2.159010846377um versus existing50um development tolerance.
- Local active partial-footprint full skin work-map covariance <=2.618526293123e-10;
  actual manager boundary/coverage guard passes. This pose violates supports and
  is a local derivative check, not a new solved lifecycle or rim admission.
- Directional force-rate tangent error <=6.694971058320e-7 at h1e-7/1e-8,
  moment-rate <=8.789647186299e-13; gate1e-5. Scalar work error<=1.845597748703e-11.
  Explicit1m/1rad charts,0.15N/0.15Nm rate scales and0.3J/path-parameter work scale
  retain stronger absolute checks than the original relative norm checks.

Test SHA256:0ed8f6d354faccbd96eb34e71770654a221ea3d80d53da62df584966db64397c.
Initial NONPASS2.274983s was a test-harness abs(tuple) error before solve;
fixed by np.abs. Subsequent PASS5.672222s retained at its original relative
reporting/hash; final dimensional PASS above is a distinct affected rerun.
All failed inputs/logs and prior histories remain unchanged. Supporting source
review checked final hash/four-case maps/scales; same-family scrutiny is not
engineering independence. No finite-motion/arbitrary-oblique-frame, warped
obstacle, Q4, spatial-convergence or C4 acceptance claim follows.

The SAME C4 purse has33terminaljobs/172.931528899935s spent,
7.068471100065s remaining. No renewal or borrowed scope. Raw:
C:/ANYworkspaceWork/contact_triangulated_rigid_20261006/invariance_worker_handoff.md,
invariance_final_manifest.json, the three invariance_installed* job directories,
and invariance_root_* provenance/ledger-prefix/reconciliation audits.
Full C0-C9 ACTIVE/incomplete; source/installed development testing is distinct
from engineering acceptance and release. [Guide](../../GENERAL_CONTACT_TRIANGULATED_RIGID_DEV.md).

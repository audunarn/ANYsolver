# Gravity with selected-node rigid footprints — 3 October 2026

The installed experimental public workflow completes gravity loading, chart
rebase, checkpoint/restore and continuation. Admission is deliberately limited
to elastic-response, flat Q4/generalized native beams with declared physical
inertia and increment-origin V2 footprint charts. Footprint-only and combined
point/footprint models are exercised. This is not a bonded area weld,
distributing footprint, G4 acceptance or complete material/load qualification.

The existing conservative gravity operator and atomic owner are reused.
The new footprint context activates the driver's existing fixed-parent trial
work norm. Current-state equilibrium (1e-8), compatibility (1e-9), material
validity and zero plastic-history guards remain mandatory. Existing point
contexts retain their original backtracking behavior. No pressure amendment,
Armijo experiment, equations, defaults, package version or checkpoint schema
was changed. S3/mixed, J2/fibre, curved, unrebased-chart and staged combinations
remain excluded from this new intersection.

## Verification and preserved failures

- Initial source checks: 7 failed / 23 passed, 170.59 s. Six combined models
  exhausted Newton; one negative fixture was malformed.
- One unchanged diagnostic: 217 evaluations, 176 rejected, no accepted state.
  A first full step improved global work ratio 1 to 0.03056, but the changing
  active-row scale reported 375.98 when a small cell torque appeared. Existing
  fixed-parent trial comparison resolves that starvation; it is not equilibrium.
- Repair checks: 2 passed, 10.36 s, including complete actual-update tangent
  and conservative external-force/work derivatives, errors <=1e-6.
- Disposable build failed once because its source directory was omitted.
  Correcting the runner source path built the wheel; original logs retained.
- Installed affected suite: 47 passed / 3 failed, 90.38 s. These three failures
  were new-test defects: wrong expected exception for a nonfresh restore owner,
  and hashing chart-dependent predecessor coordinates across rebase. The
  unchanged fresh-owner guard and physical tolerances were preserved.
- Corrected affected checks: 3 passed / 47 deselected, 15.09 s. Material histories
  compare exactly, predecessor physical configurations use existing 1e-9 checks;
  cancellation, injected successor failure and changed acceleration preserve
  the accepted checkpoint. No unchanged passed suite was repeated.
- Installed public example: completed factors 0.25/0.5/1, exact same-chart
  checkpoint restoration and final restart parity, selected connection action
  balance and wrench recovery (not an explicit final ground/body wrench sum).
  Mass 1256 kg, applied vertical force -12321.36 N, final
  equilibrium 5.425e-9 and compatibility 4.444e-16.

Wheel SHA256 `16ce45d951d3bd8a7fddddc6edfcd3022f0bca298dc96dc5fa3fd1ebbc3269b4`;
417 source/wheel/site module byte identities verified. Actual tests/example
imported 238 solver modules from the disposable installed site. Python 3.14,
NumPy 2.4.6, SciPy 1.17.1, Numba 0.65.1/JIT disabled, pytest 9.0.3; effective
BLAS/OpenMP/Numba pools one. Runs serial, <=600 s/1 GiB; installed-suite sampled
peak 199565312 bytes. ANYmaterial remains an explicitly recorded editable
dependency, not an isolated final package graph or cross-platform evidence.

Source parent 16cec54f plus captured dirty product files. Original binding binds
the original fixtures; corrected fixtures are separately captured in raw/source
and the archive manifest. No claim that original failures passed.

Independent OpenAI source/evidence review found the same two test defects and
no additional implementation defect. Different-family scientific acceptance
remains unmet; this review does not close M4/G4. Formal F03 remains unconsumed.

Explicit safe archive: 54 files, 2232043 bytes, manifest SHA256
`26084d86799fab1ad59900781d14abf0446fd32099059d4e5768acd19fddc6dd`.
[Manifest](raw-manifest.json) preserves failures, diagnostic, commands,
runtime/installed identities and source. Full scope and release obligations stay
open; no main merge, publication or unrelated history sweep.

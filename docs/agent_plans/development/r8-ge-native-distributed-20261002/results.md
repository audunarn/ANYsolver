# Experimental native distributed beam loads — 2 October 2026

Delivered GEBeamLineAction / GEBeamDistributedLoad through the existing public
point-owner facade. Fixed spatial densities are measured per reference arclength.
Actual order-4/8 generalized and physical-fibre operators retain all 42 coordinates;
curved lifts and shared-node scatter are preserved. Force work is conservative;
fixed spatial couples have zero spatial derivative and no endpoint potential.
Recovery reports resultant force/moment, force work and `potential=None` for couples.

The existing compiled external-load slot now handles gravity and distributed work.
No legacy admission guard, element law, default, package version or checkpoint
identity was changed. The new distributed envelope binds the model, densities and
element IDs; changed requests and mismatched/stripped envelopes are rejected.

## Evidence actually executed

- Source local/shared-gravity checks: 28 passed (2.17 s pytest).
- Initial owner run: 7 new tests failed on a test-helper ID lookup; 9 passed,
  including all 8 gravity owner checks. Fixed helper, retained failure.
- Source distributed owner: 8 passed, then expanded family/identity coverage
  11 passed (19.10 s pytest). No claim of runtime improvement.
- Isolated wheel: 60 passed, no skips/failures (82.45 s pytest;
  84.492 s complete route; sampled peak 192020480 bytes).
- Additional installed curved-owner nonzero Jacobian/actual-update test: passed
  (2.379 s route; 169934848 bytes). Earlier fixture failures preserved: frames
  initially not tangent aligned, then shared frame differed at floating precision.
  Correct physical tangent frames and exact shared-frame ownership resolved them;
  no scientific tolerance or product guard was weakened.
- Installed public example: completed 0.25/0.5/1, restored continuation identical;
  5.674 s route, 155209728 bytes. Applied force (0,0,-200) N;
  current-origin moment (106.000055539,210.000061978,4) Nm;
  equilibrium 3.424254e-10, compatibility 7.798304e-18.
- Initial installed collection failed for an omitted test-helper fixture; retained
  and repaired without changing product. Independent source review found no
  remaining consequential defect. Private preacceptance request rebinding was
  hardened and tested before building the final wheel.

Wheel SHA256: `7b0886fd7ddb3796c629f4abd451357c9b64c44f5c58fa6bcf7f60cb9999627f`.
395 source/wheel/site modules matched; 219 actual ANYsolver imports verified in
isolated site. Python3.14.2; actual BLAS/Numba1 thread, JIT disabled. The run bounds
were 600s/1GiB with observed process-tree memory; no limit reached. Raw archive
contains commands, versions, identities, fixtures, failures and execution records.

## Acceptance boundary

Experimental implementation and installed Windows checks, not aggregate G4/G0
acceptance. Direct tests cover point Q4/mixed/S3, generalized/fibre/mixed families,
force-only/couple-only/combined linear response, finite combined response, reactions,
cancellation, injected rejection, chart/restart, actual-update derivatives and
model-bound ownership. Kernel curved work and assembled curved derivative pass;
this is not a completed curved engineering reference solve or external comparison.
Active yielding under these new loads, line/footprint/combined load programmes,
ANYfem persistence of the new request, practical scale, full platforms and all
remaining programme gates stay open. F03 remains unconsumed. No push or release.

Raw archive SHA256: `33e7c74b5c2dc51740e45bfcf259846675f3d9bef9d6c7af76453c1ea4906084`.
New records passed a scan against available inherited credential values; this does
not remediate the previously identified historical archive. Do not disseminate
that history until authorized remediation.

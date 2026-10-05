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
# 2 October material-history extension

Product base5e95e593; no product code changed in this extension. The existing
two-stiffener Q4 J2/physical-fibre/generalized fixture now executes uniform native
transverse force3000N/reference-m on all four beam elements. Accepted factors
0.5/1/0.25/1.1 cover loading, positive-magnitude unloading and reloading. Shell and
physical-fibre updates are simultaneously active at1 and1.1. This is not signed
load reversal; the generalized member remains the existing elastic control.

The source and installed lifecycle test pass: cancellation after the yielded
factor1 prefix, material snapshot restoration, identical continued checkpoint,
requested target order, actual distributed force, and failed-next-step checkpoint
and immediate recovery preservation. Final shell alpha is1.4176071e-5 and final
fibre incremental dissipation0.00200419J. Maximum observed equilibrium ratio
7.53933e-9 and compatibility5.09575e-17 satisfy unchanged limits. Force/moment
balance uses the programme's1e-8 normalized criterion with reference scales
12000N (4m*3000N/m) and24000Nm (2m span); maxima1.52894e-9/1.95700e-10.

Installed wheel SHA256
`5cd1df657cf5191b896000e999a3dc7c4a408615b9b44fcb1d1b1cc9dbea46ad`
matches all397 source/wheel/site Python modules.218 observed solver imports come
from the isolated site; both OpenBLAS pools use1thread and Numba JIT is disabled.
Final source route65.7032s/175845376B peak; installed65.8581s/174452736B. These are
observed costs, not performance gains. One source and one installed case passed;
repeated fixture revisions are not counted as additional independent checks.

Retained failures:1500N/m activated fibres but not shell plasticity;3000N/m was
chosen without changing laws. Negative-factor targets rejected before solving,
exposing the still-open signed/staged distributed-load programme requirement.
The first full history used an elastic helper's absolute zero-component balance
tolerance; its1.81e-5N residual on13200N loading passes the programme's scaled
criterion. The test was corrected to that existing material-history scheme.
An assertion-order coding error was also repaired. The xunit record_property
warning is retained; activity is additionally recorded in stdout and XML.

Independent Read review of the history test requested explicit target-order and
post-failure recovery checks; both are included. This is source scrutiny, not
different-family scientific acceptance. Distributed couples with active yielding,
signed/staged reversal, other attachment/material combinations, engineering
accuracy and aggregate G3/G4A remain open. Pressure assessment remains unchanged.

[Raw source revisions/failures, installed fixtures and identities](material-history-raw-v1.zip)
SHA256 `2ac691d6541040508ed6c40929749a775d2d3fe606a77e7a24b9b867e2a4d908`.
The wheel remains in the local r8-ge-distributed-material-installed-v1 evidence
directory. No release or dissemination of the restricted repository history.

# Signed native distributed programme — development evidence, 2 October 2026

Implemented a separate `GEBeamDistributedProgramme` identity with absolute
piecewise-affine force/couple densities, implicit initial zero, positive forward
positions and mandatory crossed stage boundaries. Native geometry/quadrature is
captured once. Missing element actions are zero; no trial topology compilation.
The existing positive legacy-factor guard and physical acceptance remain unchanged.

The point-owner finite route now publishes programme progress and physical load
recovery, preserves cancellation prefixes, and restores a programme-bound binary
checkpoint. Reference-linear programme execution is explicitly rejected. This is
experimental, not G4A acceptance or complete consumer support.

## Evidence and limitations

- Density foundation:31 source checks, then20 native checks after one added case
  (32 distinct); logs in staged-density-source-v1.
- Programme v1 failed collection (incorrect test import, corrected).
- Programme v2: descriptor passes; complete unloading to zero fails backtracking.
  Preserved unchanged in staged-programme-source-v1. `_linear_equilibrium` returns
  infinity whenever total applied force is zero but residual is nonzero. No
  acceptance alteration or reference-state reset was introduced.
- Programme v3:14 source checks pass (new elastic route and legacy distributed).
- Programme v4:18 pass (five programme checks, existing nodal-stage owner and
  body-load checks). The zero-load test asserts failure and accepted-prefix
  preservation; it does not establish zero-load convergence.
- Independent source review found no blocking defect. Its two coverage requests
  were addressed together by one additional passing source check: changing element
  inventory/order and interpolated couples, including exact couple cancellation.
- Five installed programme checks pass in11.513s supervised,176476160B sampled
  peak process-tree memory. Source/wheel/site parity covers398 modules, not398
  qualified modules. Runtime verifies imported site,1 numerical thread and JIT off.
- Signed simultaneous-plasticity history passes source51.804s/175915008B and
  installed50.472s/173813760B. Positive programme positions .5,1,1.25,1.75,2
  represent resultant forces +6000,+12000,+6000,-6000,-12000N. Shell and physical
  fibres are simultaneously active at1,1.75,2. Maximum accepted equilibrium ratio
  2.526e-9 and gap6.426e-17; final shell alpha2.467542e-5. Cancellation at1,
  restored continuation and exact checkpoint equality pass. Balance uses fixed
  programme scales12000N/24000Nm at1e-8, not per-component relative accuracy.
  Installed runtime records219 imported solver modules. The recorded-property
  xunit2 warning is retained; the XML contains the activity data.

Wheel SHA256:
`b636e6a8c52851cb9c3bd783e29ad8934791f95e0567d04e06aae0d964396ec2`.
The material run reuses this verified wheel/site with separately captured fixtures;
its copied artifact manifest describes the original five-test fixture set, while
the material archive manifest identifies its actual fixtures and logs.

Raw installed records: staged-programme-installed-v1.zip and
staged-programme-material-installed-v1.zip. Source logs: staged-programme-source-v1.
Supervisor limit600s/1GiB, configured1 numerical thread; installed runtime checks
verify effective pools. No timing comparison or speedup claim. No demonstrated
adaptive cutback occurrence; pending adaptive sequence restoration is exercised.
Couple-bearing local work is checked, but plastic histories use force-only stages.
Mixed/S3 staged histories, consumer serialization, zero-load convergence and broad
qualification remain open. Pressure assessment amendment is still pending.

Independent OpenAI Read reviewer `/root/s3_dead_work_review` inspected source and
the installed material XML/runtime. No blocking defect; requested distinct
inventory/couple checks pass. Review also requested that the material assertion
require simultaneous activity after position1.5 rather than1. That assertion was
tightened and checked directly against retained installed XML observations
[1.75,2.0]; the numerical campaign was not repeated for this assertion-only change.
Installed fixture hashes therefore identify the original assertion source.
This is source/evidence review, not an independently executed mechanics campaign.

Archive SHA256: elastic
`c72c713a39aabf30883e49f50377f516fb04988cd6f0fbf204b4b7b49ef7e67b`;
material `1f94feb1fa8e14dfd4accc3834accee6c3b140cb0f3745781712a0b73dcaa575`.

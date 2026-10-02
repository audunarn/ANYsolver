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

## Mixed shells, example and consumer continuation

Two additional elastic cases (mixed Q4/S3 and all-S3) pass signed stages1/2,
physical balance and identical restored continuation: source6.769s/175599616B;
installed5.583s/173608960B, using the unchanged verified solver wheel above.
The new runnable `examples/stiffened_shell_ge_distributed_programme.py` passes
source4.342s/172843008B and installed4.062s/171495424B. It demonstrates accepted
stage cancellation and restart on the two-Q4 eccentric panel; no zero-load point
is requested. Fixture hashes and installed runtime checks retained in
staged-programme-mixed-installed-v1.zip and staged-programme-example-installed-v1.zip;
source records in mixed-example-source-v1. These tests do not broaden plasticity
coverage to mixed/S3 material histories.

ANYfem's separate distributed-programme schema, strict persistence, model binding,
finite dispatch and real Project/cancel/disk-restore workflow pass139source and
139installed focused checks. Consumer wheel c67232b6 uses solver b636e6a8.
See C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/
r8-ge-distributed-programme-20261002/results.md. No G4A/G6 aggregate acceptance.

## Mixed and all-S3 material histories

The same two-stiffener material model now also runs with the downstream shell
split into two S3s, or both shells split into four S3s. Geometry, section laws,
shell J2 law, force densities, support conditions and programme positions remain
unchanged. Initial source run: one mixed observation failure and one all-S3 pass
in65.83s pytest. The failure occurred after acceptance: the example helper tried
to make a rectangular array from Q4's12 and S3's9 native alpha stations. It was
not a failed material solve or partial solver commit.

The helper now matches (formulation,element ID), checks unique matching inventories
and native station shapes, preserves the existing stationwise roundoff budget,
and reports family activity. Independent OpenAI Read review found no consequential
defect and requested homogeneous station-local parity tests, which were added.
16small helper checks pass, including unchanged Q4/S3 arithmetic, station-local
increments around the existing tolerance, reordered elements and invalid histories.
The corrected mixed history plus6initial helper checks pass in57.356s supervised.

Both installed material histories pass in115.078s supervised,174166016B sampled
peak process-tree memory, using unchanged solver wheelb636e6a8 (398source/wheel/site
modules). Runtime verifies219onsite imports,1numerical thread and JIT disabled.
Actual revised test/example fixture hashes are retained separately from the reused
wheel manifest. The xunit2 recorded-property warning remains in the raw logs.

At positions1,1.75,2 the mixed case has active Q4 and fibre updates; its downstream
S3s remain elastic. The all-S3 case has active S3 and fibre updates at those same
positions. Maximum accepted equilibrium ratios: mixed4.790159e-9, S3 1.284940e-10.
Positive-prefix cancellation, snapshot restore, negative-load history, physical
balance and exact final checkpoint parity pass. This does not establish simultaneous
Q4 and S3 yielding within the mixed case, every material/load combination, or
independent constitutive accuracy. Zero-load and broader qualification remain open.

Source records: mixed-material-source-v1. Installed records:
staged-programme-mixed-material-installed-v1.zip. No numerical product equation or
acceptance criterion changed; this slice repairs example observation and extends
executed lifecycle coverage.

Installed archive SHA256:
`5afb0d14925583076ba95714d26aba51f36e55964b3e69d3372f9592ea271250`.

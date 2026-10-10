# Automatic Q4/S3 press /20mm actuator slide /open /recontact

## Verified development outcome

The installed ordinary solver completes the declared four-increment automatic workflow on the unchanged physical guided-Q4-source/free-S3-target fixture. Use the retained V2 package on PYTHONPATH with JIT disabled,Numba1 and pools1 (the exact tested private environment/command is retained in attempt08/input.json):

```powershell
python examples/general_contact_automatic_domain.py --deformable-sliding
```

`build_projected_shell_pair(sliding=True,path_predictor='control_projection_dev')` is the optional fixture mode. Existing defaults, press/lifecycle modes and prior tests remain unchanged. The explicit path is [(0,0),(0,-.015005),(.02,-.015005),(.02,0),(.02,-.015005)] for node1(ux,uz). All six source uz share the existing actuator guide; other source ux remain actual equilibrium unknowns. Target node9uz stays free; targetxy and rotations remain fixed. Physical skins/directors/offsets, elastic material, mesh, Jet2 projected penalty1000,50um gap budget and explicit control predictor are unchanged.

20mm is the ACTUATOR slide. The five free source ux pass the declared>10mm motion gate; their reported values happen to lie near20mm, which is not a claim of prescribed or exact rigid translation. This bounded frictionless translational/small-rotation development workflow does not establish generic deformable-contact, friction, finite-rotation, rim, pressure-stability or D1 acceptance. The compiler selects declared coarser median reference faces with stable-ID ties and keeps positive supports; it makes no geometry-discovery claim. No mechanics-speed comparison, qualification or release is claimed.

## Frozen checks and actual evidence

Raw root: C:/ANYworkspaceWork/contact_automatic_sliding_20261008. PROSPECTIVE.md and SOURCE_READY.md preserve the question, candidate, physical inputs, criteria, cap and decisions before observation. Fresh private unpack reused the immutable V2 wheel,627 payloads:

`SHA256 fec0e27010587cc96af5ab5d4182cb82ecd0a116e53e4239d5e2acde5340fcd1`

No product source changed and no wheel was rebuilt. Private imported modules and payload hashes, JIT disabled/Numba1/pools1, exact commands/environment/source/example/test identities, process-wall/RSS, full stdout/stderr/JUnit, machine results and immutable per-attempt inputs/harness are retained. SUMMARY.json records final closure. Unaffected V1/V2 geometry/predictor/compatibility controls are reused by impact, not rerun as broad suites.

| Attempt | Check/result | Process wall seconds |
|---|---|---:|
|01|full automatic4increments:PASS|15.472793200009619|
|02|authenticated saved full strict opening/independent area:PASS|4.0099855000007665|
|03|ordinary explicit pair +endpoint/per-phase parity:PASS|11.787207400004263|
|04|3/4prefix through genuine separation:PASS|9.068761499991524|
|05|fresh model authenticated resume to recontact:PASS|13.379513199994108|
|06|refusal test:NONPASS diagnostic regex mismatch|12.098179699998582|
|07|corrected refusal expectation:PASS|5.809275100007653|
|08|actual public slidingCLI:PASS|8.48140710000007|

Six pytest cases passed plus actual CLI. The initial refusal attempt correctly raised `checkpoint SHA-256 does not match its contents`; the lowercase hash/digest/checksum test regex did not match SHA-256. Its failure/full output remain preserved. One concrete test-only correction matched the real diagnostic, with unique attempt/output. No physics, travel or tolerance tuning occurred; no further corrective experiment was needed.

Snapshot inventory is exact: full/explicit[1,2,3,4],prefix[1,2,3],resume[4]. Therefore missing accepted-pose oracle calls cannot silently pass. Phase controls, active state, force/moment/gap/storage parity match saved full at every phase, not just the endpoint. Normalized declared response differences are0 for both explicit and resumed routes; displacement parity meets rtol1e-7/atol1e-9m. Provenance, predictor-selector and checkpoint tamper continuation refuse. The refusal mutation check covers repr-visible FEModel fields; it is not a proof of every hidden transaction/material field.

| Phase | Active pressure DOFs | Physical gap oracle | Production footprint area m² |
|---|---:|---:|---:|
|press|5|-5.000000000001531e-6m|.8099999999978452|
|20mm actuator slide under press|5|-5.000000000001531e-6m|.7919999999979771|
|open|0|+.014999999999999998m|.7919999999999999|
|recontact|5|-5.000000000001531e-6m|.7919999999979368|

At opening, exact independent clearance is strictly positive, targetuz returns within1e-10m and storage is exactly0. Zero active pressure alone is not the opening proof. All six source ux and actual projected pair polygons/physical nodes are saved at slide and final. Final actuatorux=.02m; free sourceux span.020000000002386956–.020000000005094373m. Independent area changes by approximately.018m², confirming movement of the contact patch beyond the actuator coordinate.

Free targetuz changes from-1.4558843327570134e-5m on press to-1.434862650784466e-5m after slide; final=-1.4348626507830727e-5m. Final target equilibrium normalized by positive.02N is3.137952137716171e-14. Original scientific gates remain normalized force/moment≤1e-6 at.02N/.02Nm and physical gap50um. Maximum measured normalized force/moment imbalance is1.0842054452120251e-17/5.421012324038671e-18. Actuator/support balance and both-body instantaneous virtual/residual work checks pass. Their full values and work convention projected_weak_gap_nonpotential_v1 remain in outputs/full.json; residual work is not path-integrated work or potential storage.

## Independent geometry oracle and review limits

The new oracle calls no production gap/overlap kernel. Fixed rotations/directors imply sourcebottom referencez=.055-.025 and targettop referencez=.025-.01, with sourceuz tied, targetxy fixed and source horizontal. Scalar reference-add then displacement-add independently constructs the accepted binary physical points. Fraction arithmetic checks convex source quads and positive target orientation, clips2D polygons against target triangles and evaluates exact affine P1 target height at polygon vertices. Affine extrema occur at those vertices, giving an exact rational minimum vertical/source-normal gap for that binary pose; nextafter bounds the displayed float. The same50um gate applies. Fraction shoelace independently reports clipped area and the press-to-slide change. The authenticated saved-full closure computes shoelace of its already saved independent binary polygon vertices and checks strict clearance/target return/zero storage, avoiding a redundant full solve. Explicit/prefix/resume use the final exact-clipping/area implementation.

Read review confirmed applicability to the fixed-director/horizontal-source convention. This is an accepted-binary-pose check, not full map-roundoff or swept-path coverage qualification. Production whole-path admission remains unchanged and authoritative; the earlier D1 finite-precision coverage limitation remains. Current fixture has d1_interior_profile=false. No nonaffine rotation wrapper, geometry padding or normal flip is introduced.

## Exact resource closure

AUTOMATIC_SLIDING_DEV240 used80.10712270000658/240 process-wall seconds;159.89287729999342remaining. Eight serial jobs,≤60/job,953MiB; maximum sampled tree RSS216.5MiB. Lead released the protected60 only after source/oracle review for final checks. No active job or further check is planned. Old deformable, swept-lifecycle and predictor balances/failures remain frozen and separate. Source fallback ownership continues because cached Mistral/local unavailability remains established. Lead owns final independent acceptance and Git integration.

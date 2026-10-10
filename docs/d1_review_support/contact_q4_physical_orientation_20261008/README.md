# Q4/Q4 physical-side director declarations

Verified the bounded `shell_pair_orientation='physical_sides_dev'` extension to original Q4/Q4 monolithic contact. All four upper/lower director-sign combinations completed the automatic force-driven press/open/recontact path and passed independent physical pose checks. Original and opposite declarations also restarted from strictly open checkpoints and reproduced their own full endpoints exactly. Engineering acceptance and release remain pending lead review.

## Use

```powershell
python -m examples.general_contact_q4_physical_orientation --signs mm
```

Choices pp/mp/pm/mm mean upper and lower physical director signs. Negative bodies use persisted `director_polarity=-1`, authoritative +z `reference_normal`, reflected element connectivity, and exchanged physical top/bottom side declarations. The model is freshly built before contact preparation. The example requires an explicit public zero-control `ContactPathProgram`: prescribed nodal forces, rather than displacement guides, drive both-body bending. The ordinary force call without an explicit program refuses this selector at the existing early public guard. The legacy monolithic generated-force hook remains unchanged.

The geometry, material, supports, fine Q1 pressure space, 1000 normal regularization, 50 um gap limit and force history are the prior positive-clearance bending fixture: upper reference z=.04+2e-7 m; lower reference z=-.01 m; thickness .05 m; free upper rotations and deformation, free lower rotations and five normal unknowns; nodal forces on nodes3/6 each 0,-5e-5,+5e-5,-5e-5 N. Public solver tolerance1e-12/max12 and one increment per force segment remain frozen. Automatic coarser-reference selection still chooses the upper two Q4 faces against four lower Q4 faces; feature/body/pressure IDs and selection rules are unchanged.

## Reference atlas and work

The existing S3 physical-side reference adapter now accepts the exact Q4 skin adapter. It uses the fixed reference permutation (0,3,2,1), applying the same permutation to physical corners, material IDs and work rows. For the complete original bilinear surface this is P'(u,v)=P(v,u); no triangulation or material feature is removed. The desired chart is role*side_sign*physical_director. Opposite director and opposite physical side give offset'*director'=offset*director, so physical skins and rotation force couples remain identical by material node ID. This covariance concerns the same canonical directed physical chart; it does not equate a reversed-normal invalid legacy chart.

Only core.py and s3_patch_static.py changed. Exact opt-in public and direct-constructor admission permits the existing original-Q4/Q4 augmented monolithic, whole-face, fine-Q1, exact-support profile. Existing S3 admission and all legacy/default omission/identity behavior are preserved. q4_skin_work.py, derivative kernels, fixed-z semismooth equations, structural elements, static driver, controllers and public signatures are unchanged. Current normal/chart/gap guards still process the original bilinear faces.

## Checks actually run

| Check | Observed |
|---|---:|
| Physical skin/work-map/interior-Q1 correspondence, four variants | exact |
| Independent force-couple work pullback | <=1e-14 absolute |
| Structural K relative polarity difference | <=2.069e-16 |
| Independent Fraction Q1 reference operator difference | 6.939e-17 |
| Smooth contact force/tangent/gap-gradient polarity difference | zero |
| Coupled directional contact / equilibrium / C maximum | 4.944e-8 / 2.345e-13 / 2.747e-9 |
| Matched all-phase displacement difference vs pp | <=1.219e-17 m |
| Matched all-phase supported-force difference / Fref | <=9.718e-14 |
| Maximum full-phase normalized free equilibrium | 7.008e-12 |
| Maximum full-phase normalized C L1 | 2.903e-12 |
| Worst independent press/recontact gap bound | -2.611 um |
| Strict opening source-normal chart gap lower | 0.199991767835 um |
| Opening supported contact forces | all zero |
| Maximum normalized physical contact moment | 4.546e-16 |
| Maximum normalized structural-coordinate contact moment | 1.650e-7 |
| Fresh pp/mm resume difference from own full endpoint u/z | zero |

The directional checks include both structural bodies and supported force unknowns at two step sizes. They test one complete force-vector direction per variant, not a full Jacobian inventory. Limits stay 1e-5 directional, 1e-6 equilibrium/wrench, 1e-8 complementarity, positive pressure, 50 um physical gap, strict positive opening. Separate force/moment scales are 1e-4 N/1e-4 N m. All six positive supports remain; two supported forces activate on press/recontact. Every accepted phase includes real free-body bending/rotations, reactions and both-body endpoint work contractions. These contractions do not establish integrated path work.

All four full and proof inventories are [1,2,3]. pp/mm prefix and proof inventories are [1,2], ending strictly open; fresh resumed inventories are [3]. Own checkpoint and passing full/prefix SHA identities are bound before continuation. Independent Fraction gap proof uses actual authoritative binary skin points after separate skin reconstruction agrees; original all-pair Q1 gap proof is retained for press/recontact, and exact global-z/variable-normal chart positivity proves opening. No production projection oracle or sampled surface substitution is used.

Safety passed actual orientation/provenance/content incompatible checkpoints, precancellation, direct contributor nonprofile refusal, low-level force validation-context refusal, default automatic identity/checkpoint continuation, and a legacy-valid public multiple-beam transient allocation trap. Corrected public ordinary-force refusal also passed before path/contributor/BC allocation. Existing S3 physical atlas/work directional and legacy Q4 monolithic full coupled tests passed. The installed current CLI completed.

## Evidence, retained failure and scope

One new immutable 629-payload wheel: 082f9600e99b0daf5c8bda1a49235186b98ea190a4aaff479402f76f704c80e3. Two changed and 627 identical payloads versus wheel92f5da4.... Source impact retains unchanged legacy/cycle/tangent/c-scaling/pressure/kernel evidence, rather than replaying unrelated suites.

24 guarded jobs: one build,21 passing testcase invocations,one retained test failure,and the passing installed CLI. Attempt19 ordinary failed because a route expectation missed the earlier explicit-program guard; no solver response began. The corrected targeted refusal passed in a unique attempt; the failed input/stdout/stderr/JUnit remain intact. Reviewer-found settings/provenance fixture errors were repaired before their safety execution. Test-version changes were confined to safety/reporting/new ordinary refusal; metadata proves earlier unit/cycle/proof function ASTs unchanged.

Exact new-scope process-wall use257.7632303000137/480s; remaining222.23676969998633s including unused protected60. Maximum job25.02633190000779s; sampled process-tree peak205.03515625MiB. JIT disabled,Numba/native pools1;629payloads/6784private imports rehashed. No active process and no further execution planned. Raw C:/ANYworkspaceWork/contact_q4_physical_orientation_20261008 contains CLOSURE.json,ledger,input/source/package/runtime/exit/time/RSS/full logs and all uniqueattempts. IMPACT.md records function/source reuse; lead-owned inspectors/central records remain untouched.

This is a planar-reference, small-rotation, frictionless development row. Four body sign combinations with the declared legal reflected numberings are covered; arbitrary numbering/material anisotropy/warped reference/common rotation/finite rotation/spatial inf-sup/general nonlinear hidden rollback are not newly qualified. The inherited zero-alignment floating reference-polarity confidence limit remains. The admitted skin map is reference_skin + u + h*(theta cross dref); its second-order structural-coordinate wrench deficit is reported without erasing rotations.

## Next connected required slice (recommendation only)

Finite-rotation physical skin/work and actual controller-path certification is a consequential next mechanics boundary. The present h*(theta cross dref) omits h*(R-I-[theta]x)*dref, while the whole-face swept bounds assume affine fixed-map nodal paths. Enabling the existing corotational structural option alone would therefore use an incorrect surface/work map and an unproved chord certificate. A coherent next slice must adopt the physical rotation convention, carry its pose-dependent work/Jacobian/Hessian into the unchanged supported-force equations, and certify the actual nonaffine path before public integration. Pressure/spatial stability and nonlinear material rollback remain separate required obligations. No new slice was started.

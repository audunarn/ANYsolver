# Native material patch / deformable S3 development evidence

## Latest opt-in material-area activation — ce3e5495

The unchanged higher-penalty low-yield fixture now completes all nine targets
.25/.5/.75/1/0/.25/.5/.75/1 with the explicit activation setting below. This is a
new algorithmic candidate; both historical default failures remain NONPASS.
First target:21 geometry queries, gap7.116um, nonzero accumulation9.045e-5.
Full cycle:48 queries, peak penetration19.203um under50um, maximum resultant-law
accumulation4.11144e-4, zero unload storage and exact open/split restart.
Support force/moment errors6.93e-9/6.49e-9; full plastic-increment owner tangent
errors3.38e-8/2.15e-9 under1e-5. This is the six-resultant associated ellipsoid
law, not fibre/J2 plasticity or general material acceptance.

The material-aware limiter queries actual full patches and certifies the prefix
with radius/internal rotation, physical normals/offsets, orientation and rim
bounds. Endpoints only select a proposal. Both physical commit and eight-cut
merit/gap checks remain unchanged. Query cap256, activation gap1um inside the
50um physical budget; unsupported/unresolved paths fail. Settings/revision bind
restart; default and historical line descriptors remain unchanged. No automatic
algorithm switch, increased Newton/backtrack limit or fixture load/penalty tuning.

Installed wheel59b5372d70281a38118ad0182e87bec67cb973cc34c1b5cee6385e8a51f18e49:
10 changed checks97.281s191135744B;5 affected compatibility/example checks
43.246s333393920B. All518package files/216imports match; JIT0/pools1, no runtime,
import or hash errors. Three patches/two deformable facets press/open/recontact,
exact continuation and staged cancellation pass. Limiter-level hidden radius-spin
and finite-edge crossings, own second-native block, query exhaustion, cancellation,
complete state preservation and incompatible settings checkpoints pass.

Raw `C:/ANYworkspaceWork/contact_native_material_s3_20261004/candidate04` includes
source checks, input hashes, resource/runtime/import logs and private wheel.
`first_target` failed runner preflight (wrong relative test root), with no
numerical process launched; repaired `first_target2` and subsequent groups pass.
Supporting Read review found no concrete source error; requested tests now pass.
No engineering/application/release promotion, spatial/enforcement convergence
or universal speedup follows. The failed default is not a converged timing baseline.
[Summary](activation_summary.json), [package checks](package_activation_verification.json),
[supporting review](activation_review.md).

## Historical multiple-facet extension

Candidate `fbdd5c27`; private wheel SHA256
`db29c3e1c28a53f1d6e4cf5f56727f2216c8c953adf7fc77be46392b2bfdd360`.
Raw `C:/ANYworkspaceWork/contact_native_material_s3_20261004/candidate03`:
24material checks142.032s188338176B;7affected compatibility checks6.164s325988352B.
517files/223imports match, no runtime/import/hash errors, JIT0/pools1.
Two orthogonal S3 facets/three patches/two native beams retain120coordinates;
one beam/two facets retain78. Complete contact/owner work and support wrench,
per-pair press/open/recontact, open restart and positive director admission pass.
Earlier line checkpoint replay and ordinary-route lazy import pass.

Additional source history under `contact_coupled_tool_staging_20261004`:

- `numbering16`: test accessed wrong vertex-force field; corrected.
- `numbering17`: real report ordering defect; residual/tangent parity held, all
  nine corner-force components differed (maximum5.614N). Corrected using exact
  authoritative translation columns, not node-label or coordinate inference.
- `numbering18`: numbering/work/wrench and affected restart pass2checks7.623s.
- `facets19`: remaining18-column normal guard rejected wide map; widened only
  for the explicit compensated material route.
- `facets20`: independent120-coordinate work and coupled response pass16.782s.
- `facets21`: full owner derivatives/support wrench, cycle/open restart and
  negative-director rejection3pass53.317s.
- `facets22`: reviewer-requested per-pair active/open assertions1pass38.254s.

Supporting Read review found the cycle initially checked only aggregate energy;
per-pair pressure and open-gap assertions now pass. No remaining production issue
was found in its bounded map/polarity/restart review. The earlier reviewer claim
that45/51/57 rotational scaling changed legacy behavior was withdrawn after exact
parent-source comparison: those entries already existed. No legacy replay was
performed to resolve that source fact. No engineering/application/release claim.
Numericalv2 rejects prior area checkpoints; legacy line identities remain unchanged.
Uniform-pose angular-resolution failure and coarse-programme gap/merit failure
remain unresolved. No tolerance, cap, interval-drop or hidden-target repair.

### Native yielding discriminator — no coupled admission

Production remainsfbdd5c27; supplemental tests bindbe0fa6bf and use the same wheel.
The exact resultant-ellipsoid section is reconstructed with lower declared yield,
preserving its reference, elastic/metric/hardening tensors and captured inertia.

- `material_plastic23`: yield.001 fixture completed but did not yield; failed
  positive-accumulation fixture assertion7.625s. Not constitutive evidence.
- `material_plastic24`: yield1e-5/penalty1e6 accepted three targets, then failed
  at target1 with9gap rejections and lastgap−50.004469um;11.761s. RetainedNONPASS.
- `material_plastic25`: one discriminating higher-penalty1e7 trial; failed at
  first-target gap/merit,3.493s. No tolerance/budget/load tuning followed.
  `test_draft.py` retains the exploratory test; raw logs preserve earlier inputs.
- `material_plastic26`: local plastic-branch60-coordinate owner derivative and
  physical-history disposal, plus both failed-solve prefix checks3pass21.127s.
- `candidate03/installed_plastic`:3pass19.360s185868288B on the same wheel.
- `candidate03/installed_plastic_restart`: complete mechanical descriptor and
  nonzero-plastic prefix restore delta1pass17.551s185135104B.

Local directional errors5.032e-8/2.352e-9; trial accumulation.000479898 andgap19um.
The1e6 fixture's accepted three-target prefix has maximum accumulation.000349513
andgap41.425um within50um; all station accumulation is monotone and exact restart
restores its compensated positions, nodal/cell rotations, resultants, shell and
material state. This is a bounded code check; full requested programme remains
NONPASS. The1e7 fixture preserves the virgin zero-target prefix.
Supporting Read review requested comparison of complete mechanical descriptors;
added and verified. No independent engineering acceptance was performed.
Cumulative35outcomes contain34unique cases and one changed restart repeat.
All517files/223imports still match, JIT0/pools1, no runtime/hash/import errors.

`material_plastic_cycle27` separately checks the already working.75 peak through
explicit targets.25,.5,.75,0,.25,.5,.75:1pass22.219s. Tests at`aec4148a` add complete
final support-wrench/equilibrium reporting; `candidate03/installed_plastic_cycle`
1pass22.184s185233408B. All7 targets complete, normal storage becomes0 at unloading,
station history stays monotone, and split restart matches exact bytes. Maximum
penetration41.425um under50um; normalizedsupportF/M4.67e-14/4.36e-14. This is a
bounded resultant-ellipsoid lifecycle code check, not full-load or engineering
qualification. The current36outcomes/35unique cases include the earlier one
changed restart repeat. Production/wheel remain unchanged; all files/imports match.

## Latest two-beam extension

Candidate `c211d4c9`; private wheel SHA256
`987a05acbf67b11d6a33f67e0abdb58f6a0732fac2c5df4e7d017b5369a643b2`.
Raw `C:/ANYworkspaceWork/contact_native_material_s3_20261004/candidate02`:
32installed outcomes135.178s331382784B;517files/217imports match,JIT0/pools1.
Two material patches share one S3; all102coordinates and cross blocks retained.
Supporting Read scrutiny found no new consequential source issue. Requested
pre-change line checkpoint compatibility now passes on source/current wheel;
the fixture binds its prior wheel/source/module hashes and is preserved as bytes.

Source history in `contact_coupled_tool_staging_20261004`:

- `material_two_s3_owner08`: coarse .5,1 target NONPASS at gap/merit limit.
- `material_two_s3_discriminator09`: test fixture moved fixed root; corrected.
- `material_two_s3_discriminator10`: nearly uniform axial perturbation exhausted
  angular resolution. No relaxed controls or tiny-interval drop.
- `material_two_s3_discriminator11`: nonuniform smooth work/tangent and explicit
  four-target coupled solve/split restart pass22.832s. Changed diagnostic fixture,
  not a retrospective pass of the uniform pose/coarse programme.
- `material_two_s3_boundary12`: own-block hidden rotation, capability isolation,
  nine-target example pass24.270s.
- `material_two_s3_state13`: staging exception/cancel, incompatible gap restart
  pass15.608s.
- `material_two_s3_compat14`: prior-wheel line replay and affected legacy/current
  example routes14pass54.156s.
- `material_two_s3_wrench15`: current coupled tangent/support wrench and split
  replay pass25.569s. Force/moment scales.008N/.016Nm.

Prior artifact capture: `candidate01/legacy_capture`, one new routine prefix from
the unchanged line fixture using the prior installed wheel. No saved friction,
impact or consumed qualification execution replayed.

## Earlier single-owner candidate

Candidate `46ea65f6`; private wheel SHA256
`d654f456679403486be46e2dc200f0657e008e43c6b8e9873ad7f60cac6d86ba`.
Raw build/install/commands/file hashes/import identities/runtime/resource/result
records: `C:/ANYworkspaceWork/contact_native_material_s3_20261004/candidate01`.
Earlier source records: `C:/ANYworkspaceWork/contact_coupled_tool_staging_20261004`.

- `material_s3_geometry01`: hidden normal/finite-edge discriminator, 2 pass.
- `material_s3_source02`: initial work/owner checks, 7 pass; before reference guard.
- `material_s3_boundaries03`: hidden S3 inversion/friction isolation, 2 pass.
- `material_s3_workflow04`: current finite-section work, cycle, penalty sensitivity,
  force/moment balance, restart and staging rollback; 11 pass, 26.286 s.
- `material_s3_example05/06`: retained example failures accessing result wrapper.
  Mechanical solve completed; example result access was corrected to `.contact.contact`.
- `material_s3_legacy07`: corrected example plus affected legacy routes, 28 pass,
  46.317 s, 338309120 B peak.
- `candidate01/installed_checks`: current package and affected routes, 39 pass,
  73.466 s, 349569024 B peak. Includes installed runnable example.
- `candidate01/package_verification.json`: all 517 source/package files and
  222 imported modules match; runtime/import errors empty, JIT0/pools1.

Runs retain 180 s / 953 MiB process-family bounds. Native per-owner120 s deadline
and all mechanical/integration/gap controls remain unchanged. No saved friction
owner, impact nonpass or consumed formal execution was replayed.

Supporting same-family Read scrutiny found missing reference-normal path proof
and unintended friction bridge broadening. Both corrected; isolated predicates
demonstrate the old/new boundary. Delta scrutiny found no remaining actionable
issue in those corrections. No engineering or application acceptance/release.

Penalty sensitivity is not convergence: 31.093→11.439 um at 1e6→1e7 N/m³,
2.108% force change. All original geometry, acceptance and programme requirements
remain. [Guide](../../GENERAL_CONTACT_NATIVE_MATERIAL_S3_DEV.md).

### First-contact discriminator and time boundary

Trace28 failed only while serializing a NumPy boolean; correctedtrace29 passes
4.507s182824960B. Two disposable Newton iterations of the failed1e7 fixture use
the same origin/gates. Eight permitted backtracks and two smaller diagnostic
probes; no physical commit, production cap change or full failed-solve replay.
Origin bytes remain exact. Iteration0/cut5 is open withplastic accumulation
7.442e-5. Iteration1/cut8 hasgap-12.129um andcontact force.010699N against.00125N
applied;merit.008109 exceeds.001211. Diagnosticcut9 staysopen at3.424um with
lowermerit.001209, but never enters production. Derive area-aware first-contact
fraction control under the same8backtracks/path/gap/state gates, with finite
activation and no zero-gap stall. No simple yield bound on18retained resultants:
actual station stress comes from the constrained generalized-cell conjugate.
Full-loadNONPASS unchanged. Raw candidate03/trace28/trace29 and summary retained.

At the original120-hour boundary, metadata write used the wrong text encoding
and truncated this README. Restored exact01420d7f bytes before appending this
section with explicitUTF8. No source, prior evidence or numerical result lost.
Development clock exhausted:428891+3120=432011s. User time/scope/method decision
is required before further development. This is not programme completion.

# Matching-point mixed-shell/native conservative buckling

`GEMixedBucklingRequest` and `GEMixedBucklingResult` add a distinct experimental
accepted-state route to `analysis.buckling`. The policy is
`GE_Q4_S3_PHYSICAL_FIBRE_ACCEPTED_CONSERVATIVE_MIXED_BUCKLING_V1_EXPERIMENTAL`.
It admits flat elastic Q4, S3 or mixed shells, generalized, physical-fibre or
mixed native members, matching six-pose point connections, and conservative
nodal dead translations. The public `mixed_buckling_capabilities` describes
definition admission; constitutive validation remains pending until capture.
Line/footprint attachments, current plastic advancement, shell J2, external
load programmes and unresolved accepted equilibrium are rejected.

The S3 components use the actual accepted local correction and translation
arithmetic policy. If local deformation is `d(q)`, its differential is `D`,
local elastic tangent is `K` and local force is `f`, the coordinate material
block is `Km = D.T K D` and prestress curvature is
`G = sum_j(f_j Hess(d_j))`. The unchanged local force includes the correction;
no standalone geometric stiffness is added. The Q4 adapter retains its existing
material/prestress components and prepared correction.

Each native member retains all 42 coordinates, including the 18 resultants.
The material block contains the existing work map and negative coupled
compliance; the geometric block contains the first 24 by 24 force-curvature
block. Both include high and low parts. Physical fibres are never replaced by
station-local inverses. Every recovered station/fibre must match the owned
inventory and canonical history and report an elastic branch. Its fixed-origin
flow radius must exceed the absolute high-plus-low stress by the existing
64-epsilon relative margin plus a binary64 ULP representability witness.
Opposing fibre stresses cannot cancel into admission. A previously plastic
history may unload elastically without changing that history.

The full conservative identity is `H = Km + Gshell + Gbeam + Gpoint`, including
point multiplier curvature and all multipliers before and after support
restriction. The shared general sparse descriptor solver checks the original
mixed equations and constraints at the unchanged `1e-8` criterion. There is
no symmetry repair, condensation, artificial inertia or SPD whitening.
Factors scale frozen accepted prestress. Nearest-shift selection establishes
neither nonlinear limit loads nor spectral completeness or the lowest mode.

Capture binds the accepted state, history, checkpoint, compiled support/operator
data, stable-S3 policy and prepared Q4 corrections. Packet arrays are owned and
read-only; mutation and cancellation return no successful modes. Capture does
not repair an accepted state. Before factorization it rechecks the current
replayed residual with the driver's unchanged free-equilibrium and scaled-gap
metrics (`1e-8` and `1e-9`). The replay already subtracts the dead load once;
only shell rotation covectors are converted back to spatial rows by solving
the three-by-three `P.T` systems. Cached and replayed nonfinite witnesses are
rejected. No extra trial assembly or cache mutation is introduced.
Typed recovery preserves coordinate and spatial
shell modes, native resultants, point multipliers and support wrench semantics.
Existing point/line requests, analysis defaults and checkpoint formats persist.

`examples/stiffened_shell_ge_mixed_buckling.py` provides a public matching-point
eccentric panel and workflow. Its default combines Q4/S3 shells and generalized/
physical-fibre members. `--shell q4|s3|mixed` and
`--beams generalized|fibre|mixed` explicitly select one case.
`scripts/r8_ge_mixed_buckling_dev.py --output <fresh-directory>` records one
connected compression case, effective imports/threadpools/JIT, accepted
checkpoint, sparse decomposition, full modes and checkpoint preservation.
Tension is an explicit separate option. Neither runner performs an automatic
sweep. Execute under the task's single-job supervisor: 600 seconds, 2 GiB
process tree, one affinity, one numerical pool and JIT disabled.

The focused development module independently scatters bounded dense scalar
derivatives, checks actual-update covector differences at three fixed steps,
compares original descriptor factors and verifies chart/restart invariance.
It covers Q4/fibre, S3/generalized, S3/fibre and mixed/mixed models, material
identity/history/branch/yield negatives, opposing stresses, subnormal metadata,
mutation, cancellation and backend failure. Public example definitions are
compared against the exercised model definitions.

Focused source-v1 retained `19 passed, 1 failed, 16 errors`: all-S3 definitions
selected an inapplicable Q4 policy, and the oracle recovered a small geometric
entry by subtracting material-scale matrices. Source-v2 corrected those fixtures
and independently scattered geometric blocks without changing product equations,
loads or tolerances. Its 24 affected checks passed in 21.11 seconds; 12 unchanged
passed checks retain their source-v1 applicability. Supervisor elapsed time was
23.62 seconds, sampled peak process-tree memory 186482688 bytes and sampled
numeric/unresolved thread maximum one. Effective pools, affinity and JIT settings
were recorded. Raw logs, JUnit, source hashes and runtime records are under
`.qualification/b3-ge-e4-pl/r8-ge-mixed-buckling-dev-20261005-v1`.
The initial bundled-runtime launch lacked `psutil` and failed before starting a
child; that startup evidence is preserved. The actual checks used the previously
effective `C:/Python/Python314/python.exe` runtime.

Supporting review then identified the cached-witness admission gap. Source-v3
checks the repaired current-state guard with 16 corrupted-coordinate/resultant/
nonfinite-witness negatives, four valid mixed-family captures and one point plus
one BL5 P0 seam. All 22 affected checks passed in 11.49 seconds (supervised
13.98 seconds, sampled peak 186171392 bytes, one numerical thread). Corruption
is rejected before factorization and both corrupted-call and restored-checkpoint
bytes are preserved. Unchanged split, factor, chart, history and restart evidence
is retained by impact; this is not a replay of an unchanged campaign.

Installed integration: all52 mixed-route checks PASS, zero skips/errors,26.628s.
The installed public mixed-shell/mixed-native example completes; accepted
checkpoint bytes are unchanged. Frozen-prestress factors are11211.39615199803
and41263.84675594574; original equation/constraint residuals<=1.0531e-15.
The new diagnostic script also executes against the installed artifact, retaining
its checkpoint, sparse packets and physical provenance.
WheelSHA256:9fd1400670a09e6b011f0b307d851b9a79b6c9db0beabaaf7cc8acaecd84de80.
All423 package Python files match the bound source; imported facade/site identity,
pools1/JIToff and affinity[0] are verified. Installed suite/public workflow31.108s,
sampled peak186880000bytes. Supervisor retains600s/2GiB ceiling; observed numerical
worker count1, while its declared thread ceiling remains8. No measured speedup.
Supporting independent OpenAI source/delta/artifact review has no unresolved
correctness finding on this tested scope; it does not meet different-model-family
scientific acceptance. Full G4B, external/platform/scale/consumer obligations,
scientific acceptance and release qualification remain open. Failed evidence
and original unexecuted prepared full-campaign runners are preserved.

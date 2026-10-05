# Experimental elastic native physical-fibre BL5 workflow

Select `BL5_ELASTIC_NATIVE_FIBRE_V1` explicitly in
`LinearDefinition.bl5_material_policy`. The owner admits flat virgin-elastic Q4
with `Q4_ALGORITHMIC_PULLBACK_V1`, supported native axial/biaxial physical-fibre
members, optional generalized members and six-pose points, and actual BL5
`p0` or `continuous_p1_coarse` lines. The five director-bond rows remain
unchanged: three translations and two director components, with normal spin
free. This does not adopt the polar six-row research candidate.

The public sequence is `create_analysis`, `preflight`, `solve`, `recover`,
`checkpoint`, fresh-owner `restore`/`solve`, and
`buckling(GENativeLineBucklingRequest(generation))`. The headless
`examples/stiffened_shell_native_fibre_bl5.py` exercises that complete sequence.
Its `--family axial|biaxial`, `--beams fibre|mixed` and
`--basis p0|continuous_p1_coarse` choices preserve declared section data; the
background factor is an explicit physical input, not invented stiffness.

Every candidate must preserve virgin native histories and remain on an
elastic-interior branch at every station/fibre. Native high/low stresses,
inventory, positive flow radii and unchanged ULP/yield-margin witnesses are
checked before publication. A witnessed plastic history/branch or unresolved
yield margin raises `BL5NativeElasticDomainError` with element/station/cause.
Ownership, inventory, JSON and programming failures retain their original
errors; they are not relabelled as constitutive nonconvergence or retried.
Failure and cancellation preserve the accepted prefix.

Snapshots use the existing native-material binary schema, arrays, integrity
reader and exact same-parent replay. The explicit material policy, native beam
identity, BL5 descriptors and compiled model identity bind the new model. Only
the owner/driver model-admission seams recognize this combination; no legacy
reader, schema or default meaning changes. A snapshot from another model or
policy is rejected. Fresh snapshots are created by this workflow; no old S3
archive or portable restart candidate is consumed.

`GENativeLineBucklingRequest` and `GENativeLineBucklingResult` identify
`B3_GE_NATIVE_FIBRE_BL5_ACCEPTED_BUCKLING_V1_DEV`. The sparse descriptor retains
all 42 native coordinates per member, all shell coordinates, existing line
coefficients and optional point multipliers. It includes the complete BL5
scalar-work curvature and shell/native prestress contributions. No mass,
condensation, global dense production operator or symmetry repair is added.
Factors scale frozen accepted prestress; they are not nonlinear limit loads or
a completeness guarantee. Original equilibrium `1e-8`, compatibility `1e-9`,
spectral equation/constraint `1e-8` and derivative `1e-6` criteria remain.
Old point, mixed-point and generalized-line request domains/defaults are
unchanged. Query `native_line_buckling_capabilities` for this explicit route.

Development evidence is in
`.qualification/b3-ge-e4-pl/r8-native-fibre-bl5-dev-20261005-v1` with source
bindings, runtime/import settings, raw diagnostics and failed evidence retained.
The first source check produced 10 failures and 4 passes: a prefixed public
pencil identity was compared with a raw matrix mutation digest, and the
corruption control incorrectly used an accepted owner despite the established
fresh-owner restore contract. Both were repaired without mechanical changes.
The affected ten checks then passed; the four unchanged passed controls are
reused by impact. This covers biaxial physical-fibre, mixed generalized/fibre
and axial physical-fibre models, two admitted BL5 spaces, actual public
restore/continuation and headless example, a bounded independent full-coordinate
descriptor/direct BL5 curvature oracle, the unchanged derivative plateau,
mutation/cancellation/stale-state/corruption refusals and typed yielding versus
unmodified ownership errors. These are development checks, not acceptance.
Runtime verifies one CPU, one thread per actual pool, disabled JIT and unforced
SkylakeX dispatch with isolated exact CI dependency imports.

The supporting same-family development review found no blocking issue. An
offline wheel was built and installed into a fresh target without global
installation. The first installed attempt stopped in collection because the
runner lacked the examples namespace path; that setup failure remains intact.
With only the runner path corrected, all fourteen new checks and two selected
legacy point/BL5 fixed-checkpoint checks passed (16 total, 34.02 seconds).
All 424 package Python modules matched source bytes; all 244 loaded solver
modules came from the fresh target. The complete installed headless example
also completed, recovering eight fibre stations and twelve line work records.
Fresh restore and continuation were byte-exact; accepted checkpoint bytes stayed
unchanged during spectrum. Example equilibrium was `9.3960e-11`, compatibility
`9.2908e-18`, and the largest eigen/constraint residual was `3.2913e-16`.
The source and installed numerical children used one sampled numerical job;
the installed child peaked at 191635456 bytes under the 2-GiB/600-second limit.
Build setup separately recorded two Python processes before test bodies.

Wheel SHA256 is
`52bf905e84682206256996d2440af1812972d92e66464b7faca61710852d2eec`.
Source/module/artifact bindings, import manifests and exact commands are retained
with the raw evidence. Root review and integration remain distinct from these
development checks. This workflow is experimental and
not scientifically or production qualified. Plastic native BL5, S3 native BL5,
consumer integration, scale domains and different-family acceptance remain
open obligations.

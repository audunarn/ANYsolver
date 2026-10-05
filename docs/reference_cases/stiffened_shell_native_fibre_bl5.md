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

## Separate stable elastic S3/mixed-shell development slice

`BL5_ELASTIC_NATIVE_FIBRE_MIXED_SHELL_V1` selects
`BL5_ELASTIC_NATIVE_FIBRE_MIXED_SHELL_V1_DEV` for a flat mesh containing admitted
elastic S3-V2D cells, with optional algorithmic Q4 cells. The earlier Q4-only
policy continues to refuse S3. When no Q4 exists, its selector is irrelevant;
the example retains the historical selector. Every actual BL5 segment still
must follow an edge of the declared Q4/S3 cells. No surface-normal replacement,
sixth bond row, physical port/lift, quadrature or multiplier basis changes.

The existing stable elastic S3 material/prestress/chart map is consumed by the
finite driver and conservative capture. Fresh snapshots use the unchanged
stable-native binary schema and replay, with the explicit mixed-shell model and
material policy bound into their identity. Existing readers and old S3 archives
are not changed or consumed. The same `GENativeLineBucklingRequest` dispatches
the selected owner; mixed-shell results/capabilities/pencil identities report
`B3_GE_NATIVE_FIBRE_MIXED_SHELL_BL5_ACCEPTED_BUCKLING_V1_DEV`.

Use the example's `--shell s3|mixed` option for this separate domain; its default
remains Q4. The focused slice includes all-S3 biaxial and axial fibres plus a
mixed Q4/S3 generalized/physical-fibre model, both admitted line spaces,
physical recovery, fresh restart/continue, chart restart and prestress-factor
parity. An independent bounded S3/native full-coordinate scatter and direct
BL5 scalar-work oracle preserve the original derivative and spectral criteria.
Versioned `s3-v1` evidence is retained under the existing evidence root;
`handoff-s3.md` identifies the current inputs and exact commands. The source
slice passed **16 cases** in 44.34 seconds. After supporting source review, a
fresh offline wheel and isolated target passed all **32 installed cases** in
73.84 seconds: the 16 new cases, 14 impacted Q4-native controls, one legacy
point/request control and one legacy BL5 fixed-history/chart/restart control.
All **424** package modules matched source bytes, and all **245** loaded solver
modules came from the fresh target. Bound source inputs stayed unchanged.

Both installed headless examples completed with eight recovered fibre stations,
twelve line work records, byte-exact fresh restart/continuation and unchanged
accepted checkpoints during spectrum. S3 equilibrium was `8.5474e-11`, gap
`1.8340e-17` and maximum eigen/constraint residual `3.9265e-16`. Mixed-shell
values were `2.3353e-10`, `1.4190e-17` and `2.9972e-16`. The spectrum reports
frozen-prestress factors, without completeness or nonlinear limit-load claims.

Wheel SHA256 is
`b3d5f572797f3c2954d1bf9dc1c6b4293da14c5812e543dbde7f314a60207291`.
Actual isolated dependency imports, unforced SkylakeX pools at one thread,
one-core affinity and disabled JIT were verified. The installed child took
84.88 seconds and peaked at 194437120 bytes. The source sampler recorded a
maximum numerical-or-unresolved thread count of five in one PID at exit,
including four unresolved ending-thread queries; its pool settings remained
one and the inherited sampler ceiling eight was met. This counter is not a
count of concurrent numerical jobs. Complete samples remain preserved.

This delivers the admitted elastic S3/mixed-shell development route. Plastic
native/S3 BL5, consumer integration, scale/scientific qualification and
different-family acceptance remain mandatory open obligations. Root owns
integration and final acceptance.

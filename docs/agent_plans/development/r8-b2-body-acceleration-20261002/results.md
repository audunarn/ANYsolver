# B2 reference-linear body acceleration — development delivery, 2 October 2026

The existing B2 Q4/mixed/native-S3 static owner now prepares owned equivalent
nodal loads for uniform global acceleration from explicit physical shell density
and beam mass. Point and admitted nodal-rigid-footprint attachments add no mass.
This is experimental implementation, not G4A or aggregate acceptance.

The public method is `analysis.body_acceleration_load((ax, ay, az))`. Its
`B2ReferenceBodyLoad.load` passes to the existing static/batch methods. The
bytes-backed result is immutable and detached. Missing mass leaves existing
static behavior available and explicitly excludes body loading. Invalid supplied
density, nonfinite acceleration and unrepresentable required force fail before
any solve. Static S3 loading does not opt into modes or allocate modal inertia.

## Mechanics and ownership

Compilation prepares a total-DOF-by-three map once. Q4 uses its existing physical
consistent mass acting on uniform translations; S3 integrates uniform areal
force exactly. Beam action is integrated as `J.T M_axis[:, :3]`, then transformed
through the actual physical frame. This retains the mass first moment, declared
origin and section-dependent station trace without rotary-mass cancellation.

The preprocessing representability check compares active-axis rigid-translation
work with integrated physical mass using compensated summation and a relative
`1e-9` bound. It adds no absolute floor and changes no equilibrium tolerance.
Zero acceleration and a representable subnormal remain valid. This is a check of
total active-axis force, not a certificate of every local component or moment.
Ordinary-scale independent quadrature tests check full loads and virtual work.

## Actual verification and retained failures

- Initial focused source20/20; affected source122/123 exposed an overlapping
  footprint test fixture. The existing overlap admission was retained; the test
  now uses the established five-cell fixture.
- Follow-up source25/26 failed an overbroad expectation that `1e-320` must be
  rejected. Its total required force was representable. The revised test checks
  actual lost-force min/2min-subnormal cases and explicitly accepts `1e-320`.
- Repaired focused source26/26. Final installed127/127 across the body-load,
  Q4/mixed/footprint descriptor and mixed-static test modules.
- Independent controls cover distorted Q4, exact S3, oblique/reversed beams,
  mass-origin changes, large rotary inertia, coupled generalized sections,
  total force/moment and arbitrary work, ownership, 1/10/100 batch factor reuse,
  complete-case cancellation and invalid/missing data.
- The first public example failed the existing native-scalar admission. Only
  its calculated torsion scalar was converted to Python float. Final installed
  Q4/mixed/S3 examples each complete1/10/100 cases with one factorization and
  balance total weight `-3449.9808 N`. Their attachment hosts differ; the
  displacement outputs are not a matched discretization comparison.

Wheel SHA256 `0c4d6edba5385d3c9e3dd0ddf96899cfb27fae55ff2aa1db6893a17e66b03e15`
binds391 source/wheel/site modules, base7994c8d3 plus the archived product patch.
Actual imported solver paths are installed-site paths. Python3.14.2; numerical
BLAS/Numba1; JIT disabled. Installed check15.295s/183267328B sampled process-tree
RSS, serial600s/1GiB ceiling. These are execution records, not speedup claims.
Consumer sources/persistence are unchanged and were not rerun.

[Raw inventory](raw-v1.json) and [raw archive](raw-v1.zip) preserve68 members,
including failures, commands, fixtures, current source, wheel, hashes, runtime
and resource records. Archive SHA256
`216cbf868e4414e536add463a1f9993cb255b665a3a1470b6b30f47c12b42cf3`.
Known inherited credential-value scan is clear; historical contaminated evidence
is not copied. Existing dissemination restriction remains in force.
[Separate implementer-independent Read review](review.md) found no remaining
development blocker; this is not different-model-family qualification.

## Remaining mandatory scope

Member recovery currently reports nodal-state constitutive fields without the
distributed-load particular field. The payload/capabilities state this limit;
examples request no member fields. Complete body-load section recovery and its
load-record/persistence semantics remain M4/G4A obligations, together with GE
gravity, native distributed loads and later physical/artifact acceptance.
No default, version, legacy equation, checkpoint, formalF03 authority or release
status changes. Full programme and scientific gate statuses remain open.

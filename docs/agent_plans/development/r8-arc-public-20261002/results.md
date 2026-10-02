# Public arc lifecycle development — 2 October 2026

Status: IMPLEMENTED_NOT_QUALIFIED. Base 4746de34; final source is preserved in
`integration-v1.zip` and the local commit containing this report. No scientific
gate, first limit point, stability or capacity claim. Formal F03 is unconsumed.

## Delivered behavior

The existing public owner now supplies `continue_arc_length`, `ArcLengthControl`,
`PhysicalChordMetric`, `ArcResult`, `ArcAttempt` and typed selection failure.
Scope is an accepted coupled Q4-J2/generalized BL5 state, fixed mesh/physical
weights, affine nodal dead translations and a locally usable orientation DOF.
The same fixed-predecessor trial mechanics and bounded cutbacks are retained.

`ANYSSARC1` separates arc history from legacy controllers. It binds model, actual
predecessor digest, generation, origin poses/materials, fixed-seed affine load,
metric, orientation, frozen controls and all accepted-step attempt groups.
Publication rechecks the live predecessor and cancellation under the owner lock.
Fresh restore is separate. Endpoint validation reuses the extracted unchanged
displacement mechanical replay checks and their 64-epsilon material tolerance.
Force/displacement continuation and chart rebase reject arc history explicitly.

Two steps at requested radius 5e-6 complete, with absolute load amplitudes
0.21414850444631248 and 0.13814268700575816 relative to the authentic force seed.
Trial work is respectively 18/14 evaluations, 17/13 solves, 0/0 rejected trials
and 32/24 generalized event cell evaluations. Each publication separately
validates its endpoint mechanically. Final equilibrium is 2.4484374048238137e-11;
constraint norm is 5.8694544271782824e-18. The changing amplitude is not a limit
point or stability proof. The original failed -500 N history remains failed.

Cancellation after step one preserves its checkpoint. Continuing directly or
from a fresh restored owner produces identical checkpoint bytes and compared
material/resultant fields. Selected material recovery performs no assembly.
Corrupt predecessor/controller/work/normal bindings and changed live controls
are rejected. Reentrant callback writes fail. Earlier failed radius attempts
remain covered by the private selection regression.

## Verification and artifact identities

- Source endpoint slice: 14 passed, 99.63 s supervised.
- Expanded source slice: 23 passed, 117.33 s supervised.
- Installed v3: 27 passed, one fixture failure. The late external-context test
  incorrectly required an attribute absent on ordinary owners; its preceding
  public solve, cancellation, restart and recovery assertions passed. The full
  failed log is preserved. The fixture now uses `raising=False`.
- Final installed v4: 2 affected tests passed, 21.19 s supervised, sampled peak
  process-tree memory 177,123,328 bytes. This reruns the complete public lifecycle
  case and the physical metric/constructor case, including the new subclass
  rejection. The other 411 module hashes match v3; only arc-control's constructor
  predicate changed. The unaffected v3 passes are reused by impact analysis.

Final wheel SHA256:
`2e8ea7b90d11253fd0f9fb871481dd8e98e7c6d367038bb3bfb3192d78880c27`.
All 412 source modules matched wheel and installed site. Runtime checks verified
installed imports, one numerical thread in discovered pools/Numba and disabled
JIT. Per-run ceiling: 600 s / 1 GiB, one heavy job at a time. No measured speedup
claim. Windows Python 3.14 only; other platforms and complete CI remain open.
Installed v1/v2 builds were superseded before execution and confer no test pass.

Commands/runners, source and fixture hashes, build logs, raw tests, runtime
identities, sanitized resource metadata, final source and the prior active note
are in `integration-v1.zip`, SHA256:
`3fa53c4d947bb4bfccb914abbcdad89750b31f7dd5d1d4e3e4c6b65d1be2d2c2`.
Original runs reside in `%TEMP%/r8-arc-public-installed-v1` through `v4` and
`%TEMP%/r8-ge-pressure-source-v1/{arc-checkpoint-v1,arc-public-v1}`.
No environment credential map is copied into the archive.

## Review and remaining boundary

OpenAI worker `pressure_precision_review` identified missing live-predecessor,
predictor and cumulative-history bindings, then implemented the trial/checkpoint
portion; root implemented publication and the public driver. Separate worker
`b2_baseline_audit` reviewed the lifecycle slice and identified frozen historical
control validation, an overbroad external-load capability claim, the missing
public attempt type and inconsistent metric subclass admission. All were fixed;
the source predicates and affected runtime checks support closure. Root also
compared the separately extracted mechanical validator with its predecessor.
This is code review, not independent scientific/cross-family qualification.

Read [the public scope and usage](../../../stiffened_shell_arc_development.md).
ANYfem arc-specific workflow verification, physical metric/refinement evidence,
registered first-limit-point/descending-branch acceptance and full programme
requirements remain open. Do not extend this local pair into an automatic
amplitude or mesh campaign. No release, push or main merge was authorized.

## Subsequent ANYfem integration

The previously open arc-specific consumer check now passes through the existing
ANYfem adapter; no consumer product code changed. Local ANYfem commit `f92929f`
adds a standing regression and usage documentation. One installed check passed
in 5.39 s (7.56 s supervised), peak process-tree memory 187,777,024 bytes.
It covers standalone input and native Project round trips, owner construction,
accepted-prefix cancellation, a separately saved solver checkpoint, fresh-owner
restore, exact continued checkpoint parity and selected material recovery.
The small elastic-prefix case is integration evidence, not material/capacity
qualification. Controller state remains in the solver checkpoint, not the
Project definition.

Reused ANYfem wheel SHA256
`16e3d8634ecc0cdbc78c449066db448eddf312ead0f3119d45e9622ade57e754`;
all 98 product modules still match source/wheel/site, paired with the final
412-module solver wheel above. Actual imports, one-thread numerical pools/Numba
and disabled JIT were checked. No new run authority was consumed.
`consumer-v1.zip` contains the runner, preparation, module/fixture identities,
raw logs, runtime observations and sanitized resource metadata; SHA256
`d481f4c9a632f9552f4d17ce148422610227c043f567a7130cd92c56288f62a3`.

## Next mechanics decision

Read-only review by `pressure_precision_review` checked the coupled fixture and
current acceptance records. E04 is still NOT_STARTED with no executed matched
mixed capacity comparison. The `coupled("p0")` history fixture has no identified
analytical or executed external capacity oracle. E01 elastic and E02 torque
evidence cannot supply that oracle, and standalone B3 arch evidence does not
qualify the coupled model. No additional solve was run for this review.

The next task is concrete V22/E04 case admission: geometry, supports,
imperfection, compatible laws and connection idealization; a bounded bracket
around the first load maximum; and comparable external outputs. Ascending and
descending accepted equilibria plus turning-point restart are required. Fixed
reference physical measures and declared shell/beam weighting must replace
fixed-mesh equal weights for refinement claims. If that physical case needs
elastic-shell, S3, follower/moment or other attachment admission absent from the
current controller, implement the prerequisite rather than change the reference
to fit the current API. Another extension of the -500 N fixture would not answer
the missing-reference question.

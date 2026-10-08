# Exact committed-material history reuse — 2 October 2026

Development only; no accepted capability or installed artifact change.

The cache binds source index and exact binary material coordinates to an immutable
committed-frame tuple. It stores copied, read-only state and returns owned arrays.
Replacing the history invalidates it before lookup; restore uses a separate scratch
cache. Resident entries are bounded by the existing integration-point cap. Candidate
history queries retain uncached replay; no interpolation or physical commit occurs.

Focused checks: 3 passed in 6.24 s (bounds, order/duplicates, copy ownership,
commit invalidation, existing restore atomicity and analytical force/tangent).
Retained-history parity and both-body reversal tangent: 2 passed in 68.34 s;
reversal call 63.52 s, previously 52.87 s. These runs do not demonstrate speedup.
Raw logs: `C:/ANYworkspaceWork/contact-friction-history-cache-local-20261002.log`
and `C:/ANYworkspaceWork/contact-friction-history-cache-retained-20261002.log`.

Read-only OpenAI worker `history_cache_review` found no concrete implementation
defect in identity, copy ownership, eviction or restore isolation. It did not run
checks or provide engineering acceptance. Source-index separation and post-eviction
numerical parity were not separately tested; the existing restore test warms the
live cache before corrupt-checkpoint attempts. Optional Mistral was previously
unavailable; no equivalent cross-family acceptance is claimed.

One prospective retained coupled tangent is registered in
`history_cache_tangent_v1_registration.json`. The old saved candidate was written
at tangent entry, whereas the old 374.553 s timing belongs to a completed tangent.
Their pose identity is not established: do not calculate a speedup ratio from them.

The new matched uncached run completed622.763s versus343.481s cached, both46
evaluations, with bitwise identical force/tangent arrays. Process peaks were
198737920B uncached and207151104B cached. Keep the bounded cache. This is a single
matched tangent result, not balanced whole-route performance qualification.
Registrations/results and `history_cache_matched_comparison.json` retain identities;
both run authorities are consumed.

Follow-on mechanism: strictly separated S3 faces have zero anchors/storage. Their
past cumulative slip/dissipation/released storage are additive offsets absent from
force. Read-only reviewer supported exact-arithmetic invariance but warned that
zeroing offsets changes floating-point cancellation and can alter restart ledgers.
Implementation therefore applies only to `_integrate(full=False)` candidate work.
Canonical full=True commit controls, restore and public queries retain full replay.
A vertex-gap certificate with positive numerical margin declines touching or any
penetration; historical quadrature partitions and actual previous pose are retained.
Three focused checks passed4.97s (endpoint/event parity, canonical commit/restore,
per-face positive/touching/penetrating certificate). Raw
`C:/ANYworkspaceWork/contact-friction-separated-work-local-20261002.log`.

State-only optimization's retained tangent exhausted180s (process190.135s,
197681152B); no completed tangent/parity claim. Preserve raw
`contact-friction-separated-work-tangent-20261002` and its log.

The remaining candidate partition still subdivided by all old contact fronts.
For the same certified-separated source and empty disposable work state, those
fronts no longer mark physical history discontinuities in candidate force. A single
per-face decision now omits them only for candidate integration. Current overlap,
actual last-frame path, integration rule and controls remain. Default direct
quadrature and full=True commit/restore keep every original partition.
Read scrutiny found no remaining physical-history dependency, but noted old cuts
can incidentally improve resolution of new transitions. Retained-partition parity
and tangent checks therefore remain necessary; adjacent-level agreement alone is
not universal proof. Broader thin-overlap/stick-slip/transition qualification remains.

Isolated partition comparison plus endpoint/event canonical checks:3passed29.85s.
Saved recontact level1:504→96points,4.216→0.996s; level2:2016→384points,
15.637→3.933s. Existing force/moment/work comparison gates pass at both levels.
`separated_partition_comparison.json` retains outputs and counters. Raw root
`C:/ANYworkspaceWork/contact-friction-separated-partition-local-20261002`.

Retained full tangent after separated-state/partition change:55.503s,46evaluations,
process61.534s/193699840B. Derivative-resolution and integration checks pass. Against
the matched canonical output, force relative difference2.526e-11 and tangent2.500e-6;
see `separated_tangent_comparison.json`. This does not qualify arbitrary thin fronts.

Integrated C5_PARTIAL_REPLAY_SEPARATION_FULL_V1_20261002 passed: all five original
nonguided increments and final checkpoint,513.90s pytest call,519.475s process,
224055296B peak. All six frozen source/test bindings match; authority consumed.
`separation_full_v1_result.json` and `_checkpoint.json` retain the outcome. Split
restart now uses that saved reference, with authentic new two-increment checkpoint
and resumed continuation; no repeated full reference solve. No acceptance/release
or installed-artifact claim follows from this development result.

Authentic partial-slip split restart passed529.94s, process537.424s/249552896B.
Final checkpoint integrity equals the uninterrupted reference exactly, including
accepted history; six frozen source bindings verified. Registration consumed;
split/resumed checkpoints and separation_restart_v1_result.json retained.

An independent mixed-stick/slip clipped-triangle oracle was then derived without
calling the production kernel. For material coordinate b, area density.16(1-b),
overlap a=.02, tangential displacement delta0+d*b with delta0=.00599,d=.001,
initial open shift s0=.78599 and normal touch.75, final traction is
min(250*(delta0+d*b),1.5). With c=.01 its integral is.00475000666666667N and
uniform-source-x derivative is-.188533665835411N/m. A separate read-only worker
confirmed the integral and proportional-path event-force equivalence; discrete
event dissipation is not covered by this endpoint-force oracle.

Routine test endpoint/event modes, levels1/2/3 and history partitions on/off:
force integration checks pass, but both tangent evaluations reject level3 coarse/
fine probe disagreement~.003767 against unchanged1e-5 gate, before comparing the
analytic derivative.2failed8.54s; process10.319s/196091904B. Raw root
C:/ANYworkspaceWork/contact-friction-clipped-integral-local-20261002 contains
failed_source snapshots and logs; clipped_triangle_reference_mode_0/1.json retain
force rows. This is a new unresolved case, not invalidation of the preceding
five-step/restart evidence. Next bounded discriminator separates probe-kink aliasing
from quadrature bias; do not increase tolerances or launch another coupled solve.

Prospective next bounded check: two material points in the mixed-friction fixture
remain in the target during proportional pressure/slip loading after touch at.75.
One sticks, one slips. Independent continuous slider: D=.25*(.00599+.001*b),
cap=1.5, kt=1000, L=max(D-cap/kt,0), dissipation=cap*L/2,
storage=min(kt*D,cap)^2/(2*kt). Run event subdivisions8/32/128;
require decreasing dissipation error and <=1% at128, final force/storage1e-9
relative and slip1e-7 relative (absolute1e-12). This is a local development
refinement check, not general temporal acceptance. Routine180s/953MiB; classify
failure before further work. No complete coupled solve is repeated.


## Canonical partition fallback and cancellation — 2 October

The bounded discriminator found integration bias: retained cuts at level3 with
original2e-7 probes give analytic derivative error4.07e-9 and probe disagreement
3.75e-6; omitted cuts give.0038359/.00376747. Smaller probes do not resolve it.
See mixed_derivative_discriminator.json. Historical failure remains unchanged.

Only an unresolved optimized tangent may retry once with canonical partitions.
Both evaluations share the existing candidate cap; retry must pass original
integration/tangent gates plus fast/canonical force, moment and work agreement.
Successful policy stays with the same committed-frame tuple, including residual
line searches; commit/restore clear it. Generic errors and resources never retry.
Endpoint/event analytical checks and shared-cap rejection passed3checks11.45s in
contact-friction-canonical-partition-fallback-20261002, portable4acwu1sb/P01.

Own read-only reviewer history_cache_review identified that except Exception
failed to reset an unvalidated policy on BaseException cancellation. Replaced it
with success-guarded finally, re-raising every failure. Real unresolved-tangent
fixture with injected ValueError/KeyboardInterrupt at the canonical evaluation:
2passed6.35s, process8.010s/189595648B. Both keep physical checkpoint unchanged and
reset the latch. Raw contact-friction-retry-cancellation-20261002, portable3ihel30x.
This is focused code scrutiny, not cross-family or engineering acceptance.

Impact reuse: both prior full/restart raw directories contain candidate logs and
no unresolved_candidate.json (the harness emits it for unresolved tangent or
resource exceptions). The new wrapper preserves every previously successful
_evaluate_once path. Reuse those tested paths; they do not qualify new fallback.

Pressure-ramp work check passed1test4.37s (call.38s), process5.967s/186548224B.
Dissipation relative error11.71875%,3.07617%,.77820% for8/32/128event subdivisions.
Force/slip/storage gates pass; state unchanged. Output partial_pressure_ramp_work.json;
raw contact-friction-pressure-ramp-work-20261002, portablesyjdpduk/P01.
This confirms local convergence, not work accuracy of the full workflow's4-stage
setting. Next bounded action: compare actual accepted-step work under event/step
refinement using retained physical paths, before any new expensive coupled run.

Prospective retained-path discriminator: reuse only the five saved FE poses and
verified pressure fields, not their old work ledger. On the same canonical final
material partition compare (event subdivisions, spatial level)=(4,0),(4,1),(12,0),
(32,0). Integrate independently replayed cumulative dissipation/storage/release.
This separates coarse spatial error from event bias at unchanged physical paths;
no re-equilibration, restart or spatial qualification claim. Retain all rows and
cost/sample counters. Routine180s/953MiB and existing32768partial sample limit.
If temporal differences exceed2%, select an accuracy-controlled event implementation
or an explicitly finer candidate before new coupled work. If spatial differences
dominate, resolve their partition/integration cause instead. A resource failure
selects bounded implementation work, not automatic cap increase.

Retained-path discriminator terminal:1passed42.63s; cumulative D for4/12/32events
at level0=.0456256362/.0459234282/.0460083354J. Level1 at4events=.0456256065J.
Spatial difference~6.5e-7 relative, event4-vs32~.00832; no refinement gate claim
beyond this fixed path. Saved_workflow_work_refinement.json retains raw values.
Next single step-partition control: split each same affine physical segment at its
midpoint,16events per half, on identical original147material points/weights. Compare
D with saved unsplit32events, <=2% relative response budget; measure release/storage
separately and preserve no physical mutation. No equilibrium or new restart claim.
Routine180s/953MiB and existing sample limits; no repeated unsplit reference solve.


Step-partition check terminal:1passed13.29s, call9.36s, process14.894s/193748992B.
Ten half-segments with16events give D=.046015762795J versus unsplit32events
.046008335373J: relative difference.00016143645 (0.01614%). Same147material points,
4974partial samples; no physical mutation. Release storage6.58715898e-6J versus
6.52643825e-6J (~0.93%); final storage~2.5e-15J is numerically negligible.
Result saved_workflow_step_partition.json; source/resource record in
retained_work_refinement_result.json. Earlier refinement process44.174s/222056448B.

These checks bound work sensitivity on retained FE paths, not changes in coupled
trajectory, arbitrary spatial cuts or broad C5 admission. Do not replay the two
successful coupled authorities. Next checkpoint the coherent development source,
then verify the installed partial-replay profile with focused physics/state tests
and obtain scoped independent assessment; required broader programme stays open.

Independent read review: ramp-work derivation valid, but the step comparison only
bound point count. It did not record identical coordinate/weight/path/settings
identity. Preserve those unbound v1 outputs; no isolated-step claim from them.
Bind exact quadrature arrays, work columns, initial/accepted geometry/pressure/pose
and restart contract excluding only the deliberately varied event count. Rerun
only these changed fixed-path checks under the same routine180s/953MiB limits.
Narrow claim to total dissipation: released storage changes~7.9% at4vs32events,
so no all-work-quantity convergence claim. Step test renamed accordingly; other
work quantities remain measured, not assertion-qualified. No whole solve replay.


Corrected bound comparison terminal: reference1passed44.00s, split1passed13.85s.
Exact input identity matches; total-dissipation difference remains0.01614%.
Latest source/resource bindings in retained_work_refinement_result.json, raw
contact-friction-retained-work-bound-20261002/y5zff_h6 and
contact-friction-retained-step-bound-20261002/00ti5_vi. Unbound v1 outputs retained.
No all-work-quantity, continuum, coupled-trajectory, acceptance or release claim.

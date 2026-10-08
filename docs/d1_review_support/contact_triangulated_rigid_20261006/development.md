# C4 finite triangulated rigid obstacles - development evidence

6 October 2026. Parent3829f01d; authoritative checkout
C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001.
**Implemented and private-installed development-tested. Engineering acceptance,
full C4 qualification and release remain open.**

## Implemented route

Immutable oriented finite mesh descriptor; one elastic e4-pl-s3-v2d physical
source skin, fixed consistently oriented nonoverlapping planar target triangles,
explicit frictionless penalty settings and the ordinary von Karman static driver.
Every target face contributes to shared support and weighted gap before applying
E=k/2 sum(w*w/s) on compressive supported modes. Existing Jet2 geometry derivatives,
moving supports, cross-face Hessian blocks and both-body work are retained.
Target vertices are geometric labels, never extra FE nodes or constraints.

The fixed-plane swept enclosure uses exact affine maps, pre-cancellation error
bounds and quadratic Bernstein normal controls. Its plane superset only certifies
the gap; the force law retains the finite footprint. Exact closed intersections
check every unrepresented contact, including a singular component beside a
positive-overlap component. A single exact positive-area represented convex
polygon must cover the whole intersection; otherwise unsupported rim contact
refuses. Internal diagonals add no physical feature or pressure unknown.

## Final artifact and checks actually inspected

- Installed12PASS,3.835957199917s,181317632B peak.
- Wheel83d9f843ae9ecb3b549295d35aafe6c5cc14eb205cb758291404435c8fb22b1e;
  raw dist5/installed5. All536 source/wheel/installed payloads match.
- All234 solver imports resolve to installed5; runtime/import errors empty.
  Effective JIT disabled, Numba1 and all3 numerical pools1.
- Actual force-controlled deforming shell: gap-4.610748106977895e-6m,
  energy6.38688713091931e-8J. Support+load+skin-contact force error
  5.475786490904966e-11 and moment error4.172718773173467e-11,
  each against1e-6 with separate .1N/.1Nm scales.
- Actual path active/open/active at approximately-30/+10/-30um; exact final
  displacement and canonical complete checkpoint equality after split restart.
  Changed mesh checkpoint refuses; cooperative cancellation propagates.
- Independent constant-gap energy/force/centroid-moment and geometric normal-H
  oracle; directional work/tangent1e-5, actual FE skin-rx pullback, partial
  footprint and rigid rotational virtual work, diagonal-exchange invariance.
- Finite outside opening, initial interior overclosure, hidden intermediate
  crossing, normal inversion, cancellation-scale bound/refusal, tiny positive
  mesh overlap, singular rim, disconnected hidden rim and degenerate coverage
  controls. Captured settings/operator/inventory mutation refuses.

The50um gap is this development fixture's explicit setting. It does not amend
the programme's qualification budgets, dimensional gates or historical criteria.

Root independently checked final9 owned-file hashes, payload records, effective
runtime/import roots and actual result evidence; diff ownership and whitespace
checks pass. Separate Read scrutiny closed the consequential derivative/work,
swept-enclosure, binding and rim findings. This same-family supporting review is
not formal independent engineering acceptance. Mistral remains cached unavailable.

## Retained failures, authority and limitations

24 terminal numerical/build/install jobs consumed122.03240189980716/180s;
remaining57.96759810019284s, maximum process-tree peak216449024B. Perjob120s/
953MiB/onejob, JIT0/pools1/watchdog. No held or frozen authority renewed.

Eight NONPASS jobs retain label/report integration defects, overly coarse remote-
corner swept refusal, omitted geometric term in the independent H oracle, test
cancellation/serialization defects and missing checkpoint emission. Corrected
criteria were not loosened; earlier successful artifacts also remain at their
executed hashes. Five builds include consequential changes and the final EOF-only
integration repair, whose earlier diff check had omitted the new file. Its prior
hashes/summary/payload manifest remain as *_before_eof.json. No complete-route
speedup is claimed.

Q4, multiple source elements, nonplanar/moving/free tools, finite-rotation,
nonlinear-material admission, physical boundary-only forces, friction, self-contact,
native combinations and scale acceptance are not established. The independent
constrained structural-K displacement oracle remains missing. Existing unaffected
transaction/no-contact evidence is reused by scoped impact analysis; no new
whole-route5% regression claim or blanket rollback qualification is made.

[Usage guide](../../GENERAL_CONTACT_TRIANGULATED_RIGID_DEV.md).
Raw C:/ANYworkspaceWork/contact_triangulated_rigid_20261006 contains worker_handoff.md,
summary.json, final_source_hashes.json, installed_payload_parity.json, exact input
commands/hashes, per-job resource/runtime/import/log records and installed_eof_final/
actual_result.json. [Previous restart](prior_restart.md) retains prior obligations.

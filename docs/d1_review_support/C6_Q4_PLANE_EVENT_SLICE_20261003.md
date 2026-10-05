# Q4 plane pressure-mode events — development evidence

3 October 2026. Parent `ee22dc60`; the owned Git checkpoint and
`contact_c6_q4_plane_events_20261003/source.json` bind final source content.
Implemented, source-tested and isolated installed-tested development. No
independent engineering acceptance, release or historical-default change.

## Question and implemented slice

Prior Q4 plastic fixture energy was strongly timestep-sensitive, with11.648%
endpoint excess at dt2.5e-5s. The bounded question was whether explicit contact
branch timing removes the discrepancy without changing the pressure/material laws.
The independent fixture has uncoupled affine membrane and rigid-normal modes;
it cannot establish impact-induced plasticity.

New explicit `q4_plane_event_subdivision_dev` selects guided fixed-plane Q4
elastic/plastic profiles. Pressure-mode normalized gaps are the penalty switches.
Physical corner/complete-path gap checks remain separate. Endpoint duration trials
solve `M*a+f(q_predict+beta*h*h*a)=0` from one committed material parent; Newton
uses `M+beta*h*h*K`. Candidate trials are discarded. Proposed event endpoints are
reequilibrated and every pressure mode must pass its complete represented Hermite
branch enclosure before physical commit. The Hermite lift is the declared discrete
path, not a certificate for the exact continuous trajectory.

The local helper uses exact rational coefficients/discriminants and enclosed
stationary roots with outward floating bounds. It encloses the cubic defined by
supplied floats, not upstream matrix arithmetic errors. A duration root is only
a proposal: hidden excursions or ambiguous/below-minimum brackets cause bounded
cutback. No current law, mass, material kernel or accepted static profile changes.

Shared stage/query budgets span localization/re-equilibration/cutbacks from one
committed origin. Failed callback attempts count. V8 elastic/V9 plastic packets
bind controls and semantic support/gap/rate/departure phase; plastic packets retain
the accepted return-map parent. Ordinary truncated END, including one inside an
event gap band, does not acquire boundary restart authority.

## Focused checks

44 helper outcomes pass in the geometry worker's bounded selection. Independent
linear/quadratic/cubic/Fraction controls cover extrema, hidden crossing, near-double
root, simultaneous mixed branches, omission and bounded callback failures.
8 integrated event-driver outcomes and2 affected legacy outcomes pass through
scoped selections; this is not one broad qualification run.

| Record | Outcomes / relevant result |
|---|---|
| `plane-newmark-events-dev-20261003-b` |44 passes,4.917s,180240384B |
| `contact_q4_event_elastic_b_20261003` |Independent elastic trajectory/energy passes; separate budget-test assertion fails |
| `contact_q4_event_elastic_c_20261003` |Corrected stage-work budget/opt-in check passes |
| `contact_q4_event_plastic_a_20261003` |Independent trajectory/material/work and yielded restart pass |
| `contact_q4_event_controls_d_20261003` |Elastic response, failed query/cutback accounting and END rejection pass |
| `contact_q4_event_cancel_e_20261003` |Yielded event-family cancellation and same-model reuse pass;43.243s,188801024B |
| `contact_q4_event_restart_f_20261003` |Final driver:2 END cases plus yielded split/control/tamper checks pass;150.409s,188690432B |
| `contact_q4_event_compat_g_20261003` |Old elastic active restart and nodal load/restart pass |

All successful runners use actual reconciled imports, JIT off, NumBa/BLAS threads1
and180s/953MiB limits. Runtime/resource files and selectors are retained in raw.zip.
Unchanged codec/static/native evidence is reused, not repeated.

## Matched development discriminator and package

Identical fixture/load/material/mass, dt3e-5s and end.003s:

| Route | Steps / cutbacks | Maximum energy defect | Final defect | Elapsed / peak RSS |
|---|---|---|---|---|
| Historical profile, source |100 /0 |13.469525% |1.460879% |64.275s /164163584B |
| Event profile, source |101 /0 |0.000072341% |0.000072341% |68.525s /165969920B |
| Event profile, installed |101 /0 |0.000072341% |0.000072341% |73.725s /169127936B |

Two represented events occur at.0007999999966s and.0009171867752s.42 endpoint
requests and291 stage evaluations; final open/unloaded. Minimum represented
physical gap−3.535871575e-5m meets the explicit5e-5m development budget. The
energy evaluator uses known fixture masses, uniform elastic deviatoric storage,
constant plateau dissipation `20*volume*alpha`, contact storage and zero external
work. It is not a general hardening/nonproportional energy evaluator.

The comparison resolves the identified discrepancy in this fixture. These single
cost runs are not balanced performance measurements and establish no speed-up.
The below1% development result does not supply formal temporal/engineering
qualification or prove monotonic refinement.

WheelSHA256 `b4b0a30be0562a86fe41c1c57b1ef5ffd733d07ee15da78aac30f404c05ced01`.
All205 imported module hashes and numerical fields match source/installed.
Artifact folder `C:/ANYworkspaceWork/contact_q4_event_package_20261003` holds the
isolated install, runner/environment/hash reports and measured comparison.
The existing installed accepted shell artifact remains unchanged.

## Retained failures and scrutiny

- Elastic a: cancellation callback signature mismatch; corrected to accept context.
- Elastic b: budget test expected an endpoint cap alone to force failure, although
  bounded cutback finished. It now explicitly exhausts shared stage-work; mechanics
  and resource limits are unchanged. Original failure remains retained.
- Geometry a:2 expected scalar bounds were narrower than the required outward
  floating enclosure. Tests now allow2ULP; independent Fraction sample checks stay.
- First wheel build/install: protected user pip cache denied access, then missing
  wheel install failed. New build uses no cache inside owned workspace; successful
  source/installed runs are bound to the resulting wheel. No machine installation.

Read-only same-family review found no concrete defect in endpoint reequilibration,
complete branch/physical gap checks, material parent, counters, END restriction,
semantic phase restart or fixture energy algebra. It performed no independent
execution and does not constitute engineering acceptance. Reviewer-identified
callback failure, yielded localization cancellation and END gaps now have checks.
Stationary/grazing multimode integrated drivers remain unverified beyond local
helper controls. Full D5/C6 and C0–C9 remain incomplete.

Next: a mechanically coupled impact-induced plasticity fixture with an independent
reduced-work reference and matched-end refinement. Preserve native friction's
closed-strip tangent NONPASS and every consumed execution restriction.

# S3 event subdivision — development checkpoint, not promoted

Parent `f2bab7ee`. Exact current candidate/delta in `raw.zip`; v11 records in
`current-source-check.zip`. No event installed verification, final independent
acceptance, release or speed claim. The C0–C9 objective remains unchanged.

## Candidate

Explicit event opt-in has distinct constant/history profiles and fingerprint-bound
time/gap/root/localization controls. The physical Newmark/penalty equations remain.
Mass-null algebraic work is condensed solely for the endpoint-family calculation;
physical inertia is retained. Generalized modes form complete rational gap numerator
polynomials. Bounded Bernstein root isolation retains every coefficient; actual
endpoint equations refine roots. No mass, stiffness/eigenvalue clipping or discarded
support is introduced. Schur roundoff uses original subtraction/mass scales.
Proposed durations are reequilibrated by the ordinary coupled solver from committed
origin; cancellation, work and full lifted/endpoint gap checks precede commit.
See the [prospective derivation](../C6_S3_EVENT_SUBDIVISION_SLICE_20261001.md).

## Executed source checks

| Stage | Observed result | Interpretation |
|---|---|---|
| v1 | 8 passed | Broad-bracket prototype; later independent counterexample disproved first-root selection |
| v2 | No tests ran | Incorrect selector, no numerical result |
| v3 / diagnostic | 7 passed, 3 failed / 1 failed | Condensed rigid-mode positivity-preflight rejection |
| v4 | 8 passed, 2 failed | Ill-conditioned companion polynomial roots |
| v5 | 9 passed, 1 failed | Bernstein isolation corrected root conditioning; prefix roundoff remained |
| v6 | 1 passed | Focused prefix-boundary correction |
| v7 | 13 passed | Uniform activation/release, independent scalar Newmark/energy, history work, restart, limits and failure/cancellation at that stage |
| v8/v9 | 1 failed each | Tilted continuation detects sub-minimum transition after localization |
| v10 | 2 passed | Review fixes: exact point root and gap-only checkpoint promotion |
| **v11 current module** | **12 passed, 4 failed**, 6.56s pytest | Release/restart/history and tilted continuation repeat a resolved start event; candidate NONPASS |

Selections overlap; do not sum counts. Raw logs and runtime/selection/resource
records retain exact targets/settings. Routine180s/953MiB/thread1/JIT-off used.
No tolerance/minimum_dt/resource increases converted failures to passes.
Earlier source-stage passes do not establish current whole-candidate correctness.

Independent references include accelerated free flight, condensed scalar release,
scalar Newmark energy/work, a three-mode manufactured multiple-duration-root case,
and actual skin/P1 weighted-gap reconstruction in a tilted S3 fixture. Injected
failure and exact-token cancellation check pre-event physical commit. Failed cases
remain active assertions, without XFAIL/removal or engineering scope reduction.

## Principal finding / next correction

V11 traces identify repeated numerical boundary events. Uniform release starts
with oriented gaps around1e-18m and outgoing rates around1m/s, but its tiny initial
lifted segment still carries the incoming active mask. That mask is invalid at
the1e-8s positive probe, causing repeated cutback.

Tilted failure at t=.0101500192s starts with mask=[false,true,true], oriented gaps
[1.100511175e-11,4.999600194e-5,0]m and rates around−.999m/s. First/third supports
are numerically simultaneous within1e-10s and1e-10m budgets; the tiny first-support
transition should belong to that already resolved boundary. These traces do not
demonstrate a genuinely distinct sub-minimum event.

Retain resolved boundary supports; derive right continuation/coalescing only within
both declared budgets and bind necessary state into event restart. Preserve force
contributions and full interval gap checks. Do not shrink minimum_dt, suppress
contact or enlarge tolerances. Then run the same coherent source selection, one
installed artifact/example and final independent review. General C6 still open.

## Review / retention

[Read review](review.md) found broad-bracket root selection, point-root loss and
gap-only promotion of truncated checkpoints. The first was replaced; the latter
have v10 regressions. Mistral startup Access denied, preserved incomplete.
Independent OpenAI scrutiny is development evidence, not engineering acceptance.
`raw.zip` preserves51files including source stages, diagnostics, exact candidate,
tracked diff and failed worker attempt; embedded manifest/readback receipt bind
bytes. `current-source-check.zip` binds v11 separately. Defaults, prior accepted
static evidence, historical failures and consumed authorities remain unchanged.

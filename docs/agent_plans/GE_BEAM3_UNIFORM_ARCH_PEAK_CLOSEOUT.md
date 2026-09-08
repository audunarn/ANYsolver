# Native arch load-peak diagnostic closeout

Implementation `0780ffa51c9f625c763d491a83b079716818c2e1`, tree
`f65316b05bbeae026408bfaf254fb85bb9a58e79`, base `9d6882144fe01d462df3b532f1e6da247ffe9d7f`.

Outcome: `DEVELOPMENT_PEAK_MACRO_ACCURACY_MEASURED_ONLY`.
A reproducible sampled native descending branch is observed under displacement
control, with all three measured load errors below 2%. This is not an objective
arc-length crossing, full spatial stability proof or full beam qualification.

## Separate inventories

| Inventory | Passed tests | Scientific JSON files | Supervisor seconds |
| --- | ---: | ---: | ---: |
| Unit/reference rehearsal | 9 | 9 | 8.227 |
| Native rehearsal | 1 | 6 | 410.393 |
| Frozen unit/reference A | 9 | 9 | 9.435 |
| Frozen native A | 1 | 6 | 418.348 |
| Frozen unit/reference B | 9 | 9 | 8.227 |
| Frozen native B | 1 | 6 | 416.148 |

Each lane's entire scientific file set is byte-identical across rehearsal and
both frozen replicas. No mechanical/unit worker failed or was retried.
The inherited capacity, earlier accuracy and state-safety inventories were not
rerun or recounted here. The full objective remains active.

## Sampled native branch

| Crown drop | Native load density | Load relative error | Native drop slope | Reference drop slope |
| --- | ---: | ---: | ---: | ---: |
| .006 | .05451552137974471 | .007920339460702364 | .7888956863465496 | .7454205922830974 |
| .008 | .05514125763671928 | .008871432812885605 | -.019201713296080537 | -.036327615493008676 |
| .010 | .054756777475319374 | .009341858735129938 | -.3221309978595698 | -.32835677371900956 |

Relative errors are fractions: the worst load error is approximately 0.934%.
The native last sampled load is below the second. Slopes are positive at the
first and negative at the last two sampled states. No exact peak location,
branch uniqueness, or stability classification is claimed.

Native slopes use the existing analytic tangent and analytically condensed
load-parameter column on cloned models/stores. The GENERAL bordered system
enforces a unit control-coordinate derivative without inverting K alone.
The crown-drop sign is the negative of the controlled y-displacement derivative.
Exact scalar tests include singular K; the actual native bar reproduces slope 8.
Finite-difference frames and empirical stabilization are not used.

Normalized slope discrepancies (denominator max(1,abs(reference slope))) are
.04347509406345218, .01712590219692814, and .006225775859439786.
They are diagnostics, not a claim of relative derivative accuracy near zero.
The source of native slopes is the candidate operator, not an independently
authored tangent reconstruction.

At 128 stations per target, resultant-compliance norm errors are
.008069956603576414, .008291685515459736, and .008052391894305972.
Constitutive errors are at most 5.551115123125783e-17 under the unchanged 1e-11
check. Position maxima are 4.0609101410987725e-05, 5.1850961037783194e-05,
6.20063224336942e-05; frame component maxima are .0020017240383508553,
.0029566205166806554, and .0038722096747407777.
Full history remains elastic. All three equilibria satisfy the unchanged native
Newton threshold; no tolerance, material, load or geometry was altered.

The complete checkpoint is 2376637 bytes, SHA-256
`B3140913B93C304D9AF95A55EDD97E113381F7DB7EC16B11EBE7B1A930F8A0BF`.
Authenticated full decode/re-encode is byte-identical under explicit HISTORY8M.
Original accepted snapshots remain unchanged during slope replay. This was a
new complete programme from genesis, not an old checkpoint extension or retry.

## Bounds and archive

Longest child: 418.3481657999946 seconds. Maximum observed process-tree memory:
345341952 bytes. Frozen-wave span: 418.348166 seconds. Every child reached
terminal state with zero active descendants. Limits remained one numerical
thread, 24 GiB tree memory, 600-second wall, 120-second CPU inactivity,
at most three concurrent workers and 1800 seconds per wave.

Archive: `C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-uniform-arch-peak-0780ffa-20260908`.

90 data files (9645830 bytes), plus a 13575-byte manifest, preserve raw
runs, commands, initial/frozen source, baseline, supervisor observations, audit
and a next-step proposal. Every archived size and SHA-256 was verified.
Manifest SHA-256: `E14AE96363CEDF7E16B0C2393E92696F679C59FE8138E7AD28B6698DCD5EB520`.
Audit SHA-256: `B5F28BC362C59281D789979A59D7E5A23CE265ECC9CC0B04894B4049CDF3C2D0`.

The read-only audit recomputes saved field/load errors and checks checkpoint,
slope-value, inventory, source and replica bindings without a mechanics or BVP
rerun. It does not independently rederive the native tangent. Independent
authorship review remains PENDING; the continuum specialization is same-author.
Only the hash-verified staging duplicate may be removed. Original run directories,
external evidence and all earlier failed incidents remain preserved.

Exactly three research paths were added. All source mechanics, legacy B2/B3,
Q4/S3, section properties, quadrature, recovery, public routing, defaults,
packages and historical evidence remain unchanged. No push, merge or release.

## Next gate and remaining scope

Establish actual objective arc-length continuation across the load peak with
rejected-step safety and adaptive step/cutback. Assess a separately schema-bound
translation-to-arc handoff retaining the complete authenticated source history,
or preregister a bounded fresh arc programme. Never reinterpret old displacement
records as arc records or silently relax cross-programme restart rejection.

Wider postbuckling/slenderness and convergence, scale/history performance,
broader load/support/material/state parity, physical mass/modal/prestress/buckling,
independent review, installed-wheel/public integration and actual objective
beam-shell connections remain necessary. This diagnostic does not complete or
narrow the full production-quality objective.

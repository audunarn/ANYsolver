# Q4/Q4 monolithic force cycle

Verified the assigned development fixture: automatic press, strictly open release, and recontact with genuine free two-body bending. Fresh restart from the open checkpoint reproduced the full recontact displacement and supported force vectors exactly. Engineering acceptance and release remain pending lead review.

## Run

From the repository with the installed package available:

```powershell
python -m examples.general_contact_q4_pair_monolithic_cycle
```

The tested private-package command and all environment variables are preserved in the raw attempt input manifests. The example uses the existing public zero-control `ContactPathProgram`, nodal forces on nodes 3/6 of 0, -5e-5, +5e-5, -5e-5 N, one increment per segment, tolerance 1e-12, and maximum 12 iterations. No product source changed.

## New fixture and evidence

The upper reference midplane is .04 + 2e-7 m; the lower midplane remains -.01 m. Fresh geometry is constructed before preparation. Material, topology, supports, physical half-thickness skins, fine Q1 coefficients, normal regularization 1000, 50 um gap limit, and the admitted linearized director work map remain as in the prior bending fixture. The common upper-uz guide is absent; rotations and target deformation are genuine unknowns. This positive-clearance fixture has a distinct automatic identity; the prior nominally coplanar evidence is preserved.

Every accepted phase was checked independently from saved authoritative binary skin points after agreement with a separate skin reconstruction. All eight original bilinear face pairs and all six positive Q1 supports were retained. No triangulation, production projection oracle, tolerance change, or expensive cell engine was used.

| Check | Observed |
|---|---:|
| Full / open prefix / fresh resume inventory | [1,2,3] / [1,2] / [3] |
| Maximum normalized free equilibrium, full | 6.983e-12 |
| Maximum normalized complementarity L1, full | 4.496e-13 |
| Press / recontact independent gap lower | -2.611 um |
| Opening exact global-z clearance | 0.199999999997 um |
| Opening source-normal chart lower | 0.199991767835 um |
| Opening supported contact forces | all zero |
| Opening target normal displacement norm | 1.892e-20 m |
| Press upper normal deformation range | 2.655 um |
| Press target normal displacement norm | 2.960 um |
| Press upper / target rotation norms | 8.191e-6 / 1.593e-5 rad |
| Maximum normalized contact physical force / moment | 2.033e-16 / 2.143e-16 |
| Maximum normalized contact structural-coordinate moment | 1.650e-7 |
| Fresh resume endpoint u / z difference | 0 m / 0 N |

Force and moment scales are separately 1e-4 N and 1e-4 N m. The frozen equilibrium/wrench limit is 1e-6; complementarity and opening force-release limit is 1e-8. Press and recontact have two positive supported forces, with all six coefficients/supports retained. Complete phase reactions and both-body instantaneous work contractions are in the proof outputs. Endpoint contractions do not establish integrated path work.

Opening uses an exact Fraction Q1 nodal convex-hull z clearance. Exact original corner-normal alignment and a corner L1 normal upper bound also give a strictly positive varying-source-normal gap in the actual projection chart. Rational predicates are authoritative; displayed decimals are approximate. The simpler certificate superseded the pre-execution cell-subdivision proposal, as recorded in raw ORACLE_DECISION.md.

The independent hard-contact reference includes the represented binary initial clearance term g0 = S * delta; its reference equilibrium error is 1.992e-14. Observed nonlinear versus linear displacement differences are 1.930e-6 in press/recontact and 7.438e-6 at opening, reported without a 1e-6 comparison claim or truncation bound.

## Closure and limits

Nine guarded installed-package jobs passed: eight test invocations and the actual public CLI. No failed attempt, timeout, skipped test, or active job remains in this scope. Exact measured process-wall use is 90.65610759999254 / 360 seconds; 269.34389240000746 seconds remain, including the unused protected 60-second reserve. Maximum job wall was 18.8084344999952 seconds and observed peak process-tree RSS 188.77734375 MiB. JIT was disabled, Numba and native pools used one thread; 629 payloads and 2661 private imports were hash checked.

Actual public calls rejected a changed force-cycle definition, changed automatic provenance, and tampered checkpoint contents, and handled precancellation. Declared FEModel fields were unchanged. This elastic fixture and those checks do not qualify generic hidden material-trial rollback.

The unchanged wheel is 92f5da4ab8c3ff5da72b380d2a5fd95b63ec74eba400f11b888a5fab88261eec. Product and old fixture bytes are unchanged. Prior full coupled derivative, positive-c scaling, and legacy-route evidence is reused by function-level source identity; this scope adds the new clearance geometry, active-set release/recontact and open-state restart evidence.

Raw evidence: C:/ANYworkspaceWork/contact_q4_pair_monolithic_cycle_20261008. CLOSURE.json binds input, output, dependency, package and prior closure hashes; each attempt retains command, source snapshots, full stdout/stderr, JUnit, runtime and process-tree accounting. Saved solve/proof stages are separate bounded jobs, with no solver replay for reporting.

Finite rotations, universal pressure stability/inf-sup, spatial convergence, generic nonlinear rollback, and engineering acceptance remain open. The next scientific slice should address spatial pressure/normal-trace stability on genuinely deformable meshes with an independently specified reference, rather than another guided fixture. No such campaign was executed or charged here.


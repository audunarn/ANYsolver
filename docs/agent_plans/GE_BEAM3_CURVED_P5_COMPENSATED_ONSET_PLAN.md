# GE-B3 P5 compensated 32-element onset successor

Research-only continuation from clean `709eb294d78b894289cb1e9b4b10e59877f217c3`.
Exactly five new paths: this plan, compensated_onset_probe, compensated_onset_inspection,
compensated_onset_wave, and test_ge_beam3_curved_p5_compensated_onset. No existing
mechanics, source, test, default, alias, environment or authority path is edited.

## Reason and preserved evidence

The frozen compensated comparison at `29b0d4e06ba4a1275411b3dd39b8843e6cb9c457`
converged for target 0.095 with residual 5.506791506773546e-12 at the unchanged
1e-11 rule. Request `4d4cbecbbba445a4a9656976f1e2dee8` is consumed. Its ten files
(2,378,664 bytes) are bound individually in the successor runner. All 37 earlier
failure/diagnostic files, historical 4/8/16 onset aggregate and both knot-resolved
continuum endpoints remain hash-bound, read-only background. None is rerun.

## Exact extent

Use the already frozen compensated assembly and controller, including high/low
coordinate state, local force-error budget 1e-12, physical residual 1e-11,
16 global updates, ten backtracks and at most 8192 local evaluations per state.
The arch is unchanged: span 2, rise 0.1, 32 elements, 65 nodes, 378 free DOFs,
512 stations/state, order eight per half-cell and the original elastic section.

Reuse the original 13 prescribed drops `i/200`, i=0..12, followed by at most
16 bisections of the earliest sampled positive/negative lateral pair. Width
target 1e-7; retain uncertainty at every endpoint and stop on an uncertain
midpoint. Do not relax the uncertainty band, extend the interval or substitute
an exact-zero claim. Each bisection starts from its saved positive endpoint.

Every accepted state is committed and independently reconstructed through the
frozen model replay. Store both coordinate parts, origin and accepted checkpoint
hashes, full tangent, local responses, station histories and spectra externally.
The new integrity inspector validates normalized coordinate pairs, element/global
low-part identity, fixed coordinates, prescribed low-part zero, raw assembly
scatter, equilibrium, full conservative spectrum, uncertainty, histories,
checkpoint path and search coverage. It is not an independently authored mechanics
oracle and does not qualify the element. No high-part-only schema substitution.

## Execution and evidence

Test only small two-element disposable fixtures before freeze; also test schema,
coordinate, history, hash, spectrum, origin, budget and authority mutations.
Require deterministic bytes for two small rehearsals. Existing compensated-state,
controller and historical closeout tests remain unchanged.

After clean five-path freeze, create a new exact resource request, obtain the
resource administrator's ledger approval, acquire it and run its stored command
once. One contained child, one numerical thread, 24 GiB per process tree, 600 s
child wall limit, 300 s inactivity threshold and 890 s total coordinator watchdog.
No retry, parallel heavy run, reused request or historical output mutation.
Full Git/environment/historical guards precede numerical execution and run again
before publication. Fresh external directories, exclusive claim and exclusive
canonical outputs. Each control iteration emits a bounded scalar checkpoint.

On explicit process/solver/evidence failure, retain progress, stderr, partial
raw diagnostics and any reconstructible last uncommitted evaluation. Do not
create an aggregate. Failure snapshots never become accepted states. Preserve
the global lock until process containment has finished, then release in finally.

On successful completion and integrity inspection, publish a research aggregate
with both continuum endpoint errors, all historical comparisons unchanged,
`historical_recomputed=false`, `accuracy_qualified=false`,
`first_critical_point_proven=false` and `production_qualified=false`.
Even agreement within 2% is only a refinement diagnostic, not complete buckling,
state, dynamic, material, joint or production qualification.

Every outcome retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

## Next boundary

Review actual onset errors, uncertainty and work/state integrity after the new
request terminates. A subsequent engineering/qualification gate needs its own
scope and authority. Existing beams, Q4/S3 and all ecosystem defaults are untouched.

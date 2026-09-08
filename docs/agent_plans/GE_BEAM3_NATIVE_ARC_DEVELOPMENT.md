# Native generalized objective arc continuation development

Base: 1076411c655df09c681a1968c5038dff33632b9b.

Reuse the unchanged spatial Exp frame-chord hyperplane, analytic condensed
parameter column, signed effective loads, native assembly and state store.
Use isotropic translation/rotation blocks averaged over nodes, explicit positive
length and parameter scales, and the spatial left-trivialized predictor dot
policy. At each accepted origin the predictor is a spatial vector; the next
orientation comparison uses the same global spatial trivialization, not a
reinterpretation of accumulated rotation coordinates. Evaluate actual step
increments in the objective chord constraint. Do not modify old mechanics.

Solve full general bordered predictor/corrector equations, with no K-inverse
load sensitivity or automatic branch switching. A singular/ambiguous augmented
direction fails closed. Keep 1e-12 solve and chord residual limits, 1e-11 metric,
covariance and independent engineering identities, and the existing native
reference/load/material guards. Do not symmetrize nonconservative tangents.

The new checkpoint binds complete stress-free genesis/history, signed loads,
metric/scales, ordered arc steps, predictor orientation and residual. Replay
every predictor from its accepted origin on a separate but identity-equal model;
never replace the live model's issued material validators while staging a
checkpoint. Require exact predictor replay and canonical re-encoding plus an
external SHA-256. Preserve 2-MiB/65-snapshot and 60-second validation limits.

Rehearse an analytical signed elastic bar, prefix continuation, resealed input/
history/metric/direction mutations, accepted-prefix failure/cancellation,
preflight/nested scopes, a synthetic fold predictor and a finite common-frame
covariance case with noncommuting increments. The synthetic fold is not a beam
postbuckling reference. Use fixed mixed elastic line (.4,-.1,.15) and nodal
couple (.1,.15,-.12), arc steps (.15,.2), and rotation vector (.4,-.2,.7) with
translation (2,-3,1) for covariance. No tuning after observed results.

Curved and connected plastic lanes use arc steps (.2,.2), scales (1,1) and the
previous combined load patterns. Each complete geometry node includes solve,
full decode/predictor replay, recovery and resumed solve. Run a small smoke
before complete separate local/safety/geometry rehearsals; freeze after they
pass, then run two fresh-directory replicas per lane with byte-identical
scientific output. Rerun the unchanged independent frame-chord geometry suite
as a separate inventory. Do not combine counts.

Each child has one numerical thread, 24 GiB, 600-second wall and 120-second CPU
inactivity bounds, at most three simultaneous workers and 1800 seconds per
wave. No automatic retry. Preserve failed attempts before corrections. The
programme remains private and unqualified, with at most 42 nodes inherited from
the chord evaluator and the existing smaller element/DOF admission envelope.

Actual beam limit points/postbuckling, practical scale, broader loading/support/
initial-field parity, physical mass/modal/prestress/buckling, independent review,
engineering qualification, public integration and objective beam-shell joints
remain required. No public route, default, package version or release changes.

## Preserved initial safety incident

The first safety rehearsal had 18 passes and one test-hook failure. The
factorization injection correctly stopped the second step and the checkpoint
equality assertions passed, but the hook remained enabled when the test next
called the real predictor-replaying decoder. Preserve that failed inventory
and its five-source snapshot. Disarm the test hook after verifying the failed
solve and before independently decoding the preserved prefix. No producer,
checkpoint implementation, load, metric, step or tolerance is changed.

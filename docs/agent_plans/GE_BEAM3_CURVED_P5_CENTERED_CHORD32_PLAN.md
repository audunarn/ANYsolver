# P5 bounded centered-chord comparison

Parent `b9b93afe07b05f6844c0c4e810965a9e450698de`, tree
`2ee313c04063b47f606cbd071a9443d4b9b99676`.
Exactly three added paths: this plan, the centered_chord32_diagnostic research
runner, and its test. No existing source or frozen evidence is changed.

## Extent and purpose

Use the explicitly selected centered-chord assembly from the parent. Its
potential is an exact algebraic rearrangement, not a coefficient, reference,
quadrature, section-law or tolerance change. The previous force-accuracy
comparison failed to meet global equilibrium; it is preserved, not retried.

The successor evaluates the same 32-element arch at targets 0.1 and 0.095
only. Commit/replay the initial state, attempt the second state, and commit
and independently reconstruct that state only if the ordinary research
controller accepts it. No onset grid, eigenvalue calculation, bisection or
qualification aggregate is authorized by this diagnostic.

Retain global residual acceptance 1e-11; total estimated local-force-error
budget 1e-12; 16 controller iterations, 10 backtracks, 8192 counted mixed
evaluations per trial. A failed trial remains uncommitted. Save and replay
its last successful evaluation as an expressly uncommitted diagnostic;
that evaluation may be a rejected candidate, not the last accepted iterate.
Missing states must never be fabricated. The inherited absolute rigid-motion
residual diagnostic remains open; do not reinterpret it as accepted equilibrium.

## Authority and execution

Before numerical imports, validate clean exact HEAD/direct parent/three-path
extent, frozen environment and sibling identity. Bind all eight original
failed-run files, nine controller-observation files and ten force-accuracy
files by bytes and SHA-256. Preserve their consumed requests and claims.

After the three-path clean freeze, create one fresh immutable resource
request for the exact module command and a fresh external directory. Obtain
the resource administrator's explicit APPROVED ledger row, then acquire the
global slot. Never execute alongside another heavy task. Verify exact request,
repository and command identities and reject consumed or cross-runner claims.
Release in finally after the complete child tree terminates.

Use one numerical-library thread; 24-GiB Windows Job process-tree memory cap;
600-second child timeout; 300-second inactivity watchdog; 890-second outer
coordinator watchdog. Inherit the reviewed kill-on-close Job runner. Exclusive
raw files, checkpoints and partial logs remain external. No automatic retry,
request reuse, ledger bypass or timeout extension.

The schema is `GE_BEAM3_P5_CENTERED_CHORD32_DIAGNOSTIC_V1`; assembly records
must use `GE_BEAM3_P5_ASSEMBLY_CENTERED_CHORD_FORCE_ACCURACY_V1`. Old profiles
cannot be relabeled as this successor. Use strict canonical JSON, complete
raw hashes, failure-snapshot revalidation and deterministic observation
adjudication. Revalidate inputs and lease before terminal publication.

## Adjudication and tests

`RESEARCH_CENTERED_CHORD_COMPARISON_CAPTURED` reports the actual
`TARGET_CONVERGED` or `FAILED` solver outcome. A captured failure may be a
successful diagnostic process but is never solver success. Process, authority,
schema, replay or hash failures produce blocked diagnostics, not success.
Every result keeps `production_qualified=false` and
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

Small tests cover two-element success and forced-budget failure, raw schemas,
rehashed mutations, duplicate/nonfinite/noncanonical JSON, immutable prior
bindings, guards before capture, dirty/parent/extent/environment changes,
request consumption, exclusive claims, and synthetic process failures.
They do not launch a 32-element worker. Existing default-path fixtures and
the centered-chord scalar/derivative/state tests must continue passing.

A passing two-state comparison only supports preparing a separately frozen
onset32 successor. It does not authorize the full onset wave, production
integration, defaults, publication or beam qualification. A failed comparison
is preserved for diagnosis without coefficient tuning or tolerance relaxation.

## Pre-freeze result

The complete selected 15-file small regression passed: 258 tests in 45.84
seconds, including 47 successor-runner checks. Historical byte/hash checks
passed for all 27 bound files. This test run did not execute 32-element
mechanics. `git diff --check` passed; only the three declared research paths
are added relative to the frozen parent.

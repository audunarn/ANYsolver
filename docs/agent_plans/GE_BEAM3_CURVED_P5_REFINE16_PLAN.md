# P5 explicit sixteen-element cyclic refinement — 2026-09-06

Development successor to `607e45b9255de35500c6744df06ece9bc6b30e7e`,
tree `b64522aeb8c1c364b234df0bb74c93153b13f93b`.
This is a resource-controlled research diagnostic, not formal qualification,
production integration or authority to activate a selector/default.

## Question and unchanged science

At eight macro elements, the previous controlled cyclic comparison had 4.15%
reverse-loading and 3.42% permanent-set error. Determine whether sixteen
elements resolve the same experiment to below 2%, and report its integration
sensitivity. Preserve all earlier results, including those above 2%.

The exact scientific recipe is the program's literal `CASE`: height-0.4
parabolic reference; the unchanged complete coupled section factor; direction
[1,0.2,-0.1,0.3,-0.4,0.5]; y=0.02; H=0.4; force pattern [0.1,-0.3,0.2]; and
amplitudes [0.1,0.2,0.1,0,-0.2,0]. No load, section coefficient, constitutive
law, reference equation, mechanical residual/tangent, local solver, tolerance
or criterion changes. The reference remains the separately implemented
fixed-history continuum shooting method at 256 steps.

The assembly constructor retains `extent='SMALL8'` by default. The explicit
`REFINEMENT16` profile admits up to sixteen elements and their corresponding
bounded node IDs. It does not change any local/global evaluation algorithm.
The profile is research-only, not a public selector. Seventeen elements remain
rejected. A small two-element test requires byte-identical nonlinear trial
records under both profiles. The new geometry builder agrees exactly with
the previous builder at every earlier supported refinement.

## Frozen implementation and resource sequence

The implementation commit must contain exactly these four paths relative to
the stated base:

- This plan.
- `docs/reference_cases/ge_beam3_curved_p5_assembly_history_probe.py`.
- `docs/reference_cases/ge_beam3_curved_p5_refinement_wave.py`.
- `tests/test_ge_beam3_curved_p5_refinement_wave.py`.

After the clean implementation commit, create one immutable request through
`C:\Github\.resource-manager\request-test.ps1`. Its exact command invokes the
coordinator with that commit and a fresh absolute external ANYrelease output
directory. Record the request hash, bytes, command and output path with the
resource administrator. Estimated duration is five minutes, informational only.
Do not start a scientific child until the administrator has entered exact-ID
approval and the global resource lock has been acquired. No lease is implied
by this plan or the user goal alone.

Execute the stored command byte-for-byte from its registered worktree. The
external PowerShell owner must release only its own lock in `finally`.
The coordinator requires exactly one APPROVED ledger row for the request;
do not add EXECUTION_STARTED before this diagnostic command. Its exclusive
central claim marks the request consumed. A failure does not authorize retry,
reuse, automatic correction or a second wave. Administrator terminal recording
follows completion and release.

No scientific inputs are imported by the coordinator. Authority checks bind
the clean commit/tree, exact changed-path extent, case hash, Python executable
and its hash, exact immutable request command/repository/hash and active lease.
Workers repeat those checks before numerical imports and after computation.
The coordinator checks them again before aggregate publication. This is not
a complete transitive environment freeze, cryptographic execution attestation,
independent mechanics review or an adversarial filesystem security boundary.

## Serialized process controls and evidence

Launch exactly these workers in this order, in distinct fresh subdirectories:

1. `continuum256`: six continuum-history increments, 513 material history points.
2. `elements16_order8`: six discrete increments, 256 stations per increment.
3. `elements16_order24`: the same six increments, 768 stations per increment.

At most one worker is active. Each uses one numerical-library thread and a
Windows Job Object with a 24-GiB whole-tree memory limit, assigned while the
root is suspended and before numerical execution. Reuse the existing process
containment implementation unchanged; do not rerun historical S3 studies.
Each child has a 600-second envelope with termination reserve. Inactivity of
300 seconds without CPU-time or progress-file growth terminates the job.
A separate whole-coordinator watchdog starts before authority validation and
exits at 1,780 seconds, within the 1,800-second wave ceiling. The OS then closes
its Job handles; the external lease-owning PowerShell finally remains in force.

Preserve root PID/command/start timestamp, stdout, stderr, initialization and
per-step checkpoints, process wall/CPU/peak-memory diagnostics, full completed
per-step response records, complete worker summaries and their hashes outside
the repository. No timings participate in scientific adjudication. These
diagnostic checkpoints are not the complete per-station trace protocol of a
future formal qualification runner.

Publication uses same-directory staging and exclusive hard links. Failed or
interrupted staging is never a canonical target; abrupt failure may leave a
pending file for diagnosis. Existing output names are not overwritten. Every
complete worker must have exact identity, six ordered steps, registered
forces/counts, passing residual/local-health checks, bound raw hashes and
summary values reproduced from the raw records. A process or validation failure
stops the wave, preserves existing diagnostics, and creates no aggregate.
Absent later worker evidence is not fabricated.

Only after all three process trees are terminal and all records validate may
the coordinator publish `aggregate.json`. It contains both per-step relative
tip-error sequences and the relative tip difference between integration rules.

- `RESEARCH_REFINEMENT_BELOW_2_PERCENT`: both discrete integrations have error
  strictly below 2% at every registered increment.
- `RESEARCH_REFINEMENT_ABOVE_2_PERCENT`: at least one does not.
- Process/authority/record failures: external blocked diagnostic, no aggregate.

A completed above-threshold diagnostic is not an execution failure or a retry
instruction. Both complete dispositions retain `production_qualified=false`
and `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`. Neither authorizes production or
closes general quadrature/history/local-algebra qualification.

## Ordinary unit validation before requesting resources

- New profile/runner suite: **19 passed in 4.08 seconds**.
- Existing assembly suite: **20 passed in 12.78 seconds**.
- Tests preserve the eight-element default; reject unknown/unbounded profiles;
  compare unchanged small-case trial bytes; verify exact geometry/case inputs;
  reject missing/reused/wrong leases, dirty authority, extra implementation
  paths, noncanonical/duplicate/nonfinite records and mutated hashes, forces,
  counts, summaries and raw data.
- Actual small Windows-process tests verify ordinary completion, timeout,
  descendant termination and denied allocation under a small memory cap.
  They launch no refinement mechanics and create no scientific partial output.
- Failed-wave and publication tests require absent aggregate/target files.
  Threshold adjudication never emits a production qualification flag.

Inspected working-file SHA-256 values:

- Assembly: `C9716ADF7DF21A2063F476F69A5476042CB2C7208B2B5E80AFB0EA755FC15385`.
- Runner: `72552E04F005804E6DC3D812DAF71134CC83C1B8BEB214FB39BD8AB3EBB9F567`.
- Test: `CE4DBA2BD682A1B6ECB2ADA25CD4224A9A349BCADE31730FE4DA6D4D8AE1E740`.

These bind inspected files, not a self-referential commit. No 16-element load
cycle was executed during preparation. The resource request identity and its
execution outcome must be recorded separately after this implementation freeze.

## Scope retained

No production source, B2/B3/Q4/S3 mechanics, defaults, recovery/state laws,
packages, dependencies, workflows or accepted qualification evidence changes.
No push, merge, release or activation is authorized by this development gate.
Further refinement or additional waves require a separately reviewed extent
and a fresh approved request. General nonlinear sections, assembled restart,
arc length/postbuckling, prestressed dynamics, the extreme coupled local
failure, broad curved/slender coverage, independent review, production exposure
and objective eccentric/curved beam-shell connections remain open. The full
development goal is unchanged and incomplete.

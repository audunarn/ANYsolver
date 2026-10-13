# Contact CI5 — deadline repair and exact replay diagnostics

Base `cc6f0962d0f9d39c9989c317df2bc7ddbbf63177`, branch `codex/contact-ci5`.
Local CI repair; not engineering qualification, release or proof of complete
cross-machine replay. No push, PR, workflow execution or main merge/rebase.

## Delivered changes

The twelve native deadline dependencies used by the three reported fixtures
now share `_ge_beam3_effective_deadline`. Application default scale is **1**;
`ANYSOLVER_GE_BEAM3_DEADLINE_SCALE` permits finite scales **[1,8]**. Invalid
declarations, nonfinite bases and overflowed effective budgets fail closed.
The portable CI runner explicitly selects **4**, reports it, and retains its
outer process-tree timeout (the existing workflow uses 1800 seconds).
A 120-second native context therefore has 480 seconds of CI execution budget.
Physical laws, convergence tolerances, iteration/integration limits, cancellation
and transactional state checks remain unchanged. Resource timers do not enter
checkpoint identity. Legacy synthetic expiry tests now expire the effective
configured budget rather than assuming the application default inside CI.

Native/S3 and retained-pair restore errors now append a bounded first differing
record path, stored/replayed values and capped difference count. Definition
binding errors include owner component digests. Exact canonical comparisons
and the aggregate identity remain mandatory; diagnostic generation neither
changes records nor repairs mismatches. Plain tokens omit only the display
newline; component digests hash the original canonical bytes.

## Actual runner evidence and remaining quantities

Read-only logs from GitHub run **38351792519** were retained locally. Its
retained-body-pair failure at canonical byte 44 is inside
`contact.beam_a_force_n[0]` (saved `-1.3863746386554766e-05`). GitHub exposed
only the differing byte, `5` versus `4`, not the entire recomputed value.
The new diagnostics identify the complete local Haswell replay value as
`-1.3863746386548754e-05` on both Windows and WSL. That full token is a local
reproduction result, not a recovered GitHub token.

Existing native/S3 GitHub errors hid their field values. The local reproduction
now reports:

| Case | First differing field | Stored | Replayed, Haswell |
|---|---|---|---|
| active budget / initial guess | contact.pairs[0].tangent_error_n_per_m | 2.7902272984168655e-07 | 2.790227500475597e-07 |
| curved S3 restart | contact.pairs[0].tangent_error_n_per_m | 2.958106896226822e-07 | 2.958106727472888e-07 |
| retained body pair | contact.beam_a_force_n[0] | -1.3863746386554766e-05 | -1.3863746386548754e-05 |

The binding discriminator reproduced GitHub's **exact** identity pair:
default `2831aea349b0a5844ded464aaa3a57fd6517f6742a9e6d9976a1bf7b3341ff1d`,
Haswell `8e70df45b9418558039eb8e22d52c017eadbfa456f06586695604586ba25fc08`.
Differing owner components: **native, pairs, shell**. Matching components include
cached shell stiffness, support, native slots and numerical settings. The saved
schema contains only an aggregate identity, so it cannot retrospectively supply
stored component digests. Component localization does not establish a repaired
definition arithmetic path.

CI4's spectral-norm compatibility and incomplete matrix-arithmetic findings
remain applicable. No new rounding, norm substitution, backend selection or
fixture regeneration was adopted. Universal impossibility is not claimed.

## Verification

Frozen source archives `candidate-source-01` and `candidate-source-02` bind
tested files. Their production code is identical; the second adds three
synthetic expiry-test adaptations. The actual source import paths, numerical
pools, JIT/thread settings and deadline scale were recorded. Windows Python
3.12.13 and WSL Ubuntu-24.04 Python 3.13.12 used NumPy 2.5.4 / SciPy 1.18.1 /
Numba 0.68.0 and the same pinned public sibling sources as CI4. No second physical
CPU was available; verified SkylakeX/Haswell dispatch variation shares one CPU.

| Completed checks | Windows | WSL |
|---|---:|---:|
| Three queued deadline cases, default dispatch | 3 passed, split runs | 3 passed |
| Guard, cancellation/mutation, diagnostic and runner controls | 47 passed | 47 passed |
| Two additionally checked default native restart/initial-guess cases | 2 passed | included below |
| Five original replay/binding cases, default dispatch | 5 passed across focused runs | 5 passed |
| Five original replay/binding cases, Haswell dispatch | 5 failed | 5 failed |
| D1 KKT, default dispatch | passed | passed |
| D1 KKT, Haswell dispatch | failed | not repeated |
| Complete saved retained-body record, default dispatch | passed | failed |

The original KKT gate remains `1e-6`; alternate-dispatch error is
`1.4948506139016305e-05`. Prior CI3 evidence attributes the roughly `1e-13 N`
control-reaction difference to structural response at slightly different states
on a roughly `4e-9 N` reaction; contact contributes exactly zero at those control
coordinates. No further parameter sweep or threshold change was made.

The stronger WSL default complete-record check reports
`contact.energy_error_j`: stored `1.1056579054093155e-20`, replayed
`1.1056579054093008e-20`, with three differing diagnostic leaves. The preexisting
physical-only test passes, but the complete saved-record test remains red.
Its assertion was not filtered or replaced with a fresh checkpoint.

### Preserved red queue

- `test_general_contact_d1_two_body_nonlinear_oracle.py::test_saved_slide_matches_independent_current_contact_kkt`
- `test_general_contact_native_active_budget.py::test_budget_policy_checkpoint_identity_and_default_active_fixture_replay`
- `test_general_contact_native_curved_s3_restart.py::test_curved_s3_active_restart_opens_and_preserves_prefix`
- `test_general_contact_native_initial_guess.py::test_guess_trial_uses_virgin_material_and_preserves_initial_prefix`
- `test_general_contact_native_material_s3.py::test_pre_area_multiple_line_checkpoint_remains_replayable`
- `test_general_contact_native_retained_body_pair.py::test_default_saved_curved_energy_and_identity`

The additional complete-record companion failure also remains visible.
No skip, xfail, tolerance relaxation or fixture edit was introduced.

## Reproduction and retained evidence

Full local commands, source snapshots, outcomes, precise process-wall durations,
sampled tree RSS and stdout/stderr are under `.development/contact-ci5/receipts/`.
The frozen input queue is `CI_FAILURES.tsv`; downloaded existing logs are
`github-failed-38351792519.log`. No external workflow was started.

Focused CI checks use this unchanged selection interface (exact nodes in each
receipt):

```text
python scripts/run_portable_ci.py --workers 1 --timeout-seconds 170
  --development <exact nodeids> --jit on --memory-limit-mib 953
```

The three deadline cases use 290 seconds per local batch, under a 300-second
supervisor. Windows initial aggregate batch hit its outer timeout after two
completion markers; it was not counted as a pass. Separate completed Windows
runs passed all three. WSL's completed aggregate passed all three.

Key receipt prefixes: `windows-deadline-first-two-02`,
`windows-two-fibre-deadline-02`, `linux-deadline-cases-01`,
`windows-guard-and-default-01`, `linux-guard-integration-01`,
`windows-replay-haswell-01`, `linux-replay-haswell-01`,
`linux-replay-default-01`, `lead-kkt-base-01`, `lead-kkt-haswell-01`,
`linux-kkt-base-01`, `native-binding-discriminator-02`, and
`github-byte44-map-01`.

Also retained: interrupted wide deadline patch (not adopted), failed scratch
probe, two defective new diagnostic-test expectations followed by five passing
diagnostic checks, and the Windows batch timeout. Source review narrowed the
candidate and inspected actual receipts; worker zero exits without handoffs
were not counted as completion. The author is not claiming independent
engineering acceptance.

Measured supervised execution: **1254.230573 seconds**, 19 terminal receipts;
largest sampled process-tree RSS **402710528 bytes** (about 384.1 MiB).
No performance improvement is claimed. Full CI matrix shards, different physical
hardware, GitHub rerun and scientific qualification campaigns were not executed.
The repaired deadline cases are locally verified; the six original numerical
failures above remain unresolved.

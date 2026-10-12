# Contact CI3 — local checkpoint, 12 October 2026

**Result: CI3 repair is incomplete. None of the ten queued failures is cleared.**
This branch is a diagnostic/experimental checkpoint, not a completed deterministic
replay implementation or an engineering acceptance.

- Branch: `codex/contact-ci3`.
- Base: `95c335124860a4aec2d7a83f0a628c7d5cfdc6b7`.
- No pushes, PRs, workflow runs, main merges or rebases.
- Main, previous worktrees, protected fixtures, historical failures and all
  original test assertions/tolerances remain unchanged.

## Retained changes

1. The existing two-body KKT comparator reports the structural pose contribution
   to the reaction discrepancy. Its original compared quantities and 1e-6 gate
   are unchanged.
2. A focused regression proves zero active-contact contribution at the fixture's
   control DOFs at common arguments, including the registered finite-difference
   perturbations. It complements, and does not replace, the failing response test.
3. An **unused experimental** scalar reduction module and independent arithmetic
   tests preserve the useful native-worker implementation. They cover fixed FMA
   order, correctly rounded spectral norms for Gram dimension at most three,
   scale extremes, rank deficiency, midpoint ties, refusal and bounded bracketing.
   No native analysis owner imports this candidate.
4. Two reproducible KKT decomposition/probe tools retain the measured diagnosis.

The scalar native integration candidate stayed red on all original queued tests.
Local matrix replacement candidates also broke exact local archived replay.
Their production changes were retired; the ten affected native source files
are back at the base revision. Do not present these experiments as fixes or
as complete host independence.

## Verification

All runs used the unmodified `scripts/run_portable_ci.py` locally, in focused
`--development` mode with JIT on, one worker, explicit time/memory limits,
single BLAS/Numba threads and verified Haswell dispatch as the failing
discriminator. These are exact-node reproductions, **not full matrix-shard runs**.

| Scope | Windows | WSL Ubuntu 24.04 |
|---|---:|---:|
| Immutable main95: original queued tests | 10 failed | 10 failed |
| Rejected scalar integration candidate: same tests | 10 failed | 10 failed |
| Final retained arithmetic + common-argument regression | 26 passed | 26 passed |

The final production native source is unchanged from main95, so its original
failure evidence is reused by impact analysis. The added diagnostic arithmetic
and regression were verified against the final retained source.

Windows baseline: Python 3.14.7; candidate/final: Python 3.12.13.
WSL baseline/candidate/final: Python 3.13.12.
Numerical pins: NumPy 2.5.4, SciPy 1.18.1, Numba 0.68.0, llvmlite 0.50.0,
pytest 9.1.1. Each interpreter has its own editable installation; baseline
installations and checkouts were preserved. Source manifests include new files.
The timing runs have different interpreters/concurrency and are not evidence
of a speedup or slowdown.

## Original red tests

| Module / test | Observed failure |
|---|---|
| `test_general_contact_d1_two_body_nonlinear_oracle::test_saved_slide_matches_independent_current_contact_kkt` | Reaction relative error 1.4948506139016305e-5 exceeds unchanged 1e-6 gate |
| `test_general_contact_native_anchored_enclosure::test_anchored_accepted_fixture_exact_replay[active-1-98d22…]` | Exact multiple native/S3 record replay mismatch |
| `test_general_contact_native_candidate_reuse::test_exact_candidate_reuse_parity_invalidation_and_bounded_storage` | Exact replay mismatch |
| `test_general_contact_native_curved_s3_multifacet::test_curved_multifacet_extension_preserves_single_facet_restart_identity` | Exact replay mismatch |
| `test_general_contact_native_curved_s3_restart::test_curved_s3_active_restart_opens_and_preserves_prefix` | Exact replay mismatch |
| `test_general_contact_native_curved_static::test_curved_material_authentic_split_restart_and_atomic_failure` | Continued checkpoint bytes differ from the archived full checkpoint |
| `test_general_contact_native_fibre_enforcement::test_enforcement_coarse_independent_gap_and_fixture_preflight` | Exact replay mismatch |
| `test_general_contact_native_fibre_results::test_committed_recovery_energy_units_origins_and_separate_storage` | Exact replay mismatch |
| `test_general_contact_native_fine_lifecycle::test_anchored_fine_policy_staged_lifecycle[opening]` | Exact replay mismatch |
| `test_general_contact_native_surface_replay_owner::test_replay_coupled_active_rebase_and_split_restart` | Windows: native friction axial resolution exhausted; WSL: first-touch candidate requires released physical history |

Full node IDs, commands, process-wall/RSS receipts, errors and source identities
are in the local evidence referenced below. No skips, xfails, pressure-law changes,
fixture rebaselining, omitted replay fields or tolerance relaxation were introduced.

## Interpretation and next decision

The KKT discriminator attributes the measured control-reaction discrepancy to
structural response at two slightly different solution states. Contact terms
are exactly zero at the registered common arguments. The discrepancy is about
1e-13 N on a roughly 4e-9 N reaction. Three additional Newton iterations did not
clear the gate. This supports the measured arithmetic sensitivity; it does
**not** prove universal impossibility or absence of every structural defect.

For native replay, replacing scalar norms alone did not close the record graph.
Dense work maps, structural evaluation/linear solves and other numerical kernels
remain. Exact legacy compatibility has not been demonstrated. Two-dispatch
parity of a helper does not prove complete cross-machine replay.

The next coherent implementation outcome must cover the complete record-producing
arithmetic route and show compatibility with the archived records before
production promotion. Further norm-order fitting or small matrix substitutions
are not supported by this slice. If the chosen deterministic route cannot
reproduce a legacy case, retain its original red gate with a specific numerical
explanation; do not silently change the checkpoint contract. The friction
integration/history failures also require their own compatible repair.
No complete-delivery forecast is supported by this checkpoint.

## Local restart evidence

Living note: `../.development/contact-ci3-20261012/TASK.md`.

- `CI3_FAILURE_DISPOSITION.json`: all ten baseline/candidate verdicts and receipts.
- `EXECUTION_ACCOUNTING_FINAL.json`: supervised execution totals and uncertainty.
- `CANDIDATE_SOURCE_MANIFEST.json`: final retained source.
- `NATIVE_CANDIDATE_SOURCE_RECOVERED.json` and
  `native-candidate-source-recovered.zip`: rejected native candidate content,
  recovered from the verified untouched WSL payload before retirement.
- `native-scalar-candidate-not-promoted.patch` and
  `local-map-candidate-rejected.patch`: preserved integration experiments.
- `LEAD_KKT_REVIEW.md`: qualified interpretation of the worker's diagnosis.
- `mistral-replay-01/02/03.log`, `mistral-kkt-01.log`, and `receipts/`.

Three native-worker phases ended without a complete handoff. Phase 3 also ran
nine checks outside the required supervisor; their full tool logs and inclusive
tool-wall bounds are preserved, but precise process-wall/RSS/source receipts
are missing. No precise figures were fabricated or executions repeated merely
to reconstruct that accounting. Lead finished verification and disposition.
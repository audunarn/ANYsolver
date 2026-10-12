# Contact CI4: partial deterministic replay integration

Base: `647164328f2c4cda7058813d93293d99264f13bd`.
Branch: `codex/contact-ci4`. This is ordinary CI repair, not scientific
qualification or release. **Cross-machine exact replay is not established.**

## Changes

The existing `_ge_beam3_deterministic_reduction` scalar kernels now feed the
actual centered-reference tangent, native surface measure/bounds, curved S3
center bound, B3 projection/work, two-cell search and retained whole-pair
reference measure/monotonicity calculations. No global NumPy monkey patch,
runtime CPU selection, fixture-dependent answer selection or public API change
was introduced. The helper's stale unused-candidate description was corrected.

Residual/Hessian work maps, both-body contributions, retained coordinates,
physical laws, checkpoint schema and numerical tolerances remain unchanged.
Protected checkpoint fixtures were neither regenerated nor edited.

The existing retained-body-pair test filters three diagnostic fields and can
use a freshly produced in-memory checkpoint. That behavior predates CI4 and
was left unchanged. The new companion
`test_saved_curved_full_record_replay_is_exact` compares every saved field,
then restores and checks the original payload bytes. Its failures stay red.

## Actual verification

All listed pytest checks used `scripts/run_portable_ci.py`, one worker,
JIT on, 953 MiB numerical-worker limit, 170-second inner timeout and a
180-second supervised process-tree limit. These are focused exact nodes,
**not the complete CI shard matrix**. BLAS/OMP/Numba threads were fixed to one.

| Check | Windows | WSL Linux |
|---|---|---|
| Immutable base, original five, Haswell dispatch | 5 failed | 5 failed |
| Candidate, original five, default dispatch | 5 passed | 5 passed |
| Candidate, original five, Haswell dispatch | 5 failed | 5 failed |
| New complete saved-record test, default dispatch | passed | failed |
| New complete saved-record test, Haswell dispatch | failed | failed |
| Live connected static restart/rollback, explicitly enabled | passed | passed |

Windows Python 3.12.13; WSL Ubuntu-24.04 Python 3.13.12. Both used
NumPy 2.5.4, SciPy 1.18.1, Numba 0.68.0 and pinned local public siblings.
Recorded threadpool metadata verifies SkylakeX versus Haswell dispatch.
Windows and WSL share this workstation's physical CPU; a second physical
CPU was unavailable. Dispatch variation is not a second-hardware result.

Additional Windows checks: 25 reduction/refusal tests, 43 centered-reference,
B3 projection/curved-measure and surface-quadrature checks, 6 B3 potential
checks, and 3 retained-body work/refusal/internal-motion checks passed.
An earlier existing active-solve skip was not counted as coverage; the later
explicitly enabled live restart/rollback checks above passed on both systems.

## Original cases still red under Haswell

1. `test_general_contact_native_active_budget.py::test_budget_policy_checkpoint_identity_and_default_active_fixture_replay`
2. `test_general_contact_native_candidate_reuse.py::test_exact_candidate_reuse_parity_invalidation_and_bounded_storage`
3. `test_general_contact_native_curved_s3_multifacet.py::test_curved_multifacet_extension_preserves_single_facet_restart_identity`
4. `test_general_contact_native_fine_lifecycle.py::test_anchored_fine_policy_staged_lifecycle[opening]`
5. `test_general_contact_native_retained_body_pair.py::test_default_saved_curved_energy_and_identity`

The first two share the plastic fixture replay core. Routed scalar sites
reduced its differing fields from six to two; the curved S3 core likewise
went from six to two. The remaining field is the tangent error and its pair
mirror, containing a matrix spectral norm. For one identical captured plastic
input, the recorded singular value was `0.0152380350953256`, Haswell returned
`0.015238035095325614`, and the existing correctly rounded candidate returned
`0.015238035095325602`. Substituting that candidate therefore cannot preserve
this legacy literal. This demonstrates a specific candidate incompatibility,
not impossibility of every fixed numerical algorithm.

The anchored-open core still differs in a shell moment component by one ulp,
the tangent error and downstream record hashes. Captured inputs already differ
before some remaining reductions. Uncaptured small matrix products/frame work
are suspects, not a demonstrated unique origin.

The retained body-pair path still contains a 36-by-84 spectral norm and a
72-by-72 dense solve. The current deterministic spectral helper supports Gram
dimension at most three; this is a software limitation, not a mathematical
impossibility. Solve inputs also differ, so deterministic factorization alone
would not establish replay. Integration subdivision counts remain different.
Replacing spectral norms with Frobenius bounds would change the contract and
was not done.

WSL default replay of the complete retained record differs only in these
diagnostic fields (physical fields match in the diagnostic comparison):

| Field | Saved | Replayed |
|---|---|---|
| energy_error_j | 1.1056579054093155e-20 | 1.1056579054093008e-20 |
| force_error_n | 9.314512879119906e-16 | 9.314512625873622e-16 |
| tangent_error_n_per_m | 2.0539642086357748e-08 | 2.0539642086364524e-08 |

These differences still fail the complete-record gate; they were not rounded,
filtered or locally re-recorded away. CPU, OS, Python and library-build effects
have not been individually separated for this WSL discrepancy.

## Evidence and disposition

Local evidence: `.development/contact-ci4/receipts/`, original queue
`CI_FAILURES.tsv`, frozen eight-file candidate archive `candidate-source-01`,
runtime pins and the Mistral implementation handoff `CI4_REPLAY_HANDOFF.md`.
The only subsequent helper edit changes its module description, not execution.
Receipt command/source hashes bind the actual tested implementations.

Key receipt prefixes: `windows-base-haswell-02`, `linux-base-haswell-01`,
`ci4-default-node`, `windows-candidate-haswell-01`,
`linux-candidate-haswell-01`, `linux-candidate-default-01`,
`windows-full-record-and-live-default-01`, `windows-full-record-haswell-02`,
`linux-full-record-and-live-default-01`, `linux-full-record-haswell-01`, and
`linux-full-fields-default-01`. Setup failures and sandbox-denied attempts
were retained separately and are not scientific test results.

Measured supervised execution: 1119.456355 seconds over 56 terminal receipts;
largest sampled process-tree RSS: 261705728 bytes (about 249.6 MiB).
This includes diagnostic failures and denied Windows startup, not only passing
tests. WSL launcher denial started no numerical job. No speedup claim is made.

Source review found no changed physical maps or weakened original assertions.
The repair is useful partial integration, **not closure of the five CI failures**.
Full portability remains an implementation/evidence gap. Any further slice
must resolve record-feeding matrix arithmetic and the demonstrated legacy
rounding conflict before claiming exact replay. No push, PR, workflow run,
main merge/rebase or fixture regeneration was performed.

# G3b first M_B2 reference-linear implementation

Status: **DEVELOPMENT_SMOKE_PASSED_NOT_G3B_QUALIFICATION**.
Parent: accepted G3a closeout `ebd3b203e4df72186bd82b2f6d7e6609e18685c6`,
tree `0aefccb6e963ccf0defb4b20d7996e744c199357`.
The frozen G3 contract and M_B2 fixture are unchanged. Main, existing runtime
files, qualified Q4/S3/beam mechanics, default routes and old evidence are
untouched. This branch is additive and private; no merge or release.

## Implemented first slice

`B2TranslationReferenceProblem` captures one fresh native `ElasticElement`
and one explicit legacy `BeamElement` with the registered scalar isotropic
section. The five distinct node IDs include two coincident but unmerged tip
nodes. Each family has its own fixed root and independent rotational DOFs.
Only the three unit-weight translation ties are admitted; no offset arm,
rotational row, shared node, finite-rotation target or adapter is inferred.

The native 42-coordinate reference stationary Hessian is condensed through
its 24 internal coordinates. The legacy contribution is its actual linear
stiffness, never its zero internal-force placeholder. A deterministic rational
translation/support elimination reduces the 30 global DOFs to 15. The
reference quotient must be positive definite. Native internal coordinates
are back-substituted and native station strains/resultants are recovered by
the unchanged cell operator. Legacy recovery uses the existing scalar B2 path.
Recovered native quantities are labeled reference-linear, not finite frames.

The independent test assembles a fresh 54-coordinate full internal/external
system and 15 explicit multiplier rows: 69 total equations. It checks
displacements, multipliers, internal coordinates, reactions, energy, station
recovery, global force/moment balance and tie work against the condensed path.
A native-only torsion moment proves the tied legacy rotation remains free
from an artificial rotational equality.

This is a stateless reference problem, NOT the complete G3b transactional
graph owner. It never initializes or commits native rotations/material state.
Cancellation and repeated independent solves leave no shared history.
Restart deliberately rejects; no new checkpoint schema is introduced.

## Development checks and limits

- M_B2 development: 25 passed in 2.39 seconds; supervised duration
  3.1324987 seconds, peak 231944192 bytes, exit 0, zero active processes.
- Separate unchanged G1 elastic operator regression: 10 passed in 1.79 seconds;
  supervised duration 2.3277259 seconds, peak 199733248 bytes, exit 0,
  zero active processes. This is not a rerun or replacement of accepted G1/G3a
  formal qualification.
- Exact additive extent and frozen parent source/text bindings are tested.
- The independent-assembly test is not an independent implementation review.
- A fresh-directory bounded runner enforces one numerical thread, 600 seconds,
  24 GiB/process tree and 120 seconds without CPU/output progress. It uses the
  preserved process-tree supervisor and never retries automatically.

All development attempts are preserved, including two test-harness failures:
the initial smoke attempted numerical subtraction of a legacy recovery string
label, and an added mutation fixture initially treated FEModel.load_cases as
a dictionary instead of its actual list. Both were corrected in tests before
the final 25-pass run. Neither was a mechanics contradiction; neither failed
output is reclassified. The intermediate 20-pass run is separate evidence.
Per-file hashes, exact source bindings and raw-output locations are recorded
in `reference_cases/ge_beam3_g3b_mb2_development_v1.json`.

## Remaining G3b gate and recommended next step

Extend the same reference-linear comparison to M_B3, M_Q4, M_S3 and
M_Q4_WEIGHTED using the explicit frozen classes and physical normal authority.
Add numbering/reversal/global transport, weighted interface work, the complete
S18 cache/transaction/restart owner, all specified negative admission cases,
and the full independent review/rehearsal/formal two-cycle protocol.
Do not widen this smoke helper silently or claim its rejection tests establish
positive G3c rotational-adapter parity.

**Next:** implement M_B3 alongside M_B2, preserving independent rotations and
the unchanged legacy operators; then add the shell/weighted interfaces before
full G3b ownership/restart confirmation. G3c, G4 and G5 remain separate gates.

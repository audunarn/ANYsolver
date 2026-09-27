# Distributed Q4/S3 restart identity: checkpoint-schema correction

The registered v2 solver execution ran once and completed in 1140.093 s
under its 1200 s cap. The immutable raw report is
`reports/general_contact_d1_distributed_restart_identity_v2_formal_20260927.json`
(SHA256 `ecb35911a65a49d4106266d51de68106d0bc800e901125ff6083608cc4816215`).
The frozen v2 adjudicator verdict is preserved in
`reports/general_contact_d1_distributed_restart_identity_v2_verdict_20260927.json`
(SHA256 `5ce0145c7aaf69b9cf66b64fadbdca048e1bbaefe460b77001b6006a32583e8dc`).
It failed only `checkpoint_contract`; every mechanical, pressure-identity,
runtime, source and wall-time predicate passed.

The registration named `ANYSOLVER_STATIC_RESTART_CONTRACT_V2`, which is the
**analysis contract** schema. The actual checkpoint emitted by
`src/anysolver/nonlinear_restart.py` has payload schema
`ANYSOLVER_NONLINEAR_CHECKPOINT_V2` and version 2. The v2a adjudicator
changes only the expected payload schema, retaining the frozen v2 run,
source, input, pressure identities, thresholds and all other checks. It
writes a distinct verdict and performs no solver execution. The original
failed verdict is not overwritten or reclassified. Independent review is
still required for claim-bearing restart acceptance.

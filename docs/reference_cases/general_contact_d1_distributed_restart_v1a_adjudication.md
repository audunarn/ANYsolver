# Distributed Q4/S3 split restart: path-only adjudicator correction

The registered v1 solver execution completed once in 1138.977 s, inside its
1200 s cap. Its immutable raw report is
`reports/general_contact_d1_distributed_restart_v1_formal_20260927.json`
(SHA256 `7e565d6870586a3f337ba68c2852561d8fc302754c4cb7194977e99985e93d35`).
The first adjudication verdict is retained as
`reports/general_contact_d1_distributed_restart_v1_verdict_20260927.json`
(SHA256 `5240a8e3d1e4423022cedfc722d3551d66a36e987dd77dbc5448821562f6d0a0`).
It failed exactly `reference_identity`: the report records a Windows
backslash path, while the registration records the same relative path with
forward slashes. All thirteen other checks passed.

The v1a adjudicator changes only that comparison to native `Path` equality.
Its source blob is `8662a26809cb59a8a65c3d0ffb778016689f254e`. It will read
the same registered reference and raw restart report, write a distinct v1a
verdict, and perform no solver execution. The v1 failed verdict is not
overwritten or reclassified. Independent review remains required for a
claim-bearing restart disposition.

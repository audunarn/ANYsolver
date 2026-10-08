# ANYfem generalized-material BL5 — 2 October 2026

Consumer `eaed5ec` adds explicit `bl5_material_policy` and strict
`anyfem.experimental-ge-bl5-panel-material-v3`. Existing default v1/v2 records
remain unchanged. The distinct record survives standalone and native Project
round-trip; distributed envelopes accept the material base without arbitrary
nesting. No legacy route or default is relabelled.

Four source checks passed in128.73s;17 installed checks passed in134.17s
(supervised136.319s; peak process-tree208678912 bytes). These cover strict parsing,
owned programme/model identity, both P0/coarse-P1 actual yielding, cancellation,
chart rebase, checkpoint restore and exact signed continuation, plus historical
BL5 formats and Project regressions. One numerical thread, JIT disabled.

Consumer wheel SHA256:
`38aff033edde80435a8f1cb275e9dbab5df4540610f8fce1bfc31796c4c0fbd6`.
Solver wheel SHA256:
`76f18db25d1ad3df88308139bfe8e1593f11ad3f07dfbe9f880bc64b757a5153`.
All98 consumer and398 solver modules match source/wheel/site bytes. Actual imports
and dependencies are recorded. Package versions unchanged.

Root independently inspected the worker diff, preserved file ownership and ran
source/installed checks. No consequential consumer issue found within this slice;
this is not independent mechanical acceptance of the connection/material envelope.
The solver's low-hardening convergence failure and M2/F03 boundary remain open.

`evidence-v1.zip` SHA256:
`93c4534764be974fbf1d6a57774cf839fecfdeb113e0d2f022f6ce1dcff2fe85`.
Contains exact fixtures, runners, safe execution metadata, logs, JUnit, runtime
imports and artifact hashes. Full environments excluded. No publication.

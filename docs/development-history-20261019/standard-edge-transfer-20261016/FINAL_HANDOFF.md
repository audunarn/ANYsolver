# Standard edge beam-shell transfer — completed locally

Implemented: fail-closed weight/offset/reference admission (including nonfinite
weight reduction), revalidation of mutable aliased inputs, unchanged eccentric
MPC equations, corrected COUP-012 label,16 active production-path regression
tests, and standard coupling guide. Parent reviewed the full patch and resolved
R1-R4 with the same Mistral implementation owner. Claude Fable reviewed plan only.

Verification: portable development runner passed178/178 tests across9 affected
modules on Windows Python3.13.9, JIT off, effective BLAS/OpenMP threads1. It covers
kinematics, virtual work, actual-diagnostic force/moment about a common origin,
real AnalysisSession refresh/cold parity and stale-plan refusal, malformed inputs,
linear/quadratic/negative/zero weights, ordering/frame, corner and shared-node
controls. Nine standard COUP cases passed; seven pre-edit case reports have
exactly unchanged numerical fields, corrected COUP-012 title only. Valid-case
evidence reused after rejection-only sum-finiteness repair. No accuracy gain claimed.

Repository licence gate FAILS on pre-existing unchanged metadata:
ANYsolver-results>=2.1,<3 is missing from dependency-licenses.json. This prevents
a repository release-ready claim; no unrelated inventory edits made. Failure and
all earlier debugging/intentional interruptions preserved. No full CI matrix,
installed-wheel qualification, WSL or retired programme runs. No commits/pushes.

The new tests are in default portable merge inventory. Retirement stays effective.
164 unrelated dirty files and protected assembly bytes preserved; HEAD remains
95c335124860a4aec2d7a83f0a628c7d5cfdc6b7. No owned worker/process remains active.

Full exact commands, hashes, counts, measured durations, failure disposition and
runtime settings: FINAL_RECEIPT.json, portable-runtime-preserved/, parent-*-*.json,
HANDOFF-02.md, HANDOFF-04.md and unique attempt directories. Guide:
docs/standard_edge_beam_shell_coupling.md; living plan:
docs/agent_plans/STANDARD_EDGE_BEAM_SHELL_TRANSFER_PLAN_20261016.md.

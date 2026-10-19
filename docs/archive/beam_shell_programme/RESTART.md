# Experimental beam-shell programme: restart capsule

Status: RETIRED, UNQUALIFIED, no active worker or run (16 October 2026).
This is the single programme-history entrypoint retained in this delivery.
Frozen source/tests on main stay in place; old worktree state is archived locally.

## Selection and preserved scientific state

The whole stiffened-shell / GE beam-shell programme, including BL5/F03 and
the nonlinear pilot, is removed from default pytest/portable CI. Standard
coupling, shared beam/shell and general-contact coverage remains active.
`scripts/retired_programme_manifest.json` is the unchanged exact CI inventory:
597 modules plus one node, including checkout-specific paths. Its SHA256 is
`33157ae2fef4441b6dbe1e851f35d52bb38e90bd80727d5e321d2ee73b7ee81e`.
`ANYSOLVER_RUN_RETIRED_PROGRAMME_TESTS=1` changes selection only; it grants no run.

BL5 remains RED; old R4 STOPPED; F03 CLOSED/unmet; paused lifecycle UNRUN.
The nonlinear pilot is SOURCE_REVIEWED_UNEXECUTED: 103 authored tests, zero
executed. Validated quadrature remainder and loaded tangent/stability methods
are absent, so accuracy admission stops. The 2% design target and proposed 5%
feasibility have no measured qualification. The accepted experimental reference
method assumes error halving over four levels and targets 0.5% uncertainty;
it is conditional evidence, not a certified maximum-error bound.

## Frozen source and evidence identities

Original rev8 baseline: `436457c86d1a30b951086aa195748ca590f253e4`.
Canonical later source: branch `codex/rev8-trackA`, commit
`e10a646a1e3888bf3b7e98b5ecbd6741f04263f2` PLUS preserved dirty source,
untracked tests and `.restart-ci/` in the archived `rev8-trackA` checkout.
That commit alone is incomplete; see the local recovery package below.
The earlier binding successor is branch `codex/rev8-binding-portability` at
`e5e823cffbad391a1927217da830cd08d45a2dcf` in archived `rev8-binding-portability`;
original fixtures and failed/provenance evidence remain preserved there.

Read these frozen trackA records in order; older ACTIVE instructions are history:

1. `.restart-ci/ACTIVE.md` and `NONLINEAR_PILOT_RETRY04_HANDOFF_20261015.md`.
2. `NONLINEAR_PILOT_RETRY04_FINAL_REVIEW_DISPOSITION_20261015.md` and
   `nonlinear-pilot-closure-20261015/SCIENTIFIC_ROUTE_ASSESSMENT_20261015.md`.
3. `retirement-20261016/FINAL_RETIREMENT_RECEIPT.json` (source/worktree map).

Pilot package: `.restart-ci/nonlinear-pilot-closure-20261015/`, manifest
`PILOT_CLOSURE_MANIFEST_20261015.json`, frozen SHA256
`6f5d622d72ec9b6d8c278424d252b8f1d348576a602e3af6e41b9b90eaf02d01`.
Source receipt:
`C:/ANYworkspaceWork/rev8-fable-review-20261015/parent-retry04-final-source-receipt-20261015T195741319907Z.json`.
Product digest: `e26fb633f7a794e5dc9765248d6ff28821f7ae546f21ff08ebf1124a71af595e`.
The archived checkout and external receipt/review package are essential inputs;
the summary does not replace uncommitted source or invent missing evidence.

## Local recovery package

Old programme worktrees were removed after byte-verified preservation at
`C:/ANYworkspaceWork/beam-shell-programme-archive-20261016/`. Its `README.md`,
`ARCHIVE_RECEIPT.json` and `CLEANUP_RECEIPT.json` identify the five complete
checkout manifests and original heads, including dirty/untracked/ignored files.
`checkout-blobs.zip` stores deduplicated contents; `programme-history.bundle`
retains complete branch histories. These bulk files stay outside main.
Use `restore_checkout.py rev8-trackA <new-directory>` with a trusted Python
interpreter to reconstruct frozen source/evidence without importing it.
The managed standard integration worktree is separately archived in Codex.
No restoration renews execution authority.

## Later standard-route lessons; no delivered finite-rotation feature

No `rotating_offset_v1` or `work_conjugate_elastic_dev_v1` was implemented.
The standard attachment remains fixed-reference. Full work pairing would use
`p=B.T*f_local`, `K=B.T*K_local*B + sum(f_local[a]*Hessian(d[a]))`, with
`B=derivative(d(u))` including frame motion and beam twist. Spatial moments
require the rotation-vector/spin dual conversion, rather than relabelling
generalized moment covectors.

Astra proved a separate unchanged-frame objectivity obstruction: for a straight
beam with unequal transverse bending stiffnesses and identical small mixed
nodal rotations, superposing a rigid chord-axis rotation changes the extracted
axial-log-projection twist and local elastic energy. Common torsion cancels;
mixed bending energy does not. A force pullback alone cannot repair it. The
unchanged-frame STOP applied; neither later slice ran numerical checks.
Proof and original Mistral checkpoint/correction:
`C:/Github/ANYsolver/.development/work-conjugate-elastic-20261016/`.
Earlier conditional binding analysis:
`C:/Github/ANYsolver/.development/rotating-offset-20261016/`.
These are analytical findings, not measured tolerance failures.

## Restart prerequisites

Begin with source/receipt identity checks, not imports or solver runs. Recover
missing dirty source/evidence before relying on a commit-only reconstruction.
Reconcile original manifests, historical failures, the applicable contract and
unmet quadrature/stability/frame questions with an independent review. Define
one fresh bounded deliverable with prospective criteria and stopping rules.
Source-worker allowance was 2386.835113/2400s consumed; unused or historical
allowances never renew authority. Obtain applicable fresh execution authority
before any programme import/test/run. No automatic retries, qualification,
CI/release claim or resumption is authorized by this capsule.

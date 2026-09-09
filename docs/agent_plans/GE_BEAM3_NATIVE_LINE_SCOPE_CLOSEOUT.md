# Native line-load trial development closeout

Frozen `b7fc905a1131dc07329834abf2f98745438a8e34`, tree
`a5744676464acfeeebf86a79113e3e6b762d90fb`, passes this private development
gate. Four new paths add the load-aware successor, owned live load scope,
tests and plan. Existing code paths, physical kernels, nodal-only adapter,
restart/load-admission guards, qualification records and defaults are unchanged.

## Separate inventories

- Smoke: 3 passed, 11 deselected; supervised wall 8.426 seconds.
- Initial rehearsal: 15 passed, 2 failed; 60.953 seconds.
- Corrected rehearsal: 18 passed; 100.443 seconds.
- Frozen cycle A: 18 passed; 97.424 seconds.
- Frozen cycle B: 18 passed; 96.216 seconds.

All 15 scientific JSON packets are byte-identical between the frozen cycles.
Every child completed under one numerical thread, 24 GiB, 600-second wall and
120-second CPU-inactivity limits, with zero active children at exit. Two frozen
children ran concurrently; no automatic process retry occurred. Exact clean-head
and configured-runtime guards passed before/after both runs, but do not establish
complete dependency-graph qualification. Times are diagnostics, not speed claims.

The failed rehearsal exposed test lifecycle mistakes: querying an expired token
and reading a trial-backed payload after discard. Tests now check has_active_trial
and capture owned values before advancing/discarding tokens. The new wrapper's
exception path uses the same active predicate, avoiding a secondary token error.
A deliberate post-assembly load-authority mutation proves scope reset, trial
discard and unchanged committed material/rotation history. Failure evidence remains.

## Load work, tangent and authority

The real native nonlinear assembler and state transactions now evaluate a
load-aware private element under an owned effective reference-line pattern.
The preserved line potential includes work on physical internal cell rotations.
Local equilibrium and replay subtract that complete potential; the returned
internal residual adds back its nodal force part, which is assembled exactly once
as external load. The consistent load-aware Schur tangent is retained. No nodal
lumping, new coefficient, finite-difference frame or material-law change is used.

Independent load-only reconstruction uses Q2 nodal polynomials, reference
arclength and explicit cross-product first/second variations. It does not call
the producer load potential, lift or Jet2 helpers. The largest full/condensed
load-identity error is 4.285460875053104e-14 against 1e-11; the largest directional
tangent error is 8.99639130733773e-11 against 1e-7. This is not an independent
oracle or review of the complete beam formulation.

Straight elastic, curved elastic and curved plastic imposed-state cases pass.
Curved cases retain nonzero internal load work. Zero-line residual/tangent and
response are byte-identical to the preserved nodal-only adapter. A separate
read-only audit also matches the exact response in historical frozen f5bc443's
curved-plastic packet, whose archived size/hash is bound in the new status.

Each accepted state contains its line pattern and local-load input hash, with
fixed material origins and exact local replay. Trial issuance is tied to the
live material context and store-specific validator; a locally valid response
for another load trial cannot be staged or committed. Distinct registrations
cannot share live load authority even for byte-identical physical states.
Missing scope, resealed force/signature/provenance/potential mutations, changed
patterns and shell-pressure fallback are rejected. Changing load and discarding
the trial preserves committed histories.

## Preservation and next implementation

The manifest/status bind 81 data files plus the manifest copy at
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-native-line-scope-b7fc905-20260907`.
All byte counts and SHA-256 hashes are verified, including four frozen source
copies, two exact runner commands, every separate inventory and the failed
rehearsal. Original temporary runs remain; only the verified transfer duplicate
may be removed.

This layer exposes a private actual-assembly operation, not yet the global
Newton line-load controller. Next bind effective proportional/constant/staged
patterns at every real solver evaluation, including line search and reaction
evaluation. Keep internal line work in local stationarity and count nodal work
once. Then extend typed checkpoint chains and recovery for the load-aware
candidate, checking continuation/unloading against full retained-system paths.

Nodal-couple work/tangents, general section and analysis parity, physical mass,
modal/prestress/buckling qualification, packaging/performance, independent review
and the objective beam-shell connection remain open. Review is PENDING. No
production selector, full workflow qualification, release, merge, push, default
change or overall goal completion is claimed.

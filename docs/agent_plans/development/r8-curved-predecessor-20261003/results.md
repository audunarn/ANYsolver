# Curved point material predecessor recovery — 3 October 2026

**IMPLEMENTED_NOT_QUALIFIED.** Solver parent `2cef442c`; captured candidate changes
in `raw.zip`. Consumer product code `85ed953`, documentation `3819b23`. No aggregate
gate closes. Formal F03 remains unconsumed; no push, main merge or publication.

## Decision and delivered behavior

The previous curved material snapshot stored the accepted Markov state, so it
could continue but could not reconstruct last-increment generalized station work.
The existing binary codec now has distinct curved point material/coupled kinds,
with their anchored variants. These carry accepted and preceding native beam
states and, for shell J2, accepted and preceding layer states. Layouts come from
the compiled model, with existing byte, finite-state and resource bounds.

Restoration evaluates the endpoint from the saved predecessors and checks the
result against accepted material arrays before atomic publication. Cached detailed
station records now report actual strains, resultants, frames, plastic increment,
stored endpoint energy and incremental dissipation. Recovery does not evaluate
constitutive mechanics or assembly. The existing native formatter and BL5
predecessor mechanisms are reused; element equations, tolerances, defaults,
globalization and package versions are unchanged.

Older snapshots preserve decoding/re-encoding and accepted-path semantics. Their
unknown last-increment records remain empty. A subsequent accepted increment
supplies its known predecessor and upgrades to the new kind. No zero dissipation
is invented for old history. Byte integrity and mechanical validation still do
not authenticate an arbitrary loading path; independent replay remains distinct.

## Verification and identities

**27 focused installed checks passed**, covering:

- Tilted material covariance and active/unloading/reverse derivatives.
- Simultaneous yielding, unload/reload, exact station recovery and continued
  checkpoints, cancellation and rebase invariance.
- Native endpoint station-update/work comparison, nonnegative positive plastic
  dissipation, detached cached recovery with evaluation forbidden.
- Four altered predecessor arrays with recomputed valid digests, rejected before
  acceptance; policy/material mismatch rejection.
- Legacy snapshot truthfulness and automatic upgrade after new acceptance.
- Restored residual and last-increment tangent parity within 1e-10.
- Elastic-shell/generalized-beam schema and cached formatter negatives.
- Existing generic Q4 material restart and BL5 material/scale isolation controls.

These native evaluation and parity oracles share implementation; they do not
replace independent mechanics or executed external reference acceptance.

Solver wheel SHA256:
`cdc4c4e8dc427dd03a5a61b4fe82caa2a13f46b641ad775e1a59eecb0dcf3db2`.
All 413 source/wheel/installed modules match. Supervised route 119.414 s,
191725568 sampled peak process-tree bytes.

Unchanged consumer wheel SHA256:
`6435122e6aded71bcaa3b16a535c23efc15889367f85aa4810c77256d07e2b10`.
All 98 consumer and 413 solver installed modules match current product source.
Two paired installed checks passed: strict input rejection and actual native
Project save/reopen with simultaneous yielding, exact restored detailed station
records, unload/reload and continuation. Route 31.230 s, 198090752 bytes.

Runtime checks verify actual installed import paths, native/Numba one-thread
settings and JIT disabled. Each supervised job used 600 s/1 GiB limits, serially.
These costs are not a performance qualification or speedup claim.

## Review, retained failure and boundary

Integration-owner review checked schema/profile binding, exact compiled shapes,
old-format preservation, prospective checkpoint publication, accepted-predecessor
ownership, anchored rebase and absence of history replay. The first new station
test failed because it referred to a nonexistent owner coordinate attribute; it
was corrected to the native driver's actual reference coordinates. Its process
log remains failed evidence. Source v1 and corrected v3 passed; v2 had six passing
negative/legacy cases and the failed test helper. Independent cross-family
scientific review remains outstanding; this is development verification.

The larger fixed-step reload budget from the previous slice is unchanged, and
its earlier twelve-backtrack failures remain protected. No new material family,
attachment, control, external load, spectral or capacity capability is admitted.
The full practical elastoplastic workload and required external agreement remain
unfinished. Generalized station fields are not physical fibre stresses or
cumulative dissipated energy.

Archive SHA256:
`c944c5d3001392cbea41c0e2d1996fbf93e366ab42be2faea0163c2e0d15b7c3`.
The archive contains fresh candidate/fixture/runner source, wheel, logs, raw
results and whitelisted execution metadata; no complete environment maps.

Next: coherently construct a **virgin material** curved reference through the
existing imperfection operation, keeping it separate from transporting a loaded
material state. Then verify its zero initial material/gap state and native consumer
history. Broader attachment, fibre, curved S3, external, scale and acceptance
requirements stay open.

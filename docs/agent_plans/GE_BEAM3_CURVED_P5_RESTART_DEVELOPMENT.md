# P5 nonlinear research restart checkpoint — 2026-09-06

Successor to `90bd119234af4c31d205ec66058745fb036c3cb5`, tree
`8e1d9f647a5475497fcb76d9f77e8ccf7c9e898b`.
This completes the unfinished research codec preserved across the restart.
It does not change production serialization or confer qualification authority.

## Scope and identity

`GE_BEAM3_P5_RESEARCH_HISTORY_RESTART_V1` is restricted to the existing
one-macro, first-vertex-clamped research driver with the directed-hardening
section law. Geometry, reference triads, section, integration order and
station ordering must match caller-supplied expectations. The record includes
candidate identity, explicit `production_qualified=false`, spatial matrix
update convention, Python/NumPy/platform identity and hashes of the eight
listed geometry, AD and research implementation modules.

The codec persists committed geometry, rotations, loads and all station
histories together with the last accepted trial and its original histories.
It never substitutes the newly committed histories as the replay origin.
No payload-selected imports, classes or executable expressions are used.

Digests provide integrity and identity checks, not authenticity, a complete
historical load transcript, a complete external dependency graph or a proof
that the runtime was not modified in memory. Recorded iteration counts are
bounded diagnostics; their past execution cannot be reconstructed from the
checkpoint. This is not a hostile-code isolation boundary.

## Validation and publication

The parser requires canonical ASCII JSON, exact keys and scalar types, finite
values, exact array shapes, at most 1 MiB and at most 32 nesting levels.
Duplicate keys, extra whitespace, BOM, nonfinite constants, float overflow,
scalar coercion and unregistered fields are rejected. Payload and expected
identity checks precede mechanical response reconstruction.

Import allocates a fresh model. Initial checkpoints must exactly reproduce
the zero-history reference state. Accepted checkpoints must reproduce their
complete station response and condensed residual/tangent from the original
histories, local rotations and moments in a single functional evaluation.
No Newton solve runs during restore. Epoch linkage, committed/accepted
geometry and loads, material histories, local stability, equilibrium and
clamp identity are checked before publishing the new in-memory model.

Export refuses pending trials and applies the same import validation to its
own bytes. `write_exclusive` stages a complete, flushed and fsynced file in
the target directory, then creates the target through an exclusive hard link.
An existing target is not overwritten. Unsupported hard-link publication
fails closed; normal failure cleanup removes only the uniquely created
staging file. Power-loss durability of directory metadata is not claimed.
Abrupt process death can leave a staging file; it is not canonical evidence.
There is no general filesystem/reparse-point admission or production file
reader API in this probe.

## Verification

- New restart suite: **50 passed in 8.87 seconds**.
- Existing sixteen P5 suites: **241 passed in 25.70 seconds**.
- A 16-station plastic checkpoint is 34,884 bytes in the inspected runtime.
  Export/import/export is byte-identical, including in a fresh Python process.
- Starting after amplitude 0.1, restored and uninterrupted drivers produce
  identical trial digests, committed states, accepted-origin responses and
  checkpoint bytes for amplitudes 0.2, 0.1, 0, -0.1 and 0. The force pattern
  and material law are those of the preceding history-path development record.
- The default 48-station plastic checkpoint separately round-trips exactly.
- Mutation checks cover schema/types/counts, epochs, coordinates, frames,
  loads, original/committed histories, moments, local rotations, station
  identity, strains, resultants, residuals, tangent, convergence, hashes,
  implementation/runtime identity and candidate identity. Semantic mutations
  remain rejected after the enclosing payload hash is recomputed.
- Existing-model state is unchanged after rejected import. Pending export
  fails without advancing state. Tests disable Newton during import/replay.
- Exclusive publication, attempted overwrite and injected publication failure
  are checked in disposable directories; failure creates no target or partial
  canonical output.
- An earlier 48-test pass reported a pytest shutdown cleanup permission warning
  for the shared `pytest-current` directory. The final 50-test run used a fresh
  UUID-named external base directory and completed without that warning.

Implementation SHA-256:
`79EDA20ED58221B0862AD7834AA18851DC0069C25B1524766D1540CA66017329`.
Test SHA-256:
`12CAEE464DFA54654ABD172CFD8433DCAEAE7F6343BD4338CA4B002287FEE975`.
These identify inspected working-file bytes, not a self-referential commit.

## Transfer and remaining work

Continue on `codex/ge-beam3-curved-p5-objective-lift-v1` in
`C:\Github\ANYsolver\.perf2-worktrees\ge-beam3-curved-p5-objective-lift-v1`.
This turn adds exactly this record, the restart probe and its test. No formal
resource request, external qualification cycle, candidate freeze, independent
review, push, merge, release or activation was performed.

This remains same-author research sharing the geometry and AD kernel. It is
not an installed-wheel, production restart, cross-runtime migration or general
nonlinear material qualification. The accepted P3/P4 evidence and all earlier
P5 failure/limitation records remain unchanged. Existing B2/B3/Q4/S3 mechanics,
production recovery, defaults, package metadata, dependencies and workflows
are unchanged.

Next development should address multi-element finite-state transactions and
continuation, with separately defined bounded cases. General nonlinear section
adapters, independent engineering references, nonlinear quadrature, the
extreme coupled local failure, finite prestress/buckling/postbuckling, dynamic
integration, curved/slender domain qualification and objective eccentric/
curved beam-shell connections remain unresolved. Do not infer formal authority
or full beam parity from these restart checks. The full development objective
remains incomplete. `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

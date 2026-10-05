# F06 beam accepted-chart foundation, development v5

This separate prototype uses the existing curved S3 two-step loaded prefix
and v4 shell owner. F06/G0B remain open. Frozen v4 sources, tests and evidence
are unchanged.

**Decision question.** Can an owner-held accepted snapshot bind native B3
nodal and retained-cell chart anchors to the physical beam state, issue one
atomic shell-plus-beam rebase, restore it directly, and carry those anchors
through the existing loaded cursor-three continuation?

Competing explanations for failure are an Exp/Log reconstruction error, a
checkpoint lineage/encoding defect, or a change in the coupled mechanics when
the stored beam coordinates are used. One bounded discriminator checks
the rebase snapshot, direct restore, loaded successor, exact v4 accepted-state
identity, and rejection of rehashed altered beam anchors and lineage. It uses the existing
S3 fixture only, one BLAS thread, disabled Numba JIT, and no external solver.
Passing this development check permits an owner integration design. It does
not establish that the production retained-beam owner solves in these charts,
nor Q4, repeated rebases, noncommuting large rotations, cutback or F06/G0B
scientific acceptance. No frozen execution authority is consumed.

## Bounded result

At integration worktree HEAD `d1e1c14e`, source SHA-256
`0ca627627664e3abb34444966915b6a5726d9de5ac23072c9f90f34dd47d55c3`
and focused test SHA-256
`227b73f602c71eb4b1903a0e9d65f40f688ec3d7a65b54ee32d4e526e8765424`,
the single S3 test passed (`1/1`, 11.53 s) with `NUMBA_DISABLE_JIT=1`,
`OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1` and
`PYTHONPATH=src;.`. The command was
`python -m pytest tests/test_b3_e4_f06_beam_chart_v5.py -q --disable-warnings --maxfail=1`.

The first disposable attempt failed before its mechanics checks because SciPy's
rotation conversion needed a writable coordinate array. The source was
corrected; the successful run used the hashes above. The accepted cursor-two
state stores zero beam nodal and cell coordinates against its own physical
frames. Direct restore retains that state. The loaded cursor-three successor
has nonzero nodal and cell coordinates against the unchanged accepted anchors;
direct restore reproduces it. Both rehashed semantic corruptions are rejected
without advancing the owner head, and a stale continuation is rejected.

**Decision:** this establishes the bounded accepted-state/restart foundation
for the S3 fixture. The native B3 solve and joint currently still operate on
physical frame matrices; they do not consume the stored chart coordinates in
their residual and tangent. Production owner integration with chart pullback
and its independent mechanics review is the next substantive F06 gap. This
development test does not upgrade F06 or G0B status.

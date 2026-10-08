# F03-K1 preexecution independent review

21 September 2026. The independent F03 mechanics auditor read the K1
design, rank probe, single-use runner and external supervisor without
executing a candidate. The audit checked the five basis definitions,
26-mesh and 130-candidate inventory, K0 physical source and quadrature
reuse, mass-whitened row rank and work-scaled trace rank, resource bounds,
exact record grammar and diagnostic-only completion semantics.

The auditor identified a panel geometry error: with `N_s=1`, the physical
shell x-grid has an interior edge at `s=.5`; the shell-grid multipliers
therefore have two intervals/three nodes. The basis now clips the actual
panel grid to `[0,1]`, and an import-only stub check confirmed its knots.
The review also found that a zero/nonfinite quadrature reference should
invalidate a candidate instead of aborting the entire inventory, and that
reference gaps should retain K0's `1e-12` limit. Those issues were corrected
with a narrowly matched `ValueError` and the original limit. Row rank now
compares with declared row count. A subsequent narrow correction explicitly
classifies nonfinite multiplier mass and inconsistent trace/row ranks; these
branches were not observed or executed in a scientific candidate.

Both runner and supervisor imported successfully in a non-executing smoke
check, and all three K1 scripts passed syntax parsing. The auditor found no
remaining preexecution source blocker within this bounded review. This is
not an independent review of future numerical results or an acceptance of
the full line law. Commit and bind the exact corrected source before the
one-shot run.

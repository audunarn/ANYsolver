# Native mixed reference-modal development handoff

State: verified against the assigned focused source criteria by impact reuse;
76 unique instances covered (V1 73 pass plus V3 three affected pass). Independent
review, installed-artifact evidence and final scientific acceptance remain open.
No qualification, installed-artifact or release claim is established here.

## Outcome and contracts

The extension uses the unchanged public factory and `owner.modes` operation,
with distinct `GEMixedReferenceModesRequest` and `GEMixedReferenceModesResult`.
Legacy request, capabilities, Q4 mass bytes and legacy free boundary retain
their existing meanings. The explicitly adopted new free boundary is
`GE_MIXED_FREE_FREE_MODAL_ONLY_V1`, POINT-only and modal-only; legacy requests
on that boundary deliberately refuse even Q4/generalized models.

Root adopted the S3 linear nodal director kinetic approximation for the actual
direct18 V2D stiffness owner. This does not reproduce MIN3 displacement/shear
enrichment kinetics or legacy S3 lumped mass. Other S3 bubble families refuse.
Supported flat Q4/S3/mixed shell and generalized/virgin axial/biaxial physical
fibre POINT/BL5 paths retain actual compiled stiffness and constraint rows.
Material BL5 and shell J2 remain refused. BL5 topology linking does not assert
six-pose coupling; the original single-P0 mechanism refusal is preserved.

Native mass uses explicit definition 6x6 spatial inertia and the centered
reference kinetic lift/order24 in authoritative first24 incidences. Algebraic
nodal rotation traces, retained18 resultants, normal shell spin and multipliers
stay exactly massless. The full singular descriptor solver is reused. No
stiffness surrogate, reduction, averaging, penalty, mass floor or tolerances
were introduced or relaxed.

## Owned changes

- `src/anysolver/_stiffened_shell_ge_reference_modal.py`: typed request/result,
  admission, distinct policies/capabilities/cache and existing-solver dispatch.
- `src/anysolver/_stiffened_shell_ge_experimental.py`: modal-only new boundary,
  separate cache and capability seam only.
- `src/anysolver/stiffened_shell.py`: public exports.
- New `src/anysolver/_stiffened_shell_physical_s3_mass.py`.
- New `src/anysolver/_stiffened_shell_ge_mixed_modal_mass.py`.
- New `tests/test_stiffened_shell_ge_mixed_reference_modal.py`.
- New `tests/test_stiffened_shell_physical_s3_mass.py`.
- New `examples/stiffened_shell_ge_mixed_reference_modes.py`.
- New `docs/reference_cases/stiffened_shell_ge_mixed_reference_modal.md`.
- New raw evidence files in this directory only. Root owns execution launcher
  and independent contract report, not authored by implementation worker.

## Verification actually completed before numerical run

Nine owned Python files parsed by stdlib AST; final boundary/test/entry delta
also parsed after freeze. No numerical process was launched by this worker.
Root authorized and launched exactly `C:/Python/Python314/python.exe` with
`ci-entry-v1.py` under its bounded supervisor (600s, sampled 2GiB process tree,
affinity0, pools1, JIT disabled, unforced backend). Root holds the single slot.

The entry binds exact source/test snapshots, imports and versions, actual
Numba threads, native threadpools, affinity and environment. The four-file suite
includes unchanged legacy GE reference-modal and physical Q4 mass controls.
`effective-runtime-v1.json`, source snapshots, full stdout/stderr, JUnit and
root supervisor result are the authoritative evidence for this run; this
checkpoint does not claim their pending result.

Source-ready/frozen notification preceded root launch. No product/test/entry
edits are authorized during that job. Focused repair belongs to the same owner
after concrete findings and a separately allocated numerical slot, preserving
the original failure and bounds.

## Preserved limitations and authority

Experimental nearest-shift pairs are not a complete lowest spectrum. The
final 2% spectral convergence/reference acceptance and other programme gates
remain required and unexecuted. No F03 formal driver, closed campaign, body
workflow retry or modal-canary was launched/read by this worker. No commits,
branch/history/config changes, sibling edits or Git publication were made.
Sandbox status reported ACL false deletions; root's host Git inspection
established a clean baseline and no restore/discard was performed.

## V1 result and V2 focused repair

Root reports V1 terminal status: 73 passed / 3 failed, 76 instances in 8.47s.
The supervisor observed 13.010s and 232493056 bytes. V1 failure output, JUnit,
runtime and source snapshots remain immutable. Two failures were unscaled dense
QZ oracle comparisons (relative discrepancies about 2.6e-8 and 1.7e-5 at the
unchanged 1e-8 criterion); the third oracle supplied identity nodal frames to a
curved reference that correctly refused tangent misalignment. These three are
failed/inconclusive V1 verification evidence, not passes.

Root adopted a test-only repair: exact binary scalar normalization of B's units,
followed by 12 bounded power-of-two congruence sweeps on the complete A/B pencil.
All unknowns, algebraic variables, zero mass and infinite spectrum are retained;
original physical A/B stay unchanged. QZ values map back by `lambda=beta*mu`,
vectors by `x=S*y`. Finite-positive scales, nonzero-pattern preservation and
mapped original physical equation/constraint backward residuals are checked at
the existing 1e-8/1e-9 budgets. Comparison tolerance stays 1e-8. Curved triads
now derive their first axis from the actual quadratic tangent and complete a
proper right-oriented frame; independent direct quadratic-lift work is unchanged.

Only those two test functions changed; product source is identical to V1.
The 73 passing V1 instances remain applicable to unchanged code and cases.
New `ci-entry-v2.py` selects exactly the two QZ parameter instances and one
curved kinetic oracle. Versioned runtime, snapshots, temporary files and JUnit
preserve V1. V2 entry and repaired tests passed stdlib AST before freeze.

V2 did not execute pytest. Root reports that a broad suffix replacement in its
launcher changed the fixed dependency directory to a nonexistent path. The
entry correctly caught global NumPy 2.4.6 instead of the required isolated
2.5.3. Startup evidence is preserved (1.90966s, 156971008 bytes); this is a root
orchestration error, not numerical or product evidence. No tests passed in V2.

`ci-entry-v3.py` changes only the four exact output names (runtime, snapshot,
pytest temporary directory, JUnit) from V2 to V3. The original pinned CI site
directory ending `20261005-v1/ci-site-network-v2` stays unchanged. Test and
product bytes remain identical to the V2 candidate; exactly the same three
affected instances are selected. V3 entry passed stdlib AST before freeze.

V3 terminal result was inspected by this worker: JUnit three tests, zero errors,
failures or skips, 1.801s test time; stdout records 73 deselected. Root supervisor
reported child31272, 5.4632715s and 228888576 bytes. Combined with the applicable
73 unchanged V1 passing instances, this covers 76 unique instances by impact
reuse; it is not a clean rerun of all 76. V1's three original failures and V2's
zero-test startup failure remain retained.

Actual V3 runtime was inspected: `C:/Python/Python314/python.exe`, isolated
NumPy2.5.3, SciPy1.18.1, Numba0.68.0 and llvmlite0.50.0 from the exact pinned
`r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2` directory.
ANYsolver imported from this checkout's `src/anysolver/__init__.py`. Affinity
was exactly `[0]`, JIT disabled, Numba threads1, both NumPy/SciPy OpenBLAS pools1
and no forced backend. All current source/test bindings match V3 runtime hashes.

The example definition is exercised through the public owner in the source
suite. Its CLI/workflow is not separately executed, so there is no standalone
example execution claim. No worker-owned process exists and no new numerical
job was launched. Root's independent source/evidence review is pending, as are
installed-artifact and scientific programme gates; this handoff waives none.

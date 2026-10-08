# B2 loaded interior point workflow — 3 October 2026

**Delivered:** the explicit `B2_FIXED_END_LOADED_POINT_TRACE_V1_DEV` policy
couples the existing physical B2 member's actual loaded interior pose to Q4
point attachments. The existing facade, selected batches and ANYfem experimental
input round-trip work. This is implemented and tested, not programme qualification.

Solver source `af7876710ad0952050c8a03ad988a5601cda668b`; ANYfem source
`2ede338ba28932bb9dd3e8eb0f0a4908d37fc765`. The initial owner was `4bc228c8`.
Defaults, historical identities and package versions remain unchanged.

## Mechanical and lifecycle change

The sparse reference KKT includes the member-local Green compliance:

```text
[[T.T K T, (C T).T], [C T, -H]]
rhs = [T.T(F - K u0), -C u0 - a_body]
gap = C u + a_body - H lambda
```

All same-member cross-blocks, eccentric port work and reference-frame transforms
are included. No extra interface equivalent nodal load is added to the first
row; it already contains `C.T lambda`. Endpoint Green response is zero. The
complete KKT, rather than the legacy C-only rank test, governs new-policy
admission. Sparse global storage retains locally bounded member maps.

Raw vectors remain nodal loads. Only an owner-bound `B2ReferenceBodyLoad`
represents distributed acceleration. Selected output contains actual loaded
member poses and section resultants. `loaded_strain_energy` includes fixed-end
bubble and cross-work; historical `internal_strain_energy` keeps its nodal
homogeneous meaning. Owned compiled maps and one eligible factor are reused;
closed owners release them. Complete-case cancellation preserves finished cases.

Footprints, mixed/S3 owners and loaded spectral requests reject this initial
policy. The section factory remains SI. Numeric unit-covariance tests do not
establish an additional public unit-system API.

## Executed verification

- Final isolated solver/ANYfem wheels: **188 checks pass in 22.02 s**;
  supervised route 24.404 s, sampled process-tree peak 210,726,912 bytes.
- Exact source/wheel/site verification covers **417 solver and 98 ANYfem modules**.
- ANYfem source checks: 97 pass. The solver's focused final controls include
  an independently integrated initial-resultant BVP, two same-member points,
  all cross-work, rotated frames, offsets, prescribed motion, raw/body distinction,
  complete work/strain energy, ownership, unit covariance and 1/10/100 batches.
- Installed physical steel example completes **10 cases with one factorization**.
  Last selected displacement is `(-8.63922812965488e-17, -0.005972509894100471)` m;
  maximum point gap `2.5478751053409354e-18`; last loaded energy
  `8.16418751743641` J. Experimental ANYfem round-trip reproduces results exactly.
- Python 3.14, NumPy 2.4.6, SciPy 1.17.1, Numba 0.65.1, pytest 9.0.3.
  Actual BLAS/OpenMP/Numba pools are one; JIT disabled. Checks used 600 s/1 GiB
  limits without exceeding them. Process-tree thread count is not numerical
  pool count.

The final solver wheel SHA256 is
`abc24bde60db8c10ddd4d14c2f1e423821562f79bc9eb43b57b5f18ecf294ac6`;
ANYfem wheel SHA256
`ba96a6969136389be29c875742d8a9135259ea7623057bfaf635a53c8615cc9a`.
ANYmaterial was imported from **editable source**, commit
`d8a233ef4c5e38d25dbba0eb20e6cfa8d44ec5a2`; its 13 module hashes and unrelated
dirty documentation are recorded in [dependency binding](editable-material-binding.json).
This is not full installed dependency-graph or cross-platform G6 acceptance.

## Failed evidence and corrections

1. First source run: 12 failed/77 passed. Analytically zero H entries stored in
   sparse matrices confused the pattern/underflow guard. Only exact zeros are now
   canonicalized; no nonzero loss guard was weakened.
2. Next focused run: 1 failed/14 passed. The numeric unit fixture's floating
   mass congruence was nonsymmetric. Symmetric physical entrywise congruence
   repaired the fixture; subsequent unit and full-work controls pass.
3. First installed attempt: two collection errors from an omitted named
   imported graph fixture. The safe helper was explicitly added; it did not
   execute formal F03. The initial installed candidate then passed 186 checks.
4. Public example initially constructed the mixed-owner definition returned by
   an existing Q4 fixture. It now explicitly constructs the admitted Q4 definition.
5. The repaired example then failed conservative mixed-load resolution. The
   offending stored row contains a real **15.4017 Nm** action, not quadrature
   noise. A model-wide roundoff estimate exceeds the unchanged per-row allowance,
   while the existing exact-product stored-row residual certificate passes.
   The certificate is now eligible for this explicit new policy, still only with
   zero prescribed offsets and unique unit-selector supports. Uncertified/lost
   controls fail. It does not establish forward displacement accuracy, assembly
   accuracy or resolution of arbitrarily tiny superposed parts of one load row.
6. One new test wrongly expected the unchanged default steel fixture to fail;
   actual default completion was preserved and the test corrected. The separate
   historical endpoint mixed-load boundary remains open.

All meaningful failures, affected snapshots and corrected results are retained.
No load, support, scientific tolerance or physical acceptance criterion was tuned.

## Evidence, review and remaining scope

[Raw manifest](raw-v1.json) binds the explicit safe archive (`raw-v1.zip`),
failed source snapshots, selected fixtures, wheels, commands, effective settings,
resource records and numerical outputs. It includes no historical canary/history
sweep. [Independent development review](review.md) records the missing work control
and consumer finding, both repaired. No reviewer numerical jobs were launched.

M3 remains incomplete: broader attachment/formulation coverage, external physical
comparisons, required mass/prestress/spectral, practical scale and final consumer/
artifact obligations remain. M2 and aggregate G0–G6 remain open; formal F03 remains
UNCONSUMED. No push, main merge or publication. The full Revision8 goal stays active.

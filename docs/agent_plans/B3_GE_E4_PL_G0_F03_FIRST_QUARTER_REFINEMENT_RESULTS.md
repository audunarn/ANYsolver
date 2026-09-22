# F03 first-quarter natural refinement: bounded diagnostic result

22 September 2026. **DIAGNOSTIC_ACCEPTED_G0B_OPEN.** This is a classical
planar Q4/CST-CB comparator, not a native B3-GE/E4-PL line-law qualification,
external physical reference, or production selection. The previous adverse
Ny64 draft 1% physical-reference screen remains adverse. F03 and G0B remain
open, and G1 product integration remains barred.

## Frozen execution and evidence

- Source worktree: `codex/b3-ge-e4-pl-integration`, execution commit
  `7970243915a62809567d39c500b30b4c47f2cef8` (clean for every case).
- Authoritative registration:
  `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-quarter-refinement-registration-v1/registration.json`,
  SHA-256 `91de602901a98b8b354aa4ea96e31aac1bc3108d227f29dd74bedb6a52d397e9`.
  The independent registration review is `independent-review-v4.json` in
  that directory, SHA-256
  `ab7630fbae8a0be3d69a18fecd5851dca94e1f445169b16c1499701da44ab93b`.
- The source-frozen 59-test preflight passed at
  `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-quarter-preflight-v3/`.
  Its receipt/log are pinned by the registration. The separate v1/v2
  preflights and their three fixture-setup errors each remain preserved;
  sandbox denial of temporary-directory creation/removal caused those
  errors. They did not consume any of the fourteen scientific case roots.
- Fourteen serial, single-use Q4/CST-CB natural cases covered seven
  `(Ns,Ny,Nm)` triples, with `Nb=512`, P1, one BLAS thread, 8 GiB and 900 s
  per case. Every supervised root completed and received a separate
  six-raw-file, source/dependency-bound reconstruction receipt. There were
  no failed or retried scientific cases.
- The mandatory six-case historical parity passed exactly on 23 signed
  physical channels and both G2/Gmotion gaps:
  `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-quarter-refinement-parity-v1/parity.json`,
  SHA-256 `d6aef4e25436ced2ea85313f41badcdfb40ab5ca42b64bd6b3da658adbaa7ee3`.
  Historical manifest, phases and result files were pinned before the
  comparison. This is reproducibility of earlier natural controls, not
  independent physical agreement.
- The full signed reconstruction and three-axis sweeps are in
  `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-quarter-refinement-adjudication-v1/adjudication.json`,
  SHA-256 `93aceaf4e8d1a21177f454ba93ab12b2426b72e8eb96eb1beb4bcbd485c2d652`.
  It recorded `DIAGNOSTIC_ACCEPTED_G0B_OPEN`, fourteen entries/receipts,
  force/constraint/balance/work checks, signed support/port/elastic terms,
  physical first-quarter bands, and branchwise crossing derivatives.
- Independent read-only mechanics interpretation:
  `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-quarter-refinement-mechanics-review-v1/review.json`,
  SHA-256 `2ec06b602c71b6fc058b232f54c4a388a7c647970cace468481f09ffc0f42901`.
  It checked all nine matched contrasts and found no basis for a
  convergence or causal trace claim.

## Signed physical response

The entries below are left-support vertical force in N. Pair difference is
CST-CB minus Q4; mesh refinement changes must be read within each natural
topology, rather than treating their difference as a physical error.

| Sweep | Mesh `(Ns,Ny,Nm)` | Q4 | CST-CB | Pair difference |
|---|---:|---:|---:|---:|
| Transverse | 128,16,64 | 95,267.736 | 99,767.377 | +4,499.641 |
| Transverse | 128,32,64 | 81,105.729 | 83,277.491 | +2,171.762 |
| Shared fine | 128,64,64 | 67,411.428 | 68,554.545 | +1,143.118 |
| Longitudinal | 32,64,64 | 98,847.012 | 100,988.718 | +2,141.706 |
| Longitudinal | 64,64,64 | 75,872.534 | 75,957.136 | +84.602 |
| Multiplier | 128,64,16 | 15,932.482 | 16,242.870 | +310.388 |
| Multiplier | 128,64,32 | 51,890.565 | 52,708.412 | +817.847 |

The Q4 fine-step changes are `−13,694.301 N` for Ny32→64,
`−8,461.106 N` for Ns64→128, and `+15,520.863 N` for Nm32→64. Thus
neither longitudinal nor multiplier refinement is saturated at the
registered finest levels. The longitudinal pair contrast is nonmonotone
(`+2,141.706`, `+84.602`, `+1,143.118 N`), so its small middle value
cannot establish convergence. Three levels do not establish an asymptotic
order.

At the shared fine mesh, the beam-root moment contrast is
`−499.758 N m`: `−455.653 N m` elastic and `−44.105 N m` direct port.
The direct-port vertical force contrast is `−2,192.255 N`, whereas its
elastic root term changes by `+550.512 N`; the left-support force changes
by `+1,143.118 N`. The first-quarter port vertical force changes by
`−1,677.531 N`. The first physical `1/32` band carries about `−580 kN`
in either topology, but its matched difference is only `+158.583 N`;
the next band differs by about `−1,085.5 N`. A local port magnitude is
not the explanation for the full global reaction difference.

The checkerboard diagonal crossing calculation evaluates 32/64/128
interior crossings for Ns32/64/128, respectively, in the first quarter.
It reports zero skipped endpoints in these meshes. At `(128,64,64)`,
the CST-CB branchwise slope-jump norm has median about `3.08e−6 m` and
maximum `1.48492e−4 m` per unit normalized material coordinate; Q4 at
the same stations is nearly smooth. This is an interpolation signature,
not a displacement discontinuity or proof of causation.

## Disposition and next bounded work

Natural refinement changes shell stiffness, support partition, host
geometry, diagonal phase and coupling at once. The numerical checks
establish a reproducible finite-model comparison; they do not isolate a
defective shell trace or select a multiplier space. Preserve the
unresolved 1% independent-reference screen and the full G0B acceptance
criteria.

Before another execution, register a fixed `(128,64,64)` four-cell
stiffness/trace operator isolation with both natural corners and both
crossed combinations, using the same load, beam, multiplier and physical
stations. Include manufactured nonaffine interpolation and an independent
physical-reference check, retaining the root elastic/direct/external
split and support/port bands. Separately budget and register an Nm64→128
resolution comparison before fixing a multiplier policy. The review is a
design recommendation, not authority to run those cases or claim a
corrected formulation.

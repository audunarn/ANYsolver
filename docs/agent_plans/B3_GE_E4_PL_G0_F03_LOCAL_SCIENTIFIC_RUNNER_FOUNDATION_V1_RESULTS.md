# F03 local scientific runner foundation v1 results

**Implemented and independently reviewed — 23 September 2026. No scientific
registration or execution authority. G0B remains open and G1 remains barred.**

## Result

The bounded local-scientific protocol is frozen sufficiently to implement its
runner. The first runner foundation now provides:

- An exact five-case Q1/Q2 topology inventory with exact midpoint refinement.
- Topology-only graph and assembly preflight before numerical assembly.
- A rederived, source-bound preflight inventory; caller-fabricated observations
  cannot be hashed or admitted.
- The complete protocol resource envelope, including the 512 MiB raw-archive
  cap, factor/certificate/exact-verifier limits, process RSS/time, launch
  cutoff and thread cap.
- A contiguous, single-use inverse-block archive plan for every KKT column.
- Process-tree supervision that retains observed descendants after parent
  changes, aggregates their RSS, and cleans them on limits or interruption.
- Exclusive start and terminal receipts bound to the registration, plan,
  source, case, topology and exact supervised root PID.
- Strict bounded array groups with exact member order, shapes, dtypes and NPY
  payloads, deterministic ZIP size, one immutable input snapshot and all
  admission checks before evidence allocation.

The implementation does not assemble a scientific case, factor a matrix,
solve equilibrium, register a run, or adjudicate physical acceptance.

## Frozen inventory

| Case | p | cells | physical DOFs | KKT order | intervals | max trace | KKT nnz | assembly triplets |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Q1_L0 | 1 | 9 x 5 | 96 | 99 | 9 | 40 | 3,792 | 12,112 |
| Q1_L1 | 1 | 18 x 10 | 374 | 377 | 23 | 96 | 25,268 | 112,656 |
| Q1_L2 | 1 | 36 x 20 | 1,470 | 1,473 | 47 | 240 | 201,092 | 1,045,600 |
| Q2_L0 | 2 | 9 x 5 | 374 | 377 | 9 | 108 | 29,388 | 75,492 |
| Q2_L1 | 2 | 18 x 10 | 1,470 | 1,473 | 23 | 280 | 234,772 | 852,000 |

Complete inverse evidence is exactly 37,068,136 bytes. Each largest case is
17,357,832 bytes. The archive plan uses blocks of at most four columns and
requires one contiguous 0..N inventory.

## Source history

- `363d325b`: corrected independently reviewed numerical protocol.
- `80046813`: recorded protocol review and implementation-only GO.
- `f2afc86f`: initial case/resource and archive-plan contract.
- `8e0e1655`: factory-owned rederived preflight and complete resource binding.
- `534ba848`, `df2d30dd`: process-tree supervisor and retained-descendant fix.
- `610e6bc3`, `7090d4aa`: lifecycle receipts, bounded reads and root-PID binding.
- `0252db0b`, `a557b6b4`, `9f4a6be0`: bounded saved-array storage and all
  allocation-order, immutable-snapshot and ZIP-envelope corrections.

## Verification and independent review

The affected suite passes 83 tests after the final correction. It covers the
existing local grid, assembly and saved-composition contracts plus the new
case, archive-plan, supervisor, lifecycle and storage modules.

Independent review found and then verified corrections for:

1. Fabricated/stale preflight records and unbound resource limits.
2. Detached descendants omitted from later RSS samples.
3. Start receipts not tied to the supervised root process and receipt growth
   between a size check and read.
4. Writer/reader ZIP cap disagreement, mutable ZIP/header reads, and ownership
   copies before complete validation.
5. Oversized individual members read before their per-schema bound.

The final independent review reports no findings in the bounded foundation.
It did not perform a scientific solve, large 512 MiB archive exercise,
factorization or physical-mechanics acceptance.

## Decision and next boundary

Status is `IMPLEMENTED_NOT_QUALIFIED`. Scientific registration remains barred.

Next implement the exact evidence-group schemas and exclusively writing case
producer, followed by the solve-free adjudicator and top-level one-use
coordinator. Every group must bind the complete inventory listed in Section 5
of `B3_GE_E4_PL_G0_F03_LOCAL_SCIENTIFIC_PROTOCOL_V1_DRAFT.md`. After bounded
synthetic producer/replay tests and independent review, commit a clean source
and create one immutable registration. Only that later registration may grant
one scientific execution authority.

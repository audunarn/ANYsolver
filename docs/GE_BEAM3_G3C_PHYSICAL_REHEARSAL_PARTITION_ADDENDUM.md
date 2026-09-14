# GE-B3 G3c Physical Rehearsal Partition Addendum

Status: design authority only; it authorizes no numerical execution by itself.

## Bound predecessor and reason

This addendum succeeds the private physical mixed-owner contract whose
normalized SHA-256 is
`f6638863e6e222c795e980194c9a71cf42eb83bdcba6af2a8c409164ad4d957b`.
It changes no mechanics, cases, ordering, tolerances, child limits, acceptance
predicates, restart semantics or public boundary.

Candidate `5166d9282ce4a965c143474efcac01a78626bf95` completed its frozen smoke and
local gates. Its unpartitioned rehearsal reached the registered 1,800-second
whole-wave limit after 37 complete nodes and three attempted nodes. No
scientific node failed, no canonical rehearsal aggregate was created, and no
child survived. This is a process-partition obstruction.

## Frozen rehearsal inventory

The unchanged rehearsal has exactly 234 assignments. Its canonical inventory
SHA-256 is
`a53103c9d3162dbfdc04e647c81fa36aaad6fa80f9a13b1cd4abcae124c96733`.
The partition manifest has canonical SHA-256
`0b1beffb58ddbed1bb53891e11a7f5e0c8ad7b646cc539e4a908d7e4321ade86`.

| Partition | Original indices | Count | Assignment-list SHA-256 |
|---|---:|---:|---|
| `R-HISTORY` | 0–9 | 10 | `654af72fd3dddca92c736a138e179df0e4ba97da7cd25e4ae97316403fbb5d27` |
| `R-PREFIX-A` | 10–29 | 20 | `7a3390c1df7c7391feb2bea111bd9ee314db0b90c411145f42fbe0844170eae5` |
| `R-PREFIX-B` | 30–49 | 20 | `b3e168ff12baee60cb5c88eed5e2337aafa9ec7b860704cf92ba0626ff4314bc` |
| `R-PREFIX-C` | 50–69 | 20 | `a91be5d24950c85c45bdaf4efd8e1ce23515c1f4adf2f3db472b973dbe8d8313` |
| `R-PREFIX-D` | 70–89 | 20 | `10d5cd0ca3a3529605f02f12d0b821c801cd4cce564f85d74830c158b3ad741e` |
| `R-GUARDS` | 90–233 | 144 | `e597616542d6bf5a323b1cd12b7e3c0517d726eab812118b8ec63548c5429827` |

The manifest uses this exact canonical JSON value:

```json
{"lane":"rehearsal","partitions":[{"assignments_sha256":"654af72fd3dddca92c736a138e179df0e4ba97da7cd25e4ae97316403fbb5d27","indices":[0,1,2,3,4,5,6,7,8,9],"partition_id":"R-HISTORY"},{"assignments_sha256":"7a3390c1df7c7391feb2bea111bd9ee314db0b90c411145f42fbe0844170eae5","indices":[10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29],"partition_id":"R-PREFIX-A"},{"assignments_sha256":"b3e168ff12baee60cb5c88eed5e2337aafa9ec7b860704cf92ba0626ff4314bc","indices":[30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49],"partition_id":"R-PREFIX-B"},{"assignments_sha256":"a91be5d24950c85c45bdaf4efd8e1ce23515c1f4adf2f3db472b973dbe8d8313","indices":[50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69],"partition_id":"R-PREFIX-C"},{"assignments_sha256":"10d5cd0ca3a3529605f02f12d0b821c801cd4cce564f85d74830c158b3ad741e","indices":[70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89],"partition_id":"R-PREFIX-D"},{"assignments_sha256":"e597616542d6bf5a323b1cd12b7e3c0517d726eab812118b8ec63548c5429827","indices":[90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233],"partition_id":"R-GUARDS"}],"schema":"GE_BEAM3_G3C_PHYSICAL_REHEARSAL_PARTITION_V1","whole_inventory_sha256":"a53103c9d3162dbfdc04e647c81fa36aaad6fa80f9a13b1cd4abcae124c96733"}
```

## Execution and dependency rules

- `R-HISTORY` runs first and produces all ten authentic checkpoints.
- Partitions run only in the exact serial order `R-HISTORY`, `R-PREFIX-A`,
  `R-PREFIX-B`, `R-PREFIX-C`, `R-PREFIX-D`, `R-GUARDS`. Every partition after
  `R-HISTORY` requires complete accepted records for every preceding partition,
  in addition to the accepted smoke/local prerequisites.
- Packet paths, byte counts and SHA-256 values are revalidated from the original
  `R-HISTORY` nodes. `R-GUARDS` additionally binds all four accepted prefix
  partition receipts. This proves the fresh positive resumes for B2 BASE S0
  NONE prefix 2 and MULTIFAMILY_LOOP BASE S2 CM3 prefix 9 succeeded before any
  of the inherited 142 negative probes is launched.
- Assignments keep their original whole-inventory indices; local renumbering is
  forbidden.
- Every partition binds the whole inventory hash, partition-manifest hash,
  selected indices, implementation review and smoke/local prerequisites.
- A partition terminal cannot classify G3c or satisfy rehearsal acceptance.
- Each partition retains at most three children, one numerical-library thread,
  24 GiB per tree, 600 seconds per child, 120 seconds inactivity and 1,800
  seconds per invocation. No consumed partition is retried.
- Failure drains the tree, preserves diagnostics and creates no accepted
  partition record.

## Canonical union

A no-mechanics finalizer accepts exactly the six complete partition records. It
recursively validates every receipt, review, node lease, node process,
completion, science record and input packet. It rejects duplicate or missing
indices, wrong membership, foreign candidates, inconsistent history packets,
noncanonical/nonfinite/type-confused JSON, unregistered files and any
nonpassing process.

Only the exact ordered union `0..233` may emit the unchanged
`GE_BEAM3_G3C_PHYSICAL_AGGREGATE_V1` rehearsal aggregate and its receipt DAG.
Partition records never masquerade as that aggregate. The finalizer uses the
same 1,800-second watchdog and exclusive same-volume publication, and imports
no production mechanics or numerical package.

## Acceptance boundary

An accepted union establishes the frozen rehearsal only. It does not close
MO08/MO18, authorize formal dispatch, establish full G3c, qualify production or
change a public/default route. Formal partitioning and active/passive complete
operator/history covariance require a later, separately frozen addendum based
on rehearsal measurements.

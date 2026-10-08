# F03 five-case aggregate: reviewed implementation result

23 September 2026. The read-only five-case aggregate and exclusive receipt
codec were committed on `codex/b3-ge-e4-pl-integration` at `dbc6acbe`.
This is an implementation/review result, not a scientific registration,
executed F03 result, G0B acceptance, or release qualification.

The aggregate inventories all five registered plans, lifecycles, and canonical
sealed case receipts before replay. Successful executions, including numerical
FAIL/HOLD cases, receive independent single-case replay. A missing, invalid,
or incomplete case blocks all cross work. A nonpassing replay leaves cross
predicates `NOT_EVALUATED` under the frozen status precedence. Passing cases
feed five retained snapshots to the reviewed sparse comparator. The aggregate
binds source and evidence hashes, four exact nested prolongations, registered
cross-resource caps and tolerances, comparison failures, and zero cross-phase
assembly/factorization/solve/recovery work. Single-case replay retains its
separately declared recovery checks. The final five-case evidence and source
registration are rechecked before and after the exclusive write. Read-only
aggregate replay independently recomputes the decision.

Verification: all 32 local scientific test modules ran with **341 passed and
2 skipped**; the skips require symlink-creation privilege denied on this
Windows host. `git diff --cached --check` passed before commit. Independent
code/mechanics review reported no remaining findings after corrections to
canonical inventory, stale evidence, stable receipt reads, source rebinding,
cross budgets, complete failure inventories, and the exact P topology.
The reviewer independently ran 88 passing tests with the same two privilege
skips. No scientific child was launched and no one-use registration was made.

Next prerequisite: implement and independently review the serial one-use
coordinator, including source/environment preflight, exclusive launch markers,
durable terminal closure on failure/cancellation, registered cutoff, and
bounded lifecycle tests. Only then freeze a clean candidate and decide whether
to create a single scientific registration. G0B remains open; G1 is barred.

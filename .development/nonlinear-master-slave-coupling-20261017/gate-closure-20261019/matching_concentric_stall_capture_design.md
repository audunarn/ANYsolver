# Matching concentric stall capture — prepared, not executed

Independent instrumentation preparation only. No product/test edits, Python
imports, tests or numerical jobs were launched. Root must inspect this script
and grant separate execution authority; the existing shared ledger, source
freeze, single numerical child and reserve still govern execution.

The sole case is the original `arc_reference.run_case(32, 'matching', 0., 30.)`
from zero: unchanged geometry, oracle, loads, constitutive/trace defaults,
12 initial increments, 40 Newton iterations and actual tolerance 1e-8. The
script adds status/progress observers and accepted snapshot recording only.
It does not change line search, increments, tangent, precision or material law.

The inspected force route is `_newton_increment` nested inside
`_solve_static_nonlinear_under_lease`. Traversal matches both function name
and the imported production file, crossing forwarding/performance wrappers.
The status callback sees coherent current Newton u/q/F_int/K_T/residual and
trial/committed histories before factorization. A wrapped factorization handle
captures the actual K_red, RHS and returned delta for the SAME state, after
the real solve, before the production caller changes q. Stamps contain accepted
step/load, trial load, increment serial, iteration and hashes of u/q. A stamp
mismatch or missing required local raises a typed diagnostic layout error;
no missing local is silently fabricated.

Every raw state is explicitly accepted or unaccepted. Before-factorization
captures have matrix/RHS/delta explicitly unavailable; after-linear-solve
captures bind all three to that iterate. Saved history is deep-copied, never
committed/discarded/reassembled by instrumentation. Existing reference cache
geometry, frames and center derivatives are observed without rebuilding them.
T, affine offsets, stored dead loads, actual reduced external load and residual
are saved. A full dead-load vector formed from stored F_const/F_prop is clearly
labelled as an algebraic observation when projection reuse leaves the cached
full external load unset. No residual/tangent evaluation is added.
The before-linear-solve raw has the actual matrix/RHS and delta=None, preserving
the system even if the real linear solve fails. Normal solver returns preserve
raw u/history/full info/steps separately from the arc assessment. Its accepted
flag requires exact u-hash/load correspondence to the last accepted snapshot;
false means no such correspondence was established, not that a returned state
was independently proved inadmissible. Completion still requires terminal status.

Capture band is actual residual_norm/reference in [1,5] times actual tolerance.
At most16 pre-factor dumps are written; all band post-solve dumps are retained.
After four consecutive band states at exactly the same increment and load,
with residual max/min <=1.05, a diagnostic-only BaseException stops AFTER the
fourth matching linear solve data is durably saved. It is caught outside the
public solver, allowing normal lease/context finally blocks to unwind. This
criterion records a short plateau; it does not establish a numerical floor or
nonexistence of a solution. A normal result is preserved separately, and an
outer process timeout may leave no terminal.json. Already atomically completed
raw files and flushed events remain useful; a timeout alone proves no physics.

Exact planned command (NOT executed; root chooses a unique evidence/run name):

```powershell
& .venv/Scripts/python.exe .development/nonlinear-master-slave-coupling-20261017/gate-closure-20261019/harness.py --name matching-concentric-stall-capture-1 --timeout 120 --hash-input .development/nonlinear-master-slave-coupling-20261017/gate-closure-20261019/diagnostics/matching_concentric_stall_capture.py -- .venv/Scripts/python.exe .development/nonlinear-master-slave-coupling-20261017/gate-closure-20261019/diagnostics/matching_concentric_stall_capture.py .development/nonlinear-master-slave-coupling-20261017/gate-closure-20261019/matching-concentric-stall-capture-1
```

Runtime limitations: source-layout and private-state copying cannot be confirmed
without the separately authorized run. No small-strain/rotation reconstruction,
high-precision analysis, repair or acceptance assessment is included. This
private diagnostic deliberately fails closed if the force layout changes.
Hashes of relevant product/oracle/helper/script files and import origins are
saved at launch/end. A deterministic rebuild expression, actual model node/DOF
layout, element classes and original solve kwargs accompany the raw captures.

Static handoff: ProgressEvent is a Mapping in src/anysolver/control.py90, with
public event_type field and Mapping iteration/getitem, so the progress observer's
attribute and dict(value) observations match source. All twelve named product,
oracle/support/derivation identity paths existed at handoff. Script SHA256:
C639873E3EA25D5F87CD69F37CD32D1988A7478E7ED466CBA5BE3DD49DC9E4F1.
Only shell text/path inspections were used; no Python syntax/import/runtime check
was performed under this preparation authority. Frozen for root inspection/run;
no further script edits will be made during the serialized harness attempt.

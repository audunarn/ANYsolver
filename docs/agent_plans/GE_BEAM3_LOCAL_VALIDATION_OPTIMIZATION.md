# Local sealed-operator validation scheduling

Measured predecessor 88e9b657254803a40267d55d8bebe82ed5a2ea0f completed two
serial native enrollment/replay diagnostics (53.537046 and 54.137091 seconds).
Control and observed checkpoint, state and completion bytes agreed. Observed
enrollment made 10578 full physical guards (23.114851 seconds); restore made
5299 (12.090790 seconds). Full model identity alone took 32.078757 seconds.
This is selected-call profiling, not a statistical speed benchmark or qualification.
Its verified external archive is
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-replay-profile-88e9b65-20260909`:
25 entries plus manifest, 3308 bytes, SHA-256
1bc407636af2c421f989cf2512ba83310dd7399907cfd1baf76ef7bb0277e196.
Coordinator session 38991 exited zero; both child trees are empty.

Add explicit private GE_BEAM3_LOCAL_OPERATOR_VALIDATION_BOUNDARY_V1 scope. Outside
the scope every original full-check callback is forwarded unchanged. Inside it,
each evaluate/recover call validates the full model/program/constraints immediately
before and in finally after the local operation. The exact sealed retained
generalized operator must be used. Each existing inner callback checks that local
operator, the unchanged 120-second context deadline and cancellation. No callback
is removed; no timer is reset. Scope cleanup is guaranteed and nested scope rejects.

The local operator does not read model, constraint or load registries; it uses
owned input arrays, immutable reference/section/history values and its own local
guards. Those computations and their order are unchanged. Loads and global
assembly remain outside the local boundary with the original full checks. No
mutable identity cache or accepted-state shortcut is introduced. Complete native
mechanical checkpoint replay remains mandatory.

Test exact return/exception forwarding, before/after validation including failures,
mutation rejection, deadline and cancellation, exact scalar recovery, and actual
load/unload/reversal/prefix-resume/fresh-replay equality. Rerun the original elastic
seed suite on the unchanged default path. Follow with one bounded explicit-scope
N32 replay diagnostic using the original accepted target-one input. Require exact
checkpoint and state bytes against the predecessor, and observe full-check counts.

Do not rerun a consumed failed branch command. After this optimization passes its
tests and measured equality check, a new frozen branch successor may run all the
same targets and lifecycle operations in fresh directories under the same limits.
The prior deadline wave and every qualification record remain immutable.

No public selector, default, section law, mechanics, tolerance, B2/B3/Q4/S3,
version, tag, integration or publication changes. No independent-author review
claim. The full production beam and objective beam-shell goal remains unfinished.

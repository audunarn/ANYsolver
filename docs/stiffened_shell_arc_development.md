# Experimental physical arc continuation

`continue_arc_length` is available on the existing stiffened-shell owner for
accepted Q4 shell J2 / generalized BL5 states, and separately selected
`CURVED_Q4_POINT_REFERENCE_V1` elastic point states or
`CURVED_Q4_POINT_MATERIAL_REFERENCE_V1` generalized-beam material point states
(with optional shell J2), with affine nodal dead forces.
It is experimental and unqualified. It does not establish stability, a first
limit point, branch uniqueness, mesh-independent continuation or capacity.
Other materials, external load contexts, moments and chart rebasing on this
history are not admitted. Existing force/displacement defaults are unchanged.

Construct the owner through `anysolver.stiffened_shell.create_analysis` as usual
and first obtain or restore an accepted force or displacement endpoint. The
following fragment uses that owner and a caller-supplied physical load direction:

```python
from anysolver import stiffened_shell as ss

order = analysis.preflight()["arc_metric_node_order"]
# Supply positive reference weights in exactly this (domain, model-node-ID) order.
# Their physical interpretation is a model input; equal weights do not establish
# mesh-independent behavior. length_m is an explicit positive reference length.
metric = ss.PhysicalChordMetric(weights, length_m)
control = ss.ArcLengthControl(
    domain="beam", node=tip_node, component=2,
    metric=metric, radius=5e-6, orientation=-1,
)
result = analysis.continue_arc_length(load_direction, control, steps=2)
saved = analysis.checkpoint()
```

`steps` counts accepted increments, not requested total travel. An exhausted
Newton/backtrack attempt can halve the radius under the bounded cutback controls.
The accepted radius and fixed-seed load amplitude appear in `result.history`.
The applied force is `seed_load + amplitude * load_direction` throughout the
history. A chosen free translation orients the tangent at each increment and
must remain a valid local coordinate. There is no automatic branch switching.

The physical metric measures translations divided by length and physical
rotation chords. The corrector uses a frozen tangent-plane projection in this
metric. Native retained coordinates and multipliers remain in equilibrium but
do not enter an arbitrary Euclidean continuation norm. Relative rotations at
or beyond pi/2 are rejected. Existing physical equilibrium, compatibility and
material checks remain mandatory.

`ArcResult.status == "completed"` means that this invocation completed its
requested accepted-step count. The owner, callbacks and restored result retain
`accepted_prefix`, independent of an invocation's goal. `ArcAttempt` records
trial evaluations, solves, rejected candidates and generalized beam event work;
`attempt_history` retains all accepted increments' attempt groups. Endpoint
validation performs an additional mechanical assembly outside these trial
counts. `ArcSelectionFailure.attempts` preserves work for an exhausted step;
the owner's checkpoint remains its last accepted prefix.

Cancellation before publication preserves the predecessor. Cancellation between
increments preserves the complete accepted prefix. An accepted callback receives
a detached result and may request cancellation; reentrant state writes fail.
Selected recovery reads cached physical/material quantities without assembly.

Restore the `ANYSSARC1` checkpoint into a fresh, identical owner, then call
`continue_arc_length` with the same metric, load direction, radius, orientation
and numerical controls. The number of additional steps can change. Checkpoints
bind the model, predecessor, affine load and complete accepted-step attempt
inventory; they also replay the final material update for consistency. A digest
is not proof of physical loading history. Force/displacement drivers reject arc
history instead of interpreting it as their own controller state.

The curved elastic point route uses a separate mechanical kind and policy inside
the arc envelope. It stores no shell plastic arrays and reports no shell plastic
recovery. Native generalized beam history is validated as elastic. Its bounded
cancel/restore/continue test also compares the endpoint with force control; it
does not qualify the E04 roof, a first limit point or a descending branch. The
known tiny-load nonconvergence in the curved force-control control remains open.

Current limits are 1,024 accepted increments, bounded binary/metadata size and
the unchanged twelve-backtrack arc budget. The curved material route has its own
`B3_GE_CURVED_MATERIAL_POINT_TANGENT_PLANE_V1_DEV` controller policy and
`B3_GE_E4_PL_CURVED_MATERIAL_POINT_ARC_MECHANICS_V1_DEV` mechanical kind.
Accepted and fixed-predecessor beam histories are mandatory; shell J2 histories
are stored only when the definition admits that material. Restore replays the
actual endpoint update before atomic publication. Elastic checkpoint identities
are unchanged. Bounded loading/unloading and restart evidence does not establish
material limit loads or the programme's full continuation envelope.

Other limits include the explicit per-step budgets. These development limits do not fulfill the
programme's scale or capacity requirements. The standing test is
`tests/test_stiffened_shell_arc_trial.py`; accepted evidence is tracked in the
programme acceptance matrix.

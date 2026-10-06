# Native flat BL5 position/director arc metric — source candidate

Status: **implemented but unverified; source tests and example UNRUN**. This is
an explicit DEV prerequisite candidate, not G4D capacity evidence, scientific
acceptance, a limit-point demonstration, or release authority. The existing
`PhysicalChordMetric` continues to measure full shell and beam frames and keeps
its historical controller/checkpoint format. The new option is never selected
automatically.

## Admitted convention and API

`NativeDirectorChordMetric(weights, length, shell_nodes)` is available from
`anysolver.stiffened_shell` and may be supplied to `ArcLengthControl`. Weights
follow the compiled shell nodes, then beam nodes; `shell_nodes` must exactly
match that owner's shell node count. The new metric owns immutable weights and
length. It admits only the already constructed **flat native material BL5**
profile, including its admitted Q4/S3 material combination and native mixed beam
history. POINT, curved reference, footprint and distributing footprint routes
are refused. Existing native ordinary/fixed-translation seed restrictions,
constitutive equations, attachment law, constraints, and equilibrium tolerances
remain in force.

The flat native shell reference normal is material `e_z=(0,0,1)`. Its physical
director is the third column of `R=exp(phi) A`, using the driver's owned shell
anchor `A`; actual native BL5 seed admission requires unrebased identity anchors.
Beam physical frames are stored rotations advanced spatially on the left. No
caller-supplied director may change this material convention.

## Mathematical contract

For shell nodes `S`, beam nodes `B`, physical translation differences `u`, proper
physical frames `R,R0`, directors `d=R e_z,d0=R0 e_z`, positive frozen weights
`w` and characteristic length `L`, the squared chord is

```
C = sum_S w (|u/L|² + |d-d0|²)
  + sum_B w (|u/L|² + 1/2 ||R-R0||_F²).
```

For a spatial left spin `delta omega`, `delta d=delta omega cross d`; hence the
shell spatial gradient is `2w(d0 cross d)`, and translation gradient is
`2wu/L²`. A proper-rotation check precedes director extraction, so reflected,
nonorthogonal, nonfinite, incomplete or incorrectly ordered data cannot hide in
the director quotient. Inputs are read without mutation.

The controller freezes a physical predecessor tangent `(v,omega0)` normalized
by this seminorm. Its signed tangent plane is

```
P = sum_S w [u dot v/L² + (d-d0) dot (omega0 cross d0)]
  + sum_B w [u dot v/L² + 1/2 (R-R0):(skew(omega0) R0)].
```

The shell spatial row is `w d cross (omega0 cross d0)` and its translation row
is `wv/L²`. At the predecessor, the tangent's plane derivative is exactly

```
N² = sum_S w [|v/L|² + |omega0 cross d0|²]
   + sum_B w [|v/L|² + |omega0|²].
```

Normalization uses `sqrt(N²)` and refuses a zero or unrepresentable value. A
shell spin parallel to the **current physical predecessor director**, including
a tilted director, is null; the same beam spin remains measured. The stored
`normal_spins` retain the actual equilibrium predictor divided by that norm.
Mechanical predictor and Newton increments are never projected to remove
drilling. Retained coordinates and multipliers remain in equilibrium and in the
actual update; only their metric row is zero.

Shell chart columns map to spatial spin by the existing left Jacobian
`J(phi)`; the metric row is pulled back with `J(phi).T`. The actual driver adds
shell chart increments and left-multiplies beam frames. This exact pullback is
used for both the chord and frozen plane, rather than treating additive chart
entries as spatial spins.

## Local domains and projection nulls

Shell directors must remain in the open predecessor hemisphere `d dot d0>0`.
Antipodal and equatorial candidates are refused; arbitrary shell drilling does
not trigger the beam/full-frame pi/2 metric guard. Beam relative angles retain
the existing strict pi/2 frame-chord domain. The shell squared chord has the
expected zero row at the predecessor, so correction uses the frozen plane.
For a nonzero shell tilt direction `eta=omega0 cross d0`, the rotational plane
row is `d cross eta`; it can vanish when `d` is parallel to `eta`. The open
hemisphere excludes that alignment because `eta` is perpendicular to `d0`.
Null directions still exist for pure drill and unmeasured algebraic coordinates;
the free translational orientation and the complete equilibrium system govern
branch continuation. No branch uniqueness or stability conclusion follows.

The **new option only** also restricts the unre-based additive shell chart to
`|phi|<2*pi`, the connected domain before the first left-Jacobian rank loss.
This guards against a complete drill hiding a degenerate chart behind zero
director distance. It is a chart restriction, not a claim that physical rotations
of larger accumulated angle are invalid: a future rebased route would require
separate admission. It is not a conditioning certificate near that boundary.
Existing element strain/log guards and beam/cell increment guards remain active.

An invalid accepted parent chart is refused before assembly or predictor solve.
An initial new-option predictor leaving the metric/chart domain, or hitting the
existing beam/cell rotation increment guard, becomes a typed trial failure for
bounded cutback. Its failure snapshot is the unchanged valid origin with actual
origin evaluation, predictor solve, and rejected-predictor counts. New-option
Newton/backtrack metric guards also precede candidate assembly. No invalid
candidate evaluation or equilibrium is fabricated; cancellation, stale ownership,
programming and unclassified failures propagate under the existing rules.

## Objectivity, units and refinement

A common proper spatial rotation `Q` transforms `u,v,omega` by `Q` and both
physical frames by left multiplication. Euclidean norms, scalar products,
cross products, and the beam Frobenius product then preserve `C`, `P` and `N²`;
spatial metric rows transform by `Q`. A common rigid translation cancels in
the supplied translation differences. Shell normal spin is excluded **from
this metric only**. The complete shell mechanics, supports and attachment law
are not asserted to be drilling-gauge invariant.

Translations are divided by the same physical characteristic length `L`;
director/frame differences are dimensionless. Weights carry the caller's chosen
reference measure; radius and plane distance use its corresponding metric units.
No mass, node-count normalization, or mesh-independent weight rule is inferred.
Splitting a reference contribution among duplicate samples with weights summing
to the original preserves the metric. Actual mesh refinement requires physically
consistent reference quadrature, not equal node weights by default.

## Checkpoint and publication contract

The new outer policy replaces `TANGENT_PLANE_` in the admitted native BL5 policy
with `POSITION_DIRECTOR_TANGENT_PLANE_`. Its metadata also binds
`metric_kind=flat_native_bl5_position_director_v1` and the exact integer
`metric_shell_nodes`. Together with the compiled model identity these define
the distinct shell-director/beam-frame metric layout and fixed `e_z` convention.
The existing numeric physical-pose/normal layout is reused without a redundant
copy of material reference directors. Old metadata contains neither new field
and is decoded exclusively as `PhysicalChordMetric`.

Decode reconstructs the declared metric, validates admission/count, proper
rotations, finite shapes, weights/length, unit predictor norm in that metric,
oriented native coordinate progress, the local endpoint plane, and the current
chart (plus stored predecessor shell chart when the existing S3 layout contains
it). Existing digests, model/generation/history/control identities and the
mechanical endpoint replay are retained. Controller continuation and atomic
publication refuse crossing old/new metric prefixes. Fresh restoration remains
the existing strict public endpoint validation route; the new option supplies
no codec bypass or synthetic history substitution.

## Pending verification

`tests/test_stiffened_shell_native_director_arc_metric.py` specifies immutable
ownership, exact admission, pure drill versus tilt, rotated-parent drill null,
common rigid rotation, spatial derivatives, actual shell-chart/beam `_advance`
derivatives, retained/multiplier exclusion, unit predictor norm, invalid pose and
local chart/hemisphere refusal, initial cutback work counts, pre-assembly guards,
old/new checkpoint identity refusal, restart and atomic cancellation.

The one public integration case requires the existing authentic mixed/P1 gen3
checkpoint through `_loaded_seed` in
`tests/test_native_material_bl5_arc_same_origin_jacobian.py`, with both
`ANY_NATIVE_BL5_ARC_JACOBIAN_FIXTURE` and its existing exact `_SHA256` environment
input. It refuses the helper's fresh-load fallback. That fixture, its restored
material histories, and the common fixed predecessor remain provenance; no raw
evidence was traversed or altered for this source change.

All test functions and `examples/stiffened_shell_native_director_arc_metric.py`
remain **UNRUN**. No interpreter, build/install, numerical benchmark, loaded
fixture restore, or numerical verification was executed. Later execution needs
separate authority and must preserve historical failed evidence and scientific
acceptance gates. This candidate does not demonstrate the full G4D capacity goal.

## Complete-slice source review

An independent OpenAI Read reviewer assessed the metric, actual-update rows,
predictor, cutback, codec, controller, publication and source tests. The author
repaired the review's guard-placement/retry findings and strengthened atomicity
coverage to compare every public recovery field plus live state/history identities.
The final source assessment found no blocking defect. Root inspected the source
and scoped changes; Git whitespace checks passed. No Python or numerical check
ran. This review is not installed verification or different-family acceptance.

Next verification requires a fresh bounded allowance: focused new metric and
affected legacy checks, one isolated wheel build/install, and the installed
loaded-prefix/restart/refusal workflow. Existing remaining Jacobian/consumer
allowances exclude this new slice. Preserve their accounting without transfer.

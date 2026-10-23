# Corotational shell speed, 2026-10-23

Branch `claude/corot-speed-20261022` from main b7494ed66. Not pushed.

## What dominated (cProfile, 8x8 corotational plate, t = 3 mm, 50 kPa, 59 Newton iterations)

After the native contractions the cost is the authority-guard machinery of the
qualified Q4 element, not arithmetic: every observation of an external object
(material attributes, mesh coordinates, section arrays) was followed by a full
boundary guard (`boundary_guard`: module, epoch, class namespace, instance and
quadrature authority; about 46 us each). 17 full guards ran per element
evaluation, 4 component re-binds per evaluation, 8 material fingerprints.

## Changes (values bit-identical)

Review round 1 (Codex) found the plain-instance-attribute shortcut unsound
(a property `__dict__`, a spoofed `__getattribute__` descriptor, non-str dict
keys whose `__eq__` runs on lookup, non-atomic MRO/dict reads). It was REMOVED:
attribute reads are rechecked after every observation again, as before.
Regression tests `test_attribute_reads_are_always_rechecked[...]` fail on
71853cb58 and pass now. Kept (no findings):

1. `_guarded_float`: no recheck after `float()` of an exact `float`.
2. `_guarded_array`: no rechecks after converting an exact numeric ndarray
   (`dtype.kind in "fiub"`).
3. `_compensated_contractions.product` / `sum_arrays`: with the compiled kernels
   the Python finiteness screens run only after a kernel refusal (the kernels
   refuse nonfinite input; the reference exception is still raised).

Full boundary guards per element evaluation: 17.2 -> 11.1.
Measured (best of 3): corot 4x4 3.18 -> 2.65 s, 8x8 14.11 -> 11.7 s,
4x4 plastic 8.63 -> 7.96 s (about 17 %, 17 %, 8 %). The first version reached
17-24 % but relied on the removed shortcut.

## Not done (options; all remain owner decisions)

* `_qualified_linear_correction` re-runs the legacy zero-state kernel and a
  second component re-bind every evaluation although the result is constant for
  fixed inputs (about 13 % + 6 % of the remaining time). Caching it skips
  observations that the guard contract requires to be rechecked; needs a
  contract decision.
* `formulation_class_guard` identity-list fast path (about 4 %), warm-hit
  re-bind reuse of the component metadata, and trimming the per-coordinate
  rechecks in `get_node_coordinates` edit `e4_pl_element.py`, which is
  source-bound and concurrently edited by the plasticity branch.
* A fused compiled `elastic_shell_nonlinear_increment` (58 small products per
  evaluation, about 15 %).

## Output rotation DOFs with 2*pi offsets

Reproduced with a simply supported 4x4 plate (t = 1 mm, 50 kPa, one step): two
nodes carry |theta| = 6.365 = 2*pi + 0.082. Translations and the rotation
matrices agree with the 5-step run (1e-12 / 1e-10). Rotation DOFs are rotation
vectors updated additively; `theta` and `theta - 2*pi*theta/|theta|` are the same
rotation (1e-16) but `R(theta + d) != R(wrapped + d)` (gap 5e-2 for a 0.05
increment). Wrapping the stored or returned DOFs would therefore change what a
restart, continuation load step or any additive post-processing does, and the
wrapped values equal the original rotation only to rounding, not bitwise. Not
implemented. A consumer needing a canonical rotation should use the rotation
matrix (`rotation_matrix_from_vector`). Characterised in
`tests/test_corotational_speed_guards.py`.

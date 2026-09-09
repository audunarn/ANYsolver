# Retained GE-B3 support-construction optimization

Base: 65e4be3f5288670161345d8a5b0db8090ee545ce. No mechanical, tolerance,
load, material-state, spectrum, serialization, default or public-route change.

Preserved partial Euler development archive:
`ge-beam3-retained-euler-partial-65e4be3-20260908`, manifest 16025 bytes,
SHA-256 CE3CB44587311AC1CF88725CDF9AC95D3EA413C82D767D3BE14B91D2AAD87779.
N1 and N2 completed; N4/N8 and full repetitions have not run. This is not a
complete Euler gate. The diagnostic N2 checkpoint matches saved N2 point 02.

The profile recorded 3546 repeated sparse support transformations in one N2
point, 2.858997 cumulative seconds of 10.505678 total profiled seconds. Remove
only that redundant construction. Initial _model still validates the complete
supported transformation and node order. Every inner guard still recomputes
model_identity and validates/compares the complete constraint audit, including
element-supplied MPC equations; deadlines and program/load checks remain live.
There is no object-only cache, sampling interval or cached acceptance of dirty
inputs. DOFManager's legacy constrained set is not a transformation input:
assembly.build_constraint_transformation consumes require_valid_constraints.

Freeze this source and test support/node/DOF/material/load/program mutations,
element-provider changes and deadline rejection. Instrument the transformation
call count. Run the same diagnostic profile and compare checkpoint and point
bytes, then N1/N2 and prior nodal/port/ownership/modal regressions against saved
scientific files. Do not infer general speed from this one instrumented sample.
Expand N4/N8 only after evidence indicates safe execution or separately freeze
bounded point scheduling. Keep 600 seconds/child, 24 GiB/process tree, one
numerical thread, at most three workers and 1800 seconds/wave; no retries.

Independent review and complete environment graph remain pending. This private
optimization does not qualify GE-B3 or authorize any production integration.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

## Post-rehearsal input-type correction

The 16bef8b rehearsal completed N1/N2/N4 and all guards/ownership/nodal/port/modal
inventories. Its archive manifest is 32910 bytes, SHA-256
ECCAEF6F8E79A3FFC41E866362C16832ACF8677557A768767779AFFA2129CAE1.
N1/N2 scientific bytes match the pre-optimization archive. N4 completed in
243.316462 seconds, with relative Euler-load error 0.002063751220703347.

Review identified an input-type edge case: the constraint audit normalizes the
DOF count to int, while rebuilding the sparse transformation rejected a float
count. Bind the captured count's type as well as value in every guard. Add the
same-value float mutation and require rejection by both historical _model and
the optimized guard. This correction does not affect valid mechanics or any
serialized identity. Recheck the guard suite and saved scientific byte parity
before the next mesh refinement. N8 and complete deterministic cycles remain
unexecuted; avoid a monolithic N8 launch given measured scaling.

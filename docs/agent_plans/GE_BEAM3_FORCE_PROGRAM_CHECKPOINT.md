# GE-B3 native force program and global restart checkpoint

## Status and boundary

Development successor of `45a3fe533dbb6623f01d8bf10a14a508b8aef3a6`.
One new private module, `anysolver._ge_beam3_load_program`, implements an actual
bounded force-program driver over the preserved scalar assembly, sparse solver,
native rotation store and parameter-bound V4 element transactions. It adds no
mechanics and changes no existing source file, public selector, default,
qualified Q4/S3, B2/B3 or historical qualification record.

This is not production qualification or full solver parity. Independent review
is pending. No wheel, formal campaign, resource request, release or activation
was created for this checkpoint. Earlier wheel checks do not qualify this new
driver. The prior V4 checkpoint remains true for its own frozen extent; this
successor adds the standalone schedule and global restart missing there.

## Implemented path

`ForceProgram` binds one through 64 explicit signed parameter targets, a sorted
unique nodal spatial-force pattern, and exact bounded Newton/backtracking counts.
The parameter multiplies both the separate nodal pattern and each element's
model-bound spatial dead line force per reference arclength. The line force is
already included in the native residual; it is not projected and subtracted a
second time. Unloading and reversal use accepted station-owned plastic histories.

The driver admits V4 native elements only, at most 256 external-plus-cell-spin
coordinates, homogeneous translational supports and complete rotational support
blocks. MPCs, partial rotational supports, nonzero prescribed values, activity,
point masses and mixed formulations fail closed. Full rotational blocks avoid
silently confusing partial spatial constraints with a changing increment chart.
These restrictions are remaining parity work, not a replacement for the full
requested beam objective.

Newton uses the existing chart-consistent assembled tangent. Acceptance requires
both the chart residual and physical spatial imbalance on free DOFs to satisfy
the fixed computational threshold. Backtracking evaluates each candidate from
the same accepted state. Output imbalance is the physical net force, including
support reactions and the small remaining free residual, not the last rotation
increment's pulled-back moment. Result arrays are read-only.

There are at most 32 Newton updates and 12 backtracking halvings per target;
the defaults are 12 and 8. A failed target is not retried or automatically cut
back. Initialization, assembly, factorization and commit have cooperative
cancellation/identity/deadline checks. The deadline is 600 seconds, but cannot
interrupt a third-party factorization in progress. Formal execution still needs
the separately authorized process-tree resource/watchdog runner. This module
does not claim a hard process memory or time limit on its own.

## Transaction and restart safety

The canonical global capsule binds the complete program, model descriptors,
geometry, section and element identities, DOF mapping/support inputs, accepted
parameter, cursor, total displacement, physical imbalance, ordered step records
and every typed V4 element state. Exact canonical parsing rejects duplicate
keys, nonfinite values, wrong types, excess size/depth and unknown fields.

A complete capsule is staged and checked before the accepted pointer swap.
Cancellation or serialization failure before commit returns the preceding
accepted capsule. Cancellation after commit returns the newly accepted capsule.
Exceptions discard unaccepted trials. Observer mutations are checked before
further evaluation. Hashes do not turn mutable input changes into authority.

Restore replays each native state with its saved algorithmic origins and load
parameter, verifies global/local displacement agreement, epoch/cursor agreement,
supported equilibrium and exact physical-reaction replay. It does not re-origin
plastic response on the newly committed history. Changed programs, models and
rewound cursors are rejected. A paused capsule binds the full original program;
appending targets is not an implicit hot-restart permission. This is a model-bound
operational restart record, not an independently proven complete historical
scientific certificate.

## Verified checks

Initial development runs: 27 passed in 47.32 seconds; expanded 36 passed in
62.18 seconds. Final combined source regression: **151 passed in 137.44 seconds**.
The canonical development record lists the nine separate test-file inventories.
Runtime was Python 3.13.9, NumPy 2.4.3 and SciPy 1.16.3 with one numerical-library
thread. These were small correctness checks, not performance measurements.

The 39 new checks include elastic comparison against a separate assembly loop,
nodal reaction balance, plastic loading/unloading/reversal, byte-identical
uninterrupted versus paused/restarted capsules in fresh models, shared-node
models translated by `2^40`, support/model/program rejection, cancellation on
both sides of commit, precommit serialization failure, failed-step retention,
no automatic retry, deadline handling and canonical/hash mutations. Both split
paths ran in the same interpreter; two fresh-process cycles and installed-wheel
validation remain pending. The inherited 112 checks retain native state,
load-work, local-operator, accepted straight routing and generic cleanup coverage.

## Next work

1. Validate this successor in isolated installed-wheel/fresh-process checks.
2. Add displacement and arc-length scheduling using the native load-parameter
   derivative, with equally strict accepted-state/cancellation/restart semantics.
3. Complete broader support/load/section parity, loaded modal and buckling,
   engineering qualification and independent review.
4. Qualify public standalone integration and objective beam-shell connections.

The full straight/curved production beam and connection goal remains active.
No scientific acceptance threshold or qualification evidence has been changed.

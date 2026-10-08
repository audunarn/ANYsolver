# V10 matched-port and saved warping-action discriminator

Decision: V9's pure-Mz retained-spin response is 2/3 of its resolved-face
rotation, but those are different generalized coordinates. Under the same
isolated half-body supports and action, load the native cut **nodal frame**
as a second declared port and measure its rotation and retained-spin response.
Compare the work with V9's retained and C3D20 rigid-face ports. If nodal
frame agrees with the solid while retained spin differs, prioritize the
discrete trace/work map; if both differ, investigate body idealization.

From the previously saved V7 nodal cut action, form its exact six-resultant
rigid-face load using V9's dual Q8 face map and take the zero-resultant
remainder. Report each component's work on the *saved V5 displacement*.
This separates what a six-port test omits. It is not a new response solve
for the warping load and cannot allocate V5's original work ratio.

V10 must import ANYsolver from this worktree's `src`, record module origins
and byte hashes, reuse V5/V7 as immutable inputs, and preserve each failed
attempt. No F03, external execution, multiplier selection or qualification.
Authorized prospectively by the user's 8 October 2026 approval: up to two
attempts, 120 cumulative process-wall seconds with 60 seconds reserved,
30 seconds per child, CPU0, one numerical thread, JIT disabled, 2 GiB
process-tree RSS, one numerical job. Stop if the bound input/source changes.

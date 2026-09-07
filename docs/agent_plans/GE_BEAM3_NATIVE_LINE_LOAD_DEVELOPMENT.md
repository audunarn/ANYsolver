# Native physical-fibre line-load integration — development only

Parent checkpoint: `30152589dab2b8c19354244850a402769f7cc05a`.
Existing mechanics, shell/beam defaults, public routing and historical evidence
are unchanged. This is a private conservative dead-load successor, not a
qualification or release. Independent review remains pending.

## Scope and equations

For each of the two cells use the existing centered physical centerline
`r_h = (1-t)x_left + t*x_right + U*c0(t)`, reference lift `c0`, and
reference-arclength measure. The external work relative to the undeformed
geometry is

`W = integral f . [(1-t)(x_left-X_left) + t(x_right-X_right) + (U-I)c0] ds0`.

The force is constant in spatial axes and per reference arclength, and shares
the force program's scalar parameter with the separate nodal force pattern.
Its quadrature is the element's frozen rule (4 or 8 per cell). No quadrature
convergence or continuum load-accuracy claim follows from same-rule agreement.

Differentiate the load-only expression using analytic Exp-chart derivatives;
do not subtract material potentials. Retain all cell-rotation work. The 18
retained force/moment coordinates and nodal rotation traces carry zero direct
line work. Assemble `R = R_internal - lambda*grad(W) - lambda*f_nodal` and
`H = H_internal - lambda*H(W)`. The spatial Newton Jacobian removes the
connection of the **net** rotational residual from this complete chart
Hessian. This is different from the existing nonconservative nodal-couple route.

The new program identity binds the exact force rows, axes, measure, lift,
quadrature policy, model and section identities. Reuse the native accepted-only
history chain, including full residual/material/recovery replay. Changing load
policy is not a compatible restart. The existing force and couple programs are
left byte-for-byte unchanged. No public distributed-load adapter, follower
force/couple, modal/buckling authorization or new section model is introduced.

## Development checks and bounds

Use the preserved separately reconstructed rational-Q2/closed-derivative oracle
in `ge_beam3_centered_line_load_oracle.py`. It does not import producer mechanics;
this is algorithmic separation, not a new independent-authorship review.
Check tiny/zero work, curved/straight geometry, cell load terms, complete spatial
tangent directions, force/moment reactions, large common rotations, exact
common translations, reversal, coupled physical plasticity, unloading,
accepted-only cancellation, restart, mutation rejection and failed-step state.
Keep `1e-11` invariant and `1e-7` directional checks unchanged.

Each test wave: one numerical thread, Windows process-tree job capped at 24 GiB,
600-second wall bound, 120-second CPU-inactivity bound, fresh external directory,
no automatic retry. Each native solve/context retains its 120-second cooperative
deadline. Test XML, logs and state packets remain external. Two fresh-directory
development cycles should agree byte-for-byte on saved canonical state packets;
they are not formal scientific qualification cycles.

## Preserved preparation failure

First unfrozen test invocation: 21 passed, one failed, 9.51 pytest seconds
(11.030 supervisor seconds), exit 1. Directory:
`C:/Users/AUDUNA~1/AppData/Local/Temp/ge-beam3-line-preparation-mbn3tmq3`.
The directional test attempted a perturbation of fixed support DOFs, which the
existing supported-state guard correctly rejected before evaluation. Correct
the test to vary only free coordinates. Do not relax the support guard or the
directional tolerance. Preserve that failed invocation; the corrected test is
a separately initiated development run, not an automatic retry.

Corrected preparation invocation:
`C:/Users/AUDUNA~1/AppData/Local/Temp/ge-beam3-line-corrected-3pdhuogp`.
The new line-load inventory passed 24/24; the existing spatial-moment inventory
passed 19/19, including byte-exact old six-macro checkpoint replay. A separately
included historical checkpoint inventory passed 7 and failed 1: its live-source
hash assertion expects 16,910 bytes for the original fibre-state module, whereas
the previously accepted coordinate-budget/moment successor is 18,543 LF bytes.
That module is byte-identical to this work's parent `30152589` (LF SHA-256
`50197c685e73a32ec35a6ed658ac5ffbb8885ec48a0b43b3304e1c5661c2f2ea`).
The preceding edits are commits `1569152` and `9c5431e`, not this line-load work.
Preserve the historical evidence and assertion; do not update its frozen hashes
to make it pass. Overall invocation exit 1, 20.41 pytest seconds, 21.849 supervisor
seconds. This is not an all-suite pass. Subsequent line-load deterministic cycles
have their own explicitly separate inventory.

# Nontrivial material-anchor work: development workflow

The existing finite-resolution S3 history owner now reports the return algebra
without changing its contact force, tangent, Coulomb law, material anchors or
restart identity. The parameterized public example accepts `--workflow sliding`;
its default `pressure_event` fixture remains unchanged.

## Work conventions

For the independent fixed-normal, constant-pressure scalar slider, let
`e_trial=e_old+ds`, `e_new=clip(e_trial,+/-mu*p/k)` and `dp=e_trial-e_new`.
The exact piecewise traction integral is `DeltaE + mu*p*abs(dp)`.
The backward-Euler endpoint product adds `k/2*(e_new-e_old)^2`.

`return_storage_drop_anchor_j` measures hypothetical trial storage minus returned
storage. `hypothetical_projection_excess_anchor_j` is the trial excess beyond
endpoint-pressure plastic dissipation. Neither is additional physical dissipation.
The existing `return_projection_loss_j` is preserved as a diagnostic.

At finite gap, material-relative and moving-normal power components are only
jointly objective. The actual point-map common virtual-spin test verifies their
cancellation. It does not establish finite-pose admission. For varying pressure,
the return uses endpoint pressure times material-anchor slip: a discrete convention,
not an exact pressure-path integral. Accepted endpoint contractions and external
or control trapezoids remain quadrature diagnostics.

New work aggregates include only rows carrying
`material_anchor_return_algebra_v1`. Compatible older checkpoints may produce
mixed report rows; coverage lists the excluded rows. Empty history has explicit
zero-row status. No missing legacy field is silently interpreted as zero.

## Physical and numerical scope

The frozen six-phase fixture exercises press, stick, slip across target facets,
reversal, strict physical opening and recontact, with genuinely deformable target
normal/in-plane coordinates. Fine P1 pressure and all positive supports remain.
Ratio2/4 are actual equilibrated physical-subincrement resolutions. They measure
discrete sensitivity; they do not establish continuum or spatial convergence,
event-free histories, exact path energy, or engineering acceptance.

Scientific scales are separately Fref=0.02N and Mref=0.02Nm. Frozen gates are
equilibrium/wrench1e-6, complementarity1e-8, directional1e-5, dimensional gap50um
and algebra/sign tolerance1e-12J. Solver controls remain tolerance1e-12/max18.
The independent scalar slider is a matched local reference; reused structural and
contact operators in saved-pose checks are integration evidence, not an independent
nonlinear path-energy reference.

Final executed inventory, failures and artifact identities are in OUTCOME.md and
the raw CLOSURE.json under
`C:/ANYworkspaceWork/contact_s3_mesh_nontrivial_work_20261009`.

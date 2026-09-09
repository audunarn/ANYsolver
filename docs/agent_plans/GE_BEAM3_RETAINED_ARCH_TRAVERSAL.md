# Actual retained arch traversal and engineering refinement

Base 0d17ce55222a7814a8770521325f34bbe5ea16fe, tree
bb35898489dd9946bd50af25f2367e439467d1f3. This is a new actual retained
controller case; no old arc source/history is imported or reclassified.

Freeze the historical crown-loaded span-2 parabola y=.1*(1-X^2), clamped at
both ends, with the physical second director +z. All free spatial DOFs remain.
Section diag(1000,400,400,.02,.01,.02), generalized ellipsoid yield1e6/H1
keeps this registered path elastic. Four points per retained half-cell; no
change to operators, section law or quadrature implementation. Counts2/4/8/12
remain inside the current retained allocation. Twelve .01 frame-chord steps,
length scale2, parameter scale1, positive initial parameter orientation.

First run source/admission checks and the two-macro smoke. If it traverses,
run4/8/12 as a bounded development wave, maximum three workers. Preserve
all failures and partial diagnostic checkpoints; do not retry automatically.
Each child600s/24GiB/one numerical thread/120s CPU inactivity; whole wave1800s.
The unchanged physical Context120s guard remains active. A bound failure is
not evidence of a physical contradiction and does not permit bypassing guards.

The separately implemented continuum BVP9 is used only AFTER actual Newton
steps, at their actual crown drops. Evaluate reference fields directly at every
discrete station and node, not by unregistered interpolation. Recompute the
current accepted-state dP/dd from a new oriented full-border tangent; never use
the old predictor as the new slope. Check positive-to-negative native and
continuum slopes, increasing drops and descending accepted load. Full spatial
stability and independently reviewed branch uniqueness remain separate claims.

Every point: equilibrium/compatibility/chord/full remaining correction,
constitutive relation, force/moment/work balance, reflection and planarity
<=1e-11. Archive load, compliance-weighted recovery, physical energy, node/frame
errors, reference sensitivity/residuals, full recovered fields and replay hashes.
Finest twelve-macro maximum load/recovery/energy errors must EACH be <2%.
Coarse results stay explicitly diagnostic and cannot authorize production.
No coefficient/threshold tuning, suppressed mode, shifted tangent or partial GO.

Run two fresh deterministic cycles only after the complete rehearsal passes.
If it fails, preserve and diagnose before a separately frozen successor. Existing
beam/shell mechanics, defaults, aliases and historical evidence remain unchanged.
No public integration, merge or release here. Independent authorship review
and environment graph remain PENDING; this comparison is same-author
development against independently implemented equations, not qualification.

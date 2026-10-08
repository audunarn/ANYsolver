# Guided S3 algebraic interval path — prospective development contract

Question: can a reference-linear elastic S3 owner represent the physical Newmark
interval and its massless penalty equilibrium without interpolating through an
algebraic rate kink? No change to force law, mass, endpoint equilibrium or original
profiles. This is development, not scientific acceptance or general dynamics.

For reduced coordinates q, certified mass null basis Z and
P=I-Z(ZᵀZ)⁻¹Zᵀ, declare the physical interval

    p(s)=Pq0+s h Pv0+s² P(q1-q0-h v0), 0≤s≤1.

Average-acceleration physical Newmark makes this the common quadratic joining
physical endpoint positions and velocities. Algebraic coordinates solve

    Zᵀ[K q - f + Bᵀ W min(gref+Bq,0)]=0, Pq=p(s).

K is the exact reference-linear structural operator for the currently admitted
elastic S3 local route, not a tangent approximation to an arbitrary nonlinear
model. History base loads have zero algebraic projection; constant loads enter f.
For each fixed active mask A, q(s) is obtained by one block solve for its three
polynomial coefficients. Positive definite ZᵀKZ gives a unique algebraic solution;
otherwise this path profile fails explicitly. Positive penalty weights preserve
this convexity. Do not infer admission for other structural formulations.

Enumerate at most the admitted three pressure supports (eight masks). Partition
[0,1] at all real gap-polynomial roots of every branch. Within each root-free
interval choose a branch whose gap signs agree; check inequality extrema as well
as midpoint signs, complete coverage and continuity with a scale-based floating
point budget. No sampled path is used as a crossing certificate. Unresolved or
exhausted enumeration fails. Artificially small positive supports are not dropped.

Physical shell-corner gaps are affine maps of q. Their exact polynomial extrema
over every segment give the represented-path minimum, separately from weighted
pressure gaps. Candidate endpoint and represented-path gap gates both remain.
Report support transition locations on this discrete path; do not call them exact
continuum collision times. Event-driven step subdivision remains a later action.

Verification: independent scalar solution a=-c min(x,0)/(k+c), crossing and reversal,
two-constraint analytical separable case, explicit non-SPD/coverage rejection,
physical projection and piecewise algebraic residual checks, then a tilted public
S3 solve/restart with independently checked corner minima. One integrated fixture,
180s/953MiB/thread1. Reuse unaffected checks. No consumed authority or tolerance
is renewed or relaxed.

Prospective integration detail: explicit `s3_algebraic_path_dev` requires the
one-sided-rate opt-in and selects distinct constant/history profiles. Historical
profiles remain unchanged. Full lifted endpoints must agree with accepted nodal
coordinates under separately dimensioned controls: position1e-10m and rotation
1e-9rad initially. These numerical matching budgets are explicit API settings,
not engineering penetration/response defaults; mismatch is non-success.
Only this profile binds them into restart identity. Version3 checkpoints retain
the last accepted terminal support mask so grid-aligned transitions survive
restart. This is algorithmic reporting state, not physical friction/material state.
All nonfinite intermediates and unresolved interval coverage fail explicitly.

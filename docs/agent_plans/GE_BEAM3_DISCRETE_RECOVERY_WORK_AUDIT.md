# Discrete curved-moment recovery: work-map audit

Parent: `868fbfe40bf31758e5396570f29eb95cab304872`.
Scope: the preserved nine records and 168 station fields of the 1/2/4-macro
curved end-moment comparison only. Independent algorithm, same authorship;
independent scientific review and production qualification remain pending.
No nonlinear solves, continuum reference solves, smoothing, state updates,
changes to mechanics or changes to historical evidence are permitted here.

## Source and interpretation

The bound candidate uses a discontinuous cell rotation U and the physical
reference triad R0(s); its station director is Qh(s)=U R0(s). Nodal directors
are separate unknowns. They are not interpolated into this station field.
This distinction follows the discrete-curvature construction and separate
nodal/interior rotations in Humer--Steinbrecher--Pechstein, arXiv:2605.04573v1,
[sections 3.1--3.2, equations 48--49](https://arxiv.org/html/2605.04573v1).
The paper's lowest-order rotation approximation is cell-constant; the curved
reference lift and full coupled fibre conjugate are separately derived
candidate extensions, not claimed to be printed or qualified by that paper.

Consequently, differentiating Qh within a cell gives only intrinsic reference
curvature: its curvature strain there vanishes. Nonzero recovered constitutive
curvature represents discrete endpoint rotation work. It must not be described
as the pointwise derivative of a smooth interpolated nodal rotation field.
Likewise, a recovered station force need not equal a spatial boundary force
pointwise. These facts explain a possible approximation mechanism, not proof
that this implementation or its continuum limit is correct.

## Independently reconstructed discrete identities

For each half-cell, z=U^T(xR-xL)-(XR-XL), Vj=R0j^T/Jj,
and retained forces/moments p=[a,mL,mR]. The existing complementary problem
requires:

    sum_j wj Vj^T nj = a
    mj = (1-tj)mL + tj mR
    sum_j wj (1-tj) kappaj = -Log((U R0L)^T QL)
    sum_j wj tj kappaj = Log((U R0R)^T QR).

Thus sum_j (wj/Jj) Qhj nj=U a, the actual cell force entering nodal work.
The first six retained coordinates contain a for the two cells; the remaining
twelve contain endpoint moments. This ordering is reconstructed explicitly,
not obtained by calling native assembly or recovery.

For A=U R0node, ell=Log(A^T Qnode), spatial nodal rotation work maps an endpoint
moment to sign*A*Jl(ell)^(-T)*m, not simply Qnode*m. The inverse left Jacobian
is I-hat(ell)/2+[1-theta*cot(theta/2)/2]/theta^2*hat(ell)^2, with its analytic
small-angle series. The cell-rotation residual is -d cross (U a) minus the
sum of its two signed endpoint moments. These reconstructed cell/nodal
residuals are compared with saved residuals at 1e-11; separate directional
variation checks use 1e-7. These are checks, not modifications of the beam.

## Approximation-floor diagnostic

At saved continuum samples, minimize sum_j wj ||U R0j-Qreference,j||_F^2
over one proper U per cell using weighted SO(3) Procrustes. The fitted U is
never used to change state, recovery, work, resultants, qualification evidence
or solver coefficients. It measures the sampled best approximation within
the existing cell-constant deformation-rotation space; it is not a rigorous
continuous-domain bound or an improved recovery operator.

The first audit rehearsal passed 10 tests in 0.19 seconds without any new
equilibrium/reference solves. All 42 cell work maps reconstructed within
1e-11. At the full moment, maximum native weighted RMS frame errors at
1/2/4 macros were .205443/.107503/.055138; corresponding best-in-space values
were .202580/.107133/.055091. The near equality points to cell approximation
error as the dominant station-frame mechanism in these samples. Native U's
distance from the best U decreases approximately fourfold under refinement.

The recovered-force work identity differs by at most 8.7e-19, and nodal
residual reconstruction differs by at most 9.3e-15. The previously reported
nonzero pointwise forces are preserved, not replaced by their zero average.

This resolves the specific suspicion of a mismatched frame or work map in
these packets; it does not establish general recovery accuracy, section
parity, slenderness robustness, stability, independent review or qualification.
The next substantive scope is a frozen standalone finite-static/recovery
convergence and loading-path programme, followed by current-state spectral
and curved/ring coverage. Objective beam-shell coupling remains separate and
unfinished. Existing B2/B3 and Q4/S3 remain untouched.

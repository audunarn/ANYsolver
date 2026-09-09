# Diagonal-congruence saved-energy checker successor

Parent eb7c811a3d650c96f188316d68056b2ad7e3fa42. The unscaled front-aware
smoke failed after6.739seconds: no admissible pivot within front96. It launched
no paired workers and produced no inertia result. Preserve its12-entry archive,
manifest1688bytes SHA256
c4d0cf7dcf830a05a39e4cd01db4a33b403050302f97310715efb422336898a7.
No old command or output is reused.

Retain every binding, interpretation, case and limit in
GE_BEAM3_FRONT_AWARE_ENERGY_GATE.md. Add only positive diagonal congruence to
equilibrate coordinate units before its unmodified front-aware pivot algorithm.
For a nonzero diagonal use s_i=1/sqrt(abs(A_ii)); for a zero diagonal use the
maximum absolute entry in that row. An all-zero row fails. Stored finite positive
Decimal scales define a nonsingular diagonal S regardless of approximation in
their computation: inertia(S A S)=inertia(A). No stiffness modification,
stabilization, dropped term, sign adjustment or tolerance relaxation occurs.

Compute transformed symmetric entries once, retain all source values, and check
coordinate roundtrip. In addition to the existing reconstruction gate, bound
original-coordinate reconstruction error by transformed error times
max(1,maxabs(SAS))/(min(s)^2*max(1,maxabs(A))) plus roundtrip error; require<=1e-60.
This is a finite-precision diagnostic, not a rigorous interval certificate.
Return scales and both errors externally. No change to the raw-tangent-symmetry
failure, accepted mechanics or material history.

Background: optional symmetric scaling before sparse indefinite pivoting is
described by HSL MA57 (https://www.hsl.rl.ac.uk/specs/ma57.pdf). No HSL code or
dependency is used and this algorithm does not claim to implement MA57.
Test exact rational coordinate-congruence identity, signed scaled438-coordinate
chains at80/100digits, original-coordinate reconstruction,2x2zero-diagonal
pivots and unchanged failure guards. Freeze before one positive80smoke; only
on success run the remaining precisions/signs and fresh same-precision replicas.
Require identical replica bytes, matching inertia and original-index pivot paths
across precisions. Keep600second/24GiB children, max3concurrent, one numerical
thread,120secondinternaldeadline,1800secondwave, noautomaticretry.

Saved factor packets from d0ef7f5 are the only scientific inputs. No expensive
capture, solve or prior campaign rerun. Full production qualification, independent
review and objective beam-shell connections remain open.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

# Saved line-load spectra: separate continuum modal comparison

Development successor to clean `f19d7d40e46f1c8bdb641de40d972e0cebb53d70`
(tree `7d61ae0efbd1e171d4cdaca2a18ac0d4a7311483`). No public routing,
production mechanics, shell mechanics, defaults, qualification or release changes.

Reuse the immutable, already accepted line-load checkpoints and signed native
spectra for one, two and four curved macrocells. Their exact external paths,
byte counts and hashes are frozen in `ge_beam3_line_modal_comparison.INPUTS`.
No native nonlinear or spectral solve is authorized by this comparison.

The fixture is the preserved root-clamped curved cantilever with height 0.15,
full coupled elastic section, uniform reference-arclength spatial dead force
(0.3,-0.2,0.1), and physical sectional inertia diag(1,1,1,.02,.01,.01).
Construct one separate BVP9 continuum equilibrium and two independent-of-native
Ritz discretizations: degree/rule 14/64 and 18/80. The source equations and
continuum second variation are the preserved dead-line and loaded-Ritz reference
implementations; this is algorithmic separation, not independent authorship,
multiprecision certification or completed independent scientific review.

Spatial additive displacement and spatial exponential rotation are the continuum
variation coordinates. The fixed dead-force potential has zero continuum second
variation in those coordinates. In the native lifted centerline coordinates its
external Hessian is nonzero and is already included in the preserved native
spectra. Neither operator is substituted for the other.

Use the BVP's balanced spatial force and moment to form geometric stiffness and
check their constitutive consistency to 1e-11. An unfrozen zero-load preparation
failed because recomputing prestress through integrated Q-transpose-Q introduced
artificial stress (geometric norm 1.679277600817424e-9 versus unchanged 1e-9
zero-load check). Preserve that failure. No director projection, clipping,
mechanics change or tolerance relaxation is permitted. The corrected 21-test
reference inventory passed before this full comparison rehearsal.

Compare six signed eigenvalues; compute relative frequencies only when both
spectra are positive. No absolute-value repair of negative eigenvalues. Report
material-frame transported kinetic MAC, with 4/16/32 per-halfcell rules. This is
not a clustered-MAC qualification. Same-rule native kinetic identity uses 1e-11;
the 16/32 MAC and reference norm comparisons use 1e-8. Higher-rule native mass
differences remain quadrature diagnostics. Ritz-profile agreement uses 1e-7;
reference residual uses 1e-8. Record actual errors, not an inferred qualification.

Reassemble saved continuum operators and recheck eigenpairs during evidence
inspection, without another eigensolve. Reject changed inputs, matrices, modes,
profiles, overlaps, missing records, noncanonical JSON, duplicate and nonfinite
values. Twelve artifacts precede the canonical comparison. Outputs are exclusive,
and promotion follows successful worker exit, complete process-tree cleanup,
clean frozen-source checks and repeated reload validation.

First run a bounded complete rehearsal. Freeze this exact research/test extent
before one external development wave. One numerical thread, 24 GiB process tree,
600-second wall limit and 120-second CPU/output inactivity threshold. The BVP
and each Ritz solve also have 60-second limits. No automatic retry. Preserve
all partial failure evidence externally; it cannot become a canonical success.

The first complete unfrozen rehearsal recorded 26 passes and nine shared-fixture
errors: exact residual reload differed by approximately 2.7e-16 because LAPACK's
transient eigenvector memory layout preceded canonical sign/layout conversion.
Fix measurement order: canonical C-layout and signs first, residual second.
Preserve the failed packet; do not relax exact reload equality or the 1e-8 bound.

The result remains DEVELOPMENT_MODAL_COMPARISON_NOT_QUALIFICATION. Independent
review is pending; critical buckling factors, postbuckling qualification,
general nonlinear sections, solver/public integration and beam-shell joints
remain outside this comparison. Existing signed native evidence is immutable.

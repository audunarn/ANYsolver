# Sparse constrained-kernel design review

Read-only mechanics/numerics design input. No runs, factorization, tests, source edits, workers, Git operations or qualification packaging. Recommendation: a separately bounded sparse graph-kernel plus outward interval Schur certificate is mathematically defensible; neither SuperLU pivots nor an eigsh Ritz residual alone is sufficient.

## Dimensions and scope

For N_s=n, N_h=t=2nb, shell nodes (n+1)(n/4+1), fixed coordinates 6(n/4+1)+5, the free physical count after ONLY resultant elimination is

p=6[(n+1)(n/4+1)+t+1]+3t-[6(n/4+1)+5].

There are 9t negative resultant variables, m=10S constraints, kernel order p-m, and supported full KKT order p+9t+m. Largest case n64/whole8:1/t1024/H64/S16 gives p15745, resultants9216, m160, kernel15585, full supported KKT25121. The old 2400-physical/3000-KKT dense limits remain intact. Any large sparse protocol needs explicit prospective order/fill/work/retention limits and supervision under the unchanged time/memory envelope; this design is no execution authority.

Inspected saved reciprocal arrays/results: stationary S has 9910 stored coefficients at physical order625 and 11878 at1057; dense restricted minima3.7825923e-5 and5.4234328e-6 exceed recorded uncertainties4.0062866e-11 and6.7760138e-11. These small cases are useful crosschecks, not a bound for larger fill or conditioning.

## Sparse basis and complete rank

Use the actual dimensionally/diagonally scaled C, with its real free coordinate map. Select per support six translation pivots at the two quarter beam nodes and four transverse retained-director pivots at two distinct interior halfcells. The director moments must have distinct xi means; verify the selected director-component map is nonsingular. The local 10x10 block is triangular in translation/director groups under the declared straight constant-arm geometry. Quarter nodal hat support lies inside its own support for H divisible4; retained directors belong to exactly one halfcell. Nevertheless verify all other-support pivot coefficients are exactly zero, all pivots free/distinct, endpoints fully retained, and every physical role survives. Do not substitute external nodal rotations for native cell directors.

After permutation C=[C_f,D], D block diagonal and invertible, form the graph Z*=[I;-D^-1 C_f]. Invertible D proves all m rows independent and Z* spans the COMPLETE kernel; smin(Z*)>=1 follows from its identity rows. Rounded Zhat retaining exact identity rows also has smin>=1, but that does not establish that it spans the actual kernel. For rounded Zhat, certify local inverse/residuals against the actual scaled D and C, then bound eZ=||Zhat-Z*||. A 10x10 approximate inverse with outward ||I-DE||<1 gives ||D^-1||<=||E||/(1-||I-DE||), avoiding an assumed SVD backward constant or any global inverse. SVD can remain a diagnostic.

The new basis is not orthonormal. A=Z*.T Sscaled Z* must be paired with G=Z*.T Z*. Do not compare ordinary A eigenvalues to old QR eigenvalues. With B*=-D^-1 C_f, Gupper=1+||B*||1||B*||inf bounds ||G||2. Compute these from local/certified sparse bounds, not an unverified condition estimate.

## Interval Schur certificate: conditions that matter

Declare a symmetric represented target A0 explicitly, e.g. exact binary64 lower completion of the assembled Ahat. This is a diagnostic representative, not an averaged solver tangent. Bound the absolute difference to the original frozen constrained operator: local negative-resultant reduction/reconstruction, sparse-product accumulation, scaling, C leakage/exact graph correction, and upper/lower triangle discrepancy. Relative near-symmetry alone is not a sufficient error bound. If eS bounds the stationary operator defect and eZ the graph defect, a valid contribution is

(2||Zhat||eZ+eZ^2)||Shat||+(||Zhat||+eZ)^2 eS,

plus independently bounded accumulation/triangle errors. All terms must use the same scaled kernel coordinates. The old Frobenius/induced-one ideas are reusable; outward or exact local arithmetic must justify their upper bounds, including rounding in sparse products.

Certify A0-delta I by interval LDL/Schur elimination without pivoting. Start each entry as its exact stored value (and outwardly enclose diagonal subtraction). Maintain a symmetric interval for each pair. At each positive pivot interval, every product, quotient and subtraction must enclose the exact real update. Induction then proves all leading Schur pivots positive for the target, hence SPD. No heuristic width threshold or sampled entries may replace that complete proof.

LU may supply a symmetric permutation and fill candidate only. Verify permutation orientation (SuperLU old-to-new maps require inverse gather), every initial target entry, and every elimination neighbor clique against the pattern. If a needed entry is missing, refuse. Include all nonzero-width intervals even when their midpoint is zero; never drop generated entries merely because rounded cancellation gives zero. Arithmetic must handle negative intervals, division only by strictly positive pivot intervals, subnormals, overflow and outward sqrt/norm operations. check_arithmetic is a primitive control, not proof of the whole implementation.

If ||A*-A0||2<=epsilonA and interval elimination proves A0-delta I SPD, then actual kernel positivity follows when delta>=epsilonA. For a positive numerical lower margin use one preregistered choice such as delta=2epsilonA (outwardly rounded), giving a physical-scaled generalized lower bound (delta-epsilonA)/Gupper. With delta=epsilonA the proof is strict positivity but supplies no positive numeric lower margin from the shift alone. This conversion must appear in the report. A Ritz vector supplies a diagnostic/Rayleigh upper observation; Ritz-minus-residual does not prove the lowest mode.

Interval wrapping can make a positive matrix unresolved, especially at high condition/fill. Crossing zero, unavailable fill or exceeded arithmetic/work limits means HOLD/unresolved, not formulation failure; do not enlarge budgets or change scientific tolerances after seeing it.

## Inertia, facilities and economical crosschecks

For a declared symmetric stationary target, full row rank plus positivity on ker(C) implies reduced saddle inertia (p positive,m negative,0 zero). Add the locally certified negative resultant blocks to get full supported inertia (p positive,9t+m negative). Do not assign symmetric inertia to an unsymmetric stored matrix; quantify its relation to the symmetric energy representative and retain actual full/reduced solve, residual, work and response parity as separate obligations. Positivity of the entire physical S or complete K is not required.

Relevant existing facilities: ratio_kernel_dev.py local negative reduction/pullbacks (384–428) and conservative error terms (451–460); algebraic_dynamics.py coordinate-shear warning (1040–1055). Its _certify_spd (1687–1803) must not be reused as this gate: relative LDL reconstruction plus eigsh smallest-Ritz-minus-residual lacks the factor-conditioning/all-mode argument needed here. The synthetic _b3_e4_f03_sparse_positivity.py:124–142,183–227 provides a valid complete-residual/triangular-comparison proof concept, but its tiny scoped budgets/authority do not transfer. Its global comparison inverse bound can become extremely pessimistic; this is why interval Schur is a reasonable first implementation choice. No new dependency is needed: SciPy/SuperLU supplies candidate ordering only.

Before a large case, crosscheck the new graph on the saved625/1057 systems: complete CZ and rank, stationary work, generalized eigenvalues against existing orthonormal QR, shifted interval positivity versus dense inertia, and reconstruction of all three loads/retained roles. Include small negative controls: an inserted negative direction orthogonal to an eigsh start, a nearly singular local pivot, an omitted fill edge, and cancellation creating a zero midpoint/nonzero interval. These discriminate the dangerous shortcuts. Then one explicitly bounded largest-geometry sparse feasibility case can decide fill/wrapping practicality; do not launch the remaining matrix automatically. None of this changes multiplier norm criteria, seven ratios/three levels, physical acceptance, CalculiX/F03/G0 or different-family qualification.
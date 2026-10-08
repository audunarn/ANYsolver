# Experimental conservative accepted-state BL5 buckling

`GELineBucklingRequest` selects policy
`GE_Q4_BL5_ACCEPTED_CONSERVATIVE_MIXED_BUCKLING_V1_EXPERIMENTAL` through
the existing `owner.buckling` operation. `GEPointBucklingRequest` retains its
point-only meaning, controls and result schema. `line_buckling_capabilities`
reports definition admission separately from the elastic-interior material
witness validated during capture. This extends the same sparse descriptor
engine; it introduces no new static driver or multiplier-space selection.

Admission covers existing finite BL5 P0 and continuous-P1-coarse definitions,
optionally with existing six-pose points, objective elastic flat Q4 shells,
and generalized elastic-interior GE members with unchanged histories. Other
spaces, material branches, loads and attachments fail explicitly within this
current route; these limits do not permanently exclude programme obligations.
Actual compiled station operators must be BL5LocalOperator with complete finite
support maps and coefficient rows. Supports retain fixed translations and full
physical rotation triples. Loads retain conservative nodal dead translations.

At a compiled station the existing scalar work is `w (B lambda)^T c`.
`B`, reference-arclength weight `w`, port lift/frame and station geometry remain
the existing compiler's values. LocalWork gives zero-left-Exp derivatives
`g,H0,A`. The additive shell coordinate differential `D` contains the actual
`P(theta)` blocks; beam half-cell increments remain zero-left-Exp spatial.

The mechanical Hessian is `D^T H0 D` plus, for each shell rotation block,
`E - .5 P^T skew(g_rotation) P`, where
`E[j,k] = sum_i g_rotation[i] dP[i,j]/dtheta[k]`.
Equivalently pull back the spatial derivative `H0-.5 skew(g_rotation)`
at all three rotation blocks, add shell `E`, and restore the beam block's
`.5 skew(g_rotation)`. This is an exact chart transformation, without averaging.
The material crossblocks are `w D^T A^T B` and their transpose; the multiplier
block is zero. All station mechanical curvature belongs to the frozen-prestress
geometric block, including nonzero line multiplier curvature. Optional point
curvature retains its existing exact mixed-chart conversion.

The assembled conservative identity is
`H = Km + Gshell + Gbeam + Gpoint + Gline`, before and after support restriction.
All 42 variables/member and all point/line coefficients remain retained.
The material block is indefinite. The shared general sparse shift-invert solver
uses congruence scaling and checks original unsymmetrized mixed equations and
constraints at the unchanged 1e-8 criterion. There is no SPD whitening, static
condensation, artificial mass, dense production inverse or symmetry repair.
Returned factors scale frozen accepted prestress; they are not nonlinear limit
loads or a completeness/lowest-instability claim.

The distinct line result preserves coordinate/spatial mode and support-wrench
semantics. It adds owned line coefficient modes, basis-mapped station density
variations and actual gap variations. Station metadata records reference weight,
compiler beam-edge index, beam alpha and global multiplier rows. Densities and
raw coefficients are not labeled physical wrenches. Reference quadrature weights
are not current-arclength measures. All resultants remain available.

Boundary witnesses bind accepted history/checkpoint, compiled operators and port
lifts/frames, slots, weights, coefficient rows/basis, and owned recovery maps.
Iterative generation/pointer/cancellation checks remain constant-time. Recovery
maps and sparse arrays own byte-backed read-only data; mutations fail without
returning modes. Checkpoint formats and ordinary analysis routes are unchanged.

Focused development tests use three shell cells against four beam half-cells,
both existing admitted bases, nonzero rotations/multipliers, and an optional
point fixture. The bounded dense mixed oracle differentiates the local law's
direct additive-shell Jet2 path independently of the spatial pullback. Actual
`_advance` covector differences use three fixed steps `(3e-6,1e-6,3e-7)` and the
unchanged 1e-6 derivative plateau criterion. Tests also cover descriptor factors,
restart, ownership, stale generations, malformed/historical compiled operators,
material admission, mutation, cancellation and backend failure.
The direct scalar AD oracle now explicitly evaluates
`Exp(theta+dtheta) anchor`, including nonidentity accepted shell anchors and
the actual rotating native port lift. An owner rebase witness checks unchanged
physical frames/history, the covector and Hessian chain rule (including chart
curvature), restart parity and the same three-step actual-update criterion.
The same physical accepted state also requires pre/post-rebase finite-factor
invariance within 1e-9 relative error, with only a binary64 representability
floor, completed spectral calls, original mixed residuals at 1e-8 and unchanged
checkpoint bytes across each call.
A controlled nonzero-lift port uses `at_reference` to establish its own exact
stress-free arm/director map, then checks multiplier work and curvature against
the independent AD law and derivatives through actual finite-driver updates.
It is a local mechanics witness, not a changed model or reference campaign.

`scripts/r8_ge_line_buckling_dev.py --output <fresh-directory> --basis p0`
prepares one connected compression case. `continuous_p1_coarse` and tension are
explicit separate options, never an automatically executed sweep. The runner
records actual imports/threadpools/JIT, accepted checkpoint, sparse blocks and
owned recovery. Root supervises one job at a time with 600 seconds, 2 GiB,
one affinity, one numerical pool and JIT disabled. The implementation owner has
performed AST checks only. Root's source-v3 checks passed 41 executions in
19.37 seconds under
`.qualification/b3-ge-e4-pl/r8-ge-line-buckling-dev-20261005-v1`.
Source-v1's two test-fixture failures and v2's supervisor startup failure remain
preserved. Fresh source-v4 passed 45 checks in 28.96 seconds; installed-v4 passed
the same 45 checks in 26.48 seconds, including anchored/rebase/lift witnesses.
The installed P0 compression example completes with two finite factors
7436.23653335 and 40821.1606844, original equation/constraint residuals below
3e-16 and an unchanged accepted checkpoint. The wheel SHA256 is
7aa5b9f911cb9e506ca5d25fbbaaa063e8d18a1f450930061cb1dd18fe753777.
Supporting independent OpenAI full-slice and delta reviews leave no identified
defect; they do not supply different-family scientific acceptance. This remains
experimental development evidence; full G4B, external
acceptance, qualification and spectral completeness remain OPEN.

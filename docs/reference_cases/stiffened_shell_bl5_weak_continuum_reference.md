# Weak-P0 continuum director reference — development only

The new tool retains the SAME eight C3D20 bodies / 102 nodes / 306 translations
of the executed released-director reference. Plate 1 by .2 by .02 m, centered
y0/midsurface z0; bar .04 by .06 m, axis z.04, material frames I; E210 GPa, nu.3.
The full physical plate x0 face (13 nodes /39 translations) is fixed; no beam
support is added. Only +1 N global Fz at bar centroid tip (1,0,.04) is applied.
No density, mass or dynamic claim is introduced in this static continuum tool.

The original strong five stations/25 rows and new weak four supports/20 rows
share the SAME assembled full body K. Each element uses the existing independently
checked C3D20 shape/order, engineering Voigt xx,yy,zz,xy,yz,zx and isotropic D,
27-point integration. New assembly uses local 3x3 Jacobian solves and sparse
global accumulation of B.T D B. No global inverse, penalty, body condensation,
symmetrization or fitted elastic constant is used.

The continuum gap is beam bottom minus shell top (three components), then
beam material-director xy minus shell material-director xy, reconstructed from
opposite face-pair displacements divided by .06/.02 m. Independent directors
are NOT geometric normals. Face values use actual full C3D20 interpolation.
The native eight Gauss stations on four .25 m supports and weights .125 m are
used. Weak rows integrate ds*c, channel-major: position row units m2, director
row units m; their physical density multipliers N/m and N. Strong station rows
have m/dimensionless gaps and concentrated multipliers N/Nm. Native shell-minus-
beam gap has opposite polarity on the established common affine trace subspace.

KKT is Kq+C.T lambda_alg=f, Cq=0. Physical exerted interface forces are
-C.T lambda_alg. The previous strong recovery solves Cfree.T lambda=-[Kq-f]free,
which is the SAME algebraic sign convention. Root support is Kq-f-interface.
Native opposite-gap densities therefore have opposite signed coefficients for
the same physical common work. No algebraic multiplier is relabelled as a force.

Sparse general LU is applied to an indefinite KKT, after diagonal congruence:
dq=1/sqrt(Kff diagonal), dl=1/row_norm(Cfree*dq). These are numerical scales only;
q=dq*zq and lambda=dl*zlambda are reversed before all physical checks/actions.
Three bounded corrections use the unchanged sparse factor. No KKT SPD assumption.

## Prospectively fixed development checks and denominators

All displacement coordinate scales are1 m. Free-row rank uses constraint rows
divided by support length .25 m (mean gaps, model length1 m), and the standard
machine epsilon / matrix dimension numerical rank cutoff; report all minimum /
maximum singular values. Check rank20 and restraint of all6 whole-bar rigid
motions relative to the clamped plate. Unconstrained body rigid residual uses
max|K| times max(max|rigid field|,1), floor max|K|>=1 N/m; require<=1e-12.
Body skew is recorded/checked relative to max|K| with<=1e-12, never repaired.

Equilibrium uses the original `_linear_equilibrium` load-normalized norm and
active-load-row check<=1e-8. Gaps use the original scaling helper, support mean
rows for weak / unit length and director scale for strong, <=1e-9. Physical
global and body-cut wrench residual components normalized by the applied1 N /
1 Nm specimen lever scale must be<=1e-8. Work denominator max(abs(applied pairing),
1e-12 J), internal/applied and interface relative discrepancies<=1e-8.

BEFORE weak response reporting, reconstruct the strong25 system through the new
K, compare saved binary64 CCX U with denominator max(max|U_saved|,1e-12 m), and
original recovered internal covectors with max(max|g_saved|,1 N): both<=1e-8.
This is a DEV same-body operator reconstruction, not an accuracy/acceptance or
old/new-owner equivalence claim. Raw RF vs internal-root semantics remain the
prior executable-bound empirical observation; RF is not physical support when
interface acts at the root. All old bytes/source/evidence stay immutable.

Common-work controls use actual installed native BL5 C and genuinely representable
globally affine translations/material directors on both meshes; supported fields
have zero shell root translation/spin. Check signed integrated work, actual
constraint transpose, force/moment balance at common origins, compensated normal
spin and independent nonzero transverse shear. Local/structural fields are distinct.
Arbitrary independent native half-cell director sides still do NOT have a shared
continuum image; no averaging or missing-side substitution is introduced.

ONE ordinary bounded DEV batch:600s/2GiB tree, affinity1/pools1/JIT off/unforced
backend, pinned existing installed wheel/CI4 dependencies. One reconstructed
strong solve and one new weak solve; saved native calibration only read, never
rerun. No CCX/deck/refinement/F03/closed campaign. Source/runtime/input bindings,
JUnit/raw/failures must precede claims. Outcome pending checks; scientific
independent assessment, physical accuracy and convergence remain open.

Before the affected retry, root adopted an explicit helper interpretation
correction. V1's additional absolute2e-13 shifted-origin helper failed at
4.405364961712621e-13; BOTH solves were correctly withheld. Six prerequisites
passed, including rank20/bar rigid6 and common native weak work. This failed
helper remains FAILED. Stored-C/action force rounding transported by (7,-11,3)m
accounts for the amplified residual. The original pre-run physical gate1e-8 at
1N/1Nm floors governs the retry; no scientific tolerance is relaxed, matrix is
projected or empirical floor is fitted. Compare six whole-assembly rigid fields
at that origin through wrench(-C.T lambda)=-(C Vrigid).T lambda, retaining stored
coefficient residuals. Any gamma_n sum-of-products estimate is reduction-only
diagnostic, not a certified whole-chain bound (C construction also rounds).
Prior passes are reused by exact source/AST identities; the origin-zero prior
stronger helper pass implies the physical gate. Only the failed shifted-origin
control and still-unexecuted strong/weak checks rerun. Rank is restraint evidence,
not inf-sup stability or a qualified multiplier-space selection.

## Verified development outcome, 2026-10-06

All9 unique controls are satisfied using V1 six passes, V2 the affected shifted-
origin pass, V3 the two completed reconstruction/weak checks. Failed evidence is
unchanged: V1 one failed helper/two withheld setup errors; V2 two setup errors
from builtin abs on a serialized wrench list. The V2 strong KKT computation
reached equation/gap/work checks but was unvalidated/unpublished; weak was
withheld. The compatible np.abs repair preserves the physical gate. V3 repeats
that affected strong calculation and executes weak once. Actual compute inventory
is TWO strong calculations (one failed reporting), ONE weak solve, ZERO native
calibration/external reruns. Calculated-before-validation snapshots now explicitly
say CALCULATED_NOT_VALIDATED; validated result status is DEV, never acceptance.
Unchanged operator/test AST and prior JUnit/binding identities justify reuse;
origin-zero's prior stronger helper pass implies the original physical gate.

Free weak rank20: physically scaled singular min .40628258260327255, max
76.53588583226616. Whole-bar rigid rank6, minimum .49674447701726243. Body rigid
residuals 4.447337864623953e-16 (plate), 1.5450811873430476e-16 (bar). Actual
installed-native/common weak gap error1.1796119636642288e-16; virtual work
2.5167 J agrees within4e-15. These prove the declared affine common work and
rigid restraint, not arbitrary trace coverage or inf-sup acceptance.

Strong reconstruction of saved CCX U has relative discrepancy
4.1953276548028604e-10 (declared1e-12 m floor), internal action discrepancy
4.0699540221882284e-10 (1 N floor). Strong free equation ratio
3.4209236834107565e-10, scaled gap3.4761230599160033e-22, internal/applied work
discrepancy2.334662373390102e-10. Saved raw RF vs assembled internal-root maximum
2.5774937739697634e-11 N remains an empirical check; raw RF is NOT physical
support when the interface acts there. Prior root-interface/RF distinction is
preserved, and no response accuracy conclusion follows from reconstruction.

Weak free equation ratio3.280510607791814e-10, support-mean scaled gap
1.852523872454486e-22 (raw integrated4.631309681136215e-23), complete external
wrench residual max3.822755270982428e-10. Internal/applied relative work
discrepancy1.6792550469990966e-11; interface-work ratio2.862567646847619e-16.
Complete body cuts/actions/supports/displacements and signed density coefficients
are retained. The weak calculation passes the original1e-8/1e-9 gates.

Diagnostic tip centroid uz for the same +1 N Fz: reconstructed strong
4.791221833700107e-7 m, weak5.085776329850438e-7 m, SAVED native calibration
1.2775155904068065e-6 m. These are engineering observables, not an accuracy
score, converged continuum truth or a selected law/space. Weak reference uses
the SAME five-channel arclength work/supports as native on the common subspace;
full 3D continuum versus Q4/fibre beam primal spaces and the native independent
half-cell directors still differ. No empirical section changes are justified.

The pinned unchanged wheel is
`b3d5f572797f3c2954d1bf9dc1c6b4293da14c5812e543dbde7f314a60207291`,
with all424 installed Python module hashes verified. Actual imported ANYsolver
paths stay inside installed-s3-v1; numerical imports use CI4 NumPy2.5.3,
SciPy1.18.1, Numba.68.0, llvmlite.50.0. Runtime files record actual versions/
paths, pools1, Numba1/JIT off, affinity[0], OPENBLAS_CORETYPE unforced. This
does not claim general CI or thread/peak-memory qualification. The prior exact
Python314 WMI support classification is reused with local pyd SHA and primary
CPython source reference; total/support/original classifications remain sampled.

V1 supervisor3.3496991s / sampled182616064 B; V2 2.6710337s /183418880 B;
V3 2.5516805s /182792192 B. Numerical/unresolved maximum1 throughout; bounds
600s/2GiB tree. JUnit V1 1.185s, V2 .633s, V3 .466s. Resource sampling is not a
comprehensive peak/library-thread certification.

Raw root `.qualification/b3-ge-e4-pl/r8-bl5-weak-continuum-dev-20261006-v1`
contains source/test snapshots, bindings, immutable input/reference hashes,
operators, JUnit/runtime/stdout/stderr and all failure/reuse records. Successful
strong/weak/action/diagnostic records are in results-v3; V1/V2 stay failed.
Final source SHA256
`ecaedbab83249f46a390a4bb2bc0da269d54459f9d7722233b0675208cb8c645`;
tests SHA256
`dda3d809f3eab42def3cd22745ea13c15b3e80cdc0359d0a513d48554b1671e1`.
Final prose postdates executed bindings, and is not treated as an executed input.

Exact executed commands are Python314 run-v1.py/run-v2.py/run-v3.py in that raw
root, whose entries retain selections/environment and refuse reused output
directories. Reusable CLI is `python -m scripts.r8_bl5_weak_continuum_reference
--saved-strong <original-ccx-v1> --output <fresh-directory>` under the same pinned
runtime and bounded supervisor; this documentation does not authorize another
run. Existing trusted manifest SHA344c3587..., parsed SHAf0956217... and native
calibration SHAffdbe095... are explicitly pinned, not caller-asserted provenance.

The deliverable removes the strong25-versus-weak20 enforcement difference from
the reference comparison route. It supplies no automatic refinement, production
law replacement or physical acceptance. Root can now adjudicate body/trace-space
correspondence using these preserved observables; arbitrary broken native sides,
body/primal convergence, independent scientific assessment and accuracy remain
open. No frozen authority or historical failure is consumed or relabelled.

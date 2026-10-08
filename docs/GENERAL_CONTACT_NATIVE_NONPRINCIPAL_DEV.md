# Genuine nonprincipal native dynamics DEVELOPMENT candidate

**TESTED DEVELOPMENT at16dt1/256; retained4/8 totalH NONPASS.**
The corrective16 trajectory passed the unchanged normalized totalH1e-6 and
complete development gates through actual public8+8 segments. Local mechanics,
the prior exact4=2+2 restart and actual CLI checks passed. The original coarse
and fine trajectories remain NONPASS against totalH1e-6.
This candidate uses the existing public
single-native `solve_transient` and `TransientConfig`. No production module,
profile, defaults, controller, load admission or checkpoint schema changed.
The primitive independent reference imports only NumPy and elementary math;
it never calls a production force, tangent, inertia or recovery kernel.

## Physical input and scope

One straight element has nodes1/2/3 at(-.5,0,0),(0,0,0),(.5,0,0)m, reference
framesI, two affine zero-lift half-cells ell=.5m, no boundaries or loads. The
centered translational mass density is2kg/m; rotary density diag(.12,.17,.19)
kg m is positive and anisotropic. Declared generalized elastic moduli are
EA128N, GA32N and isotropic rotational modulus EI2N m2. These are explicit
constitutive inputs; `EllipsoidalGeneralizedSection` is the generalized law,
not a claimed geometrical elliptical section. The existing stable SO3 arithmetic
policy is explicitly selected, without changing its production implementation.

Initial physical cell spins are(2,3,4) and(-1,4,2)rad/s. Nodal velocities are
mean(cell spins) cross reference position. This breaks exchange symmetry and
dynamically excites the relative cell rotation and retained bending moments.
Both spins are body-nonprincipal. No initial rigid-top centripetal acceleration
is imposed: initial nodal acceleration is zero, whereas each cell has the
independently derived gyro acceleration -J^-1[omega cross(J omega)]. The
public owner resolves algebraic traces and rates under its existing contract.
Saved algebraic rate slots remain zero inertial placeholders, not trace rates.

Prospective coarse request is4steps at dt1/64s, horizon1/16s. Fine request is
8steps at dt1/128s with exactly the same physical inputs. The public trajectory
must demonstrate angle>=.2rad, relative cell angle>=.01rad, nonzero retained
moments and an accumulated rotation commutator>=1e-5. At each endpoint the
commutator uses Uc(t) Uc(0).T for the two cells; it measures noncommutativity
over the fixed physical horizon, so halving dt does not reduce the excitation
measure merely by shortening each increment. Both coarse and fine requests
retain these excitation checks. None is inferred
from a rotated planar/principal fixture or a local operator pose.

## Independent elastic elimination

For xL/xR and physical cell rotation U define d=xR-xL and
z=U.T d-ell e1. Axial/shear work is z.T diag(EA,GA,GA) z/(2ell).
The independently derived complementary bending work is
ell(|ML|2+ML dot MR+|MR|2)/(6EI); its inverse is
(EI/ell)[[4,-2],[-2,4]] tensor I3. This is the actual affine half-cell retained
contract, not textbook quadratic or Euler beam stiffness.

Let gamma=Log(U0.T U1). On the bounded branch |gamma|<.5rad the stationary
free nodal frames are U0 Exp(a gamma), a=(-1/4,1/2,5/4). The left/right
log strains are (gamma/4,gamma/2) and(gamma/2,gamma/4). Thus endpoint trace
couples vanish, central trace couples cancel, retained moments are
(0,3EI gamma/(2ell)) and(3EI gamma/(2ell),0), and eliminated bending work is
3EI |gamma|2/(4ell). This is a stationary small-relative-chart branch, not a
global uniqueness/minimum assertion across all SO3 branches. Independent full
trace work and native algebraic residuals/retained fields explicitly check it.

For n=diag(EA,GA,GA)z/ell and f=U n, physical node gradients are(-f,+f),
cell shear torque is -d cross f. The bending gradient adds opposite torques
-/+3EI U0 gamma/(2ell). These closed scalar-work gradients supply the oracle;
no production residual is used to construct expected values.

## Physical inertia and temporal reference

Each half-cell has the consistent P1 nodal translation mass
rho ell/6[[2,1],[1,2]] tensor I3 and physical rotary inertia
ell U diag(Jdensity) U.T. There is no frame mass, physical mass condensation,
hidden spring, damping or constraint. Angular inertia is I alpha +omega cross
(I omega), including genuine nonprincipal gyro work.

Independent midpoint unknowns are all15 physical accelerations. Stage positions
are x+.5h v+.25h2 a; stage rotations are Exp(.5h omega+.25h2 alpha) U; stage
velocity is v+.5h a. The oracle solves Mstage a+gradient(Ustage)+gyro=0 with
24Newton and12backtrack bounds. Only the reference Newton Jacobian uses
bounded central differences; force/torque values are closed work gradients.
Endpoints use the full increment and velocity+=h a. Initial, stage and endpoint
complete physical vectors, algebraic traces and retained fields are compared.

A separate unprojected-matrix RK4 semidiscrete ODE reference uses64and128
subdivisions per coarse step and verifies all common endpoint convergence<=1e-7 and rotation
orthogonality<=1e-9. It is a numerical semidiscrete reference, not an analytical
rigid Euler-top solution, continuum/spatial reference or certified floating
error enclosure. Its engineering response target is2% and must improve at
half dt. Its separate dimensionless response rows are position/L, SO3 relative
angle/(1rad), nodal velocity/(L sqrt29) and cell omega/sqrt29. Coarse and fine
responses use all four common physical endpoints, preserving units and horizon.
A closed analytical general elastic spatial solution is not claimed.

## Frozen dimensional criteria and potential method obstruction

Positive scales are length1m, spin sqrt29rad/s, acceleration29m/s2 or rad/s2,
force58N, moment5.51N m; initial independent kinetic energy is59/15J. Work/H
checks retain1e-5 and separate force/moment directional rows; discrete coupled
response, local force/moment equilibrium, retained fields and native/reference
accounting retain1e-6, including separate elastic and kinetic energy partitions
alongside total energy. Actual finite nonuniform arbitrary-axis pose checks are
local operator evidence, not an admitted transient initial state. Numerical
reference convergence and branch guards must pass before interpreting response.
The native inertia probe uses that finite rotated pose and compares every block
of the physical15x15 mass, including exact translation-spin and algebraic zeros,
and the complete M a+gyro vector. It does not rely only on rest-frame diagonals.

Energy drift target is1% with improvement at half dt. Total P/H conservation
checks remain1e-6; **their satisfaction is unverified and is a principal method
question at this noncommuting coarse step**, not silently assumed from old
commuting cases. Reports save all metrics/capsules before scientific asserts.

The existing spatial-omega midpoint/SO3 exponential update has an exact discrete
spin increment different from its linearized stage impulse. Write W=skew(omega_m),
p=I_m omega_m and A=hW/2. Then

    Delta Hspin = 2sinh(A)p
      + h/2 [Exp(A)I_m Exp(-A)+Exp(-A)I_m Exp(A)] alpha_m.

Subtracting h(I_m alpha_m+W p) gives leading
h3[W3 p/24+[W,[W,I_m]]alpha_m/8], generically nonzero. Constant symmetric
P1 nodal mass gives exact orbital increment h sum(x_m cross M a_m), so stage
wrench equilibrium does not remove this finite-SO3 defect. The oracle checks
that exact discrete angular increment separately, labelled numerical method
defect, never fictitious applied/support impulse. A failed strict H gate needs
lead interpretation/compatible boundary repair or a prospectively justified
new input; it cannot be regraded by the discrete comparison.
Each coarse and fine stage saves the exact numerical increment, linear stage
impulse, their finite-SO3 difference, cumulative increments/differences and the
observed endpoint-H accounting mismatch. The strict totalH1e-6 check remains
separate and is required on both trajectories. Exact numerical impulse
accounting does not imply that conservation passed.

## Public usage and prospective execution

    python -m examples.native_nonprincipal_dev

Prepared tests: `tests/test_ge_beam3_native_nonprincipal.py`. A module fixture
reuses one coarse public trajectory within a process. Fresh restart is4=2+2
with exact public result dictionaries and capsule bytes, not displacement only.
`NATIVE_TRANSIENT_RESULT_RECORD` optionally saves fixed-name raw JSON plus
capsules; ordinary pytest needs no environment path.
Completed public results/capsules are saved before independent-reference work
or scientific assertions, preserving them if a later check raises. The CLI
limits dt to1/64,1/128 or the explicit corrective1/256 and the horizon to1/16s,
emits a status record, and
returns a nonzero exit on a solver non-success.

The original unexecuted preparation recommended a separately
scoped240s allowance for three focused processes<=60s each
(local work+coarse response; temporal refinement; fresh restart), a<=20s public
CLI and40s repair/integration reserve. That historical proposal was subsequently
authorized for this fixture; its pre-measurement20s CLI recommendation was
prospectively changed to40s within the same approved60s/job and240s total.
Reuse a verified matching current artifact if all existing
package bytes match; these new example/test files need no product rebuild.
Lead must bind command/input/source/import/runtime evidence before executing.
The strict momentum-method question should be adjudicated before claiming a
passing full route; optional past scope residues cannot fund this fixture.

## Executed development disposition (7 October 2026)

Raw evidence is in C:/ANYworkspaceWork/contact_native_nonprincipal_20261006.
The five terminal attempts consumed exactly119.1498137001181 process-wall
seconds, leaving120.8501862998819 of the separately authorized240s. The40s
integration reserve was retained. No timeout, memory refusal, guard refusal,
product edit or rebuild occurred; the verified installed product was reused.
All executions recorded196 installed imports, JITdisabled, Numba1 and all
observed numerical pools1, with no runtime/import errors.

The original V2 local mechanics test passed. Its coarse trajectory completed
all4 steps, but the V2 check failed with KeyError('stage'): single-native public
rows store the full42 mixed increment and endpoint, rather than an original
stage record. That failed evidence remains nonprincipal_local_coarse_v2.
The V3b test repair reuses the SHA-bound completed4 result/capsule, reconstructs
all stage algebraics from the saved native increments, and reevaluates native
stage work/inertia. It uses production rotation/split_sum and a declared
binary64 acceleration rounding enclosure; no independent-reference fields
substitute for actual native stage data. Ordinary pytest still runs fresh.

New fine/restart solves observe the existing authenticated candidate_stage_audit
with a reversible test-only spy, returning each original audit unchanged. Saved
increment, predecessor, material, dt and epoch bind each captured stage to the
accepted public row. Fine captured/reconstructed consistency was1.80698e-15;
the explicit acceleration enclosure checks passed. Captured original stage
coordinates are distinguished from reevaluated native stage accounting.

Repaired coarse full-state and equilibrium/accounting maxima were9.67441e-13
and1.00658e-12. Fine maxima were2.00238e-13 and2.22189e-13. Local work/tangent
maxima were2.45379e-6 and1.91029e-6 against1e-5. Native rotated mass error was
1.38778e-16, with exactly zero cross/algebraic blocks. Exact public4=2+2
dictionary/capsule restart passed; the actual public CLI completed4 steps at
1/16s with total energy3.9361646555235783J.

Strict normalized totalH failed: coarse8.141713955288152e-6 and
fine2.0416609389404326e-6 against1e-6. Exact finite-SO3 impulse accounting
errors were at most1.67764e-16 per stage and1.67199e-16 cumulatively. The
observed angular change matches the finite-SO3 method defect while the linear
stage impulses remain at rounding scale. The approximately fourfold reduction
at half dt supports the predicted fixed-horizon second-order time defect for
this pair; it does not waive conservation or prove a universal convergence law.

Saved temporal metrics show reference convergence3.45445e-12; response maximum
0.0019808154324603903 decreases to0.0005022594954832697; energy drift
0.0007198276754856106 decreases to0.0001803555517275904. These measured metrics
meet their respective targets, but later temporal assertions were not reached
because the strictH assertion failed first. Both scientific tests remain FAIL.
No automatic refinement, altered physics/profile/default, scientific acceptance
or release is inferred. The next method decision belongs to the lead.

## One temporal correction V4

Following the measured finite-SO3 defect and approximately second-order H
reduction, the lead adopted one same-model, same-horizon correction:16 steps
at dt1/256, executed as an actual public prefix8 and checkpoint-resumed8. This
was prospectively source-bound and then executed as exactly two approved jobs.
The4/8 NONPASS fixtures and their original test meanings remain unchanged.
The example adds only this explicit timestep/count inventory; its default
request remains4dt1/64. No product/method/physics/default law was altered.

Prepared selectors are test_public_nonprincipal_corrective_prefix_eight and
test_public_nonprincipal_corrective_resumed_sixteen. The prefix tests full state,
equilibrium, accounting, strictP/H, energy, impulse and authentic capture
integrity at its half horizon. Full-horizon excitation floors apply to completed
16, including angle.2, relative angle.01 and accumulated commutator1e-5;
the half-horizon prefix is not reported as complete-fixture qualification.
Completed16 also must improve the measured8-step response and energy while
retaining every original meaningful gate. No expected-failure masking is used.

The original saved8-step record includes response/convergence metrics but not
full ODE state rows. The first segment regenerates only the unchanged128
subdivision ODE states once, reuses the bound64/128 convergence evidence, and
saves those states with its prefix. The second segment reuses that saved
reference and authentic prefix capture records; it does not repeat the4/8
native trajectories, the64 reference, local work or CLI checks. Ordinary tests
remain fresh and self-contained unless explicitly supplied authenticated saved
records. Deserialized ODE rows convert to arrays at the reference boundary.

Each segment is initially capped55s, inside the remaining120.8501862998819s
of the existing240s allowance, with at least10.8501862998819s held reserve.
Every previous charge is retained. Source/runner/manifests require exact review
and binding before launch. After a terminal prefix PASS, its result, capsule,
producer inputs/resource/runtime/imports are immutably bound before the second
segment. Captured stage increments/dt/epoch/material/predecessor and preserved
prefix journals prove the actual8+8 chain; no separate fresh16 equality run is
claimed. A failure or timeout remains evidence and authorizes no automatic
repeat, finer inventory or allowance renewal.

The prefix8 passed in44.87309310003184 process-wall seconds; the resumed8
completed16 and passed every final assertion in38.87476909998804s. All seven
terminal attempts now sum202.89767590013798s of240, leaving37.10232409986202s;
the held10.8501862998819s reserve was retained. No timeout, memory refusal,
guard refusal, additional fixture or numerical process is pending.

At full16, normalized totalH is5.108152488863217e-7 against1e-6;P is
3.607856700170062e-17. Complete state/equilibrium-accounting maxima are
3.312599237060881e-13/2.8573269290198036e-13. Exact finite-SO3 impulse errors
are2.1276671813119586e-16 per stage and3.4422005628812953e-16 cumulatively.
Response maximum0.00012603624368333867 improves the saved8 maximum
0.0005022594954832697; energy drift4.5115691231816134e-5 improves
0.0001803555517275904. All exposure floors pass, including angle.327565,
relative angle.194491,commutator.0746713 and nonzero strain/gyro work.

All16 genuine accepted stage captures bind the public journal and source.
Prefix genesis, first8 step/output dictionaries and restored predecessor are
preserved exactly;8 resumed captures have no overlap with the first8. Prefix
capsuleSHAc56142aa416b7abbbc949843b70a9e3e25e1d7d18710d0ea534452a6a819e889
and finalSHA daf10a3cfacdf439b8beb63635bc4b98a6c201e545d5e5840fc79bf147de1ced
are recorded with the immutable prefix binding. This establishes the actual8+8
chain, without claiming a separate fresh16 equality run. Both jobs recorded196
matching private imports, JITdisabled,Numba1,pools1 and no runtime/import errors.
Raw directories are nonprincipal_corrective_prefix_v4 and
nonprincipal_corrective_resumed_v4; frozen source/manifests and prior failures
remain preserved. This is bounded development evidence, with engineering
acceptance, widerC7 admission and release still open.

Remaining C7 obligations include general sections, connected/nonprincipal
multi-element deformation, nonzero lifts/eccentricity, load/contact coupling,
finite-relative-chart breadth and engineering acceptance. This candidate and
same-family review do not establish fullC7 or release admission.

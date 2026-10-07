# Genuine nonprincipal native dynamics DEVELOPMENT candidate

**Implemented, numerically UNVERIFIED.** This candidate uses the existing public
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
limits dt to1/64 or1/128 and the horizon to1/16s, emits a status record, and
returns a nonzero exit on a solver non-success.

No tests, CLI, builds or solver imports have run for this slice. A separately
scoped240s allowance is recommended for three focused processes<=60s each
(local work+coarse response; temporal refinement; fresh restart), a<=20s public
CLI and40s repair/integration reserve. This is a resource proposal, not a cost
claim or authority. Reuse a verified matching current artifact if all existing
package bytes match; these new example/test files need no product rebuild.
Lead must bind command/input/source/import/runtime evidence before executing.
The strict momentum-method question should be adjudicated before claiming a
passing full route; optional past scope residues cannot fund this fixture.

Remaining C7 obligations include general sections, connected/nonprincipal
multi-element deformation, nonzero lifts/eccentricity, load/contact coupling,
finite-relative-chart breadth and engineering acceptance. This candidate and
same-family review do not establish fullC7 or release admission.

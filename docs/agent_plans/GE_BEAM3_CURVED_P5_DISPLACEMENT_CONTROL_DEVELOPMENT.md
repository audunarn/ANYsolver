# P5 controlled displacement and reaction — development checkpoint

Parent: `3b23f5a3d7022e971c43067be0582ce8c17ccead`, tree
`f40e7d7eda86ef1177a06946cd1bdd77ea0b0ad6`. Adds only a research controller,
small tests and this record. All beam/section/local stationary operators,
continuation algorithms, archived proofs, production code and defaults remain
unchanged. The broader GE-B3 goal remains active and unqualified.

## Purpose and formulation boundary

The next critical-onset study needs equilibrium states at specified crown
displacements, not only the previous arclength-generated samples. The new
wrapper controls exactly one free Cartesian nodal translation. It does not
add rotational constraints, suppress a lateral eigenmode, diagonal-shift a
tangent, change material mechanics, or implement a general constraint API.

Every other free spatial DOF remains in the Newton system. Existing clamps
stay fixed. Other existing nodal dead forces remain fixed. At the controlled
coordinate, the internal force becomes the recovered reaction. The entire
assembled residual is then checked against that equivalent nodal force vector,
including all lateral coordinates, at the unchanged 1e-11 physical tolerance.
The final full tangent remains available for force-controlled stability
assessment; the displacement-control system's reduced matrix is not substituted
for the lateral stability operator.

An initial linear constraint predictor distributes the target increment through
equilibrium rather than moving only the control node. Subsequent corrections
hold its coordinate exactly. Both use the existing spatial residual derivative,
including its rotational BCH term. The reaction derivative is its scalar Schur
complement after eliminating the other free coordinates. For downward crown
drop d and downward force P, dP/dd equals this derivative because both signs
reverse together.

Only one Cartesian component is implemented; arbitrary vector constraints,
rotational control, MPCs, follower loads and beam-shell joints are not thereby
qualified. The controller does not claim general post-bifurcation branch
selection. A symmetric solution may remain an unstable spatial equilibrium.

## Transaction and execution controls

The wrapper owns a private copy of the assembly. All trial evaluations use
the same committed material origins. A converged trial remains pending until
explicit commit/discard. The existing all-element replay and internal-block
checks precede publication. Altered/stale trials, invalid targets and failed
solves cannot publish state. The caller's original assembly is not modified.

Target changes are limited to 1% of the assembly's reference length per trial.
One constrained predictor is followed by at most sixteen Newton correctors,
each with at most ten line-search candidates, inside the existing total budget
of 256 mixed evaluations per element. The existing relative-rotation limit
is retained. No automatic target cutback or failed-run retry is provided.
There is no OS process watchdog inside this small helper; any larger campaign
must use a separately frozen resource runner with whole-tree containment.

This uses the existing research material transaction protocol, not a new
production serialization/restart implementation. Its plastic test exercises
the existing restricted directed-hardening section law, not every nonlinear
material model required by the overall goal.

## Small-test evidence

The final suite passed **16 tests in 7.06 seconds**. It covers exact target
placement, reaction recovery, full equilibrium, equivalent-load replay,
unchanged caller state/clamps, independent finite-target-difference verification
of the reaction derivative to 1e-7, explicit pending/discard behavior,
zero-budget failure, mutated-trial rejection and invalid/bounded controls.

An elastic two-element load/unload cycle returned to the initial geometry and
rotations within 1e-10, with no acquired plastic history. A separate one-element
fully coupled 6x6 section fixture used the existing directed-hardening law:
target extension, unloading, reversal and discard exercised active plastic
stations and retained nonzero accumulated history. Accepted-origin replay
matched each committed response exactly. This is limited state-safety evidence,
not general plasticity or production restart qualification.

## Coarse turning-point smoke, not an accuracy claim

A two-element parabolic arch was advanced through ten explicit crown drops
0.005, 0.010, ..., 0.050. The command completed in about 7.47 seconds, with all
accepted-origin replays matching and physical residuals below 1e-11. It is
ordinary small correctness output in the task transcript, not an external
formal certificate or a consumed resource request.

| Crown drop | Recovered load | dP/dd | Lowest unscaled odd value |
|---:|---:|---:|---:|
| 0.005 | 0.013458382549325841 | 2.086875759890895 | 0.022959783819857887 |
| 0.030 | 0.03461956332301909 | 0.21739273418059435 | 0.01179560185013725 |
| 0.040 | 0.03572058237175315 | 0.020324140394421875 | 0.005342726204125858 |
| 0.045 | 0.035648788391434316 | -0.04639030847029613 | 0.0027845710466504864 |
| 0.050 | 0.03527962189507857 | -0.09928805107105276 | 0.0005984095489793493 |

Mixed evaluations per target ranged from 26 to 40. The largest reported
physical residual was 8.017095796807984e-13. The load slope changes sign while
displacement control continues successfully; the lateral values are retained,
not removed to make the nonlinear solve pass. This coarse model's load error
relative to the continuum is already known to be too large. Controller
convergence does not repair that approximation error or qualify the element.

## Next bounded gate

Prepare a fresh research critical-onset runner using fixed displacement
samples and bounded root location on multiple meshes, initially within the
existing explicit sixteen-element envelope. Freeze case, input-reference
hashes, interval/root rules, raw records and terminal distinctions before
requesting resources. Retain numerical sign uncertainty and mode information;
do not infer a first critical point from one sampled eigenvalue or qualify a
load error without an independently reconstructed reference comparison.

Use a fresh resource request and external output for any larger run; do not
reuse the consumed 16-element arclength request. Larger meshes, if needed,
require a separately tested explicit extent rather than bypassing the existing
assembly bound. No such request or larger critical-onset run was created here.

General nonlinear-section parity, broad curved/slender and spatial coverage,
physical mass/dynamics, prestressed modal, production interfaces/restart,
independent review, packaging and objective beam-shell connections remain
open. No push, merge, package/default change or activation occurred.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

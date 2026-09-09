# Native spatial nodal couples in actual Newton

Base `cc80def7e620c7015f2ee8394a98a922929cf475`, tree
`e06c617fdee3f3acdaa6fd82c43d40f322959aa1`. This private successor connects
the preserved spatial-couple virtual-work convention to the real native
force-control solver. It does not change physical beam/shell mechanics,
qualified Q4/S3, B2/B3, material laws, aliases, defaults or historical evidence.

## Exact four-path extent

1. `src/anysolver/_ge_beam3_native_spatial_couples.py`: exact owned couple
   patterns, one model/store scope, committed/native trial chart validation,
   external couple force/tangent and a bounded actual-solver entry point.
2. `src/anysolver/nonlinear_static.py`: candidate-only general matrix selection
   and external-force/tangent addition. Existing paths are unchanged when the
   private couple scope is absent. Internal responses are not relabeled as net
   forces, and no external couple is put into a constitutive energy.
3. `tests/test_ge_beam3_native_spatial_couples.py`: independent closed-Rodrigues
   virtual work, combined residual directional derivatives, actual torsion,
   biaxial bending, large common rotation, coupled curved plastic loading,
   connected shared-node loading, direct support reactions and failure guards.
4. This plan.

## Frozen work and chart rules

Import the preserved SpatialNodalMoments policy and analytic Exp-chart terms.
For additive incremental chart a about solver-owned committed rotation,
spatial virtual rotation is A(a) delta-a. Thus the external chart force is
A(a)^T m and its derivative is (dA/da)^T m. Do not use a fictitious -m dot log(Q)
potential or replace the derivative with zero in additive chart coordinates.
Constant spatial couples have nonzero work on a closed noncommuting SO(3) loop.
They do not grant conservative symmetry, energy or spectral authority.

Assemble each nodal couple once, including at shared nodes and constrained
nodes. Reconstruct chart increments from the actual store's committed native
view; issued trial views must match requested poses. Bind model, registration,
store, generation and immutable input signatures. Reject unknown nodes, changed
patterns, foreign stores and unissued poses. Discard uncommitted trials on
mid-evaluation failure and reset programme context in finally.

The real force controller must use GENERAL factorization and K_internal minus
the external chart tangent. Line-search and reaction calls use the same load
authority; reaction recovery at a committed pose has zero chart increment.
The already frozen objective reference-line force work and local static
condensation remain unchanged. Existing no-couple global outputs must remain
byte-identical to the prior archive.

## Scope, tests and limits

The actual wrapper inherits bounded standalone line-static controls: at most
16 elements/512 DOFs, one layer, supported homogeneous constraints, at most
16 increments and 24 Newton iterations. No arbitrary initial state, moment-
bearing restart, distributed couple, MPC, activity, dynamics or public routing
is authorized here. Result evidence explicitly binds moment policy, inputs,
nonconservative status and lack of restart/spectral/production qualification.

Require closed-Rodrigues work agreement and covariance/equilibrium at 1e-11,
and independent combined residual directional agreement at 1e-7. Verify actual
1.2-radian pure torsion, biaxial bending, large proper common-frame rotation,
coupled physical plasticity with line forces, root-couple reactions, connected
junction counting, general-matrix selection and unchanged failed-step history.
Do not tune coefficients or relax thresholds.

Separate inventories: three-node smoke; complete nodal-couple rehearsal;
existing line-global regression; Q4 ownership regression; frozen cycle A;
frozen cycle B. One numerical thread/child, 24-GiB process-tree memory,
600-second wall and 120-second CPU-inactivity supervision, at most three task
children, exclusive fresh outputs, no automatic retry. Freeze after rehearsal.
Two clean-head/configured-runtime guarded cycles must have byte-identical
scientific output. Preserve exact run commands, raw output and hashes externally.
Independent review remains PENDING unless actually obtained.

## Required continuation, not a workaround

Distributed couples cannot simply be lumped onto nodal loads. The preserved
retained physical station frames are U_cell R0(s); their virtual rotations
therefore load the internal cell rotations. Such nonconservative cell loads
require the correct unsymmetric internal Newton derivative and Schur reduction,
not the current conservative-Hessian-only static boundary. Preregister that
load/reduction successor and its independent checks before implementation.

Moment-bearing restart must bind complete line/couple path descriptions and
net spatial equilibrium. The line-only checkpoint contract must not be presented
as full provenance for a couple-loaded analysis. These remaining load/state
steps, general nonlinear sections and paths, mass/modal/buckling/slenderness/
engineering/package gates, independent review and the objective beam-shell
connection remain required for the full goal. No public activation is implied.

## Pre-closeout numeric-range correction

Preserve initial frozen c0ace9209d5835bc47308388b01586347287fa69 and both
successful 15-test cycles. A subsequent three-test finite-input range witness
failed: effective moment sums could overflow, chart-force norms could overflow,
and a combined line/couple load was not rejected. Finite components alone do
not ensure a finite convergence reference norm. These are guard defects, not
new mechanical equations; the initial freeze is superseded before closeout.

Reject nonfinite effective sums, chart forces/tangents and external force norms.
The combined-force guard is restricted to the private native line model; old
beam/shell routes are unchanged. No numerical threshold is relaxed or coefficient
tuned. Add the three rejection tests, rerun the complete revised 18-test suite,
freeze this same four-path extent in a successor commit and repeat two guarded
cycles. Preserve both initial cycles, the failed witness and corrected runs.

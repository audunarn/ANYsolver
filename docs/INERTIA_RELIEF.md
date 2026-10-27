# Linear inertia relief

`solve_inertia_relief` computes the constant rigid acceleration of a free body,
balances its applied load with mass-derived inertial loads, and solves for the
elastic deformation in the accelerating frame. It supports one connected
free-free linear beam/shell assembly, including homogeneous internal MPCs.

```python
from anysolver import solve_inertia_relief

result = solve_inertia_relief(model, load_case)
if result.converged:
    print(result.acceleration_at_center_of_mass)  # global m/s²
    print(result.angular_acceleration)           # global rad/s²
    elastic = result.recover()                  # existing stress/strain recovery
else:
    print(result.status, result.error, result.diagnostics)
```

The full signature is:

```python
solve_inertia_relief(
    model, load_case=None, *, reference_point=None, session=None,
    resource_config=None, cancellation_token=None, progress_callback=None,
) -> InertiaReliefResult
```

## Physical equations and coordinates

The six physical columns of `R` are ordered `Tx, Ty, Tz, Rx, Ry, Rz`. At reference
point `O`, a nodal acceleration is `a_O + alpha × (x - O)`, with nodal angular
acceleration `alpha`. Using the canonical assembled mass matrix:

```text
G = R.T M R
G a = R.T F
F_inertia = -M R a
F_effective = F + F_inertia
```

The reference defaults to the centre of mass. An explicit finite global
`reference_point=(x,y,z)` changes the reported translational acceleration and
moment reference; it preserves physical acceleration fields, inertial loads and
elastic strains. The solve uses a centred generalized-coordinate congruence of
the full coupled rigid-inertia equation, avoiding large global-origin moments.
Section rotary inertia, generalized-section mass coupling, point masses and the
model's consistent/lumped selection all enter the same `M`. In particular, the
default two-node beam uses its existing lumped formulation unless its section
selects `consistent_mass=True`. Inertia relief does not change that selection.

After homogeneous MPC reduction `u=Tq`, the existing augmented nullspace solve
enforces `Q.T q=0`. `Q` is an orthonormal gauge basis, and its coefficients are
not physical accelerations. Reported displacements describe elastic deformation
in this gauge; they do not include an integrated free-flight trajectory.

## Admission, status and recovery

Physical supports, nonzero affine offsets, constraints removing rigid directions,
disconnected/isolated nodes, solid models, native nonlinear configurations,
follower pressure and load-case-only `added_node_masses` are rejected with
`InertiaReliefError`. Attach physical point masses through `model.add_point_mass`.
The native-element exclusion does not exclude a reference-linear profile merely
because it shares a shell-family name. The current public S3 factory selects the
linear V2D profile; supply its authoritative `reference_normal`. Manufactured
shell acceptance covers that S3 profile and E4-PL Q4 elements. Dormant native
total-Lagrangian prototypes retain their exclusion.
Both declared and directly assigned point masses must be finite, nonnegative and
reference existing nodes. Total mass must be positive and all six rigid-inertia
directions numerically resolved. Semidefinite full mass matrices are permitted;
the algorithm never inverts the full `M`.

Numerical failure returns a nonconverged result whose `displacements` is `None`.
For example, `unresolved_elastic_stiffness` identifies an additional/negative/unresolved
elastic stiffness mode, or an unconverged bounded Lanczos classification. No
artificial support or physical stiffness is introduced to make a case pass.
The rank-six lift used by the classifier is solely a numerical spectral device.
The scaled elastic lower margin must exceed `1e-12`, with eigenpair residual at
most `1e-13`; a more ill-conditioned valid structure can therefore be refused.
The restarted Lanczos workspace is bounded to 256 columns (or the system size
when smaller), with at most 2000 ARPACK iterations. Actual operator-application
counts and the workspace dimension are reported; there is no fixed wall-time
promise, and every operator application observes cancellation.

`SolveCancelled` propagates from existing cancellation safe points, including
Lanczos iterations. Sparse third-party factorizations remain synchronous; a
pending cancellation is observed immediately after control returns.

`result.recover()` uses the unchanged source model and existing elastic recovery.
It refuses failed or stale results. There are no physical support reactions in
this profile. Internal MPC forces are available separately in
`result.constraint_forces`, computed against the effective load. The full
`K u - F_effective` may contain legitimate MPC forces; its reduced `T.T`
projection measures elastic equilibrium. Gauge multipliers and inertial loads
are not reported as support reactions.

## Numerical reporting

The result holds full read-only arrays for displacements, rigid accelerations,
applied loads, inertial loads and effective loads. `to_dict()` produces summary
metadata, including a result case with `analysis_type="inertia_relief"`, physical
accelerations, mass/inertia, reference point, resultants, diagnostics and backend.
The result case also records model revisions and deterministic point-mass and
constraint identity tokens, including direct point-mass dictionary changes.

Force and moment balance are reported separately about the stated reference,
with absolute errors and cancellation-resistant scales from the individual
nodal virtual-work contributions. Dimensionless balance, rigid compatibility,
stiffness-nullspace, acceleration backward error and displacement-gauge gates
are `1e-10`.

For physical-data elastic backward error, translations are scaled with the
radius-of-gyration length and rotations with one. With this diagonal `S`, the
reported error is

```text
||S (Kr q - T.T F_effective)||inf
--------------------------------------------------------------
||S Kr S||inf ||q/S||inf + ||S T.T F||inf + ||S T.T F_inertia||inf
```

Its gate is `1e-10`. The effective-load-only backward error and absolute reduced
equilibrium residual are also reported. When applied and inertial loads cancel
to rounding size (for example uniform free fall), dividing by `F_effective`
alone can give a large relative error despite a roundoff-sized absolute
residual. No load projection or artificial balancing correction is used.

`elastic_load_cancellation_ratio` gives the scaled effective load divided by the
sum of the applied and inertial load scales. A small ratio means a small elastic
signal is being obtained by subtracting large loads. The accepted backward error
is relative to those total input loads; it is not a guarantee of small relative
error in that small elastic signal or in recovered stresses.
No separate warning status is emitted for cancellation alone; callers inspect
the reported ratio when interpreting elastic stresses.

These diagnostics establish numerical solution accuracy for the supplied FE
operators. Mesh-discretization error, constitutive modeling accuracy and the
validity of a quasistatic accelerating-frame approximation require their own
engineering assessment. No centrifugal, gyroscopic, transient, contact,
nonlinear or prestressed equilibrium terms are included in this linear route.

## Repeated solves and scope of evidence

An `AnalysisSession` reuses canonical matrices, reduction and factorization.
Rigid inertia, acceleration and inertial loads are recomputed on every call.
Point-mass dictionary contents participate in mass-cache identity. Other direct
model edits retain the existing revision contract: use model mutation methods
or explicitly advance the corresponding revision after a direct edit.

Element activity retains its separate mass/load contribution policies. If those
policies differ, gravity loads and participating inertia can scale differently;
the acceleration reflects the actual assembled operators. No implicit policy
change makes them equal. The source implementation is covered by focused
analytical, independent dense-reference, lifecycle and refusal tests; it does not
broaden historical element qualification or authorize publication.

See `examples/inertia_relief.py` for a complete free bar example.

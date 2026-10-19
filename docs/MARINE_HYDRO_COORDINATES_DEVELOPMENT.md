# Exact equilibrium hydrodynamic coordinates

`anysolver.marine_hydro_coordinates` is a public development API
(`marine_hydro_coordinates_v1`). It supplies kinematics, work-conjugate pullbacks
and exact derivatives needed by six-DOF fluid integration. It does not admit
a BEM source, a physical motion envelope, a hydrostatic force-basis interpretation
or a runnable fluid contribution. Existing native jobs still refuse fluid inputs.

Each immutable `EquilibriumHydroFrame` records a stable body ID, equilibrium
mechanical origin r0, body orientation R0, coefficient axes E (columns in WORLD
axes), and material reference vector rho from that origin. For the current
mechanical state R=Exp(theta) anchor:

```
h = [E.T (r + R rho - r0 - R0 rho), Log(E.T R R0.T E)]
H = [[E.T, -E.T skew(R rho)], [0, inverse(Jl(hrot)) E.T]]
D = H B
hdot = D qdot
hddot = D qddot + b
b = sum_j (dD/dtheta_j) qdot_rot_j qdot
```

The numerical principal-log seam is refused within1e-6 radians of pi. It is
not a physical potential-flow validity envelope. No wrapping, projection or
orthonormalization is performed. Translational derivatives of D vanish; first
and second rotational derivatives include the moving lever, inverse-Jl chain
and mechanical-chart derivatives. Full original chart acceleration is retained
to avoid recovering it by subtracting large bias terms.

`evaluate_coupled(frames, states)` uses the explicit frame order and requires
exactly its unique body identities. Each body has surge/sway/heave/roll/pitch/yaw
coordinates. Full cross-body source matrices are retained. Derivative tensors
stay per-body rather than allocating an N-cubed global tensor. Inputs are
copied and output arrays have immutable backing bytes.

For a source covector in the h-gradient basis, `pullback_force(Fh, Ch)` returns
external Q=D.T Fh, WORLD wrench H.T Fh about the mechanical origin, and
K=-dQ/dq. Ch means -dFh/dh at the current source state. Total Fh includes the
reference buoyancy/preload baseline; K contains its geometric connection:

```
K = D.T Ch D - columns[(dD/dq_j).T Fh]
```

This does not justify treating a physical-wrench source stiffness as an
h-gradient stiffness; ADR-004 requires explicit source semantics and conversion.
Reference buoyancy, dry gravity and preload remain separate ownership records.

`pullback_added_inertia(Ah)` assumes a constant source matrix in h coordinates.
It returns positive INTERNAL Qint=D.T Ah hddot, Ma=D.T Ah D, geometric force
D.T Ah b, and complete analytic K=dQint/dq and C=dQint/dqdot. External inertia
is -Qint. The reported geometric force is already included in Qint and must
not be assembled again. No symmetry, PSD, regularization or scientific source
validity is inferred from arbitrary matrix input. Full coupled blocks survive.

The fixed development checks use independent SciPy pose/log and five-point
local time derivatives. Four cases cover equilibrium, the0.02-radian series
boundary, distinct current/equilibrium anchors, and a near-seam pose at zero
mechanical chart after recharting. Two-body cases check nonzero baseline stiffness,
WORLD/chart/source power and all K/C/Ma force derivatives with full12x12 coupling.
Reference/ordering/mutation/malformed-input/seam refusals are included. Initial
matching-anchor passes are preserved as limited evidence, superseded by distinct-
anchor coverage. No trajectories, random states or BEM solves are used.

Prospective criteria: pose/algebra/work/mass symmetry1e-10; derivative blocks
and coordinate-rate/acceleration reference1e-8, with separate unit floors of1
in the declared SI units. FD step1e-5 in each input SI unit; local time step1e-3s.
Force/moment and translation/rotation derivative blocks are checked separately.
These criteria are development evidence, not the full scientific W4 or W8-W10
acceptance. Evidence and remaining gates are recorded in ANYmarine/TASK.md and
`C:/ANYworkspaceWork/anymarine-evidence/hydro-coordinate-*`.

Review follow-through adds a separate mixed near-seam/nonzero-chart case and
an upper-triangular nonsymmetric source-matrix case. The latter proves algebraic
preservation without mirroring or regularization; it is not a physical added-mass
source. State-type, input-alias and direct duplicate-block refusals are covered.
All nine scoped tests pass in source and installed modes. Original/revised checks
total35pass executions across23measured attempts (including offline build/install
and import identity); the separate160s pool used92.38587659993209s. Independent
one-file mathematical and two-file coverage assessments completed with no
identified equation defect; review corrections and limitations are preserved in
the task note. Source/wheel/installed six marine modules match; headless import
loads no Qt/ANYhydro/Capytaine/viewer, and wheel metadata is MPL-2.0.

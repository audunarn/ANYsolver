# Standard element-edge beam-shell coupling

This note documents the standard (non-experimental) beam-shell coupling
boundary in ANYsolver: the adopted kinematic contract, the input admission
rules, the array aliasing and model-update semantics, and the force/moment
diagnostics conventions. The regression coverage lives in
`tests/test_standard_edge_beam_shell_transfer.py` and the COUP verification
cases in `src/anysolver/beam_shell_verification.py`.

## Routes

| Route | Element | Constraint source |
|---|---|---|
| Shared beam/shell node | none (DOFs already shared) | must not acquire a second constraint |
| One-to-one eccentric MPC | `elements.CoupledBeamShellElement` | `get_mpc_constraints` |
| Interpolated edge MPC | `mesh_gen.InterpolatedBeamShellMPCElement` | `get_mpc_constraints` |

## Kinematic contract (fixed common-offset map)

For an interpolated coupling with shell master nodes `i`, shape weights `N_i`
and a single stored offset `r` (from the shell attachment reference to the
beam node):

    u_b     = sum_i N_i u_i + (sum_i N_i theta_i) x r
    theta_b = sum_i N_i theta_i

For the one-to-one route `N_1 = 1`, giving `u_b = u_s + theta_s x r`,
`theta_b = theta_s`. The MPC is linear in the DOFs with fixed reference
weights/offsets and is enforced exactly by
`assembly.build_constraint_transformation`; the coupling elements contribute
zero stiffness (no penalty). Explicit offsets define the algebraic attachment:
they are an override and are deliberately not required to match the node
coordinate difference. ANYmesher owns physical projection and its tolerances;
physically matched records are verified in the manufactured-geometry tests.

Zero and negative weights are legitimate (quadratic edge shape functions can
be negative); a zero weight contributes nothing but its node must still exist.

## Input admission (fail-closed)

Both coupling classes validate their inputs at construction and revalidate
the mutable arrays at every constraint emission, so later corruption cannot
silently bypass admission. The following are rejected with `ValueError`
before any partial constraint set is returned:

- shape-weight array that is not 1-D with exactly one weight per shell master
  node (no silent `zip` truncation);
- non-finite shape weights or eccentricity/offset values;
- shape weights that do not form a partition of unity within the absolute
  dimensionless tolerance `COUPLING_PARTITION_OF_UNITY_ATOL = 1e-10`
  (`rtol = 0`, parent-adopted input-admission threshold), including a
  non-finite weight sum (finite mixed-sign weights can overflow the
  reduction to +/-inf or NaN). Weights are never renormalized;
- eccentricity/offset arrays whose shape is not `(3,)`;
- missing referenced nodes at emission time, including missing zero-weight
  masters and, for the one-to-one route, a missing beam or shell node.

The production constraint audit (`constraint_audit.audit_constraints` /
`require_valid_constraints`) wraps an emission failure as a `CONSTRAINT001`
error, so a malformed coupling makes the model invalid
(`ValueError: Invalid constraint system: ...`) instead of silently emitting a
partial constraint set. There is no coordinate-consistency rejection: an
explicit offset inconsistent with the node geometry remains a valid algebraic
input.

## Array aliasing and model updates

The constructors preserve array aliasing (`np.asarray`, no defensive copy):
mutating the caller's weight or offset array after construction is a
legitimate model update, picked up at the next constraint emission, and it is
revalidated then. The shell node id sequence is copied at construction.
Session fingerprints include constraint coefficients, so a refreshed
transformation after a legitimate update matches a cold session built with the
new values; the regression test drives a reused
`analysis_session.AnalysisSession.constraint_plan()` through separate
aliased weight and offset updates and asserts exact parity of the
transformation and offset against cold sessions, structure-key
invalidation, and rejection of a stale pre-update plan.

## Force and moment diagnostics

`assembly.compute_constraint_force_diagnostics` uses the raw residual
convention `K u - F` on the unreduced system:

- `mpc_slave_forces` holds the slave-DOF residuals (with zero coupling
  stiffness and zero displacement this is minus the applied slave load);
- `mpc_master_equivalent_forces` pushes each slave residual through the MPC
  coefficients, i.e. the transpose of the displacement map, with the same
  internal sign. For an applied slave wrench `[F, M]` the reported
  master-equivalent at master `i` is `-N_i [F, M + r x F]` (moments about
  each master node's own origin). The per-node couples are moments about
  different node origins, so their algebraic sum is not a global moment;
  the reported set is instead statically equivalent to the applied beam
  wrench: for any common reference origin `o`, `sum_i f_i = -F` and
  `sum_i [m_i + (x_i - o) x f_i] = -(M + (x_b - o) x F)` when the beam
  node sits at the physically matched position `x_b = sum_i N_i x_i + r`;
- `support_reactions` contains only fixed-DOF residuals and does not
  double-count the MPC transfer.

Transferred internal forces are not additional external loads. The
manufactured virtual-work oracle in the test module checks
`f_b . u_b = sum_i N_i (F . u_i + (M + r x F) . theta_i)` for arbitrary
admitted master fields through the production transformation, and
additionally contracts the actual reported master-equivalent wrenches from
`compute_constraint_force_diagnostics` with the same independent virtual
field (giving the negative of the beam-side work by the internal sign).

## Verification coverage

`tests/test_standard_edge_beam_shell_transfer.py` exercises the actual
production transformation and diagnostics (not a copied equation helper) with
independently written oracles, all dimensionless identity residuals bounded by
`1e-10` against separately stated translation/rotation/force/couple/work
scales:

- affine translation and rotation fields with the common offset (actual
  2-node linear edge weights `[1-t, t]` and 3-node quadratic weights,
  including negative and zero weights);
- infinitesimal rigid-motion consistency for a physically matched record;
- frame covariance under a rotated reference frame;
- invariance to edge/node ordering (reversal);
- a corner node shared by two edges with unique slave ownership, and the
  endpoint weight degeneration to the one-to-one map;
- the shared-node controls: the positive direct FEModel composition (a
  standard beam on a shell edge sharing the exact edge DOF mapping, with
  no MPC element or slave constraint installed) and the negative
  self-coupling rejection by the audit;
- wrench transfer, common-origin resultants from the actual reported
  per-node wrenches, support-bucket separation and virtual work (analytic
  oracle and reported-diagnostics contraction);
- fail-closed rejection of malformed counts/shapes/non-finite data/missing
  nodes through the production audit and assembly, with no partial emission;
- constructor aliasing, post-construction corruption rejection (including a
  finite weight array whose reduction overflows to NaN), and mutable-update
  refresh through a reused AnalysisSession versus cold-session parity.

COUP-012 in the verification catalogue covers the actual one-to-one
eccentric MPC affine-field reproduction; the interpolated edge route is
covered by the test module above and the COUP production-mesh cases.

## Nonlinear and contact reliability coverage

The standard connection has focused production-path coverage in
`tests/test_standard_edge_beam_shell_nonlinear_contact.py`. The fixture is a
qualified Q4 cantilever with a standard beam on an element edge and frictionless
rigid-plane contact acting on the shell. It covers shared nodes, one-to-one
eccentric MPCs and interpolated edge MPCs. It uses elastic material and
`von_karman` kinematics. Accepted fixture rotations are checked against 0.01 rad;
this is a test-domain bound, not a new public capability limit.

The tests compare production reduced force/tangent assembly with the full
assembly through the actual constraint transformation. Independent residual
central differences use the fixed perturbations 1e-4, 1e-5 and 1e-6; the two
smallest adjacent steps must meet the scaled 1e-6 tangent-error criterion.
Every perturbation preserves the actual weighted-pressure active mask and stays
away from first touch. Manufactured closed derivative states are local residual
checks; they are not accepted equilibrium states or penetration qualification.

A single staged press/release/recontact solve checks each accepted snapshot's
coupling and nonlinear equilibrium. The successful cycle uses a plane at the
reference shell midsurface, gap tolerance 0.001 and penalty stiffness 1e5. The
root can remain at zero gap with zero pressure when the free edge opens. Fixed
small in-plane loading exercises nonzero eccentric force/couple transfer.
Successful comparison solves use Newton tolerance 1e-10, keeping displacement
parity at rtol 1e-8 and atol 1e-10. Per-attachment analytic wrench transfer and
virtual work use actual nonlinear forces and a common reference origin.

Rejected trials retain the last accepted displacement, constitutive history and
checkpoint. Finalized qualified Q4 states add displacement-binding and integrity
metadata to raw snapshots; the physical history must agree exactly, and the
existing formulation validator checks the seal. Cancellation is injected after
an observed accepted increment. It checks the actual returned committed state
and reuses the same model after contact-scope cleanup. The observed fixture
backend is the mapping fallback; persistent-store cleanup also has existing
separate regression coverage. Split restart matches uninterrupted execution,
and valid weight/offset changes reject an incompatible checkpoint before Newton
iteration.

Completion and convergence are distinct in the existing result API:
`result.converged` also covers `stopped_at_limit`. Require `status == "completed"`
and the intended terminal load factor before treating a solve as reaching its
requested target. A stopped result can still contain a valid last accepted
state. The rejected-trial tests preserve that distinction.

Finite contact paths retain their existing zero-offset selector restriction:
weighted MPC rows, repeated selector columns and nonzero affine offsets are
refused. This unchanged guard was reviewed in source; this slice executes no
finite-rotation contact programme. Sharing nodes alone does not satisfy every
other admission condition of a finite contact profile. No rotating-offset
attachment, friction, plasticity or transient capability is established by
these tests. No measured accuracy, speed or convergence gain is claimed.

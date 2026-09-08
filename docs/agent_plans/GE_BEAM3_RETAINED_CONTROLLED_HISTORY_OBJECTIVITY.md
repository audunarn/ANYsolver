# Controlled generalized history and objectivity gate

Base: `05a6aae7a53e923611c1add31039336228a99d8e`, tree
`5f4696d3135388f445eb74fb1ed8bc30b6594c97`.
This gate adds tests/research fixtures only. No beam, shell, section, controller,
recovery, quadrature, tolerance, state schema, default or package changes.

Freeze the following standalone clamped-free specimens, each with 6 physical
DOFs/node and all mixed internal variables retained:

- Straight one-macrocell length-two bar. Reference triads have first director
  along x and second along z. Elastic diagonal (1000,400,350,0.8,1,1.2), identity
  yield metric, yield force 0.05, isotropic hardening 10. Axial tip-force pattern
  (1,0,0); displacement targets (0.00005,0.00015,0.0005,0.00045,0.0002,0,-0.0005,0).
  Compare the full path with the independently implemented one-dimensional
  return map and require plasticity and reversed plastic flow.
- Curved one- and two-macrocell beams. Nodes have x in [0,2],
  y=0.25*(1-(x-1)^2), z=0; frames use the analytical tangent and physical second
  director z. Use the existing coupled six-resultant section fixture, yield
  force 0.025 and its existing positive hardening. Tip-force pattern (1,-0.3,0.2)
  and its unit direction as the physical control row. Targets
  (0.005,0.02,0.08,0.079,0.03,0,-0.08,0). No distributed forces or couples.

For every accepted target: exact origin/predecessor continuity; nondecreasing
accumulated plasticity; immutable input model/state; force and moment balance;
physical load work; native recovery; independent 96-decimal primal section
oracle at every station. Require actual plasticity, unloading and reverse flow,
not merely an elastic path through a nonlinear adapter. Compare stress, plastic
strain, accumulated variable, incremental potential and dissipation to 1e-11
normalized error. Verify full-prefix restart is byte-identical and final-state
replay does not advance material history. At the peak, check the actual retained
spatial residual Jacobian by centered directional differences with fixed origins
and normalized error at most 1e-7; no numerical derivatives enter the element.

Test operator objectivity by superposing an arbitrary common rigid rotation
and translation on current nodal/cell frames and compensated positions, without
rotating reference geometry or material axes. Local station fields/history and
potential remain invariant; spatial residual/Jacobian transform by the explicit
mixed DOF map. Distinguish this from coordinate covariance, which rotates both
reference and current geometry, load pattern and control direction. The latter
maps global reference force variables in the first six retained resultants;
the twelve material rotational work variables remain unchanged.

For controlled curved histories, use two frozen coordinate poses: Rodrigues
axis (2,-3,4) with angle 2.1 radians and translation (16,-8,4); and an exact
proper cyclic coordinate permutation with translation (2^30,-2^29,2^28).
The dyadic geometry is preserved by the latter. Compare compensated positions
as exact dyadic sums, not by subtracting large rounded positions. Require 1e-11
normalized state, load-factor, field, reaction and work covariance. No claim is
made to recover reference geometry already lost when external coordinates were
rounded. Rehashed actual plastic origin/history mutations and cancellation on
continuation from an accepted plastic state must fail without publication.

Freeze before execution. Smoke the scalar/kinematic checks before larger lanes.
One thread, 24 GiB/tree, 600 seconds/child, 120-second CPU inactivity; at most
three children concurrently and 1800 seconds/wave. Preserve partial/raw files;
no automatic retry or consumed worker reuse. After complete rehearsal passes,
run two fresh-directory repeats and require identical canonical science.

Failure blocks this gate and is preserved; no tolerance relaxation, shortened
history or removal of failed cases to obtain a pass. This is not fibre-section,
arc-length, large-arch, shell-joint or full production qualification. Independent
review and complete environment attestation remain pending. The full goal stays
active. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

## Smoke-discovered protocol correction

Initial freeze `4a8748983d946fbd859cca815c35a709eb44556b` passed both
unloaded rigid-objectivity checks but failed the scalar unloading assertion.
The original axial step 0.0005 -> 0.0002 crosses the reverse yield surface;
its correct plastic increment is 4.558376629742179e-05, not zero. No actual
plastic controller campaign had run. Preserve the failed smoke as such.

Add an intermediate target 0.00045 for axial and 0.079 for the coupled curved
paths, so the explicit elastic-unloading check has a physical observation.
Every originally registered target remains, in order; no history is shortened
and no failed case, operator, load, material, tolerance or gate is removed.
The reverse-flow check moves to index six only because of the inserted target.
This is a new test/protocol freeze, not a retry of the failed frozen worker.
Initial smoke directory: `ge-beam3-controlled-history-smoke-smoke-o4bx6xtf`.

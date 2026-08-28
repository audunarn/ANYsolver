# Qualified Q4 vector-layer replay guard incident

## Frozen input and classification

- Candidate parent: `005d8a6ba32a0ed8888416d9c489b16d2540399b`
- Parent tree: `b90a6b11122bcc80e2c1a2093771df0665755e5d`
- Incident class: `REFERENCE_GUARD_CROSS_KERNEL_IDENTITY_DEFECT`
- Production disposition: `NO_Q4_MECHANICS_CHANGE`

The exact-source ANYfem suite supplied an accepted vector-produced Q4 state for
which a later scalar replay did not reproduce `layer_strain` byte for byte.  The
seal rejected the state with `qualified Q4 accepted algorithmic origin does not
reproduce committed layer_strain`.  Focused scalar witnesses had previously
passed, so they did not establish a scalar/vector binary64 identity.

This is a guard identity defect, not a constitutive contradiction.  The
registered vector producer computes layer kinematics through leading-batch
matrix products.  The scalar shell replay uses a different operation shape.
Mathematical equivalence does not authorize cross-kernel byte equality.
This record supersedes only the V2 incident's statement that a vector producer
retains exact *scalar* replay of `layer_strain`; all other V2 authority remains
in force.

## Authorized correction

For a state carrying `Q4_VECTORIZED_ALGORITHMIC_PRODUCER_ID`, the seal replays
only the kinematic `layer_strain` through a guard-local copy of the registered
vector operation order: one-element batch allocation, `T0`, `Gw_all`,
`B_m_all`, `B_b_all`, and the admitted Lobatto coordinates.  Equality remains
exact binary64 equality.  A one-ULP mutation remains a hard failure.

The scalar replay remains authoritative for force and tangent reconstruction.
Scalar and legacy state producers retain exact scalar checks of
`plastic_strain`, `alpha`, and `layer_strain`.  Vector-produced plastic and
alpha histories remain closed by their registered accepted-core digest and the
outer committed-state binding, as established by the preceding V2 incident.

The correction does not change `vectorized_nonlinear.py`, plasticity, forces,
tangents, coefficients, tolerances, recovery, quadrature, or physical state
laws.  It authorizes only the guard helper, focused exact witnesses, and this
record.

## Required regression evidence

- Exact vector helper equality for square, skew/warped, and rotated frames.
- Exact rejection of a one-ULP committed-layer mutation.
- The complete current-tangent guard suite.
- The three ANYfem capacity workflow nodes that exposed the incident.
- Frozen Q4 mechanics and vector-producer blobs outside the guard path.

# G1a exact-elastic extension and G1 resumption

Frozen design; implementation and scientific acceptance are separate.
Parent: `7b747da8f4371015fe10d5fd83b18a638816ec61`.
Inherit the static integration contract at `51ebc3c07dc218ba7a78eb71c49f3f5fde829587`
and its S01-S08 gate, without editing either historical document or evidence.
User authorization: review/freeze G1a, implement it, then resume G1.

## Reviewed resolution

Introduce additive private modules only. Keep all existing runtime files,
type guards, qualified beam/shell mechanics, identifiers and defaults unchanged.
No aliases, public exports, versions or publication. New identities:

- `GE_BEAM3_G1_LINEAR_ELASTIC_SECTION_V1`
- `CANDIDATE_GE_BEAM3_G1_ELASTIC_RETAINED_V1`
- `CANDIDATE_GE_BEAM3_G1_ELASTIC_STATIC_V1`
- `GE_BEAM3_G1_ELASTIC_RESTART_V1`

The extension has exactly linear material response, not linearized geometry.
It must never import ellipsoid/fibre laws as material substitutes. Reusing the
existing pure geometry/AD/chart/load primitives is permitted. All history for
this law is the empty tuple; internal forces and physical cell rotations are
nevertheless authoritative state. No yield parameter or fabricated inertia.

## Equation map

E1: `s=C e`, `psi=e.C.e/2`, `Psi*=s.C^-1.s/2`, tangent C. C is the validated
SPD matrix in existing beam-section ordering. Isotropic diagonal is
`[EA, k_y GA, k_z GA, GJ, EIy, EIz]`; explicit axes and coefficients required.
External section conversion captures the existing validated matrix and a stable
descriptor; it does not retain a mutable external constitutive object.

E2: Per quadrature station use the unchanged reference map V=R0.T/J,
measure w>0, and moment interpolation N(t) over the two centered half-cells.
Let x contain all independent three-component station forces and p contain six
cell forces plus twelve endpoint moments. Let A assemble w*C^-1_nn, D assemble
w*C^-1_nm*N, F assemble w*N.T*C^-1_mm*N and B assemble w*V.T into the two
cell-force balances. Solve `[A,-B.T;B,0] [x;lambda]=[-D*p_m;p_f]`.
For the resulting linear lift x=X p, the complementary matrix is
`S=X.T*A*X + X.T*D*P_m + P_m.T*D.T*X + P_m.T*F*P_m`.
Check symmetry/SPD; do not repair a failed matrix by clipping. Use factorizations.

E3: Retain the existing centered geometry expressions, including compensated
strain and endpoint relative SO(3) logarithms: `Pi=p.k(q)-p.S.p/2`.
First/second variations use existing analytic Jet2 primitives, not numerical
frame differentiation. Full layout is 18 external, six cell rotations, eighteen
resultants. Physical recovery uses x=X p and station moments, not displacement
differencing. Reference/current station frames remain explicit.

E4: Subtract the unchanged reference line-force work. Spatial distributed
couples act on internal cell rotations by integrated reference measure. Their
residual has no scalar potential; preserve its nonsymmetric spatial derivative.
Reuse pure `spatial_jacobian`/`chart_pullback` expressions without altering the
guarded old static solver. Add a new exact-type bounded local reduction. Retain
the nonzero internal-residual Schur correction and back-substitution.

E5: Integrate via existing Element/NonlinearStateStore/native material protocol
and actual reference assembler, not an independent state owner inside elements.
Validate issued token, previous hash, accepted pose, empty material history,
local residual and captured definition before global atomic commit. At most two
elements; zero supports, complete rotational triples, fixed graph, elastic law
only. General MPC/mixed families remain G2+. No dynamic or mass claims.

E6: Restart envelope binds exact definitions, ordered graph/fixed DOFs, committed
state/load sequence, source digest, shared SO(3), internal coordinates and state
hashes. Require externally supplied SHA-256 and replay the accepted steps from
virgin state; compare canonical committed payloads. Reject altered definitions,
noncanonical/duplicate/nonfinite JSON, missing/foreign history, unknown family,
excess size and cross-version source digests. Exclusive same-volume staging and
atomic no-overwrite publication; failed staging never replaces an old checkpoint.

## Paths and fixtures

Add only the four private modules `_ge_beam3_g1_elastic.py`,
`_ge_beam3_g1_operator.py`, `_ge_beam3_g1_element.py`,
`_ge_beam3_g1_analysis.py` under src/anysolver; tests
`test_ge_beam3_g1_elastic.py`, `test_ge_beam3_g1_integration.py`; runner
`scripts/run_ge_beam3_g1.py`; this contract, its JSON binding/review and a later
G1 status document/result. Any old runtime edit needs successor review.

Fixtures: straight nodes at x={0,.5,1,1.5,2}; second element roll .37 rad;
isotropic E=100,G=40,A=1,Iy=.2,Iz=.3,J=.1,k_y=.8,k_z=.7;
dense SPD C=L L.T with diagonal L={10,9,8,7,6,5}, strict lower entries .2;
Q2 geometry transformed rigidly and connectivity reversed. Four stations per
half-cell. Nodal test force (.01,-.02,.015), moment (.002,.003,-.001);
line force (.01,-.02,.005), distributed couple (.001,.002,-.001).
Use scales length=1, force=1, moment=1 for these nondimensional fixtures.
Existing G1 errors 1e-11 invariants and 1e-7 tangent checks are unchanged;
directional steps {1e-4,1e-5,1e-6}, all registered checks must pass (no best-step
selection). Local and global residual <=1e-11, maximum 24 Newton iterations,
up to 9 backtracking trials, local elapsed bound 60s. Existing SO(3) bounds stay.

Independent test equations reconstruct station constrained minimization without
the producer's compiled matrix, and compare full stationary elimination to
the condensed solve. Material direct equations are not a production-matrix
oracle. Geometric and assembly tests include frame/work, tangent, shared Q,
rollback on second-element preparation failure, stale/concurrent tokens,
changed input rejection, recovery and restart replay/publication faults.

Execution remains one thread, 24 GiB/tree, 600s/child, 1800s/wave, at most three
children; inactivity120s, no automatic retry. Run smoke then rehearsal. Freeze
candidate/test hashes and obtain independent implementation review before two
formal cycles. Primary-agent design review is not independent scientific review.
No formal acceptance is claimed merely from passing development tests.

Next after successful G1 implementation/review: recommend G2, do not execute it.

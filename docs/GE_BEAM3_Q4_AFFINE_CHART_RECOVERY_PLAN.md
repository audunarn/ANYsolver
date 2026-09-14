# Q4 affine chart-image physical recovery — exact-gate contract

This recovery-only successor contract requires independent review before
implementation. It is not execution authority or accepted MO16 evidence.
Base47e84f0a58585bdad5ca69c82a993cb34ba11cbe.
Preserve the natural retained-space audit at d0057065
and its genuine NO_GO; do not revise public Q4 mechanics or qualification.

## Scope and identities

Recovery identity: GE_BEAM3_Q4_AFFINE_CHART_PHYSICAL_RECOVERY_V1.
Keep the actual finite local potential, force, tangent, qualified coefficients,
PL/hourglass terms and Procrustes chart unchanged. No public recovery API,
default, restart routing or historical identity changes. A later mixed-owner
successor must bind this recovery identity explicitly and reject old packets.

Admission is the frozen G3c planar affine-reference, homogeneous virgin scalar
elastic Q4 scope. Existing graph Q4s are the unit square in J_Q4_PAIR and 2x1
rectangle in J_MULTIFAMILY_LOOP, both at z=1/8. Their five registered variants
preserve reference affinity. Current nodes may warp: only reference affinity
and smooth admitted Procrustes fit are used. Nonaffine reference, generalized
or history-bearing sections, offsets, loads and unrestricted parity remain open.
No new rejection can be silently treated as full legacy parity.

Source authorities inherited from the coefficient-audit plan remain immutable:
e4_pl_element.py, elements.py, local shell chart, matrix-shell contract and MO16
assessment. Bind ge_beam3_g3c_fixtures_v1.json SHA-256
d5fecc80c3203ac7d191b4031d64bf35c56d2900066cb01fc1dfa4276d24c006;
_ge_beam3_g3c_definition.py SHA-256
4b46b870fec010e3378df83c374d763f858d8f25820c14f9704dc6f0a656f0c2.
All source hashes are LF-normalized, as in inherited authority.

## Physical fields and exact obligation

Let M_g d be the actual recovered mixed-linear eight-component strain in the
Equation-7 frame, obtained through the existing linear stationary solve. Let
n_g(d) contain only the compatible quadratic membrane strain, correctly
transported from the inherited centre frame. Define

    e_g = M_g d + n_g(d),    s_g = C_g e_g.

These are material constitutive fields. They are NOT Nsigma beta_linear, and
are NOT asserted to solve the rejected natural nonlinear 35-variable system.
Retain the old independent mixed stress as separately named diagnostics only.
Never contract the new resultant through Bcompatible+Bnl: its differential is
M_g + Dn_g. No signed diagnostic sum or projected nodal-force surrogate is used.

The source physical potential is

    Uold = .5 d^T Kphysical d
         + sum_g w_g [ecompatible_g^T A n_g + .5 n_g^T A n_g].

First prove the linear strain-energy/Schur identity. Then prove

    Phi(d) = sum_g w_g (Mmembrane_g d-ecompatible_g)^T A n_g = 0

on the actual Procrustes chart image. For affine reference geometry, centered
local translations and symmetry of the position/reference covariance define
six linear constraints. Use a deterministic exact nullspace Z for these
constraints, with all local rotation coordinates retained. Independently verify
Phi(Z z)=0 coefficient-by-coefficient; do not infer it from sample poses.
The proof must check rank of the constraints, positive reference station
weights, frame transports, engineering shear convention, and image membership.
The global fit must remain on its existing simple-top admitted branch.

The consequence is Uold=.5 sum w e^T C e ON the chart image, not throughout the
unrestricted 24-dimensional local space. Verify the full identities

    D^T grad(Phi)=0,
    D^T Hess(Phi) D + sum_i Phi_,i Hess(d_i)=0.

Numerical implementation retains actual old local force/tangent. Recovery work
and full chart Hessian must independently match them through the complete chart;
do not replace an off-image local operator or omit its force-weighted Hessians.
PL and hourglass energies/forces remain separate numerical diagnostics and are
excluded from these physical resultants, section checks and recovered energy.

## Stationary interpretation requiring explicit review

A possible independent station representation is

    L(d,e,s)=sum_g w_g [.5 e_g^T C_g e_g
                       + s_g^T(M_g d+n_g(d)-e_g)].

Stationarity gives e=M d+n and s=C e. Its full station saddle system and Schur
derivatives can be reconstructed independently and condensed exactly. This is a
NEW explicitly identified recovery representation, not the original 35-variable
pair. It does not erase the need to verify the original linear internal system.
Review must decide whether this source-derived representation discharges the
required stationary physical virtual work for this admitted scope. It must not
be accepted merely because it can express an arbitrary fitted energy.

There are 64 internal variables, eight strains and eight multipliers at each of
four stations. In (e,s) order the station internal Hessian and two-sided inverse
are w[[C,-I],[-I,0]] and (1/w)[[0,-I],[-I,-C]]. With J=Dq(Md+n), the condensed
physical force is sum w J^T s and its tangent is sum w[J^T C J +
sum_a s_a Dq^2(Md+n)_a]. Verify full-system stationarity and Schur in the common
external chart. No old local-d Hessian equality is asserted off the image.

The source stationary 35-variable system remains separately reconstructed for
the linear M map and linear physical energy. The new 64-variable representation
must carry its own ID, GE_BEAM3_Q4_AFFINE_STATION_RECOVERY_64_V1. It never rewrites
the historical internal system or claims acceptance of its rejected enrichment.

## Complete recovery obligations

1. Exact affine image constraints, rank/nullspace and source linear Schur/strain
   identity; all cubic/quartic coefficients of Phi on the image; station saddle
   and Schur equality. Include square, rectangle and rational affine skew.
2. Native recovery against an independently authored source-equation checker:
   zero, checkerboard transverse, membrane/bending/shear mixed poses, independent
   accepted/trial noncommuting rotations, every frozen graph Q4 variant.
3. Energy, constitutive consistency, station work, actual full chart force and
   Hessian; six rigid modes, common motion, D4, director reversal, passive frame
   transport, same-pose rebase and physical tensor/resultant provenance.
4. Negative/mutation guards for frames, weights, strain/resultant distinction,
   gradient and force-weighted Hessian terms, numerical-energy leakage, nonfinite
   data, definition changes, mutable returns, old identities and unsupported
   section/geometry. No normalization floor may hide tiny-energy differences.

The numerical recovery implementation and its complete named inventory must be
frozen after the fatal exact gate below passes. No numerical production adapter
is implemented or executed by this first exact-gate contract. Reuse the shared
qualification runner and completion register. Keep exact, inert,
numerical, smoke, rehearsal and formal inventories separate. Run smoke, one
complete rehearsal and two fresh formal cycles; require identical canonical
science and independent evidence acceptance. Max3 workers,1 numerical thread,
24GiB/child,600s/child,120s inactivity,1800s/wave; no automatic retry.

## First fatal gate: frozen exact fixtures and nodes

Gate identity: q4-affine-exact. This is the next gate, not the full recovery gate.
Use E=100, nu=1/4, thickness=1/10, director+Z, at four Gauss stations in inherited
registered order. All coordinates below are rational and have z=1/8:

- AFFINE_Q4_SQUARE: (0,0),(1,0),(1,1),(0,1).
- AFFINE_Q4_RECTANGLE: (0,0),(2,0),(2,1),(0,1).
- AFFINE_Q4_RHOMBUS: (-8/5,-4/5),(2/5,-4/5),(8/5,4/5),(-2/5,4/5).

First two reproduce graph reference shapes; the rhombus is additional skew
coverage, not a substitute for the graph inventory. Derive both source frames,
station Jacobians/weights, section C, original mixed stationary system and M
independently in producer/checker. Share only exact arithmetic and canonical IO,
not mechanics assembly. Exact field remains Q(sqrt2,sqrt3,sqrt5), with the eight
basis masks of the accepted coefficient audit. Reject any unrepresentable root.

Constraint rows are mean-zero x,y,z followed by covariance-skew xy,xz,yz;
columns use the original24 nodal DOFs. Leftmost-pivot exact RREF determines Z:
free columns ascending, each free coordinate1 and all other free coordinates0.
Require constraint rank6, Z shape24x18 and exact Cconstraint*Z=0. Confirm all
12 rotations are unrestricted; do not apply an energy-tuned complement.

Proof includes all1140 ordered degree3 and5985 ordered degree4 monomials in18
reduced variables per fixture:7125 per fixture,21375 total. Compare energy
difference polynomial, not just Phi if implementation reconstructs it another
way. Quartic cancellation must be explicit, not dropped as presumed. Include
complete24x24 linear physical operators, station M maps, frames and weights,
constraint/RREF/Z, all64-variable block/inverse factors and exact Schur checks.
Preserve a first nonzero witness in fixture/degree/lexicographic monomial order.

Registered tests, ordered:

1. test_affine_exact_arithmetic_and_schema
2. test_affine_source_and_representation_boundaries
3. test_affine_square_chart_polynomial
4. test_affine_rectangle_chart_polynomial
5. test_affine_rhombus_chart_polynomial
6. test_affine_stationary_schur_and_mutations

Smoke runs only1-2; complete rehearsal/formal runs all6. Each full fixture gets
two fresh independently authored checker processes; require byte-identical
checker outputs, then two formal scientific cycles. Parent and checker children
stay inside the shared three-worker cap. Reconstruct a protected independent
baseline once per fixture for mutations; do not solve repeatedly per corruption.
Mutate geometry, frame, weight, M, n, constraint, Z, station coupling sign,
inverse, coefficient, identity and bound hash; require rejection by actual
checks, not only a final summary flag. Audit cardinality/duplicate keys/nonfinite
JSON and nested artifact hashes. All arithmetic evidence remains external except
canonical reviewed manifest/status; no public mechanics imports are allowed.

Exact-gate terminal precedence:
1. BLOCKED_G3C_Q4_AFFINE_RECOVERY_PROCESS_OR_EVIDENCE
2. NO_GO_G3C_Q4_AFFINE_RECOVERY_VARIATIONAL_IDENTITY
3. UNCLASSIFIED_G3C_Q4_AFFINE_RECOVERY_EXACT_IDENTITIES_ONLY

Even all-zero proofs leave physical_recovery_qualified=false and
full_g3c_qualified=false until actual numerical/work/state gates and independent
acceptance. A negative affine proof preserves its contradiction and requires a
reviewed correction or private successor, never threshold/case relaxation.

## Adjudication boundary

Malformed evidence/process failure blocks this gate. Any exact coefficient,
constitutive, force, tangent, covariance or state-safety contradiction is a
genuine recovery NO_GO. Success accepts ONLY affine chart-image physical
recovery under the registered scalar virgin scope. It is prerequisite evidence,
not full MO16/G3c, material parity, activation or public Q4 requalification.
If the required stationary interpretation is incompatible, preserve the finding
and separately preregister the permitted private variational Q4 successor.

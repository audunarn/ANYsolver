# Distributed spatial-couple static-reduction development gate

Base: 9346ce821d998f47cb0a992b7782eb8c572d3c68. Four additive paths:
this plan, the private distributed-couple module, a separate closed-equation
oracle and its tests. No existing mechanical source, section, state schema,
public element, alias, default, version or qualification evidence changes.

## Bound source map

These existing blobs at the base commit remain unchanged:

| Source under src/anysolver | Git blob | Working-file SHA-256 |
| --- | --- | --- |
| _ge_beam3_retained_fibre.py | 11e22dbdf6e7142237acd84c1ef01b7d0d59ed46 | B484E356A4ACFA681647B669FBCE51985BD56919A7356E23437E75D947561EE9 |
| _ge_beam3_fibre_static_boundary.py | 158c7c4a172672da2828f132ba093992ddc70362 | 3BAE4C1D1457BA9C3E284C9C33A254BCE5A150547616FDE8392299CB91D65057 |
| _ge_beam3_fibre_line_work.py | e5eb23de10116fbc3480c7b6156360b897bb7090 | 26FF303007822E32F3E3EA77E96985BA0D51C85FD17BDFF6FFB1E6D05DEAD791 |
| _ge_beam3_p5/chart.py | c94e6f8bc3f19cb5c45dc9bd65f71d7a2ef5e1b5 | 785AFE1F3FECCB325CFE7F2B5B5A5C41357D1BDF60B78F4C72F750638F3FC35A |

The retained operator's recover() defines the physical station frame as
Q(s)=U_cell R0(s). With spatial multiplicative cell variations,
delta Q Q^T = hat(delta theta_cell). A fixed spatial couple density m per
reference arclength therefore has work integral(m dot delta theta_cell ds0).
Its residual G has only the six internal cell-rotation entries:
G_cell = integral_cell(m ds0). Nodal and retained-stress entries are zero.
Use the unchanged element stiffness quadrature (order 4 or 8), not nodal
lumping, current length, director-component moments or an SO(3) potential.

Let Rc be the residual of the preserved conservative material-minus-dead-line
work potential and Hc its spatial Exp-chart Hessian. The loaded residual is
F=Rc-G. Its spatial Jacobian is J=Hc-C(Rc), since D G=0 under this fixed-spatial
reference measure. C has 1/2 skew(Rc_rot) on all five rotational blocks (three
nodal, two cell). It must use Rc, not F. At internal equilibrium Rc_i=G_i can
be nonzero: J_ii is generally nonsymmetric. With 18 nodal and 24 internal
variables, L=-J_ii^-1 J_iq and J_cond=J_qq+J_qi L. Preserve GENERAL solves;
do not symmetrize or substitute the conservative Hessian-only Schur boundary.

For additive nodal increment coordinates a, spatial virtual rotation is
A(a) delta a, with A the left Exp Jacobian. The pulled force is A^T F_q and
its tangent is A^T J_cond A + (dA^T/da) F_q. This follows from virtual work,
not from an invented total potential. The response explicitly labels the
conservative-part value and denies conservative spectral/dynamic authority.

## Separate reconstruction and gates

The oracle imports only math and NumPy. It reconstructs the Q2 reference
metric from coordinates and uses closed Rodrigues coefficients/derivatives
instead of importing the producer, its geometry helpers, Jet2 or chart code.
Independent observed residual derivatives use the preserved material and
conservative line operators with this separately integrated couple. This is
algorithmic separation, not a completed independent human/scientific review.

Check straight elastic, curved elastic and curved coupled plastic states:
distributed virtual work; full spatial derivative; internal equilibrium;
general Schur/lift equality; condensed spatial and additive-chart derivatives;
large rigid superposition; fixed-origin unload/replay; failure/cancellation;
immutable outputs; invalid density/range/deadline rejection. Explicitly show
that net-residual connection and conservative-only reduction substitutions
give incorrect tangents. At zero density require byte-identical physical
state/history and conservative Hessian relative to the preserved boundary,
with equivalent spatial tangent to 1e-11.

Normalized work/objectivity/algebra checks use 1e-11; independent directional
differences use 1e-7. Do not tune coefficients or relax thresholds. These tests
do not establish continuous quadrature accuracy, global load/restart parity,
mass/modal/buckling authority, or production qualification.

Smoke before rehearsal; freeze after passing the complete rehearsal. Then two
fresh-directory clean-head/runtime-guarded cycles must produce byte-identical
canonical scientific packets. Keep inventories separate and archive failures.
Each child uses one numerical thread, 24-GiB tree memory, 600-second wall and
120-second CPU-inactivity watchdogs; at most three children, 1,800-second wave
cap, exclusive outputs, complete process-tree termination and no automatic
retry. Independent review stays PENDING. Integration into native material
transactions/solver/restart is a subsequent step, not implied by this gate.

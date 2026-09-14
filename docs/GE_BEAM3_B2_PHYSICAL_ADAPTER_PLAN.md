# B2 physical matrix adapter: successor preregistration

Implementation base: 22289a62fda9bb09def91c21b297b2cf06533a19.
Boundary: private integration only; public operators and old identities unchanged.
The separately authored draft below is adopted as the proposed equation/test
contract. Independent contract acceptance is required before implementation.
Implementation freeze and independent execution review are required before runs.
This plan does not authorize qualification claims from drafting or smoke results.
Source hashes in the draft bind unchanged inherited files, not the draft's old HEAD.
Full G3c, G4/G5 and all applicable parity rows remain mandatory.

## Concrete initial adapter identity and geometry admission

Policy ID: `GE_BEAM3_G3C_B2_PHYSICAL_MATRIX_ADAPTER_V1`.
Core ID: `GE_BEAM3_G3C_B2_PHYSICAL_FLEXIBILITY_V1`.
Schema ID: `GE_BEAM3_G3C_B2_PHYSICAL_MATRIX_DESCRIPTOR_V1`.
No old policy ID may dispatch to this adapter.

This initial adapter uses the inherited pure analytic chart unchanged: exact
finite binary64 arrays, two distinct positive integer node IDs, physical anchor
equal to one of those IDs, finite computed length L>=1e-12, proper supplied
rotations within1e-11, and both increment and all-pair relative-rotation guards
already frozen in that chart. The physical local-z input is normalized after
max-component scaling; its axis-orthogonal residual must exceed1e-6 of its norm.
Nonfinite computed geometry or derivatives are typed admission/representability
failures, not numerical fallback. No new scale-safe chart or relaxed admission
is authorized by this initial adapter implementation.

The formal fixtures are exactly the six geometries/materials and all transforms
in the existing physical B2 contract. Core-only L=1e308 representability evidence
is not adapter coverage. This initial gate does not settle the full geometry
parity row: actual legacy-supported inputs outside this inherited chart admission
must remain OPEN for a separately reviewed numerical-geometry extension, unless
their legacy rejection is demonstrated. Rejecting them here is not proof that
full parity is finished and does not authorize dropping them from the inventory.

---

# Private physical B2 matrix adapter: design draft

DESIGN DRAFT ONLY. This file is not a frozen contract, execution authority,
implementation review, or qualification evidence. No candidate file was changed
while preparing this read-only design. No numerical execution was performed.

## Additive implementation boundary

Add a separate private adapter, for example
`src/anysolver/_ge_beam3_g3c_b2_physical_adapter.py`, with a B2-only concrete class
and distinct adapter policy ID. Do not modify, subclass, redirect, or call the
old `_ge_beam3_g3c_stable/beam.py::LocalBeam.evaluate`: that method constructs
legacy `BeamElement`, evaluates its scalar mechanics, and invokes old recovery.
Preserve old local/graph/restart policies and all historical evidence.

The approved successor core is `_ge_beam3_g3c_b2_physical.py`. Pure analytic
chart logic is in `_ge_beam3_g3c_stable/beam.py::deformation`; analytic spatial
left-Exp Jacobian and derivative are in
`_ge_beam3_g3c_stable/joint.py::_exp_terms`. Reuse these mathematical helpers
subject to the admission caveat below; never reuse old scalar mechanics or its
mutable material/element caches. Public B2/B3, qualified Q4/S3 and defaults stay
unchanged. This adapter remains pure and has no commit or checkpoint-import API.

## Physical frame and complete pullback

Let the two reference coordinates be X1, X2, length L, and supplied physical
local-z orientation o. Construct

    a = (X2-X1)/L
    z = normalize(o-a*(a dot o))
    R0 = [a, cross(z,a), z]

Reject degenerate/parallel orientation according to the reviewed admission
contract; do not infer roll from a fallback global axis. Bind physical anchor
node 101, not its connectivity index. For the direct-anchor chart,

    Qi = Exp(eta_i) Qaccepted_i
    d_i.translation = Qanchor^T (xi-xcentre) - (Xi-Xcentre)
    d_i.rotation = Log(Qanchor^T Qi)

The chart returns d, D = partial d/partial z, and S_i = second derivative of d_i,
including both translational and rotational dependence of the anchor. Here z
denotes the full 12-coordinate trial vector, not the section normal above.
Use the block matrix T containing four R0^T blocks (translation and rotation
per node). The section frame is reference-fixed, so T has no trial derivative.

    dlocal = T d
    core = physical_core.evaluate(L, physical_rigidities, dlocal)
    fref = T^T core.force
    Kref = T^T core.tangent T
    g = D^T fref
    H = D^T Kref D + sum_i fref_i S_i

The force-weighted second chart derivative is mandatory; it cannot be omitted
because the local core tangent is analytic. The resulting H is the Hessian of
the same discrete potential, not a separately chosen stiffness.

For each rotation increment obtain J_i = Jleft(eta_i) and its derivative dJ_i.
Define P = blockdiag(I3,J1,I3,J2). Spatial virtual rotation is P times chart
variation. Pull back rows with a linear solve, never a cached inverse:

    r = solve(P^T, g)
    C[j,k] = sum_i r_i * partial P[i,j]/partial z[k]
    A = solve(P^T, H-C)

A is the derivative of spatial force with respect to chart coordinates. It is
not generally symmetric. H is the conservative chart Hessian. At the same pose
after rebase, compare r and A P^-1 (a right-side solve), rather than directly
comparing chart Hessians or claiming A is a symmetric spatial Hessian.

## Physical recovery and transport

Return the actual core physical strains/resultants, station order, weights and
energy, with definition and operator provenance. The recovery differential with
respect to reference-global d is `core.strain_differential @ T`; with respect to
trial z it is `core.strain_differential @ T @ D`. Its integrated virtual work
must reproduce g. Reference frame is R0; current frame is Qanchor R0. Never
replace physical shear by effective shear or numerical work channels.

Connectivity reversal swaps the two node blocks while preserving the same
physical anchor node and physical local-z direction. It gives

    R0_reversed = R0 diag(-1,-1,1)

Reverse station order. The signs for both the physical strain order
[eps_x,gamma_xy,gamma_xz,kappa_x,kappa_y,kappa_z] and resultant order
[N,Vy,Vz,T,My,Mz] are [1,1,-1,1,1,-1]. Verify the differential column/node map as
well as field signs. Global chart force and Hessian transform by the node
permutation, without extra physical-space signs.

For common spatial motion W,t with reference coordinates unchanged, transform
current coordinates as W x+t and matrices as W Qi. At a rebased pose the local
fields and energy are invariant; current recovery frame and spatial force rotate
by W. For passive coordinate change U,t, transform reference coordinates and
orientation, trial translation/increments by U, and matrices as U Qi U^T.
Reference/current frames transform by U, while physical components stay fixed.

## Immutable descriptor and rejection

Bind distinct core and adapter IDs, schema, node IDs and coordinates, physical
anchor, normalized physical orientation and complete reference frame, scalar
material/section, update convention, recovery convention and quadrature. Store
canonical descriptor bytes and a seal. Require an exact concrete adapter type;
capture descriptor/seal at entry and verify again at exit so coherent replacement
mid-trial is rejected. Return fresh descriptor values and detached immutable
arrays. Copy caller inputs once before using them in both chart and connection
calculations; do not reread mutable caller inputs after chart evaluation.

Wrong or historical policy IDs must be rejected before chart/core evaluation.
Do not add historical checkpoint import to this adapter. New graph definitions,
runtime identity and restart schema are a later distinct integration gate;
historical packets retain their old authority and are not successor evidence.

## Frozen-contract three-node test inventory

1. `test_noncommuting_chart_pullback`: use the registered noncommuting accepted
   matrices, sinusoidal trial and direction, and all six scalar fixtures.
   Independently reconstruct physical frames, basic flexibility and recovery.
   Verify energy, physical values, full chart gradient/Hessian, spatial force
   derivative, D and S, strain derivatives and integrated station work at all
   inherited steps 1e-4, 1e-5 and 1e-6. Include nonzero local force to detect a
   missing force-weighted chart Hessian. Retain 1e-11 invariant and 1e-7
   directional tolerances, with scale-safe relative comparisons for tiny work.
2. `test_common_motion_passive_reversal_rebase`: cover all registered common
   rotations (including pi and 1.4*pi), translation, passive Rz(pi/2), reversed
   connectivity with anchor 101 retained, and same-pose zero-increment rebase.
   Check energy, fields, frame directions, force/tangent maps, station and
   derivative maps. Compare chart-independent spatial-input derivatives for
   rebase; do not compare unlike chart Hessians.
3. `test_definition_and_old_identity_rejection`: reject old/wrong identity before
   any numerical call, malformed arrays, improper/nonfinite matrices, wrong
   anchor and node IDs, parallel orientation and unsupported section keys.
   Exercise caller mutation during evaluation, coherent descriptor/seal swap,
   subclass admission, detached immutable outputs, and unchanged inputs after
   failure. Assert no commit or checkpoint-import route. Preserve old dispatch;
   do not monkeypatch it to expose the successor.

Existing recipes in `tests/test_ge_beam3_g3c_local_beam.py` are useful background,
but its legacy mechanics oracle must not determine the new operator's result.
Use an independent physical-flexibility reconstruction, not production core
internals, for expected station fields and local force/energy.

## Inherited range/admission caveat

The current chart helper rejects L < 1e-12 and uses unscaled Euclidean norms and
mean/centering arithmetic. Blind reuse can overflow for extreme finite geometry
even when scalar physical-core quantities remain representable. The core's
extreme L=1e308 test therefore does not establish that range for the adapter or
assembled graph. Do not silently claim all-positive binary64 graph closure.

Before implementing any change to chart admission or numerical geometry, bind
the exact intended range in the successor adapter contract. Preserve inherited
scientific tolerances and all-pair relative-rotation guards. If scale-safe
geometry/chart improvements are required, add them separately under the new
adapter identity and independently review them; do not alter the historical
chart or claim that rejecting representable physics solves the full-domain gate.
Dense binary64 derivatives also have conditioning/subnormal limits distinct
from exact scalar intermediate arithmetic. Record actual failures rather than
flooring coefficients or weakening physical recovery.

## Execution boundary

Freeze implementation and independently review before numerical execution. Use
the shared bounded runner and original three adapter test names, one numerical
thread, 24 GiB, 600 seconds per child, 120-second inactivity monitoring, at most
three workers and 1800 seconds per wave. No automatic retry or authority reuse.
Adapter success alone does not qualify a graph, full G3c, Q4 recovery, G4/G5,
public routing, or production use.

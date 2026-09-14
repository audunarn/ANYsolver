# Independent Q4 finite work-channel source assessment

Reviewer: `/root/g3b_independent_review`, separately approved independent agent.
Read-only derivation against checkpoint
44dc811ccf620536216c8bc97c2930f2502454b4 in the finite-local worktree.
No mechanics were executed; no production source, tests or prior evidence were
changed. This is an equation assessment, not a frozen implementation approval.

## Decision and admitted source branch

The proposed potential, force and tangent split follows exactly from the source
for a planar homogeneous scalar elastic Q4 with positive thickness, virgin zero
state, no initial fields, no generalized section, no plastic/hardening/Hill law,
no activity/deletion or other inherited extensions. Keep the actual admitted
quadrature and local transforms. The split is not authority to relabel existing
linear mixed recovery as full finite work-conjugate recovery.

Source anchors in `src/anysolver/e4_pl_element.py`:

- Lines 522–523 capture the inherited nonlinear response/geometry functions.
- Lines 3209–3363 preserve inherited geometry with a dimensionless-Jacobian
  fallback implementing the same arrays and rules, including separate MITC4
  shear integration.
- Lines 5641–5693 define the planar correction as actual qualified stiffness
  minus the inherited zero-displacement tangent, evaluated at five layers.
- Lines 5729–5738 clear the hourglass cache before the inherited finite call;
  line 5679 clears it before the inherited zero call. Thus a stale qualified
  hourglass matrix cannot enter either inherited branch of this identity.
- Lines 5756–5776 add correction times displacement to force, and the same
  constant correction to tangent.
- Lines 5534–5567 separate actual qualified physical core, PL and hourglass.
- Lines 5962–6075 recover the linear stationary mixed fields; lines 6357–6498
  map those fields to the physical director and global tensor conventions.

Source anchors in `src/anysolver/elements.py`:

- Lines 1938–1969 define T0 and engineering membrane/bending operators.
- Lines 2594–2687 define reference geometry; the membrane/bending/drill rule is
  the Q4-authorized ordered 2x2 rule, and shear uses its distinct MITC4 2x2 rule.
- Lines 2872–3000 select the scalar route, set A=h*C_el, D=h^3*C_el/12,
  zero coupling C1, and compute compatible von-Karman membrane strain.
- Lines 1395–1535 integrate Beff-transpose N, linear bending/drill/shear forces,
  their material tangents and Gw-transpose N-tensor Gw geometric tangent.
- Lines 3154–3232 apply the local/global transforms and optional cached linear
  hourglass contribution. That cache is explicitly absent in the two qualified
  calls described above; the qualified hourglass remains in Kqualified.

The five-layer correction does not introduce a layer mismatch on this branch:
the elastic shortcut uses analytical h and h^3/12 integrated moduli, independent
of Lobatto layer count. This argument does not extend to other constitutive
branches by assumption.

## Exact algebra of the source potential

Let d denote the extraction-deformed element vector in reference-global
components, y=T0*d, e=Bm*y, p=Gw*y and
n(p)=[p_x^2/2,p_y^2/2,p_x*p_y]. Define ev=e+n and Beff=Bm+dn/dy.
For each source membrane quadrature point, A=h*C_el is symmetric and constant.
The inherited potential is

    Uinh(d) = sum w * (ev^T A ev)/2 + (y^T Kother y)/2,

where Kother comprises the unchanged linear bending, MITC4 shear and drill
terms, each with its own actual weights. Its zero tangent is

    Kinh0 = T0^T [sum w * Bm^T A Bm + Kother] T0.

Therefore adding (d^T (Kqualified-Kinh0) d)/2 cancels those inherited linear
terms algebraically and yields exactly

    U(d) = (d^T Kqualified d)/2
         + sum w * [(ev^T A ev)/2 - (e^T A e)/2].

Its derivative increment in y coordinates is

    delta_f_y = sum w * [Beff^T Nv - Bm^T Nl],
    Nv=A*ev, Nl=A*e.

Its Hessian increment is

    delta_K_y = sum w * [Beff^T A Beff - Bm^T A Bm
                      + Gw^T [[Nv_xx,Nv_xy],[Nv_xy,Nv_yy]] Gw].

Transform with T0^T and T0. The geometric term uses Nv, not a substituted mixed
or summed resultant. Engineering xy strain is 2*tensor_xy; Nxy is tensor_xy.
These formulas recover the precise cross-term Hessian of p_x*p_y, without an
extra factor of two. At d=0 both force and Hessian increments vanish.

No assertion of positive finite delta-energy follows: the subtracted channel
is signed, and a nonlinear-minus-linear difference is not a separately positive
material energy. Do not introduce positivity assertions or stabilization here.

## Honest output and work interpretation

Use separate, explicitly identified channels, all derived from the same owned
d and immutable definition:

1. Qualified linear physical baseline: actual Kcore, Ucore=d^T*Kcore*d/2,
   fcore=Kcore*d, and its unchanged source mixed compatible/independent fields,
   resultants and physical frames. Do not assume pointwise constitutive equality
   between the two independent mixed fields; verify their stationary weak work.
2. Qualified numerical PL and hourglass: their actual matrices, energy, force
   and tangent separately; these are never physical section resultants.
3. Added compatible von-Karman membrane: ev, Nv, Beff, source weights/frame,
   positive-sign potential, force and full material/geometric Hessian.
4. Removed compatible linear membrane: e, Nl, Bm, the same source weights/frame,
   and explicitly negative-sign potential/force/tangent.

The sum must equal actual source U/f/K, then the complete common-pose pullback
uses each force-weighted deformation Hessian. It must reproduce actual spatial
nodal wrench/virtual work and the eventual joint multiplier work. Physical
station-value diagnostics retain channel provenance and are not interchangeable
with the actual external nodal forces.

Even if the qualified compatible membrane derivative equals Bm after transport,
using one Beff with Nmix+Nv-Nl produces an extra

    Bnl^T * (Nmix-Nl)

relative to the correct mixed baseline plus source increment. The mixed and
compatible linear fields do not coincide identically over the general domain.
Thus a single claimed ordinary finite work-conjugate membrane resultant is not
established. A tensor sum can be an explicitly named composite diagnostic only,
not a replacement public recovery field or authority for yielding, fatigue,
design checks or a single-strain constitutive interpretation. It is safer not
to expose that sum in this local gate at all.

If the G3c requirement is interpreted as demanding one such unique conventional
physical recovery field instead of auditable source-native multi-channel work,
that requirement remains blocked under unchanged Q4 mechanics. Do not redefine
the requirement silently; freeze the multi-channel interpretation explicitly
for review before implementation. Source-native nodal work itself is not
blocked by this issue.

## Frames, physical director and required tests

Nonlinear R0 is the center frame from the inherited source. The qualified mixed
recovery has its own Equation-7 frame. They may differ: never compare raw local
arrays as if those frames were identical. Bind natural/physical station maps,
transport strain tensors with half engineering shear and resultant tensors with
full shear, and only then compare values. The existing physical-director map at
e4_pl_element.py3823–3865 reverses numbered tangent/normal consistently:
membrane diag(1,1,s), curvature s*diag(1,1,s), shear s*diag(1,s).
Do not apply an invented beam convention. For current spatial diagnostics,
rotate each reference-global channel tensor by the same extracted common-pose
R on both sides; do not swap R for a selected nodal Qi or regenerate graph D0.

Freeze tests that independently reconstruct these operators and weights, verify
U/force/tangent channel sums against actual source, and check all inherited
directional steps and D4/director transports. Include a square checkerboard
w=[a,-a,a,-a], zero rotations: it has zero linear membrane recovery but nonzero
compatible von-Karman strain. Also include a mixed-field mismatch case to expose
the extra Bnl-transpose term in the invalid single-field formula. Both are test
proposals here, not executed numerical findings.

Require finite checks before norm comparisons on every channel and aggregate;
retain zero-state reference recovery and numerical separation; reject foreign
origin/initial/history routes before family evaluation. Same-pose rebase must
preserve local d, all channel values and detached actual family candidate state.
The Q4 elastic shortcut's virgin trial dictionary is not itself a record of
finite station strains, so do not infer those values from its plastic arrays.

This assessment permits drafting a source-bound multi-channel local contract.
It does not authorize implementation execution, graph closure, full parity,
default changes or modification of qualified Q4/S3 laws or recovery.

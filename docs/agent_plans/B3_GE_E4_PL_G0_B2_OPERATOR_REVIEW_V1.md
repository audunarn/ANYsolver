# Independent G0 B2 physical-operator review v1

Reviewed read-only on 21 September 2026 in the B3-GE/E4-PL integration
worktree. This is a mechanics and gate recommendation, not an implementation,
execution authority, F09 acceptance or production qualification. No registered
runner was executed. The worktree had concurrent uncommitted registration,
programme and probe work; this memo leaves those files untouched.

## Finding and proposed route

**F09 is open.** The registered F09-S-v1 six-row diagnostic reports
`BOUNDED_PHYSICAL_RANGE_MISMATCH`. Its raw log SHA-256 is
`b40a3f764622fbe45569745f16cc315cc772f299c11ef6a3b95017796cbaaf6aa`
(recomputed here). For L=1, E=1, nu=0, Iy=Iz=J=1e-12, ky=kz=1 and A=1e-14,
both transverse energies are 4.615384615384616e-17 in public scalar B2 versus
2.498958767180342e-19 under the unfloored physical Timoshenko law: a factor
184.6923076923077. Both A=2e-12 and A=1e-10 controls agree with that law.
The registration reports tool-observed exit zero, but the JSON log itself
does not attest to launcher exit/environment. Its consumed v1 execution must
not be retried to improve provenance.

Public `BeamElement._local_linear_stiffness` uses
`phi_w = 12 EIy / max(G13 A kz L^2, _SMALL)` and the analogous `phi_v` with
`G12 A ky`; `_SMALL` is 1e-12. This is a material change of shear compliance
in the admitted small-area range, not a shell attachment error. Preserve that
public class's scalar and generalized equations, selectors, outputs, defaults,
serialization and all historical evidence. A corrected result must carry a
**new, explicit physical B2 operator identity** inside the separately selected
`B2_E4_PL_FAST_LINEAR_V1` definition, never an implicit reinterpretation of
an old `BeamElement` or checkpoint. The programme revision 3 currently says
this profile uses *public* B2 mechanics. Before changing its implementation
contract, amend that programme and G0 registration under independent review
to specify the new identity, supported sections, compatibility, negatives and
revised F09/B02 oracles. A new operator is no longer same-law public-B2 parity;
run old-route preservation and physical-law comparisons as distinct evidence.

For a straight, constant, isotropic scalar section, let
`S=diag(EA, G A ky, G A kz, GJ, EIy, EIz)` in the physical local frame, with
`G=E/[2(1+nu)]`, strictly positive physical inputs and no coefficient floor.
With the existing six basic deformation rows `B` and equilibrium resultant
interpolation `H(x)`, define `F = integral_0^L H(x)^T S^-1 H(x) dx`,
`q = F^-1 B u_local`, `U = (B u_local)^T q/2`, `f=B^T q`, and
`K=B^T F^-1 B`. Integrate the polynomial exactly (the existing three-point
rule suffices) and use stable factorization/modal arithmetic: in either
bending plane the positive symmetric/antisymmetric stiffness eigenvalues are
`[L/(6 EI)+2/(G A k_s L)]^-1` and `2 EI/L`. Retain both factors through
energy, force and recovery; subtracting rounded dense entries loses the weak
mode at extreme shear ratios. Section resultants are `H(x)q`; physical strains
are `S^-1 H(x)q`. Verify `delta U=f dot delta u` and station virtual work,
including shear and moment signs. Rotate the local tangent once into global
coordinates; the linear reference operator has no accepted-rotation state or
nonlinear pose pullback. Six basic modes and six rigid nulls are the reference
rank target, subject to explicitly reported finite-precision limitations.

An elastic generalized symmetric positive-definite 6x6 section can use the
same `F=integral H^T S^-1 H` construction, retaining off-diagonal coupling;
it needs its own conditioning, units, recovery and reference tests. The public
generalized branch already uses this force-based formula (and `inv(S)`,
`inv(F)`), whereas its scalar branch uses the floor-bearing closed form.
Equality with a diagonal generalized section in ordinary well-conditioned
cases is a useful cross-check, not an independent oracle for the shear-soft
case. Do not relabel arbitrary generalized data as isotropic scalar, infer
mass or Wagner geometry from 6x6 stiffness, or use an unrelated section law
for buckling prestress.

## Relevant prior evidence and limits

The private `GE_BEAM3_G3C_B2_PHYSICAL_FLEXIBILITY_V1` core implements the
unfloored modal flexibility with exact rational intermediate coefficients,
physical strain/resultant recovery and axial von-Karman energy. Its local-core
review accepted bounded evidence only. The private matrix adapter has policy
`GE_BEAM3_G3C_B2_PHYSICAL_MATRIX_ADAPTER_V1`, a sealed descriptor, physical
anchor/frame, analytic chart Hessian (including the force-weighted second
chart derivative), and spatial rotation pullback. Its separately reviewed
bounded evidence covers the **initial inherited geometry adapter only**;
`graph_qualified`, `geometry_parity_closed`, `full_g3c_qualified` and
`production_qualified` are all false. It is neither a public dispatcher nor a
linear B2 shell operator. Its chart requires computed L>=1e-12 and has
finite-geometry overflow and conditioning caveats; a core extreme-length test
does not close graph admission. Reuse its reviewed physical equations and
tests as design evidence, not its historical acceptance tokens or nonlinear
adapter identity. The linear profile should take a separate implementation,
descriptor/schema and evidence identity; a shared numerical kernel is possible
only after its exact applicable input/equation contract is reviewed.

## Required gates before selection or release

1. Freeze the amended programme and F09 registration *before* candidate
   execution: exact scalar and generalized admitted domains (length, frames,
   material, SPD section conditioning, representable output), operator/profile
   and persisted definition identities, input hashes, independent oracles,
   tolerances, resource limits, logs, terminal rules and negative requests.
   Distinguish input failures from representability failures; do not narrow
   previously supported public B2 inputs to hide the observed mismatch.
2. Review the implementation and runner independently, then test the six
   reference basic modes/rank, rigid motions, both bending planes and signs,
   clamp-active/threshold/unclamped and `A=2^-80` modal retention, unequal
   `Iy/Iz/ky/kz`, section coupling, units/scaling, orientation/reversal,
   derivatives, station work, and positive nonzero tiny physical energy with
   relative physical denominators. Record numerical graph-conditioning and
   geometry-range failures openly. Existing private evidence cannot substitute
   for this new source/input graph.
3. Keep G0A-B2's 14/14 source preservation baseline separate (registered raw
   log SHA-256 `7b8dce0345428278ec9441ac993cef6604fe1c20454ef07923028415475e7de5`);
   establish installed 0.4.7 baseline and old public scalar/generalized,
   mass, geometric stiffness, material and MPC compatibility. F09 must prove
   the new physical section/trace; F10 the linearized point, exact weak line
   and footprint laws; F11 affine versus constrained-system reactions; F12
   consistent reference prestress and conservative buckling; F13 ownership,
   batch reuse and mutation invalidation. Each remains separately registered.
4. Carry B01-B18, relevant V01-V28, independent mixed external comparisons,
   scale/consumer and final reviews through G0-G6. Modes require a physically
   consistent mass route; buckling must preserve the declared compression sign
   and Wagner metadata policy. The `FAST` label is an identity, not a speed
   finding. Do not mix the private nonlinear G3c adapter into the linear
   assembly or silently assemble B2 and B3-GE in one nonlinear model.

No new B2 operator, shell coupling or changed admission is accepted by this
review. The concrete next gate is a versioned programme/F09 amendment and
independent equation/admission review for the explicitly selected linear
physical operator, followed by a frozen implementation and bounded evidence.

# Physical-cap transition mechanics review — 4 October 2026

Read-only supporting assessment of `C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001`, assigned source identity `3a501e69`. No repository edits, numerical execution, commits, branch/history changes, nested workers, protected-original access or restricted impact replay. Policy read: `ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1`, revision `2026-09-24.2`. This is a mechanics/source review, not engineering acceptance or C0–C9 qualification.

## Finding

Generalized derivatives can extend a continuous, locally Lipschitz geometric/contact law across suitable feature transitions. They cannot repair the existing full endpoint spring being deleted at a penetrated cap/side ownership switch. A single genuine selected cap gives a finite energy jump. Picking either force or either tangent at the equality does not change the unequal one-sided energy limits or supply the missing work. The present explicit rejection is therefore justified for the declared legacy law; merely removing it would create an unsupported model.

An extension is possible by changing and declaring the potential. The fastest broad route compatible with actual round surfaces and friction is a distinct profile with fixed material side/cap patches, surface-point work, declared measure normalization, and a continuous signed target gap. Existing local Jet2, surface variations, paired work and transactional friction infrastructure provide useful kernels. The classical geometry maps and actual round target projections still need implementation and verification; the existing centreline-radius laws are not that profile.

## Source evidence inspected

Paths below are relative to the assigned repository.

- `src/anysolver/general_contact/beam_plane.py:248–270, 311–330`: end gap is endpoint centre height minus radius; ownership is outward curve derivative dotted into plane normal; penetrated equality is rejected, positive ownership skipped, negative ownership adds the complete `0.5*endpoint_stiffness*gap**2` and only endpoint translational work. Its path guard separately rejects a closed ownership crossing.
- `src/anysolver/general_contact/beam_pair_ends.py:108–152`: active projection/ownership ties are rejected; side-owned ends omitted; admitted end/interior springs contribute full `ke*g²/2`; reciprocal end/end springs are counted once. `evaluate` combines this with the symmetric distributed line potential.
- `src/anysolver/general_contact/beam_radial_ends.py:144–163`: the same full spring/deletion ownership structure, with radial point gap derivatives.
- `src/anysolver/general_contact/beam_end_topology.py:5–14`: every classical material-node incidence is counted, including unselected elements. Only incidence-one selected ends are cap candidates. Therefore cancellation from two selected caps is not a general property.
- `src/anysolver/_ge_beam3_mixed_ad.py:15–99`: dense local value/gradient/Hessian Jet2 primitives. Jet2 differentiates a selected smooth branch; it does not establish continuity or automatically resolve a geometric tie.
- `src/anysolver/general_contact/native_retained_station.py:34–82, 121–183`: physical surface position and generalized work include section rotation; exact local rotation variations are available. The station is explicitly an interior native half-cell point, so it is evidence for reuse, not an existing classical/cap adapter.
- `src/anysolver/general_contact/native_surface_s3_friction.py:219–281`: objective relative surface increments, joint source/target local Jet2 coordinates, frame/history terms, reference-area weighting and pullback to authoritative DOFs. This is a useful construction pattern, not admission of round target geometry or of a new full profile.

## Analytic discriminator: one cap, fixed endpoint, finite energy jump

Take a fixed plane with normal `n=(0,0,1)`, beam radius `r>0`, stiffnesses `kL>0` (N/m²), `ke>0` (N/m), and `0<δ<r`. Choose δ within the permitted penetration tolerance. A selected B2 has

`a=(0,0,r−δ)` and `b(s)=(L,0,r−δ+s)`, `L>0`.

These are deformed states; choose initially open or touching reference positions at height r, so the initial-penetration validation is satisfied. The path represents a later finite-stiffness contact state, with fixed reference length (L0=L for that straight reference).

Attach one unselected classical B2 from `b` to a separate material node `c`. The selected node `a` has incidence one and `b` incidence two. Thus the selected contact surface has exactly one genuine physical end. The continuation remains regular for sufficiently small s; it need not contribute contact. This respects the actual all-node topology rule.

For the selected end a, `q=n·(a−b)=−s` and `g_a=−δ`. Therefore the existing spring is active for `s>0`, absent for `s<0`, and rejected at `s=0`. At a material coordinate `λ∈[0,1]`, the existing line gap is `−δ+sλ`. For `|s|<δ` it is negative throughout. With fixed reference line length `L0`, the exact integrated legacy energy is

`E_line(s) = (kL*L0/2) [δ²−δs+s²/3]`.

The endpoint term is

`E_end(s) = (ke*δ²/2) 1{s>0}`.

Consequently `lim(s→0+) E_total − lim(s→0−) E_total = ke*δ²/2 > 0`. The distributed line term has identical limits and cannot cancel that difference.

Endpoint a is fixed along this path. Its reported endpoint force does exactly zero incremental work. The integrated line generalized force between `−ε` and `+ε` is `E_line(+ε)−E_line(−ε)=−kL*L0*δ*ε`, which tends to zero. The full energy difference tends to `ke*δ²/2`. Hence the reported forces do not generate the energy difference across the ownership switch.

No value assigned only at s=0 makes the potential continuous. The classical Clarke generalized gradient requires local Lipschitz continuity, which this potential lacks. Differentiating the step in a distributional sense introduces an impulse proportional to `ke*δ²/2`, absent from the current mechanics and unsuitable as an ordinary Newton tangent. A tangential force or invented orientation stiffness cannot be added silently to compensate.

This one-plane case already disproves a universal generalized-derivative repair of the current law. It does not imply every two-cap setup jumps: in special B2 plane paths one cap can replace another with equal energy. That cancellation is topology- and geometry-dependent and cannot authorize the one-cap or pair/radial domain. Joint open activation at `g=0` is also a different case: squared unilateral penalty then has zero limiting energy and force.

## A narrowly bounded continuous alternative

For one cap against one plane, retain a spring on the minimum actual hemispherical surface gap rather than deleting it by ownership. Let `t` be the unit outward section axis, `q=n·t`, and cap centre c. The exact cap support gap is

`g_cap = n·(c−p) − r` for `q≤0`,

`g_cap = n·(c−p) − r*sqrt(1−q²)` for `q>0`.

On the second branch the minimizing point is the equatorial rim. Both gaps and their first derivatives agree at q=0; their second derivatives can differ. The complete `ke*[min(g_cap,0)]²/2` thus has a legitimate piecewise tangent there under regular geometry. Its axis derivative supplies the rotation/work terms on the rim branch. This is an explicitly changed cap law, retaining a rim spring when the legacy law said side-owned. It needs a distinct identity and cannot be described as an implementation-only tangent fix.

This is a useful cheap analytic oracle for a single plane. A whole-section minimum can lose simultaneous distinct contacts for more general obstacles, and minimizing-point velocity includes contact-location migration unless material velocity is handled separately. Therefore this reduction alone is not a complete C0–C9 surface/friction formulation.

## Broad extension: fixed material patches and a declared surface potential

Represent the actual side by the model-owned centreline and section frame, schematically `x_s(ξ,θ)=c(ξ)+R(ξ)ρ(θ)`. Represent each topologically genuine hemisphere by `x_e(v)=c_e+r*R_e*v`, with v in the fixed outward reference hemisphere. The circle/hemisphere seam is shared once as a boundary of measure zero. Section axes, shear, curved lifts and interpolation belong to the authoritative element model. Do not substitute the centreline tangent for a section director without an explicit supported kinematic contract. A sheared/curved material sweep need not have the same normal as its radial arm; normal and signed gap come from the actual target geometry.

For each declared source/target interaction let `g(x_source,q_target)` be the continuous signed target-surface gap. On smooth resolved projection branches derive both participants' variation. A normal potential with preserved input units is

`E = (kL/2) ∫_side [min(g,0)]² dμ_s + Σ_ends (ke/2) ∫_cap [min(g,0)]² dμ_e`,

where `dμ_s=dA0/(2πr)` has units m and `dμ_e=dA0/(2πr²)` is dimensionless. For a straight circular reference side this is circumference averaging times reference centreline length; for a hemispherical cap it is an area average. If reference sweep area is different, use its actual reference Jacobian. These are explicit constitutive normalizations, not numerical quadrature weights masquerading as physics. They give equivalent per-reference-area penalty densities `kL/(2πr)` and `ke/(2πr²)` (both N/m³), with no inferred relation between kL and ke.

Material domains remain fixed as contact migrates across the seam; only the continuous point gap changes. There is no orientation switch that deletes finite energy. Distinct contact patches/pairs remain represented. A stiffness density mismatch between side and cap is a declared material-law distinction, not an energy jump caused by repartitioning an active point spring.

For a quadrature point with constant material weight w and scalar penalty coefficient k, the smooth active branch gives

`f = w*k*g*∇g`, `K = w*k*(∇g∇gᵀ+g*∇²g)`.

Seed both bodies and all relevant translations/section rotations in a small local Jet2 chart; differentiate the actual geometry and any eliminated smooth projection coordinates, then pull back once. Existing `_projection_work` demonstrates reduced projection-curvature terms: freezing a moving target projection is generally insufficient for the Hessian. Existing exact branch certificates/topology may screen or locate candidates, but centreline-distance geometry cannot serve as the surface work geometry. Equal/opposite resultant force and moment follow from objective joint-body energy, and must still be measured.

Pair symmetrization, quadrature convention and histories must be declared prospectively. Existing half-sum line symmetrization is a useful precedent, not permission to double endpoint springs or copy a spring to every quadrature point. Fixed material source stations and genuinely distinct interaction partners are not reciprocal duplicates; the new measure law must specify which directional contributions define its potential.

Continuous signed distance is necessary but not sufficient for a universal semismooth Newton claim. At closest-feature ties, prove the relevant one-sided gap/gradient limits, regularity, and the selected generalized derivative. Medial axes, degenerate sweeps, nonunique opposed normals, or unresolved projections may still require a typed non-success. Do not turn this into dropped contacts. Continuous squared activation at g=0 supports the usual unilateral semismooth branch; that result does not settle nonunique geometry or friction.

## Friction and work requirement

At a fixed material surface label, `v_s=ċ+ω×(Rρ)` (including any model-owned curved-lift terms). Use actual relative material surface motion on both bodies and objective transport of tangent frames/history. Differentiate the friction residual with its history/frame dependence; dissipative friction is not generally the Hessian of the normal potential. Native multiplicative rotation work may also require the spatial residual tangent correction already documented by `spatial_surface_force_tangent`, rather than blindly using a chart energy Hessian as the final spatial tangent.

An immediate discriminator is a circular beam spinning about its axis with stationary centreline. A material point has tangential velocity `ω×Rρ`; tangential traction produces torque `(Rρ)×F_t` and power `F_t·v_s=torque·ω`. A centreline-only velocity predicts zero slip, torque and frictional power and fails this case even though the geometric circle is unchanged. Moving the nearest geometric point is not the same as moving the material point; friction history must track the latter.

## Smallest useful next checks (not executed here)

1. Encode the one-cap analytic path and compare energy difference to integrated virtual work. The legacy model must retain its rejection; a candidate new potential must have matching one-sided energy/work limits.
2. For plane and cap support geometry, verify exact rim/cap limits and distinct line/end units, then verify fixed-patch surface quadrature without blending or hidden ke–kL matching.
3. Check complete source/target force and moment, joint rigid translation/rotation objectivity, gap activation and materially rotating surface-point friction power. Use nontrivial target rotation and section spin, not centreline translations alone.
4. Retain all candidate material patches and distinct simultaneous partners; certify integration error and projection branches within the prescribed bounded resources. No source review or prototype passes imply C0–C9 acceptance.

No claim of measured speed, complete implementation, execution or qualification is made. This review resolves the principal mechanics question: the current active ownership deletion is incompatible with conservative work across a closed switch; a newly declared continuous potential is required.

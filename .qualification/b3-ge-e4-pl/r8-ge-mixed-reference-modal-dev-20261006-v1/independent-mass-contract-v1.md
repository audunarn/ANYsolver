# Independent development coordinate/mass contract assessment

State: source assessment only. Root subsequently adopted the narrow experimental V2D LINEAR kinetic approximation below; external/convergence 2% acceptance remains open. No numerical imports, jobs or tests ran. F03 remains UNCONSUMED. No qualification or complete-spectrum claim. Policy read: ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1 revision 2026-09-24.2. Baseline HEAD identity 543ee80d is supplied by root; no Git commands ran. Historical defaults/evidence remain unchanged. This reviewer assessed existing source rather than incomplete author edits.

## Verdict

Native retained-fibre and generalized families share the same explicit reference kinetic map; extending their physical-mass assembly is defensible without stiffness-derived inertia. The native fibre section has no `.elastic` attribute. A virgin elastic tangent may supply the unused elastic-factor argument of `reference_kinetic_factors`, provided it is genuinely virgin, finite/SPD and passed without changing physical inertia or geometry.

Flat V2D S3 nodal rotations are axial rotations, so the proposed director inertia is coordinate-compatible. Its barycentric translational/director interpolation must be explicitly adopted as a NEW kinetic approximation. Existing S3 legacy masses and dynamic-algebraic declarations do not authorize it. Coordinate compatibility, rigid patches and dense QZ agreement alone do not establish physical convergence of this approximation.

BL5 family labels do not establish a regular descriptor. Preserve the existing single p0 BL5 free-native-rigid-mode refusal and verify the actual constraint matrix. Do not replace all attachment connectivity with the assertion that a line supplies six pose conditions.

## Exact source chain and coordinate interpretation

`_stiffened_shell_ge_experimental._shell_reference` creates `e4-pl-s3-v2d`, with six global nodal slots and reference normal z in the noncurved owner. `_assemble_shell` uses its 18-slot virgin response. `NativeParityE4PLS3V2DShellElement` inherits `ShellElement` directly and aliases `StrictFlatLinearE4PLS3V2CShellElement._operators`; V2C also inherits `ShellElement` directly. Neither imports `e4_pl_s3_element.py`.

V2D `_local_component_transform` transforms both translation and rotation by frame.T. V2C `_operators` gives kxx=d(omega_y)/dx, kyy=-d(omega_x)/dy, and base shear components dw/dx+omega_y, dw/dy-omega_x, with MIN3 dl/dm corrections. These signs identify axial omega, not a slope vector beta. Thus omega cross n is the physical director velocity.

The separate qualified S3 `_compatible_kinematics` in `e4_pl_s3_element.py` has 17 coordinates and theta=sum(L_i theta_i)+b alpha, where alpha is a two-component hierarchical physical director bubble. If THIS family were admitted, its M_alphaalpha=(rho h^3/12) integral(b^2 P) is positive on tangential bubble directions and its corner/bubble mass coupling is generally nonzero. Eliminating alpha through static K_aa is not exact: dynamic elimination depends on K_aa-lambda M_aa. This is an obstructing equation for applying the proposed nodal mass to that family. It does not describe the actual V2D owner. Exclude this other family unless its retained kinetic treatment is separately resolved.

## Proposed narrow new kinetic contract

At the virgin midsurface, on each flat homogeneous zero-offset shell facet define v(x)=sum N_i(x)v_i and omega(x)=sum N_i(x)omega_i, with physical thickness velocity V(x,z)=v(x)+z omega(x) cross n. This is the explicitly selected interpolation, including for V2D MIN3; do not claim exact integration of its rotation-enriched displacement reconstruction.

For centered thickness, odd z terms vanish and twice kinetic energy is integral_A [rho h |v|^2 + rho h^3/12 |omega cross n|^2] dA. Therefore M=G tensor diag(rho h I3,rho h^3/12 P), P=I3-n n.T=[n]x.T[n]x. For S3 barycentric N, G=A/12*(I3+ones3). Area uses the positive geometric magnitude. For Q4 preserve the existing nonfolded bilinear-map consistent Gram. All local entries scatter once through authoritative shared nodal slots; a mixed node receives the sum of physical neighboring contributions, not duplicated nodal inertia or averaged family matrices.

Rotations are dimensionless radians; translational mass has kg, rotary mass kg m², and an offset coupling would have kg m. Midplane symmetry is essential. A nonzero reference-surface offset or asymmetric thickness density needs explicit first moments and translation/rotation coupling; refuse it under this contract. Density/thickness are explicit, not inferred from E, material curve, fibre area stiffness or stabilization.

Local shell mass has rank 5 per nodal interpolation direction; arbitrary omega_i parallel n is massless. Tangential directors have inertia. For the current globally XY-flat owner n=z, exact zero columns are component 5 at each shell node. Do not reuse that index list for a tilted or noncoplanar extension: its mass kernel is a subspace and shared-facet normal spins need not coincide. Director reversal n to -n leaves P invariant. Node permutations induce the corresponding six-block permutation. Proper global rotation induces block congruence and preserves kinetic energy; global translation has no effect.

## Native map, packing and stiffness independence

`_beam_reference` places nodal18 first, then each member cell6 and resultants18. Its local42 incidence maps slots[:24] to physical nodal translations and two retained cell rotations, leaving nodal rotation traces at indices 6i+3:6i+6 and trailing resultants massless.

`RetainedFibreOperator.evaluate` uses the same packing: spatial left SO(3) increments for nodal and cell rotations, variables delta[:24], resultants delta[24:]. Consequently the centered kinetic factors use the correct chart basis. At half-cell coordinate t, local spatial velocity is Dq=[F.T((1-t)v_left+t v_right-skew(offset)Omega_cell); F.T Omega_cell], offset=`reference.half_cell_lift(cell,t)`. M=sum w J/2 D.T S D, with S the captured explicit section spatial inertia. A curved half-cell lift is needed even though shell facets are globally flat. A common rigid field v_i=V+Omega cross x_i, Omega_cell=Omega reconstructs rigid velocity at the reference curve position.

`reference_kinetic_factors` validates `section` and builds elastic rows from it, but kinetic rows only use reference geometry, section_mass Cholesky, frames and lift. Thus changing only the elastic tangent cannot change returned `.full`. This must be tested explicitly, including a nontrivial fibre background/coupling. PhysicalFibreSection's constructor certifies the virgin summed elastic matrix in high precision; a binary64 argument still needs finite/SPD representability. Do not replace actual owner K by the helper's uncondensed stiffness factor.

The existing `_physical_spatial_inertia` requires mI translational block, skew first-moment coupling and realizable central second moments. Preserve it; SPD alone is insufficient. Existing explicit inertia and the legacy physical admissibility domain remain captured without projection. Density/stiffness perturbations must not secretly change S.

## Discriminating development checks still required

1. Independent kinetic oracle: integrate V(x,z) directly for constant translation, constant tangential rotation, normal spin and arbitrary nodal fields on a skew S3. Use independent barycentric integration (or exact polynomial moments), not the implementation Gram function. Confirm translational total rho h A, rotary constant-field rho h³ A/12, three normal-spin kernels, expected rank15, permutation and director reversal. Explicitly state that this validates the new interpolation only.
2. An enriched MIN3 physical-field comparison should discriminate the selected linear kinetic approximation from its rotation-dependent displacement reconstruction. A rigid patch must match exactly; nonrigid rotation/shear fields can differ. Preserve that difference as approximation evidence rather than tune tolerances to erase it. Low-frequency mesh/refinement behavior is needed before a broad physical S3 dynamics claim.
3. Native oracle: directly integrate reference spatial velocities and explicit S, with nonzero centroid/translation-rotation coupling and nonstraight half-cell geometry. Test random physical24 vectors, nodal rotation-only traces, resultant-only vectors, common rigid translation/rotation, and materially different virgin elastic sections with identical reference/S. Kinetic output must be independent of elastic section; source inspection alone does not certify numerical representability.
4. Full small dense generalized-QZ oracle for [K C.T; C 0] q=lambda [M 0; 0 0] q, preserving resultants/traces/multipliers, including supported S3/generalized, mixed Q4/S3, physical-fibre and admissible BL5. Compare requested finite eigenpairs nearest the declared shift, physical/constraint residuals and mass Gram. Keep infinite/algebraic modes distinct; do not compare a condensed positive-definite surrogate. Include single p0 BL5 refusal, duplicate/dependent attachment or unresolved native-rigid-field cases, mass invalidity, accepted histories, curved shell owners, unintended J2/offset domains and historical request refusals.
5. Refusal/cancellation/cache tests must demonstrate unchanged virgin owner state, no new fake mass, unchanged old request behavior and no reuse across incompatible new mass policies. QZ agreement is algebraic evidence, not qualification or spectrum completeness.

Root adopted the NEW S3 kinetic approximation, with other bubble S3 families excluded. No further source-level blocking correctness objection was found within that narrow coordinate/mass contract. The integrated author code and actual check logs still need independent review; approximation/convergence evidence remains open. This OpenAI-family reviewer is a different author, not different-model-family independence; any mandatory family-specific gate remains unmet. No numerical gate has been consumed here.

## Inspected source SHA256

All paths relative to src/anysolver; hashes captured during assessment.

| Source | SHA256 |
|---|---|
| _stiffened_shell_ge_reference_modal.py | 9276AF9CBA1436A56D904ECFCB80EBF6401DB521130FA624BED6394B59DCA57D |
| _stiffened_shell_physical_q4_mass.py | 66B174BADE92F322DD87CB194292AAA3179A9A59D2E217C2D2A77DC04DF7B2F5 |
| _ge_beam3_p5_centered/mass.py | F1F0DE6EB24D8759B0F4C6D4515D65C5C7BB7487354ED4637BA07AD9D5D403B5 |
| _ge_beam3_retained_fibre.py | 8502CE1F85474002CFA15D6CA3DCADE9C837A8CD764C2EC19DC1C6E349184BAB |
| _ge_beam3_fibre_section.py | 2C8BA8C72252515BAD3051C0BB0E8ED61A5563C2CE1854601C87BA6E09248824 |
| _ge_beam3_centered_reference.py | 9187333942931213A01FDCA90DD4D7F44850304370EF4452DE505A3193904758 |
| e4_pl_s3_v2c_element.py | 39CB171AA31F432EB937AF972B30D709B5A51BFD5A977B51AC459B52B61AA8D8 |
| e4_pl_s3_v2d_element.py | 13BA4B7BA3A34DF714AB0A981E770A005242A88BF175DC6328BD3EBCAAD90A59 |
| e4_pl_s3_element.py (separate excluded bubble family) | E2A8495B08E66EE95F7E6BAE0899322FEDC1CC2862A958C3D3605B3192F8FF25 |
| _stiffened_shell_ge_experimental.py | 6D5BE44F86CE443EDD65861DE074735B51E8F573E5C1B053675927BA2B680281 |

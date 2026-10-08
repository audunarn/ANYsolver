# G0 F05 Q4 fixed-predecessor algorithmic pullback diagnostic

21 September 2026. This is a bounded **Q4 feasibility** check following
the S3-V2D v1 local experiment, not a production plastic-shell adapter,
mixed-model admission, or G0B pass. Freeze
`scripts/probe_b3_ge_e4_pl_g0_f05_q4_pullback_v1.py` in the integration
branch and obtain independent pre-execution review. The exclusive
one-time raw root is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f05-q4-v1/`.
Use one BLAS thread and a separate explicit writable Numba cache. Record
source hash, imported package path, dependency versions and raw hashes.
The manifest also binds the exact frozen source commit and hashes of the
deformation, pose/AD, Q4 element, state, material and model modules.
Include the `plasticity.py` return map. Check the tracked probe and
mechanical modules are clean before creating the exclusive evidence root.

Use the existing qualified Q4 element and DNV C208 J2 law unchanged:
square `(0,0,0),(1,0,0),(1,1,0),(0,1,0)` m, shell thickness `.02` m,
three layers, `E=210 GPa`, `nu=.3`, density `7850 kg/m³`; curve
`sigma_prop=100 MPa`, `sigma_yield=105 MPa`, `sigma_yield_2=110 MPa`,
`eps_p_y1=.005`, `eps_p_y2=.010`, `K=400 MPa`, `n=.20`, and Q4 material
`yield_stress=100 MPa`. Starting from virgin material, obtain the
loaded local predecessor via the full deformation map from a *global*
configuration with `.004` m nodal x at nodes 2 and 3 and z `.0004`,
`.0007` m at nodes 2 and 3. Evaluate and seal its complete material
history as the accepted predecessor. The subsequent global trial adds
x displacements
`.0002`, `.00015` m and z displacements `.00004`, `.00005` m at those
nodes, and rotation vectors by node `(0.003,-0.002,0.001)`,
`(-0.001,0.002,-0.003)`, `(0.001,0.001,0.002)`,
`(0.002,-0.001,0.003)`. All trial evaluations start from the same
unchanged accepted predecessor; no tangent promotion may commit it.

For the complete Procrustes shell deformation map `d(q)`, assemble the
coordinate pullback from the local algorithmic force/tangent of this
same predecessor:

`g=D.T f`, `H=D.T K_alg D + sum_i f_i Hess(d_i)`.

Compare `H v` against central differences of `g(q±h v)` for the two
unit directions proportional to `sin(i+.3)` and `cos(.4+.73i)` over
24 coordinates and `h=(2e-6,2e-7,2e-8)`; each direction must have two
adjacent steps with relative error at most `1e-5`, denominator
`max(1,||numeric||)`. Require increasing `alpha` in at least one material
station, a matching sampled `alpha`-active mask between base and both
perturbations at the two adjacent passing steps, bitwise-identical
serialized predecessor before/after all trials, and finite force/tangent.
Report tangent skew but do not impose conservative symmetry on active
plasticity. Preserve any typed failure
with nonzero exit; nonfinite base/perturbed material state, response, or
derivative error is a typed failure. No retry under this root.

The previous elastic-only variational adapter guard is unchanged. This
checks directional derivatives at a Q4 plastic-updating point with
sampled active-mask continuity and one deformation-map pullback; a
smooth return-map branch across the complete perturbation interval is
not proved. Other active-branch changes, mixed element/global assembly,
shell/beam coupled
state ownership, attachments, rejects/restarts and independent mechanical
review remain required for F05/G0B.

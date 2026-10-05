# F03 independent membrane feasibility screen

21 September 2026. **Unregistered exploratory operator comparison, not
F03/G0B qualification or a coupled reference solve.** Source commit
`44b6699`, script `scripts/probe_b3_ge_e4_pl_g0_f03_independent_membrane.py`
SHA-256 `bbb217fcafd95871e4c6648e0ce99ece8ab96ede7ed2b1d95d156d982fd65396`.
The eight complete JSON records from a Python 3.13.9 source-import run are
preserved at
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-independent-membrane-v1.jsonl`,
SHA-256 `7bdfaddfd5199946da12d71a66aa1ac029c62a1df7f55737852450e03c1282f9`.
The process exited zero. It does not contain a mixed load/coupling result.

The separately implemented isotropic plane-stress operator uses Q4 bilinear
shape derivatives and 2×2 Gauss integration, or S3 constant barycentric
gradients, at thickness 0.07 m. It extracts the E4-PL physical in-plane
`ux,uy` block and checks the same rectangular/triangular patches. The S3
matrix agrees to `7.32e-17` relative Frobenius error. The Q4 matrix differs
by `0.113431` on the rectangular patch; three affine membrane-strain energy
tests nevertheless agree within `3.55e-16`. A Q4 bilinear nonaffine nodal
field gives an E4/classical energy ratio `0.936782`. No single-triangle
"nonaffine" claim is made: all three-node displacement data interpolate
affinely there.

An independently assembled 2-row panel with the fixture's geometric recipe
and supported index map gives these relative free-matrix differences and
unit center-y-load compliance ratios (E4 / classical):

| Topology | `N_s` | Relative matrix difference | Compliance ratio |
|---|---:|---:|---:|
| Q4 | 1 | 0.090074 | 1.002739 |
| Q4 | 2 | 0.107465 | 1.054271 |
| Q4 | 4 | 0.106887 | 1.098656 |
| S3-V2D | 1–4 | ≤ `1.99e-16` | within `1.8e-15` of 1 |

The fixed 2-row shell and x-only refinement do not establish convergence
of classical Q4 to E4's finite-mesh response. Classical Q4 cannot serve as
an exact discrete Q4 oracle merely because its affine patch passes. A
resolved continuum comparison must refine both in-plane directions,
separately document the shell formulation difference, and qualify coupled
beam/trace/loads and physical response. S3 membrane parity is a useful
independent suboperator check, not a full S3 coupled reference. The panel
probe shares the fixture's free-index map and geometric recipe, so it is
not wholly independent of fixture construction.

Independent read-only source review checked Q4/S3 derivatives, quadrature,
plane-stress law, thickness, channel extraction, and panel connectivity;
it found the Q4 difference mechanically credible given E4's 35-field
stationary condensation. The reviewer did not execute the probe. The
observed magnitudes are from the source-pinned run above, not the review.

An executable CalculiX 2.23 binary is present and hash-matches G0A, but its
existing runner verifies only a pressure plate. A planar CPS4/CPS3 and U1
general-section beam with explicit four-sample tie equations could supply
an **auxiliary external continuum comparison** after execution and joint
refinement. Its two-node beam rotation, standard plane-stress discretization,
and finite collocation constraints differ from the native retained B3,
E4-PL Q4 and continuous signed line law. Independent feasibility review
found this route plausible under the [official CalculiX U1/general-section
documentation](https://www.dhondt.de/ccx_2.22.pdf), but no mixed deck was
generated or run. F03 still requires the matched physical response and
signed-stability evidence in `B3_GE_E4_PL_G0_F03_NEXT_REFERENCE_CONTRACT.md`.

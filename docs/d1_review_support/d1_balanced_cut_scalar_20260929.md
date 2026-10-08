# Balanced cut-front scalar pressure control — development evidence

**29 September 2026. No production mechanics or D1 acceptance change.**
The saved shell pressure check refined x from 16 to 32 while retaining eight
nonuniform y cells. Its weakest pressure mode lies on the clipped rim row.
This independent scalar control asks whether a similar collapse is observed
when **both** directions refine and the cut crosses the same fraction of a
cell at every level. It does not replay accepted shell poses or establish a
shell trace-space inf-sup bound.

## Declared family and checks

Use the unit square, Q1 displacement and pressure, `w=0` on x=0, natural
conditions elsewhere, and energy `∫|∇w|²`. Contact extends to `y=.9`.
At 16×16, 32×32 and 64×64, adjust the intersected y-cell so the cut is
always 0.1 of a cell above its lower knot. Its cell height equals the x-cell
width. Adjacent y-cell widths remain 0.3–1.7 times x width across the family;
the explicit admission bound is 0.25–2.0. The pressure subspace consists of
the Q1 hats at the first node above the cut with x node positions ≥.65.
These hats have positive clipped support. Test both the full declared row
subspace and one signed x-alternating pressure direction. Signed directions
are admissible local perturbations of a strictly positive active pressure.

Construct discrete work from the clipped Q1 mass and scalar stiffness from
tensor-product Q1 gradient energy. A separate 2×2 element quadrature checks
the stiffness work. Compare to the existing analytic Q1/Fourier reference and
Parseval remainder. Use 512 modes per axis at 16/32 and, prospectively from
the 32-level tail, 1024 at 64 so the 10% tail preflight remains useful.
The reported intervals bracket the squared discrete/continuum dual-response
ratio for this scalar problem; floating-point eigensolves do not outward-round
them.
The `x≥.65` node cutoff begins at x=.6875 on the 16 grid and x=.65625
on the 32/64 grids. The Q1 support extent is therefore not identical across
levels; small differences cannot be attributed solely to mesh width.

| Cells | Active cut-row modes | Shape ratio min–max | Worst subspace ratio interval | Alternating-mode ratio interval | Largest relative Fourier tail |
|---:|---:|---:|---:|---:|---:|
| 16×16 | 6 | 0.7–1.3 | `[0.562864,0.567761]` | `[0.771685,0.775157]` | 0.872% |
| 32×32 | 12 | 0.3–1.7 | `[0.495585,0.513466]` | `[0.664360,0.679975]` | 3.610% |
| 64×64 | 23 | 0.5–1.5 | `[0.519147,0.538025]` | `[0.627809,0.645220]` | 3.637% |

All three discrete response residuals are below 3.7e-14 relative; raw
compliance symmetry errors are below 4e-16. Separate element energy agrees
within 6e-15 relative. The Q1 mass matches the independently implemented
Fourier helper's Gram to floating-point zero in these fixtures. These checks
support the scalar calculation, not its transfer to general shells.
An independent read-only reviewer found no consequential assembly or
interval-direction defect and verified the clamp, cut phase, shape bounds and
element-energy check. The work check uses the assembled clipped mass;
Fourier Gram supplies a separate integration comparison, not an independent
virtual-work quadrature. The full pressure cone, shell and two-body mechanics,
and coupled equilibrium are outside this scalar subspace.

The final common probe SHA-256 is
`ed11a12160e7d930f6090dae7a2c5b2fee9cd5a5fea0bec24cae9b899279fb5e`;
the Fourier helper SHA-256 is
`2a323715a85a15e5299f844343f9e6b67ca4583d0699eea4fa079b6c37dcdc96`.
Run source: `2f08ec2b079933af0819149f43a8178d15495b71` plus the
uncommitted offline probe. The [16](d1_balanced_cut_16_v2_20260929.json),
[32](d1_balanced_cut_32_v2_20260929.json) and
[64](d1_balanced_cut_64_20260929.json) raw records include the complete
mode, support, mesh and environment fields. Their resource records show
0.505 s / 63.98 MB, 0.571 s / 64.60 MB and 1.000 s / 465.04 MB
process-tree peaks respectively, under 180 s / 1 GB. The initial valid
16/32 exploratory outputs used 512 modes at both levels before the 64-level
reference-resolution policy was added; they remain preserved separately.

## Decision

The worst-row intervals are **nonmonotone** across these three balanced
levels. The prescribed alternating direction decreases, but its upper bound
at 64 is still about 0.645. This bounded family neither constructs a
destabilizing sequence nor proves a positive uniform lower bound. It does
not justify changing the primal Q1 pressure law. The earlier x-only saved
comparison, changing near-rim geometry and unresolved prescribed-edge
quotient must not be collapsed into one numerical stability claim. Stop this
mesh batch; the next useful work is an analytic macroelement/Fortin bound or
an explicit cut-row counterexample with a declared shape-regular family,
then a shell-specific qualification design. No additional mesh level or
coupled run follows automatically.
The minimizing coefficient modes alternate along the cut row with growing
amplitude toward the free right edge; they are not periodic interior
checkerboard certificates.

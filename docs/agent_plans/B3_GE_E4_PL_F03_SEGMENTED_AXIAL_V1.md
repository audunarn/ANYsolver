# F03 segmented-transverse axial diagnostic V1

24 September 2026. This is a Level-A development experiment under
`ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1`. It does not consume the
formal F03 run authority, establish a physical reference target, or qualify
the native B3-GE/E4-PL coupling.

## Question and method

The previous independent classical-shell comparator used a global Legendre
basis across the one-metre transverse panel width. Its four attachment
samples occur on material lines at `y=±0.23 m`, where the weak line traction
can allow a transverse derivative jump. This revision keeps the same
plane-stress energy, x Fourier-sine basis, separate classical beam, P1
three-channel exact weak line and loading. It replaces only the y basis with
three continuous Gauss-Lobatto spectral elements whose boundaries coincide
with `-0.23` and `+0.23 m`. Displacements are continuous and derivative
jumps are admitted. It does not add a penalty or change the physical model.

The optional basis is implemented in
`scripts/_b3_e4_f03_segmented_y.py` and selected with
`--segmented-degree`; the historical global `--ny` route is unchanged.
The basis has `3p+1` coordinates for degree `p`. Exact polynomial quadrature
forms its physical mass, derivative and mixed matrices. The same actual
four-sample pose feeds the coupling and gap checks. Edge-stress diagnostic
moments use the new basis's integrated constant and first moment.

## Verification and raw evidence

Five new focused checks and the four existing global-basis checks passed
(`9/9`). They cover nodal interpolation, continuity, partition and linear
reproduction, integration by parts, direct physical quadrature of the
transverse matrices, independently integrated two-dimensional shell strain
energy, sampled pose, and direct line virtual work. Replaying the retained
`nx64,ny16,beam128,mortar128` global-basis case reproduced its tip, energies,
work and gap values exactly at displayed precision.

Fourteen serial guarded segmented runs completed with no failed status.
Each immutable root under `docs/agent_plans/` is named
`B3_GE_E4_PL_F03_SEGMENTED_NX{nx}_P{p}_B{beam}_M{mortar}_V1/` and holds
the manifest, source hashes, invoked command, stdout/stderr, parsed result,
status and sampled child RSS. The runner used one numerical thread, an 8 GiB
sampled-child-RSS limit and a 300 s wall limit. Maximum sampled child RSS
was 3.394 GiB and maximum elapsed wall time was 50.78 s. Sampled RSS is not
a hard memory peak or process-tree total. All measurements are exploratory,
not benchmark speedups.

Source SHA-256 for the 14 runs:

| Source | SHA-256 |
|---|---|
| `b3_e4_f03_spectral_axial_reference.py` | `32fd1aa290c8de5e2ecffeb3b2bb8317da65afcd5bc1e4be2364c2d6b6876b29` |
| `_b3_e4_f03_segmented_y.py` | `04a904a6db4a23edf011550ecdf9a2864a0117872d747f1d1e94f1961126db3f` |
| `b3_e4_f03_spectral_guarded.py` | `3b1f1a0cb72fa75c47fcc2e71d932f2f127b83192f31e284756e27367bca431c` |

All run manifests name predecessor source revision `42b6d069` and bind the
working source bytes above; the final development commit is a later identity.

## Observations

At `nx=64`, beam 128 and mortar 128, increasing segmented degree produces:

| p | Beam tip axial (m) | Shell energy (J) | Beam energy (J) | Root axial (N) |
|---:|---:|---:|---:|---:|
| 2 | `-3.445772e-7` | `0.004747386` | `0.000371576` | `-9777.46` |
| 4 | `-3.387508e-7` | `0.004880667` | `0.000426023` | `-8996.52` |
| 6 | `-3.371564e-7` | `0.004895723` | `0.000439935` | `-8783.76` |
| 8 | `-3.367842e-7` | `0.004899016` | `0.000444048` | `-8726.14` |
| 12 | `-3.366832e-7` | `0.004899881` | `0.000445338` | `-8709.16` |
| 16 | `-3.366802e-7` | `0.004899907` | `0.000445382` | `-8708.61` |

At that fixed x/beam/mortar resolution, p12→16 changes beam energy by
`0.0098%` and root force magnitude by `0.0063%`. This is markedly more
stable in y than the retained global-Legendre screen. It supports the
interface-aligned basis as a more efficient development comparator at this
fixed resolution, not as an accepted continuum target.

Other refinements remain material. With p12, nx64 and beam128, mortar
`64→128→256` gives beam energy `0.000466693→0.000445338→0.000428002 J`,
an adjacent decrease of `4.58%` then `3.89%`; root axial magnitude also
changes. Holding p12, beam128 and mortar256, x modes `64→96→128` give
beam energy `0.000428002→0.000438303→0.000445788 J`, adjacent increases
of `2.41%` then `1.71%`. At nx64/p12, refining beam elements 128→256
changes beam energy by `0.57%` for mortar128 and `2.05%` for mortar256.
Thus x, beam and multiplier resolutions interact. A small assembled weak
row (`~1e-23`), work discrepancy (`<1e-12` relative), or sampled gap
does not resolve their physical convergence.

A further matched-beam-resolution screen uses `(nx,p,beam,mortar)=
(128,12,512,256)`. Against the separately assembled classical Q4
`n=256`, beam512, mortar256 case, the segmented comparator differs by
`0.68%` in tip magnitude, `0.069%` in shell energy, `2.12%` in beam
energy and `3.34%` in root axial magnitude. Against its CST counterpart,
the differences are `0.59%`, `0.011%`, `1.25%` and `2.68%`. These are
development comparisons of distinct shell discretizations at finite
resolution. Their force/beam-energy differences remain larger than the
prospective physical-reference threshold; neither is promoted as a
converged target.

## Decision and next technical action

Retain this separate classical-shell diagnostic as an independent
development comparator. Do not select a native shell trace, line multiplier
space, or physical acceptance target from it yet. Before formal F03
assessment, resolve the longitudinal and line-resolution interaction with
a matched physical reference and a reviewed interface-stability
interpretation. In particular, test whether the remaining changes follow
the finite x trace, beam interpolation, multiplier resolution, or their
combination; preserve any contrary evidence. F03/G0B remain open and G1 is
barred. The mandatory torque/shear, signed stability, full mesh-ratio and
executed external comparisons remain open.

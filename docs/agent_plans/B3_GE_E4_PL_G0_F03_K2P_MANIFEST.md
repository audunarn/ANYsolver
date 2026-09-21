# F03-K2P: fixed-load physical KKT diagnostic registration contract

21 September 2026. **Preexecution design, no registered execution yet.**
K2P tests actual planar physical response of two K1 rank-eligible exact
multiplier bases. It is a bounded subexperiment of the reviewed
[`K2 design`](B3_GE_E4_PL_G0_F03_K2_DESIGN.md), **not** its conditional
`H^-1/2` norm or exact-retained stability qualification, and cannot select
the production F03 six-channel line law or close G0.

## Frozen physical case inventory

Preserve K0's native retained B3 generalized elastic section, two-rail
physical in-plane E4-PL Q4 and S3-V2D panels, supports, reference trace,
section and shell properties, characteristic length `ℓ=.46 m`, and exact
signed KKT. Use K1's clipped physical shell-grid knots and separate
host/diagonal integration subdivisions. Compare P1-beam and
P1-shell-grid on 26 meshes: Q4 and S3-V2D, `N_b=4,8,16` at
`N_s/N_b=.5,1,2`, plus `N_b=8` at ratios `.125,.25,4,8`.
This yields 52 candidate matrices and 104 registered load cases if all
admit a solve. The four reciprocal-reach ratios have only one level each;
do not claim 1:8 convergence from them.

Every matrix receives these **unchanged continuum** beam line densities on
the actual native lifted `y` trace, with `f0=10^6 N/m`, `L0=1 m`:

```text
smooth: f0 [1 + 0.25 cos(2πs/L0)]
sine:   f0 sin(2πs/L0)
```

The sine's net resultant is zero. Normalize forces by `f0 L0`,
displacements and pointwise gaps by `u*=f0L0/(Et)`, weak constraints by
`sqrt(L0)u*`, and virtual work by `W0=f0u*L0`; never divide by the signed
resultant. Assemble loads using eight-point Gauss on the split integration
segments. Independently recompute each smooth and sine reduced/full native
load vector with twelve-point Gauss on identical segments. Require their
work-scaled vector relative differences `<=1e-10`. Record the legacy K0
smooth four-point load difference separately and check its same-rule parity
`<=1e-12` (both full and reduced vectors); the legacy four-point vector is
not the K2P load.

At `s=0,.125,.25,.375,.5,.625,.75,.875,1`, record beam and shell
linearized planar traces, with yaw converted to metres, and their gap.
Also record all segmented four-point gap samples, maximum and `L²` gaps,
multiplier coefficients and oscillation diagnostics, aggregate support
wrench, force/moment balance about a common origin, shell physical energy,
assembled constrained multiplier work `λᵀCq` and its quadrature discrepancy;
this near-zero work is not an independent energy-transfer observable. Retain the existing
native assembly parity and complete KKT residual, signed Schur spectra,
physical-only spectra, conditioning, reduced/full native coordinate scales and retained
coordinates. Individual support-node reactions require later qualification.
These are linearized-source diagnostics;
finite nonlinear pose and six-channel objectivity need later proof.

## Local numerical classification

Record typed rank/mass/reference/numerical failures per case without
stopping another valid case. Do not classify a programming, ownership,
memory or cancellation error as a constitutive/KKT candidate failure.
For a local diagnostic row, preserve K0 limits: symmetric-coordinate
skew `<=1e-10`; positive reduced physical `K_e` minimum/maximum ratio
`>1e-12`; scaled full KKT minimum/maximum singular ratio `>1e-12`;
free equilibrium `<=1e-9`, weak residual `<=1e-10`, interface work
`<=1e-10`, reference gaps `<=1e-12` m/rad, support force/moment
balance `<=1e-8`, and coupling quadrature `<=1e-10`. Report exact
`-S_r` and physical-only spectra separately. A forward sparse/condensed
solution difference `>1e-10` remains **PARITY_OPEN** even when residuals
are small. D1's conditioning diagnosis never waives that failure.

There is deliberately **no K2P convergence pass**: a three-level response
trend is reported together with an independent-reference requirement.
The old half-cell alternating load is omitted because its wavelength
changes under refinement. Do not replace it with the fixed sine history
in historical K0 evidence. No `H^-1/2` metric, full retained inf-sup,
plasticity, eccentric six-channel law or nonlinear state is claimed here.

## Provenance, resources and terminal decision

Commit and independently review exact source before registration. Bind
the clean commit, K0/D1/K1 predecessor source and evidence identities,
new probe/runner/supervisor/manifest hashes, 363-path solver tree hash,
Python and dependent versions, source and installed package identities,
loaded threadpools, one-thread environment, Numba cache, hardware,
cases, limits and exact cold evidence path. Use a 7200 s external wall
and 8 GiB sampled child-RSS limit; the sample is not a hard instantaneous
peak. Fsync start, each of 26 meshes and terminal to an exclusively
created JSONL file; the supervisor independently checks exact record
grammar, process exit, logs/hashes and resource violations. Preserve an
aborted attempt and correct it under a newly reviewed registration.

Independent postexecution review recomputes inventory/statuses, load
quadrature, result/force/work normalization, physical trends and exact
evidence identity. A completed diagnostic prioritizes further mechanics
research; it does not accept F03 or advance to G1.

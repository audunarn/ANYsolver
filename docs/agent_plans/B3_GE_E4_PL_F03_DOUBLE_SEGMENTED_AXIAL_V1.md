# F03 double-segmented classical axial diagnostic V1

24 September 2026. Level-A development evidence under
`ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1`; no formal F03 authority
was used. This continues the independently assembled classical plane-stress
shell / classical beam / exact P1 weak-line comparator. It is not a native
B3-GE/E4-PL result or a qualified continuum target.

## Mechanical change and checks

The shell now optionally uses a continuous Gauss-Lobatto basis in x, with
zero values at both supported edges and breaks at
`[-0.5,-0.2,0.2,0.8,1.2,1.5] m`. These are the ends swept by the
four fixed material samples. The previously developed y basis has breaks at
`±0.23 m`. The two-dimensional plane-stress energy and sample/beam/line
work laws are unchanged. The line and physical-gap integrations split at
the two interior material stations where samples cross x-element edges.
There is no penalty, artificial stiffness or altered load.

Four focused x-basis tests passed: continuous shared interpolation and
Dirichlet edges, direct mass/derivative quadrature, independent full-shell
strain-energy integration, and independently integrated line virtual work
across the crossing stations. Along with all nine prior reference tests,
the affected suite passed **13/13**. The recorded global-basis case again
reproduced six physical observables exactly.

Eight serial guarded double-segmented runs completed. Raw evidence roots are
`docs/agent_plans/B3_GE_E4_PL_F03_DOUBLE_SEGMENTED_XP{x}_YP12_B{beam}_M{mortar}_V1/`.
Each root has the invoked command, source hashes, thread/dependency identity,
stdout/stderr, parsed result, status, 8 GiB sampled-child RSS limit and
300-second wall limit. Largest sampled child RSS was **1.432 GiB**; longest
elapsed time was **40.34 s**. Sampled RSS is not a hard peak or process-tree
total. All manifests bind predecessor source revision `f0e86951` and the
exact working source bytes below, not a post-hoc source claim.

| Source | SHA-256 |
|---|---|
| `b3_e4_f03_spectral_axial_reference.py` | `e353ebd25b853b4954ffda2297c3088837693a59c1c5a168bbf47faa51ca78d7` |
| `_b3_e4_f03_segmented_y.py` | `04a904a6db4a23edf011550ecdf9a2864a0117872d747f1d1e94f1961126db3f` |
| `_b3_e4_f03_segmented_x.py` | `8f86bc2e11ca892ff7d2727a339b99db8b2c82bbdc20e8125bc7b7ef25f8c81b` |
| `b3_e4_f03_spectral_guarded.py` | `c3da1516db107c5b9bfebb37aeb8171e2e550630fb5a8ea10edcdf128b5dc37a` |
| `_b3_e4_f03_independent_beam.py` | `f0ff2d55536b108260162d0fdc08bd8a4df0683cc4328b35e221d3533760d43c` |

## Physical observations

Holding y degree 12, beam 256 and mortar 256:

| x degree | Free x coordinates | Tip axial (m) | Beam energy (J) | Root axial (N) |
|---:|---:|---:|---:|---:|
| 4 | 19 | `-3.363232e-7` | `0.000444649` | `-8588.93` |
| 8 | 39 | `-3.341156e-7` | `0.000467633` | `-8274.55` |
| 12 | 59 | `-3.339374e-7` | `0.000470401` | `-8225.62` |
| 16 | 79 | `-3.336835e-7` | `0.000470625` | `-8209.02` |
| 24 | 119 | `-3.335749e-7` | `0.000471737` | `-8180.94` |

The corresponding global-sine x64/y12/beam256/mortar256 result had beam
energy `0.000436767 J` and root force `-8786.62 N`. Interface-aligned x
changes these quantities materially while retaining internal numerical
consistency. At the two finest x orders, beam energy still changes `0.236%`
and root magnitude `0.342%`; no asymptotic target is established.

At beam512/mortar256, x degree 16→24 changes beam energy
`0.000471163→0.000472403 J` and root axial force
`-8205.90→-8176.54 N`. At degree 24, the tip magnitude and root-force
magnitude differ from the separately assembled Q4 n256/beam512/mortar256
case by `+0.195%` and `-0.133%`; shell energy differs `+0.289%` and beam
energy `+1.722%`. Agreement of two channels does not qualify the whole
response, especially because the Q4 comparison is itself finite-resolution.

At fixed x degree24/y degree12/beam512, mortar128→256 changes beam energy
`0.000481813→0.000472403 J` (**-1.95%**) and root-force magnitude
`8079.42→8176.54 N` (**+1.20%**). The physical-gap L2 drops by about
75%, but that does not make the two discrete structural responses equivalent.
The line-resolution interaction remains an explicit adverse finding.

## Decision

Retain the double-segmented classical comparator as an exploratory physical
reference route. Do not select a native shell pose, multiplier space, or
acceptance target from it yet. A next diagnostic should isolate and bound
the multiplier-resolution effect at fixed x/y/beam spaces, and check
physical work, root force and beam energy together; a more resolved Q4/CST
comparison may also be needed. The signed native KKT floor trend, physical
torque/shear and full mesh-ratio checks remain independent open questions.
**F03/G0B remain open, and G1 is barred.**

# Two native physical-fibre beams and two connected S3 patches

5 October 2026. Development-tested subset; no native engineering acceptance or
release. Parent `3692f237`. [Exact evidence](two_beam_two_patch_summary.json).

The existing example's `two_beams=True, two_facets=True` definition constructs
four explicit physical pairs with beam indices `(0,0,1,1)`. All 84 native
coordinates and 24 shell coordinates remain in the coupled system. There is no
single-patch restriction, separate per-pair solve or internal condensation.
Default identities and production core bytes are unchanged.

The parameterized runner now covers one/two patches. Its independent analytic
energy integrates the correct negative/positive native cell with the corresponding
local coordinate and retained rotation. Adaptive axial integration and independent
angular refinement remain separate from production quadrature. Previously passed
one-patch controls are rerun only where this reference implementation changed.

| Installed route | Elapsed s | Peak bytes | Result |
|---|---:|---:|---|
| Local one/two-patch controls | 18.648 | 185274368 | 2 passed |
| Actual four-pair first target | 78.662 | 184262656 | passed |
| Saved-state gap/wrench/recovery/binding | 4.846 | 186355712 | passed |

Native limits remain 120 seconds/953 MiB from construction including idle; JIT is
disabled and numerical pools are one. The explicit 8e7 Pa/m normal law, 30 um gap
budget, 64-interval cap and existing integration/equilibrium gates are unchanged.
Imported paths are verified in raw records. No full coupled solve was repeated.

Local tangent errors are 1.670343e-8 and 4.152039e-9; independent virtual-work
errors are 8.736615e-8 and 2.209390e-8, below 1e-5. The assembled shared-target
maps preserve both-body residuals and retained-coordinate derivatives.

Actual solve: 46 candidate requests, 76 pair evaluations, 27 reuse hits and no
trial failures. Both beams contact their right facets and have independent plastic
histories; the left facets remain open with zero reactions. Sixteen fibre stations
yield. Virgin-origin rational constitutive reconstruction, monotone committed
state, equilibrium and exact checkpoint replay pass. Equilibrium norms are
2.205365e-14, 8.859154e-17 and 1.286601e-14 against 1e-10.

Independent per-pair physical gaps are +112.334912 um, -6.264237 um,
+108.243011 um and -4.544035 um. They meet the dimensional gate and lie above
production lower bounds. Complete support/load force and moment balance errors
are 3.690407e-12 and 2.775026e-12 on the retained 0.008 N / 0.02 Nm scales.
CLI recovery preserves both element histories and matches independent rational
stored energy, plastic dissipation and incremental potential. The one-patch
checkpoint is explicitly rejected under the two-patch definition.

Byte-preserved fixture:
`tests/data/general_contact_native_fibre_s3_plastic_two_beams_two_patches_v1.checkpoint`,
SHA `38263a956e22496693d968c8c3b6a59f91120c94d4a9e412c4624919814bb28b`.

To construct this explicit development definition, use the preceding two-beam
example command with `--two-facets`. To recover this fixture without another
solve, use `--targets 1 --two-beams --two-facets --plastic-fibres
--normal-stiffness 80000000 --integration-budget-policy certified_active
--root-tangent-enclosure-policy anchored`, then the fixture's `--restart` path
and `--recover-material` destination. Defaults do not silently select this profile.

Supporting same-family review found no consequential delta defect. Cached Mistral
remains unavailable. This does not establish simultaneous four-pair active
pressure, spatial/enforcement convergence, broader material admission or native
engineering acceptance. Prior failures and consumed/no-replay authorities remain.
The next implementation slice extends physical-fibre retained work/history to
the existing native beam-beam static owner. Full C0–C9 remains incomplete.

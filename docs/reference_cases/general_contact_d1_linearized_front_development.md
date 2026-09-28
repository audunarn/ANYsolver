# Fixed-geometry linearized contact-front discriminator

**Status:** development evidence, 28 September 2026. No coupled refinement,
pressure acceptance or historical execution authority is changed by this
probe.

## Question and method

The 16→24 and 24→32 Q4 coupled distributed-press states passed their local
equilibrium and gap gates, but pressure-field changes grew near the moving
contact front. This probe asks whether that behavior needs nonlinear motion,
projection changes or load-path effects, or is already present in the
discrete structural/pressure system.

`scripts/general_contact_d1_linearized_front_reference.py` builds the
deformable Q4 strip alone, with the same elastic material, 0.3 N distributed
load, physical dimensions and fixed degrees of freedom as the saved coupled
fixture. The S3 target is fixed and contributes no structural compliance.
It obtains the Q4 structural tangent at zero displacement, independently
integrates the planar Q1 pressure work matrix over the physical overlap
`x∈[0.1,1.1] m, y∈[0.1,1] m`, and solves the nonnegative pressure quadratic
programme. The reference gap is 40 µm. Weighted gap, complementarity,
structural residual and pressure-compliance symmetry are checked.

This calculation shares ANYsolver's Q4 structural tangent and the selected
primal Q1 pressure *space*. Its contact integration and bound-constrained
solve do not call the general-contact kernel. It can separate geometric and
path effects from the linearized discrete response; it cannot independently
qualify shell mechanics, continuum pressure regularity or finite sliding.

The 16-Q4 two-step and 32-Q4 three-step completed press reports were read
without rerunning them. For 24 Q4, the first full-press state of the frozen
four-phase report was read without changing its authority. Full load,
geometry, pressure basis, step and pressure-node identities are checked before
comparison. The 48/64/96/128 cases are **linearized-reference-only** solves.
The raw report and execution log are
`reports/general_contact_d1_linearized_front_16_to_128_validated_dev_20260928.json`
and its `.log` companion.

## Result

| Q4 columns | Relative L2 difference: saved coupled vs linearized | First active reference x | Peak nodal pressure (Pa) | Integrated pressure force (N) |
|---:|---:|---:|---:|---:|
| 16 | 1.61×10⁻⁶ | 0.68750 | 0.5048 | 0.103872 |
| 24 | 2.21×10⁻⁶ | 0.66667 | 0.5975 | 0.103879 |
| 32 | 1.14×10⁻⁵ | 0.65625 | 0.6914 | 0.103857 |
| 48 | coupled run absent | 0.66667 | 0.5266 | 0.103880 |
| 64 | coupled run absent | 0.65625 | 0.6579 | 0.103880 |
| 96 | coupled run absent | 0.65625 | 0.6247 | 0.103883 |
| 128 | coupled run absent | 0.65625 | 0.5922 | 0.103884 |

The linearized 16→24 and 24→32 adjacent full-field changes are 7.04% and
13.82%; front-interval absolute L2 changes are 0.01209 and 0.02791 Pa√m.
They reproduce the saved coupled trends. At 48→64 and 96→128, adjacent
full-field changes are 5.22% and 4.14%; 64→96 rises again to 7.16%.
The 32-Q4 field still differs from the 128-Q4 linearized field by 14.61%
relative full-field L2. The established interior's 32→128 absolute L2
difference is 0.000315 Pa√m, compared with 0.03021 Pa√m in the front interval.

The pressure optimum has 34 through 258 supported modes across these meshes,
with maximum active weighted-gap error below 1.3×10⁻¹² m and reduced
equilibrium residual below 1.7×10⁻¹⁴ N. These are discrete checks. They do
not certify independent physical gap or pressure-space stability.

## Decision

The saved moving-front difference is reproduced by a fixed-geometry,
linearized structural/contact calculation to much less than its mesh-to-mesh
size. Thus nonlinear projection and loading path are not necessary causes
in this fixture. The nonmonotone front sequence also provides no evidence for
a claimed singular peak or an accepted pressure convergence rate.

The next method decision should test front resolution or pressure-space
choices against this cheap linearized system and an independent continuum or
manufactured structural reference. It should preserve the coupled pressure,
gap and response gates. A larger nonlinear run needs a specific candidate and
resource rationale; the old 64-Q4 rejection is not repaired by this probe.

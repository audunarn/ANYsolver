# D1 interior pressure stability — development candidate for review

**Status:** Pre-acceptance design. No threshold or reference has been frozen for a claim-bearing run. Solver source for the new 64-Q4 press is `c0dfc7a1`; the spectrum runner's eight-row fixture validator was extended afterward without changing the solver.

## Question and measure

Does the full supported **interior** nodal Q1 pressure space retain structural work as source resolution changes, using the actual constrained Q4/S3 physical work map? The accepted D1 profile excludes physical rims, prescribed-normal source nodes and positive target-boundary cuts. The previously failed cut-front cases remain D2 evidence.

At a saved pose, let `T` map independent structural coordinates into physical DOFs and let `N` span the null space of the two prescribed target-x controls. For pressure coefficients `p`, use

```text
B = diag(S) D(gbar) T N
K = Nᵀ Tᵀ Kstruct T N
Mij = ∫source Ni Nj dAref
β² = min(p≠0) [pᵀ B K⁻¹ Bᵀ p] / [pᵀ M p]
γ = β² D / hmin⁴,  D = E t³/[12(1−ν²)].
```

`S` is the positive reference nodal support, `gbar` the normalized weighted gap, and `Kstruct` the contact-free constrained structural stiffness. All source and target structural variations retained by `T N` participate. `M` is the exact planar reference Q1 mass over **fully covered** source faces. This uses structural energy and the physical L² pressure norm. The `D/hmin⁴` factor removes the leading small-wavelength bending compliance scale; it is a proposed comparison scale, not a proven stability constant for these mixed shells. For these specimens `E=10⁵ Pa`, `t=0.05 m`, `ν=0.3`; `hmin` is the smaller source cell width.

If the full signed-space Rayleigh minimum has a valid lower bound at a pose, every active-mode subspace at that **same pose and in the same norms** inherits it. This does not transfer a bound between poses, across changing support, or to physical boundary cuts. Rank alone does not supply a quantitative lower bound.

## Accepted press development observations

All three ordinary static force-control cases used 0.04 N interior-distributed loading, perimeter source support, deformable S3 target, physical skins, free source rotations, the fine nodal Q1/monolithic route and the unchanged 50 µm gap budget. The 4×4/two-S3 and 8×4/four-S3 presses were retained from earlier development. The new 8×8/four-S3 press completed both increments in 107.31 s/432 MB with one interior active node, no rim pressure and final certified gap −28.644 µm (sampled −10.015 µm). A 4×2/two-S3 alternative failed at the genuine gap limit before first acceptance and is excluded from this family, not regraded.

| Source / target | Full interior modes | Minimum `β²` | `γ` | Frozen-footprint oracle relative difference |
|---|---:|---:|---:|---:|
| 4×4 Q4 / 2 S3 | 9 | 1.0209094e−5 | 0.00299168 | 4.99e−6 |
| 8×4 Q4 / 4 S3 | 21 | 1.0439886e−6 | 0.00489489 | 1.10e−5 |
| 8×8 Q4 / 4 S3 | 49 | 5.4405332e−7 | 0.00255087 | 1.63e−6 |

The independently clipped oracle freezes the reference XY footprint and vertical work. Its agreement checks a component of the work calculation at these shallow accepted poses. It does not independently validate rotating physical skins or the nonlinear coupled response. The three `γ` values are positive and within a factor of 1.92; they are **development observations**, not a mesh-uniform proof or a retrospective pass.

An additional guarded, offline 8×16 Q4 / four-S3 press completed after this three-mesh screen. It has two active interior pressure nodes and 105 signed interior modes. The same procedure gives `β²=1.7686655e−7` and `γ=0.0132682`; the frozen-footprint oracle differs by 3.64e−6 relative. [Saved coupled pose](d1_coupled_source_y16_20260929.json) and [spectrum](d1_pressure_y16_spectrum_20260929.json). This new point does not create a frozen threshold or establish a uniform bound. Its finer y spacing changes the proposed `D/hmin⁴` scale, so interpret the increase in `γ` with that scaling in mind.

## Retained cut-front loss as a control

The [two-hat counterexample](d1_cut_front_two_hat_counterexample_20260929.md) has fixed source `hmin=0.5 m` and a target rim cutting the upper Q4 row by fraction `θ`. Its saved v4 touching-pose records contain the actual two-body constrained structural energy dual norm for the exact signed pressure combination. The separable physical L² pressure norm follows independently from its stated Q1 coefficients. With `b=θ²/2−θ³/3`, `d=1/4+θ−θ²+θ³/3`, `η=−b/d`, upper/lower y coefficients `1, η, −η/2`, and x-hat coefficients `c₁,c₂`:

```text
Ix = (c₁²+c₂²)/3 + c₁c₂/6
Iy = η²/4 + η²θ + η(1−η)θ² + (1−η)²θ³/3
||p||²L² = Ix Iy.
```

| Cut fraction `θ` | Saved energy dual norm | Exact pressure L² norm | Same `γ` |
|---:|---:|---:|---:|
| 0.100 | 1.8287162e−4 | 8.6784109e−3 | 0.0081324 |
| 0.050 | 2.5563528e−5 | 3.2060617e−3 | 0.0011644 |
| 0.025 | 3.4244343e−6 | 1.1662500e−3 | 0.0001579 |

This reuses the original solver executions and their original failed-law interpretation. It demonstrates that the proposed normalization detects the known boundary-cut deterioration on this family; it does not make the cut case admissible or change its historical verdict.

## Limits and next assessment

- These accepted press poses have one positive pressure mode each. The full signed pressure space was tested, but a moving interior active-set front and lift-off/recontact on a three-mesh family are not qualified yet.
- The target refines from two to four S3 faces, then remains fixed. Three finite meshes do not establish a universal lower bound; structural, pressure and target geometry effects must be separated before a response claim.
- The contact-free structural energy norm is symmetric positive definite in these constrained cases. A nonlinear tangent or an arbitrary frictional state requires a different stability statement.
- The example uses a fixed 50 µm physical-gap budget. The failed 4×2 member shows why a positive operator measure cannot excuse an inadmissible mechanical path.

An independent mechanics review should assess the `D/hmin⁴` normalization, whether the exact cut-front L² expression and held-out control truly test the intended loss, and what quantitative three-mesh criterion can be frozen from physical reasoning. Then define claim-bearing poses, load/support/reference uncertainty, active/open/recontact cases and numeric criteria **before** their formal run. No threshold should be chosen merely to fit the table above.

Raw inputs: [16-Q4 press](d1_pressure_work_16q4_press_20260929.json), [32-Q4 press](d1_interior_pressure_family_8x4_20260929.json), [64-Q4 press](d1_pressure_family_8x8_20260929.json), [accepted-pose spectrum](d1_pressure_accepted_family_spectrum_recheck_20260929.json), and [cut-front v4 values](d1_cut_front_two_hat_touch_010_v4_20260929.json) with corresponding `005` and `0025` files. The earlier validator failure is retained as `d1_pressure_accepted_family_spectrum_20260929.log`.

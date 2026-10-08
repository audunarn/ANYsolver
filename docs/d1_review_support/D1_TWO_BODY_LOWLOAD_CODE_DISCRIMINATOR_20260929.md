# D1 two-body low-load code comparison — failed development discriminator

**29 September 2026. No code-verification acceptance.** The open D1 code
comparison asks for a genuinely two-dimensional coupled Q4/S3 pose against
the independent small-motion Q1 mortar oracle on identical meshes, loads,
supports and pressure space, with a relative `10⁻⁶` target. The previously
completed 12×12/4×4 0.04 N press differed in integrated force by
`3.73×10⁻⁵`; that comparison includes a known linear-oracle versus nonlinear
shell-model difference.

## Bounded fixture decision and result

One 4×4-Q4/4×4-cell-S3, five-times-stiffer deformable target was screened at
0.001 N. With the original 40 µm initial opening, the independent oracle
remained open by 33.19 µm, so no coupled run was made. A single targeted
fixture change translated the entire source reference patch down 35 µm via
the mesh's supported coordinate API. This leaves a nominal 5 µm opening;
all loads, supports, materials, shell thicknesses and meshes stayed fixed.
The independent oracle then selected source node 13, gave integrated force
`0.0001034573746 N` and target vertical motion `3.087 µm`.

The ordinary two-step nonlinear contact route completed in **75.16 s/369 MB**
under the routine 180 s/1 GB cap. Both solvers selected source node 13;
production had no active rim pressure, body contact wrenches balanced near
roundoff, and the independent accepted-pose lower gap was `−1.887 µm`
against the unchanged `−50 µm` budget. The same-mesh comparison was:

| Quantity | Relative difference | Required code-comparison target |
|---|---:|---:|
| Integrated normal force | `1.4322×10⁻⁵` | `≤10⁻⁶` |
| Three source vertical displacements | `1.587–1.595×10⁻⁶` | `≤10⁻⁶` |

**The comparison fails its prospective strict target.** A smaller load and
reduced opening did not remove the discrepancy. The present oracle freezes
the footprint and uses a linear small-motion structural model, while the
production route updates geometry and structural response. The measured
error is consistent with that model difference but does not prove its cause
or excuse the failed criterion. Do not sweep load or clearance to tune a
pass.

A read-only saved-pose decomposition then compared the production moving
work map with the independent frozen-footprint map. At active node 13, the
normalized gap difference is `1.315×10⁻¹¹ m`, reference-support difference
is `5.0×10⁻⁹` relative, and the active weighted-gap work row differs by
`9.79×10⁻⁵` in relative L2 norm. Separately, production von Karman internal
force minus reference linear stiffness times the same displacement has
`5.80×10⁻⁷ N` norm on free coordinates, but only `−2.68×10⁻¹² N` at the
active node's vertical DOF. These quantities show both geometry/work and
structural-model differences. They do **not** allocate the observed
`1.48×10⁻⁹ N` contact-force discrepancy uniquely, because the full coupled
response redistributes residuals. The frozen linear oracle is therefore an
inadequate stand-alone strict nonlinear code oracle for this pose. The next
method decision is an independently assembled contact map with a common
structural operator, or a separately derived nonlinear reference; the former
would verify a local coupled step but would not by itself qualify the full
nonlinear route. [Decomposition](d1_lowload_geometry_decomposition_v2_20260929.json),
[resource](d1_lowload_geometry_decomposition_v2_resource_20260929.json).

[Original open oracle](d1_lowload_code_oracle_20260929.json),
[shifted independent oracle](d1_lowload_clearance5_full_oracle_20260929.json),
[coupled pose](d1_lowload_clearance5_coupled_20260929.json),
[comparison](d1_lowload_clearance5_comparison_20260929.json),
[coupled resource](d1_lowload_clearance5_coupled_resource_20260929.json).
The first oracle probe used an incorrect result key; the first shifted
probe hit the oracle's previous 40 µm opening guard. Their logs are retained
as diagnostic-tool defects, separate from the completed mechanics run.

## Current-skin discriminator

The previously independent current-skin quadrature could only invert Q4
footprints with exactly horizontal rows. This pose has small in-plane Q4
motion, so its first invocation stopped at that oracle assumption. The
oracle was extended with an independent bilinear Q4 inverse; it still uses
its own polygon clipping, physical skin reconstruction and integration.
At the *same saved nonlinear pose*, its reference support differs from
production by at most `1.31×10⁻¹⁴` relatively, and the active normalized
gap differs by `1.90×10⁻¹⁶ m`. Source/target `ux` and `uz` first variations
agree to at most `1.73×10⁻⁸` relatively. The rotational derivatives are
only about `2–3×10⁻⁸ m/rad`; a `10⁻⁶ rad` difference step has roundoff
dominated relative error above `10⁻⁵`, while both `10⁻⁵` and `10⁻⁴ rad`
steps give relative errors below `1.27×10⁻⁶` with identical clipping
topology. The check took `15.96 s/180 MB` under the routine cap.

This closes the *local moving-geometry value/first-variation question* on
the selected smooth pose. It does not turn the failed full-solve linear
comparison into a pass, verify the production tangent at this pose, or
independently derive nonlinear structural equilibrium. The next code
verification method must use a common structural operator with an
independently assembled current contact map, or a genuinely nonlinear
structural oracle; no further load/clearance sweep is justified.
[Current-skin result](d1_lowload_current_skin_v4_20260929.json),
[resource](d1_lowload_current_skin_v4_resource_20260929.json).
An earlier run used the host checkout instead of this worktree, and the
first worktree run met the oracle's horizontal-row assertion. Both logs are
retained as invocation/oracle-scope failures. On the earlier horizontal-row
slide fixture, the generalized inverse preserved independent support to
`2.43×10⁻¹⁴` relative and gap to `7.06×10⁻¹³ m`; the largest scaled
directional difference was `4.92×10⁻⁸`.
[Compatibility resource](d1_current_skin_general_inverse_compat_resource_20260929.json).

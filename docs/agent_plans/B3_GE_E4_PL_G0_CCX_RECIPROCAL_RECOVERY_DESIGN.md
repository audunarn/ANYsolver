# B31/S4 external support-wrench recovery by reciprocal boundary motion

22 September 2026. This is a *development design* for the qualified
external-reference path, not a solved E01/E02 comparison. The existing
stock CalculiX canary runs one conservative, small-displacement elastic
B31/S4 strong-footprint model. Its all-node `RF` omits or mixes MPC force
effects and cannot be used directly as the complete support wrench.

Partition the symmetric linear equilibrium into free coordinates `u` and
prescribed support coordinates `g`. In the loaded state, `g=0`, the only
load is `F_y=1000 N` at beam tip node 48, and the support reaction is `r`.
For an unloaded influence state with prescribed support motion
`g=δa`, work reciprocity gives

```text
δ aᵀ r = -F_y u_tip,y^(a),
aᵀ r = -1000 u_tip,y^(a) / δ.
```

This sign defines reactions as support-on-structure forces/couples. It
requires the same linear model, homogeneous fixed MPC equations, symmetric
work-conjugate tangent and unchanged supports except the prescribed values.
Follower loads, NLGEOM, contact, nonsymmetric laws and dynamic terms need
a different adjoint and are not admitted here.

The ten shell-end nodes have only their 1–3 translations fixed. The first
three shell basis fields move all of those supports by `δ e_x/y/z`,
recovering their force resultant. The last three assign
`δ e_x/y/z × X_i` at each shell support reference position, recovering
their moment about the global origin. The beam root at `(0,0,+0.1 m)` has
DOFs 1–6 fixed; six independent `δ` translation/rotation probes recover
its force and local nodal moment. Convert its moment to the origin by
adding `(0,0,+0.1)×F_root`. All translations use `δ=1e-5 m` and all
rotations `δ=1e-5 rad`, with paired positive and negative solves to check
linearity and reduce printed displacement rounding. The recovery uses
`-1000 (u_tip,y^+ - u_tip,y^-)/(2δ)` for each component.

Analytic total balance for the baseline tip force at `(1,0,+0.1 m)` is:

```text
F_shell + F_root = (0,-1000,0) N
M_shell,origin + M_root + X_root×F_root = (+100,0,-1000) N m.
```

This is an independent output-recovery route relative to printed `RF`,
though global balance alone follows from the same conservative deck and
does not demonstrate native agreement. A rigid combined support motion
gives a separate exact work identity: global `x` rotation makes the tip
`y` translation `-0.1δ`, while global `z` rotation makes it `+1δ`.
Casewise source, deck hashes, solver identity, raw logs, parser, tolerances,
resource bounds and failure-stop policy must be registered **before** runs.
The first separate smoke is a positive beam-root `z` rotation to check that
stock CalculiX accepts the prescribed rotational DOF and prints a finite
unloaded influence response. A successful smoke does not consume or
substitute for the later paired 24-case source-frozen series.

The inert generator preserves all nodes, elements, MPC rows, material,
section and output cards from the canary. It moves the full 36-coordinate
support inventory into `*STEP`, with explicit prescribed values, and removes
the tip load. Nonzero prescribed values outside `*STEP` are invalid under
[CalculiX's boundary-condition contract](https://www.dhondt.de/ccx_2.22.pdf);
the first draft had that error and was corrected before any source freeze or
execution. Pure algebraic tests check work conjugacy, both signs, exact
step-level support inventory and unchanged deck remainder. Printed DAT
translation precision, unreported beam rotations and MPC expansion remain
explicit limits.

The first registered root-rotation smoke (source `4677ac39`, case record
`ccx-3d-root-rotation-smoke-cases-v1`) failed during boundary-card parsing,
before an increment. Its 22-character prescribed value
`1.0000000000000001e-05` exceeded the 20-character numeric field consumed
by CalculiX's boundary reader. This is an input encoding failure, not
evidence for or against rotational support or reciprocal recovery. Preserve
the failed record. A corrected source writes at most 12 significant digits,
checks each field's width and finiteness, and checks its round trip against
the intended motion. Any new smoke has a separate registration and output
identity; the original run cannot be retried or relabelled.

The corrected root-rotation smoke v2 passed its narrow terminal, but the
separately registered 24-case reciprocal series v2 **failed** its physical
wrench screen. All 24 cases completed and paired responses were odd. Total
force and global z moment closed, but the recovered global x moment was
`-193.2416 N m` instead of `+100 N m`. Superposing three saved support
influences into a rigid global x rotation gave tip `u_y=+1.932416e-6 m`
instead of `-1e-6 m`; a footprint interior node likewise missed its rigid
transverse motion. This is a rigid-body patch failure, not printed rounding.

The 12 footprint MPCs use rotational DOFs at beam interior node 47. The
saved CalculiX expansion trace reports no knot at that node. The bundled
2.23 manual (section 10.3.6, PDF page index 696) prohibits rotational MPC
terms at nodes without a knot. The official 2.23 source archive
`ccx_2.23.src.tar.bz2` (SHA-256 `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`)
confirms `gen3dmpc.f` remaps rotational terms to a rotational knot node only
when `rig(node) != 0` (lines 47–75); otherwise the expanded beam path uses
the unremapped direction (lines 290–331). `gen3dnor.f` creates a knot only
when multiple expanded normals occur (line 830). This is a strong source-
consistent explanation, not proof of a unique error mechanism.

Preserve the failed series and registration. Before repeating reciprocal
recovery, derive a mechanically valid connector for the exact B31/S4
expansion, register a **new** source/deck, and require direct rigid x/y/z
motion at all physical nodes, including interior footprint nodes and the
tip. Verify that the printed displacement at the expanded beam tip is work
conjugate to the applied `*CLOAD`. Only then register a new paired support
wrench series. Neither failed nor passed exploratory smoke evidence qualifies
E01/E02 or a native B3-GE/E4-PL comparison.

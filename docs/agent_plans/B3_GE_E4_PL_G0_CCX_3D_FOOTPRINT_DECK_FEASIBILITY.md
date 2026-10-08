# Inert 3D CalculiX footprint decks for E01/E02 design review

22 September 2026. The standalone generator
`scripts/generate_b3_e4_ccx_3d_footprint_feasibility.py` emits eight
**unexecuted** S4/B31 elastic input decks (two signed offsets, four loads)
and a byte-hash manifest into an exclusive new directory. Its no-argument
mode validates the in-memory decks without writing files. Neither mode calls
CalculiX. The output is a small structural feasibility specimen, not a
registered E01/E02 comparison or a selected G0B line/footprint law.

Run from this worktree:

```text
python scripts/generate_b3_e4_ccx_3d_footprint_feasibility.py
python scripts/generate_b3_e4_ccx_3d_footprint_feasibility.py --out-dir <new-empty-path>
```

The panel is `[-0.5,1.5]×[-0.5,0.5] m` at `z=0`, with 32 S4 elements
on a `0.25 m` square grid and `0.07 m` shell thickness. Its two outer
`x` columns have translations fixed; their drilling rotations are not
prescribed. A two-element B31 beam runs from `x=0` to `x=1` at
`z=±0.1 m`, has its root's six coordinates fixed, and has a `0.1×0.1 m`
rectangular section with orientation vector `(0,1,0)`. Both use isotropic
`E=210 GPa`, `ν=0.3`. This explicitly conventional expanded B31/S4 section
and shear idealization is **not** the native generalized B3-GE or B2 physical
section and has no demonstrated quantitative agreement with either.

At the beam's `x=0.5` node, four distinct shell nodes at
`(x,y)=(0.25,-0.25),(0.75,-0.25),(0.75,0.25),(0.25,0.25)` form a
noncollinear footprint. Twelve translation equations, with each distinct
shell translation first as its CalculiX dependent coordinate, impose the
linear rigid material relation

```text
u_shell(X_i) - u_beam(b) - theta_beam × (X_i-b) = 0
b = (0.5,0,sign*0.1),   X_i = (x_i,y_i,0)
```

There is no shell drilling-coordinate equation. For a shell-side multiplier
force `λ_i`, the work-transpose beam force is `-Σλ_i` and its moment about
the beam center is `-Σ[(X_i-b)×λ_i]`; shell force is `+λ_i` at `X_i`.
Hence the two sides cancel force, moment about a shared origin, and virtual
work for every compatible rigid displacement. Opposite in-plane footprint
forces transmit a physical shell-normal `Mz`; opposite out-of-plane forces
transmit a longitudinal `Mx`. The headless validator checks those two unit
couples, both signed-offset rigid patches, unique equation pivots, lever-arm
coefficients, node and element inventory, supports, section cards, and loads.
No moment is applied to a shell drilling degree of freedom.

The four independent terminal load cases are `+1000 N` in global `y`,
`+1000 N` in global `z`, `+1000 N m` about global `z`, and `+1000 N m`
about global `x`, each at beam tip node 48. The manifest gives the analytic
*total* support-wrench target about the global origin, never a predicted
partition among shell edges, beam root, and footprint. Under the `+y` force,
the applied `Mx` is `-100 N m` for positive `z` offset and `+100 N m` for
negative offset. The generated decks request nodal `U` and `RF`; their
interpretation, especially MPC reactions and beam/shell-expanded nodes,
requires an independently reviewed recovery and balance method before use.

These twelve strong point equations intentionally define a rigid footprint,
not the exact weak multiplier line integral, continuous four-sample trace,
or distributing-pose law. Four points at one beam station cannot establish
between-station compatibility. The static Python checks establish only
algebraic deck structure and ideal rigid-work identities. They do not prove
that stock CalculiX accepts the assembled shell/beam MPCs, that the solve is
well conditioned, or that either profile agrees numerically.

Before any external execution, register a separate reviewed E01/E02
contract: pin solver/deck/parser hashes and the profile-specific section,
frame, load, support, offset and attachment meaning; verify a mixed-element
canary and independent output recovery; define shell-edge and beam-root
reaction groups plus interface virtual-work accounting; and freeze signed
response, force/moment, energy, torque/drilling, thickness, and at least
three independent spatial/footprint refinements with absolute floors and
resource limits. Compare B2 and GE only where their physical idealizations
match this comparator. Preserve the failed U1+CPS and unconverged B31/CPS
evidence unchanged. E01/E02, F03/G0B, and G6 remain open.

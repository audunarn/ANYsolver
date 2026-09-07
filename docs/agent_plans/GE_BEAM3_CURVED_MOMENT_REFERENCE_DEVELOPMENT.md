# Curved spatial end-moment reference development

This branch continues private beam development from
`2b92a3696292a1680fda90c998c20be20368e6cc`. It does not qualify, expose, or
activate a formulation. Existing beam/shell mechanics and defaults are unchanged.

## Preserved first reference rehearsal

The first independent-algorithm (not independently authored) continuum IVP
rehearsal produced 11 passes and one failure in 2.05 seconds. Its IVP11 sampled
torsion frame differed from the closed form by up to 2.75125478e-11, exceeding
the unchanged 1e-11 absolute/relative check. No native curved-moment solve ran.

Original source SHA-256:

- `ge_beam3_curved_moment_reference.py`: 13edc5557b44a22732c4c0080cb29a8d9de65bd869a6b622948bbd41af8022f8
- `ge_beam3_curved_moment_fixture.py`: f0b5a082a9058134fea3bba57bb0574b34ebedc7278d0674f9e796f581d62e2d
- `test_ge_beam3_curved_moment_reference.py`: 0473cb7d6ea130225bc66d66d1575286d3e630b3eb99ca05830db873c06bf3b5

The failed XML remains in the original temporary directory and in
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-curved-moment-reference-incident-20260907/unit.xml`:
4598 bytes, SHA-256 E1C4B5FC4B94E2F291BBE90A271F0BDFDAC5BCA1420584405D765C2BD446767F.
This commit preserves the failed source before correction.

## Successor scope

Tighten the reference integration profile to IVP13 (relative 1e-13, absolute
1e-15); retain the old explicit profiles and the invariant acceptance checks.
The reference integrates spatial equilibrium independently of native mechanics,
without director projection, production tangent inspection or fitted parameters.
It is binary64 development evidence, not a multiprecision qualification oracle.

After reference unit checks pass, compare the frozen parabolic cantilever at
1, 2 and 4 macros under three-component spatial end moment (.8,.9,.6), at load
parameters .25, .5 and 1. Preserve complete native checkpoints and compare
geometry, frames and recovered fields with explicitly sampled continuum fields.
Report discrepancies and refinement trends without asserting a qualification
threshold or conservative spectral authority for spatial dead moments.

Every native child must have one numerical-library thread, a 24 GiB process-tree
memory limit, a 600-second wall limit and 120-second inactivity protection.
Use fresh exclusive external outputs; preserve failure logs and retry nothing
automatically. Full qualification and independent scientific review remain pending.

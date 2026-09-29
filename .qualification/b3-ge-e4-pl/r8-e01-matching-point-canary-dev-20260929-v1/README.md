# Inert matching-point E01 feasibility screen

This is an unexecuted development screen, not E01 or G0/G1 qualification.
The previous B31/S4 canary used a four-node rigid footprint and cannot score
M1's six-row point bond. This screen asks whether stock CalculiX can assemble
the matching-station bond on the same flat panel geometry.

The generator `scripts/b3_e4_e01_matching_point_canary.py` (SHA-256
`3b4e79b315fcf7b6da7b729d42fb84788065100dcb6bb97880f50918321653ca`)
emitted two signed-offset input decks from source HEAD `e5129c36`:

| Deck | SHA-256 |
|---|---|
| `point-minus.inp` | `8d2bce2bfa045935373442763df32e6b55d791ad280d6bb0c70edfb01de4ece8` |
| `point-plus.inp` | `71b05b0e6c29dc0e44db9f499bde32ec936b4cb77c526634367601da8e113cb3` |

The six shell nodes, two Q4 cells, five beam stations, three paired edge
stations, root shell support, applied +1000 N global-x tip load, and signed
0.1 m beam-axis offsets match the declared M1 fixture. Each station has
three translation and three rotation equations with a unique beam-coordinate
pivot. The generator's rigid-motion gaps are below `5e-17`; its arbitrary
multiplier wrench imbalance is below `2e-16`. The independent native-joint
Jacobian comparison in `tests/test_b3_e4_e01_matching_point_canary.py`
(SHA-256 `a7387b08995c12f4644c91bcc1dc917d81662f4dc0b9510f84d26f12f5e67b49`)
passed for both offset signs (`2 passed in 1.24s`).

The B31 rectangular section reproduces the native elastic area and two
second moments approximately; shear and torsion equivalence, element
formulation, support reactions and physical output recovery remain unverified.
The decks were not run because separate ANYmesh numerical jobs occupied the
available heavy-job slot. Once clear, execute one deck with the pinned
CalculiX 2.23 binary under a 120 s timeout and one thread, preserve all raw
outputs, and inspect MPC warnings and full-increment status. A successful
solve advances to section/reaction/work interpretation and a prospectively
specified three-level signed-offset E01 comparison. A failed assembly
requires a different external representation. Neither outcome spends F03's
formal execution authority.

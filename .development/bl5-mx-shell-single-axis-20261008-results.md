# Fixed-beam, fixed-interface Mx shell-refinement diagnosis

The executed 8×4×2 CalculiX comparison established external parity for the
same-law C3D20 operator at that resolution. The saved matched 16×8×4 C3D20
level then served as the common base for three **separate** one-axis shell
refinements. The 16×8×4 C3D20 beam, 80 physical five-channel P0 rows, 10 N·m
section-dual torque, shell root, material laws and physical dimensions were
fixed. No CalculiX rerun or formal F03 assessment occurred.

| Shell grid | Changed direction | Resolved work (J) | Change from fixed base | Native / resolved |
|---|---|---:|---:|---:|
| 16×8×4 | Saved base | 0.0010092788470 | — | 0.98283 |
| 16×8×8 | Thickness | 0.0010103296784 | +0.1041% | 0.98181 |
| 16×16×4 | Transverse | 0.0010136732759 | +0.4354% | 0.97857 |
| 32×8×4 | Axial | 0.0010225221404 | +1.3122% | 0.97011 |

Each accepted diagnostic passed the original `1e-8` physical equation,
global/interface wrench and work checks and `1e-9` weak-gap check. The
thickness run's global-wrench ratio was `9.51e-9`, close to its `1e-8`
limit. Its first run failed that guard at `1.077e-8`; a second attempt
recorded the specific failed control, and a third used six instead of three
linear residual-correction passes and passed without changing any criterion.
Both failed attempts and all three successful result/receipt pairs are
preserved in the versioned directories below. The source/result SHA-256,
effective CPU0/one-thread/JIT-off state, process wall and sampled memory are
in each receipt and result.

- [Thickness attempt 1](bl5-mx-shell-thickness-20261008-v1/receipt.json),
  [diagnostic failure](bl5-mx-shell-thickness-20261008-v2/result.json),
  [repaired solve](bl5-mx-shell-thickness-20261008-v3/result.json)
- [Transverse result](bl5-mx-shell-transverse-20261008-v1/result.json)
- [Axial result](bl5-mx-shell-axial-20261008-v1/result.json)

**Decision:** axial shell resolution is a material contributor to the
matched-level resolved-work movement; the 8×4×2 near-match is not evidence
of native agreement. These directional effects are not additive and do not
establish a converged reference. The next bounded discriminator should hold
the 16×8×4 shell fixed and vary the beam/weak trace together according to
the declared production interface rule, comparing work and supported local
transfer. If the discrepancy persists as both domains converge, examine the
continuous native/solid work maps before a multiplier-space selection. No
scientific tolerance, historical failure or formal F03 authority changed.

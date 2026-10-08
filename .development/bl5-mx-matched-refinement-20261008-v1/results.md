# Matched native/C3D20 Mx weak-P0 refinement — development result

This independent linear screen refined native Q4 shells, physical-fibre B3
members, resolved C3D20 shell/bar bodies, and all five P0 multiplier channels
together. It held the 1 m panel and section geometry, 0.03 m beam-to-shell
offset, elastic laws, shell-root restraint and 10 N m section torque fixed.
The four-halfcell native definition exactly matched the saved model identity;
its work reproduced the earlier native result. The indexed solid weak rows
matched the independent coarse row assembler. No CalculiX execution ran at
the finer levels.

| Surface grid / thickness cells | Native Q4 / B3 | Weak rows | Native work | C3D20 work | Native / C3D20 |
|---|---:|---:|---:|---:|---:|
| 4×2 / 1 | 8 / 2 | 20 | `0.001010067 J` | `0.000907426 J` | `1.11311` |
| 8×4 / 2 | 32 / 4 | 40 | `0.000992848 J` | `0.000984473 J` | `1.00851` |
| 16×8 / 4 | 128 / 8 | 80 | `0.000991954 J` | `0.001009279 J` | `0.98283` |

The native work changes by less than `0.1%` between the last two levels, but
the resolved work still changes by about `2.5%`; the ratio crosses unity.
The middle-level near-match is therefore not an accepted accuracy result.
The old coarse-body contrast was strongly mesh-dependent, and the current
resolved reference has not demonstrated convergence. The five-channel weak
law and P0 resolution remain unqualified: small assembled gaps, physical
wrench balance and one matched ratio cannot select them. The next useful
external comparison is an executed finer matched deck with exact section
torque, supports and weak-row provenance; refine its resolved shell enough to
separate discretization movement from a persistent law difference. Do not
run another isolated axial or channel-tuning sweep.

[Receipt](receipt.json) and [raw level outputs](levels/) bind exact source and
saved-input hashes. Observed process wall was `13.05 s`, CPU0, one numerical
thread, JIT disabled, and sampled peak process-tree RSS `658.1 MB`. All three
native and resolved solves passed their equilibrium, weak-gap and work checks;
resolved interface and global wrenches balanced. This is development evidence,
not formal F03, mandatory executed external comparison, or M2 acceptance.

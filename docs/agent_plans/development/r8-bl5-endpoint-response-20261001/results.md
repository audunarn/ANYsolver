# BL5 actual 8:1 endpoint response — development result

The declared five-channel law and complete c2/P0 pairing are retained for
assessment. All nine actual mixed solves completed, with no observed endpoint
solve/work collapse. Torque convergence, completion-sensitive root transfer,
the remaining physical envelope and independent engineering accuracy are still
open. No space selection, F03/M2/G0B acceptance or release follows.

## Fixed experiment and artifact

This completes the existing whole-element beam:shell 8:1 endpoint at three
registered grids. The 1 m × 0.2 m panel, 0.035 m thickness, material/section,
axis height 0.0675 m, direct root supports and Fy=100 N/Mx=10 Nm/Mz=10 Nm loads
are unchanged. Every P0 support spans two shell segments and 32 native
half-cells; all five channels use the same rule. The native member coordinates,
both retained cell rotations and 18 stationary resultants/member remain in the
actual indefinite system. No condensation, artificial inertia or coefficient
change is introduced.

| Shell grid | B3 members | Full q / multiplier rows | Complete process seconds | Sampled peak MiB |
|---|---:|---:|---:|---:|
| 16×4 | 128 | 5,124 / 40 | 19.74 | 201.0 |
| 32×8 | 256 | 11,004 / 80 | 43.93 | 278.2 |
| 64×16 | 512 | 25,068 / 160 | 110.14 | 559.6 |

Each fresh owner uses one eligible factorization and three RHS solves. These
observed route costs include identity checks, preparation, recovery and output;
they are not isolated assembly scaling measurements or a speedup claim.
The supervisor enforces 600 s/8 GiB process-tree limits, serial execution and
requested/effective one BLAS/Numba numerical thread, with JIT disabled.
The unchanged installed solver wheel is
`d99c59ac0464613b15461dcd23c0b8fe158a67fe3b27192a886b6daf6aa981ea`.
All 391 source/wheel/site module bytes and actual imported locations are bound;
four helper snapshots match their source. No product edit or new wheel.

## Response and numerical controls

| Load | Work J, coarse → middle → fine | Last work change | Fine work difference from saved 1:1 |
|---|---|---:|---:|
| Fy | 4.2214630e−4 → 4.2357186e−4 → 4.2413178e−4 | +0.13219% | +0.001792% |
| Mx | 6.3632762e−5 → 6.3731793e−5 → 6.3781382e−5 | +0.07781% | −0.00000405% |
| Mz | 1.7726820e−5 → 1.6894849e−5 → 1.6666036e−5 | −1.35434% | +0.014486% |

Comparison uses the saved growing-P0 matched native case, not an independent
external oracle. Its historical wheel remains `0c456666...`; full source deltas
are retained. Q4, BL5/L1 and native generalized local operators have unchanged
normalized source. Scoped review confirms the new footprint/metadata additions
do not activate in these empty-footprint reference-linear routes. This is
impact reasoning, not a claim of byte-identical historical/current artifacts.
Common shell and every-eighth beam-node reference coordinates match exactly.
Raw unweighted nodal differences separate translations, physical director x/y
and released normal rotation; they are not continuum error norms.

All nine cases pass the existing equilibrium/work/balance ≤1e−8 and scaled
weak-gap ≤1e−9 checks. The largest value is **9.51604e−9** in finest Mz
equilibrium, close to its unchanged cap; connection-work error is 4.03212e−9.
No tolerance was changed. All sparse operators, trace tables, full state,
retained variables, multipliers and actions precede physical predicates.
Pointwise g5 samples remain visible: finest translation maxima are
6.259e−9/1.857e−9/5.953e−9 m, director maxima
2.447e−8/1.119e−7/1.349e−8 for Fy/Mx/Mz. They are sampled diagnostics,
not exact point ties, supremum bounds, mechanisms or pass predicates.

The actual endpoint evidence supplements the previously completed auxiliary
trace and local-kernel premises; it does not replace them with an SPD
interpretation of the native mixed matrix. Small endpoint work differences
and downward gap trends do not independently exclude locking. Mz's last
1.35% change still prevents a converged 1% engineering-accuracy conclusion.

## Combined root-transfer interpretation

[Saved-evidence contraction](../r8-bl5-matched-comparison-20261001/completion-root-combined.json)
joins the already executed PL+hourglass derivative to the saved finest root
partition comparison. It verifies 55 endport inputs, four common operator/state
inputs and all seven repair inputs. Both use origin (0,0,0.0675) m and the
1 m force-equivalent wrench metric.

The beam-root Fy discrepancy is 0.198297 N; its derivative per unit common
completion coefficient at alpha=1 is 0.189386 N. The complete root-wrench
derivative/discrepancy norm ratio is 0.945354, signed projection 0.944499 and
direction cosine 0.999096, despite only −0.038355% local applied-work sensitivity.
Thus small tip-work sensitivity does **not** dismiss completion effects on root
transfer. These numbers are alignment measures, not a causal fraction,
finite-removal prediction or authorization to tune coefficients. PL and
hourglass are combined; a separate pure-drilling attribution is not proven.
The new 8:1 finest Mz root Fy changes only −0.002517 N from the saved 1:1 value,
whereas its Fz changes −0.028353 N; all components remain reported.

Stop this bounded three-level batch. Retain the candidate and the precise
completion-sensitive root-transfer/convergence boundary. The next connection
decision must address a physically matched torque/shear reference and the
remaining actual response envelope; another axial grid, coefficient sweep or
repeated auxiliary metric does not answer it. Formal F03 remains unconsumed.
Existing E02 rigid-tip evidence locks a different connection and cannot fill
this BL5 reference obligation.

## Evidence and review

[Raw inventory and checksum](raw-v1.json), `raw-v1.zip`, complete source-impact
diffs, commands, logs, source/installed identities and recomputable collection
are retained together. Collector syntax and an overbroad cross-inventory binding
assertion were harness defects, corrected without rerunning or altering any
numerical result. They are recorded separately from numerical outcomes.
[Independent read review](review.md) covers source, work maps, actual outcomes
and the limited interpretation. No different-family or human mechanics
acceptance is claimed. No broad test campaign was repeated for these scripts.

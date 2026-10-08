# F03 finite-pad classical feasibility: two-mesh diagnostic

22 September 2026. **Bounded algebraic/resource screen passed; physical
convergence and G0B remain open.** This is an illustrative classical
finite-area connection, neither the original four-point reference nor the
native B3-GE/E4-PL coupling. It supplies no production qualification.

## Frozen evidence and decision

The four independently supervised, serial v2 runs used clean source
`05a18cbd97639b0d3d4feb1a840c7569530ece69`, accepted main
`be41a77a62e1cd7e1767bda6e955253af0819f91`, Python 3.14.2,
NumPy 2.4.6, SciPy 1.17.1, single-thread numerical pools, and four separate
`.10 × .10 m` square material pads. The `.05 m` halfwidth was fixed from an
illustrative nominal square beam-section size before these responses were
examined. It is a different physical idealization, not a fitted correction
to the four-point comparator.

The raw files, source hashes, identity, per-case receipts and one-use
adjudication live at
`.qualification/b3-ge-e4-pl/f03-area-feasibility-v2/` in the isolated
integration worktree. The registration SHA-256 is
`9bdf3d4f7c63f86e27d8fea63fc11f81631fe8358c3df9c11dc90b0a29d2560f`;
the adjudication file SHA-256 is
`89e8faa74a218334481e871df1480a6bd287f0be6a9e78ae5c459066e1524411`.
Every case completed within 900 s and a 100-ms-sampled child RSS cap of
8 GiB. The adjudicator independently checked raw child identity and hashes,
then recomputed energy, support balance, and the root elastic/port/load
partition. All four met the registered free-residual and balance limits of
`1e-8`, weak-gap limit of `1e-9`, and energy limit of `1e-8`.

| Topology, mesh `(Ns,Ny,Nb,Nm)` | Time s | Sampled RSS MiB | Max scaled balance | Scaled weak gap | Tip `uy` µm | Root `Fy` kN | Root `Mz` kN·m | First-quarter port `Fy` kN | First-quarter port `Mz` kN·m | Motion-scaled L² gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Q4 `(4,8,8,4)` | 2.12 | 64.5 | 1.49e-14 | 4.58e-16 | 42.038 | -445.424 | -8.430 | -203.976 | 16.503 | .328 |
| CST-CB `(4,8,8,4)` | 3.33 | 66.7 | 1.51e-14 | 4.04e-16 | 40.914 | -438.743 | -8.272 | -197.086 | 16.686 | .331 |
| Q4 `(8,16,16,8)` | 5.54 | 70.6 | 4.32e-14 | 5.29e-16 | 39.517 | -601.243 | -8.879 | -271.542 | 34.726 | .132 |
| CST-CB `(8,16,16,8)` | 10.26 | 76.9 | 5.82e-14 | 8.98e-16 | 39.089 | -601.276 | -8.856 | -271.125 | 34.874 | .133 |

The displayed memory is sampled child RSS, not an instantaneous or full
process-tree peak. Timing is one diagnostic run per case, not a repeatable
performance comparison. The table rounds values for reading; raw signed
displacements, all three support wrenches, three shell stations, four
physical-quarter port wrenches, energy, matrices, and gap measures remain in
the case files.

## Physical interpretation and next G0B work

At the terminal mesh, the Q4/CST-CB difference is approximately 1.083%
in tip `uy`, .265% in beam-root `Mz`, .154% in first-quarter `Fy`, and
.423% in first-quarter `Mz`, using the larger absolute value as denominator.
Those are *between discretizations*, not errors against an independent
physical reference. From coarse to terminal, Q4 root `Fy` changes 25.9%
and first-quarter port `Mz` changes 52.5%; CST-CB changes are 27.0% and
52.2%. Refining shell, beam and multiplier all at once does not identify
which operator causes these shifts or establish saturation. The motion-
scaled integrated L² gap remains .13 at the terminal meshes despite tiny
assembled weak gaps. No certified pointwise/endpoint gap enclosure exists
for this area-averaged trace.

The next registered experiment must keep `.05 m` and the load/model fixed,
refine shell x, shell y, beam and mortar **one axis at a time**, and preserve
signed tip, station, full support, elastic/port/load root partition, all
quarter resultants, port work and integrated gap. Add an independently
implemented clipped-host integration check for nonaffine checkerboard
fields, an operator-swap diagnosis of the first quarter, and a certified
pointwise/endpoint gap bound before a physical-reference gate. Register
frozen targets, criteria, source, resources and independent review first.
Do not infer a 1% reference pass or advance to G1 from this screen.

The first `f03-area-feasibility-v1` registration at `0c74d6c0` also
completed four supervised cases, but its adjudicator raised a path-shadowing
`TypeError` before writing a decision. It is preserved with
`adjudication_failure.json` and **has no acceptance status**. The v2 result
used fresh executions and a corrected source; it does not relabel v1.

An independent read-only mechanics/evidence review confirmed the v2 source
and registration hashes, both raw phases, observed single-thread pools,
four payload hashes, and the final adjudication hash. It found no evidence
defect. It separately compared signed physical partitions and agreed that
the large joint-mesh movement bars a convergence or trace-improvement
claim. No case was rerun or edited in that review.

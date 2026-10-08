# Complete growing affine BL5 space — 3 October 2026

**Do not advance span4 to qualification: it worsens physical torque transfer on
the same mechanical mesh.** Retain the continuous native trace as a development
candidate; neither fixed span8 nor growing span4 is a selected production rule.
No automatic further mesh refinement or channel tuning follows this result.

## Bounded comparison

Same32x8 Q4 shell/64-halfcell beam grid,1m by0.2m panel,h0.035m, same sections,
offsets, frames, grounds and loads. This comparison changes only affine support
resolution: span4/sixteen physical intervals/allfive channels/160rows, rather
than the preserved span8/eight intervals/80rows. Native retains768 internal
coordinates. Independent external ASDShellQ4/Timoshenko rows, transformations
and two free quarter-station recovery blocks are derived for the same support
space; they are not imported from native assembly. Both use complete physical
work controls and exact integrated transfer moments, including lever arms.

| Same fine-grid Mx10Nm observable | Eight supports | Sixteen supports |
|---|---:|---:|
| Signed applied-work difference | -0.010969% | -1.171859% |
| Shell common-field L2 difference,1m rotation scale | 0.072678% | 1.316876% |
| Beam common-field L2 difference | 0.045594% | 1.307621% |
| Interior window Mz difference | 1.200263 Nm | 13.294821 Nm |
| Beam-ground Fy difference | 2.226006 N | 18.746252 N |
| Broken/nodal trace-work witness / applied work | -0.018560% | -0.921272% |

The growing candidate also completed Fy100N and Mz10Nm. Work differences are
-0.598020% and -0.475688%; shell field differences1.117835% and0.944502%.
Fy interiorFx differs -34.296604N and beamgroundFx70.631834N; Mz interiorMz
differs -1.170582Nm and beamgroundFx7.277141N. These are physical partitions,
not failed equilibrium controls. Close fields or small weak gaps do not qualify
transfer. Coarse fixed-eight and fine fixed-eight comparisons remain separate
evidence; this run does not prove a mesh-uniform failure or continuous-law defect.

## Checks, identity and retained execution

58 combined focused checks passed3.40s; external worker50 passed1.66s;
root8 passed1.82s. Independent source scrutiny found no actionable defect in
generic row ordering, exact integration, dual recovery, physical geometry and
admission. Previous fixed-eight behavior remains tested and unchanged.

Three serial external cases, one installed native owner/threeRHS/onefactor,
and one saved-state audit completed exit0. Complete native/external physical
controls maximum2.7623e-11, within unchanged budgets.417source/wheel/site modules
match existing wheel SHA ef96a35e7d24912500d42422be59171b0f4e9f5830157e0088d226960ce5a06b.
Product modules, material laws, defaults, solver tolerances and versions unchanged.
Editable ANYmaterial dependency and platform/graph limitations remain recorded.

| Run | Elapsed s | Sampled peak process-tree bytes |
|---|---:|---:|
| External Fy | 0.700624 | 36,454,400 |
| External Mx | 0.553241 | 53,248,000 |
| External Mz | 0.555792 | 54,345,728 |
| Native three cases | 7.497300 | 215,142,400 |
| Saved-state audit | 0.452977 | 61,456,384 |

Serial children, CPU affinity fixed before code; environment1thread/JIT off,
native effective BLAS/Numba1 verified. Sampled numeric/unresolved threads maximum1;
external effective DLL thread qualification remains unresolved.600s/8thread ceiling,
external8GiB/native+audit1GiB; sampled costs are not performance claims.

Source parentef07ddad. [Raw manifest](raw-v1.json) binds84 explicitly whitelisted
files and raw-v1.zip1490175bytes/SHA
86263401acf96249b0877480ce79f36a3171c031367cfd819563b39e16df7489.
Primary matrices/states, physical inventories, commands, all outcomes and logs
precede interpretation. Initial compact-summary extraction hit a wrong field key;
the read was corrected without rerunning or changing primary results. Previous
archives and protected history remain untouched. [Review](review.md).

## Development disposition

Withhold span4's promotion to the registered envelope. The combined experiment
separates mechanical refinement from support enrichment: the former improved
transfer at fixed space, while the latter reintroduced substantial discrepancies.
This implicates discrete trace/space compatibility as a remaining question; it
does not establish causation, instability, locking or a permissible director
substitution. A different pairing needs a physical/approximation argument before
new runs. The next mechanics decision is the consistency/stability of affine
director-moment equations using actual retained cell directors, adjudicated against
continuum virtual work, admissible patches and a justified physical dual norm.
The complete native indefinite tangent is not an energy norm. Keep M2 open and
advance independent ready M4 load/attachment work.
Formal F03 remains UNCONSUMED; no changed criterion, main merge or publication.

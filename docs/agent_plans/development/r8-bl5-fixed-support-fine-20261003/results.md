# Fixed-support BL5 mechanical discriminator — 3 October 2026

**Retain the native physical trace as an experimental candidate; M2 remains open.**
Mechanical refinement at unchanged eight physical supports reduces the physical
transfer discrepancy substantially. This supports finite approximation error;
it neither proves causation nor establishes convergence, locking freedom or a
production multiplier policy. No product equations or defaults changed.

## Matched question and outcome

The prior 16x4 Q4/32-halfcell model and this 32x8/64-halfcell model use the same
1m by 0.2m panel, 0.035m thickness, sections, eccentric offsets, frames, grounds,
Mx10Nm load and eight intervals with endpoints i/8. Both retain all five BL5
channels with affine [1,xi] densities. Native span8 freezes those supports;
automatic span4 would instead produce sixteen and confound this discriminator.
All 768 native internal coordinates are retained on the fine grid. External
ASDShellQ4/ElasticTimoshenkoBeam rows and density recovery are independently
constructed; they share a continuous law, not identical discrete directors.

| Observable | Coarse | Fine, same supports |
|---|---:|---:|
| Signed applied-work difference | -1.023869% | -0.010969% |
| Shell common-field L2 difference, 1m rotation scale | 1.274585% | 0.072678% |
| Beam common-field L2 difference | 1.271050% | 0.045594% |
| Interior window Mz difference | 11.089410 Nm | 1.200263 Nm |
| Beam-ground Fy difference | 20.426552 N | 2.226006 N |
| Broken/nodal trace-work witness / applied work | -0.840214% | -0.018560% |

The remaining interior moment discrepancy is 12% of the applied 10Nm moment.
Close fields/work do not close physical-transfer fidelity. The audit verifies
actual native weak rows separately from common nodal-P1 rows, using the actual
retained coordinates and signed physical dual map. It is a work witness, not
causal allocation or permission to replace directors. Its absolute-work output
is a sum over support/channel contributions, not an integral of absolute work.
Two mechanical grids with fixed interface space are not the required growing-space
stability/convergence envelope or a converged 1% external accuracy pass.

## Execution and identity

36 combined focused checks passed in 2.23s; worker checks31 passed in0.65s.
No replacement coarse campaign or broad installed campaign was run. One external
Mx run, one installed native Mx solve/one factorization, and one saved-state audit
completed with exit0. Physical controls: native maximum4.1124e-12, external
3.09e-12. Source/wheel/site identities match all417 modules; existing wheel SHA
ef96a35e7d24912500d42422be59171b0f4e9f5830157e0088d226960ce5a06b.
ANYmaterial remains a recorded editable dependency, not a final isolated graph.

| Run | Elapsed s | Sampled peak process-tree bytes |
|---|---:|---:|
| External Mx | 0.686587 | 61,571,072 |
| Native Mx | 6.332575 | 213,487,616 |
| Saved-state audit | 0.447450 | 60,850,176 |

These are development execution costs, not paired performance claims. CPU affinity
was fixed before child code; sampled numerical/unresolved threads maximum1.
Native effective BLAS/Numba1 and JIT off are verified. External effective DLL
thread qualification remains open; sampled threads do not establish it. Limits
600s/8 numerical threads; external8GiB, native/audit1GiB, serial children.

Source parent8dd348bb; exact staged source, commands, DLL/supervisor identities,
operator matrices, states, physical inventories, comparisons, logs and input
bindings are in [raw manifest](raw-v1.json) and raw-v1.zip:51 explicitly selected
files,685299bytes,SHA d4009e814c5b8e30547d698f609f330a17c5529bd47a667550288cb1cc5fcab2.
Prior coarse evidence remains immutable in ../r8-bl5-affine-flexible-20261003.
No protected history was swept. [Independent review](review.md).

## Decision and next action

Retain the physical trace; do not select the production space. Assess ONE complete
five-channel growing-space rule, span4/sixteen supports, on the existing32x8/
64-halfcell grid with matched independent Fy/Mx/Mz actions. Hold geometry,
sections, supports and load measures fixed; preserve this span8 baseline.
Compare exact transfer windows and ground partitions, directors, work and fields
together. Better physical transfer without emerging action modes supports taking
the rule to the required registered envelope; worsening transfer or anomalous
actions calls for a targeted force-stability/operator decision. No automatic
finer-grid campaign, norm replacement or channel tuning follows either outcome.

Formal F03 UNCONSUMED. M2, full gates and mandatory CalculiX comparisons remain
open. No main merge, publication, release or different-family acceptance.

Documentation preparation initially hit a cp1252 UnicodeEncodeError when appending
a Unicode arrow to the matrix. No numerical run failed or was repeated; UTF-8
append repaired the note operation. Existing matrix bytes were preserved.

# Independent external P0 family pre-run review

Read-only source review, 2026-10-01. Reviewed `scripts/b3_e4_bl5_external_p0_refinement_dev.py`, current SHA256 `0e5435e0d38952642662eb1aad7dd374c341c866c9d099c87d2e66ce135a21c0`, and necessary frozen P0/strong recorder, geometry, objective-gap, integration and five-row recovery helpers. No imports, solves, numerical jobs or source/Git changes. **No consequential source defect found before execution.** Numerical completion and convergence remain unmeasured.

## Geometry, namespaces and growing spaces

| nx/ny | Shell nodes/elements | Beam nodes/intervals | P0 supports/rows |
|---|---:|---:|---:|
| 16/4 | 85/64 | 33/32 | 8/40 |
| 32/8 | 297/256 | 65/64 | 16/80 |
| 64/16 | 1105/1024 | 129/128 | 32/160 |

Geometry keeps L=1 m, width=0.2 m, thickness=0.035 m, beam axis z=0.0675 m, bottom arm z=-0.05 m and global-y section frame fixed. The same E, nu, G, EA/GA/GJ/EI and shell recipe are used. Refinement preserves rectangular aspect ratio and grows both primal and multiplier spaces: one support covers four beam intervals/two shell edge intervals. All shell x=0 nodes are clamped; beam root first five coordinates are directly grounded, rz free. Loads remain Fy=100 N, Mx=10 Nm or Mz=10 Nm at the physical beam tip.

Node/element namespaces are disjoint at all levels: shell nodes reach 1105 and shell elements 1024; beam nodes/elements begin at 100001. Geometry checks node-set disjointness; the explicit derived element ranges also cannot overlap. This fixes the unsafe use of old low beam tags on a refined shell. Domain checks use declared sets, not `node>=1001` heuristics. A later native comparison must likewise map by **domain plus ID**, since native shell/beam IDs can overlap; it must not reuse the old fixed-level bare-tag offset assumption.

## Integrated rows and independent recovery

`aggregate_rows` uses exact P1/Q1 edge shape integrals from the frozen helper on the union of dyadic shell/beam knots. The last-endpoint special case and positive endpoint weights remain valid for 32/64/128 intervals. Support widths are 2/nx; each beam/shell integral sum equals that width. Translation rows are ub-us plus the fixed bottom/top arm terms; director rows are relative rx/ry. Normal spin is omitted explicitly. These are external continuous nodal-rotation P1 traces, not native retained-cell rotation rows.

The dependent pair for each row is unique and has positive endpoint integral coefficient. The recovery node is the second interior node of that support, free in all five selected coordinates and outside every other support's nonzero coefficient pattern. The code independently checks its actual C_b transpose block against

`w * [[1,0,0,0,0], [0,1,0,0,0], [0,0,1,0,0], [0,-rb,0,1,0], [rb,0,0,0,1]]`.

Here w=1/(2nx)>0, so all five pivots are nonzero; recovery scales by that integral without an artificial floor. It also verifies all coefficients of other supports at the recovery coordinate are zero. `_solve5` reconstructs density from L-G at those coordinates. Applying all rows afterwards, the code checks **every** free shell/beam coordinate, including released rz and coordinates not used for recovery. Thus local recovery agreement cannot replace global equilibrium.

Independent shape-integrated force/director/arm formulas check -C^T lambda as exerted loads. Ground is (G+C^T lambda-L) restricted to prescribed coordinates; first-support root interface loads are retained and root G is not mislabeled as ground. Common-origin support/global wrenches, full domain cuts, internal/applied/interface/ground work and compatible/noncompatible virtual dual work are all checked. Density measures reuse the helper that iterates actual supports, not the original fixed count of eight; its polynomial/smooth primitives remain valid for the refined support endpoints and all three load directions.

## First-level reuse and raw provenance

The 16-level Mz reuse route requires an exact completed P0 source/binary/helper identity and explicitly remaps shell/beam **node and element** tags, connectivity, element arguments, poses, covectors and equations. It never maps by coordinates. Remapped actual node/element/fix/load/model-command/equation inventories are compared with the newly transcribed recipe; former source geometry/rows/support intervals are independently compared too. Beam element arguments retain the unchanged transformation/section values; model commands need no physical-ID remap because the recorder keeps nodes/elements/fixes/loads/rows separately. Reuse is restricted to nx=16/Mz; a duplicate scientific solve of that unchanged case fails explicitly. At most eight new cases accompany one reused case.

Each newly executed case gets a fresh owner/process route. Full declared command recipes, explicit physical node order, supports, rows, all nodal poses and all element global covectors are retained. Raw output is saved before inventory/physical checks, and interface blocks precede derived comparisons. New poses and element covectors are checked finite on capture. Set equality verifies complete pose/covector coverage; actual recorded inventories must equal planned values. The reused Mz state is reprocessed through current recovery and unchanged predicates. Original analysis exceptions remain primary; cleanup/retention failures are recorded and cannot produce completed status.

## Floors, scope and disposition

The existing 14 physical checks keep 1e-8 force/moment/work budgets and 1e-9 average gap budget. Force/moment scaling uses the declared case load and Lref=1 m; integrated gaps are divided by support width. Work uses the unchanged 1e-12 J floor, and the derivative probe uses a width-scaled 1e-12 integrated-gap denominator floor plus the separate 1e-6 limit. No threshold is derived from candidate outcomes. Six rigid modes, reference/common finite pose, released spin, exact shape sums and the declared mixed virgin derivative are still checked on every level; finite objective quadrature is only an auxiliary control.

This source is coherent for the prescribed external family. Root execution should preserve the nine-case inventory, including the exact reused Mz baseline, all failures and runtime provenance. Completion would provide development convergence data; the runner itself does not establish a common converged limit, 1% accuracy, selected multiplier space, native retained-variable equivalence, mandatory CalculiX comparison or F03 acceptance. Target-process resource observations remain bounded: environment requests do not verify effective OpenSees API settings, and sampled affinity/start-module records do not establish lifetime numerical worker behavior. No execution authority is consumed by this review.

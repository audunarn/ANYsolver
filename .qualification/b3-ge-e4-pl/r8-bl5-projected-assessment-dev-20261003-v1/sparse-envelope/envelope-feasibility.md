# Projected whole-member envelope feasibility inventory

Read-only source inspection and exact integer/rational accounting. No numerical case, product import, Git operation, worker, source edit or completed-fixture rerun was performed. This report is prospective feasibility evidence, not acceptance or execution authority.

## Rule and exact accounting

For shell trace Ns in {16,32,64}, Ny=Ns/4 and whole-member ratio b in {1/8,1/4,1/2,1,2,4,8}: Nhalf=2*Ns*b, members=Nhalf/2, H=4*max(1,Nhalf/Ns), supports S=Nhalf/H, and complete five-channel projected P1 rows C=10*S. Every listed Nhalf and H is integral; H is divisible by4 and divides Nhalf.

Shell nodes Q=(Ns+1)*(Ny+1); beam nodes Nhalf+1; nodal coordinates D=6*(Q+Nhalf+1); cell rotations R=3*Nhalf; resultants P=9*Nhalf; full mixed coordinates F=D+12*Nhalf. Fixed coordinates B=6*(Ny+1)+5. Free physical order X=D+R-B; kernel order X-C; supported full KKT order F-B+C. All resultants stay free and all nodal/cell rotations stay in X. Fixed B is35/59/107 for Ns16/32/64. Numeric beam IDs may overlap shell IDs at larger levels, so typed domains remain mandatory.

Counts below are exact arithmetic, not observed runtime inventory. Caps mean the existing dense diagnostic limits X<=2400 and fullKKT<=3000; they are not permission to run.

### Ns=16, Ny=4: shell nodes=85, fixed=35

| b | Nhalf | H | S / C | nodal D | cell R / resultant P | full F | physical free X | kernel | supported KKT | existing dense caps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1/8 | 4 | 4 | 1 / 10 | 540 | 12 / 36 | 588 | 517 | 507 | 563 | within |
| 1/4 | 8 | 4 | 2 / 20 | 564 | 24 / 72 | 660 | 553 | 533 | 645 | within |
| 1/2 | 16 | 4 | 4 / 40 | 612 | 48 / 144 | 804 | 625 | 585 | 809 | within |
| 1 | 32 | 8 | 4 / 40 | 708 | 96 / 288 | 1092 | 769 | 729 | 1097 | within |
| 2 | 64 | 16 | 4 / 40 | 900 | 192 / 576 | 1668 | 1057 | 1017 | 1673 | within |
| 4 | 128 | 32 | 4 / 40 | 1284 | 384 / 1152 | 2820 | 1633 | 1593 | 2825 | within |
| 8 | 256 | 64 | 4 / 40 | 2052 | 768 / 2304 | 5124 | 2785 | 2745 | 5129 | exceeds |

### Ns=32, Ny=8: shell nodes=297, fixed=59

| b | Nhalf | H | S / C | nodal D | cell R / resultant P | full F | physical free X | kernel | supported KKT | existing dense caps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1/8 | 8 | 4 | 2 / 20 | 1836 | 24 / 72 | 1932 | 1801 | 1781 | 1893 | within |
| 1/4 | 16 | 4 | 4 / 40 | 1884 | 48 / 144 | 2076 | 1873 | 1833 | 2057 | within |
| 1/2 | 32 | 4 | 8 / 80 | 1980 | 96 / 288 | 2364 | 2017 | 1937 | 2385 | within |
| 1 | 64 | 8 | 8 / 80 | 2172 | 192 / 576 | 2940 | 2305 | 2225 | 2961 | within |
| 2 | 128 | 16 | 8 / 80 | 2556 | 384 / 1152 | 4092 | 2881 | 2801 | 4113 | exceeds |
| 4 | 256 | 32 | 8 / 80 | 3324 | 768 / 2304 | 6396 | 4033 | 3953 | 6417 | exceeds |
| 8 | 512 | 64 | 8 / 80 | 4860 | 1536 / 4608 | 11004 | 6337 | 6257 | 11025 | exceeds |

### Ns=64, Ny=16: shell nodes=1105, fixed=107

| b | Nhalf | H | S / C | nodal D | cell R / resultant P | full F | physical free X | kernel | supported KKT | existing dense caps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1/8 | 16 | 4 | 4 / 40 | 6732 | 48 / 144 | 6924 | 6673 | 6633 | 6857 | exceeds |
| 1/4 | 32 | 4 | 8 / 80 | 6828 | 96 / 288 | 7212 | 6817 | 6737 | 7185 | exceeds |
| 1/2 | 64 | 4 | 16 / 160 | 7020 | 192 / 576 | 7788 | 7105 | 6945 | 7841 | exceeds |
| 1 | 128 | 8 | 16 / 160 | 7404 | 384 / 1152 | 8940 | 7681 | 7521 | 8993 | exceeds |
| 2 | 256 | 16 | 16 / 160 | 8172 | 768 / 2304 | 11244 | 8833 | 8673 | 11297 | exceeds |
| 4 | 512 | 32 | 16 / 160 | 9708 | 1536 / 4608 | 15852 | 11137 | 10977 | 15905 | exceeds |
| 8 | 1024 | 64 | 16 / 160 | 12780 | 3072 / 9216 | 25068 | 15745 | 15585 | 25121 | exceeds |

## Quarter-station and policy representability

Quarter and three-quarter beam stations are integers H/4 and3H/4 within each support; they are interior, distinct across supports, and not the grounded beam root. The unchanged rational external action formula therefore has a representable two-station10x10 dependent block at all21 points. This proves coordinate representability only; it does not prove physical rank, kernel positivity or response accuracy.

Shell intervals per support are Ns/S=4*max(1,1/(2*b)):16 at b=1/8,8 at b=1/4, and4 for b>=1/2. A description saying four shell intervals for every case is wrong at the two coarser beam ratios. At Ns16,b1/8 there is one complete support; the product special unsupported-mode guard is for unsupported P0 with no beam grounds, not this projected pair plus five beam root grounds. Its actual rank/kernel still needs measurement.

## Non-product scalar reference allocation estimates

Actual helpers inspected: shell_scalar builds a sparse Q1 scalar form with Ns*(Ny+1) active coordinates (80/288/1088). lower_gram solves that sparse form against2*S columns (maximum8/16/32), retaining all cross-products. Maximum shell action/solution block at Ns64 is1088x32 float64,0.266MiB. It does not build a dense global mechanical inverse.

p0_shell_bracket currently rejects more than128 halfcells: len(knots)>129. Its modal coefficient array has shape(modes,Nhalf), float64; the current preparation ladder is4096/8192/16384. One array costs8*modes*Nhalf bytes. Cosine/difference creation can have about three such arrays live; weighted multiplication about two. Dense lower/tail/difference matrices each cost8*Nhalf^2 bytes, and generalized eigenvalue routines add copies/workspace. These are source-derived allocations, not measured peak RSS or a resource qualification.

If that guard were explicitly revised while retaining the present allocation strategy, the largest Nhalf at Ns16/32/64 is256/512/1024. At16384 modes a coefficient array is32/64/128MiB; three coefficient-sized temporaries are96/192/384MiB, and each halfcell Gram is0.5/2/8MiB. The largest Nx64,b8 point would use32/64/128MiB per coefficient array at4096/8192/16384 modes. Existing interpreter, LAPACK and sparse-factor memory is additional. No600s/1GiB success can be claimed from these estimates.

Checkerboard preparation uses4*Ns halfcells, independent of candidate ratio:64/128/256. Consequently every Ns64 checkerboard call also breaches the current128-halfcell reference guard, including candidate grids that are small. np.eye(Nhalf) for native scalar-action rank is at most8MiB at1024 halfcells; sparse shell preparations and candidate2S Grams are smaller. Unit covariance repeats the scalar/modal work rather than changing its mathematical dimensions.

Later full physical reference preparation is a separate resource concern: beam_bracket has3*Nhalf*(subdivision+1) active auxiliary coordinates and10*S RHS columns, with subdivision ladder1..32. At Ns64,b8/subdivision32, one dense active RHS/solution is101376x160 float64,123.75MiB; several such blocks coexist plus sparse LU. This is not part of initial scalar registration and is also unmeasured.

## Actual blockers in current code

1. ratio_norm and ratio_owner admit only whole_half/whole_double, fix NX=16,NY=4,SUPPORTS=4, use mutable select_case globals per fresh process, and hardcode40-row/fixed35/full804-or1668 assumptions. Owner load/state counts are partly derived already; installed417 source/wheel/site checks, raw-before-predicate lifecycle, physical recovery and one cached three-load facade are reusable.

2. ratio_norm quarter witness uses arange(SUPPORTS)*4 plus1/3. This represents shell quarters only when shell intervals per support are4. At b1/8 or1/4 with multiple supports it can probe outside a later support and falsely reject a valid rational action. Replace it prospectively with indices derived from Ns/S, keeping the all-coordinate exact boundary comparison. Current physical_ratio metadata is also fixed to member_shell1:1/halfcell_shell2:1/halfcells_per_support8 and must become actual case metadata.

3. p0_shell_bracket hard guard128 and its full-halfcell dense Gram/eigen/tail preparation prevent the largest candidate and all Ns64 checkerboard grids. Do not bypass this guard or weaken the reference_error1e-3, inverse/eigen/symmetry1e-10, condition1e4, beta margin1e-6 and ceiling(1+1e-6)^2 criteria. An independently bounded projected-reference preparation or an explicit larger reference contract needs source review and changed-dependent verification first.

4. Existing kernel caps accommodate only10/21 proposed points: Ns16 through b4 and Ns32 through b1. All Ns64 points and higher ratios exceed them. The largest full supported KKT is25121 and physical order15745. Raising integer guards does not justify dense kernel/saddle spectra. A separately bounded sparse certificate or explicitly authorized resource/method change is needed for the rest; no claim of fullK SPD or coercivity may replace the supported physical kernel test.

5. ratio_kernel and ratio_external have their own two-case/85-shell-node/35-fixed/40-row/source-schema guards; the external geometry starts refinement.geometry(16) and independent historical row admissions exclude other reciprocal grids. Use a new explicit campaign admission, not widened historical mains. inventory.layout stamps halfcell_count=2*nx and needs the already-used actual-Nhalf correction. Geometry, loadtip101+Nhalf, roots and retained layouts must remain bound to actual source/installed ownership.

6. Scientific outcomes remain unmeasured for the envelope: full scalar positivity/conditioning/reference tails, actual all-column work, kernel rank/inertia, installed corrected solves, matched Fy/Mx/Mz physical transfer and refinement behavior. Current two-fixture passes do not establish these outcomes or a uniform floor. No completed evidence or consumed run authority may be regenerated or silently transferred.

## Recommended coherent prospective campaign

Use one existing living task record and one versioned envelope manifest for all21 cases: exact rational b, Ns/Ny/Nhalf/H/S, actual sections/arms/frames/grounds, fixed scientific criteria, installed0.4.7/417 module graph, helper SHA graph, resource ceilings, principal uncertainty and stopping decisions. Give each case a directory and status in that manifest; preserve the completed fixtures as named historical evidence with impact analysis rather than rerunning them. This is one bounded development campaign, not21 new one-use qualification packages or a new framework.

First resolve/reference-review only the dependencies that genuinely prevent scalar registration; freeze independent registrations before native beta. Reuse the current geometry/model/inventory/lifecycle functions under explicit case arguments instead of mutable global fixture state. For each newly eligible case, retain actual K/C and three-RHS raw states, then check independent all-column auxiliary work and the supported kernel using a method whose resource contract covers that case. Matched physical transfer remains a separate question from norm/kernel positivity. A failed or unresolved case preserves its evidence and determines the next discriminating action; do not fit a declining floor or automatically enlarge budgets.

Changed-dependent verification should cover: exact whole-member/H/S/quarter arithmetic at the21 declarative tuples; independent rational action/row identity at both coarser-beam ratios and the maximum support count; actual layout/root/retained counts for one changed representative per dependency; modal/projected tail and checkerboard bounds including the newly admitted maximum; unchanged all-column cross-products, basis/unit covariance and duplicate-rank controls; independent kernel certificate validation against a still-admitted dense oracle; and source/wheel/site plus runtime-thread/JIT and raw/error retention gates. Repeat a completed numerical fixture only when its inputs changed or evidence cannot resolve a specific regression. Different-family review remains appropriate for consequential norm/kernel changes.

## Inspected source identities

All files are in C:\Github\ANYsolver\.perf2-worktrees\stiffened-main-reconcile-20261001\scripts. Hashes bind this feasibility inspection; they are not a qualification disposition.

- r8_bl5_projected_ratio_norm_dev.py: `2424d4ad6f5d6c0287dbbe7321b70419ade9ac2ee0908028f3c85dc86a880a48`
- r8_bl5_projected_ratio_owner_dev.py: `e3fa392f2b04a0bbb6ac93e26195631bc180a13134c657bc980166d06623293c`
- r8_bl5_projected_ratio_kernel_dev.py: `9f1191e134b36842d243370e3dff3fb5c193a0142edb46f094b2fc0deac34e2f`
- r8_bl5_projected_ratio_external_dev.py: `7d9469cc0c3fbb1f32e8f34d8e62580e2d9480feac3f9f498e203f1ec8da6492`
- b3_e4_bl5_modal_reference_dev.py: `e1553e83596d5d371a7b2e196c000a1d9b551e361abf0942e352d54018b5712b`
- b3_e4_bl5_riesz_controls_dev.py: `da2ed22be805ce6901cfdfe034fe52a80089617e83849f71375948c64f724a4f`
- b3_e4_bl5_reference_accuracy_dev.py: `bc4d66871d152d3eb41f2ae9818e4ca416a11881e215d925fc6c5231ecebbf27`
- r8_bl5_projected_auxiliary_norm_dev.py: `906ebf3d821a85b6d8851f2dc86fc6e0cb2e80d19eb4f70976bad0b22f5e2bbf`
- b3_e4_bl5_matched_p0_native_refinement_dev.py: `7f220b1a94a49c8ec7e20b66c862b9506c057da7291c92ea691d109c3edcbfe0`

Limitation: estimates concern current source allocation shapes only. No timings, scientific spectra, tolerance passes, process memory peaks, savings, family acceptance or formal F03 execution were measured or claimed.

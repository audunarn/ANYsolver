# Matched growing-space comparison — 1 October 2026

Development decision: retain the declared BL5 position/director law and complete
P0 pairing for continued assessment. Differences between the two independent
discretizations shrink systematically. This does not select a production space,
establish converged 1% engineering accuracy, accept F03/M2 or replace CalculiX.
Independent [complete review and fixed-distance supplement](refinement-v1-raw/combined-complete-review.md)
found no consequential collection, work-map or derived-data defect.

The same 1 m×0.2 m panel, 0.035 m shell thickness, material/section properties,
frames, offsets, five-channel work law and direct root grounds use:

| Level | Q4 shells | Native B3 members / external two-node intervals | P0 rows |
|---|---:|---:|---:|
| 16×4 | 64 | 16 / 32 | 40 |
| 32×8 | 256 | 32 / 64 | 80 |
| 64×16 | 1,024 | 64 / 128 | 160 |

Each support spans two shell segments/four beam half-cells or external intervals.
Explicit domain-qualified IDs prevent accidental merging at the finer levels.
External 16/Mz is reused after exact node/element-ID-remapped inventory and
source checks; eight new external cases execute. Three installed native owners
each solve Fy=100 N, Mx=10 Nm and Mz=10 Nm with one eligible factorization.
All eight old 16/Mz state/action array roles are byte-identical. Full primary
states, retained coordinates, sparse operators, covectors, actions, trace tables
and complete measures precede physical predicates. No element equations,
material laws, tolerances, solver policy, product API or default changes.

| Load | Native/external work difference, coarse → middle → fine | Finest beam / shell common nodal L2 difference |
|---|---|---:|
| Fy | −0.599803% → −0.183777% → −0.060711% | 0.052102% / 0.484905% |
| Mx | +0.014239% → +0.003870% → +0.001208% | 0.001384% / 0.009788% |
| Mz | −0.271358% → −0.084384% → −0.028128% | 0.041021% / 0.321196% |

These are common nodal Q1/P1 fields, all six components, the existing 1 m
rotation scale and 1e-24 squared denominator floor. Retained rotations remain
separate. Applied work is twice linear elastic strain energy. Every component's
integral and raw reference denominator is preserved.

Successive final native/external work changes are Fy +0.13738%/+0.01407%,
Mx +0.07777%/+0.08044%, Mz −1.31478%/−1.37031%. Final Mz shell-field changes
are 1.16055%/1.39069%; beam changes 0.80035%/0.80484%. Some regional moments
are nonmonotone. Thus smaller cross-model differences are not independently
converged-reference acceptance.

Whole-interface degree-zero wrench differences persist: fine-grid maxima
2.787207 N in Fy, 0.036681 in Mx and 0.198297 N in Mz. They equal opposite
beam-ground partition differences through complete cut balance. These physical
observables remain visible; they are not discarded as boundary noise.
An additional read-only split at fixed physical positions
0,0.125,0.25,0.5,0.75,0.875,1 m reproduces all complete wrenches within
5.68434e-13. Fine Fy's Fy-component difference is −2.787207 N overall,
−2.930736 N in the first 0.125 m, +0.132448 N in the middle and +0.011081 N
at the tip. The corresponding Mz-case differences are −0.198297, −0.207416,
−0.004629 and +0.013747 N. This localizes the principal difference near the
clamp; it neither proves an end-port defect nor makes the difference ignorable.

Next bounded discriminator: review the saved beam internal root covectors and
attachment transpose-work contributions separately, checking their sum against
actual ground recovery and the declared end-port/support contract. Internal
dominance directs an element end-traction/representation check; attachment
dominance directs a boundary trace/support-work check. No extra solve, automatic
fourth mesh, law tuning, force-partition exclusion or tolerance change follows.

All nine native cases pass nine physical checks each (maximum 1.47935e-10);
all nine external cases pass fourteen each (maximum 1.22240e-10). Derivative
controls are separately normalized, at most 5.4546e-10 against 1e-6. Native
source/wheel/site match all 388 modules; 208 actual imports per owner are
canonical. Initial/final BLAS and actual Numba threads are one, JIT disabled.
The unchanged installed wheel is
`0c45666609355e654cb726a0e4e0780d386bccfaafef1209ffd994bdd3b9d09c`.

Native routes took 6.4907/12.8518/40.8646 s with sampled peaks
172,769,280/210,464,768/375,480,320 bytes. These are diagnostic route timings,
not repeated performance qualification or a speedup claim. External commands
took 0.2049–0.8766 s, peak 120,016,896 bytes; single-CPU affinity was set while
suspended before child code. Sampled OS threads never exceed eight, but start
classification and None-returning thread APIs do not establish effective
library settings or lifetime thread counts. General resource qualification
remains unavailable. All jobs are terminal; one-heavy-job limits were maintained.

[Manifest](refinement-v1-manifest.json) preserves 208 raw/source/review/provenance
files. Original strong comparison, stopped P0 execution and prior evidence are
unchanged. Formal F03 remains unconsumed; seven-ratio/mixed-system/physical
transfer, thickness/shear/drilling, topology, material, practical-scale,
CalculiX, installed-platform and complete release obligations remain open.

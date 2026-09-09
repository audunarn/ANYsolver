# Arc-owned current-rest spectrum — development closeout

Native interface source25dd6d41bcb2a1a7fdee0fb8604fed489f17716d;
accepted arithmetic/test successor0bfc94e58d80d52cd6ee05d7dcb8fda29a69bdd6,
tree563dd1cff15eeed4e98b70c90cf55f41abd64131. The sole src addition is private
`_ge_beam3_retained_arc_modal.py`; existing mechanics, solvers, coefficients,
defaults and qualification evidence are unchanged. No public route is added.

The new entry point authenticates the complete arc checkpoint with its actual
Context and captures physical current-rest factors at the accepted load and
committed history. It neither fabricates a force-program checkpoint nor inserts
the continuation row into physical stiffness. Material evolution/yield-boundary
ambiguity fails closed. Nodal dead-force residual is included exactly once;
nodal rotation traces retain exactly zero inertia.

Separate inventories:

- Interface/authority:14 tests passed on original and successor freezes.
- Arithmetic reference:10 tests passed on the successor.
- Original smoke:FAILED binary64 reference comparison; preserved without retry.
- Read-only arithmetic diagnosis:passed,2.517934seconds.
- Successor two-macro pre-limit smoke:passed,17.084905seconds.
- Successor cycle A:steps1/12,21.206639seconds.
- Successor cycle B:steps1/12,21.502740seconds.

Each accepted two-macro snapshot has21 physical coordinates and9 massless
algebraic coordinates after constraints. The algebraic stiffness block and
physical reduced mass are positive. Six lowest full signed modes agree with
direct80/100-digit original-factor Schur/Jacobi roots and with the merged
planar/lateral spectra. Partitioning requires structural zeros in ORIGINAL
material, geometric and kinetic factors; no small-entry threshold is used.
All21 direct high-precision roots are retained, not just selected positive roots.

Numerical stability results for this TWO-MACRO discretization and the frozen
diagnostic section mass (not an engineering frequency reference):

| Accepted step | Lowest planar frequency squared | Lowest lateral frequency squared | Negative physical modes |
|---|---:|---:|---:|
| 1 | 2.60657672103388 | 0.5398331554202559 | 0 |
| 12 | -0.41330531164298573 | -0.07206849635034393 | 2 |

The post-limit equilibrium is unstable in both families. This is not by itself
an element implementation defect: instability is a physical branch property.
It does establish that the prior planar continuation cannot exclude lateral
instability. Spatial mesh refinement, bifurcation location and branch validation
are still needed. These numbers are current-frequency-squared values, NOT load
factors; no full spatial qualification or uniqueness is claimed.

Maximum paired/Decimal normalized error1.7239382265329685e-16;
maximum whole/partition error1.6398842623215665e-16; frozen gates1e-11.
The80/100-digit references round identically to binary64. The original dense
binary64 comparison errors1.024281509649317e-10 and1.865394859699676e-11 remain
explicit diagnostics. The initial smoke failure is preserved and explained in
GE_BEAM3_ARC_SPECTRUM_ARITHMETIC_INCIDENT.md; no tolerance or beam change was made.

Both successor science files and full aggregates are byte-identical. Aggregate:
51859bytes/SHA292D63571432355107711876C8594CFC2A7359A3467A6F5DB38D591F3A81E768.
Step1:25866bytes/SHAB55368D4B3822A64BFA3DC79028114C9666E26628C17EA2C66A7BC4589206891.
Step12:25873bytes/SHAA792CEBB82BFC31B69F749880EC1C62C5D8B3A961EB2ECF0FA5571321A44B102.

Combined preservation archive (failed authority, diagnosis, successor raw runs,
source and helpers):
C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-arc-spectrum-0bfc94e-20260908
67entries, verified against source and external copy.
Manifest7707bytes/SHA F493C551F9DDDC586B9A38E6497F890C99466C8A5F02CE9E100E9488BAA5B40B.
Audit5026bytes/SHA 4A491258B6AAC5AC173425E06507E1B9BC014ACC6F9BD465DE38FE415EBE6B1F.
Original TEMP files and workspace mirror remain intact. All10 contained workers
are terminal; nine succeeded and the preserved original smoke failed. Every
process tree is empty. All original resource limits were satisfied, max2workers
concurrently, no automatic retries, no canonical partial science.

Terminal:UNCLASSIFIED_GE_BEAM3_ARC_CURRENT_REST_SPECTRA_ONLY.
Independent review remains PENDING; full environment graph not attested.
Next: scalable independently checked spatial spectra of finer accepted arch
states, then actual branch and plastic-arc/state validation. Do not rerun the
completed arch continuation to recover already preserved states. The bounded
Decimal all-root audit is currently deliberately limited to the small rehearsal;
do not silently remove it or raise its bounds for larger cases. Full straight/
curved parity, production-scale orchestration, installed opt-in, independent
review and objective eccentric/curved beam-shell joints remain OPEN.

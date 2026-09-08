# Saved continuum lateral comparison: repeated private closeout

Frozen source `3ee0b8ce314df5bcdec25f3f48b46d39df29bba3`, tree
`4039316ba471288d78c5322d07012cf42f507f81`. Research-only successor to `6f2d3db`.
No native mechanics, historical evidence, aliases, defaults or runtime changed.

## What was computed

At nine previously accepted equilibria (4/8/12 macrocells, saved steps 6/7/9),
read the bound continuum BVP9 fields already evaluated at the exact native
crown displacement. Validate the distinct saved continuum/native loads, source
point/checkpoint identities and original reference-quality limits. Extract the
129 existing uniform-grid samples exactly from the union grid; no interpolation,
new base solve, discrete solve or continuation occurs.

The separate continuum lateral Jacobi equations are propagated with the
documented corrected coefficient-knot treatment, at both strides and on 129/257
nodes per half. The existing tolerances and callback/time limits are unchanged.
Maximum full-transfer grid-refinement error is 1.6171531250527533e-13, below
1e-11. Maximum cross-stride transfer difference, retained as a diagnostic, is
9.627106160791215e-10. Both resolutions/strides retain consistent nonzero
determinant signs. Hamiltonian and normalized symplectic checks pass.

This is an independently reconstructed continuum mechanics calculation by the
same author, not independent review or an interval certificate. The determinant
sign is compared with discrete negative-count parity; it does not determine the
full continuum inertia or establish root uniqueness.

## Preserved scientific discrepancy

At four macrocells, step 7, crown drop 0.039088200876182096:

- Native lateral negative count: 1.
- Continuum normalized determinant: +0.0020165843871898367.
- Native load: 0.03182243233273554.
- Continuum load at the same crown drop: 0.028556621801118186.

This parity discrepancy is preserved, not classified away by a successful
process return. The two other four-macro samples agree in parity. All six
eight-/twelve-macro samples agree in parity, but this sparse agreement does not
prove critical-point convergence or a finest-mesh engineering gate. The coarser
sample discrepancy remains a quantitative refinement question; it is not by
itself proof of an implementation defect or a complete continuum mode count.

The next useful mechanics work is an actual matched-displacement critical-point
search and comparison of its convergence, rather than more endpoint parity
sampling. Read-only inspection confirms the existing native retained translation
controller can own a fresh crown-displacement/dead-load programme from the
virgin state. This offers an alternative to transferring/resealing an arc state.
Before using it, freeze a bounded path, verify actual branch agreement and provide
a translation-owned physical factor capture that excludes the control border
from stiffness. No such new solve/capture ran in this comparison.

## Repeatability and custody

34 authority/interpretation tests passed; smoke and the complete rehearsal
passed. Two fresh full cycles produced byte-identical per-state records and
aggregates, also matching rehearsal/smoke. Rehearsal 6.739297 s; full cycles
6.741389 s and 6.643336 s. All 11 bounded child processes completed successfully
with empty process trees. Longest child 6.740907 s, peak Job memory 136,577,024
bytes, peak concurrency three. No retry, watchdog breach, or source edit during
execution. These are diagnostic runtimes, not production performance claims.

Verified mirror and exclusive external archive (106 entries):
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-continuum-lateral-3ee0b8c-20260908`.

- Manifest 12,018 bytes, SHA-256
  `126CA8EC7EC010E41BDA2500F26027CBA512EAB1F0D169848DFB43328D447A1D`.
- Audit 8,205 bytes, SHA-256
  `B49649DE6263AAA0933ED3CAA06E255A2F1FE6825DBCDC6A7436C1216D25D855`.
- Aggregate 160,796 bytes, SHA-256
  `36C1DF1C54988B89E5E464AEC58CEF6DAB17D8C870AE0F62E1CEB44CB61D3DA0`.

All files were copied and verified byte-for-byte; raw logs, source snapshots,
process receipts, full transfers, extraction indices and input hashes remain
external. Public production qualification is false. Actual spatial postbuckling,
plastic arc/state parity, broader solver/material/load/mass/recovery/restart
parity, independent review, complete environment graph, installed opt-in and
objective eccentric/curved beam-shell joints remain open. The full GE-B3 goal
remains active; B2/B3/S3/Q4 and defaults are unchanged.

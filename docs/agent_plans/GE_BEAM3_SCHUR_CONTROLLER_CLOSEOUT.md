# GE-B3 controller transaction parity — not an accepted optimization

Frozen implementation `2756a7b9b1e1ac90154e582646b40a93e982143b`, tree
`9d4aa5d5b52dd9c1721c50a687a7d7b2b998ad3c`, follows
`fc2590b91b3226fbf6fb467833a5ffef6fb0ddf1`.

The new separately identified private controller passes complete elastic and
plastic transaction comparisons against the preserved dense controller.
Both backends reproduce their own uninterrupted checkpoint exactly after
pause/resume. Cross-backend checkpoint substitution is rejected. Cancellation
before trial, after factorization and before commit, injected factor failure,
exhausted Newton iterations and changed program identity preserve the last
accepted state or fail before execution. No trial plastic history is published.

However, this is NOT an accepted optimization. Local resultant elimination
left very small spurious forces in exactly unloaded equilibrium rows. Their
componentwise backward error is one even when their absolute size is around
1e-19. Three refinement actions did not reliably remove that error. COLAMD
full sparse LU also failed the curved local witness. The V4 fallback uses the
existing full-system LAPACK partial-pivot method and still requires the SAME
componentwise bound. No coefficient, constitutive law, load operator, recovery,
convergence tolerance or acceptance condition was changed.

| New development path | Accepted targets | Newton factorizations | Full-system fallback steps |
| --- | ---: | ---: | ---: |
| Straight elastic | 5 | 14 | 13 |
| Curved elastic | 5 | 14 | 14 |
| Plastic load/unload/reversal | 7 | 24 | 24 |

Thus 51 of 52 path Newton factorizations fell back. Do not describe this as
a general half-sized solve or speedup, and do not promote it to a public
default. In the tested curved and plastic paths, the compared physical fields
match exactly; the straight elastic maximum normalized record difference is
3.2311742677852644e-27 and final physical recovery difference is
8.244806066080547e-27. These are development comparisons, not complete section,
beam, dynamics or beam-shell qualification.

## Separate inventories

- Initial unrefined rehearsal: one passed, ten errors; 7.355 pytest seconds.
- Refinement rehearsal: two passed, three failed, ten errors; 8.557 seconds.
- Sparse-fallback local checks: two passed, two failed; 2.850 seconds.
- Dense-fallback local checks: four passed; 2.504 seconds.
- V4 full rehearsal: fifteen passed; 30.696 seconds.
- Complete pause/resume rehearsal: fifteen passed; 36.913 seconds.
- Frozen cycle A: fifteen passed; 36.549 seconds, 38.0851065 supervised seconds.
- Frozen cycle B: fifteen passed; 36.445 seconds, 38.0864416 supervised seconds.

All thirty-nine JSON files are byte-identical between the two frozen cycles,
including checkpoints, progress, comparison records and intentional failure/
cancellation records. No historical nonlinear path or eigensolve was rerun;
these are the new small cases frozen in the development plan. Both processes
used one numerical thread and 24-GiB Windows Jobs with 600-second wall and
120-second inactivity limits. No process was automatically retried. No worker
remains.

All 205 preparation/cycle files, including failures, are hash-bound in
`docs/reference_cases/ge_beam3_schur_controller_archive.json` and preserved at
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-schur-controller-2756a7b-20260907`.
That directory also contains a byte-identical archive-manifest copy. Exact
source identities, case metrics and separate execution inventories are in
`docs/reference_cases/ge_beam3_schur_controller_status.json`. Original temporary
evidence is retained; only verified transfer duplicates are removed.

## Next work and full-goal boundary

Do not keep enlarging these cycles or use this fallback-heavy controller as a
performance solution. Review the linear-solver error measure and equation
scaling, then establish an equilibrium-preserving reduction or an appropriately
validated sparse full-system route using the failing initial linear systems
reconstructed from the frozen inputs first.
Any successor accuracy contract must be explicit and independently supported;
do not silently weaken a frozen check to make the current path pass.

Public standalone integration, broad slenderness and nonlinear section parity,
independent scientific review, critical buckling/postbuckling qualification and
the objective finite-rotation beam-shell connection remain incomplete. Q4/S3,
existing B2/B3, all defaults and historical qualification evidence are unchanged.
The full GE-B3 goal remains active.

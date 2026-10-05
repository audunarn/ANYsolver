# F03 signed native retained norm: finite-mesh decay

21 September 2026. **Ten/ten exploratory meshes, 20/20 space results
completed; no G0B/F03 acceptance.** The source was frozen at `7270fee`.
Raw evidence is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-signed-norm-v1/`:
`manifest.json` SHA-256
`01aa5a322919c525f7dffcb180cfe812c22c420162915eaac0ee86b38fc924c0`,
`results.jsonl` SHA-256
`dde03d93dcf4b6ebe5fae590b7b84b124080911e8f39d7ab2971638c60d6cef7`.
The manifest binds six source/helper hashes, the integration-worktree
ANYsolver import, Python/NumPy/SciPy/Numba, a dedicated Numba cache, one
BLAS thread, physical scales and the exact ten-case inventory. It does
not independently hash every transitive imported product module or an
installed wheel. No historical run was overwritten.

The pre-execution document incorrectly said “twelve” even though it
enumerated six joint-refinement and four fixed-beam reach cases, and the
committed `CASES` and untouched raw manifest both specify **ten**. The
document carries a post-execution editorial correction. No cases are
missing or added after execution.

The work-scaled exact `p/r` factorization retained `Cr`, used the
positive absolute-value native block for the *test norm*, and retained
the **signed** native block in the KKT and multiplier Schur. Both K4 and
the local dual/P0 span were measured. The largest primal vector had 906
entries, including 96 retained coordinates, and 24 multiplier rows: the
largest dense KKT was 930, below the 1,200-row bound. Native `Krr` was
exactly block-local in these fixtures; its negative-mode counts were
36, 72, 144 as the native half-cell count doubled 4, 8, 16. `Ke` remained
positive and all measured signed multiplier Schur matrices were
nonsingular, with no negative mode. Maximum symmetry skew was
`5.20e-17`.

| Panel | Native/shell mesh | K4 constraint β | K4 signed KKT σmin | Local dual β | Local dual signed KKT σmin |
|---|---|---:|---:|---:|---:|
| Q4 | 4/4 | 0.20866 | 0.041793 | 0.20260 | 0.039486 |
| Q4 | 8/8 | 0.097515 | 0.0094204 | 0.096724 | 0.0092695 |
| Q4 | 16/16 | 0.049424 | 0.0024368 | 0.049224 | 0.0024172 |
| S3-V2D | 4/4 | 0.20898 | 0.041916 | 0.20291 | 0.039602 |
| S3-V2D | 8/8 | 0.098102 | 0.0095330 | 0.097323 | 0.0093836 |
| S3-V2D | 16/16 | 0.049583 | 0.0024525 | 0.049419 | 0.0024363 |

At fixed `Nb=8`, shell-only reaches `Ns=1` and `Ns=64` give β about
`0.097–0.099` and signed σmin about `0.0092–0.0097` in both topologies.
The observed joint-refinement β roughly halves and the signed KKT floor
roughly quarters with each doubling. The decline is driven by beam-side
refinement in this inventory, not by shell-only reach. The positive
constraint floor alone would miss possible cancellation in a signed
Schur; both signed checks were therefore retained. No singularity was
observed at the ten finite meshes.

Independent mechanics review checked the scaled congruence, mass
whitening, signed block and source/results after a raw mixed-unit solve
was corrected before execution. It confirmed this finite-mesh decay and
the limitations of the norm. **This is not a physical or asymptotic
inf-sup failure proof.** The operator-adapted norm is not yet shown
uniformly equivalent to a mesh-local graph norm that controls cell-yaw
jumps and force-like variables; the L2 mass has not been justified as
the dual of the physically appropriate trace space. A broken/jump trace
norm and its dual, norm-equivalence and trace-continuity checks are the
next prerequisite before any stability assertion or F03 selection.

# F03 discrete trace-image dual: finite floors decline on joint refinement

21 September 2026. **Ten/ten exploratory cases completed; F03/G0B remain
open.** Frozen source and prior registration are at `9aaf7fd`; the
exclusive raw root is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-trace-dual-v1/`.
SHA-256: `manifest.json`
`ea783b9f4df3d89c94d01564c4799fb9e5414f4eb29b2c351381764acd0e59ec`;
`results.jsonl`
`c2a54018fe6a81e151066610dc0f1ba5a855dfc4c99a4e473c62c65487b784dc`.
The manifest's eight script hashes matched the frozen files. It records
the imported ANYsolver source path, dependencies, one BLAS thread,
physical scales and 1,200-row dense KKT cap; it does not hash the entire
transitive product tree. This is a bounded source diagnostic, not an
installed-artifact acceptance run.

The graph is the broken physical three-channel gap with L2, slope and
native yaw-jump terms. For each constraint space, the multiplier dual
Gram is `R=C_s G_s^+ C_s^T` on the *discrete trace image*, checked for
kernel annihilation and full row rank. The signed native retained block
is not replaced by a positive approximation. The full normalized KKT
includes its negative modes and the induced constraint coupling.

| Shell | Space | Positive constraint floor, joint 4/4 → 8/8 → 16/16 | Signed KKT floor, same meshes |
|---|---|---:|---:|
| Q4 | K4 | 1.0450 → .7945 → .6431 | .26536 → .11349 → .03467 |
| Q4 | Local dual | 1.3437 → .9829 → .7583 | .26080 → .11186 → .03453 |
| S3-V2D | K4 | 1.0414 → .7931 → .6403 | .26442 → .11352 → .03466 |
| S3-V2D | Local dual | 1.3404 → .9818 → .7557 | .26036 → .11197 → .03452 |

The fixed native-beam eight-cell reach is nearly flat under shell-only
refinement: from one to 64 shell cells, Q4 signed floors are .11145→.11420
for K4 and .11048→.11269 for local dual; S3 follows the same pattern.
Thus the observed decline on joint refinement is associated with beam
refinement in this finite registered family. A local dual has a larger
positive constraint floor but does not repair the signed saddle floor.

Every one of the 60 space/case/cutoff variants was admissible. Cutoffs
`1e-12`, `1e-10`, `1e-8` on *graph eigenvalues* selected exactly the same
rank and returned exactly identical saved positive and signed floors.
The largest relative Frobenius kernel-annihilation residual was
`7.48e-14`; the smallest was `2.13e-15`. Midpoint affine errors were at
most `7.93e-15`, and all native interior jumps were counted. These checks
validate this finite matrix construction, not a rowwise/uniform physical
trace norm. No negative signed-Schur modes appeared in these cases;
the full signed saddle remains the relevant reported stability floor.

This exact **discrete-image** dual is a model-wide pseudoinverse and
depends on the tested trace space. It neither supplies a mesh-local
production multiplier norm nor proves norm equivalence or a uniform
physical inf-sup constant. Three mesh levels cannot establish an
asymptotic rate. The previously observed large physical gaps of both
candidate row spaces remain unresolved. No F03 line law was selected,
and G1 production integration remains barred.

An independent read-only pre-execution review corrected cutoff reporting
before source freeze. Its post-run review checked hashes, ten distinct
rows, 60 variants, ranks, kernel residuals, floors, midpoint and jump
counts, and found no raw-evidence defect. The next work must establish an
independently converged physical response and a justified mesh-local
broken/jump trace norm, examine the weak signed mode shapes, and only
then register another physical F03 candidate.

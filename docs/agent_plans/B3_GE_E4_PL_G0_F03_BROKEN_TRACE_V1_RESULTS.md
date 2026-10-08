# F03 broken trace graph: rising finite-mesh continuity bound

21 September 2026. **Ten/ten exploratory graph cases completed; F03/G0B
remain open.** Frozen source commit `e6ec24f`; exclusive evidence root
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-broken-trace-v1/`.
SHA-256: `manifest.json`
`723e308cd8d55d6b1ef85706fca2a1728bbb94581ddec020e74edadabb93e332`,
`results.jsonl`
`943f5f704252dca0e2df69631d187bde0180a17bf46948e3951b8cb62d5bce2e`.
The manifest binds source/helper identities, this integration checkout's
import, dependency versions, cache, one BLAS thread, fixed scales and
the 1,200-primal-row dense limit. This is source-backed numerical evidence,
not installed-artifact qualification or a complete source-tree hash.

The three physical gap channels use metres after converting yaw by
`ell=.46 m`. A broken graph counts displacement, slope and native
cell-yaw jumps on the actual shell/beam overlay. Midpoint checks of the
piecewise affine trace were at most `7.93e-15`; the expected number of
native interior jumps was `Nb−1` in every case. These verify the finite
matrix construction at the chosen precision, not finite-rotation
six-channel mechanics.

The table gives `sqrt(λmax(G/u0²,H))`, a finite-mesh upper bound for this
broken trace graph against the previously defined operator-adapted
retained norm:

| Panel | `Nb/Ns=4/4` | `8/8` | `16/16` | fixed `8/1` | fixed `8/64` |
|---|---:|---:|---:|---:|---:|
| Q4 | 78.0591 | 80.0735 | 124.4464 | 80.0689 | 80.0739 |
| S3-V2D | 78.0588 | 80.0731 | 124.4464 | 80.0690 | 80.0734 |

The upper bound is almost insensitive to shell-only refinement at eight
native half-cells but grows by about 55% from joint level 8/8 to 16/16.
The signed-norm constraint and KKT floors also declined when the beam was
refined. Together these finite observations locate a beam-side scaling
concern under the stated graph and operator norms. Three levels cannot
establish its asymptotic rate or prove that no different physically
justified norm would give uniform stability.

The graph has many exact null directions unrelated to the interface.
Its reported rank uses a relative `1e-10` *eigenvalue* cutoff, and its
smallest resolved eigenvalue is not a quotient-space lower bound. The raw
jump-row Frobenius number has mixed coordinate units; it is not a
physical jump amplitude. A dual multiplier norm constructed from this
trace, actual mode vectors and localized jump/traction recovery, norm
equivalence and the six-channel eccentric checks remain necessary before
F03 can select an exact-multiplier line law. No penalty or manufactured
inertia was introduced.

Independent read-only pre-execution and post-run mechanics reviews checked
the overlay, graph scaling, source hashes, ten cases, affine/jump results
and interpretation. The post-run review found no raw-result defect and
agreed that the observed rise prevents a uniform-bound claim.

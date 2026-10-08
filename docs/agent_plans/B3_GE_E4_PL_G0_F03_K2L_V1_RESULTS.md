# F03-K2L v1 native-image rank diagnosis

21 September 2026. **Completed bounded algebraic diagnostic, not
F03/G0 acceptance.** Frozen source commit
`6acd349daa69054bdbfb4b1ea5a7304fb46523aa` on the isolated
`codex/b3-ge-e4-pl-integration` branch. Registration, raw JSONL, child
logs and supervisor attestation are under
`C:\Github\ANYsolver\.qualification\b3-ge-e4-pl\f03-k2l-v1*`.
This was a source-imported mechanics screen; installed-package
qualification remains outstanding.

## Evidence and measured inventory

The external supervisor reports exit zero, 28 JSONL records (start, 26
ordered meshes, terminal), 78 candidate rows and no resource violation.
Elapsed time was 113.97 s; sampled peak child RSS was 255,545,344 bytes.
Registration and raw SHA-256 values match the attestation. All 78 rows
were typed `RANK_DECOMPOSITION_CONSISTENT_NOT_F03_ACCEPTANCE`, with
full row rank. None was classified near the frozen cutoff. The largest
normalized numerical native-null, shell reconstruction and projector
orthogonality residuals were respectively `5.384e-16`, `1.689e-15`
and `1.334e-14`; the largest discarded native singular/cutoff ratio was
`6.071e-6`. These numbers support this finite-mesh algebraic
decomposition, not uniform stability or physical compatibility.

The table reports `d_shell=rank(A)−rank([A_b A_r])` for representative
cases. Both shell formulations yielded the same rank counts; their
physical responses differ in K2P.

| `N_b,N_s` | P1-beam | P1-shell-grid | P0-shell-grid |
|---|---:|---:|---:|
| 8,1 (coarse shell, 1:8 reach) | 3 | 0 | 0 |
| 8,4 | 3 | 0 | 0 |
| 8,8 | 3 | 3 | 0 |
| 8,16 | 3 | 27 | 24 |
| 8,32 | 3 | 75 | 72 |
| 8,64 (fine shell, 8:1 reach) | 3 | 171 | 168 |

P1-beam leaves three assembled shell compatibility combinations at all
26 meshes. On the coarse Q4 `N_b=8,N_s=1` case, K2P found nearly zero
shell work and motion under nonzero load, whereas P1-shell-grid had
finite shell response. K2L identifies a structural mechanism consistent
with the P1-beam overconstraint concern: its 27 independent rows cannot
all be satisfied by the native beam image, which has rank 24. This does
**not** by itself prove a physical locking mechanism. The independent
postexecution trace analysis goes further for this specific Q4 fixture:
the three projected shell restrictions annihilate the fitted attachment
trace at **every** station. With no direct shell load and SPD supported
shell stiffness, its exact linearized shell response is zero. S3-V2D
at the same ratio and both formulations at `N_s=2` retain nonzero
admissible fitted traces despite the same three restrictions. This is
a discrete Q4 cause, not a continuum conclusion.

Conversely, under shell-only refinement to `N_s=64` with `N_b=8`, the
P1-shell-grid interface has 195 independent rows and native beam image
rank 24, leaving 171 shell combinations. K2P's shell-grid physical
energy and displacement fall while its raw scaled KKT ratio deteriorates.
This combination raises a complementary overconstraint/conditioning
question. P0-shell-grid lowers the row count by three, but its physical
load response was not part of K2P. Neither basis is promoted.
The K2P Q4 `N_b=8,N_s=64` P1-shell-grid smooth response remains
forward-parity-open; the fine-ratio comparison does not waive it.

The transformed metre/millimetre invariance case, a justified dual
trace norm, exact retained saddle inf-sup, independent resolved physical
response, and six-channel eccentric torque/shear/director tests remain
unexecuted. F03/G0B remain open and G1 production integration remains
barred. The independent postexecution review is recorded separately.

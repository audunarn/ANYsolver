# F03-K1 v1: reduced-space rank inventory, no accepted line law

21 September 2026. The frozen diagnostic at clean commit
`dc041c9f53c5dd9742e98cc676185f50d90d0194` executed once. An
independent F03 mechanics auditor recomputed the hashes, exact inventory,
all 130 row and trace ranks and their statuses. **The rank inventory is
complete; F03 and G0 remain open.**

## Evidence identity and execution

| Record | SHA-256 |
|---|---|
| `C:\Github\ANYsolver\.qualification\b3-ge-e4-pl\f03-k1-rank-v1-registration.json` | `8a20b41cfd6229bbbead9a8b7fffadefdb7162c523861de715c5b59fce6afaae` |
| `C:\Github\ANYsolver\.qualification\b3-ge-e4-pl\f03-k1-rank-v1\raw.jsonl` | `016cfa641c08cef6bda3b7a650a0f2b32b562edbcf7a521f852cacaae79c0270` |
| `C:\Github\ANYsolver\.qualification\b3-ge-e4-pl\f03-k1-rank-v1.attestation.json` | `de2fc37564c99cacde85c6511f864e9a7c0afb726b4dbf32549b3b0664131f26` |

The supervised child exited zero, with 28 ordered records (start, 26
meshes, terminal), 130 ordered candidate matrices, no read or resource
error, 161.34 s elapsed and 289,964,032-byte maximum **sampled** RSS.
Registration, raw, stdout and stderr hashes matched the attestation; the
start and attestation source identities matched the clean commit, 21 bound
source hashes and the 363-path solver source-tree hash. This is a
source-backed G0 diagnostic, not installed-wheel qualification.

All 130 cases had finite positive multiplier mass, reference gaps zero,
mass symmetry error zero and quadrature differences no larger than
`2.07e-15`. The native assembly parity was zero in this registered fixture.
The independent audit recalculated every mass-whitened constraint rank and
weighted-trace rank from the raw singular lists at the frozen `1e-10`
relative threshold: **zero discrepancies**. The smallest full-row
singular ratio was `0.00162`. For `N_s=1`, the shell-grid candidates used
the actual clipped `[0,.5,1]` knot sequence.

## What rank says, and what it does not

Every candidate had full constraint-row rank on all 26 meshes. One case,
Q4 with `N_b=8,N_s=1` and P1-beam, had no unsupported weighted trace mode
(rank 27/27). The other **129** cases retained unsupported trace modes.
The corresponding S3 case had constraint rank 27 and trace rank 30.

| Space | Sum of unsupported trace modes, 26 meshes | Largest row incidence |
|---|---:|---:|
| P1 shell grid | 1,969 | 46 |
| P0 shell grid | 2,047 | 34 |
| P1 beam | 2,461 | 214 |
| P0 beam | 2,539 | 105 |
| P1 beam coarse | 2,809 | 352 |

The aggregate is a diagnostic across a *fixed* inventory; it is not a
mesh-independent error norm or stability score. The reciprocal extremes
reverse the apparent ranking. At Q4 `N_b=8,N_s=1`, P1-beam constrains all
27 trace modes while P1-shell-grid constrains 9; at `N_s=64`, P1-shell-grid
constrains 195 of 294 Q4 modes (195 of 564 S3 modes) while P1-beam
constrains 27. More constraint rows are not automatically mechanically
better: they may lock the interface or degrade KKT conditioning.

**Decision:** all five remain eligible for a *physical diagnostic* under
the preregistered rank criterion. Prioritize P1-shell-grid and P1-beam as
two complementary hypotheses across reciprocal ratios, retaining
P0-shell-grid as the close aggregate-coverage and lower-incidence
alternative. The independent auditor found no unique two-space winner
from rank data alone. Do not call this a multiplier selection.

The next reviewed, separately registered study must compare actual KKT
solutions and reaction/work/gap histories over common physical refinements,
alternating as well as smooth loads, and norm-scaled inf-sup/locking behavior.
It must account for D1's finite-difference plateau and KKT conditioning
without retroactively waiving K0's frozen failures. The full F03 law still
requires six-channel eccentric and curved coupling, torque and shell
director/shear/thinning checks, reciprocal 1:8 refinement, a derived dual
candidate, and independent references before G0B or G1 can pass.

# F03 coarse P1-beam physical screen: six exploratory cases

21 September 2026. **No F03/G0B acceptance or multiplier-space selection.**
The rank-only K1 programme included `p1-beam-coarse`, but K0/K2P/K3 did
not evaluate its physical load response. After confirming that distinction,
committed runner `5a9a5f2` executed one unregistered six-mesh, two-load
screen at
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-coarse-p1-v1/`.
The raw JSONL SHA-256 is
`9a1d556034c634b6a0b706826ad8bb78b2cf32ad7aed4575273cae3a3f9162dd`.
The manifest binds the runner and five helper source hashes and the fixed
eight-native-half-cell, Q4/S3 `N_s=1,8,64` inventory. It ran serially in
20.01 seconds. A prior unsaved console probe was exploratory only; this
versioned run supplies the complete record.

All six 15-row constrained matrices were full row rank, but the trace
rank exceeded their row rank by 12 modes. All 12
smooth/signed-sine loads returned the existing local numerical diagnostic
status. The maximum observed scaled free-equilibrium and normalized weak
residual were `1.59e-13` and `1.56e-14`. These metrics establish a solved
finite native retained KKT, not a stable physical connection.
Maximum normalized support force/moment imbalances were `5.77e-13` and
`3.32e-13`; maximum full/condensed solution parity was `5.98e-12`.
The minimum raw scaled KKT singular ratio was `1.31e-7`, not a qualified
native signed inf-sup bound.

| Formulation | `N_s` | Smooth active shell energy, J | Smooth nine-station maximum gap, m | Sine active shell energy, J |
|---|---:|---:|---:|---:|
| Q4 | 1 | 9.13437 | `3.19731e-5` | `5.88498e-5` |
| Q4 | 8 | 14.93260 | `3.63695e-5` | 1.15918 |
| Q4 | 64 | 15.22346 | `3.59990e-5` | 1.18915 |
| S3-V2D | 1 | 9.22293 | `3.17552e-5` | 0.0373893 |
| S3-V2D | 8 | 13.91550 | `3.47277e-5` | 1.08140 |
| S3-V2D | 64 | 14.09546 | `3.44377e-5` | 1.10052 |

With the fixed K2P displacement scale `U*=1e6/(210e9*.07)=6.80272e-5 m`,
Q4's refined smooth sampled gap is `0.529 U*`; the sine gap at `N_s=64`
is `7.39985e-6 m` or `0.109 U*`. Nine samples are only a lower bound on
the continuous gap, and two fine shell levels cannot prove an asymptotic
plateau. This space relieves some coarse Q4 smooth-load restriction but
leaves a large gap on the fine shell. Earlier K3 P0-beam had a different
row span and a smaller coarse smooth gap, yet also failed physical
selection; neither constitutes the required stable line law.

The result is a falsification of selecting the coarse P1 space on rank,
equilibrium or reduced row count alone. It does not prove that all weak
multiplier spaces fail. An independent physical target, norm-scaled
signed native inf-sup bound, refinement and all six-channel eccentric
torque/director/shear checks remain open before G0B can pass.

Independent read-only postexecution review verified the commit, all six
source/runner identities, raw digest, exact six cases, 12 successful load
entries, nine stations per load, ranks, energies, normalized gaps and
residual maxima. It agreed this is an adverse fixed-beam physical screen,
not a proof that a continuum bond or every weak mortar fails.

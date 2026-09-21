# Independent F03-K2P v1 postexecution audit

21 September 2026. Read-only audit by the independent F03 KKT mechanics
worker. The reviewer did not edit the candidate or rerun the consumed
registration.

## Evidence integrity

Registration, raw JSONL, stdout and stderr hashes agree with the supervisor
attestation. The start registration and identity match, including clean
candidate commit `0e248a02363653fd9efa9c9ad9137d007a6dc66e`, the
363-file tracked solver-tree hash, all seven K2P source hashes, 21
predecessor source hashes and K0/D1/K1 evidence hashes. All 26 ordered mesh
records, 52 full-row-rank candidate matrices and 104 two-load responses
are present. The terminal contains 103 local diagnostics and one
parity-open load result. No registered resource violation or child solver
exception was found. Stderr has sparse-format and Git-ignore warnings.

The Q4 `N_b=8,N_s=64` P1-shell-grid smooth load has scaled forward
sparse/condensed parity `1.097982078e-10`, beyond the frozen `1e-10`
threshold; the exception is not waived by its small residual. The worst
eight-versus-twelve-point work-scaled load difference is `1.695e-15`.
The signed sine load has essentially zero resultant and a moment of about
`-159154.943 N m`. Maximum normalized force and moment balances are
`3.13e-13` and `2.60e-13`; assembled `λᵀCq` has magnitude no greater than
`6.01e-12 J`. Child exit was zero, wall time 94.94 seconds, and sampled
peak RSS 350.7 MB. These attest a completed bounded diagnostic, not
mechanical acceptance.

## Adverse physical response

At Q4 `N_b=8,N_s=1`, P1-beam produces smooth/sine shell energies near
`2.66e-34/1.61e-34 J` and station motions near `1e-37 m`, even though
the continuum loads are nonzero. Multiplier densities reach about
`3.71e7 N/m`; support moments absorb the load. The S3-V2D counterpart is
also strongly suppressed. This is a possible overconstraint/locking
failure at the 1:8 ratio reach, unresolved by full row rank or small
residuals. The physical-only L2 Schur floors decline on all twelve core
topology/ratio/space refinement sequences, often by factors of 8–59.
These floors are conditional diagnostics rather than the registered
`H^-1/2` inf-sup measure. No independently resolved physical energy or
response reference was executed.

**Adjudication:** K2P v1 completed as registered with one parity-open
response. Neither basis is selected; F03 and G0B remain open. Before
production line coupling, derive the norm-scaled retained stability
criterion and compare responses to independent resolved references,
including the coarse 1:8 locking case. The planar three-component study
cannot qualify the six-channel eccentric attachment.

# P5 arch refinement result and resumption checkpoint — 2026-09-06

The single registered research invocation completed without retry. Its
disposition is `RESEARCH_ARCH_COMPARISONS_BELOW_2_PERCENT`, not production
qualification. `production_qualified=false` and
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED` remain explicit in the aggregate.

## Authority and process

- Frozen commit: `cc8f4b7ddea2deee6b29c9446a9b6269ef9b8d1b`.
- Frozen tree: `55afb09201ad7dc130fb5fa46c88be130d4057ef`.
- Exact parent: `f6b42eabf6fae9be7b212224e1402ec546940b8f`.
- One-use request: `9790867871004048873b26ae6029311e`.
- Immutable request SHA-256:
  `A34925716CED2EF97D8F0265DB3497CB228A718752A9F3ADCEECDBB71737D724`.
- Resource administrator approval: ledger row dated
  `2026-09-06T02:18:01.7190041+00:00`; exact request, clean four-path extent,
  fresh output and process bounds verified before execution.
- Registered child PID: 3200; start Unix ns `1788661129318998600`.
- Child exit 0; wall 33.6181009000029 seconds; CPU 33.46875 seconds;
  peak complete-tree memory 242565120 bytes. These are diagnostics, not a
  claimed performance qualification or general runtime guarantee.
- The acquisition/exact-command/release sequence completed. The global lock
  was released in finally; the one-use claim remains. No child is relaunched
  to recreate this evidence. The administrator was notified for terminal
  accounting. No terminal ledger entry is invented by this record.

Raw output root:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-arch16-20260906-031ef3a8651c4a5c93863f4cafab22cb`.

The worker made all eight records, each with 256 stations. After process exit,
a read-only validator checked strict canonical JSON, authority/worker/raw
hashes, exact record coverage, raw-summary identities, and scalar recovery/
energy recomputation. Re-adjudication reproduced every aggregate decision
field. The worktree was still clean at the frozen commit during validation.
This closeout is a separate later documentation commit, not an edit to that
freeze. The stored authority intentionally requires that exact frozen HEAD;
do not invoke its execution mode from a successor closeout commit.

## Scientific observations and limits

Maximum errors across the eight accepted states:

| Comparison | Relative error | Percent | Frozen criterion |
|---|---:|---:|---:|
| Load at matching crown drop | 0.007448880389156365 | 0.744888% | <2% |
| Compliance-weighted recovery norm | 0.005196145922964133 | 0.519615% | <2% |
| Physical strain energy | 0.006075709572648913 | 0.607571% | <2% |

The path passed from positive to negative accepted-state dP/dd. Its last crown
drop was 0.044820372353098756; load 0.028081301209228228 versus continuum
0.027873673548955667; slope -0.1496705331409128. The full free Hessian minimum
was -0.0026035151318724546, retained rather than deleted or treated as a
failed solver. This is consistent with traversal beyond a limit point, but
does not establish the identity of every spatial critical mode.

Maximum physical equilibrium error: 6.457011568928097e-12; maximum stationary
energy/work closure error: 1.0516761073109393e-16; maximum global force/moment
balance error: 3.632510958695434e-15. Maximum continuum interpolation-sensitivity
error: 4.442756672158544e-8. All are below their frozen limits. Accepted-origin
replay matched at every state, with no acquired plastic history. This elastic
case does not establish general nonlinear material behavior.

The preceding eight-element maximum load error remains 2.97776%, unchanged
historical evidence. Refinement to sixteen reduces it below the frozen 2%
development criterion without changing mechanics, tolerances or references.
The separate continuum solver is still same-author development, not an
independently reviewed qualification oracle. Its symmetric branch does not
cover out-of-plane bifurcation, broader curved/slender families, general
sections, dynamics, or beam-shell connections.

## Preserved artifact inventory

Exactly 16 files, total 4,413,656 bytes; paths below are relative to the raw
output root. This inventory includes empty logs rather than fabricating output.

| Path | Bytes | SHA-256 |
|---|---:|---|
| aggregate.json | 924 | A53D7BAA8AD6A21CA892DBA2F10968458171CE8A87DA6770A418545477F1BC8E |
| inputs.json | 847 | E3D5C9C9AA7E0D039F5A5C3E08B9526FA3D9AA1398FD5AFD716518A04AFEBDDA |
| arch16/complete.json | 6499 | 49E71F90D144963D8739918E5851D35A81D78579D93DB2C877B7681461D2C182 |
| arch16/process-start.json | 369 | 83F812874BC66D2271B6E3E111E0558F61F8F7BBB1A78B66C0A557C44DD8AF5E |
| arch16/process.json | 98 | 798DFD689C3218B73A36B5AD88C9A1C0B7B88A6383CD4F62F8CE878C028782E5 |
| arch16/progress.jsonl | 610 | DA0B8946D63D5F5E6BF618E0A85FD8B881489F94E71BDF1150BAE4CCA190F538 |
| arch16/stderr.log | 0 | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| arch16/stdout.log | 0 | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| arch16/step-00.json | 552269 | F68210C5D0DF71FE12836D9CB226CB5217FCC3FE7A9F0DEEF14EE118EE7212E1 |
| arch16/step-01.json | 551068 | BA571FE1E80F3A5B24C8703E59F986CE56793717B5EB564BD132D794A583AB28 |
| arch16/step-02.json | 551224 | 8C17BA175F13E1CA8D1C4EBEE7501CEF88B8F3383DE51D4BB525513E6B1622D7 |
| arch16/step-03.json | 550642 | 4EEB06FDFB2454EB680E00B9FD9B7BC24B5FF0CDC36AF920A7F0BFFC4BA38429 |
| arch16/step-04.json | 550150 | C87C8F6FE9D62A815C16328F900FFB6D36B35CA566E8FBA1B86CCC87CA7F0665 |
| arch16/step-05.json | 549807 | EAC8370C5F39CC2B2031E393C93D3FA9EB5919D0BCC49822EDE2CE674E494DB0 |
| arch16/step-06.json | 549750 | 753C31D989F0A3179300551133D6C1212C9843224CFAA72BE0BEA0B85EA4D8B5 |
| arch16/step-07.json | 549399 | FC622EAF10081AB4A2BFBBE8C217EF7CD1BC2A3E4E1F7EBC558552E2E208CCBB |

## Resumption and remaining programme

The research task remains active and incomplete. Resume from the dedicated
P5 branch `codex/ge-beam3-curved-p5-objective-lift-v1`, preserving this result
and all previous failures. The appropriate next bounded investigation is
spatial stability/mode classification around the curved arch limit, initially
using the preserved trials where possible. Establish what the symmetric
continuum reference does and does not constrain before authorizing another
larger computation. Do not treat this load/recovery pass as a modal or complete
buckling certificate.

General nonlinear sections, broad curved/slender convergence, extreme local
solves, full physical mass/dynamics, prestressed modal support, production
transactions/restart, independent review, packaging/opt-in integration and
objective beam-shell joints remain open. No src, B2/B3/Q4/S3 mechanics,
qualified evidence, defaults or aliases changed here. Main remains
`09351645ba17a0a5b130a1c7a48007d36dd08ada`. Nothing was pushed, merged,
published or activated. A new resource-heavy test requires a fresh request;
this consumed ID and its frozen execution command must never be reused.

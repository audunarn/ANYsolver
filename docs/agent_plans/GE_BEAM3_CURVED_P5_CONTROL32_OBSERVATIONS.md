# Control32 observation closeout and local stopping-rule witness

## Preserved execution and accounting

The clean observation freeze is commit
`9d3b67a730a1db5d67985c4be7c60586114917f8`, tree
`6610525721f2fa179ce33d4279c294cd82acc34c`.
Request `5b59e2613245422a922616891f8b003b` was executed once and consumed.
Its approved command completed with process exit 0, wall 35.1325966000004
seconds, CPU 34.921875 seconds and peak tree 175,992,832 bytes. Diagnostic
capture succeeded; **solver_outcome remains FAILED**. No qualification or
onset aggregate exists, and no failed target trial is fabricated.

Output directory:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-control32-20260906-765c2849b29f423199dc1e0eea37a9b7`.
Nine ordinary files total 1,158,985 bytes. Key bindings:

| File | Bytes | SHA-256 |
|---|---:|---|
| diagnostic.json | 2335 | 046373A0827D2CCBCD4EBE9EF86D0700D44F7B7FFB1F9B853607E39123C2C10E |
| inputs.json | 2249 | F03363FC6AF96ABE883C953175611FA5993412353E4BA0AE1C6ED36041D98B7F |
| control32/complete.json | 3232 | 5A02E4FF446BC94A281A6F0D65D05681AFFC1A66FDECD4D1ACE285D072FFE062 |
| control32/initial.json | 1129420 | 634A050E8BE813ABC34654CE78F02E5CBDAEEB0B52647B73883E40504A3D0DED |
| control32/progress.jsonl | 21279 | F31A644FF92B4656999B991A804BFDAFE53B3473EC941E9979778697549E35F3 |
| control32/process-start.json | 372 | 2194DCEFF95615B06573FB7D710216ED8105A61AAA686C096AD987BC467ED1F4 |
| control32/process.json | 98 | 54C421637F743384634AEBB54CD2BE84CADCE85C60DAAA3F7468140759F1FF95 |
| control32/stdout.log | 0 | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| control32/stderr.log | 0 | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |

Read-only inspection after resumption verified canonical packet/JSONL,
initial state binding, all eight preserved prior-failure inputs, summary
hashes and observation/outcome agreement. PID 4244 and the shared active
lock were absent. No worker was rerun.

The resource-administrator terminal ledger notification is **pending**:
the tool permission reviewer rejected both the requested report and a
minimal request-ID/outcome report. Explicit user permission was requested;
no alternate transport or direct ledger edit bypasses that restriction.
This document is not a resource administrator terminal row or review.

## Observed failure, not an inferred cause

There are 3 initial and 46 target events. The initial target 0.1 committed
and replayed. Target 0.095 failed without commit. Its physical residual
fell from 0.1128255697913058 to 1.2429099984191595e-11, almost entirely
translational, then all ten line-search candidates failed strict reduction.
The last requested translation/rotation corrections were approximately
2.23e-15/9.77e-15. No local candidate evaluation raised an exception.
The last local stationarity maximum was 2.669485619493793e-12.

The free derivative's observed condition number was approximately 8.52e7,
but linear-system backward residuals were small. These observations show
near-threshold stagnation, not divergence, and do not establish conditioning
or roundoff as the unique cause. Failed target arrays were not serialized.

## Small independent-of-arch-run diagnostic

The existing local solver accepts `||r_internal||_infinity <= 1e-11`,
then returns the uncorrected external residual. That condition alone does
not bound the external error from incomplete internal stationarity.
At fixed external coordinates the first-order sensitivity is

`delta r_external = H_external,internal H_internal,internal^-1 delta r_internal`.

A new test uses one scaled curved element, the existing elastic section,
eight stations per half, and unchanged solver code. Starting from an
ordinary converged local state, it applies a small internal-only perturbation
along the most sensitive internal residual coordinate. No nodal positions,
nodal frames, section origins, mechanics or tolerances are changed.

Observed in a 1.57-second disposable scalar diagnostic:

- accepted internal residual: 4.000125128052548e-12;
- accepted immediately, zero corrections and one evaluation;
- external force-vector difference at identical nodal state:
  4.2966640148367754e-10;
- internal-to-external sensitivity column norm: 107.41617754161774.

This demonstrates a local stopping-contract weakness. It does **not** prove
that this weakness caused the archived 32-element stagnation. The new tests
explicitly reproduce the weakness; their passing must not count as beam
correctness, independent review or qualification.

Focused validation: three new diagnostic tests plus eleven unchanged local
mixed-operator tests passed (14 total, 2.32 seconds). `git diff --check`
passed. Only this document and the new diagnostic test are added; no
implementation file is edited.

## Next authorized-development direction

Before another resource wave, design and review a local accuracy contract
which accounts for the propagated external residual error as well as local
stationarity. Validate it on small straight/curved, coupled elastic and
history-bearing cases, including ill-conditioned blocks and roundoff floors.
Do not simply relax global equilibrium, overwrite a physical residual with
a Schur estimate, or change accepted state/replay semantics. A tighter local
solve may be necessary but is not yet shown sufficient.

Any later 32-element comparison needs a new frozen bounded request and
administrator approval; neither consumed request may be reused. The prior
failed and observation-only records remain immutable. B2/B3/Q4/S3, source
mechanics, defaults and production interfaces are unchanged.

NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

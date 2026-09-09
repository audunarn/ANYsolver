# P5 force-accuracy32 diagnostic closeout

## Authority and immutable outcome

The user explicitly approved administrator communication and proceeding.
The previous observation request `5b59e2613245422a922616891f8b003b` is now
closed by the administrator as successful diagnostic capture, with its
solver FAILED outcome unchanged.

The new request `69778aebc5d44cbd8f91e0426edc2232` was approved, acquired,
executed exactly once and released in finally. Its immutable request is
663 bytes, SHA-256
`519F8AEA9208DA7121D5D90063953F547297B7F2F4E13FE27C44B52CE59702C9`.
Frozen commit `401ee6fa8dcac04caf468ad19888c5e112883b04`, tree
`fb556597aa4ae0fcb9eddee59e9d63f6b5d4a551`; runner SHA-256
`1E18BF5055876103ADA4BBC3E454D8314201E8B3D7A548703B617D28991E5EFF`.

Process exit 0, wall 61.90361509999639 seconds, CPU 61.5625 seconds,
peak tree 176,410,624 bytes. PID 13764 was absent at completion and the
resource lock was released; the permanent request claim remains. The
administrator independently verified the evidence and recorded resource
COMPLETED_PASS at ledger row 635. This is **capture success only**:
solver_outcome remains **FAILED**, production_qualified is false, and no
target.json or qualification aggregate was created. No rerun is authorized.
ANYmesher received the next exclusive resource slot.

Output root:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-force-accuracy32-20260906-36548b8a32f14e16bc114dc80e3b48ef`.
Ten files total 2,360,262 bytes. Bindings:

| Path | Bytes | SHA-256 |
|---|---:|---|
| diagnostic.json | 3392 | BBDF9D7B221B1FFAA50EA0AC0DAE0C9DA89FF060CFB690BAECA95F67385C009C |
| inputs.json | 3510 | B8907763D97E546C9BD603FDD6B2AFF8EF12DA332BFFDBC7623860BB5D36B881 |
| force-accuracy32/complete.json | 4658 | D9DA7BBE2D629C9BDD7C53A4C749E4D1FDFD5B3451283C8CE711C95EC0920C40 |
| force-accuracy32/initial.json | 1135374 | A223046766C5FDAC047060D324A55E769AC2A487D3793A31285B98157265BC59 |
| force-accuracy32/failed_last.json | 1185545 | 5C64284E318ACB894FF2251CE61B6BA2B2A6CE3DB9EE432B814CAE686DABE6CE |
| force-accuracy32/progress.jsonl | 27297 | 9086B94A8B4904EEC85D0DF78E919D3EA52FC9C98AE81775B51EEDAD91F527DC |
| force-accuracy32/process-start.json | 387 | DD45A53F6A82251EF6EB190E700483730B90F48441E8DAC0E5C9D0236E995048 |
| force-accuracy32/process.json | 99 | 58ED2FD32CC75BACC1382949833C86B6677DD86CF0C0ACB5BF0300F8E20FF2FA |
| force-accuracy32/stdout.log | 0 | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| force-accuracy32/stderr.log | 0 | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |

Read-only canonical inspection passed, including all seventeen earlier
failure/observation inputs, the raw bindings and event/checkpoint agreement.
There are 3 INITIAL and 59 TARGET events. The initial state committed and
replayed; target 0.095 failed without committing after 3776 mixed evaluations.

## What the comparison establishes

Residuals fell rapidly from 0.11282556978882873 to 1.314861173855003e-11
at correction 3. The last accepted iterate, correction 8, had residual
1.0956756401139303e-11; all ten candidates failed strict further reduction.
The global 1e-11 acceptance was not relaxed.

The retained **last successful evaluation** is the final rejected candidate,
not an accepted solution. Its residual is 1.1036212565697811e-11. Its
maximum internal residual is 5.217426493554951e-16, maximum local estimated
force error 1.9238194438597246e-14, and sum of local estimated errors
2.0211535283485564e-13. All satisfy the frozen internal/estimated-error
conditions, yet global equilibrium still fails. The estimates are not
rigorous bounds on rounding error.

Therefore tightening local stationarity alone was **not sufficient** for
this test. This is not a scientific rejection of the element formulation,
proof of a missing equilibrium, or justification for weakening tolerance.

## Next arithmetic investigation, no new solver execution

The saved snapshot permits a cheap scalar check of the chord strain input:

`z = U^T d - d0 = (U^T-I)d0 + U^T(d-d0)`.

The identity holds algebraically for any matrix U and vectors d/d0; it is
not an empirical stabilization. On all 192 stored components, interpreting
the existing binary64 chord/matrix values exactly, a 110-digit Decimal
comparison found maximum direct-expression error about 4.30106e-18 and
rearranged-expression error about 1.14068e-19. The worst direct component
is element 21, half 1, component 0. A new standard-library Fraction-based
reproducer checks exact rational equality and the reduction in rounding
error using explicit left-to-right arithmetic matching Jet2 summation.
Both new standard-library arithmetic tests passed in 0.14 seconds;
`git diff --check` passed. This closeout adds exactly this document and
the diagnostic test. It performs no additional beam solve or replay wave.

These results concern only the saved scalar inputs. They do not prove that
the rearrangement fixes the global residual, preserves all floating-point
derivative behavior, or qualifies an element. No mechanics implementation is
changed in this closeout. Next, develop and validate an opt-in algebraically
equivalent evaluation path for value, analytic residual and tangent on small
elastic/plastic, objective and replay cases. Only after that work and a new
reviewed freeze may another bounded resource comparison be requested.

All external records remain immutable. No production source, default,
section coefficient, physical tolerance, version or publication changes.
Broad standalone and objective beam-shell qualification remain incomplete.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

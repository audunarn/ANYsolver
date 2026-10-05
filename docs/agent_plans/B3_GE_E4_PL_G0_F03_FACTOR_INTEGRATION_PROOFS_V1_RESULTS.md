# F03 sparse factor and integration connection: proof results

22 September 2026. **33 distinct current synthetic tests pass. Independent
code/mechanics review is closed for this bounded batch. G0B remains open;
no physical reference equilibrium or native element evaluation ran.**

Source: `126a4eb1122d4b36b7651d54d73c4b32fa139ead` on the isolated
`codex/b3-ge-e4-pl-integration` branch. Existing product behaviour, version
and previously sealed evidence remain unchanged.

## Current numerical contract

**`B3_GE_E4_PL_G0_F03_SPARSE_INTEGRATION_ERRATUM.md` is controlling** for
root normalization and the error-bound interpretation. It supersedes the
incompatible paragraphs in `SPARSE_INTEGRATION_CHECKS.md` and the earlier
`LOCAL_NUMERICAL_ADMISSION_DRAFT.md`. Those older drafts remain historical
records; their residual-free expression is not a full solution-error bound.

The root comparison retains the original denominator `max(1,||C||F)`.
Combined K retains its own nonzero Frobenius norm, and load comparison uses
the original infinity-norm floor. Limits remain `1e-11`.

The original integration sensitivity has its original `1e-6` gate. The
additional rigorous bound on the alternate exact solution relative to the
saved primary state includes the certified primary residual `rU`:

```
(dH*zU + db + rU) / (sigmaL*zL*(1-alphaU)) <= 1e-6.
```

Both quantities are reported separately and are undefined if alpha reaches
one. An identical matrix/load pair has zero integration sensitivity but
can have a nonzero saved-state solution-error bound. This is numerical
verification; it does not establish physical reference convergence.

## Implemented connection

One sparse SuperLU factorization now supplies candidate L/diagonal factors
for the separately implemented exact full-K positivity proof. It uses the
documented inverse permutation gather and requires matching row/column maps.
Positive pivots do not establish positivity; the complete congruence residual
must pass. Candidate production performs no RHS solve or fallback.

The installed backend returns sparse arrays and, on a coupled 98-unknown
algebraic graph, unordered compressed entries. The adapter validates copied
buffers and applies an index/value permutation before canonical conversion.
It preserves every value bit and rejects duplicates rather than summing them.
Input matrix identity is checked before the exact positivity proof.

The integration verifier binds H, Hplus, b, bplus and z, reverifies all
primary inverse columns, processes the complete sparse difference pattern,
and encloses the alternate residual without a second candidate solve.
Connected synthetic tests exercise the owned scaled system, factor producer,
positivity proof, one candidate solve and saved-column verification together.
Saved-only verification reproduces the result without another factorization
or RHS solve; changed state is checked again and rejected when inconsistent.
All owners retain `NOT_QUALIFIED` status after these numerical checks.

## Verification and independent review

| Final group | Distinct passes | Final raw log |
|---|---:|---|
| Actual sparse factor production and native buffer handling | 19 | `sparse-factor-normalized-1b52c13e48d04cac8e8df30bbd4a2603.log` |
| Integration and corrected error bounds | 12 | `sparse-integration-connection-fixed-1e5f7c4eb41342d8ac0fbcb8448b756e.log` |
| Connected numerical and saved-column routes | 2 | Same affected 14-test log |

Earlier overlapping runs are not added to 33. All numerical commands used
the five thread caps at one, unique temporary logs/basetemps and no pytest
cache. The tests include sparse factorizations and synthetic solves, with
no physical reference solve or performance qualification.

Independent reviewer `finite_pad_axis_review` closed factor convention,
ownership, buffer handling, error-bound, root-normalization and connection
findings on the final source bindings. Initial interface failures, the
unordered-factor graph failure, the red normalization/residual checks and
all intermediate runs remain visible in the raw archive.

## Evidence and next action

The closed root `.qualification/b3-ge-e4-pl/f03-factor-integration-proof-v1`
contains 22 bound files plus inventory: eight source/doc/test copies, all
twelve raw logs, manifest and independent-review record. Read-back of the
complete inventory and hashes passed. Do not extend this root.

```
inventory 64ae0becbe72c8a949233e8be3c127c75697287f18f68a09e23476accab93868
manifest  e9743cda01e7c50eb6561a13315b1ac5fb8b99a93d22d7198154ceb3e62ecd87
review    7fa8dc29f267b63a7ea090219dc817eabe7aa031308ffef65ac23f747b887f8e
```

The next work is physical scaling/state binding, three-root and free-slope
rank admission, separate shell/beam integration checks, stationarity and
physical work/reaction checks, followed by the complete saved archive and
independent adjudicator. The prototype comparison certificate and factor
producer still need a frozen scientific method/resource selection.

Then freeze the conforming nested case family and numerical protocol for
independent review before any new one-use scientific registration. Native
factor peak memory requires external supervision; inverse-column evidence
still costs 8*N*N raw bytes. The p1 support-lift limitation, full physical
convergence criteria, other G0 foundations and mandatory external references
remain open. No old scientific execution, promotion or release was retried.

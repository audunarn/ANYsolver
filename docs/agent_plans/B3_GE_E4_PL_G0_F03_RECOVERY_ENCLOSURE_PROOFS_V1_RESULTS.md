# Bounded recovery and enclosure proofs — results v1

22 September 2026. Source commit
`5be7447fc47b2b216238d15f020b406c7028d165` on
`codex/b3-ge-e4-pl-integration`.

**32 distinct focused checks passed, with independent code/mechanics review
closed for this bounded batch. G0B remains open and G1 remains barred.**
No physical reference equilibrium, native element evaluation, installed
qualification or performance measurement was executed. Main, product code,
package version, historical failures and physical HOLD results are unchanged.

## Implemented and reviewed

The separate Action evaluator encloses the existing polynomial/cosine
representation using exact rational arithmetic and explicit fixed-order
Taylor remainders. It first combines overlapping intervals exactly, including
intervals whose endpoints coincide when converted to binary64. Cancellation
therefore precedes approximation. Saved comparisons pass only when the entire
error interval meets the limit; definite violations fail and ambiguous bounds
remain HOLD. No automatic precision retry or display-value acceptance occurs.
The existing Decimal display method and represented load remain unchanged.

Supplemental support recovery implements the admissible Q1 edge-rotation
lift, with unchanged translation lifts and explicit Q2/Q3 parity. It binds
the input to a freshly owned recovery of the same grid and predecessor,
computes both support-work routes, and tests a true first-free nodal shift.
Zero-free-coordinate models are rejected because this shift inventory does
not exist. The original recovery's unavailable-P1 field is unchanged; the
new helper reports its own explicit lift family.

Raw physical moment balance remains separate from the represented gamma
identity. Actual held-frequency load integrals and their differences from
nominal values are retained without changing either load convention.
The connection checks exercise all eight total bands and support actions
through certified comparisons. They explicitly reject the manufactured
state's nonzero equilibrium residual even though its algebraic work identities
agree. Those identities cannot establish physical equilibrium.

Independent review required and accepted these corrections:

- Charge saved values, normalization scales and thresholds to the Action
  arithmetic budget before computing the enclosure.
- Validate all public lift inputs before dispatch, and reject a missing
  first-free-coordinate shift inventory.
- Bound symbolic storage before constructing new Actions, including temporary
  work and final actual-minus-nominal load differences.
- Continue from the newly owned factory recovery after rebinding.

These are caller-bounded arithmetic and storage estimates, not measured peak
memory or a practical-scale qualification.

## Executed checks and immutable evidence

| Final group | Distinct passes | Final raw log |
|---|---:|---|
| Action enclosures and resource guards | 21 | `f03-action-operands-fixed-43cb77a0d9ba4bbd957632e8f94f9f36.log` |
| Supplemental support recovery | 9 | `f03-support-all-thread-caps-4b6229cc9683449091bee8750d41ee80.log` |
| Eight total-band comparisons | 1 | `f03-band-enclosure-connection-55c1f3e3fda84eacb40591af9094ca6f.log` |
| Support/enclosure connection | 1 | `f03-support-enclosure-connection-fixed-15d61418d1b94df4a6567f0701c660c2.log` |

Each final group exited zero. The environment was Python 3.14.2,
NumPy 2.4.6 and SciPy 1.17.1 on Windows, with all five registered thread caps
at one, unique temporary logs/basetemps and pytest cache disabled.
The final support group was rerun once because its previous command did not
explicitly set the fifth cap. The unchanged band test retains its earlier
pass; it does not import the supplemental support module.

All 16 raw logs are preserved, including the initial collection error,
intermediate implementation failures, red guard regressions, and the
connection fixture's resource rejection. That fixture declared only 32M
integer bits, below the new conservative preflight. It was changed to 80M
bits, matching the standalone synthetic tests; the 512 MiB workspace cap,
mechanics and tolerances were unchanged. This was a synthetic fixture
correction, not a revised scientific registration. Repeated passes are not
added to the distinct total.

Independent reviewer `/root/finite_pad_axis_review` accepted all seven final
source/document/test hashes without remaining findings. Review was read-only
and did not independently rerun tests. The closed archive is
`.qualification/b3-ge-e4-pl/f03-recovery-enclosure-proof-v1`:
26 bound files plus inventory, comprising seven reviewed files, the controlling
contract, 16 logs, manifest and review. Full inventory/byte/hash read-back passed.

```
inventory 861a6b02b09fead9b6af8af0c2efc6123c91da097a5688caa15f0369c431c1db
manifest  edb3342f72fae39031980bc05bf2592ac64905a54f9bd919d674b5200ac5b274
review    fc0550ec6609fc1231034ec92a3b7b9ae10883e6a240de69f091572558456905
```

Do not extend or overwrite this archive. The manifest records actual
dependency locations, source hashes and the limited reuse of the unchanged
band check. Earlier sealed roots and failures retain their original meaning.

## Next required work

Complete the saved-recovery admission layer under
`B3_GE_E4_PL_G0_F03_RECOVERY_ADMISSION_NEXT_CONTRACT.md`. It still needs
owned saved density/cosine/endpoint-atom binding, endpoint partition checks,
total and line-only band inventory, saved support-route and raw shift
acceptance, the complete scaled virtual-work inventory, and the full 48/64
functional norm checks with signed channels and unchanged resolution limits.
The current tests establish building blocks, not that complete admission.

Then implement the complete saved archive and independent adjudication route,
freeze numerical methods/cases/resources, and obtain independent protocol
review before any new scientific registration. No scientific case family or
certificate method is selected by this proof batch. Native shell/beam
mechanics, the B2 option, mandatory external references and later programme
gates remain open. No production promotion or release is implied.

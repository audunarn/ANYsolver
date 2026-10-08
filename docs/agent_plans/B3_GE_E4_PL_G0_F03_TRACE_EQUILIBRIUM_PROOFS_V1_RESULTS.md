# F03 sparse trace and equilibrium proof results

22 September 2026. **34 distinct current tests pass. Independent code and
mechanics review is closed for this bounded batch. G0B remains open and G1
remains barred.** No scientific reference equilibrium or native element
evaluation was executed.

Combined source: `a858e787d86e6f8e3a65e16f5268ce68fa53c8a1` on the isolated
`codex/b3-ge-e4-pl-integration` branch. Trace and recovery-contract source was
first saved at `22d991071a3c0a62035259432090030c9573682d`. Main, defaults,
package versions and earlier sealed evidence were not changed by this batch.

## Implemented and tested

The trace verifier binds all 27 frozen station observations to exact local
trace extraction: nine stations, three physical derivative orders, explicit
internal-right/final-left evaluation. It checks complete sparse matrices,
saved actions and the root/tip/free-slope operators, including direct
endpoint-to-station consistency. Opposite small reference errors cannot
hide a larger direct mismatch. Its owned observation inventory survives
caller-list mutation. Bound extracted root and free-slope rows also pass
the existing exact rank proof on the manufactured test model.

The equilibrium verifier checks separate shell, beam and combined
integration differences, all six scaled skew norms, primal stationarity,
physical root compatibility and energy balance after complete state
binding. A connected synthetic candidate solve passes those checks without
any additional solve during admission. The candidate remains NOT_QUALIFIED.

Independent review required four corrections, all implemented and tested:

- Use the actual rounded scaled matrix entries, then exact rational norms.
  Ideal unrounded scaling could hide the stored matrix's rounding skew.
- Sum physical shell and beam work separately for energy acceptance.
  The rounded combined-stiffness action is only an additional diagnostic.
- Own shared inputs once before binding and reuse those copies afterward.
  Caller mutation cannot make metrics refer to different bytes than hashes.
- Preflight the complete six-block sparse envelope and report actual counts.

No tolerance changed. The four added regression tests failed on the initial
implementation and passed after correction. That failed run is preserved.

## Verification and evidence

| Final group | Passes | Raw log |
|---|---:|---|
| Trace binding, ownership and extracted rank | 20 | `f03-trace-owned-inventory-0228001871ac4a38850ac96bd9b73f91.log` |
| Corrected numerical equilibrium checks | 13 | `f03-sparse-equilibrium-corrections-fixed-20260922.log` |
| Actual candidate to saved checks | 1 | `f03-mechanical-connection-0004c77a27044950910df8d9509376cb.log` |

All final commands exited zero with the five thread caps at one, temporary
logs/basetemps and pytest cache disabled. Earlier overlapping runs are not
added to 34. These are source-level synthetic/manufactured checks, not
installed-artifact, physical-convergence or performance qualification.

Independent reviewer `finite_pad_axis_review` accepted all eight current
source/document/test bindings without remaining findings. The new closed
root `.qualification/b3-ge-e4-pl/f03-trace-equilibrium-proof-v1` contains
18 bound files plus inventory: eight source/document/test copies, eight
raw logs, manifest and review. Complete byte/hash read-back passed.

```
inventory e331f76e9ae76ed23558fb7824a3e3a0e9b79ade5a2d6ee5dae5f617f998dc33
manifest  415a2f6a88178cb5c04923cb64ca30709ba912e4422b1f0d06a1bf64251a2b90
review    2237d97dcfcba38aba4799129d6f5df06dcc2938a441a51eefcc5b5bfdbf572b
```

Do not overwrite or extend this root. Earlier scientific failures and
physical HOLD results remain unchanged.

## Next physical-recovery implementation

The independently reviewed next contract is
`B3_GE_E4_PL_G0_F03_RECOVERY_ADMISSION_NEXT_CONTRACT.md`. It requires a
certified Action comparison layer before saved cosine-load work can support
acceptance. The current Decimal values remain display-only. Complete the
independent edge routes, admitted lift shifts, density/atom/partition checks,
all eight bands, virtual-work inventory and full-functional checks.

The review derived an admissible Q1 support-rotation lift, preserving the
physical boundary displacement without changing equilibrium physics. Its
implementation and executable checks remain open; current unavailable-P1
outputs are unchanged. The contract also distinguishes raw physical moment
balance from the represented gamma adjoint identity, and actual held-frequency
load integrals from historical nominal values. Neither distinction permits
removing a physical defect or weakening a frozen gate.

Then complete the saved archive and independent adjudicator, freeze numerical
method/cases/resources, and obtain independent protocol review before any
new scientific registration. Other G0 foundations, the B2 option, external
references, practical scale and the full product/consumer programme remain
open. No production promotion or release is implied.

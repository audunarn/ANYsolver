# F03-K0 v1: consumed diagnostic execution, programming abort

The one-shot `G0_F03_K0_V1` registration bound integration commit
`7c2b448db791cfe5329000c6c955cf006fca9b45`. It was executed
once on 21 September 2026 through the registered supervisor. The child
exited **1**, completed **zero** of the 18 meshes, and wrote an
`ABORTED_NOT_QUALIFIED` terminal. The supervisor attested
`ABORTED_OR_INCOMPLETE_NOT_QUALIFIED`; no multiplier candidate, F03
selection or G0 acceptance resulted.

The first `solve_exact` call raised `TypeError` in NumPy 2.4.6 while
building the exact condensed matrix: `np.block` no longer accepted
the nested tuple structure. The correction is a nested list of the
same four blocks; the governing signs and dimensions did not change.
The changed source requires a new registration. **Do not rerun v1.**

Immutable evidence lives under
`C:\Github\ANYsolver\.qualification\b3-ge-e4-pl`:

| Item | SHA-256 |
|---|---|
| `f03-k0-v1-registration.json` | `5d6a2594cedc3443cfb4b79b68c1335006404f212e36314f3a7197decda35d61` |
| `f03-k0-v1/raw.jsonl` | `b679cdd0d8c571572e10a4a73aff13e31916813be5b2fdc142081734c854029d` |
| `f03-k0-v1.stderr.log` | `ae4f8ffd833556a5c609f78fb9711a82f321cc7ee0b244645b2b808093191f89` |
| `f03-k0-v1.attestation.json` | `a7c5a3187343bbf05a29e2669259c156f7d1979ede082dc15e8e322e69608a59` |

The stdout log is empty. The v1 registration and all partial evidence
remain retained, without relabeling this failure as a mechanical result.

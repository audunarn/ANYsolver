# F03 Nm128 provisional stability diagnostic: terminal stop

22 September 2026. This records a **failed/incomplete pre-solve diagnostic**, not a
qualification result or permission to run the loaded Nm128 extension. G0B remains
open. The B3-GE/E4-PL multi-element objective and B2 option are unchanged.

## Fixed identities

- Execution source: integration branch commit `90b99cd9641a338a7b2b4cf5ee999b1a66bfaa70`.
- Single-use registration: `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-nm128-stability-registration-v1/registration.json`, SHA-256 `b22e8a637312df848cacc4d6d67f77736a20217187c0914304029e3cb0317fc6`.
- Raw cases: `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-nm128-stability-cases-v1/`.
- Partial read-only adjudication: `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-nm128-stability-stop-v1/adjudication.json`, SHA-256 `334d98bd59ae209c0f82adf750eef6badab0fc222368f9256c83710848057067`.
- Post-hoc mode description from the saved Q4 Schur payloads only:
  `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-nm128-stability-mode-diagnostic-v1/report.json`, SHA-256 `d25e2733bda00f2ea78811260c1103e4982bfef94729e4d5082add68ade1c709`.
- Independent code and mechanics reviews checked registration before execution and
  verified all three preserved case receipts afterward. The registration and raw
  case directories are immutable; no retry or replacement is authorized by this
  record. The 16 focused admission/stability tests passed before execution.

| Case | Exit | Minimum generalized eigenvalue | Minimum beta | Maximum supported-mode residual | Sampled peak RSS |
|---|---:|---:|---:|---:|---:|
| Q4 Nm64 | 0 | 0.06903201593 | 0.26273944495 | 9.8178e-9 | 219,996,160 B |
| Q4 Nm128 | 0 | 0.01980712911 | 0.14073780271 | 9.5583e-9 | 223,555,584 B |
| CST-CB Nm64 | 2, numerical failure | 0.06547766214 | 0.25588603350 (unadjudicated) | **1.0129580633e-8** | 219,271,168 B |
| CST-CB Nm128 | Not launched | — | — | — | — |

The registered supported-mode residual limit was `1e-8`. CST-CB Nm64 exceeded
it by 1.2958%, despite satisfying the other reported finite skew, factor-solve,
Schur-eigen and minimum-eigen screening checks. A favorable eigenvalue does not
override a failed numerical condition. Both Q4 cases passed the read-only
adjudicator, which recomputed the saved bounded Schur spectra, dual norm, derived
beta values, source identities and sampled resource records.

The Q4 beta minimum ratio Nm128/Nm64 is `0.5356554008794752`, a 46.4% decline;
the corresponding generalized minimum falls by about 71.3%. This is an adverse
finite-mesh trend for the frozen classical P1 and discrete H-minus-one-half norm,
not a continuum conclusion or a native B3-GE/E4-PL result. The full four-case
adjudicator cannot pass with the failed and missing cases.

A post-hoc lowest-vector description suggests a mesh-scale mode in the first
translation channel: after discarding nodal amplitudes below 5% of that
channel's maximum, the number of sign changes rises from 37 to 110 as Nm
doubles. The first ten generalized minima form a cluster; an individual
eigenvector can rotate in that cluster. This descriptive result is neither a
registered acceptance check nor proof of which formulation component causes
the adverse trend.

## Interpretation and next mechanical work

`STABILITY_ADMISSION_UNRESOLVED` remains the only admissible status. The sparse
inverse probe measures two eigenvalues nearest zero; it does not establish that
the complete supported stiffness is positive definite. The residual screening
margin is heuristic, and no physical beta floor or refinement-trend acceptance
criterion was frozen. RSS was sampled rather than hard-capped; dependency
hashes cover Python package entry files but not compiled SciPy/BLAS bytes.

Before proposing another registration, independently derive a positive-energy
check or supported-energy bound, then examine whether the declining Q4 beta is
an interface-resolution instability, a norm/trace choice, or a physical
discretization effect. Diagnose the CST-CB mode-residual discrepancy without
rerunning its consumed scientific case. Candidate changes require a new,
reviewed source and registration with explicit prospective criteria. Do not
launch a loaded Nm128 extension, relax the existing threshold retrospectively,
promote the P1 multiplier policy, or advance G1 from this evidence.

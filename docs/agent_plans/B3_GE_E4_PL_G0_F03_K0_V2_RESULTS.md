# F03-K0 v2: completed planar screen, no accepted line space

21 September 2026. This is the disposition of the registered, single-use
source-backed diagnostic at `9efc80e3fefb4fa30643f7431a49a8e2137c74ff`.
The independent numerical and provenance audit is
[`B3_GE_E4_PL_G0_F03_K0_REVIEW_V7.md`](B3_GE_E4_PL_G0_F03_K0_REVIEW_V7.md).
This document does not change the registration, raw evidence, or criteria.

## Evidence identity and execution

- v2 registration: `C:\Github\ANYsolver\.qualification\b3-ge-e4-pl\f03-k0-v2-registration.json`, SHA-256 `75269e4fe8788ca39b1f40ccc786d8b72970f9011ffb9db9c78889f52d3cd1a3`.
- Raw JSONL: `C:\Github\ANYsolver\.qualification\b3-ge-e4-pl\f03-k0-v2\raw.jsonl`, SHA-256 `7b8b3caea8d29840fb2839f4a3bd1843e57d8d589709aa31d60779f43557f496`.
- Supervisor attestation SHA-256: `0cf4c9a056f84e16329ca61c1f6b9a1fbe0d358ea7823b67fa6ec1ce10cf1d14`.
- The v1 attempt aborted before the first mesh on a `np.block` construction error; its immutable evidence and correction are recorded separately in [`B3_GE_E4_PL_G0_F03_K0_V1_ABORT.md`](B3_GE_E4_PL_G0_F03_K0_V1_ABORT.md). V1 was not rerun or combined with v2.
- The v2 child exited zero: 18 meshes, 90 candidate cases, 180 load rows and 30 trend records in the prescribed order. The supervisor status was `COMPLETE_PLANAR_SCREEN_NOT_F03_ACCEPTANCE`, at 103.41 seconds and 232,931,328 bytes maximum *sampled* child RSS, under the registered limits. This was a source import from version 0.4.7 with installed distribution metadata 0.4.6, **not** installed-wheel verification.

## Frozen disposition

Of the 180 load rows, 134 were `CONSTRAINT_RANK_LOSS`, 38 were
`RESTRICTED_MECHANICS_FAIL`, and eight were
`RESTRICTED_LOCAL_SCREEN_PASS_PENDING_TRENDS`. Every trend is
`INCOMPLETE_OR_LOCAL_FAILURE`. All union and dual spaces lose row rank on
every mesh. P1 beam has full constraint-row rank but retains unsupported
trace modes; its weak residual alone does not establish physical pointwise
continuity. The finest smooth-load maximum gap remains approximately
0.0228–0.0350 times the declared displacement scale across topology/ratio
pairs. Four physical-only spectral floor series decay on both size doublings.

The independently reconstructed predicates attribute all 38 mechanics-fail
rows to the supported-pose finite-difference derivative threshold (`1e-10`).
Twenty-six also miss the work-gradient threshold and five Q4 P1-shell rows
miss the dense/sparse solution-parity threshold (maximum `6.79e-9`). These
observations are failures against the *frozen* screen. The small absolute
finite perturbation against metre-scale reference positions suggests possible
roundoff, but that explanation is not yet established. Equilibrium and weak
residuals being small does not resolve the failures or select a space.

**Decision: F03-K0 produced a complete negative/prioritization inventory;
no multiplier space is selected. F03, G0B and G0 remain open.** This planar
three-channel screen cannot qualify the required six-channel eccentric law,
torque transfer, thinning/shear, curved interfaces, reciprocal 1:8 mesh
ratios, or final production coupling.

## Required next work

1. Register and independently inspect a separate derivative step-size/error-budget study, with preserved absolute and normalized errors, multiple stations and both shell topologies. Diagnose the five parity exceptions independently. Do not revise v2 or silently relax its `1e-10` threshold.
2. Derive admissible reduced multiplier candidates from the observed row and trace spaces and repeat a separately registered physical stability/refinement screen. A penalty or artificial stiffness is not a fallback.
3. Return to the complete G0 mechanics contract and its independent review before G1 production integration. The new capability, practical-scale, installed artifacts, external references, consumer path and release remain future gates.

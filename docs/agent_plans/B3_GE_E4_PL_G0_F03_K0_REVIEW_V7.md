# F03-K0 v2 independent evidence review, v7

21 September 2026. Read-only adjudication of the single registered v2 source-backed planar diagnostic. No candidate was rerun and no raw evidence was changed. **Execution completed; no multiplier space is selected; full F03/G0 remains open.** The v1 aborted registration is separate and supplies no meshes to v2.

## Provenance and completeness

The v2 registration is frozen at commit `9efc80e3fefb4fa30643f7431a49a8e2137c74ff`, with exact ignored evidence path `C:\Github\ANYsolver\.qualification\b3-ge-e4-pl\f03-k0-v2`, 7200 s external wall limit and 8 GiB sampled child-RSS limit. Independently recomputed SHA-256 for registration, raw JSONL, stdout and stderr match all four supervisor attestation hashes. The raw `start` embeds the exact registration, registration hash and identity; attested identity matches the registration. At source comparison, checkout HEAD was the registered commit and all 14 enumerated source hashes and the aggregate hash over 363 tracked `src/anysolver` paths matched its registered identity. It explicitly imported source `anysolver` 0.4.7 from this checkout while distribution metadata is 0.4.6; this is a **source-backed diagnostic**, not an installed-wheel qualification.

The 21 JSONL records are one start, 18 indexed meshes in the prescribed topology/ratio/refinement order, one 30-row trend inventory and one final terminal. They contain 90 cases and 180 load rows. Supervisor status is `COMPLETE_PLANAR_SCREEN_NOT_F03_ACCEPTANCE`, observed exit 0, 18 meshes, no resource or read error, 103.41 s elapsed and 232,931,328-byte sampled RSS maximum. Child terminal is `PLANAR_SCREEN_HAS_LOCAL_PASSES_NOT_F03_ACCEPTANCE` with 18 meshes, 100.76 s and 233,734,144-byte own sampled maximum. The two sampled maxima need not agree. Standard output is empty; stderr has 46 SciPy CSC-conversion performance warnings (one per full-rank load solve), no traceback, plus Git user-ignore permission warnings. Completion attests inventory execution, not a mechanics pass.

## Candidate pattern

Each cell below counts **six load rows** across `N_b=4,8,16` for one topology and `N_s/N_b` ratio. `R` means constraint rank loss; `F` means restricted mechanics fail; `P` means local pass pending trends. The nominal beam:shell ratios in the manifest are the reciprocal `2:1,1:1,1:2`.

| Topology | `N_s/N_b` | P0 union | P1 shell | P1 beam | P1 union | Dual union |
|---|---:|---:|---:|---:|---:|---:|
| Q4 | 0.5 | 6R | 6F | 6F | 6R | 6R |
| Q4 | 1 | 6R | 2R/4F | 6F | 6R | 6R |
| Q4 | 2 | 6R | 6R | 6F | 6R | 6R |
| S3-V2D | 0.5 | 6R | 6R | 4F/2P | 6R | 6R |
| S3-V2D | 1 | 6R | 6R | 2F/4P | 6R | 6R |
| S3-V2D | 2 | 6R | 6R | 4F/2P | 6R | 6R |

Totals: **134 R, 38 F, 8 P**. All union/dual spaces lose row rank on all 18 meshes. P1 shell retains full rank on only five Q4 meshes and none of nine S3-V2D meshes. P1 beam retains full rank on all 18 meshes, but only four S3-V2D meshes have both local load passes; none of its six topology/ratio refinement triples has all six local passes. Consequently all **30 trend dispositions are `INCOMPLETE_OR_LOCAL_FAILURE`**. No P0, P1 or dual space can be selected from this screen, and the screen cannot test the six-channel eccentric law in any case.

P1 beam's full constraint-row rank does not mean pointwise continuity: its weighted trace rank exceeds the multiplier-row rank on every mesh. The smooth-load maximum physical gap at the finest `N_b=16` ranges from about `0.0228` to `0.0350` in units of `u*` across the six topology/ratio pairs, despite tiny weak residuals. The registered protocol treats this gap as a trend, without a fixed absolute local-pass cutoff; the eight local `P` labels therefore do not certify a strong gap bound.

All 46 load solves with full row rank reported finite parity, residual, physical spectra and support-balance data. Their scaled free equilibrium is at most `6.58e-14`, weak residual at most `9.39e-14`, separate force/moment balance at most `5.16e-14`/`2.68e-14`, and `K_e` minimum eigen ratios are positive (`5.89e-7` to `4.28e-5`). Both physical-only and exact signed Schur floors are positive in these 46 rows; neither has a reported negative eigenvalue. Physical-only floors range from `2.39e-8` to `7.22e-3`, above the local `1e-12` floor, but four triples carry a twofold-on-both-doublings **decaying physical floor** flag: Q4 P1 shell at `N_s/N_b=.5`, Q4 P1 beam at `2`, and S3-V2D P1 beam at `1` and `2`. None can be promoted to a passing trend because its local statuses failed.

## Mechanical versus numerical interpretation

Independent reconstruction of the frozen local predicates attributes **all 38 mechanics-fail load rows** to the common supported-pose derivative probe exceeding its `1e-10` relative threshold. Twenty-six also exceed the work-gradient threshold, and five Q4 P1-shell rows independently exceed the `1e-10` dense/sparse solution-parity threshold (maximum `6.79e-9`). No other registered threshold explains those rows. The failed derivative values range up to `8.30e-10`; Q4 fails on every mesh while S3-V2D passes on four isolated meshes. Reference gaps are zero, sampled host errors at most about `5.6e-17`, unrestricted patch gaps about `1.1e-16`, and equilibrium/balance checks are much smaller than their limits. This pattern identifies a **numerical-oracle/threshold inconsistency to investigate**, not evidence that a particular beam-shell law is mechanically invalid. The central-difference step `h=1e-3` acts on directions scaled around `u*=6.8e-5 m`, producing displacement perturbations around `7e-8 m` against metre-scale reference coordinates; cancellation at the frozen `1e-10` relative cutoff is plausible, but the evidence does not prove that roundoff is the sole cause. Calibrate the independent finite-difference oracle over a separately registered step-size/error-budget study, preserve v2 failures as observed, and also explain the five parity failures before changing a threshold or selecting a space. A future correction requires a new source, reviewed registration and cold execution; v2 is not rerunnable.

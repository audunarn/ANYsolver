# Representative nonlinear profile and successor selection

These profiles use the installed candidate wheel for revision
`0a56c2c118ffbdea65f749df1a533d99350f26fe` after one unmeasured warm solve.
They are diagnostic cProfile runs, separate from the alternating wall-time
measurements used by the performance gate. Cumulative times overlap and must
not be added.

| Case | Profiled wall time | Python calls | Dominant measured path |
| --- | ---: | ---: | --- |
| `nonsymmetric_follower_shell_holdout` | 17.739 s | 41,542,600 | repeated external-load lifecycle and signature validation |
| `plastic_s3_reversal_holdout` | 15.100 s | 30,422,515 | S3 bubble equilibrium and strain-jet arithmetic |
| `large_deflection_shell_holdout` | 11.040 s | 21,094,275 | consistent corotational tangent and frame derivatives |

## Ranked observations

1. **Follower-load lifecycle validation is the selected successor.** The
   follower profile attributes 16.408 s cumulative to `external_load_at` and
   its weighted external-load assembly path. Current-state tangent lifecycle
   guards account for 12.472 s cumulative. Within those guards,
   `e4_pl_s3_state.signature` is called 3,815,504 times and accounts for 6.545 s
   cumulative. The next experiment should cache or hoist the exact qualified
   lifecycle signature validation for an analysis-local immutable
   model/load revision. It must fail closed on mutation or revision change and
   must continue to evaluate the current follower force and tangent at every
   required state.
2. **S3 constitutive arithmetic is the second candidate.** The plastic profile
   attributes 14.194 s cumulative to nonlinear S3 response, 11.637 s to native
   bubble equilibrium, and 11.514 s to incremental strain jets. Jet
   multiplication accounts for 8.549 s cumulative across about 667,000 calls,
   while NumPy outer products account for 3.302 s cumulative across about
   1.34 million calls. This warrants a separate mechanics-preserving kernel
   experiment after the lifecycle work.
3. **Consistent corotational derivatives are the third candidate.** The large
   shell profile attributes 10.081 s cumulative to 1,200 corotational element
   responses, including 5.299 s in the consistent tangent and 4.744 s in
   rotation sensitivity. This path remains important, but changing it carries
   a larger mechanics and derivative-verification burden.

## Successor gate

Implement only the analysis-local lifecycle/signature validation cache first.
Bind it to the same ownership, observation, and generation rules as the
qualified assembly runtime. Verify mutation invalidation and stale-signature
fallback before timing it. Reuse this representative campaign and require the
same physical comparisons. Keep the existing 10% representative target and
5% easy-control regression limit; report follower-load time separately because
the present candidate regressed that case by 0.96% despite passing the global
median gate.

## Evidence identity

- Profile runner SHA-256: `20c75c455cbf3605fa4313bd0b3d49b74d7d4293b79e2d74fcfe3436bda72c8e`
- Campaign runner SHA-256: `44d83a6d0889dee3364cfb6ade50c73add8a4ec0d8375349d7ac48ee12b5424b`
- Frozen `_build_case` SHA-256: `f1cf32fb23e544b2d83672ec7c790d07ae944ede6ea9de857f7fd06fffae2933`
- Large-shell profile SHA-256: `d9ad3bbcdb4b78904ff04d8cfe9861f8aa770e999cd203b074cd3821973ad046`
- Plastic-S3 profile SHA-256: `02bb9ee756da507ff86157236e94db431f7d932851829215dfa14e5de51d9d8d`
- Follower-shell profile SHA-256: `d6f3acbe5f56f1b6ac660e883c01c52a51b5ada57f34fd9d8e400b2c51355c70`
- Build-provenance SHA-256: `adf4ecea7a9cef40e80dbd0b9d02e07c00f1cfe4598edb308682033f38dc0b41`
- Candidate wheel SHA-256: `eea68a24a28fb37b7394ebaadf73b9412834afcdfd394f6a4eb774de06db0d0d`

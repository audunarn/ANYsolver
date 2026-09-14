# G3b weighted Q4 reference-linear development checkpoint

Status: **DEVELOPMENT_SMOKE_PASSED_NOT_G3B_QUALIFICATION**.
Parent: M_S3 `df9a68310943b2e8455d2a06905bd714321bee14`,
tree `725c435f594386d616d805813585cae84cdf8c60`.

## Scope and exact trace

`WeightedQ4TranslationReferenceProblem` implements frozen M_Q4_WEIGHTED.
The native beam tip at (1/2,1/2,0) is coupled to the four square Q4 corners
with exact rational weights 1/4. Seven node IDs remain distinct. Only three
translation equations are used: no shared rotations, offset arm or hidden
joint is introduced. The native root and opposite shell edge are fixed.
Qualified Q4 mechanics and its physical +z normal authority remain unchanged.

The constructor checks the canonical registered master order and weights,
exact partition of unity and exact physical position reproduction. Rational
elimination retains constrained master rows as zero primal rows without
discarding their contributions to the full dual force map. The 42 external
coordinates reduce to 21 free coordinates. The native 24 internal coordinates
are condensed/back-substituted using its unchanged reference operator.

A fresh independent assembly retains 66 external/internal coordinates and 21
explicit multipliers, giving an 87-variable comparison. Displacements, internal
coordinates, multipliers, support reactions, physical force/moment balance,
energy and recovery agree at the frozen normalized 1e-11 tolerance. Each corner,
including the two constrained corners, receives one quarter of the opposite
tip tie force. Tests cover three independent force directions, weighted virtual
work and no artificial rotational equality. Rational tests verify affine-field
reproduction and J*T=0 without numerical tolerances.

Wrong, missing, duplicate or foreign masters; floating/equivalent-but-unregistered
weight encodings; nonregistered weight distributions; and off-centre placement
reject before element evaluation. Capture mutation, epoch/subscription changes,
cancellation, repeated RHS, shuffled insertion, normal authority and numerical
drill exclusion from physical recovery remain tested. This is a stateless,
reference-linear fixture, not a general weighted MPC owner or finite joint.
Restart and finite mixed programs remain deliberately unsupported.

## Checks and preservation

- Initial independent smoke: one passed in 1.72 seconds.
- Weighted development suite: 54 passed in 3.08 seconds; supervised duration
  3.6375782 seconds, peak tree memory 218050560 bytes, exit 0, zero children.
- Separate M_B2 regression: 25 passed in 2.51 seconds; supervised 3.2344325
  seconds, peak 234893312 bytes, exit 0, zero children.
- Separate M_B3 regression: 40 passed in 2.67 seconds; supervised 3.4336808
  seconds, peak 234983424 bytes, exit 0, zero children.
- Separate M_Q4 regression: 42 passed in 2.77 seconds; supervised 3.3332334
  seconds, peak 217952256 bytes, exit 0, zero children.
- Separate M_S3 regression: 45 passed in 2.58 seconds; supervised 3.1316707
  seconds, peak 220209152 bytes, exit 0, zero children.

All four preceding packets are byte-identical to the preserved M_S3 archive.
Their helper and mechanics-test bodies are unchanged; only their declared
successor extents expand. Weighted deterministic packets agree between fresh
problem constructions. This is not the formal two-fresh-process/cycle gate.
All six runs passed with no retries. Each had one numerical thread, 24 GiB/tree,
600-second wall and 120-second CPU/output inactivity limits. Raw logs/process
records and packets are archived with per-file hashes; originals are retained.

The nine-path extent contains the private weighted helper/test/status, bounded
runner and four prior tests' extent declarations only. No native/legacy beam or
Q4/S3 mechanics, production recovery, aliases, defaults, dependency/package/
workflow files, historical contracts or accepted qualification records change.
No independent implementation review, formal confirmation, merge or release.

## Next

The five basic reference-interface fixtures are now implemented, but G3b is not
qualified. Extend them through the frozen numbering/reversal/global-frame
transport cases, then complete the common S18 cache/transaction/restart owner,
independent review, freeze/rehearsal and formal confirmation. Do not mistake
successful rejection tests for G3c positive rotational-adapter qualification.
G4 histories and G5 public integration remain separate. Accepted G3a is intact.

# Generalized nonlinear force funnel: high-contrast failures preserved

Frozen corrected test: `0197a34b0bf4048f6ccbed469771a15309366413`.
No production mechanics, tolerance or accepted evidence was changed.

## Separate observed inventories

| Case | Tests | Outcome | Child seconds |
| --- | ---: | --- | ---: |
| Straight E, ratio100 smoke | 1 | Passed | 61.337 |
| Curved E, ratio100 | 1 | Passed | 66.551 |
| Straight E, ratio10,000 | 1 | Diverged; failed test | 12.436 |
| Straight E, ratio1,000,000 | 1 | Internal equilibrium iteration limit; failed test | 56.731 |

The moderate straight and curved free residuals are respectively
2.4251e-14 and 2.8653e-14; internal residuals are below 8e-17.
Recovery leaves accepted state unchanged. All are below the unchanged 1e-11
gate. The corrected smoke's inputs, last solver evaluation and result bytes
match the earlier harness-failed run exactly. The earlier test remains failed.

At ratio10,000 the solver returns `diverged`; its final accepted state remains
epoch zero. Its recorded events reach load parameter0.5, with two tangent
assemblies followed by seven residual-only trials. The exact solver failure
reason was not retained in the result packet; do not invent it. The last
operator observation is the virgin rollback replay, not the rejected iterate.

At ratio1,000,000 the internal equilibrium limit is explicit after245 observed
operator evaluations. The saved trial has transverse translations around
0.0023 and axial resultant magnitudes near9.9e5. These are diagnostic values,
not accepted physical results. Model and supplied virgin state are unchanged.
The fixed-nodal trial and nested reduction deserve investigation; these
observations alone do not prove a transcription defect or numerical root cause.

The remaining eight registered cases were not launched after failure. No
covariance, full twelve-case success or scientific aggregate is claimed.
Three diagnostic workers overlapped; each stayed within600seconds/24GiB.
All process trees are terminal and empty, guards passed, and no run was retried.

## Evidence

Archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-force-funnel-0197a34-20260908`.
The5,012-byte manifest hash is
`7AF4DAE6C13C8CDCD6A6CC289229F7B464153BFDAF308F2C1E659D5DA7115AF8`.
It binds every original-copy receipt, JUnit outcome, progress log, input,
result/failure, last evaluation, source test/plan and read-only audit.
Copies were verified byte-for-byte against originals; originals remain intact.
The audit independently parses stored records, but is not independent mechanics
review. Failed and partial outputs remain diagnostics, not canonical success.

## Next numerical successor

The existing fully retained elastic/plastic work demonstrates a viable
equilibrium/compatibility strategy, but its different material/load/state
contract cannot be used as proof for this generalized distributed path.
Prepare a small research successor retaining the same18 nodal DOFs plus the
same24 internal coordinates during Newton, using the existing generalized
potential, work and spatial couple Jacobian. Preserve all actual source
equations; do not tune coefficients or enlarge tolerances.

First verify full residual/Jacobian and load work against the native moderate
saved states, then solve the moderate cases and compare physical fields to
the existing accepted outputs. Only after that bounded smoke passes, revisit
the two preserved high-contrast failures under a new explicit freeze. Use
checkpointed equilibrium and compatibility separately; keep failed iterates
distinct from accepted rollback state. Any integration must retain global
trial/commit/discard, accepted origins, consistent Schur tangents where used,
physical recovery and authenticated restart. A research prototype is not a
replacement public controller or a claim of full beam parity.

The complete straight/curved/general-section/large-deformation/postbuckling
goal and objective beam-shell connection remain active. Full independent
review, nonlinear engineering references, section/fibre parity and installed
public integration are still required. Production qualification is false;
Q4/S3/B2/B3 and defaults remain unchanged.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

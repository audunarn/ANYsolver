# Multiple classical beam-plane Newmark — development result

Parent `6cb9a3040869bfc764c91b9ec69ac47ae4429364`, isolated reconciliation worktree.
Scope: [prospective slice](../C6_MULTIPLE_BEAM_PLANES_SLICE_20261002.md).
Implemented and installed-tested development; no scientific C6 acceptance/release.

## Changes and checks

Explicit `allow_multiple_beam_planes_dev=True` requires the classical beam flag.
Existing contributor sums supply work/tangents, named ownership and candidate caps.
Fixed planes, penalty, exact elastic B2/B3, no caps and surface-union coverage remain
explicit. Every endpoint and complete Hermite curve/time bound uses its pair's own
dimensional gap budget; subdivisions share one cap across pairs. Actual mass,
transactions, history, cutback, cancellation and restart schemas 1/2 remain shared.
Restart binds the new profile/flag and pair contracts; old absent flags stay absent.

Twelve new checks cover independent scalar Newmark trajectories/impulses for
coincident additive and orthogonal planes on B2/B3; individual forces/moment
balance; opening; active/history split restart and order invariance; changed
stiffness rejection; unequal path budgets; aggregate split exhaustion; explicit
opt-in/radial/duplicate rejection; second-pair failure/cancellation with no partial
commit; uncovered elements; public excessive-gap failure; and disjoint surfaces.
These independent toy references do not qualify general engineering impact.

## Executed evidence and retained failures

Source logs: `C:/ANYworkspaceWork/contact-multiple-beam-transient-20261002-vN.log`.

| Run | Terminal result | Disposition |
|---|---|---|
| v1 | 12 pass / 6 fail | Test defects: tuple concatenation in wrench assertion, wrong load keyword, sphere retaining plane normal. Existing 11 single-beam checks pass. |
| v2 | 9 pass / 1 fail | Mechanics/restart/path pass; radial fixture stops at required integration setting before intended transient guard. |
| v3 | 1 pass | Corrected radial fixture verifies plane-only transient rejection. |
| v4 | 1 pass / 1 fail | Public per-pair overpenetration rejection passes; disjoint fixture used nonexistent `source` field. |
| v5 | 1 pass | Corrected public `surface` field verifies independent disjoint-beam response. |

Portable source runs use JIT off, threads 1, 180 s/953 MiB caps and fresh outputs.
Failures are retained; no mechanical tolerances changed.

Installed package: `C:/ANYworkspaceWork/contact-multiple-beam-impact-package-20261002`.
Wheel SHA256 `88a6ea7490743086c354ad17d72d1272ba21025dfa7492b3d6d29e4703029162`.
451 source/wheel/site modules match; effective JIT/BLAS/Numba settings are checked.
All solver imports resolve to isolated installed site (210 first run, 202 corrective).

Installed first run: **77 pass / 3 fail**, 9.965 s, 181809152 B sampled tree peak.
Failures: missing copied static example and two literal parses of NumPy CLI scalar
output. The CLI now prints ordinary floats and the missing example is supplied.
Focused corrective run: **3 pass**, 5.257 s, 302673920 B peak. Wheel/source bytes
are unchanged between runs. Reuse the 77 unaffected passes by impact analysis:
**80 distinct checks covered**, not one clean 80-pass rerun. Four transient CLI
variants include B2/B3 orthogonal planes. Both runs meet 180 s/999292928 B caps.

## Independent scrutiny and limits

Mistral Read first stopped at its bounded turn limit, not a completed review.
A focused follow-up completed the unresolved per-pair gate, aggregate split and
restart questions, source-only, no edits/numerical runs. Its
[assessment](mistral-final-source-assessment.md) found no counterexample and records
unread tail/child-contract limits. Lead inspected child plane contracts (geometry,
radius, law/stiffness, gap, candidate controls); failure/restart tests execute the
shared tail. This supports development, not independent science acceptance.
Full logs, final candidate and installed identities are retained in `raw.zip`.

Toy .002 m gap budgets are not application defaults. Finite rotations, moving/free
tools, caps, radial/beam-beam/shell impact, friction, nonlinear materials,
temporal/enforcement qualification and full C6 remain open. Accepted static subsets
are unaffected; application admission remains false.

# M9: isolate response-reconstruction rounding

2026-10-09. Outcome: outstanding broad regression completed; no safe staged
stress-reconstruction candidate established. Keep the existing canonical stress
and envelope execution. No product code or tolerance changes.

## Checks and conclusion

The final authority-hardened M8 source passed 51 affected-path tests, resolving
the prior interrupted regression. The timed-out M8 attempt remains preserved.

The numerical discriminator used ten small cases: five aligned S3 shells, two
rotated S3 shells, and three free-free mixed Q4/beam cases. It used identical
actual full force vectors and sparse coefficient accumulation, contiguous
single-RHS direct solves, and verified native recovery stage controls.

- All physical displacement comparisons passed their existing tolerances.
- All recovery stage controls were bit-identical at the same displacement.
- All preparation columns were bit-identical with single and multiple RHS solves
  on these fixtures; preparation layout does not explain their discrepancies.
- Summing local displacement columns failed eight principal-stress entries on
  the rotated shell at the original same-displacement `1e-12/1e-12` criterion.
- Running native staged recovery on globally reconstructed displacements avoids
  that same-displacement shortcut error, but still differs from direct-solve
  output: 90 principal entries and three mixed-model von Mises entries exceed
  the corresponding field screen. Direct-displacement principal comparisons are
  diagnostic applications of the field tolerance, not a new universal bit gate.
- Beam strain-column sums also failed the conservative shear diagnostic; that
  diagnostic does not substitute for formulation-specific acceptance criteria.

The two errors are distinct: moving a response cache earlier in recovery does
not generally preserve finite-precision arithmetic, and displacement agreement
does not by itself certify cancellation-sensitive stress quantities. This does
not disprove linear response reconstruction in exact arithmetic or establish
that every possible numerical implementation fails.

Float64 and longdouble both have a 52-bit stored mantissa on this runtime; the
alternate accumulation branch supplied no higher-precision evidence. Fixtures
have zero prescribed offsets; no new offset qualification is claimed.

Root reviewed the diagnostic equations, load and RHS construction, stage controls,
criteria and ownership. Final review corrected a diagnostic counter that used
numerical inequality under a bit-difference label, overlooking signed zero.
The corrected binary64 counter found no preparation/stage-control payload
differences. Both the earlier and corrected evidence are preserved. A separate
root run reproduced the final ten-case JSON byte-for-byte, SHA256
`b655ae09a889e7e59d887f8516783dd5af63e2c3edaacbd27274c158ff320827`.
This corroborates the rounding counterexamples; it is not a separate mechanics
oracle or different-model-family assessment.

## Evidence and next decision

Diagnostic: `tests/prepared_static_response_m9_diagnostic.py`.
Detailed findings, criteria and source hashes:
`.prepared-static-evidence/m9-solver-handoff.md`. Raw JSON and all provisional
versions remain in that evidence directory. Exact commands, environment,
source hashes and logs remain under the task root's `evidence/checks/m9-*`.
The diagnostic exits successfully when its reference controls agree; that exit
does not mean the rejected stress shortcut passed.

Root checks used 39.2941374 / 120 process-wall seconds; worker checks used
23.9242539 / 120. No benchmarks ran. M8 remains at 540.0326434 / 600 seconds.
No commit, merge, push or 10,000-case claim.

Further stress-response activation needs a concrete new numerical candidate or
reviewed conservative output-error bounds that permit canonical contender
exclusion, with direct replay whenever the bound is inconclusive. Repeating the
barge benchmark or weakening the existing criteria will not resolve this issue.

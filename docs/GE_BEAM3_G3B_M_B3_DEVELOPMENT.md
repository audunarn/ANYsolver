# G3b M_B3 reference-linear development checkpoint

Status: **DEVELOPMENT_SMOKE_PASSED_NOT_G3B_QUALIFICATION**.
Parent: M_B2 `5da2a9c6efad7feb6a573196f3791b7872717bbe`,
tree `63907df9bbe3938ed713232713944c9ab7243e65`.

## Scope and implementation

The unchanged frozen M_B3 fixture couples one private native `ElasticElement`
to one exact legacy `QuadraticBeamElement`. All six node IDs are disjoint;
the two coincident tip nodes have three unit translation ties and independent
rotations. Both families use their existing reference-linear operators.
This is a stateless, private development problem, not a general static solver,
transaction owner, restart implementation, public selector or qualification.

`B3TranslationReferenceProblem` shares only graph assembly/elimination logic
with M_B2. It captures 36 external coordinates, eliminates 12 support and three
tie rows to 21 free coordinates, and back-substitutes the native 24 internal
coordinates. Independent test assembly retains those internal coordinates
and uses explicit multipliers: a 75-variable full system. Displacements,
internal coordinates, multipliers, energy, work, reactions, force/moment balance,
and both families' recovery agree at the frozen normalized 1e-11 tolerance.

Legacy B3 recovery retains the unchanged scalar-family semantics; no native
station recovery is substituted into it. Legacy residual contribution is K*u,
not the legacy zero-force placeholder. Native recovery is explicitly labeled
reference-linear and does not claim finite-frame recovery.

Exact types, policy, straight exact midpoint, zero B3 eccentricity, scalar
elastic section, coincident traces and translation-only ties are validated.
Non-midpoint, curved, offset, generalized-section, subclass, wrong-family,
finite mixed and rotational-coupling programs reject. Capture mutation tests
cover material, geometry, connectivity, operators, nullspace, constraint rows,
loads and activity. Cancellation and successive right-hand sides are stateless;
checkpoint creation remains deliberately unsupported.

## Development checks

- Initial independent 75-variable smoke: one passed in 2.15 seconds.
- M_B3 development suite: 40 passed in 2.56 seconds; supervised duration
  3.3391594 seconds, peak tree memory 231911424 bytes, exit 0, no active children.
- Separate M_B2 regression: 25 passed in 2.39 seconds; supervised duration
  3.1326666 seconds, peak tree memory 231997440 bytes, exit 0, no active children.
- The M_B2 packet is byte-identical to the preserved prior 4465-byte packet,
  SHA-256 `f8b5caa5fa48931ca66688c7bdf36a362886bb5e0ed657af071ca35d8357623b`.
- Two independent problem constructions produce identical M_B3 packets within
  the development test. This is not the formal two-fresh-process-cycle gate.
- M_B2 mechanics tests are unchanged; only their allowed successor path set
  expands. The exact six-path successor extent and frozen G3 source bindings
  are tested. No legacy/native element operator, Q4/S3 mechanics, old evidence,
  default, public API, dependency, package metadata or workflow changes.

All three supervised attempts passed. Limits remain one numerical-library
thread, 24 GiB per tree, 600 seconds wall time, and 120 seconds without CPU/output
progress; no automatic retry. Raw logs, process records and development packets
are archived externally with byte counts and hashes in the companion record.
Original temporary outputs remain preserved. Git emitted only existing
configuration-permission and line-ending warnings; boundary checks completed.

## Remaining gate and next step

Add the frozen M_Q4 and M_S3 reference-linear interfaces with physical normal
authority, then M_Q4_WEIGHTED with exact rational weights and interface work.
After those development slices, finish the full G3b S18 cache/transaction/restart
owner, numbering/reversal/global transport, negative admission coverage, and
independent implementation review before freezing formal confirmation.

G3c shared-rotation adapters, G4 histories and G5 public integration remain
separate. Accepted G3a evidence is untouched; no merge, release or activation.

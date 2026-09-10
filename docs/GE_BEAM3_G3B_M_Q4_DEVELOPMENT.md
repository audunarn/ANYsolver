# G3b M_Q4 reference-linear development checkpoint

Status: **DEVELOPMENT_SMOKE_PASSED_NOT_G3B_QUALIFICATION**.
Parent: M_B3 `d1a564857b2b74f8b0d53c4028040a31652b9caa`,
tree `bdc486adfb1cf0591618b9006d293e58fb86b82d`.

## Implemented scope

`Q4TranslationReferenceProblem` implements only the frozen M_Q4 square fixture.
One private native `ElasticElement` and one exact `QualifiedE4PLShellElement`
retain seven distinct node IDs, including coincident but unmerged tip nodes.
Only three translation equations couple the families. The shell's physical
owner normal is explicitly +z; rotations remain independent. The native root
and opposite shell edge are independently supported.

Both sides use their unchanged reference-linear operators. There are 42 external
coordinates, 18 support rows, three tie rows and 21 free coordinates. The native
42-coordinate stationary operator contributes 24 internal coordinates, which
are Schur-condensed and back-substituted. The independent test constructs fresh
elements and assembles 66 external/internal coordinates plus 21 multipliers:
an 87-variable full system. It does not use the candidate assembler or caches.

Displacements, multipliers, internal coordinates, energy, reactions, net force
and moment balance, interface work and recovery agree at the unchanged normalized
1e-11 tolerance. Native recovery remains native and reference-linear. Qualified
Q4 physical recovery, including global resultants and authoritative director,
uses the unchanged Q4 method. Adding arbitrary shell drill coordinates to the
recovery input leaves physical fields unchanged. Total equilibrium/energy still
includes numerical stiffness; it is not presented as physical section energy.

The helper is stateless. It admits no finite mixed program, nonlinear cache,
material history, rotational adapter or restart envelope. It captures the mesh's
issued mutation token and epoch; foreign subscriptions and epoch changes reject.
This narrow cache binding is not complete G3b S18 transaction/restart authority.
General geometry, numbering/reversal/global transforms remain later coverage.

## Verification and preserved incidents

- Initial independent smoke: one passed in 1.73 seconds.
- Final M_Q4 development suite: 42 passed in 2.89 seconds; supervised duration
  3.4343757 seconds, peak tree memory 222031872 bytes, exit 0, zero children.
- Separate M_B2 regression: 25 passed in 2.62 seconds; supervised duration
  3.3321802 seconds, peak tree memory 238055424 bytes, exit 0, zero children.
- Separate M_B3 regression: 40 passed in 2.80 seconds; supervised duration
  3.5356410 seconds, peak tree memory 239296512 bytes, exit 0, zero children.
- Both beam development packets are byte-identical to their preserved M_B3
  checkpoint archive. Their mechanics tests and shared beam helper are unchanged;
  only the tests' allowed successor path sets expand.
- Two fresh M_Q4 problem constructions produce identical canonical development
  packets. This is not formal two-process/two-cycle qualification.

Two failed intermediate suites are retained without reclassification (20 passed,
20 failed in each). The added integration guard first mistook an ordinary mesh
mutation token for nonlinear state, then required an exact list instead of the
existing `_QualifiedMutationEpoch` type. The correction captures the actual
issued token, verifies its identity/value and single-owner subscription, and
continues to reject nonlinear caches. Added foreign-subscription and epoch
mutation regressions pass. No Q4 mechanics or historical evidence was changed.

All runs use fresh external directories, one numerical-library thread, 24 GiB
per tree, 600 seconds wall and 120-second CPU/output inactivity bounds. No
automatic retry. All runs terminated with zero active children. Raw outputs,
including both failures, are archived with per-file byte counts and SHA-256.
Original temporary outputs remain preserved. Git configuration-permission and
line-ending warnings did not prevent boundary validation.

The seven-path extent is limited to this private helper/test/status, the bounded
development runner, and prior tests' extent declarations. No public API, selector,
default, native/legacy beam or Q4/S3 mechanics, production recovery, dependency,
package metadata, workflow, old contract or qualification evidence is changed.
No independent implementation review, merge, release or activation is claimed.

## Next

Implement frozen M_S3 with the explicit accepted V2D class and physical-normal
authority, then M_Q4_WEIGHTED with exact rational weights and interface work.
Finish numbering/reversal/global transport and complete G3b S18 state ownership,
cache/restart/replay before independent review and frozen formal confirmation.
G3c shared rotations, G4 history-bearing sections and G5 public integration are
separate gates. Accepted G3a remains untouched.

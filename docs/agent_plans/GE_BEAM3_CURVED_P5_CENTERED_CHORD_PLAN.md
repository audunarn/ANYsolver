# P5 centered-chord numerical evaluation development

Parent `b7aeb2f4d7ad50c48100555e302df2510a737848`, tree
`0c404a85730b376e6b994ef9b585682a592eaa9b`.
Six-path scope: the research mixed evaluator, force-accurate assembly and
displacement controller; new centered-chord module and tests; this plan.
No production source, coefficient, section law, quadrature, physical
tolerance, reference case, default, version or publication change.

## Exactly equivalent potential evaluation

The preserved force-accuracy32 attempt remained FAILED. Its saved scalar
inputs show cancellation in the direct chord strain `z = U^T d - d0`.
Use the exact identity

`z = (U^T-I)d0 + U^T(d-d0)`

in an explicitly selected CenteredChordMixedProbe. Every term remains a
Jet2 expression, including both first and second variations. No finite
differencing, derivative replacement, residual correction, clipping, added
stiffness or empirical stabilization is introduced. The expression is
identical in exact arithmetic for arbitrary U, not only near-identity or
orthogonal matrices. Its floating-point advantage is data-dependent, not a
global error bound.

The original direct expression moves into a helper without changing its
arithmetic sequence. NonlinearMixedBeamProbe still uses it by default.
Both old and new paths share all remaining mixed potential, moment and
cell-rotation stationary solves, section states and Schur condensation.

CenteredChordAssemblyHistoryProbe explicitly selects the centered local
evaluator and a distinct evidence schema:
`GE_BEAM3_P5_ASSEMBLY_CENTERED_CHORD_FORCE_ACCURACY_V1`.
It retains the frozen 1e-12 total estimated-force-error budget, allocated
equally across elements, the original diameter scaling and force scale one.
It retains all local/global iteration and evaluation limits. No assembly
factory default changes; the displacement controller adds only explicit
recognition of the new exact class.

Assembly trial and accepted replay use the same selected local evaluator.
The new schema is bound into per-element response digests. Mixing an old
and new profile is rejected during reconstruction rather than silently
reinterpreting a checkpoint. This is an in-memory research transaction
boundary, not a newly qualified serialized production restart codec.

## Validation extent

- Apply the actual Jet2 helper to all 192 frozen scalar chord components;
  compare values against exact Fraction interpretations of their binary64
  inputs and verify identical chord-variable gradients/Hessians. This is
  a small scalar audit, not 32-element mechanics or equilibrium execution.
- Compare complete mixed potential/residual/Hessian against the direct
  expression on straight/curved, coupled elastic/plastic and line-load
  cases at nonzero mixed increments. Use the unchanged 1e-11 invariant
  tolerance and independent directional tolerance 1e-7.
- Check condensed energy/residual/tangent directional agreement, large
  common rigid rotations, reference re-expression, connectivity reversal,
  station origins and physical resultant transforms.
- Check two-element plastic loading/unloading, deterministic response,
  commit/replay, displacement control, schema mixing and budget failure.
- Retain historical default raw-byte fixtures and source-identity checks.

The short rigid-motion test originally applied an unscaled norm across
force, moment and moment-dual rotation-gap equations. Correct its units to
the requested normalized invariant check: characteristic force EA=1000,
reference length 2*scale, moments divided by force*length, and dimensionless
rotation gaps separately. No assembled-equilibrium acceptance changes.

Also preserve the absolute force diagnostic rather than conceal it: for
scale 1/32, common rotation [1.8,-1.7,2.1] and translation [2,-3,4], the
direct/centered residual norms are respectively about 1.37226e-11 and
1.36909e-11. Both exceed the assembly's absolute unloaded threshold even
though their normalized invariant errors are about 1.37e-14. This is not
accepted global equilibrium or proof of exact rigid input representability.
It remains a numerical-resolution consideration for broader qualification.

## Boundaries and next step

No 32-element solver is run here; no consumed request is reused. Prior raw
failure, observation, force-accuracy and administrator records remain
immutable. The administrator now permits the requested communication, and
the two previous diagnostic executions are closed as capture successes
with solver acceptance FAILED. No communication blocker remains.

After this development passes its small tests and receives a clean freeze,
prepare a separately authorized two-target comparison with fresh output,
retained uncommitted failure snapshots, one numerical thread, 24-GiB tree
memory, 600-second child and 890-second coordinator safeguards. Respect the
global resource queue; do not run alongside ANYmesher or another heavy lane.
Neither a scalar rounding improvement nor a passing comparison qualifies
the beam or closes the remaining spatial/material/mass/dynamics/restart,
independent-review, packaging or objective beam-shell joint requirements.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

## Development result

The complete selected 14-file small regression passed: 211 tests in 44.64
seconds. This includes the 16 new centered-chord tests and the preserved
default-path, force-accuracy, failure-snapshot, authority, state and control
tests. No resource-heavy solver, 32-element comparison or qualification
campaign was launched as part of this test run. `git diff --check` passed.

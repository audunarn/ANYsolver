# Active-plastic arc: first curved cantilever smoke

Base: fine-onset closeout dee92a86a588b0bfe3bd1fb3eb203787fbef45d4.
This is a research-only smoke, not full arc/state or beam qualification.
Existing beam/shell mechanics, state laws, tolerances and defaults are unchanged.
The previous onset rehearsal and two formal cycles remain final and immutable.

## Frozen fixture and checks

Fixture ID GE_BEAM3_ACTIVE_PLASTIC_ARC_SMOKE_V1. The standard-library fixture
module is the exact numerical data authority. One curved quadratic macrocell,
nodes x=0,1,2 and y=.2(1-(x-1)^2), with reference second director +z and
right-handed tangent triads. Node1 is clamped in all six physical DOFs.
The end-node spatial dead force pattern is (1,.2,.1); no nodal couple or
distributed load is substituted. Arc steps are exactly (.05,.05,.05), length
scale2, parameter scale1, initial sign+1, max24 Newton iterations/8 backtracks.

The existing six-resultant ellipsoid section uses C=A^T diag(4,6,8,2,3,5) A
and M=B^T diag(1,.25,.5,2,.75,1.5) B. A/B are identity plus the explicitly
listed fixture entries inherited from the coupled generalized-section tests.
Yield force .025 and hardening .6 are fixed. Four stations per subcell,
eight per macrocell. No tuning of these values after observing this smoke.

Every one of the three accepted increments must contain a strictly positive
plastic increment. Every station is audited, whether elastic or plastic.
An all-elastic increment does not satisfy this smoke. Require actual native
physical residual, arc gap and full Newton correction <=1e-11. The native owner
must reproduce its entire accepted chain, original increment histories and
recovery without changing them. Prefixes for capture are generated only by
that owner's checkpoint API from its issued records, never manually resealed.

The independent checker imports only standard-library modules and the existing
independent 96-digit primal KKT return map. It does not import ANYsolver,
NumPy, SciPy, producer mechanics or cached matrices. It checks actual station
resultants, plastic variables, accumulated history, nonnegative increment and
dissipation, incremental/stored/dual energies, and constitutive tangent from
the ORIGINAL increment origin. Raw high/low pairs are retained. math.fsum gives
the explicitly rounded binary64 comparison inputs; normalized Euclidean error
is ||actual-expected||/max(1,||expected||), at most1e-11. Tangent samples use
the rounded station resultant and must also reproduce its strain/resultant
within this same bound. This is not claimed to be an exact paired tangent or
an independent whole-beam tangent proof. Yield-boundary ambiguity blocks.

## Execution and disposition

Freeze the exact five-path implementation after the analytic/mutation tests.
One fresh external smoke root: unit inventory, full three-step native solve,
owned capture/replay, independent material check. Those three scientific stages
run serially in fresh child processes, after source/input authority checks.
Each child: one numerical-library thread, 24GiB tree, 600seconds; whole wave
1800seconds; existing native120second context and120second CPU-inactivity
guards unchanged. Exclusive output creation; preserve stdout/stderr, actual
partial checkpoints and receipts. No automatic retry and no consumed root reuse.
No canonical aggregate unless all workers are terminal and successful.

An actual solve/capture/check failure blocks this smoke, preserving the reason;
no success evidence is fabricated. A fully checked result is
PRIVATE_ACTIVE_PLASTIC_ARC_MATERIAL_SMOKE_PASS, production_qualified=false,
restart_cancellation_qualified=false, independent_review=PENDING.
The fixture generator also describes two connected macrocells for the next
distinct case, but this runner authorizes only the one-macro smoke. Do not
launch connected/rehearsal/formal cycles from this smoke authority alone.

## Next gates and full scope

After successful smoke, extend exact same-programme uninterrupted/prefix-resume
comparison and cancellation AFTER a plastic accepted state (before assembly,
trial and commit), including resealed-origin/history/predictor mutation tests.
Then freeze the connected case and a full rehearsal before deterministic
formal cycles. Deliberate mid-history arc reversal requires a separate immutable
programme policy; current positive steps plus initial sign do not imply it.

Spatial postbuckled branches, full material/fibre/load/mass/recovery/state/
solver/restart/linear-transient parity, current retained-curved public18DOF
integration, full environment attestation, independent review, installed
explicit selection and objective eccentric/curved beam-shell connections
remain required. Earlier straight public routing does not expose this core.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED. No change to main, B2/B3/S3/Q4,
defaults, versions, tags or publication.

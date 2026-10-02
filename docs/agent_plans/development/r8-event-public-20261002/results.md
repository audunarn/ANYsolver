# Public generalized branch-event displacement policy — 2 October 2026

Implementation/test status: IMPLEMENTED_NOT_QUALIFIED. Based on solver47fb532a
and ANYfem51e5298; source identities are bound by the wheel module hashes and
subsequent local commits. No defaults, constitutive equations, physical tolerances,
Newton/backtrack budgets, versions or release criteria changed.

Explicit `DisplacementControl.trial_policy=GENERALIZED_BRANCH_EVENT_TRIAL` now
binds from the first displacement step after a force seed. V3 snapshots and
ANYSSDCA2 adaptive envelopes retain identity even with zero event work. Existing
default V1/V2/ANYSSDCA1 formats remain intact. Policy changes within displacement
history are rejected. Rebase retains counts; adaptive failed work stays separate
from accepted cumulative work. Strict suffix accounting and atomic publication
preserve accepted prefixes. The method estimates generalized-beam events only;
it does not locate shell-J2 events or guarantee exact branch crossings.

## Executed evidence

- Source:25checks passed244.96s, supervised245.82s, peak191250432bytes.
- Installed solver:34checks passed256.74s; supervised258.67s,
  peak190263296bytes. Additional strict V3 corrupt-metadata check passed1.52s,
  supervised2.35s. Total35installed checks.
- Solver wheel SHA256
  `e6d032b2f59a3fcefd9ddc1356a0e940573987c2ef008b5ff31a3daaa8e69d0a`;
 405source/wheel/site modules identical,241onsite imports,1thread/JIT off.
- ANYfem:2installed complete consumer workflows passed80.33s;
  supervised82.47s,peak188682240bytes. Default and event policies exercise
  cancellation, chart rebase and exact checkpoint continuation.
- ANYfem wheel SHA256
  `16e3d8634ecc0cdbc78c449066db448eddf312ead0f3119d45e9622ade57e754`;
 98source/wheel/site modules identical against the solver artifact above.

The public event policy starts from the original force seed, accepts -66um and
then -68um, and repeats the latter step byte-exactly after restore. Final load
-487.0911366314456N, amplitude0.1738327444125176, equilibrium1.5137507375456974e-11,
gap1.2234587071611457e-17. Event-only work44cell responses across the two accepted
steps (22each). No -70/-72um extension, -500N completion or capacity claim.

Initial installed collection failed due to one missing copied reference fixture;
no numerical tests ran. Repaired fixtures used the same wheel. Failed output and
original artifact/runner are preserved. This was a packaging-of-tests defect,
not a mechanics result. The later metadata supplement changed tests only.

Independent code review found a nonzero work-baseline loophole when adaptive
history starts at zero. Fixed with a strict rejection and direct counterexample;
reviewer confirmed closure. No remaining implementation finding in reviewed
scope. Adaptive implementation and independent review had different owners.
OpenAI review is not cross-family scientific acceptance.

Archive `installed-public-v1.zip`, SHA256
`ce385791af4261f7dd1b3624448601b4934d1eea1d316e455d04d76a99c015f5`.
Contains runners, exact fixture/seed inputs, artifact/import identities, outputs,
failed collection, safe execution metadata, review and prior active-note bytes.
Inherited environment maps are excluded. No performance saving is claimed.

## Remaining boundary

This closes the public integration slice, not any aggregate scientific gate.
Full signed reversal/material history, connection/F03, spectra/capacity, practical
scale, external references, platform and complete consumer/release acceptance
remain open. Further physical targets need a bounded decision-oriented slice;
do not automatically resume the old refinement or larger-backtrack campaigns.

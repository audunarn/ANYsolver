# B2 rigid-footprint numerical admission repair — 1 October 2026

The original40-Q4/3-member-node free-stub fixture now completes Fz10N, Mx1Nm
and My1Nm without tuning geometry, section or load. One eligible factorization
serves the three backend solves. The historical point-only route is unchanged.
This is implemented and development-tested; mechanical qualification remains open.

## Change and reason

The original global force contribution bound exceeded the explicit-load cap,
although exact Fraction evaluation found2.7970507403e-12N on the loaded row
against1e-8N. A narrow active-row certificate now encloses stored binary64 KKT
residuals with exact products/sums and outward rounding. Only footprint models,
zero prescribed offsets and pure positive unit selectors can use public fallback.
Original physical equilibrium, finite state, recovery and backend status checks
remain. Sparse immutable KKT preparation is lazy, reused and cleared on close.

The next predicate rejected41 quiet compatibility components, max2.97e-18,
with no failing physical equilibrium row. One same-factor correction failed and
was removed. These were true stored-solution gaps, not merely dot rounding.
The owner had required1e-9 relative accuracy in nearly zero row components;
retained F10/F11 science instead uses a reference-geometry gap criterion.

A separately declared footprint admission rule maps translation/rotation
amplitudes through actual C coefficients, including lever arms. Every footprint
row also has an independent1e-9 reference length/rotation cap. Length is twice
maximum reference-node radius about their centroid, frozen during the owner
lifetime. Nonfinite allowances fail before applying the cap. This is not a
forward-error theorem or the historical F10/F11 registration. Point rows retain
their original gap predicate; point-only load admission is unchanged.

## Executed checks and artifact

- Final source136/136 passes; installed176/176 passes, zero skips/errors/failures.
- Installed solver modal/static example and unchanged ANYfem Project save/reopen
  example complete.391 solver/98 consumer module bytes match source/wheel/site.
- Solver wheel SHA256: d99c59ac0464613b15461dcd23c0b8fe158a67fe3b27192a886b6daf6aa981ea.
- Reused consumer wheel SHA256:11728ab84a2c2b290d37651c455d9f6b7d63110e4804cb9263686c37511fa56e.
- Tests cover rational residual oracles, tiny-force/couple suppression, gaps,
  unsupported affine/offsets, nonfinite allowances, units/frames, source ownership,
  sparse cache cleanup and exactly three solves/one factorization.
- Separate OpenAI Read review has no remaining development blocker. Optional
  local/Mistral availability remains unchanged; no different-family pass claimed.

Initial installed collection failed because two fixture helpers were omitted;
the failure remains. After copying unchanged helpers, the same wheel passes.
Initial consumer harness used an invalid filename suffix; that fail-closed error
and runner are retained. Corrected suffix gives successful Project roundtrip.
Prior source numerical failures, source-v1/v2 and public captures are retained;
portable source checks had no complete raw pytest stdout before source-final.log.
No failure was relabelled a pass or erased.

## Matched reference consequence

New installed B2 completes the existing10x4/20x8/40x16 grids and all three loads.
No external run or new refinement was launched.24 saved input hashes were bound;
geometry, nodes/cells, patch and loads match retained GE/external comparisons.
Maximum B2/GE work difference6.8211e-11 relative. Finest B2/external work:
Fz+.1477647%, Mx-.6203361%, My+.1196629%. Torque lastmeshchange+1.3583242%.
Serial native routes1.71/2.44/5.79s; sampled peak146/167/260MB. These are single
supervised development runs, not paired performance evidence or a speedup claim.
Effective numerical pools/Numba1, JIT off,600s/1GiB route limits, no limit hit.

Retain the restricted out-of-plane candidate and stop this batch. No fourthmesh.
Solid thickness convergence and seven-digit external1e-8 balance precision remain
open. Positive eccentricity/pure loads do not prove signed eccentric coupling,
normal-spin/in-plane/full-law or finite GE equivalence. Shared shell code limits
GE comparison independence. E02/F04/F03/aggregate gates remain open.

Raw sources, arrays, failures, wheels, actual imports, XML/logs, resource records,
comparison inputs and reviews are in raw-v1.zip with identities in raw-v1.json.

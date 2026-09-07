# Twelve-macro loaded-state refinement checkpoint

Frozen source `0ec814beac4369c16bc70368fcdbd90bf3b6e951` completed one
two-state diagnostic in 111.424 seconds, exit 0, on 2026-09-07. No workers
remain. No nonlinear history or continuum equilibrium solve was rerun.
Accepted twelve-macro states and all continuum reference inputs remain
byte-identical. The full hash DAG and reports are bound by the execution status.

The canonical result is 3,538 bytes, SHA-256
`cf8ef1e5309fdcec5a203aa6451f6ebca59ae9541f5a11b697b5073d161501b1`.

## Observations, not a qualification terminal

At crown drop .01, maximum sorted-root relative eigenvalue error decreased
from 6.72 percent at six macros to 1.6745 percent at twelve macros. At .055,
it decreased from 8.28 percent to 1.9090 percent. All six individual errors
decreased at each state. Both native and continuum spectra have zero negative
roots at .01 and two at .055. Negative roots remain signed; they are not
reported as real vibration frequencies.

Native loads are 120.293102 and 236.749248 versus continuum 119.986444 and
234.444474. Native signed-Ritz residuals remain below 3e-16. These two sampled
states are below two percent eigenvalue error, but neither identical equilibrium
branches, general modal accuracy, a critical buckling factor, nor full nonlinear
postbuckling qualification is thereby established.

The selected private bounds are 256 spectral coordinates, 160 exact-sign
coordinates and the existing 512 retained-state replay budget. Actual counts
are 222, 141 and 438. Defaults remain 80/64/256. Both native spectral calls
finished inside the unchanged 120-second constructor bound. The process retained
one thread, 24 GiB, 600 seconds wall time and 120 seconds inactivity; exact-sign
calls retain their total 30-second bound. No retry or limit extension occurred.

## Verification

Separate inventories: 76 preparation/allocation/wiring tests passed; 13
saved-evidence inspection tests passed. Inspection recomputed the original
factor-chain signed Ritz identities, physical modal-mass normalization, zero
inertia of algebraic traces, frozen-plastic-coordinate policy, complete hash
DAG, refinement observations and evidence mutations. It did not rerun spectra.
Independent scientific and code review remain pending.

## Next programme work

This is sufficient development evidence to move beyond repeated coarse-mesh
accuracy checks, not to declare the beam qualified. Next establish buckling
onset and mode-shape/branch behavior using the preserved path and independent
reference; finish general nonlinear section and production solver/state/restart
integration. Qualification must cover wider straight/curved members, rings,
curved stiffeners, slenderness, loads, mass/modal/buckling behavior, packaging
and independent review. The objective finite-rotation eccentric/curved
beam-shell connection remains a separate required part of the full goal.

Existing B2/B3, Q4/S3, public aliases, defaults, package metadata, scientific
tolerances and historical qualification evidence are unchanged. Full GE-B3
qualification remains incomplete, and no activation or publication is claimed.

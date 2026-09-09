# Six-macro loaded-state refinement checkpoint

The single invocation frozen at `b66ce8d825708014c352449dd009af23a6f6b1f0`
completed in 144.401 seconds, exit 0, on 2026-09-07. It reused the exact saved
six-macro nonlinear history and existing continuum references; no nonlinear
or reference equilibrium solve ran. Both native spectra finished within the
unchanged 120-second constructor limit. The supervisor retained its one-thread,
24-GiB, 600-second wall and 120-second inactivity bounds. No workers remain.

The canonical result is 3,490 bytes, SHA-256
`93b6507bce49e3e1022fc7792f2c9018af89bf55681ed485cc328972ed8e79bc`.
Every historical input remains byte-identical. Its complete source, input,
output, transcript and test-report graph is bound by the execution status.

## Refinement observation

At crown drop .01, the worst six-root relative eigenvalue error decreases
from 15.05 percent (four macros) to 6.72 percent (six macros). At .055 it
decreases from 21.24 percent to 8.28 percent. Every individual sorted-root
error decreases. Both native and continuum operators have zero negative
roots at .01 and two at .055. Negative roots remain signed, not frequencies.
Native signed-Ritz residuals stay below 5e-16.

The native six-macro loads are 121.169968 and 243.657491 versus continuum
119.986444 and 234.444474. Thus identical equilibrium branches and modal
accuracy are still unproved. No buckling-factor or full qualification claim
follows from this bounded refinement result.

## Verification and preserved failures

Separate inventories: 48 allocation/arithmetic tests passed; corrected
runner wiring/containment 13 passed; saved-factor/evidence inspection 12 passed.
The first unfrozen wiring suite (11 passed, 2 failed) is preserved; it caught
use of the plain-JSON serializer on native dataclass packets. The corrected
harness uses the unchanged existing native canonical serializer.

Saved-factor inspection recomputed signed Ritz identities using the original
factor chain and physical mass normalization without an eigensolve. It also
checked frozen-plastic-coordinate policy, exact zero inertia of algebraic
traces, state non-advancement, complete input hashes and mutations. These are
development checks by the same author, not independent scientific review.

## Next safe work

The next mesh uses twelve macros and needs more spectral coordinates than
this explicit 128/96 allocation admits. Do not silently raise caps or relax
deadlines. First reduce repeated exact-sign/search cost with arithmetic-only
tests and preserved-packet comparisons; then freeze a separately bounded
twelve-macro diagnostic using its already saved nonlinear state chain.

Continue toward the full objective: mesh-converged straight/curved modal and
stability behavior, wide slenderness, general nonlinear section/state parity,
buckling/postbuckling, independent review, public opt-in packaging, and the
objective eccentric/curved beam-shell connection. Q4/S3, B2/B3, public aliases,
defaults and historical qualification evidence remain unchanged.

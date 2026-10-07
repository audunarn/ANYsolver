# E03 coarse development screen — 7 October 2026

Candidate `c6cc3dba380ba765a6aa2c463b52713b6d5d1c74`, unchanged product
`535390ef9e876a412b633942b4b410b2d998d100`. Fixed level 0, positive offset,
physical B2 reference-linear point profile. This is development evidence, not
E03 acceptance, converged accuracy, or a qualified curved GE connection.

| Attempt | Result | Precise process-wall seconds |
|---|---|---:|
| Nonphysical runner controls | 33 passed; no failures/errors/skips | 9.1335864 |
| Installed native physical route | Completed | 7.9998143 |
| Native finalization | Provisional coarse phase completed | 6.7691626 |
| Pinned CalculiX 2.23 physical route | Process completed, exit 0 | 5.9957742 |
| External finalization | Rejected: force/moment balance | 6.3596042 |
| Saved-output observability probe | Same strict rejection retained | 9.4358204 |

All six child processes exited. Twelve saved before/after runtime records were
independently checked: CPU 0, one numerical thread, JIT disabled. Maximum sampled
process-tree RSS was 197,173,248 bytes, below the 2 GiB limit. Sampling is not a
continuous proof of the maximum. The original external supervisor records
actual executable identity, inherited settings, CPU declarations and affinity.

The installed native route has normalized balance `1.7275070263167436e-13`.
The external ROOT forces plus the applied force instead give
`[0.1646734516180175, 5.202695912975841e-11, 3.990588429916812]` N.
The common-origin moment imbalance is
`[-1.545249345147326e-10, 1.015131210629057, -4.7638157307794415e-11]` Nm.
The unchanged normalized limit is `1e-8`; the measured value is
`3.990588429916812`. No displacement/work accuracy comparison is accepted.

The strict parser reached this failure after validating the declared node and
output inventories, completed step, fitted-port compatibility and execution
bindings. The saved-output probe instrumented observation only, then called the
original parser unchanged. Both failures, original outputs and receipts remain.

## Decision and next discriminator

Do not refine, retry, change tolerances, or reject the connection formulation
from this result. The deck has no loads on ROOT, but attachment equations use
some supported shell nodes as independent terms. Complete equation actions
are self-equilibrated; their supported subset need not be.

The [CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf), sections 6.11.5
and 7.97, defines RF as nodal external force (reaction plus concentrated and
distributed loads). That definition alone does not establish the redistribution
of equation actions at supported independent nodes. Supporting author-source
review suggests this distinction matters; its release identity must be verified
before treating it as evidence for the pinned executable.

The present FRD contains FORC only at the 49 ROOT nodes. It cannot determine the
48 equation-side forces. A force inventory sufficient to reconstruct or verify
equation reactions, with a derivation and independent sign/work controls, is the
next useful discriminator. Do not fit missing forces to the observed deficit,
borrow native reactions, or infer equilibrium from process exit status. A new
physical execution needs new explicit authority; both approved primaries are
consumed. Saved-output investigation and compatible tooling repair remain within
the unused verification allowance.

Raw evidence: `.qualification/b3-ge-e4-pl/r8-e03-coarse-dev-20261007-v1/`.
`root-result-v1.json` binds receipts and measured accounting;
`saved-balance-v1/saved-balance.json` binds the failed FRD hash.
Used `45.6937621` of 240 seconds; remaining `194.3062379` seconds, reserve 60.
No additional primary, refinement, F03, body retry, sibling edit, main delivery
or release is authorized by that remainder. Full programme and E03 remain OPEN.

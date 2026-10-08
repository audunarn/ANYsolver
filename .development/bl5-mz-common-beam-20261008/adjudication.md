# Mz common-density beam-body attempt — failed development gate

This is a distinct +1 N m Mz **beam-only** development calculation using the
resolved-continuum five-channel P0 density. It is not the historical failed
Fz shell/body retry. No formal F03, external executable, native shell body or
new multiplier space was run. Four unique attempts consumed
11.69439049999346 s cumulative process wall of a 90 s allowance; all stderr,
preflight, calculated fields and exact source hashes are preserved. The final
attempt stayed under the 60 s/2 GiB cap with CPU0, one loaded numerical thread
and JIT disabled. The [cumulative ledger](cumulative-ledger-v1.json) supersedes
any per-attempt remaining-time arithmetic.

V1 recovered the physically sign-aligned reference density and passed the
common six-mode beam-wrench preflight. The native beam calculation reached
work 1.74538504099354e-6 J, but **FAILED** its unchanged active-row
equilibrium criterion: slot 2 carried -4.27e-13 load and -1.39e-12 residual,
ratio 3.253606. That calculated work is not a validated comparison.

V2 stopped before a body solve because the reflection search found coincident
shell and beam nodes at the same position. The correction searches within
the physical subdomain; no topology or mechanical equation changed.

V3 established the *actual discrete* y-reflection of the continuum model:
relative K equivariance defect 4.36e-16, exact five-row C and load parity,
reflection-invariant supports, state parity defect 4.92e-11 and density
parity defect 3.65e-11. Projecting only the mathematically forbidden density
channels kept the original coupled equilibrium ratio at 9.64e-12. The
standalone resolved beam then **FAILED** active-row equilibrium on a tiny
symmetry-allowed load. V4 projected its body load with the same verified
reflection operator; correction was exactly zero, and the failure recurred.
The worst V4 row has load 3.5664998967e-16 N and residual
9.1302159083e-13 N, ratio 2559.993319. Its total work error is small, but
the explicit active-row rule cannot be waived. No validated resolved or
native common-action body comparison was produced in V3/V4.

The symmetry result is useful and the unvalidated work values suggest a
large beam-side difference under one density. They do not prove a body-law,
port, or connection defect. The remaining tiny load components occur in
allowed symmetry rows; zeroing them by magnitude would change the input to
force a pass and is not justified. Stop this numerical branch. A focused
independent review should decide whether a higher-precision consistent load
assembly, a mathematically justified exact nodal cancellation rule, or a
different *registered* numerical assessment can evaluate this body action
without relaxing the physical equilibrium criterion. Continue unrelated
G0–G6 work; F03/M2/G0 and physical accuracy remain open.

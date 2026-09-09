# Loaded curved-state development checkpoint

The separately frozen successor `1a3c4cc6cfb26ac3412b1f03a94bf657f4c27bf0`
completed once in 23.342 seconds on 2026-09-07, with exit 0 and no remaining
worker processes. It used the unchanged 120-second native construction limit,
600-second process-tree wall limit, 120-second inactivity limit, one thread and
24 GiB. No nonlinear equilibrium history was rerun or advanced.

The canonical comparison is 3,689 bytes, SHA-256
`c0a4a321eeba0de537282b4f20c951bf4678c9c50143663562b223eb8e7eca54`.
All ten artifacts common with the failed invocation are byte-identical,
including the first native modal packet, both checkpoints, both continuum
equilibria and all four reference spectra. The failed invocation remains
failed. Its missing second native packet/aggregate were never backfilled.

## Arithmetic result

Only the private exact shifted-inertia arithmetic changed: symmetric integer
Bareiss congruences replace dense rational Schur complements. On the same
saved 45-coordinate shifted pencil, one warm-up and eleven alternating-order
pairs returned identical inertia (40 positive, 5 negative, 0 zero).
Median call time was 0.2156404 seconds versus 2.7013116 seconds, approximately
12.5 times faster for this call. Raw median/MAD/p95 and CPU observations stay
external and hash-bound. This is not a general solver performance claim.
Both initial benchmark setup incidents remain preserved and documented.

## Scientific interpretation

At crown drop .01, both native and separate continuum operators have zero
negative modes. At .055, both have two negative modes and the continuum load
slope is negative. No negative root is removed or converted to a frequency.
Native signed-Ritz residuals are below 4e-16; reference profile differences
are below 3e-9. These numerical residuals do not establish model accuracy.

The coarse four-macro versus continuum eigenvalue discrepancies reach
15.05 percent at .01 and 21.24 percent at .055. Accepted loads also differ:
122.488 versus 119.986, and 254.955 versus 234.444. Therefore neither identical
equilibrium branches, mesh-converged modal accuracy nor a buckling factor has
been proved. Stable-to-unstable sign agreement is development progress only.

Separate inventories: initial arithmetic 31 passed; combined arithmetic,
reference and process-guard preparation 56 passed; corrected complete harness
26 passed; read-only saved-evidence/mutation inspection 13 passed. These
inventories overlap and must not be added into a claimed distinct-test count.
All reports, transcripts and artifact hashes are bound by the execution status.

## Resume point

The next scientific gate is a bounded loaded-state refinement/branch comparison,
not a full qualification rerun. A successor must explicitly address the current
80-coordinate spectral constructor and 64-coordinate exact-inertia bounds
before admitting larger native meshes; do not silently increase these bounds.
Use preserved converged histories where available and retain signed roots.
Then finish buckling/postbuckling, nonlinear section/state parity, slenderness,
independent review, public opt-in packaging and objective beam-shell coupling.
No Q4/S3 mechanics, defaults, legacy paths, qualification evidence or releases
were changed. Full GE-B3 qualification remains incomplete.

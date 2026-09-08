# Matched-drop loaded refinement smoke

Parent42075b38c6b0cb64da75259bdb1f2b48826d7446 and accepted capacity status
SHA37DB04FFD069474085FD4CADAD557959FE0D43D57C1A4626A83C7AA0EBA7A181.
No src/element/section/load/mass/tolerance/default change. Preserve the N12
onset NO-GO and all existing evidence. This is a new diagnostic smoke, not a
retry or a substitute for the critical-point convergence comparison.

Freeze full-spatial N16/N20/N24 arches from the capacity-successor case at
common crown drop .045. Fixed programme (.01,.02,.03,.045), physical direction
(0,-1,0), crown node N+1, unit downward nodal dead force; clamped ends and all
existing geometry, reference frames, sections and quadrature unchanged.

Each mesh has six separate processes. Stages1..4 advance exactly one target
prefix using native stop_after. First starts virgin; all subsequent prefixes
restore the complete checkpoint of the SAME fixed Programme, with external
hash and successful empty-process-tree receipt. No cross-programme transfer,
reseal, extension or state interpolation. Stage5 captures physical factors
from the complete four-target checkpoint. Stage6 separately validates original
factor decoupling and Decimal80/100 zero-shift counts, mass/trace positivity,
native equilibrium/load binding and reflection/planarity of every saved record.
Never include the numerical displacement-control equation in physical K.

Validate strict canonical requests, source capacity authority, exact stage
ordering, request/ready/checkpoint/packet/science hashes and process receipts
before numerical imports. Test invalid stage/mesh/schema/source/hash/receipt,
nonfinite and duplicate keys, and forbidden previous-state routing. Unit tests
must pass before loaded workers start. Common aggregate only after all launched
workers reach terminal process state; no canonical partial aggregate on failure.
Preserve partial checkpoint diagnostics, stdout/stderr and all process receipts.

One numerical thread,24GiB/process tree,600s/child,1800s/wave,120s CPU-idle and
nativeContext120s, at mostthreechildren concurrently. Each mesh owns exclusive
external directories. No automatic retry. Process/evidence failure stops the
wave safely and blocks a larger search. Count differences between these meshes
are diagnostic: no pass/fail prediction of the missing onset gate is imposed.

After success, freeze a separate actual fine-mesh critical-point search using
the measured costs. Retain conservative2% drop AND load endpoint comparison.
This smoke cannot establish first-root status, uniqueness, spatial postbuckling,
complete material/solver/state/recovery/restart parity, installed production
integration or objective beam-shell joints. Full goal and independent review
remain open; no aliases, defaults, version or qualification change.

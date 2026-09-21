# F03-K0 v2: programming correction and one-shot registration addendum

Status: **READY FOR REGISTRATION, NOT EXECUTED.**

This addendum supplements the F03-K0 manifest without changing its
mesh/space/load inventory, physical model, thresholds, thread setting,
resource limits, or limited planar interpretation. V1 remains a consumed
programming abort with zero completed meshes; its identities and hashes
are preserved in `B3_GE_E4_PL_G0_F03_K0_V1_ABORT.md`.

V2 changes exactly the condensed KKT block construction from nested
tuples to nested lists for NumPy 2.4.6. The mathematical block matrix is
still `[[Ke, Cu], [Cl, -Sr]]`; this correction affects no mechanical
equation or acceptance threshold. An independently reviewed source diff,
AST parse and bounded synthetic block-shape/symmetry check precede v2.

After committing that source and review, create a new exclusive
`G0_F03_K0_V1`-schema registration with **v2** identity and the exact
new output directory
`C:\Github\ANYsolver\.qualification\b3-ge-e4-pl\f03-k0-v2`.
The schema gate string remains `G0_F03_K0_V1` because the runner's
case/threshold schema has not changed; registration filename, source
commit, SHA-256, evidence directory and invocation are new. A second
execution of the old v1 registration is forbidden.

Keep the 7200 s external wall and 8 GiB sampled RSS limits. Run only
through the one-shot supervisor with source 0.4.7 explicitly imported
from this checkout and the recorded 0.4.6 installed distribution
metadata. Preserve any v2 failure as a distinct immutable result.

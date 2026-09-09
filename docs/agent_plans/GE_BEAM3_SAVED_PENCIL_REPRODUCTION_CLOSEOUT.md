# Saved-pencil reproduction: diagnostic complete, old gate unchanged

Freeze 61f5a026794bf02e6156b9d9d24cfd9fcf07c4e5, tree
a2864041d99fe10ca8b7f86d85cfc6616432aa26. Local eight tests/seven files
passed in 1.68 seconds; saved-data one test/one file passed in 1.68 seconds.
No mechanical assembly or worker retry. Every process tree terminated.
All source/run copies are verified in the 24-data-file external archive.

The reconstructed trace map is exactly equal to the saved map. The same
six-mode gvx request reproduces all six saved eigenvalues exactly. Changing
only the requested range to eight gives a maximum normalized difference
1.607181054907869e-11, so the old 1e-11 assertion still fails and is recorded
as false. Full-spectrum gvd differs by 3.698541473085015e-12. Normalized
full-pencil residuals are 1.82e-17 to 5.20e-17; mass orthogonality errors
are at most 1.72e-14. These observations isolate request-dependent numerical
variation, not corrupted input or a changed mechanical operator. Floating
error estimates are diagnostic, not rigorous eigenvalue error certificates.

Both expanded solutions find the seventh native mode matching the sixth
stored bending reference: frequency error 1.17606009624%, MAC
0.9927407825032745. The sixth native torsional mode differs from its analytic
second-torsion reference by 0.3618169078%. Thus the six-mode cutoff excludes
the relevant native bending vector while including the neighboring torsion
vector. This explains the failed fixed-index comparison without qualifying
the complete mode group. No historical gate or failed assertion is relabeled.

Next: freeze reference-derived complete groups, including a guard mode past
the selected window, and verify frequency plus invariant subspace agreement
with the same 2% and .95 requirements. Cases, mechanics and inertia remain
unchanged; no empirical mode matching based on candidate output is allowed.
Then run the full rehearsal and two fresh deterministic cycles.

Independent review remains PENDING; production qualification and the full
beam/beam-shell goal remain incomplete. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

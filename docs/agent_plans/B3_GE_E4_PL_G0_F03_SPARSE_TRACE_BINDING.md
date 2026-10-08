# Saved sparse trace and endpoint binding

Bounded classical-reference verification only. This is not native mechanics
qualification, a new physical solve or a production coupling workflow.

`verify_trace_binding` receives an owned compiled tensor grid, physical q,
positive D, the complete saved station inventory, and root, tip and free
transverse-slope matrices. The inventory contains s=0,1/8,...,1 for physical
derivative orders 0, 1 and 2. Right traces are used internally and the left
trace at s=1. Second derivatives may jump; changing a side is not an
equivalent observation. Missing, reordered or inexact station keys fail.

The verifier extracts exact local trace polynomials from the compiled grid,
once per needed interval. Exact rational station evaluation is independent
of a saved floating coefficient reconstruction. The grid identity binds
reference cuts, exact event partition, degree and free-coordinate numbering.
The floating input matrices, actions, q and D have separate hashes.

For every observation it compares the complete sparse stored matrix with
the exact extracted operator, including entries outside expected support.
With S=L0^order R and R=diag(1/U0,1/U0,0.46/U0), the matrix check is
`||S (A_saved-A_exact) D||F / max(1,||S A_exact D||F) <= 1e-11`.
Squared rational comparisons avoid an uncertified square-root decision.
Exact contractions check both the supplied matrix action and saved action
against the exact extracted action, using the original relative max-one
normalization of scaled station actions and the `1e-11` limit.

Root, tip and free-slope operators are compared both to exact extraction
and directly to their corresponding saved station rows. The maximum-entry
normalization uses `max(D)/U0`, with L0 for the slope. Direct action differences
use `1/U0` (L0/U0 for slope). Each has a separate `1e-11` gate. Direct checks
prevent two individually small, opposite reference errors from hiding a
larger inconsistency. No fourth root constraint is added.

Resource checks precede retaining all copied sparse buffers and trace
extraction. The verifier bounds aggregate input entries, fraction sizes,
cumulative checked bits and estimated workspace. At most nine exact trace
intervals are retained. It never assembles a global dense matrix or solves
equilibrium. Its workspace estimate is not measured process peak memory.
This work belongs to verification preparation; repeated search and extraction
must not be put into a production local Newton trial.

Manufactured tests use an independently known quadratic displacement field,
its exact averaged translation and physical derivatives. They also exercise
changed actions/matrices, substituted endpoint operators, opposite endpoint
biases, missing or altered observation keys, sparse formats, owned results,
malformed buffers and resource failures. Exact trace binding does not prove
stationarity, positivity, condition, reactions, convergence or G0B acceptance.

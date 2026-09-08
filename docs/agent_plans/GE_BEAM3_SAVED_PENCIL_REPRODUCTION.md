# Saved-pencil reproduction diagnosis, not a qualification retry

Base a7438621060e1655554f2e42ea38dd41e87b5fbb. Preserve the failed
7a5c504 gate and its failed auxiliary attempt unchanged. Three research
paths: this plan, ge_beam3_saved_pencil_reproduction.py, and its test module.
No mechanical assembly, accepted history, inertia, production route or
threshold is changed.

Bind archived straight-diagonal native-n8.json: 339195 bytes, SHA-256
8BBA950126F865B53038827D764F4D8D8ABD84FF736ED9902D3F6B21D486B8E3.
Bind reference-high.json: 633457 bytes, SHA-256
69F620FCCD5C65191327B3FE9E305B2F665116B48337E9B0E9E8C32AFEED8E34.
Both are in ge-beam3-native-continuum-frequencies-7a5c504-20260908,
runs/rehearsal-straight-diagonal/pytest/test_native_frequency_converge0.

Reconstruct the declared massless trace map from those exact saved matrices.
Record exact map equality, data/layout consistency, physical mass condition
estimate and matrix norms. Compare same-count gvx, eight-mode gvx and full
gvd solves. Keep the original 1e-11 forward-value assertion as an explicit
boolean observation for every variant; do not waive or change its threshold.
Report complete values and residuals before final test assertions.

Record the original normalized full-pencil residual and mass-orthogonality
checks (1e-11), plus estimated Cholesky-whitened residual norms. For this
diagnostic, triangular completion represents LAPACK's existing lower-input
view, not a new physical matrix. Floating-point estimates are not rigorous
error intervals or proof of relative low-eigenvalue accuracy.

Primary numerical background: SciPy eigh documentation,
https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.eigh.html,
and LAPACK Users' Guide accuracy chapter,
https://www.netlib.org/lapack/lug/node72.html. Their algorithm-dependent
rounding discussion motivates investigation, not an assumed explanation.

Use both expanded solutions to report the physical eighth-mode window
against the six stored continuum shapes, including the seventh native mode
versus the sixth reference mode and the analytic second torsion frequency.
No old gate is reclassified, and no new engineering qualification is issued.

Separate inventories: local eight tests/seven scientific files; saved-data
inspection one test/one observations file. Run local first, then one fresh
saved-data invocation. No automatic retry. One numerical thread, 24 GiB,
600-second child, 120-second CPU inactivity; inspection itself <=30 seconds.
At most three workers and <=1800 seconds per wave. Preserve all failures.

The purpose is to determine the next scientifically justified correction,
not to replace the target beam or accept a reduced goal. Independent review
PENDING. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

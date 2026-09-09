# Actual post-plastic retained-state modal replay gate

Base `3e2048c2ee53d453db3aa5acf62116fcb6e5f4e6`. Test-only extension of
the private retained controller/modal path; no numerical operator, tolerance,
material, checkpoint, public/default, shell or legacy-beam changes.

Freeze three actual supported models: straight one-macro, curved one-macro and
connected curved two-macro. Reuse the existing coupled generalized elastic and
ellipsoidal yield metric, yield force 0.025 and positive hardening. Apply only
the existing reference-arclength spatial dead-force density (0.09,-0.03,0.02),
with no distributed couple. Explicit load targets: 0.25, 0.5, 1.0, 0.5.

Stop after target 3, require actual positive accumulated plastic history and
reject that peak-load checkpoint for elastic-interior conservative modal capture.
Resume the accepted checkpoint to target 4; this is prescribed unloading, not
a failed-run retry. Authenticate complete history and require current-material
replay from committed origins to remain strictly elastic-interior without any
history advance. Check each station's current strain/resultants using the existing
independently authored 96-digit primal section KKT reconstruction. This checks
material replay, not an independent continuum beam reference.

Capture physical current-rest inertia with the previously used coupled SPD
six-component inertia fixture. Solve the first six paired modes in bounds
(0,10000), retaining original-factor 1e-11 checks. Verify positive eigenvalues,
unchanged accepted state/checkpoint/recovery and exact repeated packet bytes.
No claim of plastic tangent frequencies, finite-velocity dynamics, buckling factors,
full beam engineering qualification, or objective shell-joint qualification.

Straight smoke first; stop expansion on failure. After all three development
cases pass, run two fresh-directory cycles and compare complete scientific bytes.
All runs use the existing bounded supervisor: at most three workers, one numerical
thread each, 24 GiB/process tree, 600 seconds/child, 1800 seconds/wave and
120-second CPU-inactivity detection. Preserve failures and terminal receipts;
no automatic retry. The Context retains its 120-second cooperative bound.
Independent review and complete environment-graph attestation remain pending.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

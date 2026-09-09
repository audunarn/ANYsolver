# Curved reference spectra: bounded standalone development

Parent `9004c6d9d781da6f14c5b49c25fd56111af362d9`. Existing production
beam/shell mechanics, defaults, historical evidence and public APIs remain
unchanged. This is not an activation or qualification stage.

## Independent-algorithm continuum reference

Use spatial variation fields v and omega about the stress-free parabola
r0(t)=(t,.15(1-t^2),0), with physical material second director +z. The continuum
reference-linear strain variation is gamma=R0^T(v_,s+tangent cross omega),
kappa=R0^T omega_,s. Integrate B^T C B and the physical velocity mass with
the same declared coupled elastic section as the saved curved moment fixture.
The separate global polynomial Ritz implementation imports no native beam
assembly, recovery, tangent, mass or cached operator.

Use (1+t)P_i(t) to enforce the clamped root; compare polynomial degree14 with
64-point quadrature and degree18 with 80-point quadrature, requiring relative
eigenvalue agreement below 1e-8. Reference eigenvector residual checks are
1e-8 and are deliberately identified as binary64 reference diagnostics, not
the native 1e-11 spectral acceptance test. No multiprecision or independently
authored reference claim is made. Native spectral/Ritz residual checks remain
1e-11. Degree10 straight axial/torsion closed forms, six free curved rigid
fields, positive mass and invalid-input guards are tested separately.

## Native comparison scope

Use exactly 1,2,4 macros of the existing coupled parabolic fixture, with
section inertia diag(1,1,1,.02,.01,.01). Construct virgin, zero-load capsules
without nonlinear advancement. The existing physical-fibre modal preparation
and exact-shift-fallback factor-chain solver produce the first six roots per
model. Never convert a spatial-moment checkpoint into conservative spectral
authority. Retain all operators, factors, vectors and reference matrices
externally, with source and capsule hashes.

Compare frequencies with the Ritz reference. Separately integrate the lifted
native velocity field v_h=I v_nodes+omega_cell cross reference_lift and its
kinetic overlap with the continuous reference modes. Check reconstructed
mass Gramians at 1e-8; record the full MAC matrix and diagonal values. This
does not substitute for clustered-MAC qualification. Frequency errors are
reported without a development GO or tuning to achieve the eventual 2% gate.

## Execution controls

One frozen child, one numerical thread, 24 GiB complete-process-tree memory,
600-second wall limit and 120-second inactivity protection. Exactly two
reference spectra and three native spectra; no nonlinear solves. Existing
smaller native constructor deadlines remain active. Use exclusive fresh
external artifacts and preserve partial/failure logs. No retries. Canonical
comparison publication requires all three positive supported native spectra,
complete saved raw artifacts, recomputed summaries, final source guards and
verified process-tree cleanup. This does not establish free native rigid-mode
coverage, loaded spectra, buckling factors, rings, wide slenderness, full
material parity or objective shell coupling; those remain required.

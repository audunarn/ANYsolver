# Physical current-rest spectra at the continued spatial endpoints

Parent 7ce4f75cbc376a0dd111ab3e989c29c536d926a2. Six research-only paths;
no native element, section, state, recovery, mass-policy or default changes.
Bind the complete saved native factor archive manifest
4ac11c904afd59613a8e74056594de6bfd9172bd68c1c295ba2d2509e70c6a13,
exact +/-0.0065 packets and prior continuum polynomials through worker loaders.
Preserve all old negative-work/inertia results and administrative incidents.
Neither owner capture nor nonlinear/continuum equilibrium solve is repeated.

## Native physical pencil

Assemble K=(L R)^T(L R)+(H+H^T)/2 and M=B^T B directly from saved binary64 factors
at 80/100 decimal digits. Do not use the rounded captured stiffness as authority.
No factor entry is dropped. Guard raw geometric skew at1e-11. Retain all426free
coordinates; algebraic141nodal rotations have exactly zero kinetic-factor columns.
Eliminate them with positive LDL^T only, checking the original complete trace
solve residual and Schur symmetry at1e-60. Negative algebraic stiffness blocks
the calculation; no mass floor, clipping, numerical drill mass or Guyan reduction.
The resulting285dimensional physical mass pencil retains144cell rotations.

Use the lowest six binary64 generalized eigenvectors as initial guesses only.
Perform exactly four bordered Newton eigenpair corrections, with residual and
Rayleigh work recomputed using the Decimal pencil at each correction. Audit the
output-rounded full438coordinate vectors against the original Decimal matrices.
Require normalized full-vector residual, original bilinear Ritz identity and
physical modal mass orthogonality <=1e-11. Residual normalization uses that mode's
force/mass action, not an unrelated maximum stiffness. Preserve negative roots.
Store modes, signed eigenvalues, trace pivots and all diagnostics externally.

The mass policy is current-rest linearization. This does not enable finite-
rotation transient dynamics or provide gyroscopic terms. For negative lambda,
sqrt(-lambda) is an instability growth rate, not a real oscillation frequency.

## Separate continuum physical mass

Reuse the derived full six-component spatial energy form on the saved fields.
Integrate kinetic density diag(I3, R diag(3e-5,1e-5,2e-5) R^T), with reference
arclength measure. This matches the saved native section inertia, including its
physical material orientation. Do not substitute the earlier L2 trial Gram.

Use continuous clamped sine fields in all six components,16/24/32modes each.
Four frozen profiles: (128Gauss,16modes),(128,24),(128,32),(64,32), on each of
the four saved continuum segments. Require sign agreement across profiles,
24-to32 signed-rate change <=0.5%, and64-to128 quadrature rate change <=1e-6.
The reference trial Hessian is assembled in binary64; its physical mass Cholesky
factor is checked against quadrature mass at1e-11. Generic Decimal pencil
postprocessing verifies eigenpairs of these saved trial matrices, not a rigorous
continuum operator bound. Roundoff symmetrization and kinetic factor rounding
are explicitly disclosed; no independent author or interval claim is made.

## Field and engineering comparison

Compare native80/100signed rates to1e-11 relative agreement. Compare both signed
native endpoints with the corresponding resolved continuum32/128profile.
Reconstruct native physical velocities from nodal translations and internal cell
rotation velocities, including the transported parabolic half-cell offset.
Nodal rotational traces have no invented kinetic contribution. Reconstruct
continuum fields from their full sine coefficients. Integrate a6x6physical MAC
matrix using the continuum spatial inertia metric and32Gauss points per48native
half-cells. Use deterministic one-to-one maximum-MAC matching; report the matching.
Require matched signs, signed growth/frequency-rate errors <2%, and matched
physical MAC >=0.95. Report disagreement honestly rather than changing tolerances
or forcing mode labels. Counts or stability outside the requested six modes are
not inferred from the finite continuum trial space.

## Execution, review and preservation

Targeted unit tests precede freeze: exact small Schur/cancellation examples,
80/100precision, original residual/work checks, massless partition and invalid
factor mutations, physical inertia objectivity, signed-rate semantics, reference
profile mutations and exact saved endpoint binding. A Decimal unit assertion
was corrected before freeze to use its intended1e-60 rounding bound rather than
assert equality after recurring division; no registered scientific gate changed.

Run positive native80 smoke first. If it succeeds, run the remaining registered
jobs: both signs,native80/native100/reference, two replicas each (12processes
total including smoke), maximum3concurrent, fresh exclusive external outputs.
All twelve must reach terminal states before aggregate publication. Require
same-profile/sign replicas byte-identical. No automatic retry or consumed-root
reuse. Child600s/24GiB, one numerical thread, max3concurrent,wave1800s,
existing120sCPU-inactivity plus120sinner spectral bounds. Runtime guards before
scientific imports and finalization bind clean commit, Python hash and versions,
not a full environment file graph. Keep partial profile/failure diagnostics
separate from accepted worker evidence.

A process/accuracy/refinement failure blocks this gate; a resolved engineering
or MAC disagreement is a failed comparison, not permission to alter mechanics.
Even a pass establishes only these six current-rest modes at the two prescribed
endpoints. Full nonlinear/state/material/solver/geometry qualification, independent
author review, installed opt-in selection and objective eccentric/curved beam-shell
connections remain open. No release, public activation, API or version change.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

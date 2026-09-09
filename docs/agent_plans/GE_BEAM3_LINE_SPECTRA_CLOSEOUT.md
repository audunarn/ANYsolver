# Conservative line-load spectral integration milestone

Frozen source `3e666be05a748b44c3d108fa18ad0171c47e81bf`, tree
`5cd1c88bdc2933d2ca4ad045a34078579f5c9e55`.

The new private path replays actual accepted line-load histories and includes
the required external potential Hessian in the at-rest spectral operator.
It does not convert checkpoints or re-execute nonlinear loading. Existing
material, geometry, force/moment/line controllers, mass, eigenvalue kernels,
public beam/shell routes and defaults are unchanged.

Separate inventories:

- Preparation: 21 passed, 10.899 pytest seconds.
- Frozen cycle A: 21 passed, 10.969 seconds; 12.434 supervised seconds.
- Frozen cycle B: 21 passed, 10.897 seconds; 12.433 supervised seconds.

All seven operator/mode packets are byte-identical between A and B. Peak
process-tree memory remained below 240 MB. Their byte counts and SHA-256 hashes,
all 30 archived files and the frozen source blobs are bound in the canonical
development status. Full process-tree cleanup and zero matching workers were
verified. There were no new nonlinear solves or automatic retries.

The complete stationary-system Schur tangent agrees with the split-factor
spectral operator. A separate rational-Q2/closed-derivative calculation checks
the external Hessian. Omitting that term changes the computed spectrum.
Moderate-contrast spectra agree with a separate dense generalized-pencil
calculation to the existing `1e-11` criterion. The largest native signed Ritz
residual was `6.585e-16`. Saved coupled plastic states retain distinct explicit
frozen-plastic and last-increment algorithmic interpretations; accepted history
is unchanged. Large common-rotation covariance, zero-inertia trace elimination,
and input/final-publication guards passed.

The seven packets each contain the six requested lowest modes. All eigenvalues
in these particular packets are positive; this turn supplies no new negative-mode
witness or critical buckling load. The backend's signed-value policy remains
unchanged, and the algorithmic operator is still a diagnostic rather than
physical vibration authority. No continuum modal accuracy, finite-velocity
dynamics or full beam qualification is established here.

Archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-line-spectra-20260907-3e666be`.
Only verified temporary transfer duplicates may be removed; original and archived
outputs remain. Independent review, continuum loaded-modal/buckling comparisons,
public solver integration, full standalone workflow qualification and the
objective beam-shell connection are still required. The full goal remains active.

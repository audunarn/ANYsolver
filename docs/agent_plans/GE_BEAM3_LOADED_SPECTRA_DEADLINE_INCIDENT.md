# Loaded arch spectral deadline incident

The single invocation frozen at `19d390e82d2d784e72ca3ebbba67d9d034d2f947`
exited 1 after approximately 180 seconds. Both continuum equilibria and all
four reference Ritz spectra were preserved. The first native spectrum was
saved; the second returned to the unchanged 120-second construction guard
too late. No native-4 packet, pending aggregate, or canonical aggregate exists.
The failed invocation remains failed, with no automatic retry. Artifact byte
counts and hashes are bound in `ge_beam3_loaded_spectra_failed_execution.json`.
Post-execution process inspection found no matching Python workers.

The first native spectrum has positive roots and very small native residuals,
but this partial diagnostic cannot classify the incomplete two-state comparison.
The four-macro versus continuum eigenvalues are not identical, and no modal or
buckling qualification is claimed. Historical nonlinear input remains unchanged.

Next development is arithmetic-only investigation: the exact shifted-inertia
fallback currently uses dense rational Schur complements. Compare it with a
fraction-free integer congruence implementation using exactly the represented
binary64 shifted pencil. Establish sign equivalence, cancellation and deadline
behavior before considering a separately frozen successor diagnostic. Do not
raise deadlines, relax root widths, change mechanics or alter accepted evidence.

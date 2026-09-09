# Explicitly bounded twelve-macro loaded spectra

Parent `18d42b0be9d52544223c4ffd3ed319ff9cb89254` preserved the faster,
byte-identical six-macro spectral reproduction. The next step is the actual
twelve-macro refinement, not another small-case qualification substitute.

## Frozen inputs and unchanged formulation

Reuse the twelve-macro accepted nonlinear checkpoint:
278640 bytes, SHA-256 ca95e88b6d354c3aeeb4bcebc1f49791cb3b1cef0781644f3be0e696e3a33683,
under `ge-beam3-fibre-arch12-20260907-v1/checkpoint-diagnostic.json` in ANYrelease.
Its original 512-coordinate retained-state budget remains part of its identity.
No nonlinear solve, history advance, remapping or state conversion is allowed.

Bind the six-macro comparison at source `4204f3a38c65fc215a76c595f994a7a71c317d54`,
3490 bytes, SHA-256 f50285799e45a7fdbbcb7d9cad997b13e83a8e7bf38e6904c4c1e247595d5362.
Reuse its degree16 continuum Ritz spectra and both equilibrium packets
byte-for-byte. The validator follows their existing six-to-four-macro hash
chain. No new continuum/reference solve is allowed in this wave.

## Explicit allocations

Twelve macros have 25 nodes and 438 retained nonlinear coordinates; replay
selects the existing 512 bound. Modal preparation has 222 assembled spectral
coordinates and 141 dynamic coordinates after removal of end constraints and
exact zero-inertia nodal rotation traces. Add explicit spectral allocation256
and exact-sign allocation160; retain defaults80/64 and the six-macro128/96
options. Each nondefault native allocation is identity-bound. A binary64
256-square array is at most 512 KiB, not a claim about total process RSS.
All work remains inside the existing 24-GiB process-tree memory watchdog.

No coefficients, quadrature, mass, recovery, constitutive laws, root widths,
residual tolerances, deadlines, public selectors, dependencies or defaults
change. The exact-sign filter retains its integer fallback and 30-second
total call bound. The spectral constructor retains 120 seconds.

## Single diagnostic and interpretation

Select `--macros 12` on the bounded refinement runner. Replay all accepted
records, derive exact prefixes at crown drops .01 and .055, and compute six
signed fixed-dead-load modes for each. The continuation constraint is removed;
accepted plastic coordinates remain frozen. Use bounds(-1e6,1e8), root width
1e-10 and unchanged native signed-Ritz/residual gates1e-11.

One process, one numerical thread, 600-second process-tree wall limit,
120-second inactivity limit, 24 GiB, fresh external exclusive outputs, and
no automatic retry. Full raw validation, immutable source/input checks and
complete job cleanup precede canonical promotion. Preserve partial evidence
if a bound, numerical guard or any process step fails.

Compare every signed root and native equilibrium load with the unchanged
continuum reference and six-macro predecessor. Report refinement honestly;
no negative mode is removed and no error threshold is relaxed. A successful
process is development evidence only. Finer-mesh agreement cannot by itself
qualify the full straight/curved beam, wide slenderness, nonlinear sections,
buckling/postbuckling, independent review or objective beam-shell connection.

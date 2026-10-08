# Executed matched 8×4×2 Mx deck — development comparison

The pinned CalculiX 2.23 binary executed the exact 906-node, 128-element
C3D20 model with 40 growing five-channel physical weak-P0 rows. The deck
retains the shell root, 0.03 m offset, and work-conjugate 10 N·m section torque
of the matched native/resolved screen. Its `*EQUATION` rows are a pivoted
representation of the physical rows: serialized relative row error
`3.48e-16`, pivot error as recorded in `case/metadata.json`. The deck SHA-256
is `984ab66d68693a8b6393c95be48b475cce2dae02bf8d888bf9f4f4c46a6daa51`.

One accepted increment completed. The independent sparse KKT reconstruction
used the **physical** rows, not the pivoted CalculiX rows. All declared
development-parity checks passed. Relative all-node displacement difference
was `1.803e-9`; scaled weak gap `3.05e-20`; corrected support difference
`5.98e-9` relative. CalculiX work was `0.000984473175679996 J`; the saved
independent work was `0.000984473175778957 J`. Corrected root Mx was
`-9.999999997142414 N·m`, balancing the applied `+10 N·m`. Raw `RF` alone
omits the exact-constraint force; the correction is `Cᵀλ`.

[Comparison](comparison.json), [comparison process receipt](comparison.receipt.json),
[CalculiX process receipt](case/ccx.receipt.json), the exact deck, metadata,
DOUBLE FRD, full stdout/stderr and `.sta` are preserved here. CalculiX process
wall was `0.164139 s`; comparison wall was `2.558927 s`. Both were requested
on CPU0, one numerical thread, JIT off, with a 2 GiB process-tree cap; the
receipts record observed affinity and sampled memory. Effective library thread
counts were not independently audited. The Python startup warning in
`comparison.stderr.log` did not prevent the comparison process exiting 0.

The [first attempt](../bl5-ccx-matched-mx-8x4x2-20261008-v1/launch-failure.md)
failed before creating a CalculiX process (`WinError 623`); it is retained
as a launch failure. The successful run used a new evidence directory.

**Decision:** the independently assembled matched C3D20 operator is credible
as a development reference at this resolution. The 16×8×4 resolved work in
the saved series is still moving relative to 8×4×2, so neither the middle
level near-match nor this parity check establishes native BL5 accuracy,
reference convergence, line-law selection, F03 acceptance or release. The
next bounded numerical question is whether *resolved shell refinement with
the beam/weak action fixed* accounts for that movement before extending the
external mesh. Do not choose a multiplier basis from the present ratio.

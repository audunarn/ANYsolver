# F03 Q6 three-grid primal-positivity diagnostic

**24 September 2026. Unregistered source-process evidence. F03/G0B remain open;
G1 remains barred.** This is a feasibility check for the original represented
scaled shell matrix of the fixed Q6 X0/X1/X2 grids. It does not qualify the
physical beam/shell interface, installed package, or a final scientific gate.

The producer saves the original scaled shell matrix, separately rounded
symmetric working matrix, SuperLU lower factor, positive diagonal, permutation,
and displacement scale in a bounded canonical archive. It also saves every
inverse column of the lower factor. The certificate checks the factor inverse
and outward-bounds the congruence residual against the **original** scaled
matrix. The exact-Fraction sufficient inequality is strictly below one on all
three grids. Each replay reads only saved inputs, uses the same experimental
proof kernel, and requires the entire proof dictionary to equal its source.
It does not reassemble, factorize, or solve the physical model.

| Grid | Shell order / inverse columns | Source seconds / sampled peak RSS | Replay seconds / sampled peak RSS | Saved input / inverse bytes | Exact sufficient ratio, approximate |
|---|---:|---:|---:|---:|---:|
| X0 | 3,286 | 262.30 / 294,961,152 B | 161.01 / 267,317,248 B | 16,480,222 / 86,382,368 B | 1.6367015404931608e-13 |
| X1 | 4,402 | 441.45 / 389,754,880 B | 307.92 / 348,037,120 B | 22,362,686 / 155,020,832 B | 2.1624013496850504e-13 |
| X2 | 5,890 | 840.62 / 547,659,776 B | 567.54 / 486,645,760 B | 30,234,078 / 277,536,800 B | 4.2850592234279293e-13 |

All six supervisor receipts report `completed`, exit 0. All three source
proofs report `POSITIVE_QUADRATIC_FORM`; all three saved-input replays match
their source proof exactly. The replay validates the source measurement,
attempt/start, receipt, archive and inverse hashes, factor/scale inventories,
and parent/child measurement identity. The archive and inverse hashes were
also checked directly against their locally retained raw files. The source
producer hash is the same across the three grids:
`d488c0f46147527356691fe9ce91c967a9dcaf15f1aa8c8f9437ca9ec9e8fba9`.
The proof module hash is
`d2c1072fcdb520d5326113744d3dcdd60b77724a806611dd6bc58d861ac9990f`;
the archive module hash is
`ee992a53cdcfe32c15d9b5c448a52f1cf296ec4af23c119f427815ce85744b36`.

Source records:
[X0](B3_GE_E4_PL_G0_F03_Q6_X0_POSITIVITY_ARCHIVED_V3_REHEARSAL_20260924/measurement.json),
[X1](B3_GE_E4_PL_G0_F03_Q6_X1_POSITIVITY_ARCHIVED_V3_REHEARSAL_20260924/measurement.json),
[X2](B3_GE_E4_PL_G0_F03_Q6_X2_POSITIVITY_ARCHIVED_V3_REHEARSAL_20260924/measurement.json).
Saved-only replay records:
[X0](B3_GE_E4_PL_G0_F03_Q6_X0_POSITIVITY_SAVED_REPLAY_V3_20260924/measurement.json),
[X1](B3_GE_E4_PL_G0_F03_Q6_X1_POSITIVITY_SAVED_REPLAY_V3_20260924/measurement.json),
[X2](B3_GE_E4_PL_G0_F03_Q6_X2_POSITIVITY_SAVED_REPLAY_V3_20260924/measurement.json).
The first X0 attempt failed on the SciPy `csr_array`/`csr_matrix` contract
before allocating inverse evidence; the second X0 attempt proved the matrix
but did not archive factor inputs. Both records remain preserved. Raw matrix
and inverse artifacts remain local and Git-ignored; tracked receipts and
measurements retain their hashes and sizes.

The focused affected suite passed **62/62** after the final replay correction.
Independent read-only review decoded and rehashed all three saved archives,
checked source, factor, inverse, receipt and parent/child identities, and
recomputed the exact-Fraction margins. It found no false-positive path in the
saved-matrix proof. The review identified the parent/child measurement race
and inverse-inventory checks, which were corrected before the three replays.
The review also found
that the archive does not independently tie the represented shell matrix and
scale to the physical Q6 assembly; formal evidence still needs owned regular
file checks, exact installed source/dependency identity, arithmetic-kernel
review, physical-observable error propagation, full physical settling, and
native interface mechanics. No G0 acceptance or speedup is claimed.

There is a separate **integrated resource concern**. X2 positivity source
reported approximately 300 s in assembly and 539 s in proof. The earlier
patched-kernel integrated X2 diagnostic took approximately 1,411 s, including
approximately 235 s of duplicate physical assembly. Reusing the certificate
assembly for positivity alone suggests approximately 1,950 s total. Reusing
that same assembly for physical recovery as well suggests approximately
1,715 s, leaving only about 85 s under the draft 1,800 s case envelope.
These are estimates from separate runs, not an integrated measurement or a
frozen scientific budget. A shared-assembly installed rehearsal with frozen
inputs and limits is needed before asserting the complete route fits.

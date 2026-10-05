# F03 Q6 X0 archived-system and saved-only replay rehearsal

**24 September 2026. Unregistered source-process diagnostic. F03/G0B remain
open; G1 remains barred.** The X0 certificate route now saves its canonical
scaled sparse KKT matrix, right-hand side and physical coordinate scales in a
strict bounded archive. The new replay reads that archive, the candidate state
and every saved inverse column; it does not assemble, factorize or solve.

The [source receipt](B3_GE_E4_PL_G0_F03_Q6_X0_SYSTEM_ARCHIVE_REHEARSAL_20260924/receipt.json)
reports exit code 0, **297.28 s** elapsed and **328,466,432 B** sampled peak
tree RSS. The [source measurement](B3_GE_E4_PL_G0_F03_Q6_X0_SYSTEM_ARCHIVE_REHEARSAL_20260924/measurement.json)
records a 3,289-order, 1,200,496-nonzero KKT system and all 3,289 inverse
columns. Its reported diagnostic status is `CERTIFIED_WITHIN_LIMIT`, condition
upper bound `624606.8922703825`, and amplified backward upper bound
`7.458894411015157e-10`. The 19,288,414-byte system archive and
86,540,168-byte inverse remain local outside Git, with SHA-256 identities in
the tracked measurement.

The final [saved-only replay receipt](B3_GE_E4_PL_G0_F03_Q6_X0_SAVED_REPLAY_BOUND_REHEARSAL_20260924/receipt.json)
reports exit code 0, **196.33 s** elapsed and **256,921,600 B** sampled peak
tree RSS. Its [measurement](B3_GE_E4_PL_G0_F03_Q6_X0_SAVED_REPLAY_BOUND_REHEARSAL_20260924/measurement.json)
records exact certificate-dictionary equality with the source. The parent's
attempt hash equals the child's actually consumed source-measurement hash. File hashes
were recomputed for the source measurement, system archive, inverse and
candidate state; all four links matched their recorded SHA-256 values. The
archive read-back test checks numerical equality, independent array ownership,
altered-hash rejection, physical-scale admission and exclusive writing. The
focused storage, archive and certificate suite passed **50/50**. Earlier
[first](B3_GE_E4_PL_G0_F03_Q6_X0_SAVED_REPLAY_REHEARSAL_20260924/receipt.json)
and [snapshot](B3_GE_E4_PL_G0_F03_Q6_X0_SAVED_REPLAY_SNAPSHOT_REHEARSAL_20260924/receipt.json)
replay rehearsals remain preserved; the final route adds source-receipt,
diagnostic-status and parent/child identity admission. Independent read-only
review found the final child replay uses the same owned snapshots for hash and
certificate evaluation. It did not provide a formal arithmetic proof.

This establishes a reproducible **source-level saved-input replay** for X0.
It does not independently prove the compiled interval arithmetic: source and
replay use the same experimental kernel. The archive's scaling vectors are
producer-supplied and do not independently certify their mechanical meaning.
No installed artifact, X1/X2 saved-only replay, physical-observable error
propagation, primal positivity, frozen three-grid adjudication or native G0
mechanics is claimed here. The numerical status is a diagnostic field, not
gate acceptance.

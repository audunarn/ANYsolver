# X2 Q6 combined shared-assembly resource diagnostic

**24 September 2026. Unregistered source-process rehearsal. F03/G0B open;
G1 barred.** This run measured the full numerical certificate, primal
positivity, physical recovery and spatial audit from one assembled Q6 X2
operator owner under one supervised process. The 2,400-second observation cap
does not revise the draft 1,800-second case envelope or establish an installed
scientific registration.

The [receipt](B3_GE_E4_PL_G0_F03_Q6_X2_SHARED_ASSEMBLY_REHEARSAL_20260924/receipt.json)
reports `completed`, exit 0, **2,258.19 s** and **692,072,448 B** sampled
peak process-tree RSS. The [measurement](B3_GE_E4_PL_G0_F03_Q6_X2_SHARED_ASSEMBLY_REHEARSAL_20260924/measurement.json)
separates approximately 340.63 s assembly, 970.11 s KKT certificate,
542.56 s positivity, 94.55 s physical recovery, and 309.68 s spatial audit.
Physical recovery reported 5.1 microseconds in its assembly slot: it received
the existing operator object and did not reassemble. The total exceeds the
draft 1,800 s envelope by **458.19 s**. It fits the observation cap by only
141.81 s, so there is no demonstrated margin for an installed formal route.

The KKT certificate reports `CERTIFIED_WITHIN_LIMIT`; the shell proof reports
`POSITIVE_QUADRATIC_FORM`. The candidate file hash matches the source
measurement. Physical recovery checks its independently reconstructed scaled
KKT/RHS hash against the certificate hash before using the candidate. The
scaled KKT/RHS hash and original scaled shell hash exactly repeat the earlier
X2 diagnostics. The free-state hash, signed physical quantities, complete
functional and spatial wrench/work values repeat the prior patched-kernel X2
result. An iterative shell eigenvalue estimate changed from
`1.85266244709543e-05` to `1.8526624470876175e-05`; it remains comfortably
above its numerical guard and is the only observed non-timing numerical
field difference.

The reviewed runner passed the same `QpOperators` object to certificate,
positivity and physical recovery. Independent read-only review found no
in-place mutation in those called phases, but the V1 run did **not** hash all
mutable operator arrays between phases. The exact V1 runner bytes are
[preserved](B3_GE_E4_PL_G0_F03_Q6_X2_SHARED_ASSEMBLY_REHEARSAL_20260924/runner_v1_source.py.txt);
their SHA-256 matches its attempt/start source hash
`f82a02bfbca0a4a5ed263b73b3f196e85db8d99d9bc1f201693c7e9c41088a3b`.
The subsequently added operator fingerprint is a V2 change and must not be
attributed to this V1 evidence. Raw inverse and matrix archives are retained
locally and Git-ignored, with hashes in tracked measurements.

The V2 diagnostic now fingerprints the trace parameters, derived sizes and
area, basis and quadrature, free-column maps, shell and beam CSR buffers,
load, root and tip arrays, and assembly diagnostics against a separate
expected trace. Focused shared-assembly and pilot tests passed **17/17**
after this change, including basis/quadrature, derived-scalar and numerical-
buffer mutation checks. **V2 has not run**;
these tests do not amend the V1 receipt or resource outcome.
Independent read-only review found no remaining omitted mutable trace or
operator field used in this path. That review accepts the V2 helper only as a
diagnostic content guard, not as code/environment identity or qualification.

**Decision:** The shared-assembly path is executable and its physical outputs
remain consistent, but this measured source route exceeds the draft time
envelope. Keep resource qualification, installed identity, formal arithmetic,
physical-observable error propagation, complete scientific adjudication and
native interface mechanics open. Before another full run, review the V2
fingerprint, choose and freeze an installed observation envelope with measured
variance, and retain the current overrun as evidence rather than overwriting
or silently relaxing it.

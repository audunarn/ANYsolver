# Preserved first curved spectral invocation and correction rationale

Frozen source `02d571a66d8e622e1dbc542434db0959153c16c2`, tree
`377cd7c61c213e892550c0050ab63272fad6a494`, ran once from
2026-09-07T13:20:56.1977580Z to 2026-09-07T13:20:58.6289712Z, exit 1.
It failed `separate kinetic work reconstruction disagrees` after the first
native eigensolve returned. No canonical comparison exists and no native mode
packet was saved; absent evidence must not be reconstructed and represented
as output of that invocation. The consumed invocation is not retried.

Preserved external directory:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-curved-spectra-20260907-v1`.

- `checkpoint-1.json`: 4793 bytes, SHA-256 5734b71e2f00a878cd36ce8406030c7e01f7c25173694db9c3f959d8da4c41c5
- `reference-diagnostic.json`: 646569 bytes, SHA-256 9434d222b33aaedfe36a0c128a476b9a14692107f6663b923eb4484cbe85a51c
- `stdout.log`: 180 bytes, SHA-256 897c6cf50f70d04339ab9926fb631a80699c8eb8267ac88cfbf0ea92d1eb286b
- `stderr.log`: 1344 bytes, SHA-256 bd0d1e0feffe8083a4a2e659468d3ea1ff95d63eb66eae5823a509345ab2a783

Transcript SHA-256: 971f4d654579372536a815e093a1f4f9b0f1a3da1d38b0e76e080d13f1cecda1.

## Isolated mass audit, without another eigensolve

The separately reconstructed four-point kinetic matrix agrees with the native
factor Gram matrix to 5.56e-17 maximum entry and 8.90e-17 relative Frobenius
error. Using 16 or 32 points instead gives a stable 1.657e-9 maximum entry
difference and 2.760e-9 relative Frobenius error. The saved continuum modal
mass Gram matrix at the independent 16-point rule differs from identity by
1.56e-15. No source or mechanical coefficients changed for this diagnosis.

The failed diagnostic conflated exact consistency under the native four-point
rule with integration error relative to a different rule. A successor must
check the independent native-rule modal Gram matrix at 1e-11, retain the
higher-rule native Gram discrepancy as a quadrature diagnostic, and retain
the 1e-8 continuum-reference Gram check. This is a corrected comparison
contract, not a relaxed native consistency tolerance or a change of beam
mass, stiffness or quadrature. Eventual mass/engineering qualification remains
unproven; the original failure remains a failure.

A corrected, separately frozen development invocation may reuse only the
hash-bound saved continuum packet and construct new native spectra. It must
save native factors/vectors before the cross-rule diagnostic so a subsequent
failure does not lose that raw packet. No reference solve is to be repeated.

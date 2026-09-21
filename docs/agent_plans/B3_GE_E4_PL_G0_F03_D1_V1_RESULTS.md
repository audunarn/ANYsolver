# F03-D1 v1: finite-difference plateau and KKT parity diagnosis

21 September 2026. The frozen one-shot diagnostic executed against clean
source commit `161e5d714d575af65884df7221e556c76e7ad7f2`. The independent
F03 mechanics auditor separately verified the evidence hashes, complete
inventory, predecessor source identity, step-size disposition and parity
interpretation. **This is a completed diagnostic, not F03 or G0 acceptance.**

## Immutable evidence

| Record | SHA-256 |
|---|---|
| `C:\Github\ANYsolver\.qualification\b3-ge-e4-pl\f03-d1-v1-registration.json` | `99305e50ea0d280fc3c27741edf37bde8764060743e487ba47707ef9b4977ee8` |
| `C:\Github\ANYsolver\.qualification\b3-ge-e4-pl\f03-d1-v1\raw.jsonl` | `7df2b9535fbc000be6dc2ac98478b01cd2cebbe3c369f27befe326c05f2699fa` |
| `C:\Github\ANYsolver\.qualification\b3-ge-e4-pl\f03-d1-v1.attestation.json` | `2b5a030695333055fd98ed8ea2fadb38a5624d90b611f0bb07d8903c83289d91` |

The supervisor and independent audit found exit zero, 12 ordered records:
one start, four derivative meshes (240 station/direction/step entries), six
KKT parity cases, one terminal. No timeout, RSS-limit violation, parse error
or missing row occurred. Elapsed time was 18.39 s and sampled peak child RSS
180,355,072 bytes. All 17 explicitly hashed sources and the aggregate
363-path solver tree matched registration; the 14 inherited K0 sources also
matched the v2 source evidence. The imported source was version 0.4.7;
installed distribution metadata remained 0.4.6. This is source-backed
evidence, not installed-artifact qualification.

## Finite-pose derivative and virtual work

The same adjacent step pairs `(0.3,0.1)`, `(0.1,0.03)` and `(0.03,0.01)`
meet the original `1e-10` normalized derivative **and** virtual-work
thresholds at every station and in both probe directions on each tested Q4
and S3-V2D mesh. Thus the preregistered common-pair plateau exists for both
topologies and mesh sizes. At `h=0.1`, the global maximum derivative error
is `8.23e-12` and the maximum work error is `6.73e-12`.

At the original `h=0.001`, the maximum Q4 derivative error ranges from
`3.98e-10` to `8.30e-10` across the two meshes; it fails the frozen cutoff.
The S3 maxima are `6.96e-11` and `6.70e-11`. Out-of-plane translation and
rotation derivatives are zero in these deliberately planar fixtures.
Increasing the finite step recovers a broad local plateau; the evidence
supports numerical cancellation in the too-small original perturbation
for this restricted test. It neither changes the failed v2 rows nor proves
the future nonlinear six-channel derivative.

## Exact KKT parity

The v2 sparse/condensed parity value was reproduced exactly for all six
registered cases. Work-scaled backward residuals for the sparse full,
dense full and signed retained-elimination solves lie between approximately
`5e-20` and `5e-18`. The full KKT smallest/largest singular ratio falls
from `2.49e-7` in the small control to `9.08e-12` at `(N_b,N_s)=(16,16)`.
The retained-block condition ranges about 660–1004. The full sparse and
full dense **forward** solutions themselves disagree beyond `1e-10` in
both `(16,8)` and `(16,16)` cases; the largest dense/condensed mismatch is
`8.82e-9`. Therefore the five v2 forward-parity exceptions cannot simply
be assigned to a sign or indexing error in condensation. Severe global
conditioning is a plausible explanation, but the diagnosis is not a
mathematical proof that all three forward solutions meet an exact oracle.
The original parity failures remain failures.

## Decision and next experiment

No v2 criterion is relaxed, no failed attempt is rerun, and no multiplier
space is selected. A future separately registered KKT comparison may use
refined scaling or a more accurate bounded oracle, with a written error
budget and independent review; physical equilibrium, work and gap checks
remain mandatory. The next line-space candidate study must address the
observed row-rank losses, unsupported trace modes and refinement-dependent
spectral floors. The required full six-channel eccentric and curved F03
mechanics, G0B and every production/release gate remain open.

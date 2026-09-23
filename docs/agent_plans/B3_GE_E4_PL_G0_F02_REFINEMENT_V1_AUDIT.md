# F02-R-v1 independent raw-evidence audit

23 September 2026. The independent reviewer inspected the preserved
`g0b-f02-refinement-v1.log` without rerunning the case. Its SHA-256 is
`a7bf86e9f2c999cdfe804b67c170af548daf87d661f8111fd085f0ae37df9e16`;
the frozen runner SHA-256 is
`e02548f4eb3c6259d0fb1036318abc5e79e718ad88e15fef3c74063bc20bc890`.
Both match the registration. The runner is separately identified by its byte
hash: it was added after the source commit named in the raw log.

The reviewer found all 12 unique Q4/S3-V2D by n=8/16/32 by t=.035/.07
cases, all six thickness comparisons and four refinement comparisons.
Shell counts, matrix dimensions, and footprint node counts match the runner's
formulas. Recalculation from raw results gives maximum relative work error
`1.45599507784387e-15`, free/constrained reaction ratio
`6.12235778909957e-15` (each within `1e-8`), and maximum absolute
thickness-ratio error `3.99680288865056e-15` (within `1e-10`). Moments and
constrained norms are finite and positive; recorded exit is zero and elapsed
time 16.1163435 s, below the 600 s envelope. Peak memory was not measured;
environment and launcher markers are self-reported.

**Disposition:** the registered preparatory in-plane membrane torque and
thickness predicates passed. F02 and G0B remain open. This audit does not
cover director/shear preservation, finite-rotation attachment, drilling,
coupled beam reaction, or a continuum limit.

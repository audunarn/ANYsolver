# F03 signed weak mode: retained-dominated mode with alternating yaw rows

21 September 2026. **Ten/ten exploratory cases and twenty modes completed;
F03/G0B remain open.** Frozen source and prior registration: `c2cf269`.
Exclusive raw root:
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-weak-mode-v1/`.
SHA-256: `manifest.json`
`b384f264283773e08a8bbac530892279fab48fa7c970e2408bb62582e77a6220`,
`results.jsonl`
`4074c564d5532acbf83e051f4a1acf4fa7e46a9eaa22dc55e0dc69f984218f6a`.
All nine script hashes matched the frozen source, and the two predecessor
trace-dual artifacts matched their pinned hashes. No case failed. The
largest normalized eigen residual was `2.97e-14`, pulled-back scaled
residual `3.84e-13`, predecessor singular-floor difference `1.35e-14`,
graph-kernel residual `7.48e-14`, and vector partition error `8.89e-16`.
The largest normalized KKT had 930 rows, below the 1,200-row cap.
The next-closest absolute eigenvalue did not meet the registered
near-repetition threshold in any case; this finite check does not rule
out changes in mode ordering on other meshes.

The *minimum-absolute eigenmode of the full signed, normalized KKT* is
not the weakest positive-constraint or signed-Schur mode. At joint
refinement, representative Q4 results are:

| Space | `Nb/Ns` | Signed KKT eigenvalue | Physical norm² | Positive retained norm² | Negative retained norm² | Multiplier norm² | Weak KKT multiplier action cancellation ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| K4 | 4/4 | −.26536 | .02201 | .33702 | .60565 | .03532 | .2750 |
| K4 | 8/8 | −.11349 | .00511 | .43609 | .55349 | .00532 | .1141 |
| K4 | 16/16 | −.03467 | .00063 | .48180 | .51707 | .00050 | .03469 |
| Local dual | 4/4 | −.26080 | .01616 | .34811 | .61344 | .02229 | .2667 |
| Local dual | 8/8 | −.11186 | .00355 | .43891 | .55340 | .00414 | .1123 |
| Local dual | 16/16 | −.03453 | .00050 | .48201 | .51700 | .00050 | .03455 |

S3-V2D shows the same pattern within about `.001` in these fractions.
At fixed eight native half-cells, the signed floor remains approximately
`.11` as the shell changes from one to 64 cells, consistent with the
previous beam-side trend. In every twenty-mode record, adjacent yaw
multiplier row coefficients have alternating signs. This is a unitless
sign statistic on coefficients normalized by the frozen `F0=1 MN/m`;
it is not a recovered spatial torque distribution. The one-sided gap
samples at native cell boundaries and explicit left/right yaw jumps are
retained in the raw output. On Q4 K4 joint 4→8→16, maximum converted
yaw-jump amplitude relative to the displacement scale falls
`.0230→.00695→.000843` in this **normalized eigenvector**; it is not a
converged loaded-state gap.

For the Q4 K4 16/16 KKT multiplier component, the positive and negative
action squares are `.51646` and `.48183`, respectively, yielding a
small absolute-difference ratio `.03469`; the multiplier vector's own
norm² is only `.000504`. The associated *Rayleigh quotient* is large
(`68.66`), so that small unnormalized action difference must not be
called a near-zero signed-Schur eigenvalue. Indeed the separately
computed weakest signed-Schur eigenvalue is **positive `.41361`** with
negligible negative action and a cancellation ratio of `1`. The local
dual has corresponding `.57500`. By contrast, the all-positive saddle
comparators based on positive constraint floors are `.31462` K4 and
`.40830` local dual, versus the signed floors near `.035`.

This isolates an alternating, retained-dominated near-zero direction of
the signed normalized saddle on the tested beam refinements. It does
not establish a loss of the positive constraint inf-sup condition, a
near-singular signed Schur complement, a physical buckling mode, or a
uniform asymptotic rate. It also cannot rescue either space's previously
measured large *loaded* gaps. A genuinely distinct local yaw moment
test may be worth falsifying against these adverse modes and loads;
reweighting K4 cannot change its solution. Its exact span, native pairing,
physical work, signed stability, and all required mesh ratios must be
registered and tested before a production line law can be selected.

Independent read-only review checked the signed factorization and inverse
pullback before execution. Its post-run audit verified raw hashes, source
identities, twenty modes, residuals, jump counts, alternating coefficient
signs and this interpretation. Alternation and retained cancellation
co-occur in these modes; no causal effect of the yaw-row pattern alone
has been established.

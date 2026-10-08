# F03 Q6 X0 numerical-certificate feasibility — unregistered diagnostic

**24 September 2026. G0B/F03 remains open.** This is a diagnostic of the
numerical-certificate cost, not a scientific gate result. X1 and X2 have not
received the complete certificate, no installed-artifact three-case run has
occurred, and independent review of the compiled kernel is not complete.

## Preserved observations

The first cost run has raw [measurement and exact source](B3_GE_E4_PL_G0_F03_Q6_X0_CERT_COST_20260924/measurement.json)
but **no supervisor receipt**. The child finished; the parent raised
`TypeError` because it opened text logs while the supervisor supplied bytes.
Treat that attempt as aborted evidence, not an accepted supervised result.
The exact source is `source_at_run.py` in that directory; its SHA-256 is
`f25e699fb9df54d5c047ee37b3b8b7d38ae57d5c3b1a8d51a249af876a859875`.

The corrected [V2 cost measurement](B3_GE_E4_PL_G0_F03_Q6_X0_CERT_COST_V2_20260924/measurement.json)
has a [completed process-tree receipt](B3_GE_E4_PL_G0_F03_Q6_X0_CERT_COST_V2_20260924/receipt.json):

| Observation | X0 |
|---|---:|
| Scaled KKT order / nonzeros | 3,289 / 1,200,496 |
| Four-column inverse blocks / entry visits | 823 / 988,008,208 |
| L / U factor nonzeros | 1,243,629 / 1,254,449 |
| Assembly / factor time | 89.27 s / 0.081 s |
| One original Python interval product | 18.61 s |
| One compiled product including JIT | 0.429 s |
| Original/compiled interval bounds | Bit-identical for this block |
| Observed tree peak | 240,340,992 bytes |

Multiplying the first Python block time by 823 gives about 4.25 hours, an
**illustrative cost projection**, not a complete-run measurement. The compiled
kernel retains scalar multiplication and directed `nextafter` operation order;
bounded random sparse checks also showed bit identity. Its numerical soundness
still requires independent review.

The separately supervised [full X0 run](B3_GE_E4_PL_G0_F03_Q6_X0_FULL_CERT_20260924/measurement.json)
has a [completed receipt](B3_GE_E4_PL_G0_F03_Q6_X0_FULL_CERT_20260924/receipt.json)
and checked all 3,289 inverse columns in 823 indexed blocks. It reports:

| Observation | X0 full feasibility |
|---|---:|
| Assembly / certificate | 93.71 s / 198.51 s |
| Complete process-tree time / peak RSS | 293.01 s / 326,852,608 bytes |
| Raw inverse bytes | 86,540,168 |
| Condition upper bound | 624,606.893 (limit 1e10) |
| Amplified backward-error upper bound | 7.459e-10 (limit 1e-8) |
| Certificate result | `CERTIFIED_WITHIN_LIMIT`, **diagnostic only** |

The inverse SHA-256 is
`194784150470b217a30750ad22ac61141d6afb3d24f275534698882f934afcb3`.
The raw 86.5 MB inverse is retained locally in the full-run evidence directory;
the digest and dimensions are in its manifest. It is not a Git-hosted artifact.
The source SHA-256 in `start.json` matches the current exact runner source.

The run used Python 3.14.2, NumPy 2.4.6, SciPy 1.17.1, Numba 0.65.1 and
psutil 7.2.2 on Windows 11, with the five recorded thread variables set to
one. These are **source-process diagnostics**, not installed-wheel evidence.

Independent read-only review confirmed the saved inverse length/hash, column
count, receipt and reported limit comparisons. It did **not** accept numerical
soundness or scientific registration. The diagnostic binds only the runner
hash; it lacks a clean committed candidate, installed wheel/dependency and
Numba/compiler identities, and a saved-only replay. Its child can overwrite
its own files if invoked directly. It checks positive diagonal but does not
perform the independent primal-positivity or full physical Q6 adjudication.
The compiled arithmetic passed additional exact-rational enclosure tests on
bounded subnormal, cancellation and mixed-scale cases. After the diagnostic,
the kernel gained an explicit compiled FTZ/DAZ signature check and nonfinite
output rejection; **the full X0 run used the archived pre-guard kernel**, not
this later hardening. Overflow rejection and full-X0-block parity still
require independent review and broader coverage. The exact kernel and
certificate sources from the full run are archived in its evidence directory.

## Decision and next work

The unchanged Python interval loop is not feasible under the provisional
900-second case budget. The compiled, bit-identical candidate made a complete
X0 certificate feasible within that budget and 2 GiB tree cap. Before
registration: close independent code/numerics review, test the compiled kernel
against the scalar oracle on actual X0 blocks and exceptional arithmetic cases,
bound the X1/X2 resource envelope, freeze exact source/install identities and
archive caps, then implement and review the complete one-use producer and
solve-free adjudicator. A valid X0 certificate alone does not establish
three-grid physical settling, a native multiplier space, or G0 closure.

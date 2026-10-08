# F03 native-line absolute-primal diagnostic

**24 September 2026. Unregistered derivation screen; F03/G0B open and G1
barred.** Source base `da27f268843c5d99ed1fd5cc99156ece11c70ff6`;
screen source SHA-256
`bfb6f4c29cb7b263d2c5b720d0ae93960cb41393ac151a417e0f7de389079cc4`.
The four 12-case raw inventories are [fixed rail](B3_GE_E4_PL_F03_ABSOLUTE_COMPLIANCE_FIXED_RAIL_V1.json),
[fixed local](B3_GE_E4_PL_F03_ABSOLUTE_COMPLIANCE_FIXED_LOCAL_V1.json),
[paired rail](B3_GE_E4_PL_F03_ABSOLUTE_COMPLIANCE_PAIRED_RAIL_V1.json),
and [paired local](B3_GE_E4_PL_F03_ABSOLUTE_COMPLIANCE_PAIRED_LOCAL_V1.json).
They retain the Q4/S3-V2D, P0/P1, 2/4/8-interval, full native retained
coordinate inventory. No installed artifact, independent review or formal
resource receipt is claimed.

The earlier screen used the signed Schur action `C K^-1 C^T` even though its
scaled native retained primal `K` has 144 negative modes in these cases.
This diagnostic replaces only that inverse in the *analysis metric* with
`|K|^-1 = V |Lambda|^-1 V^T`, after a relative-symmetry check. The same
physical constraint rows and H^-1/2 multiplier dual Gram remain. The
smallest absolute primal eigenvalue divided by the largest is
`4.82e-7` for Q4 and `3.38e-7` for S3-V2D; reported action residuals are
below `7e-12`. This positive spectral norm is not the native strain energy,
a production tangent, or a proved continuum inf-sup norm.

Minimum normalized quotients for the fixed 4-shell/16-native-half-cell
primal, rounded to three decimals:

| Shell port / topology | P0 at 2, 4, 8 intervals | P1 at 2, 4, 8 intervals |
|---|---|---|
| Rail / Q4 | 2.963, 2.078, 1.406 | 1.970, 1.387, 0.764 |
| Rail / S3-V2D | 2.959, 2.076, 1.406 | 1.968, 1.386, 0.763 |
| Local translation / Q4 | 3.207, 2.273, 1.576 | 2.184, 1.559, 0.922 |
| Local translation / S3-V2D | 3.112, 2.195, 1.506 | 2.096, 1.488, 0.855 |

On paired refinement (shell 1/2/4, native half-cells 4/8/16 and multiplier
intervals 2/4/8), Q4 rail P0 is `2.303, 1.761, 1.406` and P1 is
`1.006, 0.892, 0.764`. Q4 local P0 is `2.432, 1.922, 1.576` and P1 is
`1.023, 1.062, 0.922`; S3-V2D follows the same directional trend in the
raw inventory. The minimum remains the alternating axial `Fx` channel in
all 48 cases. In the fixed Q4 rail P0 series, its positive-norm beam
contribution falls `2.622 → 1.223` and shell contribution falls
`0.341 → 0.183`. The local origin increases shell compliance but leaves the
falling beam contribution essentially intact.

**Interpretation:** Signed cancellation contributes to the very small
earlier quotient but does not explain the descending axial trend. The
positive diagnostic also declines under fixed-primal and paired refinement.
This is evidence against selecting a multiplier resolution or shell origin
solely from the signed quotient. It does not prove a continuum instability,
locking, or convergence failure; the physical trace norm, finite-width port
regularization, matched loaded response and full F03 acceptance remain to be
resolved. The local-origin candidate remains unselected. The prior axial
loaded-response differences and historical failed references are unchanged.

The three new mathematical/native test functions passed when invoked directly;
the equivalent pytest attempts stalled during collection in this local test
launcher and were stopped without a result. The full 48-case direct screens
completed. The default signed path reproduced all 18 common fields of the
archived Q4/P0/eight-interval V2 row exactly. No formal F03 registration was
consumed.

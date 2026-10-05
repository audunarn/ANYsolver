# F03 axial channel: shell rank and independent bar comparison

**24 September 2026. Unregistered G0B diagnostic; F03 remains open and G1
barred.** Source base `3b04295e0b478aeed8b22acd378eb6a6bda25885`.
The native-screen source SHA-256 is
`57730dcc573440d46918fd0d181645dc958f7acbd268e019e124b3f01f901536`;
the independent bar source SHA-256 is
`38eec30a9cf6fb6fd07992c7168a97269d732204589a11f2ff23cafcd04051be`.
Versioned raw results are [fixed rail](B3_GE_E4_PL_F03_ABSOLUTE_SHELL_RANK_FIXED_RAIL_V2.json),
[fixed local](B3_GE_E4_PL_F03_ABSOLUTE_SHELL_RANK_FIXED_LOCAL_V2.json),
[paired one-per-shell rail](B3_GE_E4_PL_F03_ABSOLUTE_ONE_PER_SHELL_RAIL_V2.json),
[paired one-per-shell local](B3_GE_E4_PL_F03_ABSOLUTE_ONE_PER_SHELL_LOCAL_V2.json),
and the [axial-bar oracle](B3_GE_E4_PL_F03_AXIAL_BAR_NORM_ORACLE_V1.json).
Each native file contains 12 Q4/S3-V2D, P0/P1, three-resolution cases.

## Independent interpretation of the beam contribution

For a unit axial bar with `u(0)=0`, free tip and alternating unit P0 force
density on an even number `m` of cells, equilibrium gives
`EA u'(s) = integral_s^1 lambda(t) dt`. The primitive is triangular on
every cell, with height `1/m`, hence exact unit-EA compliance is
`1/(3m²)`. Five independent piecewise Gauss-work tests passed. Dividing
this exact work by the same analytically constructed Neumann H^-1/2 P0
dual norm used in the native screen gives quotient bounds approximately
`0.32155, 0.18549, 0.10740, 0.06065, 0.03314, 0.01758` for
`m=2,4,8,16,32,64`. A falling **beam-only** contribution under this
particular norm is therefore expected even in a stable, elementary axial
bar. It cannot alone be called an F03 instability.

## Native shell-side rank and response

The native diagnostic retains its physical shell and B3 operators and the
same six-channel weak rows. It evaluates the shell-row SVD after the existing
coordinate and one-metre wrench scaling. Numerical rank uses a declared
`1e-10 × largest singular value` threshold; the deficient Q4 cases have a
gap between retained singular values near `1e-7` and discarded values near
`1e-22`. The shell-only compliance minimum is a separate generalized
eigenvalue in the positive spectral-primal diagnostic norm, not the shell
contribution along the *combined* minimum mode.

At the fixed four-host-interval shell panel and 16-native-half-cell beam
with eight multiplier intervals (two per shell host interval):

| Shell / port | P0 shell row rank | P1 shell row rank | Shell-only minimum |
|---|---:|---:|---|
| Q4 / rail | 42/48 | 42/54 | Numerical zero in both spaces |
| Q4 / local translation | 37/48 | 38/54 | Numerical zero in both spaces |
| S3-V2D / rail | 48/48 | 54/54 | `0.001962` P0; `0.000208` P1 |
| S3-V2D / local translation | 39/48 | 42/54 | Numerical zero in both spaces |

With **one multiplier interval per shell host interval**, all 24 paired
Q4/S3-V2D × P0/P1 × rail/local cases at one, two and four host intervals
have full shell row rank. That is a necessary finite-dimensional check, not
a uniform stability proof. The Q4 shell-only minimum evolves as follows:

| Shell port / space | One, two, four shell host intervals |
|---|---|
| Rail / P0 | `0.717692, 0.111969, 0.002423` |
| Rail / P1 | `0.014346, 0.014505, 0.007538` |
| Local translation / P0 | `0.837076, 0.217912, 0.107852` |
| Local translation / P1 | `0.035089, 0.102737, 0.154012` |

The local P1 sequence is encouraging as a *screen*, while Q4 rail P0 has
a small finest-grid shell-only quotient despite full rank. Three levels,
one flat reference, an exploratory positive norm and no matched loaded
target cannot select a production trace or multiplier space. The existing
local-origin [axial loaded screen](B3_GE_E4_PL_F03_WEAK_LINE_RESOLUTION_DIAGNOSTIC_V4.json)
also changes when intervals rise from four to eight at fixed primal mesh:
Q4 maximum beam `|ux|` changes by `45.17%` for P0 and `7.67%` for P1
relative to the eight-interval result; S3-V2D changes by `63.88%` and
`15.19%`. This does not establish which result is physically right.
Full registered mesh ratios, curved
and pre-rotated references, thickness/shear response, physical convergence,
independent mechanics review and formal F03 execution remain required.

The bar oracle passed **5/5 pytest tests**. Four native mathematical/rank
test functions passed by direct invocation; the local pytest launcher for
that module stalled during collection and was stopped without a result.
The earlier signed path matched its archived Q4/P0/eight-interval result.
No new F03 registration was consumed and no historical failure was replaced.

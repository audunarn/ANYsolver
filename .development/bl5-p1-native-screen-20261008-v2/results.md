# Native BL5 P1-coarse contrast — development screen

The previous `continuous_p1` attempt failed the native-fibre admission guard
before solving. Its [receipt](../bl5-p1-native-screen-20261008-v1/receipt.json)
is preserved. This attempt used the already admitted `continuous_p1_coarse`
space. On the unchanged matched four-edge fixture it supplies 25 five-channel
rows, versus P0's 20. The shell/beam body operator and supports were identical.
Both cases used the exact saved P0 input, CPU0, one numerical thread, JIT off,
and a 2 GiB cap. The [receipt](receipt.json) binds the source and
[station profiles](screen.json). Cumulative process time was 5.69 s of the
120 s allowance; no CalculiX or formal F03 run was made.

| Native load | P1/P0 position-gap RMS | P1/P0 director-gap RMS | P1/P0 sum of absolute local station work | P1/P0 applied work |
|---|---:|---:|---:|---:|
| Fy | 0.597 | 0.864 | 0.340 | 0.9624 |
| Mx | 0.979 | 0.977 | 0.619 | 0.9658 |

The assembled weak constraints remained below `7e-21` and station-to-row work
reconstruction errors below `4e-20 J`. Absolute station work measures
cancellation inside weak rows; it is neither stored energy nor an acceptance
criterion. The enriched space changes Fy local transfer but barely changes the
Mx gaps. P0 resolution therefore cannot be the sole explanation of the Mx
native/resolved mismatch on this fixture. These results neither establish that
P1 is stable or nonlocking nor identify whether body, end traction, root
restraint, or connection modelling dominates the remaining difference.

Decision: stop the isolated P0/P1 comparison. The next physical comparison
must match body, end traction, root support and work-conjugate outputs before
attributing an Mx response difference to BL5. Any candidate multiplier policy
still requires the registered ratios, growing spaces, refinement, mixed-system
and physical-transfer assessment plus independent mechanics review.

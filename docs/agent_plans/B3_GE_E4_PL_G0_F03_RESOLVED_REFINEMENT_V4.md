# F03 independent comparator: joint and one-sided refinement v4

21 September 2026. **Unregistered exploratory result; no F03/G0B
acceptance.** Source and single-use runner commit `b3f532e`. The
exclusive evidence root is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-resolved-refinement-v4/`.
Its manifest records source/runner/dependency identities and the exact
40-case inventory. Raw JSONL SHA-256:
`82d53a2487db070717113c3dd3a87ddc1ae9b21bfa326739784679b8ef449d83`.
The screen took 23.22 seconds in one serial process.

All cases solved with maximum relative equilibrium residual `2.58e-13`,
maximum absolute imposed station gap `7.12e-20`, maximum relative work
imbalance `4.29e-13` and largest polynomial midpoint-fit discrepancy
`6.06e-20`. This confirms discrete algebraic balance, not the continuous
bond or an E4/native-B3 result.

For `N_s=N_y=N_b=16,32,64`, the independent Q4 smooth-load tip displacement
is `2.84222e-5,2.94765e-5,3.11584e-5 m`; S3 gives
`2.81023e-5,2.94749e-5,3.09895e-5 m`. The last-level change does not
establish convergence. For the signed sine load, Q4 gives
`-9.87804e-6,-9.97234e-6,-9.97867e-6 m` and S3 gives
`-9.81041e-6,-9.94368e-6,-9.97286e-6 m`. Thus convergence differs by
load shape and cannot be inferred from sine alone.

The Q4 smooth-load estimated off-station yaw-gap maxima at the three joint
levels are `1.28630e-5,4.86196e-6,3.48964e-6 rad`. These are many orders
above the imposed station gaps, despite decreasing overall. The estimates
search stationary points of the declared cubic/quadratic-minus-affine
discrete field; they are not rigorous floating-point enclosures or gaps in
the full distributed-load particular field.

At fixed `N_s=64,N_y=32`, refining the beam from 8 to 64 elements moves
Q4 smooth tip displacement from `3.08762e-5` to `3.03397e-5 m` and yaw-gap
estimate from `4.54157e-5` to `2.66509e-6 rad`. At fixed `N_s=64,N_b=64`,
refining width from 32 to 64 moves tip displacement back to `3.11584e-5 m`
and the yaw-gap estimate to `3.48964e-6 rad`. This nonmonotone interaction
requires further resolution, not extrapolation to a target.

The finite-station comparator is a different attachment law from the
required exact weak line coupling. The classical Q4 differs from E4-PL's
condensed Q4 at a fixed mesh, and the conventional beam differs from the
native retained B3. A full signed native stability norm, compatible
physical reference and candidate law are still missing. Keep G1 production
integration barred by the G0B foundational gate.

# Prospective density physical-control review V1

Supporting OpenAI Read review only. No numerical execution, imports, tests, solves or qualification adjudication performed. Reviewed the source contract, not the pending worker/driver implementation. Same saved ns64_b1_8 geometry, K6924, physical inventory, loads and root restrictions are prerequisites.

## Exact embedding and physical space

No analytic defect found in the proposed S4 -> S2 embedding. For each coarse support joining equal-length left/right fine supports, with coefficient order (constant, slope), the two E rows on (left constant, left slope, right constant, right slope) are

    [1, 0, 1, 0]
    [-1/2, 1/2, 1/2, 1/2].

Place this pair on each of two coarse supports within each of five channel-major blocks: E is 20x40, rank20. Source row order is exactly channel/support/(constant,slope), assembly lines150-161. The identity follows from phi_coarse=-1/2+phi_left/2 or +1/2+phi_right/2. Native-cell averaging is linear, so it also holds on every unchanged halfcell. Source lines262-269 deliberately use physical native-cell endpoint means, even when shell integration splits the cell; segment midpoints or cell indices would be incorrect substitutes. Quadrature weights at271 and Jacobian accumulation at373-381 must remain unchanged.

The underlying coarse affine polynomial is continuous across each removed fine boundary. The actual registered cell-average density is piecewise constant on native halfcells, and the two coarse supports may jump at their boundary. Do not call this a globally continuous multiplier law. The stated rational E depends on equal physical half-support lengths; a nonuniform trace needs arclength-derived coefficients, not these fixed halves.

Cc=E Cf and lambda_f=E.T lambda_c imply identical virtual work and exerted actions: lambda_c.T Cc q=lambda_f.T Cf q and -Cc.T lambda_c=-Cf.T lambda_f. This direction embeds a newly solved coarse multiplier; it does not represent every existing fine multiplier. ker(Cf) is contained in ker(Cc), so dropping20 rows enlarges the physical admissible space. E rank alone does not certify Cc rank; actual fine rank40 would imply coarse rank20.

## Analytic local derivative and exerted actions

The proposed flat-reference J is correct for local order shell2x6, beam2 translations3+3, retained cellspin3. With d=z, B=[ex;ey], shell weights n, beam weights nb:

- shell translation nI; shell rotation-to-translation -n(t/2)skew(d);
- beam translation -nbI; cellspin-to-translation +skew(lift+arm);
- director shell rotation -n B skew(d); director cellspin +B skew(d).

Local source lines138-155 rotate both frame and lift; frame differentiation supplies the arm contribution. Lines156-170 give director projection and gap ordering. Port source lines134-147 supplies lift/frame pose;149-154 maps the six beam translations and three retained cellspin slots. There is no direct nodal-beam-rotation attachment column. Retained spin must not be identified with nodal rotation or discarded from rigid work.

For exerted -J.T lambda, shell force is -n lambda_t and beam nodal force +nb lambda_t. Shell torque is -n[(t/2)d cross lambda_t + d cross (B.T lambda_d)]; retained cell torque is (lift+arm) cross lambda_t + d cross (B.T lambda_d). Use actual nodal positions plus these couples at one common moment origin. Adding a fictitious nodal beam moment duplicates the retained couple. At straight flat reference with lift0 and arm parallel d, attachment yaw columns vanish; preserving the released root yaw is consistent.

## Required discriminators before interpreting a solve

1. Prove rational E reproduction on every native-cell mean, all five channels and both supports; test arbitrary signed coefficients, slope signs, channel/support permutations and the surviving coarse-support jump. Keep exact-density proof separate from finite binary64 C assembly agreement.
2. Independently reconstruct full Cf from analytic J and the actual slot inventory; compare frozen original C, then direct C8 with E C4 before solving. Compare fixed columns too, followed by identical free restriction. A shared helper can reproduce the same incorrect frame/order twice. Record numerical assembly discrepancies with the existing arithmetic contract rather than asserting exact floating equality.
3. Check arbitrary signed five-channel virtual work and cross-product force/moment balances, including shell top offset, cell arm/lift and the actual retained-spin rigid map. Include fixed-root reactions and full-domain balance. Current lift0 geometry cannot discriminate a missing lift term; either exercise a permissible nonzero-lift control separately or restrict the conclusion to this geometry.
4. Bind unchanged full K/load/geometry/sections/frames/physical slots/fixed tuples and fresh20-row coarse C, preserve all retained variables and failed outputs. Establish actual coarse row rank and solve residual/recovery gates. No fine norm, kernel or beta certificate transfers automatically to the enlarged coarse kernel.

## Meaning of outcomes

A large response change at identical K and load isolates the effect of density resolution; it does not select the correct law or eliminate native beam discretization error. A small change only shows that these loads weakly excite the removed constraint directions. Compliance is monotone under this relaxation only with positivity on the enlarged constrained physical space and accurate matched solves; other response components need not be monotone. Failed numerical gates are unresolved evidence, not automatically physical formulation failure. This control supplies no new norm/stability/uniform-convergence, external-validation or F03 acceptance.

Source hashes (SHA256): assembly b6420a02dcb478020e4887f266890c8fcd2f665f8c7f31cb5cd0c6b73ee5942e; BL5 local 2e5bbcd493a4c423243f01d632943ed4a97e20099044df83f684e54ae2cdb738; native port 91ab352e19d6751879efbe2f2318d82abdd97f9b458e0685ceec16d0abef4c61.
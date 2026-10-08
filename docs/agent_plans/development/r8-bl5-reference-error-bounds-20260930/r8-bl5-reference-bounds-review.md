# Independent complete reference-bound development review

2026-09-30. Disposition: clear for this fixed flat, straight, zero-lift reference-bound slice. No missing whole-action proof or consequential bound/sign/source-binding defect was found within that scope. The mathematical bounds are exact-arithmetic statements; their retained evaluations use ordinary floating point. This is not formal reference acceptance, native beta, F03 or M2 acceptance.

Reviewed scripts/b3_e4_bl5_modal_reference_dev.py and scripts/b3_e4_bl5_reference_accuracy_dev.py, the unchanged auxiliary-norm helper, independent TEMP/r8-bl5-beam-dual-error-bound.md, modal V1 controls and final TEMP/r8-bl5-reference-accuracy-v1 source/result/execution/previous artifacts.

## Modal shell bound

For the area-normalized H1 norm, supported x=0, natural x=L/y=W and a boundary line at y=0, k_n=(n+1/2)pi/L. The previously independently derived single-mode weight is L²W/[2 ell² alpha_n tanh(alpha_n W)], alpha_n=sqrt(1+ell²k_n²)/ell. This is a line-source weight, not a volume-forcing weight.

A P0 density has coefficient c_n=2/(L k_n)[p_0+sum_j(p_j-p_(j-1))cos(k_n x_j)], since cos(k_n L)=0. With Dp=(p_0,p_1-p_0,...), Cauchy gives c_n² <= 4 count ||Dp||²/(L²k_n²). Using alpha_n>=k_n, decreasing coth and sum_(n>=N)(n+1/2)^-3 <= (N+1/2)^-3+1/[2(N+1/2)²] proves the implemented tail majorant proportional to D.T D. Thus the positive finite modal sum plus tail majorizes every admitted P0 action; the proof is not restricted to tested loads.

Modal V1 retains positive finite Grams, sine-projection controls, nonuniform 1024/4096-mode Loewner comparisons and m/mm congruence. Under length re-expression by s, the scalar Gram scales by s² while physical density scales by 1/s, preserving squared-force dual energy. The helper SHA256 is 27146976c131a3a72d18bf88c2609acf41bb01958c51e3abc5e52a3c2528b654. Its executed modal V1 source and the accuracy snapshot are identical.

## Beam residual and whole-action bound

Let k=ell²/L, r=(U_h-Abar Theta_h)/L-f and sigma' = r, sigma(L)=0. The implemented backward recurrence sigma(a)=sigma(a+d)-d r_0-d² r_1/2 has the correct sign and preserves flux continuity. No root flux condition is needed because admissible virtual translation vanishes there. Integration by parts gives
R(V,Psi)=integral(sigma-k U_h') dot V' + sum delta_j dot Psi_j,
delta_j=m_j-C_j Theta_h,j+D_j U_h.
No separate derivative-jump term is needed; the continuous equilibrated flux already carries that residual.

The physical norm bounds k||V'||²+sum ell²h_j/L |Psi_j|² from below, including the fixed finite-width covariance. Cauchy consequently bounds the exact error energy by L/ell² times the squared flux-mismatch integral plus sum L/(ell²h_j)|delta_j|². The code retains the actual rotation-equation residual, not an assumption that it is zero. Its mismatch is quadratic on each existing subinterval; three-point positive Gauss integrates the quartic all-column Gram exactly in real arithmetic. P0 force/cell boundaries align with the declared auxiliary subintervals. Integrated cell moments retain N m units, without an additional division by cell length.

For any approximate field, Eminus=2F(w_h)-h(w_h,w_h) satisfies Eexact-Eminus=||R||_*². The implemented lower matrix B.T Z+Z.T B-Z.T H Z is this variational functional for every action combination, so an exact Galerkin solve is not required for the mathematical bracket. Flux and delta cross-products form the complete error Gram. Adding independent shell/beam lower and upper forms and comparing their error Gram against the SPD lower Gram yields an all-action Loewner bound, not seven separate scalar certificates.

Constant-force and nonzero-arm/finite-width manufactured controls have correctly derived representers, physical force integrals and cell moments; their exact energies lie inside every retained 2/4/8-subdivision bracket and the estimator contracts as required. Retained root cell rotations are free. The norm remains an auxiliary kinematic form, not mechanical K.

## Saved physical actions and numerical evidence

The 40-column force-equivalent basis applies lambda=Q mu with Q=diag(1,1,1,ell,ell). The hardcoded flat-frame exerted loads agree with the prior independently checked map: beam arm -0.05 e_z, shell arm +0.0175 e_z, director couple (-lambda_d1,lambda_d0,0), opposing domain signs and two shell tangential rotations. Forces are densities; beam moments are integrated over each fixed halfcell. The full 40-column bound covers all combinations of this declared P0 physical-action basis. It imports no native C or native spectrum.

The final accuracy runner and current worktree script are byte-identical, SHA256 490b086def5b96d216744bd02dd0b67b4db5bef91fa9fa9df5fa2ef6c9df8ba2. The copied original action source matches prior source SHA256 41980598708a8c80722691b3fe31fb6aba66af5a532a2389740e44059b9c7506. previous.json is byte-identical to native-reference V3 result, SHA256 f9e3d314959498815b7aee229535aab80c45d787d5e528effda441be5e4d44d2. Frozen norm/modal helpers match current source.

Final execution records exit 0, one-thread BLAS pools, Python 3.14.2/NumPy 2.4.6, 0.4740196 s and sampled process-tree peak RSS 61415424 B. The fixed 40-column reference computation stops at the first prescribed beam subdivision 8: beam relative bound 0.0037861693, total shell-plus-beam relative Loewner bound 0.0006242892, below the preset 0.001 reference-development budget. Shell modal tail relative bound is 1.3696733e-5. This stop inspects reference error only, not native beta or a candidate admission floor.

Independent reconstruction of all seven saved actions from the retained 40x40 matrices agrees with stored brackets within 2.22e-15. The old mixed shell dual has estimated relative error bracket 0.00268572–0.00268712; the old mixed total bracket is 0.00082183–0.00084463. Thus the preceding 0.002105 enrichment increment was not itself an error bound. These numerical brackets inherit ordinary floating-evaluation limitations.

No outward rounding, interval arithmetic or rigorous accumulation/conditioning enclosure is implemented. Small matrix asymmetry (about 1.34e-15) and linear residuals are numerical diagnostics, not a certified enclosure of roundoff. The analytic residual/tail majorants are sound; formally calling their rounded outputs rigorous would require a separate floating-error argument.

General ratio/support/chart coverage, physical multiplier quotients and mechanical kernel/stability remain separate obligations. No native beta, new spectrum, mesh, solve or source edit was performed by this reviewer. Only this consolidated review file was written.


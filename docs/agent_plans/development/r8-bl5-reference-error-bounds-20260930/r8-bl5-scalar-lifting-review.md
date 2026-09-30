# Independent review: scalar lifting development slice

**Disposition:** no consequential source or analytical defect found in the stated boundary-line, flat supported finite family. The positive-reference construction can support a prospective product floor once its stated binary64 error treatment is retained. The printed final digits are not an outward-rounded mathematical certificate. No native GE beta, mechanical stability or qualification has been examined.

## Exact reviewed identities and inventory

Reviewed worktree HEAD: 7cb1b16c539a5a5b40b0f4f915407f2cf69dcdce. Current scalar script and saved V2 run_case.py are byte-identical, SHA256 35bac628ec57b75fbfda8875d24c09b89e7b0cc4c1f8d5dee4b177e881c2575c. Reused sources reviewed independently:

- modal reference: 27146976c131a3a72d18bf88c2609acf41bb01958c51e3abc5e52a3c2528b654;
- scalar/beam norm helper: 5f89c1e917ff9c018eff4acb71f5b2c067700134952637ea4638f579c2372324.

V2 result/execution record completed 21 c2 policy instances: seven HALF-CELL:shell ratios at each (nx,ny)=(16,4),(32,8),(64,16), plus the saved (8,2)/16-halfcell anchor and three deficient controls. The 21 instances contain nine distinct scalar (nx,ny,support-count) configurations; coincident support spaces at several beam ratios correctly reuse the same scalar mathematics. V2 sampled process-tree execution: 0.592591 s, 75,907,072 B, exit zero; both recorded OpenBLAS pools have one effective thread.

V1 failure remains preserved, including its traceback and failed execution status. The V1/V2 script diff adds only deterministic modal counts 4096/8192/16384 until the existing 1e-3 relative Loewner-tail budget is met. The failing V1 path was the deficient-control list, not a native GE solve. All 21 V2 c2 instances use 4096 modes; the 64-support deficient case uses 16384. This is reference truncation repair with no tolerance relaxation or candidate tuning.

The saved runner imports reused helpers from the configured environment; result/execution do not themselves record their source hashes. The hashes above identify the sources reviewed now. Retain those helper identities/source provenance with the archived run rather than imply the saved top-level script alone binds them.

## Scalar boundary space and exact moments

The actual space is Omega=(0,L)x(0,W), L=1 m, W=.2 m, ell=.4 m. Root x=0 is Dirichlet at every y node; other edges are natural. The coupling line is the **boundary y=0**, matching the coherent native fixture and work-map source. This differs from an interior centerline norm convention.

shell_scalar constructs the exact tensor-product Q1 mass plus ell² gradient norm, divided by L W. x varies fastest in its node layout. The line action selects the first y row and splits each P0 support at all x-element boundaries. Midpoint integration is exact on every subinterval because the Q1 boundary shape functions are linear; removed root entries are zero test traces, not missing work. Complete uniform supports and alignment are checked. c2 yields at least two shell intervals per support for every recorded ratio, including beam-coarse span=1 cases.

## Variational lower and modal upper

For physical line-action matrix A and supported scalar norm H, the exact discrete Gram is G=A^T H^-1 A. For any computed Z,
\[
 G-[A^TZ+Z^TA-Z^THZ]=(Z-H^{-1}A)^TH(Z-H^{-1}A)\succeq0.
\]
Thus the script's symmetric lower_discrete is an analytical variational lower bound even for an inexact solve. Its positivity is essential and is checked. Recorded c2 Gram minima remain positive; maximum condition number is 101.55. Worst inverse/eigen normalized residuals are approximately 3.96e-14 / 1.76e-15.

The modal helper uses k_n=(n+.5)pi/L, appropriate to the supported/natural x endpoints, and alpha_n=sqrt(1+ell²k_n²)/ell. Its boundary-line weight
\[
 L^2W/[2\ell^2\alpha_n\tanh(\alpha_nW)]
\]
is correct for the area-normalized scalar norm and natural opposite y edge. Do not substitute the interior-line half-width Green factor.

The exact P0 sine coefficients are 2/(L k_n) times the cosine endpoint differences. Writing their numerator as p_0 plus interior jumps times cosines gives the count*||D p||² Cauchy bound. alpha>=k, monotone coth, and
\(\sum_{n=M}^\infty(n+.5)^{-3}\le(M+.5)^{-3}+[2(M+.5)^2]^{-1}\)
give the implemented PSD tail matrix. The finite sum plus that tail is an all-combination reference upper bound; it is not merely a selected-load check. The first omitted mode is correctly M+.5. Maximum recorded c2 relative tail bound is .000924312, within the preset .001.

Therefore the largest generalized eigenvalue of (modal_upper, lower_discrete) analytically bounds C_S² from above. The scalar minimum-energy moment lifting preserves every admitted P0 combination.

## Product interpretation and remaining limits

The scalar C_S applies equally to v3 and eta2 because director norms carry the common ell² factor. These are spatial rx/ry fields, not the stored director multiplier components. Root support and the y-uniform beam-translation extension match. Retained cell Theta is unchanged and remains independent/free in the auxiliary space; absent-coordinate quotient checks and actual mechanical KKT constraints remain separate.

The declared .05 m normal arm and .1 m symmetric beam width give rho²=.03125 and K=2. The reviewed product bound consequently reduces here to C_product²=4 C_S². Maximum c2 C_S² is 1.3506153707897066, producing the saved finite-family prospective floor .43023343738364606. The anchor C_S²=1.326040314714624 gives floor .4342018209084961. These cover this exact finite family and norm declaration; they are not a uniform refinement theorem or authorization to change width/ell/supports.

Deficient one-shell-interval controls give C_S² approximately 167.23, 667.44, 2666.57. This is a meaningful canonical lifting contrast consistent with the independently derived alternating-mean obstruction, and it does not indicate physical mechanical failure. Strictly, growth of an upper bound alone does not prove growth of the exact constant; a lower Rayleigh control or a bounded upper/lower gap would establish that stronger statement. The tail is small and solve residuals are small, but neither should be relabelled a mechanical eigenmode.

The variational and tail inequalities are mathematically valid; binary64 assembly, summation, symmetrization and generalized eigenvalues are not interval enclosures. The 1e-10 residual gates alone do not bound every last digit or prove a rounded eigenvalue is an upper bound. Freeze source/formulas, raw constants, family and numerical error policy prospectively. For a guaranteed acceptance floor, propagate arithmetic/eigensolve bounds conservatively (or state a justified numerical margin) before native values, rather than treat the raw printed floor as exact. No arbitrary beta/p-slope threshold follows from this review.

Read-only review; only this note was written. No numerical jobs, candidate spectral inspection, product edits or F03 authority consumption.

## Applicability correction: V2 anchor and V3 supplement

The earlier review's identification of the V2 anchor as the saved work-map fixture was incorrect. Root identified the mismatch before any native GE beta execution. The saved original reference_actions source declares NS=8, NT=2, NB=16, C_LAMBDA=1: span=ceil(16/8)=2, eight supports, **one shell interval per support**, and 40 five-channel density basis actions. V2's mislabeled saved_work_map_anchor instead used coefficient 2: span=4, four supports, two shell intervals per support, and a different 20-dimensional density space. Matching NS/NB alone did not bind the actual basis/support space.

The V2 anchor value .4342018209084961 applies only to that hypothetical c2 fixture. Neither it nor the c2 finite-family floor .43023343738364606 may be assigned to the saved c1/40-action fixture. This supersedes the anchor-applicability statement above while preserving its original source/results/history. The 21 c2 policy instances and their analytical construction remain unchanged.

Reviewed V3 supplement: TEMP/r8-bl5-scalar-anchor-correction-v3/run_case.py invokes only lifting_case(8,2,16,1) and checks span=2/supports=8. Its previous.json is byte-identical to V2 result.json, both SHA256 0c83f708ad726e2237f7b02b5d559124740f53357fa91caed035455cbe50cb98; the V3 result records that same binding. Thus the unchanged 21 c2 instances are reused, not rerun or overwritten.

Current scalar source differs from saved V2 run_case only in the anchor coefficient and explanatory comment; its new SHA256 is 7aaab9732dc77a4b135c9f300b4c94f85d2b5a0f73d7ca90be2c5f50b45f4a41. The V3 recorded corrected anchor has C_S²=42.31004089889378 and product squared bound 169.24016359557513, giving the computed finite-anchor floor **.07686847794073282**. It uses 4096 modes, tail bound 1.369673255741123e-5, positive Gram minimum .0001262729220545402, and inverse/eigen residuals about 1.03e-15/8.80e-15. Execution passed, .4853423 s, sampled process-tree peak 57,974,784 B; both recorded BLAS pools have one thread.

This lower finite-anchor value is a reference lifting result for its actual one-interval support space; it does not admit c1 into the frozen c2 family or establish uniform one-interval stability. The prior binary64/error-policy limits remain in force. Any prospective native comparison must bind coefficient, span, complete support endpoints/membership, basis dimension, geometry, norm and supports before selecting its applicable floor. No native GE beta, mechanical acceptance, formal F03 execution or authority consumption occurred in this correction.

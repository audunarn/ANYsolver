# Prospective finite-domain floor — independent review

2026-09-30. Disposition: the proposed independent scalar-lifting route can supply prospective case floors and a finite-family absolute floor without circular use of GE beta. This is a numerical-contract review only: no scalar cases or native spectra were executed here, and no F03/M2/native acceptance is asserted.

Read the product transfer derivation TEMP/r8-bl5-product-fortin-transfer.md (SHA256 c18feceb4687da7622ac000776a0fe17a8892649e0d54a74a0508edc0edfc742), the physical trace-norm declaration and R8 §4.5. The governing contract expressly permits numerical evidence over a registered domain without a universal h-uniform proof or certified infinite-refinement tail; it also requires floors, admissibility and deterioration rules to be frozen independently before candidate assessment.

## Scalar lifting and product equations

For the supported scalar bulk norm H_S, P0 boundary-line moments T and actual native supported Q1 restriction H_h/T_h:
M_0 = T H_S^-1 T.T,
G_0 = T_h H_h^-1 T_h.T.

If G_0 is SPD, the minimum-norm moment lifting
Pi_S u = H_h^-1 T_h.T G_0^-1 T u
preserves every declared P0 moment and has squared operator norm
C_S² = maxeig(M_0,G_0).
These are independent scalar shell operators with the physical bulk norm and boundary-line functional. They are not the GE five-channel candidate spectrum and do not replace M_0 by a candidate normalization.

For any numerical inverse-action matrix Z, the variational form
Gminus = T_h Z + Z.T T_h.T - Z.T H_h Z
satisfies G_0-Gminus=(H_h^-1 T_h.T-Z).T H_h (H_h^-1 T_h.T-Z) >= 0 in exact arithmetic. Thus independently derived Mupper >= M_0 and SPD Gminus give the conservative scalar constant
C_S,upper² = maxeig(Mupper,Gminus).
Retain complete action cross-products; selected load energies are insufficient. Disjoint interior trace tents on the aligned supports spanning at least two shell intervals justify scalar row independence for this domain.

For the checked flat/root-compatible product map
P(U,Theta,v,eta)=(0,Theta,Pi_S(v-EU),Pi_S eta), E U(x,y)=U(x),
all force, director and arm moments are preserved. With rho=max_surface|a|/ell and K=max(2,1+2rho²), the reviewed sufficient constant and floor are
C_product² = max(2 C_S,upper², K max(2 C_S,upper²,1+rho²)),
beta_floor = 1/sqrt(C_product²).

The repeated C_S,upper² denotes the scalar squared constant, not its fourth power. The transfer uses the same root trace on shell and beam, free independent retained cell rotations, constant frames/arms, zero reference lift and the declared physical widths/norm factors. Its floor concerns auxiliary coupling on the verified physical multiplier quotient. It does not establish stability of actual mechanical KKT or justify removing native fields merely because C annihilates them.

## Domain and prospective freeze

Ratios explicitly mean native HALF-CELL:shell-trace segment. I identified that the initially proposed nx=8, ratio 1:8 would give one halfcell and violate the existing even-at-least-two BL5 admission. Root corrected the finite family prospectively to nx=16/32/64, ny=4/8/16. All seven ratios 1:8,1:4,1:2,1:1,2:1,4:1,8:1 then have even halfcell counts >=2. The fixed complete rule is span=max(1,ceil(2*nbeam/nshell)); these supports align, divide the trace and span at least two shell intervals. The saved nx=8,ny=2,halfcells=16 model remains an additional applicability anchor, not a fourth refinement campaign. The next computation is a scalar primitive family only until actual GE fixtures/work maps satisfy the transfer hypotheses.

A varying case-specific sufficient floor is not circular when it is produced solely by this fixed independent geometry/norm/lifting calculation before inspecting GE beta. Freeze the complete case table and its envelope minimum beta_star=min_case beta_floor as the finite-domain absolute floor. Also freeze the scope, support inventories, ell/width/arm bound, Mupper tail settings, complete Gminus construction and numerical budgets before candidate spectra. Changing those to improve an observed candidate result would be tuning.

Report raw beta and the signed R8 deterioration measure p=log(beta_coarse/beta_fine)/log(h_coarse/h_fine). A changing floor or beta/beta_floor normalization must not hide raw deterioration. The floor table alone does not bound the ratio of two actual beta values; allowed deterioration is a separate prospectively justified predicate. This finite-family route does not claim behavior outside its registered meshes/ratios or introduce a universal-proof gate.

## Binary64 checks and limitations

Use effective settings, complete supported physical line integration, symmetry/positive-definiteness checks, inverse residuals, conditioning and generalized eigen-residuals. Retain equivalent-unit/basis controls and resolved/deficient scalar controls. Justify and freeze comparison tolerances/margins from those independent controls and numerical budgets before GE evaluation; do not enlarge them after an unfavorable beta. If conditioning prevents the declared budget being resolved, report that case unresolved rather than discard eigenvalues or silently lower its floor.

The analytic Loewner identities/tail majorants justify this prospective finite-domain numerical route. Binary64 values with checked residuals/conditioning are ordinary numerical estimates, not outward-rounded intervals. No new exact-arithmetic or interval-certification gate is required for the authorized R8 numerical-evidence route; equally, its outputs must not be labeled formally certified roundoff enclosures.

Whole-space work/Q/unit/frame applicability, actual unsupported/null modes, mechanical kernel, locking and physical accuracy remain separate obligations. Only this review file was written; no numerical jobs, source edits or native spectra were performed.


## Complete-slice prospective freeze review — 2026-09-30

Read the full prospective appendix to B3_GE_E4_PL_M2_TRACE_NORM_CONTRACT_DEV.md (SHA256 b1d12101fd71be1cb8a3418f9808b7eb83f06e21d615bda1b598635bca02484c), the independent scalar-lifting review including its V3 applicability correction, and the deterioration addendum. Disposition: no material incorrectness blocks this limited development freeze.

The fixed 21-case c2 family and 16/32/64 shell grids preserve even >=2 native halfcells and aligned two-or-more-shell-interval supports. Actual GE work/norm/support correspondence is explicitly a prerequisite, not claimed established by scalar source. The old 8x2/16-halfcell 40-action c1/span2 anchor is outside the family; its corrected raw floor is 0.07686847794, not the c2 envelope. This corrects any broader reading of the earlier generic anchor statement in this review.

If M<=Mupper<=(1+0.001)M and the product argument yields beta_M>=f_raw, then beta_Mupper>=f_raw/sqrt(1.001). Reserving the declared 1e-6 beta arithmetic budget gives the stated safe case floor. The reported envelope 0.430233437384 becomes approximately 0.430017481869; the prospective absolute 0.43 floor is below it. This is a fixed conservative margin/rounding before GE values, not a fitted cutoff.

The 1e-10 inverse/eigen/symmetry checks, positive complete Grams and <=1e4 conditioning gates, together with the substantially smaller recorded scalar errors/conditioning, are a reasonable prospective binary64 budget for this bounded development route. They are not an interval certificate or an automatic proof of a 1e-6 bound for every future GE computation. Root's pending actual GE check must verify aggregate numerical uncertainty fits that reserved budget and the reference majorant budget; if not, mark the case unresolved without increasing tolerances or lowering floors. No additional exact-arithmetic gate is required here.

The ceiling p<=log((1+1e-6)/f_safe_fine)/log2 is the correct numerical form of the independently implied noncollapse rule. Its explicit redundancy, allowance for substantial decline and exclusion of convergence/h-uniform/mechanical acceptance are accurate. Raw beta and p remain visible; case-floor normalization cannot hide deterioration.

The appendix therefore freezes a defensible finite-family development comparison, conditional on its stated applicability and numerical checks. It does not freeze full qualification or claim GE results already exist. No numerical jobs, native spectra or source edits were performed for this addendum. Only this existing review file was appended.


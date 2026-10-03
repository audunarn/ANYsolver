# Supporting sparse envelope kernel review V2

Scope: read-only source/evidence review in C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001. No numerical job, test, worker or Git operation was run by this reviewer. This is supporting OpenAI input, not different-family scientific acceptance, engineering qualification or formal F03 authorization.

## Verdict and blocker

The mathematical pullback/error/congruence chain has no identified false-positive defect within its stated ordinary IEEE arithmetic assumptions. Current admission is nevertheless blocked by a concrete manifest-schema error: sparse_envelope_kernel_dev.py:159–166 accesses previous_manifest_sha256 in v7. Frozen raw-manifest-v7.json instead declares schema BL5_DEVELOPMENT_RAW_EXTENSION_V7, previous_manifest=raw-manifest-v6.json and previous_sha256=c5723a6a294390f2ec1d6b10e114f0f1bc1198fd4686007a33457567cd702249. The current caller will raise KeyError before certification. Use an explicit validated v7 schema/name/digest branch; preserve the historical files. Test the actual chained manifest parser, including an altered predecessor digest. This finding was sent immediately to the root owner.

The four manifests contain 999 distinct file bindings with zero conflicting repeated bindings. All nine files for each of the three older canonical owners (ns16_b1_2, ns16_b2, ns32_b1) are present and match their frozen digests. The new direct state binding at lines183–193 fixes the earlier mutually-consistent mutable metadata/NPZ admission gap, once the chain parser works. Live local sign-proof records and pivot endpoints at102–150 fix the earlier failed-evidence retention gap.

## Mechanical target and proof scope

Partition/support construction at49–99 preserves all physical roles, actual18/member resultants, complete free/fixed inventory and ten quarter pivots per support. stationary at123–151 checks exact zero Cpp and off-block Kpp and retains both Kxp and Kpx. For saved real operands L=[I;-D^-1Kpx], K L has zero resultant row; consequently L.T K L=Kxx-Kxp D^-1 Kpx even when K is slightly nonsymmetric. No full mixed-K SPD assertion is made.

Local negative work at102–120 proves the explicit lower completion of -D minus twice its bounded discrepancy positive, with outward Decimal elimination; this transfers negative symmetric work to actual saved D. Inverse/lift errors are separately enclosed in sparse_kernel_saved_dev.py:228–265. Complete graph construction at172–225 certifies all rows and unique pivots, rejects foreign pivot coupling, includes boxed nonzero support, and bounds the actual graph using local inverse residuals. It therefore covers the complete actual constrained space, rather than just observing a small C Z residual.

Caller249–276 carries row/physical scaling, exact chosen stored positive T, T-scaling error, graph error, Schur error, sparse products and lower-completion discrepancy. If the representative minus shift I is certified SPD and epsilon bounds its difference from the exact constrained pullback, down((shift-epsilon)/G) is a valid lower bound with G >= ||Z_true T||2². The numerical lower bound at290–293 refers to the dimensionless scaled physical coordinates (physical slot vector y=diag(physical_scale)x). It is not a lower eigenvalue in unscaled Euclidean physical slots or a canonical L2 inf-sup bound. Positivity transfers by invertible congruence; native inf-sup, uniformity and physical approximation remain separate.

## Proposed tighter stationary bound

The weighted-incidence bound is valid without symmetry. If local errors E_j are embedded only on I_j x I_j and ||E_j||2 <= delta_j, then for any u,v,

|u.T sum(E_j) v| <= sum delta_j ||u_Ij|| ||v_Ij|| <= sqrt(sum delta_j ||u_Ij||² sum delta_j ||v_Ij||²) <= max_i sum_{j:i in I_j} delta_j ||u|| ||v||.

Use the union of both actual Kpx and Kxp neighbour sets, formed before any rounded scaling/products; empty supports contribute nothing. Existing local Frobenius bounds safely upper-bound each local induced norm. Accumulate positive delta_j values outward per coordinate and take the maximum. Keep base scaling, independent-reconstruction assembly and reconstructed-versus-original-Shat discrepancy as separate terms. The resulting sum-local bound is induced2, not Frobenius: do not retain stationary_operator_error_fro_upper or otherwise claim a Frobenius bound for it. Save actual neighbour indices/incidences and each delta for audit.

For assembly, a canonical base and one canonical unique-entry update per member imply each entry receives no more nontrivial additions than its actual member incidence. Missing entries and addition to exact zero do not incur new rounding error under ordinary IEEE binary64 arithmetic. Dropping a cancellation zero does not erase earlier error or reset the contribution count. Count from complete original neighbour supports, never from final nnz or nonzero rounded update products. Apply the same conservative gamma envelope to the signed reconstruction and positive absolute accumulator; keep its denominator correction. A conservative unchanged-form gamma(2*(1+max_incidence)) can replace the total-block count under these conditions.

Local SciPy1.17.1 _compressed.py:1189–1222 dispatches csr_plus_csr and returns/prunes CSR storage. Its compiled C++ implementation is not supplied locally, so I have not verified its exact operation sequence. This recommendation has the same conditional ordinary IEEE sparse accumulation scope explicitly stated by sparse_product at113–119. Require canonical duplicate-free updates/accumulators; do not let sum_duplicates add an uncounted reduction. Add exact Fraction controls covering repeated cancellation/disappearance/reappearance, disjoint supports, overlapping nonsymmetric local errors and zero updates. A NumPy FTZ/DAZ check is evidence of the observed arithmetic state, not a universal backend proof.

## Evidence actually read

Original focused suite test-v1: 58 passed in0.94s, supervised exit0. Guard/retention tests test-v2: 32 passed in0.60s, supervised exit0, elapsed1.027s, sampled peak86,937,600 bytes and numeric-or-unresolved maximum1. The latter covers direct frozen-pair mutation and retained failed sign proof, but does not exercise the actual manifest chain; therefore it missed the blocker above.

Three terminal screens used predecessor caller8021f614..., not current bd52d438.... Their paired NPZ hashes match recorded JSON hashes. All27 frozen state/action files independently match the manifest records:

- ns16_b1_8: positive; physical517/kernel507, epsilon3.1137706649e-10, scaled physical lower1.4849624386e-11, caller0.588s/supervisor1.02s.
- ns32_b1_8: positive; physical1801/kernel1781, epsilon8.8389328097e-10, lower2.9530920865e-11, caller2.119s/supervisor2.62s.
- ns16_b8: HOLD; physical2785/kernel2745, epsilon8.0507398259e-8, stationary contribution7.6192729001e-8, graph4.3076847418e-9, caller25.074s/supervisor25.59s. Decimal shifted representative is NONPOSITIVE_REPRESENTATIVE. This does not establish actual-law failure.

The saved representative-only zero-shift probe also HOLDs after2197 recorded pivots (stopping index2196 of2745). It supplies no positivity claim and does not justify reducing epsilon. Earlier HOLD/failure artifacts remain intact.

Budgets are explicit: input25068/4m nnz, graph15745/2m, proof15585/1.5m pattern/50m updates/768MiB and450s, local-column384, local inverse/resultant18 and neighbourhood24. Effective library pools in screens are1,1; external supervisor remains600s/1GiB and limit8 numerical threads. Internal elapsed check at224–230 does not bound opaque native calls or final save duration; supervisor supplies the global ceiling. No resource savings or larger-case success is inferred.

## Reviewed hashes

- caller bd52d4387fdcebac8c6502ef2304589bd5b798a65f763fa31636ba663ba628e9 (blocked v7 parser)
- saved primitive 064a0d8d36dca6db916d9a8eb2563620cf8c72cb82920bd4dc0c7182b6d1c138
- interval primitive 47adfa44533b08c33aac8879d231b63d1b900ac2b50cf7d9e3427b52428d0199
- caller tests 7ddd04dfb7676e3528f81db53bef48257b27268e0be1c08b9a1a0f579340c896

Any subsequent guard or incidence implementation requires a source-specific delta review; these prior screens must retain their original source identities.
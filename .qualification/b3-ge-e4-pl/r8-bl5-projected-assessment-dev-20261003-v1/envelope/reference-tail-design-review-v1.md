# Uniform-reference tail design review v1

Supporting independent OpenAI mathematical Read review. No numerical jobs/tests, source edits, Git operations or workers were launched. This reviews the proposed theorem, not the forthcoming optional helper implementation or a new registration verdict.

The proposed exact-real uniform-tail theorem is correct under its stated complete P0 uniform partition and unchanged half-integer sine modal equation. No rank or sign restriction on the projection is needed. Its implementation must gate exact uniformity and distinguish exact mathematics from binary64 diagnostics.

Let N>=1 be the number of P0 cells, x_j/L=j/N, n integer>=0, v_n,j=cos((n+1/2)*pi*j/N), j=0,...,N-1. For any integer starting M, not only M divisible by2N,
sum(n=M,...,M+2N-1) v_n v_n.T = N*(I+e0 e0.T).

Proof: product-to-sum reduces each entry to finite sums of cos((n+1/2)*pi*(j-k)/N) and cos((n+1/2)*pi*(j+k)/N). Over2N consecutive integers, all nonzero frequencies m with |m|<2N sum to zero by the roots-of-unity geometric series. Difference frequency zero occurs at j=k; sum frequency zero occurs only j=k=0. Hence diagonal entries N except entry00=2N, with all off-diagonal entries zero. This identity survives arbitrary starting phase M.

Define J=DP, where row0 is P0 and subsequent rows are P_j-P_(j-1). The terminal term is absent because cos((n+1/2)*pi)=0 for the unchanged modal equation. The exact density coefficient is (2/(L*k_n))*v_n.T J. With k_n=(n+1/2)*pi/L, alpha_n>=k_n and decreasing coth,
omitted modal work <= A*sum(n>=M)(n+1/2)^-3 * J.T v_n v_n.T J,
where A=(2W/ell²)*coth(k_first*W)*(L/pi)^3, k_first=(M+1/2)*pi/L. A excludes both N and the series bound; no extra/missing L or W factor is needed.

For a=M+1/2>0 and block r of2N modes, the scalar weight is at most (a+2Nr)^-3. Each outer product is PSD. Applying the block identity then the decreasing-series integral test gives
tail <= A*N*(a^-3+1/(4N*a²))*(J.T J+J0.T J0).
Indeed sum(r>=0)(a+2Nr)^-3 <= a^-3+integral(r=0..infinity)(a+2Nr)^-3 dr = a^-3+1/(4N*a²).

This is a Loewner inequality. Arbitrary real signed, mixed, zero, duplicated or rank-deficient P remains admitted by congruence; no cancellation-based scalar sign argument is used. Rank deficiency may make the relative tail diagnostic unavailable, but does not invalidate the absolute tail theorem. J0.T J0 is essential: omitting it incorrectly halves the uniform block bound for the initial-jump direction (N=1 already gives a counterexample).

Required gates and limits:
- N is the actual cell count, and both endpoints and EVERY stored knot must satisfy exact rational Fraction(float(x_j))/Fraction(float(L))=j/N. Floating allclose or a nominal linspace flag is insufficient. Dyadic registered L=1 grids and their exact representable1000-unit counterparts meet the intended mathematical rule; do not infer this for arbitrary input.
- Keep complete2N blocks, with first omitted index M and a=M+1/2. No start-multiple restriction is needed; truncating a partial block under the same exact Gram identity is unsound.
- Preserve the half-integer spectrum, terminal cosine-zero identity, positive L/W/ell, actual original jump count, and existing finite mode/cell/column/resource limits. Different boundary conditions or nonuniform knots require the old applicable bound or unresolved status.
- The theorem's weights are bounded monotonically; it is unnecessary and potentially wrong to equate a weighted block Gram with its unweighted exact identity.
- No new native data, larger modal count or relaxed1e-3 criterion is required by this derivation. Version the optional preparation and retain both initial failures and19 earlier registrations.

Finite arithmetic scope is consequential. Fraction uniformity validates the stored geometry, not computed trig phases. Binary64 pi/cos/tanh, jump subtraction, matrix products, prefactor/series evaluation and modal Gram accumulation are not automatically outward enclosures. The exact-real theorem alone therefore does not prove an exact-real lower/upper sandwich around rounded arrays. A new helper may retain the existing declared development numerical scope and residual/condition/arithmetic checks; it must not label those rounded diagnostics a rigorous interval/rational certificate. Such a stronger claim would require explicit rounding error enclosures, including the finite modal lower Gram and the computed tail, or an exact/directed construction. Small dense or sampled modes cannot replace this distinction.

Relevant preserved source equation: scripts/r8_bl5_projected_modal_envelope_dev.py74–93, pinned SHA6d534e8319c3b86b4660edc9a9857f35bd1a67f9a87975e1722212d31045387b; original modal equation SHAe1553e83596d5d371a7b2e196c000a1d9b551e361abf0942e352d54018b5712b. No new implementation/source hash or runtime pass is claimed here.

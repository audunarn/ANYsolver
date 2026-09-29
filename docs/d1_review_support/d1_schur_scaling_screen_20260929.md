# D1 local-compliance scaling screen

**29 September 2026. Development discriminator only; no contact law changed.**
Source at start: `c3c912c0`. The exact two-hat Q4/S3 cut-front counterexample and all earlier failed or frozen evidence remain in force.

## Decision question

The [support-weighted projected jump](d1_cut_weighted_jump_projection_20260929.md) has fourth-order quadratic work on the two-hat cut mode, while the *global* structural response to the cancelling pressure mode has sixth-order work. Does the uncancelled **individual-hat** structural-compliance proxy have the fourth-order scale needed to make a physically dimensioned comparison, or does it also collapse to sixth order?

The alternatives were: (a) the local proxy retains fourth-order scaling, so a compliance-based scaling derivation merits investigation; (b) it collapses, leaving no scale lead from this fixture. This fixed, four-cut screen decides only that question. It does not select a coefficient, alter complementarity or initiate a coupled solve.

## Construction

For the touching four-by-two Q4 source and two-S3 deformable target, use the exact two-hat signed pressure shape `p` at one-Pa amplitude. The production contact derivative supplies the supported weighted gap map `B = diag(M) Dg T`, with `T` the actual structural constraint transform. The contact-free reduced shell stiffness is `K = T^T K_full T`. The global reduced response is `p^T B K^-1 B^T p`. The deliberately uncancelled local proxy is

```
sum_i p_i^2 sum_j B_ij^2/K_jj.
```

This is the diagonal of `B diag(K)^-1 B^T` applied separately to hats. It omits structural off-diagonal coupling and inter-hat cancellation, and depends on the chosen structural coordinates. It is **not** the diagonal of the true Schur matrix, a physical compliance bound or a candidate pressure matrix. The projected jump is `p^T S p`, with `S = Q^T W J W Q` defined in the linked note. Quadratic work is reported after dividing by `(1 Pa)^2`: structural values have units m³/Pa, jump values m², and their ratio m/Pa. Exact tensor-Q1 overlap and full-reference supports are checked independently of the contact manager.

| Cut fraction θ | Global / θ⁶ (m³/Pa) | Local proxy / θ⁴ (m³/Pa) | Jump / θ⁴ (m²) | Proxy / jump (m/Pa) |
|---:|---:|---:|---:|---:|
| .1000 | .0334420 | .0135856 | 5.45855 | .00248886 |
| .0500 | .0418236 | .0147106 | 6.06512 | .00242544 |
| .0250 | .0480328 | .0155505 | 6.48511 | .00239787 |
| .0125 | .0519079 | .0160749 | 6.74143 | .00238449 |

The four-cut run completed in 4.26 s with 173.42 MB observed peak, below the unchanged 180 s/1 GB development caps. The largest exact-support discrepancy was below `6e-16 m²`. [Script](../../scripts/general_contact_d1_schur_scaling_screen.py), [raw values](d1_schur_scaling_screen_20260929.json), [execution log](d1_schur_scaling_screen_20260929.log), and [resource record](d1_schur_scaling_screen_resource_20260929.json) preserve the calculation.

## Disposition

The observed local proxy has the same fourth-order scale as the projected jump on this one family; its ratio changes about 4.4% from θ=.1 to .0125. An independent read-only mechanics review found no material algebra or dimensional error, but identified that the proxy exceeds the true reduced response by about 41 to 1,982 times across these four cuts. The true-response/jump ratio falls from `6.13e-5` to `1.20e-6 m/Pa`. Thus the apparent stable proxy/jump ratio is **not a transferable coefficient**. The result merely shows that removing inter-hat and structural coupling removes the sixth-order cancellation in this fixed fixture. The earlier smooth-pressure screen showed a slowly decaying front term that a proposed method must also address.

Next, derive a coordinate-independent local matrix and its units from the structural work, with an explicit reason that local coupling can be omitted or retained, and test consistency, including the front transition and moving-overlap derivatives. Check a different geometry and stiffness only after that derivation predicts a discriminating result. Do not install this ratio as a tuned constant or spend a coupled-case budget on this algebraic screen. D1 pressure-space stability and delivery remain open.

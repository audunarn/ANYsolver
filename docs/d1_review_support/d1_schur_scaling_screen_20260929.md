# D1 local-compliance scaling screen

**29 September 2026. Development discriminator only; no contact law changed.**
Source at start: `c3c912c0`; the initial script and first output were committed at `ebe8c3fc`. The exact two-hat Q4/S3 cut-front counterexample and all earlier failed or frozen evidence remain in force.

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

The four-cut run completed in 4.26 s with 173.42 MB observed peak, below the unchanged 180 s/1 GB development caps. The largest exact-support discrepancy was below `6e-16 m²`. The initial [script at `ebe8c3fc`](../../scripts/general_contact_d1_schur_scaling_screen.py), [raw values](d1_schur_scaling_screen_20260929.json), [execution log](d1_schur_scaling_screen_20260929.log), and [resource record](d1_schur_scaling_screen_resource_20260929.json) preserve that calculation.

### Follow-up with the exact individual-hat Schur diagonal

To remove the diagonal-`K` coordinate dependence, the same script now also forms `H=B K^-1 B^T` using the complete reduced structural stiffness and reports `sum_i p_i² H_ii`. This is invariant under an invertible change of structural coordinates and retains the actual structural coupling *within each hat*. It still deliberately removes *between-hat* cancellation. The direct `p^T H p` and separately solved `p^T B K^-1 B^T p` agree on every cut.

| θ | Exact individual-hat / θ⁴ (m³/Pa) | Exact individual-hat / jump (m/Pa) | Diagonal-`K` proxy / exact individual-hat |
|---:|---:|---:|---:|
| .1000 | .453252 | .0830353 | .029974 |
| .0500 | .544956 | .0898509 | .026995 |
| .0250 | .609769 | .0940260 | .025502 |
| .0125 | .649353 | .0963227 | .024755 |

This follow-up finished in 4.25 s and 175.10 MB under the same cap. [Raw values](d1_schur_scaling_exact_hat_20260929.json), [log](d1_schur_scaling_exact_hat_20260929.log) and [resource record](d1_schur_scaling_exact_hat_resource_20260929.json) retain its exact numerical output. Independent read-only review found no material algebra or unit error and confirmed that the quantity is invariant under structural-coordinate changes while still depending on the chosen fine-Q1 pressure-hat basis. The exact-hat/jump ratio changes about 16% across the four cuts, versus 4.4% for the invalid diagonal-`K` proxy. Neither is a calibrated coefficient: even the exact-hat diagonal discards pressure-mode cross terms, uses the global boundary-value stiffness and has no proved consistency or stability relation to the modified complementarity equation.

## Disposition

The observed local proxy has the same fourth-order scale as the projected jump on this one family; its ratio changes about 4.4% from θ=.1 to .0125. An independent read-only mechanics review found no material algebra or dimensional error, but identified that the proxy exceeds the true reduced response by about 41 to 1,982 times across these four cuts. The true-response/jump ratio falls from `6.13e-5` to `1.20e-6 m/Pa`. Thus the apparent stable proxy/jump ratio is **not a transferable coefficient**. The result merely shows that removing inter-hat and structural coupling removes the sixth-order cancellation in this fixed fixture. The earlier smooth-pressure screen showed a slowly decaying front term that a proposed method must also address.

Next, derive a local matrix and its units from the structural work, with an explicit reason that pressure-hat cross terms can be omitted or retained, and test consistency, including the front transition and moving-overlap derivatives. Check a different geometry and stiffness only after that derivation predicts a discriminating result. Do not install either ratio as a tuned constant or spend a coupled-case budget on these algebraic screens. D1 pressure-space stability and delivery remain open.

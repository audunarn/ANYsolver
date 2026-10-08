# Sparse integration comparison: numerical erratum

This note corrects the bounded synthetic integration-check design. It does not
select a scientific numerical method or alter any previously registered result.

The frozen primal comparison measures both independently assembled constraint
triangles as `||Cplus-C||F / max(1, ||C||F)`. The primal stiffness comparison
retains `||Kplus-K||F / ||K||F` for nonzero `K`, with an absolute comparison
for zero `K`. Both limits remain `1e-11`. The physical scaling identity is a
separate admission and is not established by these sparse-array comparisons.

Let `H z = b + r` define the saved primary residual, `Hplus` and `bplus`
the increased-integration description, and `xplus` its exact solution. Write
`dH >= ||Hplus-H||F`, `db >= ||bplus-b||2`, `rU >= ||r||2`,
`sigmaL <= sigma_min(H)`, `zL <= ||z||2 <= zU`, and
`alphaU >= dH/sigmaL`. For `alphaU < 1`, the identity

`Hplus (xplus-z) = (bplus-b) - (Hplus-H)z - r`

gives the outward upper bound

`||xplus-z||2/||z||2 <= (dH*zU + db + rU)/(sigmaL*zL*(1-alphaU))`.

The previously stated expression without `rU` measures only the integration
sensitivity term. It is retained separately under
`original_integration_sensitivity_upper`, with its original `1e-6` gate.
`full_saved_state_alternate_error_upper` includes the independently admitted
primary residual and has an additional `1e-6` gate. Both are undefined when
`alphaU >= 1` or their prerequisite enclosure is unavailable; no bound is
replaced by zero. Identical matrix and load descriptions therefore have zero
integration sensitivity but can have a positive full saved-state error bound.

All upper quantities are outward enclosed from binary64 operands using exact
rational arithmetic and checked scalar square-root bounds. These inequalities
are conditional on the independently verified primary inverse and residual
certificate, and neither compare a new equilibrium solution nor authorize
physical acceptance.

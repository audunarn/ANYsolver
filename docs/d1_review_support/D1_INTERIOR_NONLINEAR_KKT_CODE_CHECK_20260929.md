# D1-interior two-body nonlinear code check — development result

**29 September 2026. Local verification; independent assessment remains open.**
This check uses the previously saved, physically cut-back 0.04 N
4×4-Q4/two-S3 deformable-target press. Its sole active pressure coefficient
belongs to interior source node 12. The source rim has no active pressure,
and the saved pose meets its independently evaluated 50 µm gap budget.
The ordinary solver result was not rerun for this comparison.

## Method and result

The independent small-motion Q1 mortar oracle supplies the initial
displacements, pressure and active mode. It selects node 12, the same
mode as production, while initially differing by `1.01×10⁻⁴` in relative
displacement and `4.21×10⁻⁵` in integrated contact force. A separate
current-skin oracle clips the deformed Q4 and S3 physical surfaces,
integrates the weighted gap, and forms its derivative numerically on all
120 free structural coordinates. It checks source/target edge incidence
on the contributing faces during each derivative. The nonlinear structural
residual and tangent are the existing admitted von Karman shell model,
shared with production. The active contact equation is solved independently
from the production contact enforcement implementation.

At the saved production pose, the oracle and production differ by
`6.44×10⁻¹⁵` relatively in reference support, `8.65×10⁻¹³ m` in active
gap, and `1.11×10⁻⁷` relatively in the full reduced active-gap gradient.
The independent free-coordinate equilibrium residual is `3.07×10⁻⁹` of
the 0.04 N force scale. [Saved-pose preflight](d1_interior_saved_kkt_v3_20260929.json),
[resource](d1_interior_saved_kkt_v3_resource_20260929.json).

Starting from the independent linear state, the nonlinear KKT solve reduced
its scaled residual from `2.07×10⁻²` to `1.03×10⁻⁹` in one Newton
correction. The final active gap is `−8.33×10⁻²⁰ m`, and the minimum
inactive normalized gap is `4.63 µm`. Relative displacement difference
from production is `3.62×10⁻⁹`; integrated contact-force difference is
`4.10×10⁻⁸`. The four active source-face force bins agree to
`4.10×10⁻⁸` in relative L1, with their independently integrated reference
supports matching exact Q1 cell support to `6.94×10⁻¹⁸ m²`. The solve
took `62.86 s/264 MB` within the routine 180 s/1 GB cap.
[Current result](d1_interior_nonlinear_kkt_v2_20260929.json),
[resource](d1_interior_nonlinear_kkt_v2_resource_20260929.json).

These local errors are below the prospective `10⁻⁶` same-model code
comparison target. The previous 0.001 N high-contrast case still fails
its separate **linear frozen-footprint** comparison by `1.43×10⁻⁵` in
force; that result is retained. The present result explains why a
same-model nonlinear oracle is needed for strict code verification; it
does not erase the historical failure.

## Limits and review questions

- The oracle shares the shell structural model. This verifies contact
  work/enforcement in a coupled nonlinear solve, not an independent shell
  constitutive implementation or continuum solution.
- The active branch is selected by the independent linear oracle and
  remains fixed for this solve. Transition, sliding, opening and recontact
  use separate D1 path checks.
- This one-mode interior fixture does not prove pressure-space stability
  or nonmatching-field accuracy. Those remain separate D1 gates.
- The current-skin oracle now inverts a general projected bilinear Q4;
  its earlier horizontal-row slide fixture retained support agreement
  `2.43×10⁻¹⁴` relative and gap agreement `7.06×10⁻¹³ m` after the change.
- Independent assessment must inspect the current-skin physical director
  map, active-face incidence, finite-difference resolution, shared
  structural operator and force-bin construction before treating this as
  claim-bearing code verification. The production tangent and transaction
  gates have their own evidence.

The first saved-pose preflight rejected a clipping-signature change on a
source face outside the active pressure support. The corrected preflight
checks incidence on every contributing source face; it still rejects a
change on the active support. Both logs are retained.

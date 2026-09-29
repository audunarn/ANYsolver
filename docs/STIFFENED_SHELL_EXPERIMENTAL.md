# Experimental stiffened-shell workflows

`anysolver.stiffened_shell.create_analysis(definition=definition)` dispatches
the explicitly selected GE or physical B2 profile. Both remain experimental;
implemented behavior is distinct from programme qualification. Legacy selectors,
element mass kernels and package versions are unchanged.

## Supported B2/Q4 reference-modal development route

The existing multi-Q4/multi-B2 point-panel owner now accepts a positive explicit
`density_kg_m3` on each `Q4PanelShell` and physical `MassMetadata` on each beam.
Missing mass remains valid for static use; the owner rejects a modal request
without complete mass. Density and inertia are never inferred from stiffness.

```python
from anysolver import stiffened_shell

analysis = stiffened_shell.create_analysis(definition=definition)
result = analysis.modes(stiffened_shell.B2ReferenceModesRequest(count=3))
if result.status == "ok":
    frequencies_hz = result.frequencies_hz
    mass_normalized_physical_vectors = result.physical_modes
else:
    failure = result.failure_reason
```

This initial route uses supported, conservative reference-linear models with
coordinate supports, including diagonally rescaled selectors. General affine
MPC columns are rejected. It returns checked finite candidate eigenpairs;
residuals and orthogonality do **not** certify spectral completeness or repeated
eigenspaces. Free-free modes, prestress, buckling, S3/GE modes and spectral
qualification remain open programme obligations.

The shell mass follows through-thickness velocity about the mid-surface and
has zero normal-spin inertia. Beam mass uses the admitted physical sectional
metadata and existing station-trace Ritz interpolation. Multipliers and any
retained zero-inertia primal coordinates remain algebraic. The sparse route
uses a negative-shift descriptor factorization and general inverse-product
eigensolve; no global dense inverse, nullspace or artificial mass is used.
Returned vectors, physical gaps, projected equilibrium, descriptor residuals
and physical-mass orthogonality are checked before publication. Numerical
failure or cancellation publishes no partial pairs and leaves static operation
available. Unclassified programming errors propagate.

The current ANYfem experimental B2 input format does not encode shell density
or beam mass; it explicitly rejects these definitions rather than discarding
them. Static input round-trip remains unchanged. Native modal persistence and
consumer execution remain unfinished.

Development evidence and exact installed identities are linked from the
[active state](agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md). This document does not
establish G0/G1, F07/F12 or G4B acceptance.

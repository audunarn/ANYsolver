# Experimental stiffened-shell workflows

`anysolver.stiffened_shell.create_analysis(definition=definition)` dispatches
the explicitly selected GE or physical B2 profile. Both remain experimental;
implemented behavior is distinct from programme qualification. Legacy selectors,
element mass kernels and package versions are unchanged.

## Physical B2 numerical output admission

The physical section law is checked for exact positive definiteness of its
binary64 inputs. The former provisional normalized-pivot cutoff is replaced by
`B2_BOUNDED_OUTPUT_REPRESENTATION_V1` on the actual emitted tangent. It certifies
all six basic deformation energies to the existing 1e-8 work accuracy, and
separately bounds physical rigid wrench leakage (1e-9) and bounded rigid/cross
work (1e-8). Exact rational tests do not average the matrix with its transpose.
The operator's immutable `output_certificate` identifies this check;
`stiffened_shell.OutputRepresentationError` carries a failed certificate.
Overflow, underflow and insufficient subnormal precision still fail explicitly.

The reference right inverse fixes node one. Rigid fields use a centroid basis,
translations scaled by element length L and unit rotations. The force scale is
the maximum of the section translation diagonals and rotational diagonals/L²;
moment and energy scales are F*L. Rigid and cross bounds each apply to their
normalized finite-amplitude cube. They are not one total-energy bound or an
all-amplitude relative guarantee near a rigid kernel. Basic energies are checked
against the implemented law; independent physical work/force/station oracles
remain required. Local admission is not continuous-range qualification or
assembled graph stability; sparse solve/equilibrium checks remain separate.

The certified constant tangent is prepared once per immutable local operator.
Each evaluation returns an owned copy. No material law, historical B2 equation,
default selector or package version changes. Programme F09 acceptance remains
separate from this implemented numerical guard.

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

## Experimental GE shell-anchor reset

After an accepted finite point-coupled step, the same owner can reset its shell
rotation chart without advancing the physical load:

```python
accepted = analysis.recover()
rebased = analysis.rebase_rotations(expected_generation=accepted.generation)
saved = analysis.checkpoint()
resumed = stiffened_shell.create_analysis(definition=definition)
resumed.restore(saved)
```

The owned physical orientation is `Q = Exp(eta) @ A`; the event sets `A = Q`
and `eta = 0`. It preserves beam poses, native retained variables, material
histories and accepted load factors. The event advances the accepted generation
once. Stale predecessors, cancellation before publication and failed mechanical
checks leave the accepted prefix intact. This operation does not extend the
admitted element strain, distortion or relative-rotation domains.

Only fully free or fully fixed shell rotation triples are admitted for reset.
Partially fixed total-rotation components require transformed support equations
and are explicitly rejected. Line owners remain reference-linear. Native beam
rotations retain their existing physical storage; this is a shell-chart event.

After reset, `shell_frames` contains the physical matrices,
`shell_rotation_anchors` the immutable anchors, and `shell_chart_coordinates`
the local coordinates. `shell_displacement` retains translations and displays
principal rotation vectors; those vectors cannot reconstruct a loading history.
The historical Q4 adapter uses a total evaluation chart and rejects its pi branch.

Anchored checkpoints have a separate V6 identity, inner policy and physical-pose
witness. Restore checks mechanical consistency and continues without replay.
Unrebased checkpoints retain their previous contracts. This development slice
does not close F06, V18, G0B or broad chart/history qualification.

## Selected Q4 full algorithmic pullback

Q4 point panels can explicitly select a separate force-map policy:

```python
from dataclasses import replace
from anysolver import stiffened_shell

definition = replace(definition,
    q4_pullback_policy=stiffened_shell.Q4_ALGORITHMIC_PULLBACK_V1)
analysis = stiffened_shell.create_analysis(definition=definition)
```

This experimental policy uses the complete deformation pullback for the
unchanged local Q4 elastic or isotropic DNVC-C208 J2 update. Each trial uses
the same accepted material predecessor. The tangent includes deformation-map
curvature and the spatial-row/additive-chart transformation, including owned
rotation anchors. It is not a claim of a conservative plastic potential.
Reference-linear and finite evaluations use the selected map consistently.

The historical corotational policy remains the default. The selected policy
changes model identity; checkpoints from the two maps cannot be interchanged.
The existing anchor-envelope format is retained with that separate model
identity. Selection requires at least one Q4 element and is currently admitted
only for point panels, including mixed Q4/S3 panels. S3's existing map is
unchanged. Unsupported material sections, line owners and all-S3 selection
fail explicitly.

ANYfem persists this selection in the separate experimental v3 panel schema;
existing v1/v2 records retain their original selection and layout. These
experimental records are distinct from ordinary native-project persistence.
The policy does not qualify F05/F06 or broaden the shell strain/chart domain.

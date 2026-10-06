# Experimental flat native reference modes

`GEMixedReferenceModesRequest` extends the existing `owner.modes` operation for
a fresh virgin flat Q4, direct18 S3 V2D, or connected mixed shell. It uses the
same native full mixed descriptor solver, existing POINT pose constraints and
supported BL5 five-row director constraints. Generalized sections and virgin
physical axial/biaxial fibre sections retain their original reference tangents.
No accepted history, prestress, active plasticity, shell J2, material BL5, curved
shell, chart state or footprint is admitted. This is development functionality;
scientific spectral convergence and the external-reference gates remain open.

The old `GEReferenceModesRequest`, its capability descriptor, and the old
`GE_FREE_FREE_MODAL_ONLY_V1` boundary keep their Q4/generalized/POINT admission.
The broader request and `mixed_reference_modal_capabilities` are separate.
`GE_MIXED_FREE_FREE_MODAL_ONLY_V1` declares a fresh POINT-only free-free modal
owner with no supports, lines or footprints, reusing six canonical rigid fields.
Stateful writes and static solves remain unavailable for modal-only owners.

## Explicit kinetic interpolation

The shell midplane is the mass origin. The new S3 law declares linear
barycentric fields `v = sum(N_i v_i)` and `omega = sum(N_i omega_i)` in the
actual global nodal `[translation, director rotation]` slots. Its thickness
velocity is `v(z) = v + z*(omega cross n)` for homogeneous density `rho` and
thickness `h`. The triangle interpolation Gram matrix is
`G = A/12*(ones(3,3) + eye(3))`; the section inertia is
`diag(rho*h*eye(3), rho*h**3/12*cross(n).T@cross(n))`.
Thus normal drilling spin is exactly massless. Actual flat shell owners use
`n = (0,0,1)`; tilted function covariance controls do not broaden owner admission.

This is an explicitly named **linear nodal director kinetic approximation** for
the direct18 V2D stiffness owner. It does not include the MIN3 displacement/shear
enrichment in its velocity field and does not claim to reproduce the element's
legacy translational lumped mass. The separate hierarchical bubble S3 family
is refused; no physical bubble coordinate is statically condensed by this route.
The difference between enriched displacement kinetics and this declared field
requires future spectral convergence/reference evidence; a development unit
test cannot establish the final 2% spectral gate.

Q4 uses the unchanged physical director mass operator. Native kinetic work uses
the existing centered half-cell lift at order24 and the explicit definition's
physical 6x6 section inertia, including centroid first-moment coupling. A kinetic-
only evaluator avoids the unused elastic factor of the original generalized
section helper. It never infers inertia from constitutive stiffness. Actual
native inertial slots are nodal translations and two three-component cell
rotations. Native nodal rotation traces, retained18 member resultants, shell
normal spin and attachment multipliers have exactly zero inertia. The full
singular mixed pencil is retained; no Guyan reduction, penalty, mass floor,
tangent averaging or SPD requirement is applied to that pencil.

## Development evidence

The bounded suite is `tests/test_stiffened_shell_ge_mixed_reference_modal.py`
and `tests/test_stiffened_shell_physical_s3_mass.py`, together with unchanged
legacy modal and Q4 mass controls. It exercises the actual facade, family and
attachment combinations, free-free rigid fields, independent small dense QZ on
the full singular pencil, direct velocity kinetic work, centroid inertia,
zero algebraic mass, immutable separate caches, cancellation, wrong requests,
wrong S3 family, legacy refusals and the genuine single-P0 BL5 mechanism refusal.
BL5 component linking establishes topological contact only; it does not turn
five director rows into a six-pose attachment. Existing mechanism refusal and
the actual compiled constraint matrix remain authoritative.

Raw source snapshots, runtime imports, hashes, complete test output and JUnit
belong in `.qualification/b3-ge-e4-pl/r8-ge-mixed-reference-modal-dev-20261006-v1/`.
Results remain nearest-shift requested pairs, without a complete-spectrum claim.
The example `examples/stiffened_shell_ge_mixed_reference_modes.py` uses only the
existing public analysis factory and typed owner operation.

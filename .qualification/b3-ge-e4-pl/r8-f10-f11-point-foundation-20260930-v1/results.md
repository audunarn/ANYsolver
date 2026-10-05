# F10/F11 finite-support point/static assessment — prospective v1

Source a5a698b5eb149ac8b62b358b0a1edcd921a77d32; unchanged kernel.
Wheel 942460a11d45ffe3dea3f32cae457f75d7c5ca283a60bce6a8f01041b817fb96,
fresh pip --no-deps target installation. Contract frozen in the existing
acceptance matrix before the single run; contract.json contains exact inputs.
Independent pre-run test review cleared the source. Runner review repaired
individual finite derivative-entry validation before execution; earlier
unexecuted runner/contract retained, with unchanged scientific tolerances.

## Observed results

65/65 installed cases:40 positive,25 explicit negative rejections;65 complete
scientific JSON reports. All386 source/wheel/site modules match;205 observed
solver imports are from this isolated installation. Python3.14.2, effective
BLAS/Numba1 thread, JIT disabled; numerical dependencies in identity.json.

Guarded route 4.651896s, peak 204963840 bytes; exit0, no resource failure. Pytest1.66s.

Largest normalized errors: constraint1.49e-15, station port1.94e-15,
displacement1.26e-14, multiplier4.86e-14, reaction3.63e-14,
virtual work4.61e-13, wrench3.11e-16, supported equilibrium7.00e-15,
support work3.06e-15, accepted gap9.72e-17, common rigid fields1.13e-17.
The maximum over every individually finite derivative plateau entry is
2.37e-9 against1e-6. Minimum solved free-shell bending norm.3123;
normal drilling is not a point-port action. Exact raw values are assessment.json.

## Meaning and remaining boundaries

Only the Q4/S3 finite-vertex physical-translation rigid-fit pose with physical
B2 station reference-linear point work and bounded affine/KKT solution is
assessed. Independent covariance/couple algebra and force-method BVP station
fields establish work/ports; a bounded independent nullspace solve establishes
constrained displacement, dual and reaction parity. Existing local stiffness
operators supply the primal mechanics; this is not external validation.

The40 combinations exercise signs, scalar/coupled sections, shifts, common
frame rotation, equivalent unit representation and support-cloud winding.
Winding is not general reversed shell-mesh admission. The small rank6 predicate
is not mesh-uniform interface stability. Local S3 proof does not create a public
S3 B2 owner. This law is distinct from GE nodal points, BL5 lines and qualified
rigid/distributing footprints. No new formulation or defaults are selected.

General F10/F11, G0B, F13 and M3 remain open. The separate callback-close batch
lifetime defect remains a required repair. Prior134/134 exact installed checks
are reused only as unchanged-source/wheel regressions, not retroactively as
scientific acceptance. No performance or complete-programme qualification claim.

Independent post-run source/artifact/scientific adjudication is recorded in
review.md before any scoped acceptance is recorded.

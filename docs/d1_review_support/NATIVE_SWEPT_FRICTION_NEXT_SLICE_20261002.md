# Swept-round friction: next implementation decision

2 October 2026; source12f89a93 (kernel unchanged from ec5bc0ad).
Own read-only worker beam_surface_contract reviewed; lead checked consequential
symbols below. No execution or engineering acceptance. This is a prospective
method/ordering decision under the existing goal, not a reduced programme scope.

## Avoid inventing classical section kinematics

`elements.py`, `_current_beam_frame_and_transform`4361–4376 derives B2 Rc from
translated chord plus fixed orientation; it contains no nodal section spin.
`_compute_corotational_nonlinear_response`4386–4406 subtracts rotation vectors
additively. It does not define a finite material R(s). Quadratic B3 override4898+
uses reference-frame von Karman gradients rather than the B2 corotational dispatch.
Classical swept-section admission needs an element-owned field/variation contract;
exponentiating a convenient interpolant would introduce a new model. This gap
remains required, not waived or hidden by centreline friction.

## Reuse the native owner's physical section field

`_ge_beam3_p5_seeded/element.py:127–150` recovers R(xi)=Uc R0(xi).
`general_contact/native_retained_station.py:53–124` already implements actual
round surface x=(1-t)xc+t xc+1+Uc*(lift+R0*rho), persistent reference/station identity,
and first variations including internal angular columns18+3c:21+3c. Its42-column
work map leaves algebraic/resultant coordinates distinct. Multiplicative spatial
rotation updates are owned by `_ge_beam3_retained_generalized.py:101–104`.
Existing Jet2 seeded work and `native_retained_s3_static` retained assembly can
be reused. No generic FEModel insertion or independent contact condensation.

Next bounded implementation: extend this exact round station with material-frame
variations and a consistent retained work tangent; connect a persistent native
surface point and planar S3 material point through the existing Coulomb law.
First discriminators: pure spin at fixed centreline creates opposing torque;
common rigid transformation preserves relative work; both-body directional tangent
and rejected-trial history remain correct. Then integrate in the retained owner.
Use exact declared surface gap/contact location and a documented reference measure;
never reuse centreline-minus-radius as the new swept profile's normal law.
The actual swept normal is derived from surface tangents when needed, not assumed
equal to a radial director under shear. Cell interfaces/endpoints/partner transfer
remain explicit rejection boundaries for the first interior slice, followed by
required programme extensions. A fixed-point check alone is not surface-contact
acceptance. Keep a distinct development profile and unchanged existing defaults.

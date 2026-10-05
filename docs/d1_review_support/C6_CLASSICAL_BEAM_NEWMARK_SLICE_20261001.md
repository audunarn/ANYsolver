# Classical round-beam fixed-plane Newmark — development slice

Parentb8960736. Question: reuse the shared transaction/restart driver for actual
B2/B3 line-contact impact, retaining structural inertia and complete between-step
curve geometry. This is LevelA integrated development, not acceptance registration.
Routine180s/953MiB/thread1/JIT-off; no frozen or consumed authority renewed.

## Coordinate, work and ownership contract

The explicit allow_classical_beam_dev flag selects exact elastic scalar B2/B3
von Karman elements and the existing round-centreline fixed-plane line penalty.
All model elements must belong to the declared surface. No hemispherical caps,
native elements, shell mixture, friction, free/prescribed moving tools or large
finite-rotation admission follows. Radius and dimensioned line stiffness remain
explicit. Existing shell flags/defaults and native accepted guards remain unchanged.

The contact geometry uses the element's linear/quadratic nodal displacement field,
as do the existing contact work map and mass interpolation. The existing line
potential uses reference chord measure, including for a deformed curved B3 field;
the structural straight-reference/midpoint-node guard is preserved. A curved
reference fixture was rejected, as required; deformation supplies the curved case.
do not replace it with a new arclength law. The supplied actual structural mass,
including admitted rotary inertia, enters the reduced system. Positive-definite
mass and512-free-coordinate admission remain explicit; no added mass or damping.
Newton evaluates M*a+Rstruct+Rcontact-f on the same candidate. Only the existing
material transaction commits after equilibrium, endpoint gap and complete-path gates.

New profiles identify von Karman/Newmark, with separate affine nodal-history
identity. Algorithm settings bind restart. Historical constant/history schemas1/2
remain adequate because these participants have no new physical history; the
analysis/contact fingerprints reject incompatible profiles, bounds and definitions.

Lead owns transient.py and coupled cases. Geometry worker owns only new temporal
bound kernel and its local tests. Independent reviewer does not implement either.

## Complete curve and temporal gap

For a fixed plane and radius, g(eta,s) is degree1/2 in beam eta and degree3 in the
declared Hermite time parameter. A tensor Bernstein enclosure bounds the complete
square, including negative quadratic shape coefficients and interior extrema.
Finite refinement and outward arithmetic allowance must return an enclosure of
the represented polynomial minimum or explicit non-success. The lower bound,
not sampled positions or the upper estimate, governs penetration admission.
This is a discrete-path check; arbitrary continuum collision guarantees require
further temporal/formulation evidence. Failed refinement cannot drop a cell.

## Discriminators and stopping rule

1. Independent manufactured interior curve/time minima, B2 endpoint extrema,
   B3 shape overshoot, common translation, nonfinite/budget rejection.
2. Uniform B2/B3 impact against independent scalar Newmark equations and contact
   impulse; physical line reactions and opening. Same inputs and accuracy.
3. Active/history split restart, distinct bounds/profile incompatibility,
   exception/cancellation cleanup and endpoint/interior gap gating.
4. A nonuniform deformable B3 case exercising actual rotary/translation dynamics
   and partial line activation, with independent mass-work balance and physical gap.
5. Independent review of mass/work/path/state assumptions, then one installed
   artifact/example. Reuse unchanged shell/event evidence by impact.

A nonpass gets one discriminating correction, not enlarged tolerances/resources
or a temporal/mesh campaign. Passing these checks establishes implemented/tested
development only; full classical impact acceptance and C0–C9 completion remain open.

Sourcev2 exposes a shared time-arithmetic defect: repeated nominal dt additions
stop a few ulps before a load knot and the next phantom step violates minimum_dt.
When the next resolved knot is within128eps of the nominal step on the actual
time scale, integrate the complete step to that exact knot. No time is advanced
without solving. True sub-minimum knot intervals still fail. Sourcev3 verifies
the corrected beam work/restart fixture and existing S3 history continuation.
The snap must also lie at or before requested t_end. Sourcev8 detects a one-ULP
overstep for nextafter(knot,0); the corrected condition retains the requested
endpoint. Earlier installed106passes remain stage evidence, not final-source evidence.

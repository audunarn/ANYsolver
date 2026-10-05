# Guided finite-mass shell-pair impact — development

Run `examples/general_contact_guided_shell_pair_impact_dev.py --output <result.json>`.
The default source is one qualified Q4 bottom skin; the target is two S3 V2D top
skins on a larger square. `--target-kind q4` selects the alternative Q4 target.
The Q4 alternative has local work/inertia checks; the recorded whole-route and
installed evidence use S3. These are two finite FE bodies, with physical masses
20 kg and 14.4 kg. Both receive contact residual/tangent and inertia in the same
average-acceleration Newmark solve.

Set `ContactTransientSolverControls(allow_guided_shell_pair_dev=True,
q4_plane_event_subdivision_dev=True, batch_plane_event_fronts_dev=True)`.
The inherited event flag enables pressure-mode events here; it does not turn the
target into a plane obstacle. Default callers retain their previous admission.
`TransientConfig` supplies time integration and initial conditions. No restitution,
artificial mass, hidden damping or independent transient driver is introduced.

## Exact development boundary

Only two explicit planar shell surfaces, one penalty interaction, isotropic elastic
material and exact qualified Q4/S3 V2D formulations are admitted. All structural
elements must belong to the selections. Reduced physical mass must be positive;
the existing reduced-size and candidate/pressure resource caps remain. No positive
pressure support is removed. Existing shell-pair validation still applies.

The existing guided contributor requires fixed reference overlap, uniform normal
translation on each face, common tangential motion and zero shell rotations.
Every normalized constraint generator is checked within its dimensionless floating
epsilon contract. This is not an exact certificate for arbitrary cancelling linear
combinations; actual endpoint and rate vectors are checked again. Inadmissible
motions fail before physical commit. Complete relative supplied-float Hermite
pressure and physical-overlap gaps are checked, including interior extrema.
Neither general sliding/deforming targets nor finite rotations are admitted.

V11 restart binds this profile, settings, the event-front algorithm and ordered
physical pressure-node identities. Active split restart and rehashed identity
tampering reject/continue as declared. Cancellation clears the contact context
and returns no partial checkpoint; the unchanged model can be solved again.
Existing V1–V10 profiles and historical sphere APIs retain their own contracts.

## Fixture and references

Thickness 0.02 m, physical initial gap 0.0002 m, source/target densities1000/500 kg/m³,
source/target areas1/1.44 m², pressure penalty3e8 N/m³ and explicit gapbudget20 µm.
Initial source/target velocities are−0.1/0 m/s. The retained motion modes are
manufactured MPC guides, not permanent-joint or unrestricted deforming-body evidence.
An independent two-mass unilateral oscillator checks continuous response; a
separate branch-enumeration Newmark oracle checks the actual accepted discrete grid.
Both references call no production geometry, contact or structural kernel.

At dt50/25 µs, normalized maximum displacement errors are0.1091%/0.02839% on the
200 µm gap scale; velocity errors0.7802%/0.1964% on the0.1 m/s scale. Energy defects
are1.78e−8/3.51e−10 relative. The S3 target recoils to−0.116279 m/s; momentum
is preserved to1.11e−15 kg·m/s. This demonstrates the named temporal comparison,
not general impact qualification. Full programme, nonuniform target motion,
material/friction combinations and engineering acceptance/release remain open.

[Evidence and limits](d1_review_support/C6_GUIDED_SHELL_PAIR_SLICE_20261003.md).

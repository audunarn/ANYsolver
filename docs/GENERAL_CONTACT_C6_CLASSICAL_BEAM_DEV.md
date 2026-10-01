# Classical round-beam Newmark impact — development profile

Implemented and installed-tested; not independently accepted engineering capability
or release. Requires exact classical B2/B3 elastic scalar von Karman elements,
one fixed analytic plane, one declared round-centreline surface covering every
model element, explicit radius/line stiffness/gap tolerance and no end caps.
The existing straight-reference B3 guard remains; its deformed quadratic field
may curve and contact in its interior. No native beam insertion is enabled.

Use the ordinary `solve_transient_contact` and `TransientConfig`. Select
`ContactSolverSettings(pair_motion='general')` and
`ContactTransientSolverControls(allow_classical_beam_dev=True)`. Existing callers
retain their profile. The new profiles are
`CLASSICAL_B2_B3_ROUND_TUBE_VON_KARMAN_FIXED_PLANE_NEWMARK_DEV_V1` and its
`...NEWMARK_HISTORY_DEV_V1` counterpart for `ContactNodalLoadHistory`.
The actual structural mass, including rotary inertia, must be positive definite
after constraints; at most512 free coordinates are admitted. No mass, springs,
damping or restitution are added.

The existing distributed line potential and force map are reused. A tensor
Bernstein enclosure bounds the complete B2/B3 curve and declared Hermite time
path. Exact rational arithmetic treats finite binary64 data as exact inputs;
returned bounds round outward. `beam_swept_gap_tolerance_m=1e-10` controls the
numerical enclosure width, separately from the interaction's physical penetration
budget. `maximum_beam_swept_subdivisions=512` bounds refinement across all cells.
Unresolved, nonfinite or unrepresentable enclosures fail explicitly. A sampled
position never supplies the admission lower bound. This certifies the represented
polynomial path, not exact continuum collision times.

The shared solver handles material transactions, cutback, cancellation, dead nodal
loads, affine load-history work and split restart. Beam controls and definitions
bind the analysis/contact fingerprints. Historical constant/history schemas1/2
remain; incompatible profiles/settings fail. Contact summaries expose line energy,
active length, physical beam/plane forces and moments; the overall result identifies
the temporal profile. Rotational inertia is retained for admitted free rotations.

Run the explicit development examples:

```text
python examples/general_contact_beam_plane_impact.py
python examples/general_contact_beam_plane_impact.py --quadratic --deformable
```

The toy fixtures' .002m gap budget and1e4N/m² line stiffness are development inputs,
not application recommendations or qualification settings. Full enforcement/time
refinement and inherited1e-3-radius qualification starting budgets remain required.
Large finite rotations/corotational dynamics, beam pairs/shells, caps, friction,
nonlinear materials, free/moving rigid bodies and broad C6 acceptance remain open.
See [results](d1_review_support/contact_c6_classical_beam_20261001/results.md).

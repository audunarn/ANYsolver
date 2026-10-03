# Physical round-beam ends against a sphere or infinite cylinder

4 October 2026. **Implemented and installed-tested development; no independent
engineering acceptance, normal application admission or release.** The profile is
`CLASSICAL_B2_B3_ROUND_TUBE_RADIAL_HEMISPHERE_ENDS_STATIC_DEV_V1`.

## Use and admitted development boundary

Select one classical B2/B3 surface with explicit `beam_radius` and
`beam_end_caps="hemisphere"`, against one `RigidContactBody` sphere or infinite
cylinder. Set `line_stiffness` in N/m², `endpoint_stiffness` in N/m, dimensional
`gap_tolerance` smaller than the beam radius, `pair_motion="general"` and explicit
`line_integration_relative_tolerance`. The existing scalar elastic, concentric
section and von-Karman structural restrictions apply. Reference B3 cells are
straight with midpoint nodes; actual deformed quadratic curves are evaluated.
The rigid axis is fixed; prescribed translation is supported.

The public [example](../examples/general_contact_beam_end_capped_cylinder.py)
accepts `--radial sphere` and `--radial cylinder`. Existing capped-cylinder and
`--plane` selections keep their defaults. Its numerical inputs are explicit
demonstration values, not application recommendations.

This is an additive distributed-line plus physical-end point penalty, **not** a
section-resolved hemispherical surface integration or Hertz pressure model.
It does not enable friction, native beams, dynamics, finite-rotation structural
admission, automatic/self-contact or multiple interactions. The no-cap radial
selection retains its existing owner and restart contract.

## Complete discrete work

For stored fixed map `B`, relative position `x-c`, declared sum of radii `R`,
`y=B(x-c)`, `d=norm(y)` and `g=d-R`, use the literal map:

```text
a = B.T * y / d
H = B.T * (I - y*y.T/d²) * B / d
E_end = 0.5 * k_end * min(g,0)²
R_end = k_end * g * a
K_end = k_end * (a*a.T + g*H)       [owned active branch]
```

`B=I` for a sphere; a cylinder uses the stored `I-axis*axis.T`. Both line and
endpoint contributions differentiate this same map. Reference line measure and
actual B2/B3 displacement interpolation are retained. Local blocks assemble on
authoritative translations. Opposite rigid force and moment use the reported
global-zero origin. Line/endpoint storage and their algorithmic sum are separate.

An active end belongs to the outward hemisphere only when
`y dot (B*v_out) < 0`, using the actual quadratic endpoint derivative. Equality
rejects. All classical material-node incidence, including unselected elements
and B3 middle nodes, determines genuine ends. Side-owned endpoint records report
a centre-offset gap; they do not claim a recovered hemisphere surface gap.

## Geometry, path and bounded integration

Exact rational Bernstein arithmetic encloses the whole represented curve's
squared mapped norm; outward square-root bounds give a conservative minimum
gap with declared enclosure accuracy `0.1*gap_tolerance`. The entire centreline
must be exterior to the obstacle. Undefined normals and unresolved bounds fail.

Affine static sweeps include prescribed-tool translation. A velocity enclosure
and finite subdivision certify the gap over the complete path. A separate tensor
Bernstein certificate keeps the physical curve derivative above the existing
nonzero-speed threshold throughout the path. Open endpoint poses cannot hide
through-crossing or an intermediate collapsed curve.

Ownership is quadratic along the affine path. Each interval must be certified
open or strictly signed; active double roots and unresolved ownership transitions
reject or cut back. This is not a certificate for a dynamic integration-stage path.

Activation roots are proposals, corrected to an exact represented open-side
certificate. Exact inactive-panel bounds and sign-variation subdivision prevent
sampled zeros from discarding a hidden second contact pocket. Adaptive 8/16-point
Gauss comparison includes energy, residual and tangent; finite line and swept
budgets remain explicit. Its reported error is an estimate, not a rigorous
arbitrary-geometry integration-error certificate. Integration refinement creates
no additional mechanical unknowns.

Restart binds the profile, geometry revision, physical ends, dimensions,
tool path and line/swept controls. Geometry caches live for one evaluation only;
exceptions discard them, and failed tool evaluation restores the previous path.
Physical increment acceptance stays under the existing static transaction.

## Evidence and unresolved delivery

[Evidence](d1_review_support/contact_radial_endcaps_20261003/summary.json):
37 installed checks pass in 31.110 s, peak process-tree RSS 336,408,576 bytes;
211 loaded modules and 494 package files match current source. Effective JIT is
disabled and numerical thread pools use one thread; limits are 180 s/953 MiB.

Checks include independent endpoint energy and directional work/tangents,
tilted-cylinder rigid covariance, actual B3 derivatives/junctions, hidden ownership
roots, complete crossing/regularity sweeps, two curved contact pockets with an
independent analytic-root/quadrature reference, exact repeated grazing, explicit
budget exhaustion, force/displacement controls and independent axial-bar response.
Active/open fresh restart, staged moving-tool storage/work, candidate exception,
cancellation/reuse, local cleanup, public examples, previous radial routes and
installed no-contact compatibility pass. Staged tool-work/storage relative error
is 2.680e-12 against the unchanged 1e-6 target. General unaligned-event work is
not accepted by that case.

Thirteen runs and 78 raw records retain preliminary failures: floating activation
cuts, a singular test curve, unsupported degree-zero restriction and an incorrect
progress-callback exception expectation. Each has a specific source or fixture
correction. The [supporting review](d1_review_support/contact_radial_endcaps_20261003/review.md)
identified the B2 restriction issue; constant derivatives are now represented by
two equal controls and rotating/collapsing paths are checked. This same-family
scrutiny is not independent engineering acceptance. C2/D3 and full C0–C9 remain
incomplete; mesh/enforcement qualification and broader pairings remain required.

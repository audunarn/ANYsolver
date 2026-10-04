# Experimental native point displacement control

The existing `DisplacementControl` now supports fixed translational targets for
elastic flat full-map Q4 panels with native generalized, physical-fibre or mixed
beam families and point connections. It requires an ordinary, unrebased
force-controlled seed with nodal dead translation forces.

```python
analysis.solve(seed_actions, (.5, 1.))
result = analysis.solve(
    load_direction, displacement_targets,
    displacement_control=anysolver.stiffened_shell.DisplacementControl('beam', 105, 2),
    max_iterations=20, max_backtracks=12,
)
```

The applied force is the seed force plus the solved amplitude times the declared
load direction. Targets are physical translations in metres, not load factors.
The existing sparse bordered corrector and equilibrium/compatibility limits are
unchanged. Every material trial uses the same accepted predecessor. All domains
and the controller history publish atomically; rejected work and cancellation
retain the accepted prefix.

The native mechanical payload and controller have separate checkpoint identities:
`B3_GE_E4_PL_NATIVE_POINT_MATERIAL_DISPLACEMENT_MECHANICS_V1_DEV` and
`B3_GE_NATIVE_POINT_MATERIAL_DISPLACEMENT_V1_DEV`. Model-derived native history
layouts preserve both compensated halves of accepted and predecessor states.
Restore checks physical state and equilibrium, replays the last material update
from its predecessor and requires exact native history agreement before publishing
the saved accepted histories. Existing BL5 and curved identities remain unchanged.

Recovery includes generalized station records, physical-fibre station stresses
and last-increment fibre energies. These are not cumulative global energy or
engineering capacity results. Selected fibre recovery is not added by this change.

This initial route excludes shell J2, S3, other attachments, staged/external or
rebased seeds, adaptive targets, branch-event trials, displacement chart rebasing
and arc-length qualification. Those requests remain explicit errors. This slice
does not resolve the saved simultaneous shell-J2/fibre force-chart failure or
qualify the complete stiffened-shell programme.

Run the public headless example with an installed candidate:

```powershell
python examples/stiffened_shell_ge_point_displacement.py --output <new-directory>
```

It shares the adjacent zero-unload example's explicit model definition and
diagnostic low-yield fibre, and exercises unload/reload targets with exact restart.

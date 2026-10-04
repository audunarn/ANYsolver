# Experimental native point displacement control

The existing `DisplacementControl` now supports fixed translational targets for
elastic or isotropic-J2 flat full-map Q4 panels with native generalized, physical-fibre or mixed
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

Shell-J2 point models select separate coupled identities:
`B3_GE_E4_PL_NATIVE_POINT_COUPLED_J2_DISPLACEMENT_MECHANICS_V1_DEV` and
`B3_GE_NATIVE_POINT_COUPLED_J2_DISPLACEMENT_V1_DEV`. They additionally preserve
accepted and predecessor Q4 plastic strains and accumulated strains. Restore
retains the existing shell replay criterion and reports actual layer stresses.
The elastic native identities and payload layout retain their meaning.

Recovery includes generalized station records, physical-fibre station stresses
and last-increment fibre energies. These are not cumulative global energy or
engineering capacity results. Selected fibre recovery is not added by this change.

Elastic mixed Q4/S3 and all-S3 panels with generalized native sections select
`B3_GE_E4_PL_NATIVE_POINT_ELASTIC_S3_DISPLACEMENT_MECHANICS_V1_DEV` and
`B3_GE_NATIVE_POINT_ELASTIC_S3_DISPLACEMENT_V1_DEV`. Mixed panels use full-map
Q4; all-S3 definitions retain the default unused Q4 policy. Elastic S3 trial
states are retained through the existing model-bound force-publication rule.
Fibre-containing native sections on elastic S3 select distinct identities:
`B3_GE_E4_PL_NATIVE_POINT_FIBRE_ELASTIC_S3_DISPLACEMENT_MECHANICS_V1_DEV` and
`B3_GE_NATIVE_POINT_FIBRE_ELASTIC_S3_DISPLACEMENT_V1_DEV`. They require the current
stable S3 arithmetic. Legacy force seeds restored with historical S3 arithmetic
remain valid force states but reject displacement control before any trial or
seed capture. Force restoration never upgrades their arithmetic. Plastic S3
shells are not admitted by either displacement route.
See `examples/stiffened_shell_native_s3_displacement.py` for both elastic meshes.

This route excludes plastic S3, incompatible legacy S3 force seeds, other attachments, staged/external or
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
`examples/stiffened_shell_native_coupled_displacement.py` exercises the existing
two-stiffener Q4-J2/fibre model under the same fixed-target contract, including
further plastic flow in both domains and exact restart. Its low-strength laws
remain lifecycle controls, not engineering design or capacity qualification.

The fibre S3 example uses fixed monotonic targets after the existing plastic
force seed; it demonstrates further fibre flow and exact restart, not resolution
of the parked force-unloading failure or physical capacity qualification:

```powershell
python examples/stiffened_shell_native_fibre_s3_displacement.py --output <new-directory>
python examples/stiffened_shell_native_fibre_s3_displacement.py --all-s3 --output <another-new-directory>
```

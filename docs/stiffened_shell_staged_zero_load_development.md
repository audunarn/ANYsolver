# Experimental point-panel unloading to zero

The existing flat native GE point owner accepts an opt-in staged normalization:

```python
programme = anysolver.stiffened_shell.StagedDeadLoadProgramme(
    analysis.preflight()["identity"],
    (loading_actions, (), loading_actions),
    zero_load_reference_endpoint=1,
)
result = analysis.solve(programme, (.5, 1., 1.5, 2., 2.5, 3.))
```

Endpoint numbers are one-based. The selected endpoint must exist, contain
nonzero translation forces and produce finite, representable nonzero free work
after the compiled coordinate scaling. Its owned vector is frozen for the solve.
An empty endpoint means zero external force; it does not erase material history.

Only an exactly zero **complete applied vector** uses the reference for residual
normalization. Actual loads, residuals, tangents, retained coordinates and physical
updates are unchanged. Every nonzero load, including tiny loads, keeps the
existing actual-load/component checks. No numerical force floor is added.
Equilibrium `1e-8` and compatibility `1e-9` remain mandatory.

The optional endpoint selects `B3_GE_E4_PL_STAGED_ZERO_REFERENCE_V1_DEV`.
Descriptor and augmented checkpoint identities include it. Omitting the option
retains historical V1 descriptor/checkpoint identity and behavior; old snapshots
are not reinterpreted. Results expose `load_equilibrium_reference_endpoint`,
`load_equilibrium_reference_policy` and `load_equilibrium_reference_used`.
The ANYfem experimental point-case descriptor delegates the same serialization.

Admission currently covers the existing flat point staged-force route, not lines,
footprints, curved reference geometry, distributed loads, pressure, B2 or a new
control method. Material combinations retain their original guards. This is
experimental implementation, not connection or aggregate qualification.

Plastic unloading may retain self-equilibrated stress, reactions, deformation
and stored energy. Those quantities are not required to vanish. Physical free
equilibrium, support/interface force and moment balance, compatibility, material
admissibility, irreversible histories and restart must still hold.

Run the public headless development example after installing the candidate:

```powershell
python examples/stiffened_shell_ge_point_zero_unload.py --output <new-directory>
```

It uses two Q4 shells, two native members with separate generalized/physical-fibre
sections, eccentric point connections, plastic load/zero-unload/reload and exact
checkpoint continuation. Its low-yield fibre is a lifecycle control, not an
engineering capacity law or simultaneous shell-J2/fibre chart qualification.

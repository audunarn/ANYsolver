# Standalone installed deformable-target example — development evidence

Source commit: `19f66ea0`. The example file was copied unchanged from
`examples/general_contact_free_target_cycle_dev.py` to
`C:\ANYworkspaceWork\general-contact-standalone-19f66ea0`, outside the solver
checkout. Its SHA-256 is
`a92282f107badf5bef6a4b57f3cb5f65b414f31b1feaf77ae8dd70e6a7d564fc`.
The source-built `anysolver-0.4.7-py3-none-any.whl` SHA-256 is
`42e862daa1dd27b015f761d4b8ec7c76494d1ffc6c30065c7f9ec3ad1abcc4f4`.
It was installed without dependencies in an isolated target under `reports/`.

The run's current directory was outside the checkout, with `PYTHONPATH` set
only to that isolated target. The reported `anysolver.__file__` resolves inside
the target. The example no longer imports a development `scripts` helper.
The bounded process completed in 22.63 s at 320.02 MB peak process-tree RSS,
below the existing 180 s / 1 GB development limits. All eight reported step
mechanics fields match the previously retained local
`d1_free_target_cycle_local_39b2c598_20260928.json` exactly after excluding
the module path. This timing is not a paired performance comparison.

[Raw result](d1_standalone_free_target_result_19f66ea0_20260928.json) and
[resource/command record](d1_standalone_free_target_resource_19f66ea0_20260928.json)
are retained. This is an installed development workflow, not independent D1
acceptance, final package release, or evidence for unadmitted combinations.

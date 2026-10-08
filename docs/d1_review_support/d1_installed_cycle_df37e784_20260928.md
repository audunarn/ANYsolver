# Current-source installed deformable-target D1 example — development check

Source commit: `df37e784`. A wheel was built from that checkout under the
180-second/1-GB development cap (8.21 s, 80.22 MB process-tree peak). The
local `anysolver-0.4.7-py3-none-any.whl` SHA-256 is
`658920683c674b0f117127e1210be7612b7142ab5b1f0ed708655f`.
It was installed with `--no-deps --no-index` into an isolated target under
`reports/d1_installed_df37e784`.

The unchanged standalone example (SHA-256
`a92282f107badf5bef6a4b57f3cb5f65b414f31b1feaf77ae8dd70e6a7d564fc`)
ran from `C:\ANYworkspaceWork\general-contact-standalone-df37e784`, outside
the source checkout, with `PYTHONPATH` pointing only to that installed target
and user site packages disabled. The reported `anysolver.__file__` resolves
inside the installed target. The bounded run completed all eight deformable
Q4/S3 press, slide, opening and recontact steps with a checkpoint in 21.07 s
at 319.96 MB peak. Its mechanical result fields match the earlier independent
standalone wheel run at `19f66ea0` exactly after excluding the module path.
Maximum reported relative complementarity is 3.63×10⁻¹³ and the minimum
reported contact gap is −2.333 µm under the declared 50 µm limit.

[Raw result](d1_installed_cycle_result_df37e784_20260928.json),
[run resource record](d1_installed_cycle_resource_df37e784_20260928.json)
and [wheel-build resource record](d1_wheel_build_resource_df37e784_20260928.json)
are retained. The example and public capability profile explicitly say
`development_only`. This check does not close the independent D1 mechanics,
pressure-space, final packaging, or application acceptance gates.

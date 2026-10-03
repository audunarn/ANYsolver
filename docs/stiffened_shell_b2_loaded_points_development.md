# Experimental B2 loaded interior points

The Q4 panel definition now has an explicit opt-in:

~~~python
definition = dataclasses.replace(
    definition,
    point_trace_policy=anysolver.stiffened_shell.B2_FIXED_END_LOADED_POINT_TRACE_V1_DEV,
)
analysis = anysolver.stiffened_shell.create_analysis(definition=definition)
~~~

The default remains the existing homogeneous station trace. The new policy
uses the same physical B2 flexibility law and finite-vertex shell pose law,
with fixed-end particular fields for uniform body action and interior point
wrenches. It assembles all same-member Green compliance blocks. Its actual
compatibility equation is C u + a_body - H lambda = 0; the multiplier block
is -H. It is physical elastic compliance, not a penalty or numerical floor.

Raw arrays remain nodal loads. Only B2ReferenceBodyLoad, created by the same
owner, supplies distributed body action. A load bound to another policy/model
is rejected. Unchanged static operators retain one factorization. For zero prescribed
offsets and unique unit-selector supports, a bounded stored-equation residual
certificate may resolve a load rejected by the conservative global roundoff
estimate. The original tolerance and physical checks remain mandatory.
Certification does not establish forward displacement accuracy, assembly
accuracy, or resolution of arbitrary subcomponents sharing one load row.

Results carry loaded_member_poses (axis poses in local m/rad),
equilibrated_sections (sided physical resultants/strains) and
loaded_strain_energy (full beam particular-field plus homogeneous shell/beam
energy). Existing internal_strain_energy retains its nodal homogeneous meaning.
Selected batch recovery returns only requested members/stations; total energy
does not depend on recovery selection. Cancelled batches return complete cases.

The initial new policy admits reference-linear Q4 finite-vertex points only.
Mixed/S3 panels, footprints and spectral requests reject it explicitly.
Capability status remains experimental and unqualified. No bonded-line, weld,
finite-gravity, practical-scale or aggregate programme acceptance is claimed.
The factory still admits SI definitions; numeric unit-covariance checks do not
add a second public unit system.

ANYfem's ExperimentalB2LoadedPointPanel has separate strict raw and body
schemas. Both persist the exact point policy and experimental status.
Historical encoders reject opt-in definitions. Standalone and project roundtrip
are detached input persistence, not accepted-state checkpointing.

Run the public example from an installed solver (and ANYfem for roundtrip):

~~~powershell
python examples/stiffened_shell_b2_loaded_points.py --cases 10 --consumer-path panel.anyfem-b2.json
~~~

Checks use an independent six-initial-resultant boundary solve, both bending
planes, full external/support work, strain-energy integration, two shared-member
points, rotated offsets, prescribed motion, numeric covariance, endpoints,
selected 1/10/100 cases and cancellation. This development evidence does not
close the full G0–G6 scope or the existing endpoint mixed-load resolution ticket.


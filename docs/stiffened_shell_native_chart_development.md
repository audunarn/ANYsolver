# Experimental native displacement chart rebasing

This operation is implemented for admitted native B3-GE point-coupled
displacement histories, including the exercised Q4/generalized J2 and
all-S3/physical-fibre J2 models. It is development behavior, not programme
qualification. Check the owner's capabilities and admission errors for the
actual model combination.

```python
accepted = analysis.restore(checkpoint_bytes)
rebased = analysis.rebase_rotations(accepted.generation)
chart_checkpoint = analysis.checkpoint()
```

Rebasing preserves physical shell frames, beam configurations, retained
variables, accepted material histories and the physical load position. It
sets shell additive rotation coordinates to zero and stores the same physical
frames as chart anchors. Generation increases by one; the operation does not
add a physical increment. A stale generation or cancellation before publication
preserves the accepted checkpoint.

The new native chart policy is distinct from the existing zero-chart-event
displacement policy. Existing checkpoint identities remain unchanged when the
operation is unused. Restoration checks physical support, pose, equilibrium,
material predecessor and serialized S3 state consistency. Full supported
rotation triples are required; partial rotational supports remain excluded.

For an unfinished adaptive displacement programme, resume its exact saved
target sequence and controller/load definition. Do not construct replacement
targets from the endpoint displacement. A fresh owner can restore the chart
checkpoint and continue that same programme.

Ordinary force seeds retain the unrebased affine nodal dead-translation admission
contract. Staged/external loads and branch-event policies are not admitted by
this operation. Arc continuation has a separate admission and checkpoint
contract; chart rebasing alone does not establish arc support, a limit point or
a descending branch.

The runnable history examples are
`examples/stiffened_shell_coupled_s3_adaptive_history.py` and the native
generalized Q4/J2 history regression. The focused chart regression is
`tests/test_stiffened_shell_native_displacement_chart.py`. Development evidence
is recorded under
`.qualification/b3-ge-e4-pl/r8-native-displacement-chart-dev-20261005-v1/`.

## Selective force-controlled free-node event

Fixed-force native point owners have a separate experimental opt-in:

```python
rebased = analysis.rebase_rotations(
    accepted.generation, preserve_supported_charts=True,
)
```

This requires the existing explicit `Q4_ALGORITHMIC_PULLBACK_V1` policy for
models containing Q4, or the existing variational S3 route. It resets only
nodes without any rotational support. Partially and fully supported nodes
retain their chart coordinates and anchors exactly. The default operation
and its existing partial-support refusal remain unchanged.

Recovery, checkpoint/restore, continued fixed-force stepping, stale-generation
refusal and cancellation were exercised through installed artifacts. The flag
rejects displacement, arc, adaptive, staged, external-load, line and footprint
contexts. It does not transport supported charts, establish their full physical
work conjugacy, or qualify F06. The measured force/moment balance and equilibrium
checks are not independent virtual-work or energy proofs. See the
[corrected development report](agent_plans/development/r8-ge-selective-rebase-20261009/REPORT-v2.md).

## Original-coordinate shell supports

A distinct construction-time experimental policy supports rebasing restrained
shell nodes:

```python
from dataclasses import replace
from anysolver import stiffened_shell

definition = replace(
    definition,
    shell_support_policy=stiffened_shell.NATIVE_SHELL_COORDINATE_SUPPORT_V1,
)
analysis = stiffened_shell.create_analysis(definition=definition)
```

Select the exported constant explicitly. Models containing Q4 also require
`Q4_ALGORITHMIC_PULLBACK_V1`; pure S3 uses the variational operator with stable
displacement-centred arithmetic. This policy admits elastic generalized native
beam sections, point attachments and fixed-force nodal translations only.

The selected restraints hold original principal rotation-vector components
`S Log(Exp(theta) A)=0`. Supported nodes update free original components and
reconstruct their local chart; free nodes retain their existing update. This
is a coordinate-defined restraint, not automatic physical-axis release
qualification. Both original and local chart norms must remain below
`pi - 1e-7`; unsupported chart states fail explicitly.

The existing `rebase_rotations` operation may now reset all shell charts while
preserving these original restraints. The selective flag remains available.
The policy and its branch/arithmetic conventions are bound to model identity;
restore checks the actual original equations and retains the stable S3 path.
Support recovery includes all three spatial moment components. Coordinate
equilibrium and independent physically admissible equilibrium are both required.

Partial beam rotations, fibre or active yielding, shell J2, reference-linear and
spectral operations, other controllers, line/footprint attachments and external
or staged loads remain refused. Existing ANYfem formats refuse to persist this
new law; their default policy remains compatible. Installed Q4/S3 solves,
rebasing, restore, continued stepping, local reaction work, actual-update
tangents, cancellation and stale-state checks passed. Full F06 and programme
qualification remain open. See the [development disposition](agent_plans/development/r8-ge-coordinate-support-20261009/root-disposition.md).

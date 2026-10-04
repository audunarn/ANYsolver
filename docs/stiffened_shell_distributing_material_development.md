# Experimental finite distributing material histories

These explicitly selected development policies use the existing flat full-map
Q4/native generalized B3 owner and finite director/projected-polar distributing
footprint. They are **experimental, not qualified**. They do not establish a
welded or bonded-line model or complete programme acceptance.

The existing generalized/coupled J2 material policies retain their positive,
increasing load-factor admission. For fixed load/unload and signed reversal,
select one of the public constants:

- `GE_FINITE_DISTRIBUTING_GENERALIZED_CYCLIC_MATERIAL_V1`
- `GE_FINITE_DISTRIBUTING_COUPLED_J2_CYCLIC_MATERIAL_V1`

Set the existing definition's `finite_distributing_material_policy` and its
`cyclic_reference_actions` together. The latter is an explicit nonempty tuple
of supported nodal dead translation actions with nonzero representable work
on free coordinates. Compilation owns those inputs and the reference pattern.
Each `solve` call must use the same pattern. For example, given an admitted
`definition` and `actions`:

```python
from dataclasses import replace
from anysolver import stiffened_shell as ss

cyclic = replace(definition,
    finite_distributing_material_policy=
        ss.GE_FINITE_DISTRIBUTING_COUPLED_J2_CYCLIC_MATERIAL_V1,
    cyclic_reference_actions=actions)
owner = ss.create_analysis(definition=cyclic)
try:
    prefix = owner.solve(actions, (.25, .5, .75, 1., .5, 0.),
                         max_iterations=24, max_backtracks=16)
    checkpoint = owner.checkpoint()
    reverse = owner.solve(actions, (-.25, -.5, -.75, -1.),
                          max_iterations=24, max_backtracks=16)
finally:
    owner.close()
```

Factors are absolute load positions. Each must be finite and must change from
the preceding accepted factor; a virgin zero-to-zero increment is rejected.
These policies admit fixed increments only. Adaptive, staged/external loads,
chart rebasing, S3, physical fibres, spectra and displacement/arc control remain
excluded from this particular route.

At factor zero, external force is exactly zero. Equilibrium and trial merit
use the model-owned unit-factor reference pattern for normalization. Nonzero
factors retain the existing normalization. Equilibrium `1e-8` and compatibility
`1e-9` limits, material laws and iteration/backtrack ceilings are unchanged.
The selected policy and owned reference pattern bind model identity and the
separate cyclic checkpoint kind. Restore checks the pattern before publication;
an altered checkpoint cannot redefine zero-load normalization.

The accepted predecessor contains actual constitutive states. Unloading does
not reset plastic strain or accumulated hardening. Isotropic hardening can
leave plastic strain unchanged during force reversal inside its expanded yield
surface; a negative force alone does not prove reverse plastic flow.

The ANYfem example
`examples/stiffened_shell_ge_distributing_cyclic_consumer.py` in the compatible
consumer checkout exercises case and Project save/reopen, simultaneous initial
shell/beam yielding, zero-force checkpoint/restore, signed reversal, selected
recovery and byte-identical continuation against the same accepted path.
Run it with the compatible experimental solver and consumer wheels installed:

```powershell
python examples/stiffened_shell_ge_distributing_cyclic_consumer.py <output-directory>
```

Consumer records retain the existing material schema, with explicit cyclic
policy and `fixed_signed_zero_nodal_translation_force_history_only` admission.
Historical monotone records keep their old token. Policy/token mismatches fail
before execution. Installed checks and the example are development evidence;
full material, physical-connection, platform and independent acceptance remain
separate obligations.

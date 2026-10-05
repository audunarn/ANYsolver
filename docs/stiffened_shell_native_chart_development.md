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

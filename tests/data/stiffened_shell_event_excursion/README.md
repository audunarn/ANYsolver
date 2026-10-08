# Fixed coupled material excursion seed

This is the accepted prefix of the preserved p0 coupled-Q4 J2/generalized BL5
force-reversal diagnostic at -484.375 N. It is not a converged -500 N result.
Model: `test_stiffened_shell_bl5_coupled_material.coupled()`; native beam sections
and Q4 shell J2 law are defined by that fixture. Recovery and endpoint mechanics
are validated by public restore before any new displacement step.

The original source failed campaign is retained in
`docs/agent_plans/development/r8-bl5-coupled-material-20261002/`.
The seed was also bound into the installed public event-policy evidence at
`docs/agent_plans/development/r8-event-public-20261002/` and generalized recovery
at `docs/agent_plans/development/r8-generalized-recovery-20261002/`.

Binary SHA256: `0be9beeb00fe12297e49ac326b1ca61ec403650be20d5d518f1de6d1b5181673`.
No regeneration or identity substitution is implicit. A changed physical fixture
requires an explicit new case decision and preservation of the prior evidence.
This seed tests continuation/restart from an authentic material history; it does
not replace tests constructing that history or prove complete reversal/capacity.

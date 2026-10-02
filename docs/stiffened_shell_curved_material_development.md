# Experimental curved Q4 point material workflow

Select `CURVED_Q4_POINT_MATERIAL_REFERENCE_V1` explicitly in the existing
`LinearDefinition.shell_reference_policy`, together with
`Q4_ALGORITHMIC_PULLBACK_V1`. Construct the owner through
`anysolver.stiffened_shell.create_analysis`. This separate development policy
admits planar Q4 facets on a curved reference, full-pose point attachments,
optional isotropic shell J2, and native generalized B3 yielding/hardening.
Its model identity differs from the older curved elastic policy. Coincident
nodes, facets and beam section frames retain the existing admission rules.

The shell material history uses the fixed reference-facet frame. The local law
is the existing corotated von Karman membrane/bending plane-stress J2 update;
this is not finite-strain plasticity. Transverse shear and drilling completion
retain their existing elastic definitions. Every trial reads the same accepted
shell and beam predecessor; the mixed owner commits them atomically.

Only reference-linear and finite force control with fixed nodal translational
dead forces are admitted in this slice. S3, physical beam fibres, line and
footprint attachments, external/staged load wrappers, displacement control,
curved material arc continuation and spectra remain unsupported. The older curved elastic policy, defaults and checkpoint
decoding contracts keep their meanings. No publication or qualification follows.

The finite fixed-step driver retains its default eight backtracks. For this new
policy only, an explicit `max_backtracks` up to 16 is admitted; adaptive stepping
retains its maximum 12. A bounded reload test needed a first improving step below
the legacy twelve-halving resolution. Its failed fixed and adaptive attempts are
preserved. The larger explicit budget changes permitted work, not equilibrium
tolerances or the globalization method, and makes no speedup claim.

Results recover actual Q4 layer strains, stresses, plastic strains and hardening
variables, native beam cell resultants and accumulated station history. Cached
`beam_generalized_material` records include station strains/resultants, physical
frames, endpoint stored energy, and last-increment plastic change/dissipation per
reference length. Recovery reads accepted owned records without constitutive or
assembly replay; these are generalized-section quantities, not fibre stresses.

New V2 predecessor-aware binary kinds retain the preceding beam material state
and, for shell J2, the preceding layer state. Endpoint re-evaluation from that
fixed predecessor validates accepted histories before publication. The bounded
check reproduces station records exactly after restore and preserves the assembled
residual/tangent within its registered parity tolerance. It does not prove an
arbitrary loading history from bytes, replace independent replay, or qualify all
material branches. Existing byte-integrity, physical-layout and resource checks
remain mandatory.

Older curved material snapshots keep their decoding and re-encoding contracts.
They omit last-increment station records because their predecessor is unknown;
no zero incremental dissipation is invented. After a new increment is accepted,
its known predecessor enables the new checkpoint and detailed recovery.

ANYfem uses the existing `ExperimentalGEPointPanel` and the distinct strict
`anyfem.experimental-ge-curved-q4-point-panel-material-v2` input schema.
Standalone and ordinary Project save/reopen preserve the policy and owned native
beam definitions. Accepted solver state still needs its separate checkpoint.
Capabilities and persistence remain `EXPERIMENTAL_NOT_QUALIFIED`.

Development evidence, including failed attempts, artifact identities and precise
checks: [curved material slice](agent_plans/development/r8-curved-material-20261003/results.md).

[Predecessor-aware recovery evidence](agent_plans/development/r8-curved-predecessor-20261003/results.md).

The existing `create_stress_free_point_reference` also admits a virgin material
definition, returning the distinct
`GE_STRESS_FREE_POINT_MATERIAL_REFERENCE_TRANSPORT_V1_DEV` operation policy.
Material curves and native section/inertia definitions are preserved, but no
accepted history is transferred. A loaded owner/checkpoint is not a reference
definition. Q4 facets and native frames must still pass existing admission.
Bounded checks cover both signs of the actual roof crown with zero initial stress
and plasticity, rigid covariance of a yielded reference model, and a nonrigid
material panel with both-domain yielding and restart. These do not qualify
imperfect material capacity, arbitrary geometry or the complete G4C scope.

[Virgin material reference evidence](agent_plans/development/r8-material-reference-20261003/results.md).

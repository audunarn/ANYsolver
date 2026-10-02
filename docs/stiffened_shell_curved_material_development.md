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
curved material arc continuation, spectra and stress-free reference construction
remain unsupported. The older curved elastic policy, defaults and checkpoint
decoding contracts keep their meanings. No publication or qualification follows.

The finite fixed-step driver retains its default eight backtracks. For this new
policy only, an explicit `max_backtracks` up to 16 is admitted; adaptive stepping
retains its maximum 12. A bounded reload test needed a first improving step below
the legacy twelve-halving resolution. Its failed fixed and adaptive attempts are
preserved. The larger explicit budget changes permitted work, not equilibrium
tolerances or the globalization method, and makes no speedup claim.

Results recover actual Q4 layer strains, stresses, plastic strains and hardening
variables, native beam cell resultants and accumulated station history. The
`beam_generalized_material` detailed last-increment records remain empty in this
route. Its force-control snapshot stores the accepted Markov state, not the prior
increment's material predecessor. Restore therefore supports accepted-state
reconstruction and continuation; it does not promise the prior return-map tangent
or last-increment dissipation. Extending that recovery/checkpoint contract is a
separate open obligation.

ANYfem uses the existing `ExperimentalGEPointPanel` and the distinct strict
`anyfem.experimental-ge-curved-q4-point-panel-material-v2` input schema.
Standalone and ordinary Project save/reopen preserve the policy and owned native
beam definitions. Accepted solver state still needs its separate checkpoint.
Capabilities and persistence remain `EXPERIMENTAL_NOT_QUALIFIED`.

Development evidence, including failed attempts, artifact identities and precise
checks: [curved material slice](agent_plans/development/r8-curved-material-20261003/results.md).

# Committed native material recovery — 5 October 2026

The existing physical-fibre contact owner now recovers a bound committed checkpoint
through its actual fibre backend. It returns detached optional station fields and
per-increment energy summaries using each previous committed material origin.
No solver, state schema, contact law, geometry or mechanical tangent changes.

Native stored energy includes elastic and hardening storage. Section densities
are multiplied by reference arclength quadrature weights. Shell storage uses the
admitted elastic reference stiffness. Contact penalty storage remains separate.
Plastic dissipation is incremental and cumulative; the incremental variational
material potential is labelled explicitly and never renamed physical work.
Energy balance and independent engineering acceptance are explicitly unqualified.

Independent rational section equations validate elastic/background and hardening
storage, dissipation and incremental potential at recovered strains. Maximum
integrated differences are6.61744e-24J and4.13590e-25J in active/open states.
The oracle does not independently solve the beam-cell or coupled problem.

Raw: `C:/ANYworkspaceWork/contact_native_fibre_s3_20261005/candidate03`.

| Batch | Actual outcome |
|---|---|
| source_material_results | 4passed,16.7877s/182861824B; energy units/origins, detached fields, invalid bindings and reporting interruptions |
| source_material_publication | 4passed,11.8895s/183193600B; explicit replay-completed fault assertion and publication cancellation, plus binding check |
| source_material_cli | 1passed,6.5004s/181129216B; example exports a saved checkpoint, with solve forbidden |
| installed_material_results | 6passed,21.5244s/184647680B; complete final API and CLI checks in installed artifact |

Five source cases then one added CLI case; overlapping batches are not additional
unique cases. Existing active/open fixtures and science evidence are reused by
impact analysis. No expensive solve was repeated. Same-family supporting review
found no consequential error in energies, origins, measure or detachment. Its
initial fault-phase finding was incorrect: replay calls the module-level cell
return, while reporting invokes `PhysicalFibreSection.response`. Source inspection
resolved the distinction and an explicit post-replay assertion passed.

Production methods are new, so a new wheel is built for installed verification:
`50cff5fe9e52b68d25cd65d5f6dc46a946596db0d8f5e5d6ebff49db8a2adfc0`.
All525production files match,219imports bind the installed tree including the new
recovery module, JIT is disabled and both effective BLAS pools have1thread.
[Installed resources and identities](material_results_summary.json).
Independent engineering acceptance, complete work/energy balance, native convergence
and the remaining C0–C9 programme remain open. No release or speedup claim.

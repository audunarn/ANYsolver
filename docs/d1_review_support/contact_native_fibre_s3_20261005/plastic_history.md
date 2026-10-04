# Plastic-fibre contact history development — 5 October 2026

The existing native contact owner uses its actual physical-fibre returns and
retained internal coordinates. This fixture explicitly selects Y=2Pa and linear
hardening H=1e5Pa. The prior elastic response reaches5.73643Pa, predicting yielding.
All geometry, loads, reference support, contact stiffness1e7N/m³,30um gap and
integration/path controls remain unchanged. No production kernel changed.

The existing rational section oracle enumerates return candidates independently
of the production return map. Given production-recovered station strains and
committed origins, it checks fibre stress, tangent, increments, signed and
accumulated plastic strain, and all six section resultants. It does not supply an
independent cell-conjugate or nonlinear coupled equilibrium solution.

Raw: `C:/ANYworkspaceWork/contact_native_fibre_s3_20261005/candidate02`.

| Batch | Actual outcome |
|---|---|
| plastic_local | 1passed,3.9125s/181760000B;12yielded entries,3.54018e-9J dissipation; directional errors1.00186e-8/4.48621e-8 |
| plastic_first_contact | 1passed,105.6947s/181829632B;37candidate/pair evaluations;12yielded entries,3.41145e-9J dissipation; actual committed history and material-bound restart |
| installed_plastic_prefix | 3passed,15.1431s/181432320B; saved-state positive force/potential and equal/opposite wrench; invented-history rejection; exception/cancellation preserve nonvirgin prefix |
| installed_plastic_unloading | 1passed,44.4019s/182288384B; committed-origin continuation opens contact,6yielded entries/2.97122e-10J additional dissipation; nondecreasing accumulated strain and full two-record replay |
| installed_plastic_recontact | 1passed,100.6586s/182091776B; positive contact,10yielded entries/2.18051e-10J additional dissipation; nondecreasing accumulated strain and complete three-record byte-exact replay |

The first-contact test initially omitted a positive-contact assertion. Supporting
review found that gap alone did not establish activation. The assertion was added,
then the completed checkpoint was explicitly checked by the installed prefix
case. No unchanged expensive solve was repeated merely to add that assertion.

Installed checks use wheel813b08560894ae4b68f84b8e4eb55c91da845c91bca5ae9ff9a093d273c3f6a1.
Its524production files remain byte-identical. Example and verification changes
do not require a new wheel. Final runtime records bind actual installed imports
and effective settings. Supporting review is same-family scrutiny, not independent
engineering acceptance. Local/Mistral availability remains unchanged/unavailable.

Supporting delta review found no new source defect. It confirms that faults are
injected after prefix validation and unloading uses the actual committed origins.
The completed recontact result closes those development checks. Final supporting
review found no consequential issue in the third-target assertions. These are
five installed cases across three bounded jobs, not an uninterrupted full solve.

Gaps at the three accepted targets are−15.0131um,+92.3421um,−15.0043um.
Normal beam reactions are0.00540210N,0,0.00540207N. Material dissipation is
reported separately from contact regularization potential; unloading includes
genuine reverse yielding. This is not an energy-balance qualification.
Completed checkpoint SHA256:
`fddc268042fbe95123271ba9222b520828efe3acd7c1c8b49e73b6545fbe1659`.
[Machine-readable resources, fixtures and references](plastic_summary.json).

Plastic constitutive oracle agreement, trial-origin immutability and actual
nonvirgin state are development evidence. Full plastic contact admission requires
additional programme convergence, material/work accounting and independent
assessment. No release, speedup or uninterrupted-cycle claim follows.

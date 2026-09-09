# Spatial continuum comparison — bounded diagnostic closeout

Disposition: PRIVATE_SPATIAL_ELASTIC_CONTINUUM_COMPARISON_ONLY.
Full GE-B3 goal remains ACTIVE. No production qualification or activation.

Frozen corrected source: e40cc66f7bc02270931f75290c535be05c011239,
tree 474737cfce851168bbbf13b5bbb4ee3961fee6de. The correction changes only
off-collocation validation sampling, its tests and incident documentation.
No src, mechanics, state, recovery, aliases, default or version changes.

## Result and scope

The separately coded quaternion rod continuum resolves all four saved N20
spatial elastic arch equilibria, at signed quarter-point amplitudes 0.003
and 0.006. It imports no ANYsolver mechanics; the saved FE fields supply an
initial guess only. The source theory and derived reference equations are
documented in GE_BEAM3_SPATIAL_CONTINUUM_REFERENCE.md. This is a same-author
reference implementation, not independent authorship review or multiprecision.

Worst errors over the four BVP9 comparisons:

| Comparison | Relative error |
| --- | ---: |
| Vertical load | 0.9031% |
| Full nodal displacement | 1.6653% |
| 160-station resultant energy norm | 0.8658% |
| Strain energy | 1.3016% |

All four quantities pass the existing 2% engineering comparison in each case.
All tighter-profile replica pairs are directly byte-identical. Loose/tight
profile load differences are at most 1.408e-8 relative. This is profile
convergence of the reference, not FE mesh refinement or branch uniqueness.

## Validation-grid incident and correction

Initial source 4d10de102dcea40270a7607de8a46d0b3264acfc used a fixed
257-site differential check. On the tighter 384-interval solution those sites
coincide with collocation nodes or midpoints. Its tiny differential residual
was not independent off-mesh validation. All original solutions, comparisons,
receipts and initial audit remain preserved without reclassification.

The corrected check samples two interior Gauss points in every actual
collocation interval: 768 sites per segment on every tight solution.
Maximum normalized differential residual is 1.6064e-10, inside the unchanged
profile check. No equations, solver tolerances, source fields or engineering
comparison were changed. The saved-data audit confirms exact equality of
every original/corrected scientific field except revision and validation
metadata; solver loads, knots, iterations and callback counts also agree.

## Separate tests and executions

Resume unit inventory: 11 passed in 0.45 seconds, fresh basetemp
ge-beam3-spatial-continuum-unit-resume-20260909. Previous truncated test output
was not assumed successful. Saved-data audit inventory: 2 passed in 0.020
seconds, including 13 mutation subcases (validation policy, site count and
nonfinite residual included). These are separate inventories, not a combined
qualification count. Test outcomes were observed in tool output; raw pytest
stdout was not separately archived and is not claimed to have been.

Corrected smoke plus wave: 12 completed reference-only processes, all exit 0
and empty Windows Job trees. Smoke 0.911 seconds; wave about 7.64 seconds;
longest child 1.416 seconds. Largest process-tree peak 1,716,170,752 bytes.
At most three concurrent workers, one numerical thread each, 24 GiB and
600 seconds per child, 1800 seconds per wave, 120-second CPU inactivity.
The continuum callback guard additionally enforces 60 seconds/2000 callbacks.
No automatic retry and no completed FE/onset/native-analysis campaign rerun.

## Preservation

Both 73-file archives were verified before and after external copying.
All original TEMP outputs and workspace mirrors remain intact.

Initial incident archive:
C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-spatial-continuum-grid-incident-4d10de1-20260909

Manifest 10143 bytes, SHA256
9efadaa11eae491802daae3f4030e1d2a615bb06cdb1971abbf0b68b465c9e0a.

Corrected archive:
C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-spatial-continuum-e40cc66-20260909

Manifest 10154 bytes, SHA256
43279d1c2ab2f76cf53f1aa3b15015b7475d15832f9751913b3bc62b486e5992.
Saved audit 7738 bytes, SHA256
2ff2a6749101f15de6a64f74c479193319c340f7c820b3cd98dbb2bbe8bf7463.

Canonical summary: docs/reference_cases/ge_beam3_spatial_continuum_status.json.
The archive includes the actual helper sources, commands, stdout/stderr,
process receipts and all comparison records. The audit verifies saved-data
identities and arithmetic; it is not an independent reconstruction of the
full ODE or an independently authored review.

## Next unresolved work

Develop the authenticated elastic-seed-to-continuation owner/handoff and
verify spatial branch continuation, cancellation and restart against original
checkpoints. Retain strict separation from plastic history. Add actual FE
refinement/branch comparison and independent source-equation review; a binary64
reference profile comparison alone does not close these gates. Broader solver,
material/dynamic parity, installed explicit selection and objective eccentric/
curved beam-shell joints remain open. Do not repeat completed onset or native
analysis campaigns as a substitute. No main update, push, merge or release.

NO_GO_PRODUCTION_RESTRICTION_UNCHANGED. Existing B2/B3/S3/Q4 and defaults unchanged.

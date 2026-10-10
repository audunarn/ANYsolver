# Two-body mortar reference outcome

Delivered an independent moving-overlap original-Q1 contact reference and a common-geometry/common-operator pressure-trace discriminator. Six bounded installed-artifact testcase invocations passed. No production files changed and no new mesh or physics candidate was run.

## Code verification

| Evidence | Observed error | Gate |
| --- | ---: | ---: |
| Base/refined actual-pose support comparison | <=1.24e-15 m^2 | 1e-10 m^2 |
| Actual-pose weighted gap comparison | <=1.43e-18 m^3 | 1e-12 m^3 |
| Full skin/spatial force-and-couple comparison | <=2.20e-10 normalized | 1e-6 |
| Independent physical-spin work comparison | <=4.63e-11 relative | 1e-6 |
| Independent contact q/z directional tangent | 7.08499e-7 relative | 1e-5 |
| Outer contact derivative resolution | 6.05160e-7 relative | 1e-5 |
| Inner-FD directional influence | 5.93024e-7 relative | 1e-5 |
| Independent chart-gap directional derivative | 4.88023e-12 relative | 1e-5 |

The qualified structural tangent is openly reused. The independently measured contact discrepancy in the full coupled tangent scale was 1.25474e-14; this does not replace the stronger contact-scale check. Exact common-frame Q1 rectangle support/normal-work checks passed for both spaces. A focused added test closed flat a_i=0.2um*S_i and psi=0.2um*sum(z_i) identities and projected target/source-bin chart refusals. Independent scalar and derivative self-resolution passed at the frozen rules/steps before comparison claims.

Accepted loaded poses retained the prior dimensional gap, complementarity, reaction-aware equilibrium and free-bending criteria. Independent physical force and moment balance errors were <=5.23e-11 against separate 1e-4 N and 1e-4 N m scales. Overlap work-allocation bin forces sum to the independent total with zero measured closure error. The observed force/moment change is entirely in the right registered material-X bin; the left bin has zero allocated contact work-force for these accepted active traces.

## Physical response interpretation

Observed refined-minus-base source resultant:

(-1.4595340504e-5, -4.0341325134e-11, -8.4267071851e-6) N.

Mapping both accepted pressure traces onto the SAME fine geometry gives:

(-1.4595420670e-5, -1.3057028208e-11, -8.4266400603e-6) N.

Observed-minus-common-geometry remainder:

(8.0165925412e-11, -2.7284296926e-11, -6.7124771751e-11) N.

Thus the accepted pressure fields on common geometry nearly reproduce the earlier 1.68533e-5 N resultant change. This is an action-oriented diagnostic identity, not proof that pressure refinement alone caused it: each accepted field contains its mesh's coupled structural response. The small remainder has no new physical acceptance gate.

The fixed-operator scaled chart-response difference between accepted traces was 5.91659e-6 (translation scaled by 1 m, rotation by 1 rad). The signed checkerboard projection error was 4.66797e-5 Pa m, and its corresponding scaled chart-response difference was 8.64348e-7. These signed probes are not nonnegative equilibria. Omitting baseline fixed-z contact geometric stiffness changes the fine response operator by 1.36445e-6 relative; the actual comparison includes that stiffness in one unchanged Kcommon for both spaces.

No 2% spatial-convergence, mesh-uniform stability or pressure-admission pass follows from these numbers. The bounded two-body contact CODE dependency is supported; the next physical dependency is an independently solved matched equilibrium on fixed structure with separately chosen pressure trace space, followed by overlap-supported physical response comparison. That requires a prospective scientific/architecture decision; no production basis change or additional refinement was made here.

## Execution and evidence

TWO_BODY_MORTAR_REFERENCE_DEV600 used 93.7806644999946/600 measured process-wall seconds in six serial jobs; remaining506.2193355000054 s, protected60 s unused. Every job was <=60 s and953MiB. All six test invocations passed; no numerical NONPASS or timeout occurred. Initial and review-delta sources, commands, effective runtime, logs, JUnit and immutable mechanics copies are preserved per attempt. No active process remains.

The unchanged wheel SHA256 is d38c213f96ae85175a5bd0ead0a1628ba385884b555244a4670e6e2516ca4fb2, with634 payloads. Exact source/input/output/runtime hashes and counts are in C:/ANYworkspaceWork/contact_two_body_mortar_reference_20261008/CLOSURE.json. Engineering acceptance and release are false.

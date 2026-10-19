# Measured accuracy and support

These values concern the selected declared finite-penalty examples, not ideal hard-contact error or universal model accuracy. The unchanged original tests remain separate from these prospective candidate metrics.

| Case / quantity | Actual | Independent expected | Relative error (%) |
|---|---:|---:|---:|
| S3/plane / normal shell force N | 0.3 | 0.3 | 0 |
| S3/plane / rigid normal force N | -0.3 | -0.3 | 0 |
| S3/plane / gap m | -6.00000000003E-07 | -6E-07 | 5.6262399E-10 |
| B3/plane / active line length m | 0.408248290464 | 0.408248290464 | 4.0792199E-14 |
| B3/plane / gap m | -0.001 | -0.001 | 8.6736174E-14 |
| physical S3 uniform Coulomb slip / source tangential reaction N step3 | 0.000240000000008 | 0.00024 | 3.4349897E-09 |
| physical S3 uniform Coulomb slip / source tangential reaction N step5 | -0.000239999999993 | -0.00024 | 2.8555062E-09 |

All seven predeclared analytical quantities satisfy0.1%. The Coulomb values concern the uniform flat-pressure resultant, not independently validated structural displacement.

Supplemental post-run B3 reference-line penalty force check (not a new acceptance criterion): measured 2.72165526975909N, integral reference 2.72165526975909N, relative error 1.63168794661262E-15.

The B3 example gap is -0.001m with declared tolerance0.002m and radius0.01m. S3/plane gap is approximately-6e-7m with tolerance1e-6m. These are chosen penalty/gap demonstrations; select justified stiffness and dimensional limits before any new engineering case.

## Lifecycle and numerical consistency

Installed guided shell-pair target-node9 displacement: -1.66861067257453E-05m. All-free normalized equilibrium error: 5.86423850361607E-09. Upper actuator/rotations and lower supports remain guided; only lower node9 has a free normal DOF. Both-body instantaneous virtual/residual work is recorded, not path-integrated work.
Physical friction normalized wrench maximum: 8.47033746744714E-18; coupled equilibrium maximum: 1.23539348781225E-12. Target normal/rotations are fixed; target in-plane elasticity is exercised.

Both active-prefix and open-prefix restarts have zero endpoint displacement difference and exact unchanged history assertions passing. Candidate mixed-norm replay bound is separately satisfied. Thirteen physical-quantity comparisons between effectiveSkylakeX and Haswell BLAS profiles pass on this one host. Cross-machine/Ubuntu comparison was not run.

## Accuracy not established

No independent matched coupled displacement/reaction reference was available for the guided shell pair or crossed beams. No generic2% response accuracy claim is made for them. Equilibrium, line integration error, restart parity and plausible response are not substitutes for independent response validation. See KNOWN_LIMITATIONS.md.

Actual complete outputs, per-quantity bounds, phase reactions/dissipation and evidence references are in MEASURED_SUPPORT.json and evidence/.

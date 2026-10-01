# S3 angle campaign: target 15 deg

## Membrane (Timoshenko cantilever, exact Dirichlet field)
| family | narrow | min angle | levels: energy-norm error | rate | N L2 error (finest) |
|---|---|---:|---|---|---:|
| regular | y | 45.00 | 9.347e-01, 4.691e-01, 2.350e-01, 1.176e-01 | 0.99, 1.00, 1.00 | 1.178e-01 |
| right | y | 15.00 | 6.600e-01, 3.314e-01, 1.660e-01, 8.306e-02 | 0.99, 1.00, 1.00 | 6.903e-02 |
| right | x | 15.00 | 7.500e-01, 3.750e-01, 1.875e-01, 9.379e-02 | 1.00, 1.00, 1.00 | 1.035e-01 |
| right_alternating | x | 15.00 | 7.346e-01, 3.640e-01, 1.812e-01, 9.038e-02 | 1.01, 1.01, 1.00 | 9.721e-02 |
| obtuse | y | 15.00 | 4.402e-01, 2.214e-01, 1.110e-01, 5.560e-02 | 0.99, 1.00, 1.00 | 4.489e-02 |
| obtuse | x | 15.00 | 3.632e-01, 1.811e-01, 9.063e-02, 4.536e-02 | 1.00, 1.00, 1.00 | 5.057e-02 |

## Plate bending (SS Mindlin plate, uniform pressure)
| t | family | min angle | w_c error by level | compliance rate | M L2 error by level | M rate |
|---|---|---:|---|---|---|---|
| 0.01 | regular | 45.00 | 2.02e-02, 4.39e-03, 8.86e-04, 1.42e-04 | 2.47, 2.42, 2.74 | 3.03e-01, 1.56e-01, 7.85e-02, 3.93e-02 | 0.96, 0.99, 1.00 |
| 0.01 | right | 15.00 | 5.27e-02, 1.16e-02, 2.65e-03, 5.39e-04 | 2.02, 2.12, 2.28 | 2.24e-01, 1.14e-01, 5.74e-02, 2.87e-02 | 0.97, 0.99, 1.00 |
| 0.01 | right_alternating | 15.00 | 5.19e-02, 1.17e-02, 2.70e-03, 5.56e-04 | 1.99, 2.10, 2.27 | 2.29e-01, 1.17e-01, 5.84e-02, 2.90e-02 | 0.97, 1.00, 1.01 |
| 0.01 | obtuse | 15.00 | 3.33e-02, 6.25e-03, 1.26e-03, 2.12e-04 | 2.11, 2.26, 2.48 | 1.63e-01, 8.20e-02, 4.07e-02, 2.01e-02 | 0.99, 1.01, 1.02 |
| 0.001 | regular | 45.00 | 2.03e-02, 4.51e-03, 9.99e-04, 2.31e-04 | 2.44, 2.28, 2.16 | 3.03e-01, 1.56e-01, 7.85e-02, 3.93e-02 | 0.96, 0.99, 1.00 |
| 0.001 | right | 15.00 | 5.32e-02, 1.21e-02, 3.00e-03, 7.44e-04 | 1.98, 2.00, 2.01 | 2.24e-01, 1.14e-01, 5.74e-02, 2.87e-02 | 0.97, 0.99, 1.00 |
| 0.001 | right_alternating | 15.00 | 5.24e-02, 1.21e-02, 3.04e-03, 7.58e-04 | 1.95, 1.99, 2.00 | 2.29e-01, 1.17e-01, 5.87e-02, 2.94e-02 | 0.97, 0.99, 1.00 |
| 0.001 | obtuse | 15.00 | 3.39e-02, 6.83e-03, 1.68e-03, 4.13e-04 | 2.03, 2.01, 2.02 | 1.63e-01, 8.27e-02, 4.16e-02, 2.08e-02 | 0.98, 0.99, 1.00 |

## Mixed Q4/S3 panels (t/L = 0.01)
| pattern | S3 fraction (finest) | min angle | w_c error: target / same layout at 30 deg / all-Q4, by level | S3 M L2 error (finest) |
|---|---:|---:|---|---:|
| isolated | 0.006 | 15.00 | 1.70e-02/3.22e-02/1.34e-02, 3.91e-03/8.12e-03/2.88e-03, 1.00e-03/2.12e-03/7.06e-04, 2.53e-04/5.38e-04/1.75e-04 | 9.470e-03 |
| chain | 0.072 | 15.00 | 4.49e-02/5.89e-02/1.34e-02, 1.09e-02/1.59e-02/2.88e-03, 2.71e-03/4.11e-03/7.06e-04, 6.82e-04/1.05e-03/1.75e-04 | 2.634e-02 |
| boundary | 0.072 | 15.00 | 5.22e-02/7.20e-02/1.34e-02, 1.18e-02/1.76e-02/2.88e-03, 2.83e-03/4.36e-03/7.06e-04, 6.96e-04/1.08e-03/1.75e-04 | 2.869e-02 |
| cluster | 0.108 | 15.00 | 5.46e-02/2.21e-02/1.34e-02, 1.62e-02/2.44e-03/2.88e-03, 4.45e-03/6.22e-04/7.06e-04, 1.17e-03/4.13e-04/1.75e-04 | 4.441e-03 |
| quarter | 0.238 | 15.00 | 5.98e-02/2.76e-02/1.34e-02, 1.57e-02/1.37e-02/2.88e-03, 4.04e-03/4.23e-03/7.06e-04, 1.20e-03/8.55e-04/1.75e-04 | 2.669e-02 |

## Modal and buckling (t/L = 0.01)
| family | level | f errors (first 3) | buckling error |
|---|---:|---|---:|
| regular | 2 | 4.14e-04, 1.15e-03, 1.72e-03 | 4.05e-03 |
| regular | 3 | 6.49e-05, 3.10e-04, 3.48e-04 | 9.33e-04 |
| right | 2 | 1.40e-03, 8.61e-04, 5.05e-03 | 6.02e-03 |
| right | 3 | 2.86e-04, 1.72e-04, 1.09e-03 | 1.38e-03 |
| obtuse | 2 | 7.13e-04, 2.58e-04, 4.50e-03 | 3.61e-03 |
| obtuse | 3 | 1.25e-04, 8.56e-05, 9.48e-04 | 7.93e-04 |
| mixed_chain | 3 | 9.04e-04, 3.48e-03, 3.54e-03 | n/a |
| mixed_quarter | 3 | 8.65e-04, 3.16e-03, 3.48e-03 | n/a |

## Corotational end-moment strip (1 rad end rotation, nu = 0, consistent tangent)
| family | min angle | status | tip error | Newton iterations |
|---|---:|---|---:|---|
| regular (level 2) | 45.00 | completed | 5.14e-05 | 56 (8 steps) |
| right (level 2) | 15.00 | completed | 5.14e-05 | 51 (8 steps) |
| obtuse (level 2) | 30.00 | completed | 2.56e-04 | 40 (8 steps) |
| obtuse (level 2) | 15.00 | completed | 4.62e-03 | 40 (8 steps) |

## Criteria
- PASS element_rigid_and_symmetry: 3.493014909508446e-16
- PASS element_patch_tests: 8.992806499463768e-14
- PASS element_twelve_elastic_modes: 0.002648688486832556
- PASS membrane_regular_y_displacement: 1.8293379764750465e-05
- PASS membrane_regular_y_rate: {"rate": [0.9946089789066189, 0.997383830639374, 0.998743299276234], "regular": 0.998743299276234}
- PASS membrane_right_y_resultant_vs_regular_at_equal_dofs: {"ratio": 1.1088545608915417, "absolute": 0.06902573926336952}
- PASS membrane_right_y_displacement: 1.5058723284906277e-05
- PASS membrane_right_y_rate: {"rate": [0.9941064445528363, 0.9974334174027645, 0.9987983323785475], "regular": 0.998743299276234}
- FAIL membrane_right_x_resultant_vs_regular_at_equal_dofs: {"ratio": 1.7524100781051088, "absolute": 0.10345052024721832}
- PASS membrane_right_x_displacement: 8.273289068268752e-06
- PASS membrane_right_x_rate: {"rate": [1.0000029478334291, 0.9996616117833276, 0.9997256382508451], "regular": 0.998743299276234}
- FAIL membrane_right_alternating_x_resultant_vs_regular_at_equal_dofs: {"ratio": 1.6466148325490757, "absolute": 0.09720507956572653}
- PASS membrane_right_alternating_x_displacement: 2.6153259176047318e-05
- PASS membrane_right_alternating_x_rate: {"rate": [1.0131454490368494, 1.0064748600396098, 1.0031727991916157], "regular": 0.998743299276234}
- PASS membrane_obtuse_y_resultant_vs_regular_at_equal_dofs: {"ratio": 1.0305396485642242, "absolute": 0.04489343070225582}
- PASS membrane_obtuse_y_displacement: 9.156883293491589e-05
- PASS membrane_obtuse_y_rate: {"rate": [0.9913850650720104, 0.9957705234035829, 0.997891319945551], "regular": 0.998743299276234}
- PASS membrane_obtuse_x_resultant_vs_regular_at_equal_dofs: {"ratio": 1.2142301082311093, "absolute": 0.050571762475739857}
- PASS membrane_obtuse_x_displacement: 2.9146479601884657e-05
- PASS membrane_obtuse_x_rate: {"rate": [1.0037830003782984, 0.9989324302001186, 0.9987249744564043], "regular": 0.998743299276234}
- PASS plate_t0.01_regular_centre_deflection: 0.00014200204865677613
- PASS plate_t0.01_regular_moment_l2: 0.03932587175973968
- PASS plate_t0.01_right_centre_deflection: 0.0005390681428814644
- PASS plate_t0.01_right_moment_l2: 0.02874169046640747
- PASS plate_t0.01_right_alternating_centre_deflection: 0.0005560489636382802
- PASS plate_t0.01_right_alternating_moment_l2: 0.029041748811102004
- PASS plate_t0.01_obtuse_centre_deflection: 0.00021190290382862826
- PASS plate_t0.01_obtuse_moment_l2: 0.020062896697111695
- PASS plate_t0.001_regular_centre_deflection: 0.00023052753194871062
- PASS plate_t0.001_regular_moment_l2: 0.03932837642509854
- PASS plate_t0.001_right_centre_deflection: 0.0007435264531173637
- PASS plate_t0.001_right_moment_l2: 0.02874523564458602
- PASS plate_t0.001_right_alternating_centre_deflection: 0.0007580859795625522
- PASS plate_t0.001_right_alternating_moment_l2: 0.02941014158136418
- PASS plate_t0.001_obtuse_centre_deflection: 0.0004133068021486808
- PASS plate_t0.001_obtuse_moment_l2: 0.020791284511583612
- PASS plate_t0.01_right_moment_rate: {"rate": [0.974586991665358, 0.9921297277545208, 0.9977993090692471], "regular": 0.9974110562590696}
- PASS plate_t0.01_right_alternating_moment_rate: {"rate": [0.972455230888187, 0.9968773008926023, 1.0078933891977395], "regular": 0.9974110562590696}
- PASS plate_t0.01_obtuse_moment_rate: {"rate": [0.9899974003354765, 1.0120590830599734, 1.0191166194477812], "regular": 0.9974110562590696}
- PASS plate_t0.001_right_moment_rate: {"rate": [0.9746620344025471, 0.9922483451124662, 0.9979737865466687], "regular": 0.997433094957714}
- PASS plate_t0.001_right_alternating_moment_rate: {"rate": [0.9706481617910862, 0.9913773448234707, 0.9980563981994335], "regular": 0.997433094957714}
- PASS plate_t0.001_obtuse_moment_rate: {"rate": [0.9821128589173098, 0.993179732374698, 0.9995180868875054], "regular": 0.997433094957714}
- PASS mixed_isolated_centre_deflection: {"mixed": 0.0002527260640913942, "layout_30": 0.0005383696764028252, "all_q4": 0.00017542390210183092}
- PASS mixed_isolated_centre_deflection_vs_30: {"mixed": 0.0002527260640913942, "layout_30": 0.0005383696764028252, "all_q4": 0.00017542390210183092}
- PASS mixed_isolated_s3_moment_l2: 0.009469551222621442
- PASS mixed_chain_centre_deflection: {"mixed": 0.0006818235032478472, "layout_30": 0.0010525244529584422, "all_q4": 0.00017542390210183092}
- PASS mixed_chain_centre_deflection_vs_30: {"mixed": 0.0006818235032478472, "layout_30": 0.0010525244529584422, "all_q4": 0.00017542390210183092}
- PASS mixed_chain_s3_moment_l2: 0.02633588691747096
- PASS mixed_boundary_centre_deflection: {"mixed": 0.0006964168515200662, "layout_30": 0.0010842765026604364, "all_q4": 0.00017542390210183092}
- PASS mixed_boundary_centre_deflection_vs_30: {"mixed": 0.0006964168515200662, "layout_30": 0.0010842765026604364, "all_q4": 0.00017542390210183092}
- PASS mixed_boundary_s3_moment_l2: 0.028692636124316103
- PASS mixed_cluster_centre_deflection: {"mixed": 0.001171192337984059, "layout_30": 0.00041269471329230333, "all_q4": 0.00017542390210183092}
- PASS mixed_cluster_centre_deflection_vs_30: {"mixed": 0.001171192337984059, "layout_30": 0.00041269471329230333, "all_q4": 0.00017542390210183092}
- PASS mixed_cluster_s3_moment_l2: 0.00444068456185136
- PASS mixed_quarter_centre_deflection: {"mixed": 0.0011954100142704443, "layout_30": 0.0008549675651364173, "all_q4": 0.00017542390210183092}
- PASS mixed_quarter_centre_deflection_vs_30: {"mixed": 0.0011954100142704443, "layout_30": 0.0008549675651364173, "all_q4": 0.00017542390210183092}
- PASS mixed_quarter_s3_moment_l2: 0.02669274300269511
- PASS modal_regular_first_frequency: {"errors": [6.488575769286703e-05, 0.0003097863491346672, 0.00034753607285920843]}
- PASS buckling_regular: 0.0009332626316025369
- PASS modal_right_first_frequency: {"errors": [0.0002861293775372388, 0.00017205918378646406, 0.0010906701458811387]}
- PASS buckling_right: 0.00137636279809582
- PASS modal_obtuse_first_frequency: {"errors": [0.00012493849142278013, 8.557291471706629e-05, 0.0009477026419049597]}
- PASS buckling_obtuse: 0.0007934546008733379
- PASS modal_mixed_chain_first_frequency: {"errors": [0.0009036633472092241, 0.0034766211087807926, 0.0035407035609033915], "layout_30": [0.0008833442673609563, 0.0033795365668589147, 0.0034928529570812526]}
- PASS modal_mixed_quarter_first_frequency: {"errors": [0.0008652502927271087, 0.0031633752908160565, 0.0034757506158600328], "layout_30": [0.0007912477719702082, 0.0028282846242655966, 0.0033066128301262256]}
- PASS nonlinear_regular_45_end_moment: {"status": "completed", "tip_error": 5.135172705150483e-05}
- PASS nonlinear_regular_45_iterations: {"iterations": [7, 7, 7, 7, 7, 7, 7, 7], "regular": [7, 7, 7, 7, 7, 7, 7, 7]}
- PASS nonlinear_right_15_end_moment: {"status": "completed", "tip_error": 5.135172705684715e-05}
- PASS nonlinear_right_15_iterations: {"iterations": [6, 7, 7, 7, 6, 6, 6, 6], "regular": [7, 7, 7, 7, 7, 7, 7, 7]}
- PASS nonlinear_obtuse_30_end_moment: {"status": "completed", "tip_error": 0.00025579374224551563}
- PASS nonlinear_obtuse_30_iterations: {"iterations": [5, 5, 5, 5, 5, 5, 5, 5], "regular": [7, 7, 7, 7, 7, 7, 7, 7]}
- PASS nonlinear_obtuse_15_end_moment: {"status": "completed", "tip_error": 0.004619459704723619}
- PASS nonlinear_obtuse_15_iterations: {"iterations": [5, 5, 5, 5, 5, 5, 5, 5], "regular": [7, 7, 7, 7, 7, 7, 7, 7]}

**All required criteria passed: False**

# S3 angle campaign: target 20 deg

## Membrane (Timoshenko cantilever, exact Dirichlet field)
| family | narrow | min angle | levels: energy-norm error | rate | N L2 error (finest) |
|---|---|---:|---|---|---:|
| regular | y | 45.00 | 9.347e-01, 4.691e-01, 2.350e-01, 1.176e-01 | 0.99, 1.00, 1.00 | 1.178e-01 |
| right | y | 20.00 | 7.087e-01, 3.559e-01, 1.783e-01, 8.923e-02 | 0.99, 1.00, 1.00 | 7.638e-02 |
| right | x | 20.00 | 7.634e-01, 3.818e-01, 1.910e-01, 9.551e-02 | 1.00, 1.00, 1.00 | 1.044e-01 |
| right_alternating | x | 20.00 | 7.371e-01, 3.636e-01, 1.805e-01, 8.992e-02 | 1.02, 1.01, 1.01 | 9.431e-02 |
| obtuse | y | 20.00 | 4.527e-01, 2.276e-01, 1.141e-01, 5.715e-02 | 0.99, 1.00, 1.00 | 4.655e-02 |
| obtuse | x | 20.00 | 3.548e-01, 1.769e-01, 8.853e-02, 4.431e-02 | 1.00, 1.00, 1.00 | 4.816e-02 |

## Plate bending (SS Mindlin plate, uniform pressure)
| t | family | min angle | w_c error by level | compliance rate | M L2 error by level | M rate |
|---|---|---:|---|---|---|---|
| 0.01 | regular | 45.00 | 2.02e-02, 4.39e-03, 8.86e-04, 1.42e-04 | 2.47, 2.42, 2.74 | 3.03e-01, 1.56e-01, 7.85e-02, 3.93e-02 | 0.96, 0.99, 1.00 |
| 0.01 | right | 20.00 | 4.93e-02, 9.78e-03, 2.24e-03, 4.57e-04 | 2.03, 2.12, 2.27 | 2.31e-01, 1.17e-01, 5.91e-02, 2.96e-02 | 0.97, 0.99, 1.00 |
| 0.01 | right_alternating | 20.00 | 4.84e-02, 1.00e-02, 2.33e-03, 4.87e-04 | 1.98, 2.09, 2.25 | 2.37e-01, 1.21e-01, 6.07e-02, 3.01e-02 | 0.97, 1.00, 1.01 |
| 0.01 | obtuse | 20.00 | 2.81e-02, 4.21e-03, 8.62e-04, 1.39e-04 | 2.08, 2.23, 2.52 | 1.64e-01, 8.27e-02, 4.11e-02, 2.02e-02 | 0.98, 1.01, 1.02 |
| 0.001 | regular | 45.00 | 2.03e-02, 4.51e-03, 9.99e-04, 2.31e-04 | 2.44, 2.28, 2.16 | 3.03e-01, 1.56e-01, 7.85e-02, 3.93e-02 | 0.96, 0.99, 1.00 |
| 0.001 | right | 20.00 | 4.97e-02, 1.01e-02, 2.49e-03, 6.16e-04 | 2.00, 2.02, 2.02 | 2.31e-01, 1.18e-01, 5.91e-02, 2.96e-02 | 0.97, 0.99, 1.00 |
| 0.001 | right_alternating | 20.00 | 4.87e-02, 1.03e-02, 2.57e-03, 6.42e-04 | 1.96, 1.99, 2.00 | 2.37e-01, 1.21e-01, 6.11e-02, 3.06e-02 | 0.97, 0.99, 1.00 |
| 0.001 | obtuse | 20.00 | 2.85e-02, 4.54e-03, 1.12e-03, 2.75e-04 | 2.01, 2.01, 2.01 | 1.64e-01, 8.33e-02, 4.19e-02, 2.10e-02 | 0.98, 0.99, 1.00 |

## Mixed Q4/S3 panels (t/L = 0.01)
| pattern | S3 fraction (finest) | min angle | w_c error: target / same layout at 30 deg / all-Q4, by level | S3 M L2 error (finest) |
|---|---:|---:|---|---:|
| isolated | 0.006 | 20.00 | 2.05e-02/3.22e-02/1.34e-02, 4.88e-03/8.12e-03/2.88e-03, 1.26e-03/2.12e-03/7.06e-04, 3.19e-04/5.38e-04/1.75e-04 | 9.418e-03 |
| chain | 0.072 | 20.00 | 5.17e-02/5.89e-02/1.34e-02, 1.30e-02/1.59e-02/2.88e-03, 3.25e-03/4.11e-03/7.06e-04, 8.21e-04/1.05e-03/1.75e-04 | 2.666e-02 |
| boundary | 0.072 | 20.00 | 6.09e-02/7.20e-02/1.34e-02, 1.41e-02/1.76e-02/2.88e-03, 3.41e-03/4.36e-03/7.06e-04, 8.41e-04/1.08e-03/1.75e-04 | 3.249e-02 |
| cluster | 0.108 | 20.00 | 3.47e-02/2.21e-02/1.34e-02, 1.37e-02/2.44e-03/2.88e-03, 4.20e-03/6.22e-04/7.06e-04, 1.16e-03/4.13e-04/1.75e-04 | 4.491e-03 |
| quarter | 0.238 | 20.00 | 5.94e-02/2.76e-02/1.34e-02, 1.70e-02/1.37e-02/2.88e-03, 4.52e-03/4.23e-03/7.06e-04, 8.99e-04/8.55e-04/1.75e-04 | 2.720e-02 |

## Modal and buckling (t/L = 0.01)
| family | level | f errors (first 3) | buckling error |
|---|---:|---|---:|
| regular | 2 | 4.14e-04, 1.15e-03, 1.72e-03 | 4.05e-03 |
| regular | 3 | 6.49e-05, 3.10e-04, 3.48e-04 | 9.33e-04 |
| right | 2 | 1.18e-03, 4.78e-04, 4.38e-03 | 5.58e-03 |
| right | 3 | 2.42e-04, 8.70e-05, 9.51e-04 | 1.29e-03 |
| obtuse | 2 | 5.00e-04, 5.42e-04, 3.78e-03 | 3.31e-03 |
| obtuse | 3 | 8.49e-05, 1.50e-04, 8.00e-04 | 7.46e-04 |
| mixed_chain | 3 | 8.97e-04, 3.44e-03, 3.53e-03 | n/a |
| mixed_quarter | 3 | 8.43e-04, 3.04e-03, 3.43e-03 | n/a |

## Corotational end-moment strip (1 rad end rotation, nu = 0, consistent tangent)
| family | min angle | status | tip error | Newton iterations |
|---|---:|---|---:|---|
| regular (level 2) | 45.00 | completed | 5.14e-05 | 56 (8 steps) |
| right (level 2) | 20.00 | completed | 5.14e-05 | 53 (8 steps) |
| obtuse (level 2) | 30.00 | completed | 2.56e-04 | 40 (8 steps) |
| obtuse (level 2) | 20.00 | completed | 1.41e-03 | 40 (8 steps) |

## Criteria
- PASS element_rigid_and_symmetry: 3.493014909508446e-16
- PASS element_patch_tests: 4.030109579389318e-14
- PASS element_twelve_elastic_modes: 0.004671380465166405
- PASS membrane_regular_y_displacement: 1.8293379764750465e-05
- PASS membrane_regular_y_rate: {"rate": [0.9946089789066189, 0.997383830639374, 0.998743299276234], "regular": 0.998743299276234}
- PASS membrane_right_y_resultant_vs_regular_at_equal_dofs: {"ratio": 1.0312785906214708, "absolute": 0.07638207264784239}
- PASS membrane_right_y_displacement: 1.4965518155925635e-05
- PASS membrane_right_y_rate: {"rate": [0.9935995379150732, 0.9972036180939559, 0.9986894128017568], "regular": 0.998743299276234}
- FAIL membrane_right_x_resultant_vs_regular_at_equal_dofs: {"ratio": 1.5033909102682361, "absolute": 0.1044420775591686}
- PASS membrane_right_x_displacement: 9.676765938050335e-06
- PASS membrane_right_x_rate: {"rate": [0.9995810719143976, 0.9994746536404211, 0.9996439561620144], "regular": 0.998743299276234}
- PASS membrane_right_alternating_x_resultant_vs_regular_at_equal_dofs: {"ratio": 1.3574909762668554, "absolute": 0.09430626250350155}
- PASS membrane_right_alternating_x_displacement: 4.155902873202284e-05
- PASS membrane_right_alternating_x_rate: {"rate": [1.0195500647689406, 1.0102979763488322, 1.005208117069683], "regular": 0.998743299276234}
- PASS membrane_obtuse_y_resultant_vs_regular_at_equal_dofs: {"ratio": 0.8965347397592252, "absolute": 0.046553300324648994}
- PASS membrane_obtuse_y_displacement: 8.606775045793579e-05
- PASS membrane_obtuse_y_rate: {"rate": [0.9917773616702319, 0.9959653052426959, 0.9979891936730341], "regular": 0.998743299276234}
- PASS membrane_obtuse_x_resultant_vs_regular_at_equal_dofs: {"ratio": 0.9823034268970583, "absolute": 0.04816443151220206}
- PASS membrane_obtuse_x_displacement: 2.6622580468697296e-05
- PASS membrane_obtuse_x_rate: {"rate": [1.0037795073656617, 0.9988113029061119, 0.9986348847937145], "regular": 0.998743299276234}
- PASS plate_t0.01_regular_centre_deflection: 0.00014200204865677613
- PASS plate_t0.01_regular_moment_l2: 0.03932587175973968
- PASS plate_t0.01_right_centre_deflection: 0.0004574528761611337
- PASS plate_t0.01_right_moment_l2: 0.029581086239549397
- PASS plate_t0.01_right_alternating_centre_deflection: 0.0004870613251037878
- PASS plate_t0.01_right_alternating_moment_l2: 0.030103388604807463
- PASS plate_t0.01_obtuse_centre_deflection: 0.00013880767884095243
- PASS plate_t0.01_obtuse_moment_l2: 0.020214887102840924
- PASS plate_t0.001_regular_centre_deflection: 0.00023052753194871062
- PASS plate_t0.001_regular_moment_l2: 0.03932837642509854
- PASS plate_t0.001_right_centre_deflection: 0.0006156297936689884
- PASS plate_t0.001_right_moment_l2: 0.02958398860964326
- PASS plate_t0.001_right_alternating_centre_deflection: 0.0006422156254623885
- PASS plate_t0.001_right_alternating_moment_l2: 0.030594105908869768
- PASS plate_t0.001_obtuse_centre_deflection: 0.00027532177342407134
- PASS plate_t0.001_obtuse_moment_l2: 0.020957146610247123
- PASS plate_t0.01_right_moment_rate: {"rate": [0.9728412004060445, 0.9919601381861455, 0.9978521396856772], "regular": 0.9974110562590696}
- PASS plate_t0.01_right_alternating_moment_rate: {"rate": [0.9691600782894981, 0.9971792071942366, 1.0118534567392417], "regular": 0.9974110562590696}
- PASS plate_t0.01_obtuse_moment_rate: {"rate": [0.983875644053343, 1.0102942045982033, 1.0229894328567275], "regular": 0.9974110562590696}
- PASS plate_t0.001_right_moment_rate: {"rate": [0.9728805171497945, 0.9920256067561553, 0.9979601821102253], "regular": 0.997433094957714}
- PASS plate_t0.001_right_alternating_moment_rate: {"rate": [0.9671611080576411, 0.9906537943121018, 0.9979353063594915], "regular": 0.997433094957714}
- PASS plate_t0.001_obtuse_moment_rate: {"rate": [0.9772564652151172, 0.9923662002576136, 0.9990451722121869], "regular": 0.997433094957714}
- PASS mixed_isolated_centre_deflection: {"mixed": 0.0003189142296852072, "layout_30": 0.0005383696764028252, "all_q4": 0.00017542390210183092}
- PASS mixed_isolated_centre_deflection_vs_30: {"mixed": 0.0003189142296852072, "layout_30": 0.0005383696764028252, "all_q4": 0.00017542390210183092}
- PASS mixed_isolated_s3_moment_l2: 0.009417775621075777
- PASS mixed_chain_centre_deflection: {"mixed": 0.0008214773849992957, "layout_30": 0.0010525244529584422, "all_q4": 0.00017542390210183092}
- PASS mixed_chain_centre_deflection_vs_30: {"mixed": 0.0008214773849992957, "layout_30": 0.0010525244529584422, "all_q4": 0.00017542390210183092}
- PASS mixed_chain_s3_moment_l2: 0.026658192730655464
- PASS mixed_boundary_centre_deflection: {"mixed": 0.0008412690343737966, "layout_30": 0.0010842765026604364, "all_q4": 0.00017542390210183092}
- PASS mixed_boundary_centre_deflection_vs_30: {"mixed": 0.0008412690343737966, "layout_30": 0.0010842765026604364, "all_q4": 0.00017542390210183092}
- PASS mixed_boundary_s3_moment_l2: 0.03249000961025545
- PASS mixed_cluster_centre_deflection: {"mixed": 0.0011553087515053363, "layout_30": 0.00041269471329230333, "all_q4": 0.00017542390210183092}
- PASS mixed_cluster_centre_deflection_vs_30: {"mixed": 0.0011553087515053363, "layout_30": 0.00041269471329230333, "all_q4": 0.00017542390210183092}
- PASS mixed_cluster_s3_moment_l2: 0.00449146241736915
- PASS mixed_quarter_centre_deflection: {"mixed": 0.0008992356448725075, "layout_30": 0.0008549675651364173, "all_q4": 0.00017542390210183092}
- PASS mixed_quarter_centre_deflection_vs_30: {"mixed": 0.0008992356448725075, "layout_30": 0.0008549675651364173, "all_q4": 0.00017542390210183092}
- PASS mixed_quarter_s3_moment_l2: 0.027196955202772655
- PASS modal_regular_first_frequency: {"errors": [6.488575755482776e-05, 0.0003097863483440837, 0.00034753607301873647]}
- PASS buckling_regular: 0.0009332626311924295
- PASS modal_right_first_frequency: {"errors": [0.0002417587457155537, 8.700583805932473e-05, 0.0009512111104657401]}
- PASS buckling_right: 0.0012875146158415098
- PASS modal_obtuse_first_frequency: {"errors": [8.486551470504372e-05, 0.00014985960724901782, 0.0007998598061471416]}
- PASS buckling_obtuse: 0.0007463674174614099
- PASS modal_mixed_chain_first_frequency: {"errors": [0.0008971399103710202, 0.003443326413190809, 0.0035263639370469503], "layout_30": [0.0008833442679537302, 0.0033795365667019313, 0.0034928529583526185]}
- PASS modal_mixed_quarter_first_frequency: {"errors": [0.0008429873473593001, 0.003038222259400878, 0.0034294651372847877], "layout_30": [0.0007912477720327956, 0.002828284624199541, 0.0033066128325258556]}
- PASS nonlinear_regular_45_end_moment: {"status": "completed", "tip_error": 5.135172705150483e-05}
- PASS nonlinear_regular_45_iterations: {"iterations": [7, 7, 7, 7, 7, 7, 7, 7], "regular": [7, 7, 7, 7, 7, 7, 7, 7]}
- PASS nonlinear_right_20_end_moment: {"status": "completed", "tip_error": 5.135172708896939e-05}
- PASS nonlinear_right_20_iterations: {"iterations": [6, 7, 7, 7, 7, 7, 6, 6], "regular": [7, 7, 7, 7, 7, 7, 7, 7]}
- PASS nonlinear_obtuse_30_end_moment: {"status": "completed", "tip_error": 0.00025579374224551563}
- PASS nonlinear_obtuse_30_iterations: {"iterations": [5, 5, 5, 5, 5, 5, 5, 5], "regular": [7, 7, 7, 7, 7, 7, 7, 7]}
- PASS nonlinear_obtuse_20_end_moment: {"status": "completed", "tip_error": 0.0014053274169113683}
- PASS nonlinear_obtuse_20_iterations: {"iterations": [5, 5, 5, 5, 5, 5, 5, 5], "regular": [7, 7, 7, 7, 7, 7, 7, 7]}

**All required criteria passed: False**

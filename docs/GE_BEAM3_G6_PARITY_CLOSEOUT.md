# GE Beam3 G6 parity closeout register

This register closes the frozen P01--P32/U01--U10 inventory without changing
its historical text. `GE` means accepted GE evidence; `N/O` means an actual
legacy-B3 non-obligation. All paths are repository-relative immutable inputs
to the G6 result.

| Row | Disposition | Controlling evidence |
|---|---|---|
| P01 | GE | G5 selector/provenance confirmation |
| P02 | GE | public workflow and mixed-P3 geometry evidence |
| P03 | GE | mixed-P3 reference algebra and engineering response |
| P04 | GE | G1 exact-elastic admission and G4 section transaction |
| P05 | GE | G4 generalized/fibre material-state confirmation |
| P06 | GE | G5 physical inertia and load/inertia route |
| P07 | GE | G5 shared assembly; G6 sparse multiple-RHS/session route |
| P08 | GE | G2 prescribed translation/support confirmation |
| P09 | GE | G2 affine MPC and G3 native graph confirmation |
| P10 | GE | G3 graph and G4 heterogeneous section confirmation |
| P11 | GE | G5 nodal/gravity/combination route and B3 baseline |
| P12 | GE | G5 admitted spatial/material dead line loads and couples |
| P13 | GE | accepted finite static variational core and G4 solver route |
| P14 | GE | accepted multiplicative finite-rotation static evidence |
| P15 | GE | G4 physical-fibre loading/unloading/reversal evidence |
| P16 | GE | G6 station-owned generalized initial-field work |
| P17 | GE | G4 Newton/line-search/cutback/force/displacement/arc controls |
| P18 | GE | G3c/G4/G5 authenticated restart, rollback and recovery |
| P19 | GE | G4/G5 physical and resultant-only recovery distinctions |
| P20 | GE | G5 physical generalized mass and common assembly |
| P21 | GE | G5 point/edge mass route and B3 reference baseline |
| P22 | GE | G5 reference/current-rest admitted modal evidence |
| P23 | GE | G5 conservative prestress/buckling evidence |
| P24 | GE | G5 Rayleigh/reference-linear Newmark and B3 baseline |
| P25 | N/O | no legacy objective finite-velocity rotation/gyroscopic route |
| P26 | GE | G6 B3/GE beam-segment contact and fracture classification |
| P27 | GE | G6 activity epoch, softening, deletion and restart evidence |
| P28 | GE | G3 coupled owner plus G6 explicit objective pose-joint boundary |
| P29 | GE | G6 64/256/1024 sparse assembly and bounded session evidence |
| P30 | GE | no changed B2/B3 hot path; scalar GE route is admitted |
| P31 | GE | explicit persisted ANYfem and ANYstructure opt-in adapters |
| P32 | GE | actual signed native arc path; stable postbuckling not claimed |
| U01 | N/O | legacy B3 rejects curved midside geometry |
| U02 | N/O | legacy B3 rejects generalized-section corotational combination |
| U03 | N/O | legacy rejects generalized-section plus fibre-plastic option |
| U04 | N/O | legacy corotational static fracture combination is rejected |
| U05 | N/O | arbitrary resultants cannot invent physical fibre stresses |
| U06 | N/O | capacity damage explicitly skips beam targets |
| U07 | N/O | inherited zero-force placeholder is not physical capability |
| U08 | N/O | no dedicated legacy B3 release or thermal-beam API exists |
| U09 | N/O | `Element.to_dict` is not a material-history checkpoint |
| U10 | N/O | inadmissible free prestress pencil is rejected |

The accepted evidence anchors are
`ge_beam3_g1_confirmation_result_v1.json`,
`ge_beam3_g2_confirmation_aggregate_v1.json`,
`ge_beam3_g3a_confirmation_v1.json`,
`ge_beam3_g3b_confirmation_v1.json`, the accepted G3c records,
`ge_beam3_g4_completion_confirmation_v1.json`, and
`ge_beam3_g5_completion_confirmation_v1.json`, each with its independent
review. G6 adds only the eight routes in
`tests/test_ge_beam3_g6_completion.py` and the strict integration regressions
in `tests/test_ge_beam3_g6_domain.py`.

The resulting scope remains explicit straight GE-B3 opt-in. It does not claim
finite-rotation transient dynamics, gyroscopic terms, capacity-based beam
damage, stable postbuckling, default routing, or production activation.

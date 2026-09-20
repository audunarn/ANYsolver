# Non-follower shared-validation screen summary

The preregistered three-pair installed-wheel screen is complete. The candidate
was product commit `019838840d0f6c4d0d7c718df45ee3f68a609623`, built as wheel
SHA-256 `562585e4107847e9cfb4757c7e1c84ca3cad9b01d9a0710cc05d16c29d3f84e1`.
It was compared with the retained follower-validation candidate
`b67517d16a589ebb397d1ef55441467ee0e62275`.

All installed regressions passed (9/9), every timed solve completed, physical
observables matched, and solver work was identical. Performance did not pass:

| Case | Median reduction |
| --- | ---: |
| Easy elastic shell | -12.45% |
| Large-deflection shell | -2.51% |
| Plastic S3 reversal | +2.27% |
| Prescribed-motion/MPC beam | -4.33% |

The four-case aggregate reduction was +0.11%. No case reached the registered
5% improvement threshold, the aggregate stayed below 5%, and the easy shell
exceeded the 5% regression cap. Raw evidence SHA-256 is
`c9082649ba84d2bca5db0122c8b613fa9c773793beb6c976dd9162950438eca0`.

The shared validation-scope component is rejected and was removed by revert
commit `39ef01e2`. It does not advance to the existing seven-pair formal gate.
The earlier follower-validation implementation and its preserved evidence are
unchanged; its formal promotion result remains NO-GO.

Independent review found that the first offline adjudicator trusted stored
summaries and did not authenticate every runner/tree/wheel provenance field.
The raw campaign was unaffected. The strict version 2 adjudicator now verifies
all identities, exactly three alternating pairs per case, 24 successful
samples, 12 bound physical comparisons, installed regressions, and exact work
equality before recomputing every median from raw pair samples. It reproduces
the same screen **FAIL** and rejection decision.

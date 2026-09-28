# Eight-Q4 distributed press with provisional macro pressure

**Status:** exploratory development comparison, 28 September 2026. This is not a
qualification run or a new C1 capability. The opt-in `macro_q1_pair_dev` basis
remains provisional.

## Decision question and inputs

On the finite-area, nonmatching Q4/S3 distributed-load case, test whether the
paired macro Q1 pressure basis improves the equilibrated pressure-response
conditioning without moving integrated force by more than the existing 2%
representative-response target or failing local pressure and gap gates. The
three-step macro run reused the eight-Q4 geometry, 0.3 N total source load,
target right edge at x = 1.3 m, 10,000 Pa/m normal regularization, 1e-5 Pa
pressure-change tolerance, 50 µm gap tolerance, seven augmentation updates,
and 250/200 Pa Schur pressure/step caps. The earlier fine-basis four-phase run
has the same first three physical targets and settings; only its first three
steps are compared here.

Macro source: `100fe44b` plus the report-script CLI change committed with this
note. Its raw result is
`reports/general_contact_d1_distributed_8q4_macro_press_dev_20260928.json`
(SHA256 `5a984cd97c2bf36cdff67eb1b512eb483aaba03fafa0eb5f7a4fa9883c5c1444`).
Fine source/result: the earlier
`reports/general_contact_d1_mixed_8q4_interior_distributed_0p3n_four_phase_20260927.json`;
this comparison does not revise that run or its independent review.

## Observations

| Full-press quantity | Fine nodal Q1 | Macro Q1 |
|---|---:|---:|
| Integrated upward contact force | 0.1034798152 N | 0.1046049594 N |
| Difference relative to fine result | — | 1.0873% |
| Supported pressure modes and scaled Gram rank | 18/18 | 10/10 |
| Scaled Schur condition, first and second full-press corrections | 1222.09; 727.33 | 224.38; 111.78 |
| Full-press augmentation count | 4 | 4 |
| Final multiplier change | 3.47e-14 Pa | 1.62e-13 Pa |
| Minimum independently sampled gap | -0.0804 µm | -0.3153 µm |
| Final equilibrium residual | 1.46e-9 N | 7.67e-9 N |

Both runs completed three press steps, had full supported pressure rank, and
met their local pressure and 50 µm gap limits. The macro basis reduced the
reported full-press scaled Schur condition by factors of about 5.45 and 6.51
at the two corresponding corrections. It did not reduce the augmentation
count on this small problem. The elapsed times are not comparable: the fine
report ran twelve steps, and the macro report ran three.

## Decision

Keep the macro basis as an opt-in development candidate. The local comparison
passes its bounded force and enforcement discriminator and gives a concrete
conditioning benefit. It does not show pressure-field convergence, stable
partial-contact behavior under refinement, a full press/slide/open/recontact
path, or an installed route. The 1.0873% response difference is already a
material fraction of the 2% target; no default or accepted capability changes.

The next pressure-space decision should use an independently defined
finite-area refinement and pressure-field measure, with target-mesh and
enforcement effects separated. Do not infer this from the one-active-mode
free-target case or automatically run larger macro meshes.

# F03 exact saved-pose representation diagnostic v1

22 September 2026. Source `d0b6d0902360210f78e06b45f7bbabb030ea4022`.
All three registered cases completed and passed the exact representation
diagnostic, exit0. This establishes the numerical attribution described
below. The original reference's FAILED_EVIDENCE, the saved audit's
FAILED_NUMERICAL_SCREEN, and physical reference HOLD remain unchanged.
G0B remains open; G1 remains barred.

## Numerical finding

The discrepancy is dominated by the saved coefficient reconstruction
relative to the independent represented-geometry integral. Direct station
evaluation and floating polynomial differentiation/evaluation contribute
much smaller errors. This identifies the coefficient-reconstruction
pipeline; it does not separately identify every operation within that
pipeline or waive the original numerical acceptance limit.

At the transverse second derivative at s=1, signed polynomial-minus-direct
contributions are in inverse metres:

| State | Total discrepancy | Floating evaluation | Coefficient reconstruction | Direct action |
|---|---:|---:|---:|---:|
| n12 | -1.94290385e-15 | 9.82657480e-20 | -1.94305105e-15 | 4.89399259e-20 |
| n16 | -8.00401412e-15 | -3.99164276e-20 | -8.00399934e-15 | 2.51389248e-20 |
| n24 | -7.50258620e-14 | 3.72429799e-19 | -7.50255728e-14 | -6.61632574e-19 |

The table rounds for display. The raw records retain exact rational
numerators and denominators. The three signed contributions close exactly
at every one of the81 order/station/channel combinations per case.
Power and Legendre representations agree exactly. Endpoint weighted
coefficient sums agree with direct exact differentiation, and all triangle
bounds hold. The tip coefficient-error bounds are1.94305105e-15,
9.53506847e-15 and7.71298478e-14 for n12/n16/n24 respectively. Signed
contributions are not substituted for these bounds.

Across all registered derivatives, stations and channels, the largest
direct-action discrepancy on the original normalization is4.90150e-16,
5.48393e-16 and1.01709e-15 for n12/n16/n24. The corresponding coefficient
contributions reach4.78454e-12,1.49056e-11 and1.15332e-10.

## Original decisions remain separate

| State | Original full saved-action metric | Replayed derivative submetric | Original1e-11 criterion |
|---|---:|---:|---|
| n12 | 4.784178386116733e-12 | 4.784178386116733e-12 | Pass |
| n16 | 1.490569246047816e-11 | 1.490569246047816e-11 | Fail |
| n24 | 1.153325509593225e-10 | 1.153325509593225e-10 | Fail |

The full metric was copied exactly from the immutable saved audit; only
the floating derivative submetric was replayed. Their equality in these
cases is observed, not assumed. The original scaling, subtraction and
max-before-division arithmetic are preserved. Separately scaled rational
terms can differ slightly from the original floating normalized result;
they do not replace it.

The oracle uses the original binary64 geometry and held rounded J, not a
new nominal-decimal model. It preserves the exact yaw factor, with
gamma-1 approximately2.1366999345975873e-17. No coefficient, displacement,
multiplier, reaction or constitutive state in either parent was changed.

The previously observed energy and full-functional trends remain
unsettled. This successful representation diagnostic does not establish
physical convergence, native shell/beam qualification or a speedup.

## Execution and verification

Command:

    python scripts/b3_e4_f03_primal_exact_pose.py --run-all --root .qualification/b3-ge-e4-pl/f03-primal-exact-pose-v1

Three serial children completed with exit0, using five environment thread
caps equal to"1" and integer-one numerical threadpool observations.
Their elapsed times were1.3112s,1.5118s and2.3159s. Total orchestration
was10.3904s and maximum sampled child RSS was93,286,400bytes, within
the registered300s/1GiB child caps. No equilibrium, element evaluation,
integration assembly, projection reconstruction, fresh reaction recovery
or Green-norm evaluation was performed.

All29 integrated synthetic/mock checks passed. After the final exact-copy
binding correction, all five affected runner mocks passed, including a
coherently rehashed inherited-value mutation below the old tolerance.
These inventories overlap. An earlier synthetic scalar-conversion failure
is preserved; it did not execute a scientific case.

Independent pre-execution code and mechanics review resolved geometry,
serialization, arithmetic and evidence-copy findings before the clean
source freeze. Independent postreview **accepted representation-diagnostic
integrity and attribution**, with physical reference HOLD. It verified
three raw chains,13 frozen source bindings, both parent inventories and
exact reproduction under the no-recomputation guards. Every preexisting
diagnostic byte and both parent roots remained unchanged. Review tool
chunk `32a9ac` exited0. At n24 the record contains1,916 rational pairs,
with a maximum integer length of851 characters, inside the frozen bounds.

## Evidence bindings

Root: `.qualification/b3-ge-e4-pl/f03-primal-exact-pose-v1`.
The immutable completed inventory binds25 files, including the three
preserved test logs, independent reviews and execution provenance. Its
own hash is recorded separately. Do not add files to this completed root.

| Record | SHA-256 |
|---|---|
| Registration | `0371cb7e2e3d6cf68f54e215fb455ba2bce8ec7e59b57c2144ebe0ec023d85d7` |
| Adjudication | `557ec2d058db562e0d1991c1929b475e9d86d5f9a7ba4109fdbcbabedbdb7b18` |
| Orchestration | `15007dc264f5df26b2f8052c3fd4b9f9469be8ee016228f6ce65703f22286d22` |
| Pre-execution review | `fa5254f48dc47aaf1c1ff969a08ea487ec53f7699807c33e3b89f1f0f9bf38a7` |
| Independent postreview | `1f99c5d4c7b0086e600fe6069e349672929e6b3ab9eda6797794e48aa932b735` |
| Execution provenance | `1f92fe8843dcb89c09e059a1042de96e8a45aad0e7096cd26ae561603954d6d9` |
| Completed inventory | `e7f0b5c8a8a403d7785ddba793e8061628b8b1b163ba4251338b63c3f0e5de0a` |

The execution launched in tool chunk `d3b06e`, session23468, and completed
in chunk `869fce`, exit0. Do not rerun or overwrite this consumed execution.

## Next question

Prepare and independently review a separate saved-state spatial residual
study using the exact pose representation. Its purpose is to locate shell
balance defects and understand the unresolved spatial approximation.
Residual magnitudes are descriptive, not physical error percentages.
The next study needs its own fixed quadrature, checks, input identities,
resource limits and registration. Do not automatically increase the Ritz
degree, relax tolerances, select a production interface space or claim
FE-as-reference acceptance.

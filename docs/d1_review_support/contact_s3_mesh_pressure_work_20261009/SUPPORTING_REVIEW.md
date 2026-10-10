# Supporting read review — variable-pressure S3 work

Same-family read-only review; no numerical jobs, product edits or engineering acceptance.

## Independent ramp derivation and assumptions

Let `c(t)=c0+(c1-c0)t` be a strictly positive Coulomb cap, `s(t)=S t`, and `e(0)=c0/k`. If every stage is sliding in the same direction, the total plastic slip is `Γ=S-(c1-c0)/k>0`. The continuous control then has `D_exact=A(c0+c1)Γ/2`, `ΔE=A(c1²-c0²)/(2k)`, and `W_exact=A(c0+c1)S/2=ΔE+D_exact`. For `r` equal accepted endpoint-pressure stages, each returned plastic increment is `Γ/r`, giving `D_r=D_exact+A(c1-c0)Γ/(2r)`. Thus rising/falling caps reverse the bias sign, with `1/r` scaling. These formulas require prescribed linear cap/motion, fixed normal, stable material feature, no opening or stick transition, and the stated initial elastic extension. The sufficient frozen condition `S>|c1-c0|/k` enforces positive slip in both ramp directions. The scalar exact work is a control only; arbitrary coupled pressure samples provide no continuous-pressure bound.

## Early consequential data requirements

Saved accepted history summaries contain per-point pressure, traction and facet IDs (`s3_sliding_friction.py:586-588`), while the terminal checkpoint has only terminal material-anchor barycentric coordinates. They do not directly contain each intermediate returned barycentric anchor. Independent attribution of coupled material slip must reconstruct each accepted old/new feature from authenticated per-step state, or from stored binary poses plus an independent geometric inverse and observed traction, with an explicit uniqueness/refusal check. Dividing production `D` by pressure, or calling the production return owner to obtain its own plastic increment, would make the comparison circular. Facet transfer must preserve actual material-coordinate correspondence rather than merely matching spatial points.

Even if the matched scalar ramp passes, the observed `5.5799%` ratio-2/4 discrete loss difference cannot be assigned to endpoint pressure alone until saved coupled pressure, material transport, branch and facet paths are separated. Compare common stages and report residual attribution and uncertainty; do not infer exact continuum work or a 2% engineering gate from two discrete histories.

## Author checkpoint equation review

`EARLY_CHECKPOINT.md` proposes reconstructing each returned target anchor from stored source point `x`, observed traction `t`, independent target unit normal `n`, and target-plane origin `o` as `y=P x+t/k+(n·o)n`, `P=I−nnᵀ`. This exactly follows the current production definitions `e=P(x−y)`, `t=−k e` (`s3_sliding_friction.py:393-409,503-505`) for a valid coplanar target. The old barycentric feature must then be advected with the **current** target skins; `dp=P(y_new−y_old_advected)` matches the law's material chord (`:499-501`). Check tangentiality `n·t≈0`, plane residual, inverse barycentric reconstruction and recorded facet membership/uniqueness, including seam ties; reject ambiguous or out-of-domain features. Source physical points should be rebuilt from independent nodal skin/shape weights rather than accepting the product point map as the sole oracle.

Because `y` is inferred from observed production traction, this coupled reconstruction can validate reporting/history consistency and separate observed pressure weighting from observed material transport, but it cannot independently validate the traction law itself. The independent fixed-normal scalar ramp supplies that narrower local law control. The checkpoint correctly calls the coupled comparison diagnostic and rules out a continuous-pressure inference. No source/test artifact or saved numeric result existed at this read.

## Source-ready findings before execution

The new `material_work_diagnostics.py:83-99` implements the derived traction inversion, independent facet solve and old-bary advection. Open and stress-free activation are explicit. The three-term comparison at `:129-138` is algebraically exact: within-fine-interval pressure sampling, fine-versus-coarse endpoint pressure response on the fine chords, and coarse-endpoint-weighted fine-versus-coarse chord/history response. Its labels correctly avoid a continuum or causal solution claim.

**Input refusal gap:** `reconstruct_material_history` converts `published_loss_j` at `:112-114` but never requires finite and nonnegative values. Nonstandard JSON NaN/Inf or negative published loss can therefore enter a report with undefined/error claims. Require a finite, nonnegative declared saved loss; similarly reject nonfinite reconstructed loss if arithmetic overflows. This is diagnostic input validation, not a law change.

**Pair identity gap:** `compare_material_resolutions` at `:120-143` checks features, faces, areas and `mu`, but reconstructed results omit stiffness and authenticated source/program identity. The optional example file consumer (`examples/general_contact_s3_mesh_history_events.py:75-81`) therefore accepts two unrelated histories with matching mesh and `mu`, or different `k`, as a named coarse/fine pressure/history comparison. The test preparer does authenticate prior output hashes (`tests/test_general_contact_s3_mesh_pressure_work.py:55-84`) before writing its specific bundle, but that provenance is not carried into or enforced by the general file consumer. Bind a declared common input/program identity and stiffness across the pair, or clearly narrow the file consumer to untrusted algebraic samples without an authenticated provenance claim. These findings were sent to the lead before author execution.

**Source-feature/CLI gap:** The first source accepted supplied `source_points_m` without validating against declared source nodes and barycentric weights, and diagnostic mode silently ignored explicit solver-only `--ratio`/`--workflow` options. The frozen test preparer independently builds its own source skins; a reusable file consumer must either receive and verify the corresponding nodal skins or explicitly label source-point correspondence as a trusted declaration. Explicit irrelevant CLI controls should refuse.

## Repaired SOURCE2 delta

`REVIEW_DELTA.md` records admission-only repairs. The current diagnostic checks finite nonnegative published losses, finite checkpoint barycentric data, identical stiffness, target node IDs and a shared declared model/program/settings context (`material_work_diagnostics.py:114-131`). The test preparer builds that context from literal fixture nodes/topology, shell contract, supports/MPC, contact definition and settings, the unchanged user program, and solver settings, removing only the physical-subincrement ratio (`test_general_contact_s3_mesh_pressure_work.py:66-89`). The diagnostic docstring now explicitly identifies source-point/material correspondence and provenance as trusted declared inputs requiring external authentication; the preparer independently constructs source points from literal nodal skins and authenticates prior closure output hashes. The example parser uses `None` to distinguish explicit solver-only options, refuses them in diagnostic mode, and applies the historical ordinary defaults (`examples/general_contact_s3_mesh_history_events.py:73-84`). These changes resolve the source-level findings within the stated trusted-input boundary. Numerical SOURCE2/installed outcomes were not yet available at this read.

## Saved SOURCE2 diagnostic evidence

`ramp.json` passed the independent `Fraction` integral and exact endpoint rule for positive and falling linear pressure ramps: rising 1→3 Pa produced measured `D₂=7.05e−5 J`, `D₄=6.345e−5 J` versus exact `5.64e−5 J`, with positive biases `1.41e−5` and `7.05e−6 J`; falling 3→1 Pa produced `D₂=4.77e−5 J`, `D₄=5.565e−5 J` versus exact `6.36e−5 J`, with negative biases `−1.59e−5` and `−7.95e−6 J`. Thus sign and `1/r` scaling match the controlled fixed-normal full-slip reference at the retained absolute algebra gate. This is prescribed local pressure, not coupled equilibrium.

`diagnosis.json` passed reconstruction of all 12/24 authenticated saved physical samples. Coarse/fine losses are `8.557554375e−4` and `9.063276286e−4 J`; maximum available-cut anchor discrepancy is `2.22e−16 m`. The exact sampled-data split of fine-minus-coarse `5.05721911399e−5 J` is within-interval pressure sampling `+5.05721993337e−5 J`, endpoint pressure response difference `−1.04e−18 J`, and chord/history response `−8.19e−12 J`, with split closure `1.74e−19 J`. In user interval 2→3, all coarse/fine point branches are slip and the two pressure-sampling contributions total about `5.05020933e−5 J`, the bulk of the difference. A further ~`7.01e−8 J` arises in the opening transition, where the fine path slips before the coarse endpoint is open; that portion is sampled event timing, not a smooth pressure-quadrature bias. This supports endpoint pressure sampling as the dominant explanation for this saved discrete dataset and supplies no general path-integral or convergence claim. It reconstructs anchors from observed production traction, so it is a history-consistency attribution, not an independent traction-law or nonlinear-solution proof.

The intended example file caller and 11 malformed-input refusals passed in saved SOURCE2 `consumer.json`/`refusal.json`, including no solver/model allocation, unchanged input bytes, deterministic result, and unused solver-option refusal. Final installed artifact/import and metadata closure were still pending at this read.

## Final installed delta and disposition

The one final wheel in `current-install.json` has SHA-256 `6d06de96dd1c5504ca286e87884800e5595065c419b63fa831e4bbccdcc6c7bc` and 646 payloads. Its new diagnostic payload hash `ef8fa7c758adf9f3b5de8ff41e4856b57da2701f3c3c62b50f3c0880689caccd` exactly matches the current reviewed source file; prior friction-history and static-path product hashes remain unchanged. Installed `final-ramp`, `final-diagnosis`, `final-consumer`, `final-refusal`, scoped `final-legacy`, and public `final-cli` stages all passed in the bounded ledger. Installed diagnostic numbers exactly match SOURCE2; the CLI output carries the same `5.05721911399e−5 J` split and explicit `not_continuum_integral_or_causal_solution_decomposition` scope. The ledger records `95.6975746001/600 s` used at this read, with no authorization inference from unused balance.

**Supporting conclusion:** No remaining concrete defect was found in the repaired source or its saved source/installed checks. For the authenticated prior 12/24-step fixture, observed endpoint pressure sampling explains essentially the whole discrete loss difference; independently recovered material chords and target feature transfers agree with published returns to the stated budgets. The matched rising/falling scalar ramps support the local endpoint-pressure law and sign/`1/r` bias. The small opening-phase contribution is event timing within the sampling term. The file consumer trusts its declared source points/context unless separately authenticated, and the coupled reconstruction uses observed traction. Therefore this is a reusable development diagnostic and dataset attribution, not an independent nonlinear solution, exact variable-pressure path integral, continuum convergence, C0–C9 engineering acceptance, or release assessment. Same-family review only.


## Lead disposition

Source, actual result fields, installed payload parity and metadata bindings were
inspected. The 5.5799% sampled-history difference is predominantly pressure
sampling, with a separately identified small opening-event contribution. Retain
the endpoint-pressure convention and its resolution-sensitive label; no law or
history repair and no further coupled refinement is warranted by these data.
The anchor reconstruction uses observed traction and is not an independent
nonlinear traction solution. The generic file caller trusts declared source
points/context; frozen evidence supplies external authentication.
Lead audit:3524 private imports,156 input copies,286 external bindings,0errors.
The first metadata audit failure and superseded SOURCE1 bytes are retained and
explicitly bound; no numerical replay. All645 existing package payloads remain
byte-identical. Build alone lacks runtime evidence. Same-family supporting
scrutiny and these development passes do not establish engineering acceptance
or release. Continuous work convergence and full C0-C9 remain open.

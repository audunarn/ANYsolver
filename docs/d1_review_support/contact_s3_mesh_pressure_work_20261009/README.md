# Saved S3 pressure/work attribution

## Result

The authenticated ratio2/4 dataset gives 50.57219114 microjoule more discrete plastic loss at ratio4 (5.5799017421%). Independent anchor inversion/transport assigns 50.57219933 microjoule to sampled pressure weighting, approximately -8.194 picjoule to anchor/chord differences and negligible matched-endpoint pressure difference. Of the total, 50.50208510 microjoule is main-slip difference (pressure term50.50209329 microjoule) and0.07010604 microjoule is opening event timing. This is a sampled-history explanation, not continuous-path work convergence, pressure/spatial acceptance or an independent nonlinear solution.

## Independent reference

For fixed normal, positive cap c(t)=mu*p(t)=c0+(c1-c0)t, e0=c0/k and imposed monotone displacement S, Gamma=S-(c1-c0)/k>0. Then D=A*(c0+c1)*Gamma/2, DeltaE=A*(c1^2-c0^2)/(2k), W=A*(c0+c1)*S/2. Equal endpoint samples have Dr-D=A*(c1-c0)*Gamma/(2r). Rising/falling ramps verify opposite signed first-order bias. Their exact discrete return algebra is checked at1e-12 J; no variable-pressure endpoint quantity is relabelled as an exact physical path integral.

## Saved-history reconstruction

On declared coplanar target, independently reconstructed n and origin o give y=x-n*(n dot(x-o))+traction/k. Independent2D facet inversion gives material barycentric coordinates. Advect the preceding committed barycentric coordinates on current skins, then compute Gamma_j=norm(P*(y_new-y_old_advected)). Released/activation chords are zero. Reference-area endpoint loss is sum(mu*A*p_end*Gamma_j). This uses reported traction, so it validates consistency rather than independently predicting traction.

For each coarse interval the exact sampled difference splits into (i) fine pressure relative to the fine matched endpoint, (ii) fine/coarse matched endpoint pressure difference, and (iii) changed total anchor chords under coarse endpoint pressure. Term(i) includes active-state sampling near opening; it is not automatically smooth quadrature or a causal nonlinear decomposition.

## Consumer and input contract

`examples/general_contact_s3_mesh_history_events.py --diagnose-material-work <bundle.json> --output <report.json>` consumes paired declared data without model allocation or solve. It refuses explicitly supplied --ratio, --workflow, --restart and --through-step. Normal solving keeps omitted defaults2/pressure_event. Inputs bind k, mu, material features, positive reference supports, exact target IDs/topology and shared declared model/program/load/settings context excluding resolution. Finite nonnegative reported loss and finite valid checkpoint barycentric arrays are required. Generic source point/material feature correspondence is trusted declared input. CLI JSON does not self-authenticate; this frozen preparer binds original outputs/CLOSURE hashes and reconstructs source skins literally.

## Verification and limits

Source checks and installed immutable646-payload wheel checks cover scalar ramp,36 saved material histories,13 checkpoint cuts, refusal/no input mutation and actual file caller. Two legacy friction cases and diagnostic CLI pass. All645 prior package payloads are identical; no solver law, force/tangent, state/restart or fixture change. Whole-path energy convergence, geometric rim/partial coverage, pointwise Coulomb qualification and engineering acceptance remain open. Preserve endpoint-pressure convention rather than tuning ratios or treating ratio4 as converged.

Raw evidence: C:/ANYworkspaceWork/contact_s3_mesh_pressure_work_20261009/OUTCOME.md, IMPACT.json, CLOSURE.json, ledger.json and unique attempt directories. The ledger accounts guarded child execution only; source staging, unpacking and audits are metadata preparation. No whole installation speed claim.

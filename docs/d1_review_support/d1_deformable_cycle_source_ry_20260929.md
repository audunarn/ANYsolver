# Deformable-target cycle source-director moment screen

**Question.** Could the existing accepted-pose four-Q4/two-S3 press/slide/open/recontact cycle supply a resolved source `ry` contact reaction while its S3 target deforms? The previously retained cycle reports did not save full poses. The existing [cycle tangent runner](../../scripts/general_contact_d1_cycle_tangent_discriminator.py) was extended only to record full-coordinate source `ry` contact residuals at its accepted slide (step 4) and recontact (step 7) poses. No contact law, solver setting, support, load or tolerance changed.

One bounded replay completed all eight increments in 45.73 s with 408.71 MB peak process-tree RSS, under the existing 180 s/1 GB development cap. Every prior tangent record and the prior full-coordinate source-direction comparison reproduced exactly. The [raw new result](d1_deformable_cycle_source_ry_20260929.json) and [resource record](d1_deformable_cycle_source_ry_resource_20260929.json) are retained.

| Accepted pose | Active pressure modes | Maximum nodal source `ry` contact residual | Summed source `ry` residual | Integrated source normal force |
|---|---:|---:|---:|---:|
| Step 4 slide | 2 | `7.6161e−11 N·m` | `1.92746e−10 N·m` | `1.51734e−4 N` |
| Step 7 recontact | 2 | `6.7609e−13 N·m` | `1.87345e−12 N·m` | `1.37407e−5 N` |

The summed residuals also agree with `0.025 m ×` the reported source `x` force at each pose, within saved precision. This is a consistency observation using the production force result, not an independent work oracle. The very small source moments cannot discriminate a coupled source-director reaction or tangent at useful scale. The [separate fixed-target tilted-pose oracle](d1_tilted_source_work_replay_20260929.md) remains the narrow reviewed source-work evidence. The deformable-target cycle still provides previously tested target work and accepted-step path observations, but the combined deformable-target/source-director response remains open.

**Decision.** Stop this cycle source-moment branch. A new nonparallel deformable-target fixture would need a specific load/geometry and independent-response design before any expensive coupled run. Resume the D1 critical path through the remaining pressure, clipping, response and state gates; do not increase this fixture's load, slope, step count or resource cap solely to make its source moment larger.

Replay source: `0497da02` plus the runner-only measurement. SHA-256 runner `C423B43FE04655EDEACE40AA06D8D11DEA75CFC026A767CC15E43F30D05158BA`; raw result `A7E213A0FFD40386F1D96BD5A422C4E8DF7D7BB67935A5234CA7AE7E1CB40F3C`.

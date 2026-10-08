# C4 connected S3 source patch - development evidence

Base941228676caefb71956a1e38d2646c00c18190c7; source held and locally integrated
after review. Implemented/source and private-installed tested; neither independent
engineering acceptance nor release. Earlier one-S3 evidence remains unchanged.

The new PATCH_PROFILE retains one global P1 pressure field. All source/target
face supports, gaps and derivatives are aggregated before the unchanged penalty
law; complete cross-face Hessian and physical skin pullback remain. Connected
oppositely directed shared edges, exact shared skin positions/work rows, and
reference/current projected-interior ownership are required. Overlap, unresolved
projection, discontinuous traces and over-budget work refuse explicitly.

The128MiB local derivative-work estimate is checked before dense allocation and
bound only to the patch identity. The old profile and checkpoint dictionary are
unchanged by static AST impact comparison. Existing process/resource limits apply.

## Actual results

- Final installed4PASS5.310244999942s; peak181460992B. All234 solver imports resolve
  from installed7; errors[], JITdisabled, Numba1, all3effective pools1. The generic
  harness scope label says source development; recorded import roots prove the
  actual installed execution.
- Independent assembled P1 M/S active-set reference plus separately assembled
  no-contact structuralK: response error1.952427544241e-11 on fixed10um scale,
  versus1e-6. No production contact kernel supplies the reference. The nonlinear
  correction estimate2.649603407436e-12m is not a rigorous uniform error bound.
- Conservative force-case gap-2.159010817951um versus50um development setting;
  energy7.513489483460e-8J. Actual support/load/contact force and moment errors
  6.099935371632e-12/4.425996825758e-12 versus1e-6, separate .15N/.15Nm scales.
- Independent constant-gap full normal-H includes the geometric source-normal
  term. Cross-face pressure coupling, scalar virtual work, directional tangent
  and actual shared-node rotational skin pullback pass1e-5.
- Actual active/open/recontact gaps-30/+10/-30um; complete canonical checkpoint
  equality after prefix/resume. Ownership, near-mismatched trace and128MiB
  admission controls pass. Installed test executes the ordinary force example.

Wheel04f4d6bdde80f12441f20b2e83b3fb563b543b37da5530dc1f4f069cb1e88c75:
all536 source/wheel/installed payloads match. Root inspected five exact held source
hashes, actual results, imports/runtime settings, scoped diff and terminal costs.
Separate same-family Read scrutiny closed overlap ownership and oracle wording;
root also checked exact shared traces. Supporting scrutiny is not formal acceptance.

## Cost, limits and evidence

Six additional terminal jobs36.614422700019s, including two builds; build6 was
superseded after a real shared-trace guard repair and is retained. Original C4
total30jobs158.646824599826/180s,21.353175400174s remain. Earlier eight NONPASS
jobs/artifacts remain. No other allocation or frozen authority renewed; no complete
route speedup or spatial-convergence claim. No old numerical campaign replay.

Q4, nonplanar/moving/free tools, finite rotations, nonlinear materials, physical
boundary-only mechanics, self-contact/friction/native combinations, pressure-space
and mesh qualification, broader rollback and installed applications remain open.

Raw C:/ANYworkspaceWork/contact_triangulated_rigid_20261006:
patch_worker_handoff.md, summary.json, patch_frozen_source_hashes.json,
patch_one_element_contract_impact.json, patch_installed_payload_parity.json,
patch_installed_final/{actual_result,resource,runtime,imports}.json and run.log.
[Guide](../../GENERAL_CONTACT_TRIANGULATED_RIGID_DEV.md),
[prior one-S3 evidence](development.md).

# separation_full_v1_vk_s3r1_checkpoint.json - provenance

* What: restart checkpoint of the full partial-overlap separation workflow (press, slide, back-off, lift, re-press), regenerated under the
  S3 R1 von Karman default (law S3_V2D_VK_R1, merged at main a0781c0bc/2f3ef539a) by
  `tests/test_general_contact_s3_friction_replay.py::test_partial_overlap_coupled_full_workflow` (its `full_checkpoint.json`), 2026-10-24,
  Claude Sonnet 5.5 session on branch claude/s3-replay-vk-retarget, commit that adds this file (see git log). Owner approval: 2026-10-24
  (retarget of the three S3 friction-replay tests, relayed by the coordinator).
* Why: the pre-VK reference `separation_full_v1_checkpoint.json` (2026-10-02, pre-VK element law, 5 steps) is superseded for the three coupled
  tests: under the VK default the single 0.55 m slide step stops with `contact_gap_exceeded` (indefinite reduced tangent, lowest eigenvalue -48 vs
  -0.54; notes: C:\ANYworkspaceWork\full-suite-20261023\triage\replay_stop_notes.md). The old file is KEPT unchanged: other tests
  (`test_saved_workflow_*`, fixed-path discriminators) use its accepted frames as fixed physical paths, which do not depend on the element law.
* Schedule: waypoints (0,0),(0,-.02),(.275,-.02),(.55,-.02),(.54,-.02),(.54,0),(.54,-.02), one step per segment (6 steps; formerly 5). The
  analysis fingerprint therefore differs from the old file; the model fingerprint is identical.
* Checks of the regenerated numbers (old pre-VK file vs this file; final-state max |du| 9.1e-6 on a 0.54 scale):
  see the table in docs/S3_VON_KARMAN_ELEMENT_DEFINITION.md section 8 and the commit message. Path independence of the VK slide: final states for
  2/4/8 increments agree to 1.3e-11.

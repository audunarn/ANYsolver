# Experimental objective-Q4 BL5 staged loading

Decision: retain BL5 experimentally; physical clamp-transfer acceptance still
needs a controlled matched coupled reference. Existing common-action, completion
and U1 findings justify no new native mesh sweep or law correction. Independent
review identified that precise reference-error obstruction; it does not block
unrelated product integration. Formal F03 remains unconsumed.

## Delivered behavior

The existing StagedDeadLoadProgramme now admits elastic, pure-Q4 BL5 models with
explicit Q4_ALGORITHMIC_PULLBACK_V1. No new API, equation, load semantics or
checkpoint schema. The existing model identity binds the selected Q4 policy;
legacy point and historical line identities remain unchanged. Mixed/S3 material
lines, L1 and physical-fibre lines remain outside this addition. Historical BL5
staged admission remains rejected. Distributed forces/couples on lines need their
own numerical-policy compatibility work and remain rejected.

Why require the explicit Q4 policy: the initial historical model converged, but
50N staged force produced moment imbalance2.9964e-5Nm (P0) and9.8292e-6Nm
(coarse P1), exceeding the unchanged2e-6Nm check. No tolerance was loosened.
The already implemented objective pullback passes the same checks. This is a
newly admitted shell/line combination, not merely load plumbing. The old failure
is retained and is not repaired retroactively.

## Evidence and limits

Source final3checks pass in23.528s,179499008B sampled process-tree RSS. Both bases
exercise signed100/-100N stages, cancellation at position1, exact snapshot restart,
negative continuation, physical force/moment balance and agreement with the
existing fixed-force final elastic path. P0 additionally exercises pending adaptive
progress, physical-frame preservation through rebase and nested chart/controller
restart. Wrong-basis and historical-policy checkpoints fail without publication;
L1 and historical staged requests remain rejected.

Two multiplier-dependent actual-chart derivative checks passed in source-v2.
They subtract zero-multiplier responses and therefore check the connection chart
contribution, not the complete Q4 residual derivative. Existing objective-Q4
kernel evidence applies. Five focused compatibility checks pass in18.063s:
point reference-map/identity, invalid policies, historical line restart and
rejected-prefix preservation. Eight existing staged-point checks passed in the
initial source-v2 campaign, alongside the two preserved historical balance failures.

Installed candidate wheel SHA256:
`d506e3f339bac1acc4c8475f394062955431386a1025503ac2ae12667b14be90`.
All398source/wheel/site modules match. Three installed checks pass in23.596s
supervised/179957760B;219actual ANYsolver imports are from the isolated site.
Both exposed numerical pools use1thread, Numba1thread/JITdisabled. Windows,
Python3.14.2; package version unchanged. No broader platform or consumer claim.

Independent OpenAI Read review inspected source, admission, nested identity and
source-v4 evidence, finding no consequential remaining issue. This is not a
different-family review or formal BL5 acceptance. Algebraic tolerances, reference
accuracy, growing-space stability, G0/M2/G4 and release obligations remain open.
Zero-load targets are deliberately absent; no new zero-equilibrium claim.

## Retained runs

`evidence-v1.zip` and `evidence-v1.json` bind source/installed logs, runner, fixture
copies, artifact identities, imported locations and runtime settings. Archive SHA:
`76089e53d5c7ed66f0bd3d4f2c7704f9ba5de81998633f0aef248d6a6dbb27ae`.
Compatibility logs are in compat-source-v1. Initial source-v1 passed without the
new balance assertions. Source-v2 preserves the historical moment failures.
Objective-v2/v3 failed only test observation: absent pre-rebase explicit frame
witness and SciPy's writable-buffer requirement. The final helper reconstructs
the known identity-anchor frames on an owned copy. All failures remain retained.

Next usable slice: exercise objective BL5/reference-linear parity and broader
load/consumer integration by impact; keep physical connection acceptance separate.
Do not launch a corrected U1 reference campaign or a fourth uniform mesh.

## Public example and reference-linear parity

After2067a594, the reference residual/tangent parity check now also exercises the
explicit objective Q4 policy for P0/coarseP1. Four parity cases plus the public
example pass source in13.788s/179109888B. Existing residual/gap/tangent thresholds
are unchanged. This compares reference operators, not finite physical accuracy.

`examples/stiffened_shell_bl5_staged.py` constructs its3Q4/2B3 definition through
public types without importing test helpers. Signed100/-100N stages complete
at .5/1/1.25/1.75/2 after cancellation, rebase, restore and identical continuation.
Installed example passes in11.594s/172363776B on unchanged wheel d506e3f3...14be90;
all398source/site module hashes were rechecked against the wheel manifest, with
actual imported locations and1thread/JITdisabled checked. No rebuild was needed.
Final equilibrium1.7531102372888848e-11 and compatibility1.3755035596190583e-17;
12line-work samples recovered. These are solver checks, not connection fidelity.

Archive example-installed-v1.zip SHA256 `d1122b5f1d3e3d956825d6e7362addf5cfacfc4ee54b81aee6612bec9a6e1d57`; source logs in example-source-v1.
User documentation states the explicit policy, run command and scope limits.
ANYfem line persistence and M2 acceptance remain open.

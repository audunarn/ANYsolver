# Tilted relative Q4 public workflow

The existing finite Q4/Q4 fixture has 15 nodes, 90 coordinates and 16 accepted poses: tilt to 60 degrees, load, relative slide, open and recontact. The source and target anchor controls preserve the existing free variables, physical directors, shell offsets, complementarity scales and solver settings. This handoff changes persistence and caller validation only; the private solver package is unchanged.

With the verified private package on the import path (PowerShell, Python314 with its existing dependencies):

```powershell
$env:PYTHONPATH='C:/ANYworkspaceWork/contact_s3_rim_recontact_delivery_20261009/candidate-final/site;C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001'
$env:NUMBA_DISABLE_JIT='1'; $env:NUMBA_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'; $env:OPENBLAS_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'; $env:BLIS_NUM_THREADS='1'; $env:VECLIB_MAXIMUM_THREADS='1'
Set-Location C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001
& C:/Python/Python314/python.exe -m examples.general_contact_tilted_relative_sliding --through-step 16 --output fresh.json
& C:/Python/Python314/python.exe -m examples.general_contact_tilted_relative_sliding --assess-saved fresh.json --output assessment.json
& C:/Python/Python314/python.exe -m examples.general_contact_tilted_relative_sliding --through-step 16 --restart fresh.json --output terminal.json
```

Explicit output paths must be new. The legacy default remains `--through-step 4`; `--restart` accepts valid owner checkpoints, and `AUTOMATIC_DOMAIN_RESULT` remains an output fallback. Stdout is a concise status summary. The full output includes poses, pressure coordinates, history, snapshots, serialized material states and the original solver checkpoint.

Saved assessment reconstructs physical vertices independently using an 80-digit director exponential and the retained exact-binary original-Q1 gap/chart oracle. It checks the 50 micrometre penetration budget, declared open/active stages, controls, pressure/support identities, ordered snapshot/history inventory and terminal checkpoint/state correspondence. Terminal snapshots precede owner sealing: every mechanical field must match, while the two checkpoint seal fields are checked separately by the existing configuration/hash binding guards at reference deformational coordinates. This does not replay constitutive semantics. Stored residual and NCP values are producer-reported; this assessment does not independently assemble equilibrium. Earlier caller-provided poses and material fields are checked for consistency, not authenticated by a self-hash or the terminal checkpoint.

A complete saved report preserves supplied prefix poses on continuation. A bare checkpoint contains no earlier poses: a restarted suffix therefore remains a suffix and cannot pass complete-pose assessment. A terminal restore has zero new increments and is separately labeled; it is not evidence of an accepted continuation.

Returned partial snapshots are retained on a failed solver result. A state-serialization failure records NONPASS and retains returned displacement fields and available diagnostics, without inventing state or checkpoints. The current solver has no accepted-increment callback; a hard process timeout cannot produce a fabricated accepted prefix.

## Evidence and status

Current installed evidence is recorded in `C:/ANYworkspaceWork/contact_tilted_relative_public_delivery_20261009`. The verified 648-payload wheel is `C:/ANYworkspaceWork/contact_s3_rim_recontact_delivery_20261009/candidate-final/wheel/anysolver-0.4.7-py3-none-any.whl`, SHA256 `6f4f4023f0193b8c1c52fc788258091c5e6664107460b26079b97cc75680df66`; no rebuild was needed. Guarded commands and source/input hashes are in PREPARED and its prospective revisions. Fresh16 completed in70.5365806s, current15 prefix in55.0328870s, current bare15→16 in15.4075152s. Final saved assessment passed all16 poses and20 focused checks passed with0failures/errors/skips in34.6820966s; maximum final process-tree memory221.102MiB. These are measured entrypoint/check costs, not a whole-route speedup claim.

The real rich15→16 continuation preserved15 supplied poses and passed assessment; bare and rich terminal u/z agreed with fresh16 at inherited u rtol1e-8/atol1e-12 and z rtol1e-7/atol1e-12. Rich terminal16→16 was separately verified with zero new increments. The conservative independent gap bound was at least−17.996924micrometres across16 poses, within the existing−50micrometre budget; maximum producer-reported NCP relative force was8.32746e-11. Stored equilibrium was not independently reassembled.

Two NONPASS attempts remain retained: historical checkpoint analysis-contract incompatibility, and the first saved-assessment snapshot-before-seal mismatch(17passed/2failed). The latter was corrected without replaying production trajectories by comparing all mechanical fields and checking owner seals separately. Lead closed DEV360:207.8404101s used,152.1595899s unused, live0, no pooling. FINAL_HANDOFF.md, FINAL_BINDINGS.json and CLOSURE.json give exact evidence and remaining limits.

Existing finite-Q4 kernel, tangent, admission and historical chain evidence is reused by impact. This is a development handoff, not engineering acceptance or release, and supplies no S3 finite-rotation/native-mechanics extension or broader cut-front stability claim.

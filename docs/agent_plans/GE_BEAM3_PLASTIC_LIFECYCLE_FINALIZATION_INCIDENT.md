# Complete worker evidence preserved after final receipt-boundary failure

Source794e3685c5c1c4723d0dbb52b8aa3be9aa73282a,
tree9b5e5d34fa1b2df0b8b4efb4a7af5f97460a5819. Its fresh rehearsal completed all
19 workers successfully in81.671040seconds: 46unit tests, both full/prefix/
resume paths, original-origin material captures/checks, all six injected
cancellation/resume cases and thirteen actual mutation rejections per mesh.
All process trees are empty. Longest child14.075887seconds, peak163987456bytes.

The first correction fixed per-worker validation but missed a second consumer:
the final whole-wave validator still received the in-memory wave with live
tuple accounting fields. It raised the same canonical-list receipt error.
No canonical aggregate or acceptance was created. The saved wave's success
flag describes successful worker execution ONLY, not accepted publication.
This attempt remains BLOCKED_GE_BEAM3_PROCESS_OR_EVIDENCE.

Complete raw source/evidence/logs/receipts and preflight are preserved in
C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-plastic-lifecycle-794e368-incident-20260909.
All232 entries byte-verified after publication. Manifest27438bytes,
SHAA1D793DF77E7D9CD0FB71E4A1CAC77EAFB31C83B3C125FE30794E5DB995C7501.
Original wave16930bytes,
SHAEFFE9BB2A7C2A59FE4F9707EA0A535ED412F840EAAB7D7B8D0C6E08ED4D98BE6.
Do not retry its command or mutate its original temporary output root.

A read-only archive audit reconstructed a DIAGNOSTIC-only summary from the
original completed worker files, rechecked both independent material packets,
and successfully validated the complete decoded19-worker graph. It ran no
native solver and created no acceptance. This confirms the second failure is
at the receipt representation boundary, not a native state/mechanics failure.
Diagnostic10348bytes,
SHA7FF99F3D4B26725F7336B8127D4D55F78F0308DF96DBDA37128B730542E5B17B.
It is not silently promoted or substituted for a qualified rehearsal.

The successor reads the actual saved whole-wave bytes after requiring exact
equality with the canonical encoding of the live object, just as at the
per-worker boundary. All strict validators remain unchanged. A regression
uses the hash-bound COMPLETE actual failed-publication graph: the live tuple
version must fail, while the strictly decoded original version must validate
both cases and all19workers. Additional tests reject live/stored disagreement
and noncanonical whole-wave bytes. Test this complete finalization path before
any new scientific execution. Freeze the three-path correction (coordinator,
tests, this incident); only then use a distinct new-source rehearsal root.

No mechanics, field/state law, geometry, programme, tolerance, case inventory,
resource limit or public/default change. Both historical incidents remain
preserved; neither is a scientific NO-GO or a full qualification result.
No automatic retry. Full production GE-B3 and beam-shell goal remains active.

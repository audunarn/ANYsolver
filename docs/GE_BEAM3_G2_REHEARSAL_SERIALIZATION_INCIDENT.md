# G2 rehearsal serialization incident (not a formal execution)

Candidate `c73bf70e7b5176ad6f0071456875d1a62c7210fe`, tree
`5026d887106bed232eec087f9925f8d658734555`, passed all 54 mechanics/regression
tests in its first complete rehearsal child. The child completed in 30.0431s,
peak 205029376 bytes, exit 0, zero active processes. The coordinator then
rejected the existing diagnostic packet as noncanonical because its newly
added compact parser incorrectly omitted the native serializer's trailing LF.

This is a confirmation-harness defect, not a change in mechanics, tolerance or
native serialization. No formal run, aggregate or acceptance was produced.
Preserve the complete failed rehearsal externally at
`C:/Users/AudunArnesenNyhus/AppData/Local/Temp/ge-beam3-g2-rehearsal-c73bf70-20260910-v1`.

The successor corrects only the harness's expected compact bytes, the synthetic
infrastructure fixtures, and adds a direct native-serializer compatibility
regression including rejection of the missing newline. Runtime source and
scientific tests/fixtures are unchanged from c73bf70. Independently review the
successor and run a fresh rehearsal; do not reuse or overwrite the failed run.

The separate G1 49-test regression passed against this same unchanged runtime
in 45.2791s (peak 203710464 bytes, exit 0, zero active processes). Preserve that
development output at `C:/Users/AudunArnesenNyhus/AppData/Local/Temp/anysolver-g2-development-j7e0r2j3`.
It does not replace accepted G1 evidence.

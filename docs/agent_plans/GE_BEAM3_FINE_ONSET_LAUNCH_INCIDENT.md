# Pre-worker launch incident and directory-only successor

Source e76fb02341c0a864f912c2c246b28cb30274e549, tree
d6f12bcbb92b92444c925df9007e5721a7a6e5ba is preserved in Git history.
Its bounded pre-freeze authority suite passed53tests. The first rehearsal
coordinator invocation exited1 before any unit/mechanics worker was launched:

    python.exe -B -m docs.reference_cases.ge_beam3_fine_onset_wave
      --revision e76fb02341c0a864f912c2c246b28cb30274e549
      --output C:/Users/AudunArnesenNyhus/AppData/Local/Temp/ge-beam3-fine-onset-e76fb02-20260909/rehearsal
      --phase rehearsal

The traceback ended at run(), output.mkdir(), with FileNotFoundError WinError3:
the new parent directory did not exist. Read-only inspection confirmed the
parent path was absent. Source order confirms failure before unit directory
creation or supervise(). No worker, physical checkpoint, factor, process
receipt, canonical aggregate or acceptance exists for this launch. This is
BLOCKED_FINE_ONSET_LAUNCH_DIRECTORY, not a scientific contradiction.

Correction is limited to coordinator output-root creation: make missing parents
while retaining exclusive leaf creation and rejection of existing/repository
roots. Add tests for nested success, reuse rejection with preserved marker,
repository rejection and a parent regular-file failure. No mechanics, worker,
search rule, input authority, tolerance, process limit or scientific scope
changes. Preserve the failed command; never rerun it. Re-freeze this successor
and use a distinct successor-named external root for a new rehearsal launch.

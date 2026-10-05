# F06 v1 setup incident before mechanical execution

21 September 2026. The one-time invocation of frozen source `3797a3a`
exited `1` after 1.40 s during fixture import. Importing
`test_ge_beam3_coupled_modes` transitively reached
`test_ge_beam3_fibre_line_program.py`, which imports
`docs.reference_cases.ge_beam3_centered_line_load_oracle`; the
standalone runner had added `src` and `tests` but not the repository
root to `sys.path`. Python raised `ModuleNotFoundError: No module named
'docs'` at that import. The source's exclusive evidence root
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f06-loaded-rebase-v1/`
was independently checked absent after the failure. No `case()` call,
coupled solve, chart evaluation or scientific result occurred. There
is no v1 numerical evidence to adjudicate or reuse.

Retain v1 source and contract unchanged. The v2 registration changes
only the fixture import path and uses a fresh exclusive root; it must
undergo a new independent pre-run check and source freeze. This
incident is not an F06 mechanics failure or a gate pass.

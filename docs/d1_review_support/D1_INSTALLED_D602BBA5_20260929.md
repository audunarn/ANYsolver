# Current-source installed D1 example — development evidence

**29 September 2026.** An offline wheel was built from committed solver
source `d602bba5` in the isolated general-contact worktree. The working-tree
diff of `src/anysolver` and `pyproject.toml` against that commit was empty.
The wheel `anysolver-0.4.7-py3-none-any.whl` has SHA-256
`D0E3F7F1AF9ADA34FBC3660793C71B021AC1087B1D9D38E8FC5455B3CC16AF02`.
Build and `--no-index --no-deps` target installation completed under their
180 s/1 GB process-tree caps. The unchanged standalone example has SHA-256
`4FC744756387B64B777D9DDF1A3D4EFAA539CF64138EBE881A636801B66DA885`.

The example ran from
`C:\ANYworkspaceWork\general-contact-standalone-d602bba5`, outside the
checkout, with `PYTHONPATH` set only to that wheel's isolated install target
and user site packages disabled. Its effective `anysolver.__file__` is
`C:\ANYworkspaceWork\general-contact-standalone-d602bba5\target\anysolver\__init__.py`.
The optional `ANYgeometry` dependency resolved to the host's existing
editable checkout at `C:\Github\ANYgeometry\src\anygeometry`, version
0.4.3; wheel metadata declares `ANYgeometry>=0.4.3,<0.5` for the
`general-contact` extra. Dependency installation from an index was not
tested.

The 16-Q4/two-S3 standalone example completed force-control press and all
eight displacement press/slide/open/recontact steps in 158.05 s/410 MB.
Split restart reproduced final displacement and integrated contact force
exactly. Every independently reconstructed accepted-pose gap passed the
unchanged `−50 µm` budget; the minimum was `−35.160821 µm`. The public
capability output remains `development_only`.

[Full example result](d1_installed_d602_example.json),
[run resource](d1_installed_d602_example_resource.json),
[wheel build resource](d1_installed_d602_wheel_build_resource.json),
and [install resource](d1_installed_d602_wheel_install_resource.json)
retain the exact outputs. The wheel and external install target remain under
`C:\ANYworkspaceWork\general-contact-standalone-d602bba5` for reuse.

This is local installed-package compatibility after the cross-side search
change, not independent D1 acceptance, application integration or release.
The larger 12×12/4×4-cell deformable-target contrast workflow, pressure
gate and experimental `overlap_local_dev` swept certificate were not part
of this standalone installed example. Review source impact before reusing
this evidence for a later frozen candidate.

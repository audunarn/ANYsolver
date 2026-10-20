# Slice 1 handoff: reliable static-contact public entrypoints (2026-10-20)

Owner: Mistral slice worker. Branch `codex/contact-static-slices-20261020`,
baseline `36a5d5d8c`. Owned files only:
`src/anysolver/general_contact/__init__.py`, the three examples
(`general_contact_automatic_s3_pair.py`, `general_contact_s3_physical_orientation.py`,
`general_contact_s3_friction_physical_path.py`), `README.md`,
`tests/test_general_contact_lazy_import.py`, narrowly focused new tests,
`docs/GENERAL_CONTACT_STATIC_CANDIDATE.md`, this file.

## Early progress checkpoint (turn ~6 of 30)

### Findings

- `S3SlidingFrictionSettings` (base class of the five already-exported friction
  settings) lives in `s3_sliding_friction.py` and was only importable via the
  submodule. The package `__getattr__` already routes the five subclass names
  to `s3_sliding_friction`; adding the base name there preserves submodule
  identity (same class object) and lazy loading.
- The top-level `anysolver` package forwards only `_GENERAL_CONTACT_EXPORTS`
  (`src/anysolver/__init__.py:257-274`), a file outside this slice's ownership.
  The new export is therefore public at `anysolver.general_contact` only; the
  existing lazy-import test's top-level identity loop must not gain this name.
- The friction example constructed `S3SlidingFrictionSettings(.3, 1000.,
  (2e-7,)*60, 145)` positionally with a hard-coded 60. The model has 10 nodes
  x 6 DOFs = 60, matching `model.mesh.dof_manager.total_dofs` (property on the
  DOF manager, `mesh_gen.py:493`). Keyword construction with
  `(2e-7,)*model.mesh.dof_manager.total_dofs` keeps the exact probe 2e-7 and
  the 145 evaluation cap while making the length requirement self-describing
  (`steps_by_dof` needs one entry per model DOF).
- The other two owned examples already construct `ContactSolverSettings` with
  keywords only; no value changes were needed there. The measured settings
  strings (`jet2_s3_dev`, `control_projection_dev`, `physical_sides_dev`) stay
  exactly as-is; the new doc states that these historical development-profile
  names are used by the selected measured examples and that the suffix alone
  establishes neither measured coverage nor qualification.
- README line 123 (rigid-sphere frictionless impact row) is correct for that
  distinct impact route and stays. README line 218
  ("no general shell-shell, body-body, frictional, rolling, or self-contact")
  was the blanket statement contradicted by the measured W3/W4/W10 candidate
  workflows and was corrected to the measured opt-in guided candidate scope.
- Existing `tests/test_general_contact_lazy_import.py` needed no weakening;
  the additive export is checked in a new focused test file instead.

### Intended edits (as planned, all executed)

1. `src/anysolver/general_contact/__init__.py`: add `S3SlidingFrictionSettings`
   to the `s3_sliding_friction` lazy route and to `__all__`.
2. `examples/general_contact_s3_friction_physical_path.py`: public package
   import, keyword construction, DOF-count-derived `steps_by_dof` length,
   comment stating the one-entry-per-DOF rule. Values unchanged.
3. `examples/general_contact_automatic_s3_pair.py` and
   `general_contact_s3_physical_orientation.py`: one comment each marking the
   measured candidate settings strings; no value/flag changes.
4. `README.md`: corrected the blanket limitation bullet and extended the
   general-contact development row with the measured opt-in guided candidate
   scope and a link to the new doc. Impact/contact row untouched.
5. New `tests/test_general_contact_public_friction_settings.py`: lazy public
   export, submodule identity, `__all__`/`dir` membership, keyword/positional
   equivalence, validation failures, exact example settings values (2e-7
   probe, 145 cap, length == total_dofs == 60).
6. New `docs/GENERAL_CONTACT_STATIC_CANDIDATE.md`: supported entrypoints,
   install/run guide (normal, automatic physical-side shell pair, friction,
   archive workflows, restart commands), measured settings strings, scope and
   limitations.

## Final state

### Working outcome

`from anysolver.general_contact import S3SlidingFrictionSettings` is a lazy
public export preserving submodule identity; the friction example uses it
with keyword settings and a DOF-derived step-vector length while retaining
the exact measured 2e-7 probe and 145 evaluation cap; README states the
measured opt-in guided candidate scope instead of the blanket no-friction/
no-shell-shell limitation; a concise install/run guide with restart and
archive commands and scope/limitations is published at
`docs/GENERAL_CONTACT_STATIC_CANDIDATE.md`. No values, physics, tolerances,
stopping rules, capability flags or measured settings strings changed.

### Doc repair pass (2026-10-20, this pass)

A prior follow-up hit its 12-turn bound during inspection and made no edits;
root inspected both files and supplied all facts. This pass edited only
`docs/GENERAL_CONTACT_STATIC_CANDIDATE.md` and this file, with four changes:

1. The measured S3 rigid-tool claim now covers only the S3 plane and finite
   planar triangulated rigid tools; capped cylinders were removed from the
   claim and the round beam profile example remains listed as a separate
   route outside it.
2. The contradictory `_dev` paragraph was replaced with: "These historical
   development-profile names are used by the selected measured examples. The
   suffix alone establishes neither measured coverage nor qualification;
   only the listed workflows have the stated evidence."
3. The run directory is the repository root or the extracted bundle ROOT
   containing `examples/`; the restart recipe is three separate command
   lines (partial `--through-step 3`, checkpoint extraction to
   `checkpoint.json`, resume `--through-step 7 --restart checkpoint.json`),
   each on its own Markdown code line, not semicolon-joined.
4. Installation now points to the current bundle
   `C:/ANYworkspaceWork/contact-incremental-delivery-20261020/slice1/ANYsolver-contact-candidate-20261020-s1.zip`
   (extracted ROOT has `wheelhouse/` with the six pure-Python private
   wheels: ANYsolver, ANYresults, ANYmaterial, ANYgeometry, ANYmesher,
   ANYfileio; in a fresh venv from the bundle ROOT install
   `python -m pip install --find-links wheelhouse "ANYsolver[general-contact]==0.4.7+contact.candidate.20261020.s1" "ANYgeometry[planar]==0.4.3"`;
   numeric/Shapely dependencies resolve normally, not offline unless
   separately provided), distinguished from the original 2026-10-19 bundle,
   whose immutable historical claims apply to it alone.

### Root verification of the current bundle (no rerun needed)

Root built the new wheel and verified 727 files equal across source, wheel
and installed artifact. Installed-artifact runs passed: normal contact,
full friction, partial/extract/resume restart, and archive commands, with
full and resumed histories exact. This closes the "Not run:
installed-artifact example runs" item above. The source focused 5-passed
evidence (`slice1-static-entrypoints-attempt1`) is retained; nothing was
rerun in this doc-repair pass.

### Changed files

- `src/anysolver/general_contact/__init__.py` (modified, +2 lines)
- `examples/general_contact_s3_friction_physical_path.py` (modified)
- `examples/general_contact_automatic_s3_pair.py` (modified, +1 comment)
- `examples/general_contact_s3_physical_orientation.py` (modified, +1 comment)
- `README.md` (modified, 2 lines)
- `tests/test_general_contact_public_friction_settings.py` (new)
- `docs/GENERAL_CONTACT_STATIC_CANDIDATE.md` (new)
- `docs/contact-incremental-20261020/SLICE1_HANDOFF.md` (new, this file)
- `tests/test_general_contact_lazy_import.py`: owned but unchanged; the
  existing check passes unmodified against the additive export.

Pre-existing root work outside this slice, untouched: the 2026-10-20
transition note in `docs/GENERAL_CONTACT_CANDIDATE_HANDOFF_20261019.md`
(35 inserted lines present before this slice began).

### Checks actually run

One supervised focused pass (no repair pass needed), attempt
`slice1-static-entrypoints-attempt1`:

- Command: bounded supervisor `supervise.py --seconds 180` over `entry.py
  pytest tests/test_general_contact_lazy_import.py
  tests/test_general_contact_public_friction_settings.py -q` with unique
  basetemp/junitxml paths inside slice1.
- Result: exit code 0, **5 passed in 10.51s**, 0 failures/errors/skips
  (1 existing lazy-import check + 4 new focused checks). Peak sampled
  aggregate RSS 314,871,808 bytes; charged 11.26 s of the 1,800 s allowance;
  no survivors.
- Evidence: `C:/ANYworkspaceWork/contact-incremental-delivery-20261020/slice1/checks/slice1-static-entrypoints-attempt1/RESULT.json`
  and `stdout.txt`, junit
  `C:/ANYworkspaceWork/contact-incremental-delivery-20261020/slice1/junit-attempt1.xml`.
- Not run: full CI, installed-artifact example runs (root tests the installed
  example against the new artifact), and the eight W modules (unchanged source
  except the friction example's settings construction, which the new focused
  test pins to the exact measured values).

### Unresolved decisions

- None blocking this slice. Resolved by root decision: the top-level
  `anysolver` export is out of scope; only the new
  `anysolver.general_contact` export was requested.
  `src/anysolver/__init__.py` remains untouched.
- The 14 pre-existing CI failures are unrelated to this slice and untouched.

Root integration: installed command checks passed after this worker assessment. Root changed guide invocations to module form so sibling example imports resolve from the extracted bundle root, and pinned all six private packages in the installation command. These are artifact/document integration corrections; numerical settings and solver source are unchanged.

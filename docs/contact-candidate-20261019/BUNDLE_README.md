# General-contact candidate 0.4.7+contact.candidate.20261019

This is an installed, headless Python candidate for the restricted static/quasistatic examples below. The fixed batch completed: 37 test executions, no test failures or skips (23 installed-artifact executions, 14 source executions). No solver-code repair was needed. This is a candidate with measured support, not full general-contact qualification or an application release.

Seven declared analytical force/gap/contact-length/Coulomb outputs met the 0.1% candidate target; the largest measured error was 3.435e-9%. These errors measure agreement with the **declared finite-penalty law and example geometry**, not ideal hard contact, mesh/model accuracy or universal engineering accuracy. The B3 example deliberately allows 1mm overclosure with a 2mm declared tolerance and 10mm tube radius. Choose physically justified penalty stiffness and dimensional gap limits for a new model. Demonstration material/scales are not calibrated engineering validation.

## Install using ordinary Python packaging

Tested interpreter: CPython 3.12.13, Windows x64. This folder contains five local wheels: ANYsolver plus pinned ANYmaterial, ANYgeometry, ANYfileio and a restricted pure-Python ANYmesher companion. Normal dependency requirements are listed in `requirements-tested.txt`; their wheels are not bundled. The four numerical versions are measured pins; the Shapely lower bound supplies the declared dependency closure and is not a measured backend claim. Validation installed the five new private wheels into a fresh isolated target while reusing the recorded numerical environment. A cold numerical-dependency install/new-venv recipe was not executed here; the ordinary recipe below is provided for reproduction. No network was used during this build or verification. Offline installation needs those numerical wheels in a local wheelhouse; an online setup may use its normal package index.

From this delivery folder, create an ordinary clean environment:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-tested.txt
.venv\Scripts\python -m pip install --no-index --find-links wheelhouse ANYsolver==0.4.7+contact.candidate.20261019 ANYmaterial==0.2.0 ANYgeometry==0.4.3 ANYmesher==0.5.0 ANYfileio==0.3.2
.venv\Scripts\python -c "import anysolver,importlib.metadata; print(importlib.metadata.version('ANYsolver')); print(anysolver.__file__)"
```

The version must be `0.4.7+contact.candidate.20261019` and the import must resolve inside the new environment, not a source checkout. The unchanged module constant `anysolver.__version__` is the base version `0.4.7`; use distribution metadata for this artifact identity. No task-specific `.pth`, source-path injection or workstation directory is needed by this recipe. Evidence wrappers in the parent task directory are historical execution tooling, not installation prerequisites.

The recipe installs the normal declared dependency closure, including Shapely>=2.0 required by ANYmesher -> ANYgeometry[planar]. Offline installation must supply a matching Shapely wheel along with the ordinary numerical wheels. Shapely was not imported or exercised by this existing-mesh contact verification; cold dependency installation was not measured. The ANYmesher companion excludes optional native acceleration. It is not a replacement for qualified native ANYmesh or a complete ecosystem distribution, and no meshing/native-performance claim is made.
## Run the supplied public examples

Set the effective profile used for the measurements:

```bat
set NUMBA_DISABLE_JIT=1
set NUMBA_NUM_THREADS=1
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
set NUMEXPR_NUM_THREADS=1
set PYTHONHASHSEED=0
.venv\Scripts\python -m examples.general_contact_s3_plane
.venv\Scripts\python -m examples.general_contact_round_beam_plane
.venv\Scripts\python -m examples.general_contact_round_beam_pair
.venv\Scripts\python -m examples.general_contact_s3_physical_orientation
.venv\Scripts\python -m examples.general_contact_s3_friction_physical_path --output friction-full.json
```

For a persisted active friction restart, use fresh output names:

```bat
.venv\Scripts\python -m examples.general_contact_s3_friction_physical_path --through-step 3 --output friction-active.json
.venv\Scripts\python -c "import json; from pathlib import Path; p=json.loads(Path('friction-active.json').read_text()); Path('active-checkpoint.json').write_text(json.dumps(p['checkpoint']))"
.venv\Scripts\python -m examples.general_contact_s3_friction_physical_path --restart active-checkpoint.json --output friction-resumed.json
```

Export a real ordinary static contact result and read it through the public detached reader:

```bat
.venv\Scripts\python -c "from pathlib import Path; from examples.general_contact_static_results_archive import analysis; r,a=analysis(); Path('contact-results.json').write_bytes(a.to_bytes()); print(r.status,a.sha256)"
.venv\Scripts\python -c "from pathlib import Path; from anysolver.general_contact import read_static_contact_results; a=read_static_contact_results(Path('contact-results.json').read_bytes()); print(a.sha256)"
```

The supplied examples are unchanged copies of the measured source inputs. The final combined smoke explicitly excluded checkout, tests and snapshot roots from Python paths and ran the bundled normal-pair/friction modules plus archive producer/reader against the installed wheels. Relative paths above are portable; tests/original worktree are not required for these demos.

## Supported demonstration range and evidence

| Profile | Demonstrated behavior | Boundary |
|---|---|---|
| Elastic S3 V2D / rigid plane or finite triangulated tool | Static normal response, physical skin offsets, press/open/recontact, detached archive | Declared guided geometry, finite footprint and penalty/gap law |
| Physical-side S3 shell pair | Press/slide/open/recontact, nonzero lower-shell normal displacement, normal equilibrium and instantaneous both-body virtual/residual work | Upper actuator/rotations guided; only lower node9 normal DOF free; not unrestricted two-body bending |
| S3 material Coulomb friction | Stick, slip, reversal, opening/recontact, nonnegative dissipation, active/open restart, in-flight failure/cancellation rollback | Target normal motion/rotations constrained; target deforms in-plane; no target normal bending claim |
| Declared round B2/B3 tubes | Beam-plane and beam-pair static force/displacement control, checkpoint and analytical line-penalty checks | Specified radius/end ownership; no arbitrary section/native dynamics/friction claim |
| Public result archive | Real installed solve, snapshots/checkpoint, exact detached producer-field preservation and corruption refusal | Headless public API; no application/UI admission |

`MEASURED_SUPPORT.json` contains actual outputs and comparisons. Active/open restart displacement differences were zero, with unchanged exact history assertions passing. Thirteen numerical quantity comparisons passed the candidate bound across effective SkylakeX and Haswell BLAS profiles **on the same host**. Ubuntu and cross-machine reproducibility remain unmeasured.

There is **no independently established 2% coupled displacement/response claim** for the guided shell pair or crossed beams. Their measured equilibrium, gaps, histories and consistency are useful evidence, not a substitute for a matched independent response benchmark.

See `ACCURACY.md`, `KNOWN_LIMITATIONS.md`, `SOURCE_AND_ARTIFACT_VERIFICATION.json`, `ACCOUNTING.json` and `MANIFEST.json`. Retained evidence includes exact commands, stdout/stderr, environment/origins, source identity and original failures. Two ordinary tooling failures were preserved and repaired: missing pip in the existing venv, and relative pytest input paths when moving to a non-checkout working directory. They were not solver failures.

The capability report still returns `admitted_for_application=False`; released/accepted flags were not changed. Full C0-C9/D0-D8, independent-family acceptance, mandatory CI/performance, native/dynamics/impact and C9 applications remain separate work. No commit, push or publication was performed.

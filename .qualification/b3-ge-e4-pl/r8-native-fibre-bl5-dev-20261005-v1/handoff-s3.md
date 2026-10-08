# Stable elastic native S3/mixed-shell BL5 development handoff

Scoped DEV outcome: verified against assigned criteria for the concrete
source/installed cases below, with acceptance gaps retained. Working public compile/preflight -> accepted solve -> physical recovery
-> fresh binary restore/continue -> conservative full42/native+BL5 buckling,
including chart restart and prestress parity. Root-provided baseline `e72fa676`.
No Git, sibling edits, contact communication, workers, old archive/campaign
consumption or product default change by this owner.

Explicit adopted material policy:
`BL5_ELASTIC_NATIVE_FIBRE_MIXED_SHELL_V1_DEV`; native-line spectral result,
capability and bound pencil identity:
`B3_GE_NATIVE_FIBRE_MIXED_SHELL_BL5_ACCEPTED_BUCKLING_V1_DEV`.
The existing Q4-only policy/domain and other request defaults stay unchanged.
Admitted meshes contain flat elastic S3-V2D, optionally algorithmic Q4. All-S3
has no Q4 selector dependency. Actual BL5 cell-edge incidence, five director
rows/free normal spin, physical lift/full42, quadrature and bases are unchanged.
Existing stable S3 material/prestress/chart and native checkpoint schema/replay
are reused; model identity binds the explicit material policy/cells/lines/beams.
No equations, tolerances, schema/reader, mass, symmetry or condensation changes.

Changed files:

- `src/anysolver/_stiffened_shell_ge_experimental.py`: separate explicit
  mixed-shell admission/capability/model identity and narrow stable-native
  checkpoint admission; old Q4-only admission preserved.
- `src/anysolver/_stiffened_shell_ge_point_buckling.py`: owner-selected distinct
  policy, native-line mixed-shell admission and bound public pencil identity;
  raw immutable matrix digest remains separate.
- `src/anysolver/stiffened_shell.py`: exports explicit material policy.
- `examples/stiffened_shell_native_fibre_bl5.py`: optional `--shell s3|mixed`,
  Q4 default preserved, actual public recovery/restart/continue/spectrum.
- `tests/test_stiffened_shell_native_fibre_bl5.py`: shared independent S3/native
  full-coordinate scatter plus direct BL5 scalar-work oracle; native/Q4
  oracle/refusals retained.
- New `tests/test_stiffened_shell_native_fibre_bl5_s3.py`: 16 public nodes across
  axial/biaxial, fibre/generalized mixtures, P0/coarse-P1, all-S3/mixed shells;
  derivative/spectral oracle, cancellation/corruption/mutation/identity
  controls, chart restart and continuation, topology/admission and examples.
- `docs/reference_cases/stiffened_shell_native_fibre_bl5.md`: grouped domain,
  evidence and remaining obligations.

Finite driver and native elastic helper were unchanged and hash-bound as
physical dependencies. Original equilibrium1e-8/gap1e-9, eigen/constraint1e-8
and actual-update derivative1e-6 checks remain. Every-station native elastic
branch/history guards run before publication. Programming/ownership errors
propagate unchanged; yielded-domain refusal retains accepted prefix.

Checks actually executed:

```
C:/Python/Python314/python.exe .qualification/b3-ge-e4-pl/r8-native-fibre-bl5-dev-20261005-v1/run-s3-v1.py
C:/Python/Python314/python.exe .qualification/b3-ge-e4-pl/r8-native-fibre-bl5-dev-20261005-v1/integration-s3-v1.py
```

Source: **16 PASS**, zero failures/errors/skips, pytest44.341s;
supervisor47.1623428s, sampled peak188522496B. Source syntax checked before run.
Supporting root source review found no consequential defect before installation.
Installed: offline no-deps/no-build-isolation wheel and no-deps/no-index isolated
install PASS; **32 PASS**, zero failures/errors/skips, pytest73.842s (new16,
impactedQ4-native14, legacy point1 and BL5 fixed-history/chart/restart1).
Both direct installed count2 public examples PASS. Entire424 package Python
module bytes equal source/prebuild manifest; all245 loaded anysolver prefixes
inside `installed-s3-v1`. Current8 bound source inputs still equal source-v1.
Installed supervisor84.8776507s, peak194437120B, sampler maximum1. Build/install
were sequential setup-only children (maximum2), preceding numerical bodies.

Effective runtime: isolated NumPy2.5.3/SciPy1.18.1/Numba0.68.0/llvmlite0.50.0
imports verified, affinity[0], JIT disabled, both BLAS pools1, unforced SkylakeX,
OPENBLAS_CORETYPE unset. Source sampler maximum5 is retained honestly: one PID,
four unresolved final thread start-module queries alongside the main thread;
not evidence of five numerical jobs. Inherited sampler ceiling8 met; effective
pool settings1 proven. No concurrent numerical job was launched. All raw
thread samples are retained; the unresolved exit-query cause is not claimed
proven.

Fresh wheel: `wheel-s3-v1/anysolver-0.4.7-py3-none-any.whl`, SHA256
`b3d5f572797f3c2954d1bf9dc1c6b4293da14c5812e543dbde7f314a60207291`.
Bindings: `binding-s3-v1.json`, `installed-binding-s3-v1.json`; prelaunch source
copies `executed-source-s3-v1/`; source/package map
`source-package-modules-s3-v1.json`, `installed-package-modules-s3-v1.json`;
loaded imports `installed-loaded-modules-s3-v1.json`; exact effective runtime
`runtime-s3-v1.json`, `installed-runtime-s3-v1.json`; JUnit `junit-s3-v1.xml`,
`installed-junit-s3-v1.xml`. Supervisor SHA256
`ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec`.
Raw source/build/install/installed execution/stdout/stderr/thread samples remain
in `focused-s3-v1/`, `build-s3-v1/`, `install-s3-v1/`,
`installed-example-s3-v1/`. All earlier Q4-v1 failures/records remain untouched.

Installed biaxial/mixed-member P0 examples, each8 fibre stations/12 line work
records, generation2/restored1, exact fresh/continued checkpoints and unchanged
accepted bytes during spectrum:

| Mesh | Model identity | Equilibrium | Gap | Factors | Max original residual |
| --- | --- | --- | --- | --- | --- |
| S3 | dd700e8b380b1e3dec2ad770112117dc14f1e600af833ad2f70f98c18b1a49bb | 8.547380158448011e-11 | 1.8340047461587445e-17 | 11571.760588881254, 67169.75583918633 | 3.9264622095729003e-16 |
| Mixed | 8c3d6c42f92221bc726169e9637690be09a14ce6a7fffa2a0b979d021e8537be | 2.3353454646476915e-10 | 1.4190182000065093e-17 | 8257.624439573543, 44359.1277896717 | 2.9971720125891697e-16 |

Exact output: `installed-example-s3-v1.json`, `installed-example-mixed-v1.json`.
No numerical job active; slot released to root. No source repair or retry was
needed in this milestone. Root integration/review is separate; implementation
and development checks do not establish scientific or production qualification.
Plastic native/S3 BL5, consumer integration, scale domains and different-family
acceptance remain mandatory open obligations. Cached Mistral unavailability
caused fallback; supporting same-family review does not satisfy that gate.

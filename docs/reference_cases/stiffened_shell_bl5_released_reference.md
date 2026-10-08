# BL5 released material-director reference preparation

Identity: `R8_BL5_RELEASED_MATERIAL_DIRECTOR_REFERENCE_LINEAR_V1_DEV`.
New source development reference, not an accepted physical reference or native
BL5 implementation. No historical campaign or frozen execution authority is
reused. The tool never launches an external executable.

## Explicit physical specimen and meaning

Two distinct Cartesian elastic continua use eight full-integration C3D20 bricks
and 102 physical nodes: a 1 m by 0.2 m plate, thickness 0.02 m, midsurface z=0;
and a straight 1 m rectangular bar of width 0.04 m and height 0.06 m, bottom
z=0.01 m and centroid z=0.04 m. Both materials are isotropic E=210 GPa, nu=0.3.
Static response requires no guessed density. Reference section axes are global
X/Y/Z. Independently integrated rectangle properties are A=0.0024 m2,
Iy=7.2e-7 m4, Iz=3.2e-7 m4 and G=E/[2(1+nu)]; no torsion constant or shear area
is guessed because the bar is a resolved continuum.

The whole plate x=0 face is fixed in all three translations. The bar has no
additional clamps: its reference attachment equations at x=0 tie five trace
components to the fixed plate, while normal spin remains locally free. The
only applied load is +1 N in global Z at the physical bar-tip section-centroid
node (1,0,0.04). This is a declared point force, not pressure, torque or a rigid
end section. All exact IDs, topology, dimensions, material, supports and load
are in generated `model.json`; its model/deck SHA-256 binds the construction.

At x=0,0.25,0.5,0.75,1, actual material points at y=0 define plate lower/upper
faces s-/s+ and bar section lower/upper faces b-/b+. Reference attachment points
s+ and b- coincide. The bar normal arm is -0.03 ez and plate top arm +0.01 ez.
For translations u, the five physical small-displacement gaps are:

```
c_position = u_b- - u_s+
c_director = (u_b+ - u_b-)_(x,y)/0.06
             - (u_s+ - u_s-)_(x,y)/0.02
```

Only the two perpendicular components of the normalized reference director
are linearized; axial face separation/thickness strain is not tied. The map
uses material face pairs, never geometric surface normal or drilling DOFs.
Solid Poisson/thickness and cross-section deformation remain part of this new
continuum body model; it is not an identical shell/retained-beam body operator.

This is a **five-station strong collocated director-hinge reference**. It is
not algebraically equivalent to native exact weak BL5 multiplier integration,
continuous bond enforcement, a six-row pose tie, or a finite-width weld/pad.
There is no response score until law/discrete work maps are matched and reference
convergence is addressed. This preparation only establishes a mechanism/output
route for a separately authorized smoke.

## Work, equation elimination and action recovery

Physical multipliers have three forces in N and two director covectors in Nm.
Their work is lambda.c; direct transpose accumulation supplies every material
sample force, including section and plate lever arms. Compensated normal spin
about each reference attachment point does zero local interface work; the two
perpendicular spins produce the appropriate director work. This local release
is not a global null mode of a finite attached line: separated force stations
can transfer normal torque through leverage.

For CCX, each position equation begins with one unique bar-bottom dependent
DOF. Each director equation begins with the bar-top x or y DOF and substitutes
the position equality, giving `u_b+ -(1+hb/hs)u_s+ +(hb/hs)u_s-=0`.
No dependent variable is reused on another row's RHS or as a fixed DOF.
These deck rows have a different scaled multiplier basis. Recovery uses the
original physical five-row map, never unconverted deck multipliers.

The [official CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf), sections
6.2.4 and 7.56, documents C3D20's 3x3x3 integration and first-term equation
elimination. The existing proven DOUBLE reader is reused with the new exact
node/element/output inventory. Its count-framed binary64 coordinates/U/root RF
are validated; ASCII RF at MPC nodes is not treated as verified interface force.
Full physical internal covectors are independently recovered by Cartesian
C3D20 isotropic 27-point integration. On free coordinates, the original physical
constraint transpose recovers multipliers; remaining support covectors, complete
bar/plate cuts, common-origin wrenches and work are reported. Raw residuals and
RF differences remain visible. Rank is only a recovery prerequisite, never a
law-selection or stability verdict. A parsed dataset is explicitly
`PARSED_REFERENCE_NOT_ASSESSED`, even if its equations are badly unbalanced.

## Prepared route and withheld external execution

Prepare a fresh directory with:

```
python -m scripts.r8_bl5_released_director_reference prepare --output <fresh-directory>
```

Proposed external smoke, only after root authorization and executable hash check:

```
C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe -i released
```

Working directory must contain the newly bound `released.inp`. Required executable
SHA-256 is `27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f`.
Deck requests `*NODE OUTPUT,DOUBLE,NSET=ALL` U and the ROOT RF dataset, plus
printed cross-checks. Root must supervise one CPU/pools, 600 s/2 GiB, preserve
command/environment/executable/deck hashes, stdout/stderr/exit and full outputs.
This assignment grants no CCX execution. The reader requires the pinned hash,
zero exit, explicit completion, one complete static increment at time 1, and
strict DOUBLE geometry/datasets; it retains actual mechanics residuals instead
of inventing a success status.

Before physical response scoring, inspect actual independent director and
surface-slope/shear fields, full gaps/equilibrium, support/internal/interface
work and both domain cuts. A full-yaw-tie negative or normal-substitution negative
must discriminate the intended mechanism. Actual external MPC/output behavior
and independent covector recovery remain unverified until that smoke; native
comparison, convergence, mandatory physical/scientific/different-family gates
and acceptance stay open. No automated execution or qualification claim exists.

### Execution provenance prerequisite

Physical parsing first hashes the **actual** `released.inp` bytes against the
prepared exact deck. A same-mesh change to MPCs, supports or load is rejected.
A preserved `execution-binding.json` must bind schema/status/exit, exact command
and working directory, the actual executable file hash, model identity, and
actual input/FRD/stdout/stderr/STA hashes. The CLI verifies actual executable bytes;
a caller-supplied digest alone is insufficient. Text is read as UTF-8 bytes
without newline normalization before hashing. Missing execution evidence returns
`UNVERIFIED_EXECUTION` with no physical response fields; nonempty stderr rejects
physical parsing pending adjudication. Bound parsing still explicitly refuses
physical acceptance. Offline parser controls use a synthetic executable and
synthetic manifest, never an external execution claim.

Schema is `R8_BL5_RELEASED_REFERENCE_EXECUTION_V1`. Manifest fields are `status`,
`exit_code`, `command`, `working_directory`, `executable_sha256`, `model_sha256`
and `files`; file keys are `released.inp`, `released.frd`, `stdout.log`,
`stderr.log`, `released.sta`. Expected status/exit are `completed`/0 and command
is `[absolute_executable_path,"-i","released"]`. This records a separately
supervised run; it is not new authority or cryptographic proof of execution.
Physical response scoring remains withheld. Independent recovered station
observations include midsurface transverse slopes from a frozen positive-side
Cartesian host (final x uses the left host), material director changes and their
sum as reference-linear transverse shear, separately from geometric-normal change.

### Preserved preparation failure

The initial offline suite passed 26 controls, but final verification of the
actual prepared file caught a Windows newline-conversion defect: metadata hashed
LF deck text while text output wrote CRLF bytes. The original deck, source/test
snapshots and binding remain intact, together with
`prepared-v1-byte-binding-failure.json`. That V1 preparation is not eligible for
an external smoke. The repaired preparation writes exact ASCII bytes and tests
both the actual prepared-file hash and CLI preparation path. A fresh versioned
check is required; no tolerance, physical model or external authority changes.

### Offline V2 verification and next action

State: **verified against assigned offline preparation/kinematic/work/parser
criteria**; actual external specimen remains **NOT_EXECUTED**. V2 passes 27
controls (pytest 0.76 s; JUnit 0.755 s), zero failures/errors. Controls include
actual CLI preparation and byte hash, unique dependent/SPC-safe MPC construction,
six common rigid fields, both director rotations and compensated free normal
spin, full-yaw-tie and geometric-normal-substitution negatives, arbitrary-field
transpose work/common-origin balance, independently integrated affine elastic
energy, strict identity/partial/nonfinite dataset and same-mesh changed
MPC/support/load negatives. Synthetic parser fixtures cannot establish external
response or equilibrium; the unbalanced fixture exposes unit residual rather
than a success claim.

V1's 26 passing controls and failed actual deck-byte binding remain preserved.
V2's exact prepared file now matches deck SHA-256
`54d72909717c07a82bdd4bb70e87b5084a402e529e60ba1a4576b86d99c0b154`, with model SHA-256
`a22170179b6e257a47288ff825a3b69ad503e5e3c4a040fcd5f3b53933c86463`.
Tested source SHA-256:
`e8a090dd3b575ecf3520112d6fe949252002273c5619b318bd932bf2dcc7cc97`;
test SHA-256:
`56cd8d3b825f9a54f62025b61540e301335a90e4cfd89adfa1a180a4d4c26f31`.
Current code/test and executed snapshots match pre-run bindings.

Raw versions, exact source snapshots, bindings, JUnit, runtime, execution/logs,
prepared decks/model and V1 failure are grouped in
`.qualification/b3-ge-e4-pl/r8-bl5-released-reference-dev-20261005-v1/`.
Supervisor V2 wall time 1.344919 s, sampled tree peak 92,938,240 bytes, affinity
`[0]`, sampled numerical/unresolved maximum one. Effective NumPy OpenBLAS and
OpenMP pools were one, Numba one thread/JIT disabled; OPENBLAS_CORETYPE was
removed. Selected interpreter file version is 3.14.2; installed metadata reports
NumPy 2.4.6, Numba 0.65.1 and pytest 9.0.3. Actual pool paths are recorded in
runtime-v2.json; source import dependencies are explicitly bound. The runtime
records no ANYsolver product imports. No CI equivalence, installed product
verification or external-thread qualification is claimed. The numerical slot
was released.

The concrete next action is root review of `prepared-v2/released.inp` and its
bound model, then a separately authorized one-case CCX smoke using the command
above and full saved execution binding. Inspect actual complete outputs and
reported residuals/work/cuts/director-shear fields before deciding whether this
reference route is usable. This does not authorize native response comparison,
convergence, a new Mz/Fy route, a qualification campaign or scientific acceptance.

### First pinned external smoke and RF interpretation

The separately authorized exact V2 deck completed one CCX 2.23 linear increment
at time 1, with zero process exit, explicit Job finished and empty stderr. No
external retry occurred. Raw root RF differs from recovered actual support
covectors by 47.5048455065 N. This difference is retained, not forced to zero.
Independent saved-binary inspection found RF matches assembled internal root
covectors to about 1.0093e-11 N. At root node 8, internal gx is 3.0239959220 N,
interface exerted Fx is -47.5048455065 N, and support Fx is 50.5288414285 N.
Thus this specimen's output must distinguish internal RF from support after
interface bookkeeping. This is executable-bound empirical evidence, not a
manual-established general MPC exception or equality oracle.

Original parsed output/source bindings remain immutable. The parser now reports
raw root RF, root internal covectors and both differences explicitly, alongside
recovered support loads. A fresh affected offline check reuses the saved exact
smoke, without external execution or revised mechanical criteria.

### Authorized exact smoke: completed, development evidence only

State: **verified bounded development reference mechanism/output/action route**.
Root separately authorized one smoke of the exact repaired V2 deck in fresh
`ccx-v1`; no retry, new field, parameter sweep or refinement occurred. Executable
and exact command/deck/model identities are bound in `execution-binding.json`.
CCX completed one static increment at time 1 and explicitly reported Job finished;
exit was zero and stderr empty. The existing deck's omitted minimum STATIC
increment caused a retained warning: CCX set that time increment minimum to
1e-6. No deck or physical input was changed after authorization.

The observed physical equations and work are:

| Observable | Actual value |
| --- | ---: |
| Maximum physical constraint component | 1.32348898008484e-22 |
| Free equilibrium unexplained force component | 2.7072744046563457e-10 N |
| Maximum total external wrench component | 2.3588597741763806e-10 (N / Nm components) |
| Applied force pairing | 4.791221835484095e-7 J |
| Internal pairing | 4.791221836001818e-7 J |
| Difference in internal/applied pairing | 5.17723e-17 J |
| Interface pairing | -2.9985297205047253e-24 J |
| Support pairing | 0 J |
| Raw RF vs internal root covectors | 1.0093259561472223e-11 N |
| Raw RF vs recovered physical support | 47.50484550651571 N (preserved) |

Recovered shell interface carries approximately +1 N Fz and -1 Nm My about
the common origin, opposite the bar interface; the support carries -1 N Fz and
+1 Nm My. Complete bar and plate cuts close with their respective loads/support.
At x=.5, independent director_x=-5.569970939717311e-7, while geometric normal_x
=-5.734162323081202e-7; actual reference-linear transverse shear_xz is
1.641913833638911e-8. The map therefore does not replace material director with
surface normal. The verified local normal-spin and director-work controls remain
applicable to the unchanged physical rows; no normal-torque load response is
inferred from this single transverse-force case.

Original CCX/parsed records remain immutable. Final parser bookkeeping exposes
both root internal RF and support-after-interface differences explicitly.
Fifteen fresh affected offline controls pass, with fourteen unchanged controls
deselected (pytest 0.78 s; JUnit 0.781 s), zero failures/errors. This includes the
actual saved bound response, existing 1e-8/1e-9 development numerical checks,
strict parser provenance and a synthetic RF/interface bookkeeping discriminator.
No physical error tolerance, native comparison or accuracy score was introduced.
Original V1 preparation failure and V2 controls remain preserved.

CCX supervisor measured 0.2161962 s and sampled peak 2,035,712 bytes; affinity
`[0]`, explicit numerical/unresolved ceiling one, sampled maximum one. Stdout
reports one CPU for setup/stress/stiffness/spooles; requested CCX and numerical
environment settings are saved. That fast-run sample is not comprehensive peak
memory or library-thread qualification. The immutable inherited execution record
contains an OpenSees backend label; `resource-adjudication.json` explicitly
corrects the interpretation without rewriting it. Saved-output parsing measured
0.330119 s / 34,754,560 sampled bytes. Affected offline checks measured
1.314367 s / 92,737,536 sampled bytes, effective pools/Numba one and JIT disabled.
The shared numerical slot was released.

Current source SHA-256:
`7d3a388ba2ba900aa7e04170fc08057b6ead8d2d11d00d5f0c1de3cf5240bbee`;
current tests SHA-256:
`30aba09f2f12cd6581f16a04fdf048503248fb0164623c23dcc5c44603800110`.
V3 executed snapshots match these hashes. CCX input remains deck
`54d72909717c07a82bdd4bb70e87b5084a402e529e60ba1a4576b86d99c0b154`, model
`a22170179b6e257a47288ff825a3b69ad503e5e3c4a040fcd5f3b53933c86463`; its exact FRD is
`0df710ea4eaffed98aca66e47e8490ccac501961c65bb4294f482be1c5244ff8`.
Final prose updates postdate the code/input/test bindings; they are not portrayed
as executed inputs. Full manifest and both parsed versions live in the same
owned raw directory. No new CCX execution is authorized by this outcome.

The route is usable for **development reference construction and physical work
bookkeeping**. Its five strong collocated stations and resolved continuum bodies
still differ from native weak BL5 and retained section kinematics. Matching
continuous/discrete measures/body assumptions and independent convergence remain
required before response comparison or physical acceptance. No formal F03,
scientific/different-family acceptance or qualification obligation is closed.

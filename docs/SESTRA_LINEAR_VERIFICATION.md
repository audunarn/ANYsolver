# Linear-static development comparisons with SESTRA

## Ordered plate, flatbar and combined comparisons

`scripts/run_sestra_three_cases.py` prepares a sequential diagnostic regime from
the retained 400-Q4 / 20-BEAS15 FEM (SHA256
`44f32e22475cfddcf2a67a855ca18b66acd234d4abb7b7c28dcc898f0ff23d6d`).
It refuses a changed live model. All decks use the public ANYfileIO writer,
ASCII and single CRLF; every source/result has explicit identity and case binding.

1. **Plate:** the same 2 × 2 m, 20 mm clamped-y0 plate, all 400 pressure loads,
   with beams removed. No mesh or material change.
2. **Flatbar:** the same upright FB100x10 section and 20-segment, 2 m centerline
   at x=1, z=-0.0500000007 m; root fully clamped, centroid tip Fz=-1000 N.
   Its physical nodes lie on the centroid, so the attachment eccentricity map
   is absent. This isolates the beam's stiffness and recovery.
   Admission independently checks nominal 100 mm height, 10 mm thickness,
   area and both inertias within float32 serialization precision, and requires
   effective local-z to be global+Z before using the analytical oracle.
3. **Combined:** the original plate, beam section/orientation and global GECCEN
   attachment offsets, with the original pressure loading.

The primary bending-sensitive observable is **all global nodal translations**,
with 1e-8 m absolute plus 0.001 relative tolerance for every UX/UY/UZ component.
Rotations have different units and are excluded explicitly. Beam cases also
require all six physical force/moment components at every reported station,
using the existing 0.001 N / 0.001 Nm absolute plus 0.001 relative criteria.
No plate case can pass merely because its mean membrane stress is zero.

Canonical RDNODRES/RDRESREF/RVNODDIS decoding follows DNV Results Interface
Format sections 2.1.1.13 and 2.1.1.37; ITRANS=0 and real results only, with
component permutations resolved and complete requested node coverage required.
The real conservative six-global-DOF BNLOAD contract follows Input Interface
Format section 5.2.21. Complex/transformed/ambiguous identities and new nodal
multi-case merging are refused. [DNV result definitions](https://sesam.dnv.com/download/windows64/sesam_results_interface_format.pdf)
and [input definitions](https://sesam.dnv.com/download/windows64/sesam_input_interface_format.pdf)
are the primary sources.

```powershell
$env:PYTHONPATH='C:/Github/ANYfileIO/src;C:/Github/ANYsolver/src'
$env:NUMBA_DISABLE_JIT='1'
$env:OMP_NUM_THREADS='1'; $env:OPENBLAS_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
& .venv/Scripts/python.exe scripts/run_sestra_three_cases.py prepare `
  reports/sestra_development/correction_parent/reference_snapshot/20261008_140714_T1.FEM `
  --output reports/sestra_development/my_fresh_cases
# After separately authorized sequential SESTRA runs provide each <case>_R1.SIF:
& .venv/Scripts/python.exe scripts/run_sestra_three_cases.py compare `
  reports/sestra_development/my_fresh_cases/suite.json `
  --output reports/sestra_development/my_fresh_comparison
```

Preparation and comparison launch no external applications. Each generated
control has full `ELOP 1,0,1`, `/dsf` staging metadata, RNAM FORMATTED and
case-specific prefix substitution. Existing suite evidence is never overwritten.
All three comparisons run in order for diagnosis; the suite passes only if
every case and its balance/oracle checks pass.

For an explicitly authorised reference run, use PowerShell 7 to stage each
generated deck in its own new working directory, substitute the prefix and run
the selected installed executable directly. The following keeps a 90-second
cumulative process-wall allocation and a maximum 30 seconds per case. Use a
fresh prepared suite: existing cached SIFs are refused, and logs remain in each
working directory. A zero process exit supplies reference data; comparison
still determines numerical success.

```powershell
$cases=(Resolve-Path reports/sestra_development/my_fresh_cases).Path
$exe='C:/Program Files/DNV/Sestra V10.20-00/Bin/sestra.exe'
$remaining=90.0
foreach($name in 'plate','flatbar','combined') {
  $source=Join-Path $cases $name
  $cache=Join-Path $source ($name+'_R1.SIF')
  if(Test-Path -LiteralPath $cache) { throw 'Reference already exists; prepare a fresh suite.' }
  $work=Join-Path 'C:/DNV/Workspaces' ('ANYsolver_SESTRA_'+$name+'_'+[guid]::NewGuid())
  New-Item -ItemType Directory -Path $work -ErrorAction Stop | Out-Null
  Copy-Item -LiteralPath (Join-Path $source ($name+'_T1.FEM')) -Destination $work
  $control=(Get-Content -LiteralPath (Join-Path $source 'sestra_control.inp') -Raw).Replace('{prefix}',$name+'_')
  [IO.File]::WriteAllText((Join-Path $work 'sestra.inp'),$control,[Text.Encoding]::ASCII)
  $ceiling=[math]::Min(30.0,$remaining)
  if($ceiling -le 0) { throw 'Cumulative reference allocation consumed.' }
  $clock=[Diagnostics.Stopwatch]::StartNew()
  $process=Start-Process -FilePath $exe -ArgumentList '/dsf' -WorkingDirectory $work `
    -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $work 'stdout.log') `
    -RedirectStandardError (Join-Path $work 'stderr.log')
  $completed=$process.WaitForExit([int]($ceiling*1000))
  if(-not $completed) { $process.Kill($true); $process.WaitForExit() }
  $clock.Stop(); $remaining-=$clock.Elapsed.TotalSeconds
  @{argv=@($exe,'/dsf');cwd=$work;wall_seconds=$clock.Elapsed.TotalSeconds;remaining_seconds=$remaining;timeout=(-not $completed);exit_code=$process.ExitCode} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $work 'execution.json')
  Get-ChildItem -LiteralPath $work -File | Get-FileHash -Algorithm SHA256 |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $work 'file_hashes.json')
  if(-not $completed -or $process.ExitCode -ne 0) { throw "Reference process failed; retain $work." }
  Copy-Item -LiteralPath (Join-Path $work ($name+'_R1.SIF')) -Destination $cache -ErrorAction Stop
}
```

Select the executable explicitly for the authorised environment; this example
uses the V10.20 binary that produced the retained three-case evidence. Do not
reuse this example as authority for additional runs after an allocation is
consumed. Its fresh files, `.MLG`/`.LIS`, hashes and process logs should accompany
the numerical comparison reports.

The first actual sequential SESTRA10.20 comparison produced:

| Case | Complete comparison | Outcome |
| --- | --- | --- |
| Plate | 1,323 translation components | Failed: 414 components |
| Flatbar | 63 translations + 360 beam station components | Passed, including analytical tip displacement |
| Combined | 1,323 translations + 360 beam station components | Failed: 495 translations + 167 beam components |

The isolated Timoshenko oracle includes bending and shear,
`uz=-FL³/(3 E Iy)-FL/(kz G A)` (about -15.275 mm). Native independent load/reaction
balance is checked at 1e-6 N/Nm absolute plus 1e-8 relative. These outcomes
separate standalone beam agreement from the plate/attachment disagreement;
they establish no qualification or broader formulation equivalence. Actual
reference execution and full source-based comparison evidence are retained in
`reports/sestra_development/three_case_parent/`, with focused worker checks in
`reports/sestra_development/three_case_worker/`.

The source-only mixed-model profile `mixed_q4_beas15_constant_pressure` is under
development. Canonical ANYfileIO maps internal node/element IDs to external
identities, retains global GECCEN eccentricities and reads BEAS15 force results
at reported global stations. Native beams apply linear rigid-arm displacement
maps and their exact transpose force map; nonlinear, dynamic and geometric
stiffness routes with nonzero offsets refuse execution.

Reported beam forces follow DNV Results Interface Format Figure 2.2. The reader
converts signs `(1,-1,1,1,-1,1)` before applying the reported rotation, producing
physical global forces/moments on the positive local-x cut. Comparison criteria
are 0.001 N / 0.001 Nm absolute plus 0.001 relative, with all stations and six
components required. Shell criteria stay 1 Pa plus 0.001 relative. Independent
double-precision axial, both bending-plane, torsion and rigid-arm controls are
separate from those development thresholds. A full supplied mixed-model pass
requires the integrated comparison and balance checks.

The retained 441-node / 400-Q4 / 20-BEAS15 user model now runs through the
integrated cached comparison. Its Q4s are planar convex distorted elements.
RDIELCOR/RDPOINTS resolve exact natural recovery locations and symmetric
top/bottom pairs; native recovery samples the unchanged E4-PL stationary field
at those locations. The compared tensor contains only in-plane membrane
components. Mindlin transverse shear is excluded explicitly. Coordinates are
unchanged; physical station serialization is checked against shape functions.

The current comparison **fails** the fixed criteria: 1,052 shell and 167 beam
component failures out of 2,400 shell and 360 beam station components. Independent
polygon pressure resultants and native reactions balance to about 5.3e-8 N/Nm.
The implementation and balance checks do not establish numerical equivalence.
Source ANYfileIO routing is required; the installed dependency is unchanged.

The immutable local comparison manifest and full evidence are under
`reports/sestra_development/mixed_model_worker/`. To replay that retained pair:

```powershell
$env:PYTHONPATH='C:/Github/ANYfileIO/src;C:/Github/ANYsolver/src'
$env:NUMBA_DISABLE_JIT='1'
$env:OMP_NUM_THREADS='1'; $env:OPENBLAS_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
& .venv/Scripts/python.exe scripts/run_sestra_verification.py `
  reports/sestra_development/mixed_model_worker/snapshot_manifest.json `
  --mode compare --output-root reports/sestra_development/local_replay
```

This creates fresh comparison evidence and launches no external solver. Live
user inputs changed during development; the retained pair is identified by
exact FEM/SIF hashes, rather than assuming later files represent that case.

The primary workflow imports the same formatted FEM into ANYsolver, solves its
admitted linear-static case, and compares the resulting global membrane tensor
with an explicitly selected result case in a formatted SESTRA SIF. Parsing is
owned by ANYfileio; this harness does not create a second SESAM syntax parser.

This is development evidence, not solver qualification or release acceptance.
The first admitted slice is homogeneous isotropic, positive counterclockwise
axis-aligned rectangular Q4 shells in one XY plane, with one nonzero in-plane
BGRAV case, explicit material/thickness, zero binary supports, and every node's
out-of-plane translation and rotations restrained. Missing material values,
zero Poisson ratio currently lost by the interchange reader, dependencies,
transforms, offsets, other loads, spatial pressure averaging, multiple cases,
and unknown semantics are refused. No missing values are replaced by zero.
The built native material, thickness and gravity must match source semantics.
The legacy BGRAV diagnostic is preserved after checking the actual mapping;
other physical warnings cause refusal. Established SIF result metadata records
are preserved and reported without inventing unsupported observables.
RVSTRESS values are checked for IDs, case, finite payload and Q4 layout.

The observable `global_shell_membrane_arithmetic_station_mean` contains all six
components SXX/SYY/SZZ/SXY/SYZ/SZX in Pa. Native recovery takes the arithmetic
mean over stations of half the sum of top and bottom global tensors. ANYfileio
averages the corresponding SIF membrane samples. This compares element averages;
it does not establish agreement at individual sampling stations, bending,
beam stress, displacement or reaction results. Rectangular constant-Jacobian
elements restrict the first development metric. Nonuniform fields still need
separate pointwise and mesh-convergence evidence before stronger claims.

From the repository root:

```powershell
.venv/Scripts/python.exe scripts/generate_sestra_verification_fem.py examples/sestra_verification/hanging_shell.FEM --overwrite
.venv/Scripts/python.exe scripts/run_sestra_verification.py examples/sestra_verification/hanging_shell.json --mode prepare
.venv/Scripts/python.exe scripts/run_sestra_verification.py examples/sestra_verification/hanging_shell.json --mode compare
.venv/Scripts/python.exe scripts/run_sestra_verification.py examples/sestra_verification/hanging_shell.json --mode execute
```

The direct generator uses the public ANYfileio raw document writer and does not
need GeniE. Its complete record layouts follow the successful user-provided
GeniE FEM: IDENT four fields, UNITS five, MISOSEL eight, GNODE four per node,
GELMNT1 connectivity continuation, GELREF1 twelve fields, TDLOAD case metadata
and a name, and IEND four zero fields. It writes ASCII with single CRLF lines.
Canonical CRLF text must never be passed through Windows default newline
translation: that creates doubled CR and drops continuation data in SESTRA.
External execution checks complete layouts and newline bytes before launching.
BNBCD remains 0 free / 1 fixed zero; no boundary-flag inversion was made.

Preparation checks admission and writes `not_executed`; it launches neither
solver. Comparison runs ANYsolver and reads an existing SIF. Set `reference_sif`
and `reference_fem_sha256` to the reference file and the SHA256 of its source FEM;
this binding is user-supplied provenance, not proof of a new SESTRA execution.
The example deliberately has no reference SIF, so compare refuses until supplied.
Its absolute and relative tolerances are declared development controls, not
qualified tolerances. Acceptance is `abs(native-reference) <= absolute_pa +
relative*abs(reference)` for every requested component and exact element ID.
Node coordinates, connectivity, material, thickness and element references must
match; any reference support/load records present must also match.
SESTRA's demonstrated single-precision property serialization is normalized
only for E, nu, density and thickness at float32 epsilon relative precision,
zero absolute tolerance and exact zeros. Both values and this metadata precision
are recorded. A BGRAV eighth trailing zero may be removed; its first seven fields
stay exact and load-record order may differ. Stress acceptance tolerances, IDs,
topology and support flags receive no precision waiver.

Execution is opt-in. The example profile uses the user-specified installed
`C:/Program Files/DNV/Sestra V11.1-00/Bin/sestra.exe` with `/dsf`. The generic
`formatted_linear.inp` supplied with the example derives from the user-provided
formatted profile; its numerical settings have not been validated by SESTRA.
Review or supply a formatted linear-static template in `execution.control_template`
and its `prefix_token`. The harness stages it as `sestra.inp`, substitutes only
that token, copies the exact FEM to `<prefix>T1.FEM`, and expects
`<prefix>R1.SIF`. INAM selects the prefix; LNAM/RNAM must request FORMATTED
output. The control file is user-supplied because command/settings are part of
the reference model. No GeniE launch is required. If new model authoring needs
GeniE, [DNV's official GeniE utilities](https://sesam.dnv.com/genie_utils/) provide
examples; the separately confirmed GenieR.exe automation is optional preparation.
The user-confirmed optional argv is
`["C:/Program Files/DNV/GeniE V9.1-00/Program/GenieR.exe", "genie", "/new", "/com=" + absolute_js_path, "/licenses=CurvedGeometry,FrameCodeCheck,PlateCodeCheck"]`.
Use a subprocess working directory for a separately authorised authoring run.
The verification runner does not launch GeniE.

Each call creates a fresh UUID directory under `reports/sestra_development`.
Execution uses argv with `shell=False`, a new working directory, explicit
timeout and process-tree cleanup. Files, including `.MLG`/`.LIS`, stdout/stderr,
executable/input/control/output hashes, loaded numerical/parser source hashes,
dependency versions, runtime pools, elapsed time and budget disposition remain
there. A nonzero exit, timeout, empty/missing output or incomplete result coverage
cannot pass. A zero exit alone is insufficient: full SIF validation and numerical
comparison must succeed. Imported evidence and fresh execution are distinct.
Reports use `passed`, `failed`, `unsupported` or `not_executed` and always mark
`qualification: false`.

The supplied small shell has unit height, density 7850 kg/m3 and gravity
10 m/s2. Force balance gives the independent mean axial stress 39250 Pa;
the tests check this before comparison with a clearly synthetic parser fixture.
Synthetic SIFs and mock processes establish tooling behavior only. Initial
actual attempts retained licensing failures, followed by an input-processing
failure. Correcting only doubled CR to single CRLF made the latter SESTRA run
complete successfully; its boundary count then matched the native count.
The newly generated complete nu=.3 fixture also completed in SESTRA V10.20.
These successful processes establish input viability, not numerical agreement.
The retained real SIF revealed single-precision property serialization/padding,
now handled by the explicit normalization above, and a local-frame discrepancy
in the previous canonical reader. The separately authorised source ANYfileIO
repair resolves RVSTRESS references through RDPOINTS and RDSTRESS, using the
reported global or common local-to-global frame rather than guessing from an
input edge. The retained real case now passes all six averaged membrane
components at the unchanged manifest tolerances with that repaired source.
Installed ANYfileIO was not updated: select the source checkout explicitly when
reproducing this development evidence.

```powershell
$env:PYTHONPATH = 'C:/Github/ANYfileIO/src;C:/Github/ANYsolver/src'
$env:NUMBA_DISABLE_JIT = '1'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
```

The reported-frame contract follows [DNV's Results Interface Format,
sections 2.1.1.15, 2.1.1.23 and 2.1.1.47](https://sesam.dnv.com/download/windows64/sesam_results_interface_format.pdf).
The source reader validates descriptor/component identities, real-case and
point counts, finite values, column-major rotations, orthonormal/right-handed
frames (1e-6 matrix validation precision), and complete three-component flat
shell tensors. It transforms each tensor before averaging. Reported layered,
complex, curved/per-point-frame and unsupported component layouts refuse;
there is no geometry fallback when reported descriptors are present. Legacy
files without them retain their previous input/geometry-frame route. Recorded
frame provenance exposes the selected descriptor, point count and matrix.
The public reader selects internal result case IRES; the admitted native wrapper
also checks reported external case IERES against its sole source case, preventing
different external cases from passing through a reused internal result number.
Preserve initial failures and successful output; no tolerance or physics change
can hide a frame error.
The synthetic orientation regression explicitly encodes local SIGXX to produce
GLOBAL SYY: for no-transform SESAM shells, local y follows the first edge and
local x is local y crossed with the normal. Native recovery already returns the
global tensor; the comparison never compares local components directly.

| Phase | Cases and independent controls | Current tooling / acceptance gap |
|---|---|---|
| 1 | Axial shell self weight, analytical force balance | Native Q4 route and retained real SESTRA averaged-membrane comparison pass with repaired source ANYfileIO; no pointwise or qualification claim |
| 2 | Beam axial, bending, torsion; elementary analytical solutions | Tight native controls implemented; actual isolated upright flatbar passes translations and all force/moment stations |
| 3 | Shell membrane patches, shell bending, pressure, point loads, supports | Constant Q4 pressure and global real BNLOAD routes implemented; plate bending translation comparison fails fixed criteria |
| 4 | Rotated frames, non-SI inputs, mixed element orientations | Reported global/common result frames tested; verification still refuses non-SI or transformed nodal input/results |
| 5 | Multiple independent load cases and combinations | Verification profiles refuse multi-case; legacy pressure aggregation is outside acceptance; new nodal import refuses merging |
| 6 | Mesh refinement of matched physical models | Planned; compare discretization and sampling effects separately |
| 7 | Stiffened representative structures, mixed beams/shells | Implemented bounded Q4/BEAS15 slice; full model comparison fails fixed criteria; no qualification |

Promote phases only with physically matched inputs, independent controls,
documented tolerances and retained failed cases. Broader qualification has its
own repository gates and execution authority; these development reports do not
populate canonical release artifacts.

## Historical input failure and its correction (2026-10-08)

The earlier V10.20 run acquired a license but failed with `invalid vector
subscript`; its logs remain in
`C:/DNV/Workspaces/ANYsolver_SESTRA_v10_20_20261008_185f6386`.
Replacing doubled CRLF with single CRLF alone made the subsequent run complete
and its support count agree with native20. The boundary-code reversal speculation
was withdrawn: DNV BNBCD code1 means fixed zero. Corrected decks and subsequent
successful reference runs supersede that historical unresolved finding. License,
newline and numerical-comparison failures remain separate retained evidence.
# Discriminating plate and attachment diagnostics

`scripts/run_sestra_deep_diagnostics.py prepare <immutable-original-FEM> --output <fresh-directory>` stages six explicit diagnostic pairs: regular 20×20 plate thin/thick, ν=0 cylindrical strip thin/thick, and regular combined plate with zero/original eccentricity using thick-shell controls. Coordinates are explicitly generated with float32-compatible serialization; the original distorted source is retained unchanged. Manifests bind FEM and control hashes and retain the established translation and force criteria.

SESTRA `ELOP` THCK is the second five-column field (columns 26–30): THCK=0 selects FQUS thin shells; THCK=1 replaces them with THQS thick shells. The third value in the earlier template does not select thick shells. The parent-controlled original-geometry experiment reduced plate peak discrepancy from about 0.122% to 0.0092%, and combined peak discrepancy from 0.525% to 0.0128%. Four plate translation components, 72 combined translation components and 50 combined beam components still failed the unchanged criteria in those retained thick-reference comparisons. These findings support a reference-formulation mismatch as the main earlier difference; they do not establish full agreement or qualification.

After separately authorised external execution, `compare <suite.json> --output <fresh-directory>` compares complete nodal translations and beam station forces. `probe <three-case-suite.json> --output <fresh-directory>` additionally applies the same native beam stiffness and physical recovery to native and SESTRA six-DOF nodal fields. Optional `additional_references` maps case IDs to labelled cached SIF paths so thin/thick cross-recovery reuses one native solve. This separates nodal-solution differences from kinematics/stiffness/recovery correspondence without selecting signs by agreement. Canonical readers expose translations in metres and rotations in radians; malformed/incomplete, transformed or complex nodal results are refused.

The ν=0 strip includes explicit UX constraints and an independent cylindrical cantilever pressure oracle: `w_tip = -p L^4/(8D) - p L^2/(2 k G h)`, `D=E h^3/12`, `k=5/6`. Its thin-reference counterpart omits the shear term physically. The oracle is reported separately from the fixed native/reference development criteria. No core mechanics or acceptance tolerances change in this diagnostic milestone.

The actual regular-mesh experiment retained 414 translation failures for thin plate and four for thick plate. The thick ν=0 strip passed every translation component; native tip displacement matched the independent shear-deformable continuum oracle to 2.35e-10 relative error. Zero-offset combined thick retained four translation and 15 beam-component failures; eccentric combined thick retained 72 translation and 50 beam-component failures. Applying native recovery to the corresponding SESTRA nodal fields reduced beam failures to seven and three respectively. The original thin coupled model reduced 167 beam failures to three under that same-field probe; the thick original reduced 50 to eight. The standalone beam positive control itself retained one same-field failure, so formatted displacement precision and cancellation need accounting before interpreting the remaining small recovery differences. These are reported failures, not waived criteria.

The zero-offset combined model is a nonphysical centric attachment control. Original −50 mm eccentricity aligns the 100 mm bar top with the shell midsurface. A bar immediately beneath a 20 mm plate would instead have centroid −60 mm relative to its midsurface. Neither geometry is silently substituted for the original comparison.

`prepare-stage2` stages the adopted thick 40×40 plate, original-offset 40×40 combined model, and distinct source-driven underplate geometry. The 40×40 plate retained six translation failures; peak difference fell to about 0.0026%. The 40×40 combined retained 51 translation and 73 beam-component failures. Underplate geometry retained 72 translation and 48 beam failures. Input/source offset mechanics remain unchanged; deep-only identity checks allow documented float32 result serialization while retaining exact vector IDs, signs and zero components.

Beam shear is not mesh converged: the thick-reference root Fz changed from −665.216 N at 20 segments to −927.049 N at 40. At the same physical right-hand cuts y=0.5/1/1.5 m it changed from −675.990/−470.855/−233.402 N to −1057.604/−746.540/−380.639 N. Native shear showed similar changes. Small tip-displacement changes therefore do not validate local-force convergence. No further external refinement or mechanism claim follows from these two meshes.

Same-field precision diagnostics propagate independent assumed float32 rounding and observed nine-significant-digit text bounds through the absolute linear beam recovery operator. They retain fixed development pass/fail separately and exclude stiffness serialization and arithmetic error. All inspected nodal components were consistent with this representation, but some recovered components exceeded the assumed bound; the estimate is not a complete explanation or an acceptance waiver.

The strip oracle is a **tip** oracle: native interior deflections differ from the continuum solution. Native-only refinement from 20 to 40 longitudinal cells reduced errors at y=0.5/1/1.5 m from 4.464/5.952/4.464 µm to 1.116/1.488/1.116 µm, approximately fourfold. Tip coincidence alone is not whole-field correctness. The thin strip excess tip deflection is consistent with a nodal-load quadrature correction `p L² dy²/(24D)`; this is a diagnostic hypothesis, not a statement about DNV implementation.
# Automatic combined-structure benchmarks

`scripts/run_sestra_structure_benchmarks.py prepare --output <fresh-directory>` creates nine complete, source/control-bound decks: three mesh levels for each of the following structures. `native <suite.json> --output <fresh-directory>` evaluates audited native models; `compare <suite.json> --output <fresh-directory>` consumes separately executed cached SIFs. No external executable is launched by these actions. Reports retain every nodal translation and beam station component, fixed criteria, source/runtime identity, balance, physical probe locations, and PNG/SVG model views.

- **Inclined rigid frame:** two joined 2 m members, from (0,0,0) through (1.2,0,1.6) to (1.2,2,1.6), with 4/8/16 elements per member, explicit local axes and an upright 100×10 mm section. The root fixes six DOFs; terminal global force is (0.2,−0.3,−1) N and moment (0,0.1,0) Nm. An independent Castigliano compliance integrates axial, biaxial bending, Saint-Venant torsion and Timoshenko shear energy from the terminal wrench and physical lever arms, using exact two-point quadrature. It shares no native stiffness/recovery calculation. The historical 1000-times-larger load case passed algebraic comparisons but produced metre-scale translations and radian-scale rotations; it is unsuitable as a physical small-displacement example and remains separate evidence.
- **Crossing stiffeners:** a 2×2 m, 20 mm plate with two intersecting upright flatbars, a shared crossing system node and centroid offset `−(plate thickness + bar height)/2`. Uniform −1000 Pa pressure and the full y=0 clamp are retained across 4×4/8×8/16×16 plate grids.
- **Right-angle folded plate:** XY and YZ faces, each 1×2 m, joined along their shared six-DOF fold line and fully clamped at y=0. Two exact global −500 N FZ forces act at fixed outer tip corners (1,2,0) and (0,2,1). Concentrated-load corner stresses can be singular; complete translations, global energy and predefined physical displacement probes are primary. The finest model contains 256 shells.

Shell controls use THCK=1. Native admission audits finite coordinates, source/effective material and section properties, support and sole-case load coverage, planar convex Q4 normals, explicit right-handed beam axes and exact effective global rigid-arm offsets. Canonical readers own result numbering and frames; transformed or unsupported result layouts are refused. The suite is development evidence for these particular models, not general correctness or qualification.

Current execution uses the source ANYfileIO checkout via `PYTHONPATH=C:/Github/ANYfileIO/src;C:/Github/ANYsolver/src`, one numerical thread and `NUMBA_DISABLE_JIT=1`; reports retain actual loaded paths and observed pools. The installed ANYfileIO package has not been updated by this work. Full 16-field GBEAMG records and separate TDLOAD `LC1` continuation are generated through its public raw-document writer. An earlier 12-field geometry record was rejected by actual SESTRA and remains historical failed evidence.

The measured shell-family comparisons retained failures at every mesh level. Crossing-stiffener translations failed 36/50/72 components and beam forces failed 92/174/315 components at levels 4/8/16. Native/reference load-work energies were 2.72973/2.73117, 2.74542/2.74682 and 2.75683/2.75798 J. Folded translations failed 53/91/244 components; maximum UZ errors fell from 10.726 to 2.277 to 0.407 µm and energy differences narrowed, but complete translation acceptance still failed. Counts apply to different node populations and cannot establish convergence by themselves. `convergence.json` retains energies, signed changes at the same physical probe locations and per-axis errors; local-force and singular-corner convergence are not inferred from displacement trends.

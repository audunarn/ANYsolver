# B2 nodal-footprint reference modes — experimental delivery

1 October 2026, base integration `a7ff866c`, unchanged package version 0.4.7.
The existing public B2/Q4 owner now returns supported virgin reference modes
for explicitly selected-node rigid footprints, optionally with finite-vertex
points. It reuses compiled physical K/M, actual C/T and the existing sparse
descriptor solver. Multipliers and shell drilling variables receive no invented
inertia; no static condensation or tangent symmetrization is introduced.

The distinct typed result records the footprint law and all constraint
multipliers with immutable source-row/frame provenance. Inherited point
multiplier fields contain only actual point rows. Footprint rows are global;
point translations use the shell reference frame and rotational gaps the beam
reference frame. Multipliers remain work-conjugate covectors, not display-ready
global moments.

Admission requires explicit physical beam and shell mass, coordinate supports
and zero prescribed offset. A footprint-only bounded rigid-field audit detects
all six physical common rigid motions through actual fixed coordinate rows.
Streaming QR uses at most 12x6 temporaries; the final SVD is 6x6. It rejects
free-free/under-supported requests even when a rounded static factor reports
success. This necessary support check is not a proof of absence of every
internal mechanism. Existing empty-footprint behavior and result types remain
unchanged. Numerical failures/cancellation publish no partial pairs and preserve
the independent reusable static factor.

## Checks and actual artifacts

One isolated wheel SHA256
`27660d7357eedf36a2d96a73282b9ede974fd3219903b2492d32553c118f47ec`
was built after source freeze. All 391 Python modules match current source,
wheel and installed site byte-for-byte; 210 actual imported modules resolve to
the isolated site. Python 3.14, NumPy 2.4.6, SciPy 1.17.1, Numba 0.65.1,
pytest 9.0.3, ANYmaterial 0.2.0, ANYmesher 0.5.0 and ANYfileio 0.3.2 are recorded.
Effective numerical pools/Numba threads are one and JIT is disabled.

| Check | Observed result | Supervised time / sampled tree memory |
|---|---|---|
| Initial focused source slice | 40 passed, before frame correction/additional support guard | 8.49s pytest; original record retained |
| Frame-corrected source slice | 18 passed | 6.22s pytest; original record retained |
| Final support-guard source slice | 21 passed | 7.505s / 178,528,256B |
| Installed new modes, existing point modes and footprint static modules | 76 passed, zero failure/error/skip | 6.584s / 175,124,480B; pytest 4.25s |
| Installed public headless example | Completed; three requested pairs | 1.829s / 145,223,680B |

Installed runs use a fail-closed owned-process supervisor, 180 seconds/1 GiB,
outside the source checkout. The example frequencies are 0.2871307055,
0.5424409864 and 0.7413875729 Hz for its explicitly illustrative SI geometry and
material values. Equation/constraint residuals are below 6e-16. The example
checks unchanged static displacements across modal work, with one modal factor
and the original one static factor. These frequencies are development
observations, not an engineering frequency reference.

The test oracle scatters constraints independently and checks bounded QZ and
constraint-reduction spectra, actual eigen-equations, physical mass and frame
work, equivalent coordinate scaling, mixed points/multiple footprints, missing
mass, MPC/nonzero-offset negatives, rigid-support counterexamples, cancellation
and classified failures. Its element/mass kernels are shared; it is not an
independent external formulation reference. An initial wrong-selector collection
failure remains retained. Subsequent runs do not erase it.

The [independent Read review](review.md) found no remaining blocker for this
limited capability, including the corrected support admission. Optional local
and Mistral workers were unavailable after bounded attempts earlier in this
task; the separate implementation/review workers use OpenAI. No different-model
family independence is claimed. Root inspected source scope, recorded outcomes,
runtime settings and installed identities rather than accepting worker claims
alone. No broad previously passed campaign was repeated.

## Decision and remaining boundary

Retain the implementation as experimental, `production_qualified=False`,
normal-spin locked, mechanical qualification incomplete. It does not qualify a
continuous-area weld, distributing footprint, drilling-independent physical
torque transfer, free-free/prestressed modes, B2 buckling, nonlinear B2, full
spectral completeness or aggregate F07/F12/G4B/G6 acceptance. BL5/F03 and the
matched engineering connection decision remain open. No scientific tolerance,
formal execution authority, default, release version or historical checkpoint
meaning changes. No overall development speedup is claimed.

[Raw archive identity](raw-v1-identity.json) binds installed wheel, runner,
source manifest, fixtures, source records (including failed collection), raw
XML/logs, effective imports/settings and resource observations. The previous
live note is archived byte-for-byte before shortening; historical records and
protected F03 source remain unchanged. No communication with the other task.

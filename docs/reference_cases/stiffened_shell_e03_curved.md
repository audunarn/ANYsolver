# E03 polygonal curved roof: profile-specific source candidate

State: **IMPLEMENTED_UNVERIFIED / UNEXECUTED**. No imports, source tests, native
solve, build/install or CalculiX runs have been performed for this candidate.
This is a named partial E03 implementation, not E03 acceptance or a reduction of
the mandatory GE+B2 programme. Root adopted the profile-specific tooling delta;
external coupling acceptance and numerical scoring remain separate decisions.

The owned implementation is `scripts/r8_e03_curved_reference.py` (case, work map,
independent deck, parser and candidate comparisons),
`scripts/r8_e03_native_reference.py` (existing public profile adapters) and
`tests/test_stiffened_shell_e03_reference.py` (prepared source controls).

## Declared fixture and model distinction

The nominal cylindrical roof has length 0.508 m, radius 2.540 m, half-angle
0.1 rad and shell thickness 0.0127 m. Two straight longitudinal rectangular ribs
are at angles -0.05 and +0.05 rad, with width 0.00635 m and height 0.0254 m.
Both use isotropic E=3.10275e9 Pa, nu=0.3. Centroidal properties are A=bh,
Iy=bh^3/12, Iz=hb^3/12 and the declared Saint-Venant rectangular odd-series J
through term 511; the native shear factors are 5/6. No effective shell flange or
parallel-axis stiffness is added to the beam section. The signed centroid offset
is ±(t+h)/2 along the selected facet normal, applied once through the connection.
Negative eccentricity is a mirrored rib on the other shell side.

The three predetermined (axial, circumferential, through-thickness/cross-section)
division levels are (4,6,1), (8,10,2), (16,18,3). Circumferential counts retain rib
facet-centre angles ±0.05 exactly. The physical target is cylindrical, but each
level is a polygonal chord approximation: Cartesian facet/rib reference positions
change under refinement. Each native/reference pair shares that level's actual
polygonal geometry; different levels have different case identities.

All root translations/rotations are restrained in the native definitions and all
solid-root translations are restrained in the independent reference. Each rib
tip receives the same dead global force (0,0,-0.5) N at its centroid, no moment.
No pressure, follower load, body load, yielding, imperfection or spectra is added.
GE density must be supplied explicitly; its inertia record is physical static
bookkeeping here and confers no spectral admission.

B2 uses one physical straight member per axial interval and a point at station
0.5 to the selected coarse Q4's equal-vertex translation-fitted pose. GE splits
each facet into four planar Q4s and uses its existing full nodal pose at that same
coarse-facet centre and B3 midpoint. These occupy the same physical port positions
but have distinct shell trace authorities. They are not declared the same law.

## Independent B2 fitted-port work candidate

For four noncollinear vertices x_i, let x0=mean(x_i), rho_i=x_i-x0,
H_i=[I,-[rho_i]x], P=(H^T H)^-1 H^T. Then q=P u is the equal-weight
translation-defined mean pose and P H=I. Only this six-role projection enters
the connection; local deformations in ker(P) remain admissible. No solid patch
or section is made rigid by these equations.

Let r=x_b-x_s and E(r)=[[I,-[r]x],[0,I]]. The independent world constraint is
c=P_b u_b-E(r)P_s u_s. Its multiplier lambda=(f,m) is work-conjugate at the beam
centroid. Nodal actions are f_b=P_b^T lambda and f_s=-P_s^T E(r)^T lambda.
Thus lambda^T c equals the actual nodal virtual work. The physical shell-origin
wrench is (-f,-m-r×f), balancing the beam wrench (f,m) about a common origin.

The solid reference uses independent C3D20R roof and rib meshes, connected only
through these six affine fit equations at declared stations. It uses neither
shared beam/shell knots, nominal DOF4–6 identification, rigidified patches,
continuous welded ribs nor penalty springs. Beam-section vertices and shell
mid-plane support vertices are explicit source identities. Equation row reduction
only selects unique beam-side dependent DOFs for CCX; it preserves the six-row
constraint nullspace. The raw source and actual rounded deck rows are retained.

For the native B2 law, the world rows are transformed by the reference material
frames: C_native=T C_world with T=diag(R_s0^T,R_b0^T), and
lambda_world=T^T lambda_native. Prepared local tests check this equation and dual
virtual work for both eccentric signs. Raw native multiplier components are not
reported as spatial wrenches. These controls are unrun. Root must inspect the
actual row-map evidence before adopting reference comparisons.

The continuum solid-to-shell/beam approximation, section constitutive accuracy,
shear and thickness resolution are separate unqualified questions. Exact fitted
port work does not establish equal bulk stiffness or converged physical accuracy.

## GE obstruction and required next action

GE permits independent shell-node rotations. B2 shell P uses only translations;
its shell rotational columns are zero. A native field with zero shell-vertex
translations and nonzero shell-node rotation can do GE point rotational work
while its translation-fitted shell rotation is zero. Likewise a CCX rigid marker
group would require marker translations to realize that rotation and would add
constraints absent from GE. Shared knots or a continuous solid weld do not cure
this difference. An independent physical shell rotation/drill trace and its
conjugate moment work, including any relevant stiffness completion, are missing.

GE definition construction remains available for later development, but GE
external scoring is explicitly refused. Next action is an adopted independent
rotation/director work map or a derived, disclosed restriction with nontrivial
physical connection work; the mandatory remaining GE E03 scope stays open.

## Preparation, execution and interpretation

`build_case(level, offset_sign)` returns the fixed primitive case and identity.
`build_deck(case)` returns an ASCII deck and primitive provenance. It launches
no solver. `b2_definition(case)` returns the existing public B2 definition and
load; `ge_definition(case, density_kg_m3=...)` returns the existing public GE
definition and dead actions. Only `execute_b2(case)` compiles/solves, and requires
separately granted numerical authority from the caller. Existing owner failures
remain explicit and the owner is closed after detached result extraction.

CCX numeric fields are bounded to 20 characters by choosing the highest available
significant precision, never slicing tokens. Full source coordinates/rows and
actual rounded coordinates/rows are separate metadata. Prepared controls check
the actual deck's rigid-field compatibility and field widths. The output requests
reuse the previously executed pinned CCX2.23 spelling
`*NODE OUTPUT,DOUBLE,NSET=PHYSICAL` for U and
`*NODE OUTPUT,DOUBLE,NSET=ROOT` for RF. The new E03 deck is unexecuted.

After fresh authority and root case/control registration, the existing resource
supervisor must capture the exact deck, CCX binary/version/hash, exit/timeout,
precise process-wall duration, actual effective settings, complete stdout/stderr,
STA and DOUBLE FRD bytes. `parse_result` requires matching hashes and a completed
single unit-time increment; it rejects diagnostics, incomplete data, mismatched
geometry, compatibility failures and nonpositive work. The existing strict DOUBLE
reader validates C3D20R identities, counts, dataset ordering and precision.
Parser-positive fixtures in the source tests are synthetic and are not physical
equilibrium solutions or executed references.

Every retained process-receipt field, including extras, must be a finite JSON
primitive: objects with string keys, lists, strings, numbers, booleans or null.
Receipt bounds are 4,096 value nodes, depth 16, 4,096 characters per string,
256 characters per key, integer magnitude at most 10^20 and 65,536 serialized
ASCII bytes. Cycles, non-JSON values and nonfinite extras are refused. The
validated receipt is detached recursively through a JSON round-trip, so later
caller or record mutation cannot change the other copy.

Both native and external balance use the same physical measure:
max(max|F_balance|/Fref, max|M_balance|/(Fref Lref)) ≤ 1e-8,
where Fref=sum of the two tip-force magnitudes=1 N and Lref=0.508 m.
There is no mixed-unit raw residual bound. The comparison denominator/near-zero
floors are separately fixed at 1e-12 m, 1e-12 J, 1e-9 N and 1e-10 N m.

The prepared B2 question compares applied-force work, physical tip translations
at declared sections and the common-origin root force/moment. The fixed relative
limit is 1%, with the stated dimensional floors. Three exact declared levels and
the last-pair work movement for each route are required before even a candidate
convergence result; no threshold is chosen from observed outputs. Missing evidence
is not a pass. A root mapping-review identity is required for candidate scoring.
Tip records must contain the distinct declared rib identities 0 and 1 exactly
once. Comparisons match by these IDs; reordered records are valid, while
duplicate, missing or foreign IDs are refused.
These source criteria authorize no runs and do not revive earlier campaigns.

Proposed source controls, only after fresh scope:
`python -m pytest tests/test_stiffened_shell_e03_reference.py -q`.
At the candidate source freeze, 56 controls were prepared and unrun. Their later
scoped verification is recorded below.
Source controls, installed-provider verification and actual native/external jobs
need separately bounded accounting and preserved failures. Every comparison
remains a B2-only unqualified candidate and refuses a full E03 verdict. No G0–G6,
F01–F13, scientific acceptance, application integration or release gate is closed.

## 7 October scoped tooling verification

Candidate `628bbff5` passed all 56 source controls and the same 56 controls
against the existing hash-matched installed wheel, with no failures or skips.
Wheel SHA256 `fa5507fe14cc09949743adb7d5ae340a2499d9b813d6b80a1b7d4ea414267e82`;
all 431 package modules and frozen input hashes matched. Actual CPU affinity0,
one numerical thread and JIT disabled were verified before and after each run.
Process-wall time total:17.4686185s; peak process-tree RSS:197648384bytes.
Raw commands, runtime, imports, per-case reports, stdout/stderr, JUnit and
accounting: `.qualification/b3-ge-e4-pl/r8-e03-curved-source-dev-20261007-v1/`.

This establishes only assigned tooling controls. No physical native or CalculiX
case executed. Parser-positive synthetic fixtures do not establish equilibrium,
physical convergence, connection fidelity or E03 acceptance. The remaining
132.5313815s is restricted to this verification/repair slice, including its60s
reserve; it cannot fund the separate bridge or physical screen.
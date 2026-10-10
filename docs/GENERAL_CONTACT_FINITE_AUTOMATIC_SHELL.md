# Automatic finite shell workflow

Status: verified against the assigned development criteria on the declared fixture.
The installed fresh16 workflow, independent saved assessment, genuine15→16
restart, separate terminal restores, cancellation and changed-selection refusal
passed. The26 current obligations have staged successful evidence:19 source-overlay
passes reused by impact and7 installed checks. This is not one whole-suite PASS.
The first20 attempt (19PASS/1FAIL), saved3 attempt (2PASS/1FAIL), and variantV8
canonical-naming assertion failure remain NONPASS;
their corrected label refusal and strict-opening obligations passed separately.
The additional installed Q4/rigid inverse matrix passed in10.9124781s: eight
admitted resolution records plus one preserved oblique-cylinder resolver refusal
with domain vector bit-roundtrip only, and zero structural solves. It covers
coarser/stable-tie Q4 roles, reversed explicit roles, complete rigid inventory,
exclusions/conflicting overrides, properties and oblique-plane vectors.
The existing cylinder profile refusal is preserved; cylinder resolution inverse
is not claimed. Exact bindings are recorded in the raw final handoff.
No engineering acceptance or release is supplied by this guide.

## Declared physical fixture and selected discretization

`examples/general_contact_finite_automatic_shell.py` reuses the unchanged paired
V2D physical builder/program. There are8nodes,48DOFs and4exact elastic NativeParity
S3 V2D owners. Upper body elements1/2 use their bottom physical skin; lower body
3/4 use their top skin. Both structural reference offsets are0.01m, thickness
0.05m, reference director+Z. Physical offsets are−0.035m and+0.015m. Initial
physical clearance is0.2µm. Upper coordinates are x0.10–0.95m/y0.13–0.98m;
lower coordinates span0–1.2m. No native-TL companion is admitted.

The declared-domain compiler chooses the lower, coarser triangles as pressure
source (median area0.72m² versus0.36125m²), with shared nonnegative P1 pressure
modes on nodes5–8. Physical-side chart winding is reversed where required;
original FE connectivity, physical directors, owner states and work rows stay
unchanged. This changes the discrete integration/pressure side. The explicit
comparison uses that SAME chosen side and pressure space; coarse/fine solutions
are not asserted identical.

Loads stay on original upper-body nodes2/4. All six coordinates at nodes1,3,5
plus globaluz at lower nodes6,7,8 give21 scalar controls; node6uy is
also fixed. The six non-anchor lower-body rx/ry coordinates remain genuine
bending unknowns. Globaluz guidance is not guidance of every current-normal
translation after tilt. Steps1–12 tilt to60°,13press,14slide0.02m,15open,16recontact.
The adopted solver/law/state/envelope/tolerances are unchanged from the paired
route (1.2rad absolute chart,0.1rad local increment,50µm safety gap).

## Public execution and fixed-selection restore

From the repository with a verified private package on PYTHONPATH:

```powershell
$env:NUMBA_DISABLE_JIT='1'; $env:NUMBA_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'; $env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
$env:PYTHONPATH='C:/ANYworkspaceWork/contact_finite_automatic_shell_delivery_20261009/installed-candidate-v2/site;C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001'
& C:/Python/Python314/python.exe -m examples.general_contact_finite_automatic_shell --through-step 16 --output fresh-new.json
& C:/Python/Python314/python.exe -m examples.general_contact_finite_automatic_shell --through-step 15 --output prefix-new.json
& C:/Python/Python314/python.exe -m examples.general_contact_finite_automatic_shell --restart prefix-new.json --through-step 16 --output suffix-new.json
& C:/Python/Python314/python.exe -m examples.general_contact_finite_automatic_shell --restart suffix-new.json --through-step 16 --output restored-new.json
```

Use separate `--through-step` and value tokens (e.g. `--through-step 16`). Default
is4; output must be a new path. The verified650-payload private wheel is bound by
`C:/ANYworkspaceWork/contact_finite_automatic_shell_delivery_20261009/built-install-v2.json`
(wheel SHA25664f44e794f5c103ddab63af02e8c8aa476f8d4128c3802a48ee432946b619894).
The repository example and its paired-builder/rigid-pose dependencies are required
alongside the private package. These commands describe reproducible usage; existing
guard stages are consumed evidence and do not grant another numerical scope.
Each report retains actual returned
suffix snapshots/states, full producer history, diagnostics and terminal owner
checkpoint, plus the exact domain, selection, fixture/settings/program. A suffix
report does not invent earlier snapshots; a terminal restore has zero new poses.

`AutomaticContactResolution.from_dict` restores the existing to_dict format.
It verifies exact canonical policy/type/identity and redundant definition,
selections/properties; complete pair/coarser/stable-ID/explicit precedence are
checked against the recorded declaration/reference. The digest supplies integrity,
not producer authentication. `verify_automatic_contact_resolution` must additionally
bind the record to the actual current model/domain/settings before solve.

A rich restart uses its stored domain/resolution BEFORE any fresh resolver call.
The new automatic wrapper refuses a bare owner checkpoint without separate saved
`--domain` and `--selection` JSON files. Supplied files are restored and verified;
ordinary owner checkpoint model/analysis/state checks still apply. No selection
is silently recompiled, no checkpoint is resealed and no callback is serialized.
Changing record hashes cannot legitimize inconsistent roles or dropped contacts;
a coherently changed physical reference still fails the actual model guard.

## Measured verification scope

The20 first cases cover exact inverse, unknown/redundant/resealed mutation refusal,
positive-label roundtrip and existing nonpositive patch-label refusal, restore without resolver invocation,
model/domain/settings guard before advancement, missing restart metadata, explicit
precedence and identical selected-role force/tangent/support parity.

Saved-field checks reconstruct physical directors with independent Decimal
exponentials and exact rational error boxes; every P1/P1 pair is bounded at every
returned pose. Independent current source tangent/binormal clipping/quadrature
retains global support and weighted gap before normalization. Orders4/8 and both
steps1e−5/3e−6 test fixed-z spatial force/moment work. These are empirical controls,
not a rigorous quadrature/FD error bound. No production gap/contact kernel is used
as the independent oracle. Full KKT checks freshly assemble structural/contact
operators with stored producer reactions: L1 force/moment scales1e−4N/1e−4Nm,
equilibrium/wrench≤1e−6, L1NCP≤1e−8, all-row support≤1e−11, independent
force/moment≤1e−6, order control≤1e−7 and gap≥−50µm. Strict positive release
separation is separate from zero pressure and safety-gap compliance.

Actual public rich15→16 and terminal0 calls retain selection identity,
compare u (rtol1e−8/atol1e−12), supported z (rtol1e−7/atol1e−12), and validate
all typed model-bound owner checkpoint records. Cancellation follows actual
material/contact trial work and checks rollback/context/hooks and input immutability.
Fresh16 completed in14.018951s; prefix15 in13.0681578s; the restart/terminal
check in12.2490955s and cancellation/refusal checks in10.7065812s. The lower
physical body's six free bending rotations reached7.206723278e−7rad, above the
declared1e−10rad witness and1.19053e−13rad roundoff bound. Supported pressure
force restart difference was zero; all four typed owner checkpoints validated.

The original extended-target-plane release certificate failed for corners outside
the smaller target footprint. Its NONPASS output is retained. The reviewed P1
source-plane certificate proves the same represented-overlap opening requirement
by affine positivity at all target corners, with outward error boxes and chart
guards. All four pairs have strict release lower bound≥1.46410161268e−7m.
The old sufficient certificate remains a diagnostic; it is not a penetration proof.

## Limits

This is an opt-in finite elastic frictionless paired-shell development workflow,
initially scoped to the stated4-owner fixture. It adds selection persistence, not
moving geometric re-pairing, general multi-contact finite acceptance, arbitrary
history authentication, continuum qualification or universal C0–C9 closure.
Prior failed/frozen records, different-family assurance and cut-front/native limits
remain unchanged. Tested, independently accepted and released are separate statuses.

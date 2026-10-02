# Coupled free isotropic sphere — development result

Parent0def128d, isolated reconciliation worktree.
[Prospective slice and corrections](../C6_FREE_SPHERE_SLICE_20261002.md).
Implemented and installed-tested, without C6 engineering acceptance or release.

## Actual capability

One named free sphere against an uncapped elastic classical B2/B3 round tube uses
the shared Newmark driver. Explicit mass and isotropic centre inertia are required;
the geometry point is the mass centre. Three independent physical centre coordinates
join the monolithic system. Partition-of-unity translation maps produce both-body
residuals and complete cross tangents from the radial distributed potential.
No lagged force, artificial mass or restitution coefficient is introduced.
Central frictionless traction gives exact decoupled isotropic spin. Physical body
motion, force, energy and momenta are reported separately from structural arrays.
V6 binds inertia, initial velocities, named ownership and coupled q/v/a state.

Complete relative Hermite bounds include beam and sphere endpoint velocities.
Exact squared-distance tensor Bernstein controls plus component boxes supply
lower bounds; exact feasible values bound the minimum above. Dyadic square-root
brackets and outward conversion retain cancellation/overflow controls. Subdivision
chooses actual lower-bound gain at unchanged1e-10m/512 development settings.
This bounds the represented curve/time path, not an unknown continuum trajectory.

## Verification

Final installed package C:/ANYworkspaceWork/contact-free-sphere-package-20261002:
**171 passed**, **29.241s / 320790528B** sampled process-tree peak,
within180s/999292928B. **454source/wheel/site modules match**;214solver imports
are isolated on site. Effective JIT off and BLAS/Numba threads1 are checked.
Wheel SHA256 `765042560a8ee2d50ba5c29c395be6150b650d373a715f97943e20e50f391721`.

Nine coupled mechanics/lifecycle checks cover an independent closed line-force
and two-body Newmark solution, body impulse, normal linear/angular momentum,
Rodrigues spin/orientation and energy, opening, full virtual work/tangent on B2/B3,
actual deforming B3 normal momentum, active V6 restart/incompatible inertia/spin
and named-state rejection, effective cancellation, exception rollback and explicit
capability rejection. Elastic energy compares a closed line-potential oracle under
dt=.00025/.000125s; fine maximum defect <=1% and improves. Sixty geometry checks
include hidden interior crossings, curved space/time extrema, common motion,
independent exact product/square-root checks, budgets, cancellation and malformed
input. The final selection also runs the prior100checks and two free-sphere CLI
variants, for eight total beam CLI variants. These are development toy fixtures;
their gap/section/material settings are not engineering admission or defaults.

## Evidence, discrepancies and review limits

Source v1 collection failure, v2 60pass/4fail, v3 2pass, v4 59pass/3fail,
v5 3pass, v6 1fail, v7 1pass and v8 1pass are retained. Failed geometry budgets,
the integration/import defects and the stiff B3 fixture are individually explained
in the prospective record. All final affected paths pass in the installed run.
No cap or scientific comparison tolerance was increased.

The geometry worker authored only the kernel and geometry fixtures, with no tests
or Git operations; lead inspected the changes and ran the checks. Two bounded
Mistral Read attempts contain useful source inspections but no final assessment;
they are **incomplete**. Separate OpenAI Read scrutiny found no consequential
blocker in the potential-derived cross blocks, isotropic spin, physical mass,
state/restart and represented-path enclosure. It ran no tests or independent
qualification campaign. [Source adjudication](source-review-adjudication.md).
`raw.zip` retains logs, final candidate, fixtures, wheel and runtime identities.

Free shell coupling, anisotropic/rotating/eccentric bodies, nonlinear materials,
friction, caps, beam-pair impact and general temporal/enforcement qualification
remain required. Accepted static subsets are unaffected; application admission
staysfalse. [Usage](../../GENERAL_CONTACT_C6_CLASSICAL_BEAM_DEV.md).

## Nodal-history branch supplement

The exposed free-sphere history profile has one additional installed pass on the
same unchanged wheel: force ramp, independent forced two-body response, active V6
restart and independently integrated polynomial nodal work. Elapsed3.655s,
174055424B sampled peak,205onsite imports,454module matches and original thread/JIT
and resource settings. This closes that branch coverage gap. Total **172 distinct
checks covered**:171 in the coherent selection plus this one targeted supplement,
not a clean172-check rerun. The updated helper defaults preserve the original
unloaded cases; production source/wheel bytes are unchanged. The initial raw.zip
remains immutable; supplemental evidence is in raw-history-supplement.zip.

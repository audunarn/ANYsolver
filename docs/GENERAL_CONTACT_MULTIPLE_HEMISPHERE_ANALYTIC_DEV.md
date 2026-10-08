# Multiple actual hemisphere plane/sphere support — development

`MULTIPLE_EXPLICIT_B2_B3_HEMISPHERE_SUPPORT_PLANES_SPHERES_STATIC_DEV_V1`
is implemented and installed-tested. Independent engineering acceptance,
application admission and release remain open.

Run `examples/general_contact_multiple_hemisphere_analytic.py`. Declare named
B2/B3 round selections with `beam_end_caps="hemisphere"`, fixed plane/sphere
bodies and explicit penalty interactions. Each requires line stiffness in N/m²,
endpoint stiffness in N/m and dimensional gap tolerance. Select
`ContactSolverSettings(beam_end_cap_work="hemisphere_support_dev")`.
Ordinary nonlinear static force/displacement controls and restart are used.

Each pair reuses the matching actual-tangent hemisphere owner. All contributors
see the same authoritative pose; complete residuals and sparse tangent blocks
are summed. Actual B3 midnode work and cap couples remain. Genuine end ownership
uses all material incidence, including unselected members and their midnodes.
Results contain per-pair fields and named rigid-body forces/moments about zero.
Endpoint counts are endpoint/target pairs, not unique physical endpoint counts.

All-child whole-curve/whole-radius bounds and regularity must admit the common
path. The aggregate rechecks every child at the common proposed fraction. Each
child contract and the composition revision bind restart. Duplicate physical
beam/body pairs, unreferenced selections, resource exhaustion and unsupported
combinations fail explicitly. Existing all-plane support identity/restart and
legacy owned-point profiles remain unchanged.

## Checks and limits

Installed49checks pass in17.766s, peak355430400B;216loaded modules and506package
files match source. Effective JIT disabled and numerical pools/Numba1, bounded
180s/953MiB. Independent combined scalar work, per-body wrench,1e-5directional
Hessian, actual simultaneous plane/sphere and sphere/sphere bar controls,
active JSON restart, genuine junction omission, real second-child cancellation/
exception rollback, common fraction and legacy/no-contact controls pass.
Both independent bar response errors are2.015e-14 against1e-6; gap budget1e-5m.
The final suite differs from predecessors; no runtime improvement is claimed.

Supporting source review found no production defect. Its junction-coverage
finding was resolved using an actual endpoint/material-midnode shared incidence
and direct endpoint-identity assertions. This is not independent engineering
acceptance. [Evidence](d1_review_support/contact_multiple_hemisphere_analytic_20261004/summary.json)
contains five runs and40raw records, source identities, actual bar fields,
effective settings, byte parity and review disposition.

Scope is explicit fixed planes/spheres, concentric scalar-elastic B2/B3 von Karman
static analysis, exterior gap budgets below beam/obstacle radii. The same C1
sphere/rim seams and open-only nonunique parallel-rim rule apply. No cylinder
fallback, moving tools, automatic/self-contact, friction, native or transient
admission. Mesh/enforcement qualification and complete C0–C9 remain required.

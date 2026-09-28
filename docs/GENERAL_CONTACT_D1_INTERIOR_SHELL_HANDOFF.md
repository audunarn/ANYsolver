# Interior Q4/S3 shell contact: bounded development handoff

**Status:** reviewed component evidence; integrated handoff disposition pending.
**Source-bound installed example:** ANYsolver wheel from `c55c3860`, SHA-256
`dcade18155bd1e5f1e2b98b6869711c07f7ba06435877f75a13a05062f304c81`.
This is an opt-in development capability, not general C1 acceptance or release.

## Run the demonstrated workflow

From the matching ANYsolver checkout, put the registered wheel's isolated
install target first on `PYTHONPATH`, then run:

```powershell
$env:PYTHONPATH = 'C:\ANYworkspaceWork\general-contact-evidence\install-c55c3860-20260927;C:\ANYworkspaceWork\ANYsolver-general-contact'
python -m examples.general_contact_distributed_q4_s3_cycle --columns 24 --output interior-shell-cycle.json
```

Check that the output's `anysolver_module` is under the registered install
target. Importing a different solver build does not reproduce the historical
installed claim.

The [example](../examples/general_contact_distributed_q4_s3_cycle.py) builds
an elastic planar strip of 24 Q4 source faces against a nonmatching two-S3
target patch. The target is structurally fixed. A 0.3 N distributed source
load produces twelve ordinary nonlinear-static steps: press, lateral slide,
opening and recontact. The source uses its physical bottom skin and the
target its top skin with the declared S3 offset. The example explicitly
selects projected primal mortar, Jet2 Q4/S3 derivatives, supported-pressure
Schur acceleration, surface regularization, pressure/gap tolerances and
resource caps. Each saved step reports integrated contact force, summed
vertical support reaction, independent minimum gap, active pressure count and
pressure change. A run-level flag reports checkpoint presence.

The [installed verification](reference_cases/general_contact_d1_distributed_24q4_installed_v1_review.md)
ran the same module and options with a registered output path and `anysolver`
imported from its isolated wheel target.
It completed twelve steps and reproduced the accepted source reference's
normal force, gap, pressure-change and active-count history. Full-load force
was 0.1038788373 N, first-unload force 0.0398439617 N, and the last
independent gap was −2.01624e−8 m under the registered 50 µm budget.

## What the evidence establishes

| Claim | Reviewed evidence | Limit |
|---|---|---|
| Integrated force and contact-state sequence | [24-Q4 response review](reference_cases/general_contact_d1_distributed_cycle_response_v1_review.md) | Planar elastic interior overlap, fixed target and registered path; 16→24 full-load force change 0.007006% |
| State continuation | [identity-aware split restart review](reference_cases/general_contact_d1_distributed_restart_identity_v2a_adjudication.md) | Fresh-model 6/12 split, same definitions and ordered pressure features |
| Tangent | [coupled tangent review](reference_cases/general_contact_d1_distributed_coupled_tangent_v1_review.md) | One smooth fixed-multiplier direction at the constrained saved pose |
| Pressure resolution | [fixed-pose partial-contact review](reference_cases/general_contact_d1_partial_pressure_space_v1_review.md) | Separate affine-penetration case; supported rank and integrated-force resolution only |
| Installed execution | [installed cycle review](reference_cases/general_contact_d1_distributed_24q4_installed_v1_review.md) | Exact wheel and example identity above |

These reviewed claims are separate. Complete coupled tangent qualification,
coupled partial-contact pressure stability, deformable-target response,
physical-edge sliding, general C1 admission, application adapters and release
remain open. The first sixteen-Q4 press failure and restart-adjudicator
metadata failures remain in the [development record](GENERAL_CONTACT_C1_MIXED_FORCE_PATH.md)
and [capability ledger](GENERAL_CONTACT_CAPABILITIES.md).

The current development branch has subsequently added opt-in search, Schur
retry and macro-pressure code. Its post-change 24-Q4 installed cycle has not
been verified. The historical installed result therefore remains bound to
the wheel and source identity stated above.

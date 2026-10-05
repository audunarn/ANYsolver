# Two curved physical-fibre beams sharing a deformable S3 patch

5 October 2026. Implemented and installed-tested development subset, not
independently accepted or released. Parent `30d6a215`.
[Exact identities and raw results](two_beam_summary.json).

## Implementation

The existing example now accepts `two_beams=True` / `--two-beams`. It constructs
two separate native elements with their own clamps, nodal loads and retained
physical/material coordinates. The second reference curve is translated by
0.25 m in y; its tip load is -0.003 N versus -0.005 N for the first. Both act on
one actual deformable S3 patch through the existing coupled owner. No new owner,
independent element condensation or beam-beam collision capability is introduced.

The example CLI now exposes explicit load targets, normal regularization and
the already implemented integration/enclosure policies. Existing defaults and
single-beam checkpoint identities remain valid. The installed production core
is unchanged: all 526 files match candidate12's preceding wheel. Example and test
hashes, including executed preflights, are retained separately.

## Verification

| Check | Elapsed s | Peak bytes | Result |
|---|---:|---:|---|
| Actual first-target coupled solve, histories and restart | 76.167 | 183566336 | passed |
| Local both-beam work/tangent and legacy checkpoint identity | 9.269 | 184377344 | 2 passed |
| CLI material recovery | 3.396 | 183144448 | passed |
| Saved-state independent gaps, complete wrench and material energy | 4.484 | 185708544 | passed |

Native runs retain the unchanged 120-second/953-MiB limit from construction;
JIT disabled and numerical pools one. Imported core paths were verified. The
full solve was not repeated for reporting or saved-state checks.

There are 84 retained native coordinates, separate histories for both beams and
shared shell coordinate 92. Both contact tangents include retained internal
rotation work and map into the same deformable-target row/column. Complete local
directional tangent errors are 2.060358e-8 and 5.225247e-9; independent energy
virtual-work errors are 1.249293e-7 and 3.135916e-8, below 1e-5. The independent
analytic parabola/circle energy uses adaptive axial integration, with separate
12/24-point angular agreement controls; it calls no production contact kernel.

Actual solve: 46 candidate requests, 39 pair evaluations, 27 reuse hits. One
beam-2 grazing trial is explicitly rejected at tangent uncertainty 1.068319e-6;
the bounded solver subsequently accepts equilibrium without changing settings.
Both beams have positive contact reaction and plastic history. Sixteen fibre
stations yield. Independent rational constitutive reconstruction matches both
committed histories from the original virgin material origins. Equilibrium norms
are 1.810868e-12, 1.206124e-16 and 1.375262e-12 against 1e-10.

Independent physical gaps are -6.379241e-6 m and -4.652081e-6 m, within 30 um and
above their production lower bounds. Complete support/load force and moment
balance errors are 3.344380e-10 and 2.532470e-10 on the frozen 0.008 N / 0.02 Nm
scales. Restart, origin immutability and cache/lock cleanup pass. CLI recovery
reports both material elements and matches independent rational stored-energy,
plastic-dissipation and incremental-potential sums.

The checkpoint is byte-preserved at
`tests/data/general_contact_native_fibre_s3_plastic_two_beams_v1.checkpoint`,
SHA `a8211bce3cf3468fa2c4f10328b031b635f88bb240f9fee0bdb98b09653282da`.

## Retained failures and review

Raw candidate12 records retain the initial local clamp/read-only fixture errors,
uniform-compression interval-budget exhaustion and fixed-order reference
virtual-work discrepancy. They are not relabelled as passes. The corrected test
uses the verified partial-front coordinate pose, with no material-history
transfer. The adaptive reference resolves the principal reference-integration
discrepancy without changing production law, tolerances or interval limits.

Supporting same-family review identified and resolved original-origin equilibrium
and per-beam participation checks. It is not independent engineering acceptance.
Cached Mistral remains unavailable; no repeated availability probe was performed.

## Usage

From the reconciliation checkout with the solver installed, the tested definition
can be constructed without hidden policy selection:

```powershell
python examples/general_contact_native_curved_material_s3.py --targets 1 --two-beams --plastic-fibres --normal-stiffness 80000000 --integration-budget-policy certified_active --root-tangent-enclosure-policy anchored --checkpoint-out two_beam.checkpoint
```

The saved fixture can be recovered without another coupled solve using the same
definition flags plus `--restart tests/data/general_contact_native_fibre_s3_plastic_two_beams_v1.checkpoint --recover-material two_beam_material.json --material-stations`.

This extends multiple-beam/shared-target static development coverage. Multiple
shell patches with physical fibres, beam-beam mechanics, spatial/enforcement
breadth, independent native acceptance, friction, dynamics and application
completion remain required.

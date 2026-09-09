# GE-B3 native: accepted scoped opt-in delivery

The exact artifact for `GE_BEAM3_NATIVE_OWNED_WORKFLOWS_V1` is independently
accepted with empty findings. Use the explicit `ge-beam3-native` workflow
interface described in [Native workflows](GE_BEAM3_NATIVE_WORKFLOWS.md):

```python
from anysolver import ge_beam3_native as beam

# Supply exact physical geometry, section and inertia definitions.
# definition = beam.define_beam(beam.SELECTOR, ...)
# owner = beam.create_analysis(beam.SELECTOR, (definition,), boundaries)
```

This is an independently reviewed delivery profile for the admitted native
straight and regular curved piecewise-Q2 workflows, not universal physical
qualification or a default replacement. Existing B2/B3, the earlier `ge-beam3`
straight interface, qualified Q4/S3 and all defaults remain unchanged.

## Accepted domain

- Native axial/shear/biaxial bending/torsion and objective finite-rotation
  straight/curved reference mechanics, with the preserved refinement and
  slenderness evidence.
- Declared coupled generalized resultant and physical axial/biaxial fibre
  section laws; authenticated load/unload/reversal, recovery and restart.
- Admitted reference/current-rest spectral and frozen-current buckling
  workflows using physical retained inertia and the unchanged admission guards.
- Objective eccentric generalized-beam connection to one owned elastic Q4 or
  S3 V2D, with the V2 variational map and durable full-history replay.

The limitations in the independent review and workflow documentation are part
of acceptance. Arbitrary material adapters, generic mixed FEModel routing,
plastic/fibre-shell coupling and finite-velocity rotational dynamics are not
included. Preserved signed postcritical branches are explicitly unstable;
they do not establish stable postbuckling or a loading path from rest.

## Exact delivery

Candidate commit: `5fc032e48d25c0a0b866363514b73ac7baf8803c`.
Candidate tree: `de654ae812344326c781d159822c3463a0804af9`.
Runtime subtree: `314995f39fd773a9afe0fd9a5011ba50c9126342`.
Profile SHA-256: `5142309586ec5dde3d9a0acc2ec8e77e1a093513ea17b96e6767c5b52d8574ee`.

Wheel: `anysolver-0.4.2-py3-none-any.whl`, 1,785,715 bytes.
SHA-256: `699ae0dbaef06be61efa7b9a8f923c2ab5607061c00f7ab9f4066217cc340ef4`.

This is an **unpublished qualification artifact**, not the existing PyPI
0.4.2 artifact. No version, tag, publication, merge or default change was made.
The original selected source commit and exact wheel remain authoritative;
subsequent closeout commits add documentation/evidence only.

## Verification and preservation

The two separate public-interface replicas passed35 tests each; their six
scientific files match the development smoke. Durable coupled-boundary
rehearsal and replicas passed39 tests each. The separate final gate-unit
inventory passed10 tests. Inventories are not combined into a single count.

All317 solver Python files agree across the exact Git export, built wheel and
installed target. The20 scientific records agree byte-for-byte between source
control and two fresh isolated installed-wheel processes. All33 formal child
processes completed successfully with empty process trees. The independent
review measured about150.58 seconds from first child start to completion-file
publication; this is diagnostic, not a relaxed acceptance threshold.

All12 balanced measured B2/B3 pairs pass the frozen median paired-ratio gate
of1.05. Worst measured ratio is1.0486896969493953 for B2 linear solve.
Median/MAD/p95, CPU, process-memory data and all raw pairs remain external.
This is not a speedup or universal-performance claim.

Canonical authority: [Independent artifact review](reference_cases/ge_beam3_final_delivery_independent_review.json)
and [complete verification/archive manifest](reference_cases/ge_beam3_final_delivery_verification.json).
The manifest binds300 final/development records, the exact wheel and source
archives, plus the preceding40-file public and67-file durable archives through
their commit/blob-bound manifests. All scientific and historical failures remain
preserved; none was reclassified or rerun during this delivery closeout.

An administrative Windows short/long-path mismatch initially nested archive
copies beneath GUID suffixes. Verified copies now exist at the declared paths;
the preliminary copies and original evidence remain untouched. No mechanics,
result or authority identity changed. Raw candidate/checkpoint flags continue
to say `production_qualified=False` by their frozen contracts; this separate
artifact acceptance must not be implemented by rewriting those historical fields.

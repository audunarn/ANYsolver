# Curved native beam-pair lifecycle development example

This is an installed-tested development fixture, not an independently accepted
native capability or application admission. Both curved B3-GE beams retain their
physical fibre history and all 84 structural coordinates.

The programme loads, unloads and reloads with parameters `(0.05, 0, 0.05)`.
Normal line regularization is explicitly `8000 N/m²`; gap tolerance is `50 µm`.
These are fixture settings, not application defaults.

## Solver controls

The internal example factory in
`examples/general_contact_native_retained_whole_pair.py` forwards:

- `initial_trial`: an immutable, model-bound mechanical guess for the first
  virgin increment. It imports neither plastic history nor another checkpoint.
- `reuse_target_trials=True`: reuse the last accepted mechanical pose at exactly
  the same parameter. Material response always starts from the current committed
  history. The complete current-to-guess path and endpoint must be certified.

Both controls are explicit and bind checkpoint identity. The defaults preserve
earlier behaviour. Unsupported geometry, corrupted controls or an uncertified
trial fail without switching algorithms.

## Reproduce the saved continuation

Use the source checkout and matching package with the focused runtime settings:
JIT disabled, Numba and numerical pools set to one, and no concurrent numerical
job. The recorded jobs had a 120-second process bound and 953 MiB memory bound.

Create a fresh evidence directory. Set `CONTACT_NATIVE_CURVED_LIFECYCLE_EVIDENCE`
to it and copy the portable fixture
`tests/data/general_contact_native_curved_pair_lifecycle_press_v1.checkpoint`
to `lifecycle_stage1.checkpoint` there.

Set `CONTACT_NATIVE_CURVED_LIFECYCLE_STAGE=2`, then run:

```text
python -m pytest -q tests/test_general_contact_native_curved_pair_lifecycle.py::test_staged_curved_pair_press_open_recontact
```

Repeat that selector with stage `3`. Each stage authenticates the same complete
programme, preserves the preceding records and writes its accepted capsule before
postprocessing. Unset the stage variable, set
`CONTACT_NATIVE_CURVED_LIFECYCLE_REPLAY=1`, then run:

```text
python -m pytest -q tests/test_general_contact_native_curved_pair_lifecycle.py::test_complete_lifecycle_canonical_replay_and_prefix_history_chain
```

This final check replays the full checkpoint without another solve and measures
each beam's support, applied-load and contact wrench balance. Fresh owners obey
their own construction deadline; replay never resets an existing owner's clock.

## Recorded outcome

Opening and recontact passed in 70.959 and 64.464 seconds. Opening has zero contact
potential and a conservative gap of +0.900 mm; recontact is active at −13.54 µm.
Independent material returns agree at all three stages. Exact chain replay and
support wrench checks passed; normalized errors are below `5.90e-9`.

[Measurements, source identities and remaining limits](d1_review_support/contact_native_fibre_s3_20261005/curved_pair_lifecycle.json)
and [retained development failures](d1_review_support/contact_native_fibre_s3_20261005/curved_pair_development.md).
Native spatial/section qualification, independent engineering acceptance and the
broader friction, impact and application programme remain open.

# Partial shell contact — installed development handoff

The public [example](../examples/general_contact_partial_shell_cycle.py) presses
two guided Q4 faces against a nonmatching two-S3 target, translates the target,
opens and recontacts. Source boundary normal controls remain in contact work.
Active/open checkpoints persist and resume on fresh models. This handoff is
tested development work; independent capability disposition is separate.

## Run

The installed artifact is local and has not been published. In PowerShell:

```powershell
$env:PYTHONPATH='C:/ANYworkspaceWork/general-contact-partial-swept-dev/target'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python C:/ANYworkspaceWork/ANYsolver-general-contact/examples/general_contact_partial_shell_cycle.py --restart --output C:/ANYworkspaceWork/partial-shell-cycle.json
```

Use a new output name. The example writes integrated source/target forces,
control reactions, gap bounds, activity, final displacement and checkpoint, plus
separate active/open checkpoint files. Omit `--restart` for an uninterrupted run.
It uses public solver definitions and does not import tests or development helpers.

## Numerical model and limits

All quantities are SI. Elastic shells use E=100000 Pa, nu=.3 and thickness=.05 m.
The initial physical-skin gap is100 micrometres, including the target's .01 m
reference offset. Source in-plane motion and rotations are fixed; the target
keeps its flat shape and translates .16 m. Two source normal controls press
130 micrometres. Friction and contact damping are absent.

Select `normal_law="projected_penalty"`, normal regularization10^7 Pa/m and
physical gap tolerance50 micrometres explicitly. These are fixture settings,
not application defaults. Fine nodal Q1 pressure, shared positive support and
the full generally nonsymmetric work derivative are retained. Regularization
storage is not material work or a total contact potential. Numerical penetration
and reactions depend on the declared finite regularization; this is not exact
hard-contact complementarity or an interference-fit facility.

The interval certificate encloses the represented affine physical skin-node
path, including rounded subdivision endpoints. It does not establish general
finite-rotation director or dynamic event detection. No warped geometry,
friction, arbitrary rims, beam contact, self-contact or application admission is
established by this example. D1 defaults and accepted scope remain separate.

## Evidence and remaining programme

The installed example completes10poses in19.486 s/276 MB, with exact displacement,
force, gap, control-reaction and material-state parity with its development
reference. All433 installed Python files match the recorded source bytes.
[Artifact identity](d1_review_support/d2_partial_installed_v1_20260930.artifact.json),
[effective process](d1_review_support/d2_partial_installed_v1_20260930.identity.json)
and [comparison](d1_review_support/d2_partial_installed_v1_20260930.assessment.json)
retain the reproducible details. Complete checkpoint identity parity between
differently named examples is not claimed.

[Analytical partial-support benchmark](d1_review_support/D2_GUIDED_PARTIAL_FOUNDATION_REVIEW_20260930.md)
and [swept/state review](d1_review_support/D2_OVERLAP_SWEPT_ENCLOSURE_REVIEW_20260930.md)
have distinct scopes. Radial response and timeout failures remain NONPASS.
No universal pressure-space or hard-contact limit follows from these results.
See the [capability ledger](GENERAL_CONTACT_CAPABILITIES.md) and
[full programme](GENERAL_CONTACT_FULL_PROGRAMME_20260929.md) for D2–D8 work.

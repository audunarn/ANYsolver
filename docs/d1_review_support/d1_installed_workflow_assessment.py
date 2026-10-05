"""Compare an installed force-prefix replay using the existing owner checks.

This closes an installed-artifact boundary; it does not repeat or broaden the
eight-pose scientific qualification. No constitutive/contact state is resealed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from docs.d1_review_support.d1_cycle_restart_assessment import (
    TOLERANCE, _Comparison, _current_pressure_mode_ids, _fixture,
    _program_fixture_identity, _validate_record,
)
from docs.d1_review_support.d1_saved_checkpoint_roundtrip_dev import _contract


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--expected-steps', type=int, choices=(2, 6), required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    import anysolver
    from anysolver.assembly import build_constraint_transformation
    from anysolver.matrix_assembly import assemble_stiffness_matrix
    from anysolver.nonlinear_restart import (
        canonical_checkpoint_json_bytes, load_nonlinear_checkpoint,
        validate_nonlinear_checkpoint,
    )
    from scripts.general_contact_d1_interior_press_dev import build_saved_cycle

    records = {
        'reference': json.loads(args.reference.read_text(encoding='utf-8')),
        'prefix': json.loads(args.candidate.read_text(encoding='utf-8')),
    }
    model, definition, settings, program = build_saved_cycle(records['reference'])
    contract = _contract(model, definition, settings, program)
    pressure_ids = _current_pressure_mode_ids(model, contract['general_contact'])
    model.apply_boundary_conditions()
    stiffness, _ = assemble_stiffness_matrix(model)
    _, _, transform, offset, _, _ = build_constraint_transformation(
        stiffness, np.zeros(model.mesh.dof_manager.total_dofs), model)
    comparison = _Comparison()
    checkpoints = {}
    for label, record in records.items():
        canonical_checkpoint_json_bytes(record)
        _program_fixture_identity(record, program)
        loaded = load_nonlinear_checkpoint(record['restart_checkpoint'])
        validated = validate_nonlinear_checkpoint(
            loaded, analysis_kind='static', model=model,
            analysis_contract=contract, num_layers=contract['num_layers'])
        checkpoints[label] = validated.payload
        poses = record['accepted_pose_displacements']
        if len(poses) != args.expected_steps:
            raise ValueError('complete declared prefix snapshots required')
        _validate_record(record, validated.payload, poses, args.expected_steps,
                         model, program, transform, offset, comparison, label,
                         pressure_ids)
    comparison.compare(_fixture(records['reference']), _fixture(records['prefix']),
                       'fixture', 'fixture')
    for key in ('displacements', 'accepted_pose_displacements', 'history',
                'swept_fraction_trace'):
        comparison.compare(records['reference'][key], records['prefix'][key], key, key)
    comparison.compare(checkpoints['reference'], checkpoints['prefix'],
                       'complete_state', 'checkpoint', owner_validated=True)
    passed = comparison.failure_count == 0
    for row in comparison.hashes:
        row['disposition'] = (
            'owner-validated hash; complete underlying payload agrees within tolerance'
            if passed else 'unresolved: underlying payload comparison failed')
    result = dict(status='installed_prefix_boundary_assessment', checks_met=passed,
        expected_steps=args.expected_steps, absolute_tolerance=TOLERANCE,
        complete_current_owner_validation=True,
        comparison_failure_count=comparison.failure_count,
        comparison_failures=comparison.failures,
        maximum_absolute_differences=comparison.maximum,
        diagnostic_difference_count=comparison.diagnostic_count,
        diagnostic_differences=comparison.diagnostics,
        derived_hash_differences=comparison.hashes,
        anysolver_module=str(Path(anysolver.__file__).resolve()),
        inputs={key: dict(path=str(path.resolve()),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            for key, path in (('reference', args.reference), ('candidate', args.candidate))},
        independently_accepted=False, released=False)
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(checks_met=passed, failures=comparison.failure_count,
                         diagnostic_differences=comparison.diagnostic_count)))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

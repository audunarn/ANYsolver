"""Static provenance check for retained first-three director test evidence."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parents[1]
REPO = PHASE.parents[2]
NAME = 'tests/test_nonlinear_beam_shell_slice3_director_continuation.py'
COMMON = 'tests/test_nonlinear_beam_shell_slice3_continuation.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    old = PHASE / 'failed-candidates/director-before-rejected-interval-seed' / Path(NAME).name
    current = REPO / NAME
    historical = json.loads((PHASE / 'candidate-identities/revised-endpoint-frozen-candidate/candidate.json').read_text())
    receipt = json.loads((PHASE / 'evidence/director-option-plastic-first-three/receipt.json').read_text())
    negative_receipt = json.loads((PHASE / 'evidence/restored-director-negative-state-access-retry/receipt.json').read_text())
    previous_seven = PHASE / 'candidate-identities/rejected-seed-pilot-frozen/snapshot' / NAME
    before = ast.parse(old.read_text())
    after = ast.parse(current.read_text())
    prefix_equal = [ast.dump(n, include_attributes=False) for n in before.body] == [
        ast.dump(n, include_attributes=False) for n in after.body[:len(before.body)]]
    additions = after.body[len(before.body):]
    product = ['src/anysolver/' + n for n in (
        'corotational.py', 'elements.py', 'mesh_gen.py', 'nonlinear_static.py',
        'nonlinear_performance.py', '_corotational_batch.py', '_director_trace.py',
        '_nonlinear_events.py', '_nonlinear_seed.py')]
    source_equal = all(sha(REPO / p) == receipt['identity_hashes'].get(p)
                       == historical['working_source_and_selected_inputs_sha256'][p]
                       for p in product)
    helper_equal = sha(REPO / COMMON) == receipt['identity_hashes'].get(COMMON)
    original_bound = sha(old) == receipt['identity_hashes'].get(NAME)
    previous_seven_ast = ast.parse(previous_seven.read_text())
    refusal_prefix_equal = [ast.dump(n, include_attributes=False) for n in before.body] == [
        ast.dump(n, include_attributes=False) for n in previous_seven_ast.body[:len(before.body)]]
    additions_inactive = all(isinstance(n, ast.FunctionDef)
                            and n.name == 'test_director_stopped_negative_run_excludes_rejected_history'
                            and not n.decorator_list for n in additions)
    checks = dict(original_module_bound_to_receipt=original_bound,
                  original_module_prefix_ast_unchanged=prefix_equal,
                  additions_are_separate_negative_test_definitions=bool(additions) and additions_inactive,
                  common_oracle_dependency_identical=helper_equal,
                  prior_seven_case_module_bound_to_refusal_receipt=sha(previous_seven) == negative_receipt['identity_hashes'].get(NAME),
                  prior_seven_case_original_prefix_ast_unchanged=refusal_prefix_equal,
                  refusal_common_dependency_identical=sha(REPO / COMMON) == negative_receipt['identity_hashes'].get(COMMON),
                  refusal_all_nine_product_sources_identical=all(
                      sha(REPO / p) == negative_receipt['identity_hashes'].get(p) for p in product),
                  all_nine_product_sources_identical=source_equal)
    report = dict(kind='root_static_test_source_impact', checks=checks,
                  active_first_three_paths_equivalent=all(checks.values()),
                  original_module_sha256=sha(old), current_module_sha256=sha(current),
                  raw_test_module_hashes_equal=sha(old) == sha(current),
                  retained_outcome='Two preyield passes and one stopped-at-limit full-target failure; no restart/cancellation pass is inferred.',
                  no_solver_or_material_imports=True)
    out = PHASE / 'restored-director-first-three-source-impact.json'
    with out.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report))


if __name__ == '__main__':
    main()

"""Reconcile exact development selections, terminal counts and runtime evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

TASK = Path(__file__).resolve().parents[1]
PRODUCT = ('corotational.py', 'elements.py', 'mesh_gen.py', 'nonlinear_static.py',
           'nonlinear_performance.py', '_corotational_batch.py', '_director_trace.py', '_nonlinear_events.py', '_nonlinear_seed.py')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def matches(node, target):
    return node == target or node.startswith(target+'::') or node.startswith(target+'[')


def summarize(collection, names, excluded_modules=()):
    selection = read(TASK/f'{collection}-selection.json')
    collection_receipt = read(TASK/'evidence'/collection/'receipt.json')
    collection_product = tuple(collection_receipt['identity_hashes'].get(
        'src/anysolver/'+p) for p in PRODUCT)
    ids = [line.strip() for line in (TASK/'evidence'/collection/'stdout.txt').read_text().splitlines()
           if line.startswith('tests/') and '::' in line]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError('collection IDs missing or duplicated')
    full_collection_count = len(ids)
    unknown_exclusions = set(excluded_modules) - set(selection['all_required_targets'])
    if unknown_exclusions:
        raise ValueError('Excluded modules must be explicitly present in the collection')
    ids = [node for node in ids if node.partition('::')[0] not in excluded_modules]
    membership = {node: [] for node in ids}
    fingerprints, rows = [], []
    total = dict(collected=0, passed=0, failed=0, skipped=0, error=0, xfailed=0, xpassed=0)
    for name in names:
        selected = read(TASK/f'{name}-selection.json')
        receipt = read(TASK/'evidence'/name/'receipt.json')
        hashes = receipt['identity_hashes']
        fingerprints.append(tuple(hashes.get('src/anysolver/'+p) for p in PRODUCT))
        expected = [node for node in ids if any(matches(node, t) for t in selected['targets'])]
        for node in expected:
            membership[node].append(name)
        text = (TASK/'evidence'/name/'stdout.txt').read_text()
        records = re.findall(r'\[development\] exact targets=\d+; record=(.+)', text)
        runtime_path = Path(records[0].strip())/'runtime.json' if len(records) == 1 else None
        runtime = read(runtime_path) if runtime_path and runtime_path.is_file() else None
        stable_tests = all(selection['selected_file_sha256'].get(p) == h
                           for p, h in selected['selected_file_sha256'].items())
        effective = bool(runtime is not None and not runtime['errors']
                         and runtime['jit_disabled'] is True and runtime['numba_threads'] == 1
                         and runtime['plugin_autoload_disabled'] is True
                         and runtime['effective_pools']
                         and all(p['num_threads'] == 1 for p in runtime['effective_pools'])
                         and receipt['child_env']['ANYSOLVER_RUN_RETIRED_PROGRAMME_TESTS'] == '0')
        terminal = receipt['status'] in ('EXIT', 'EXIT_1') and runtime is not None
        coverage = bool(terminal and runtime['collected'] == len(expected))
        if terminal:
            total['collected'] += runtime['collected']
            for outcome in total.keys()-{'collected'}:
                total[outcome] += runtime['outcomes'].get(outcome, 0)
        rows.append(dict(name=name, status=receipt['status'], terminal_runtime=terminal,
                         expected_count=len(expected), actual_collected=runtime['collected'] if runtime else None,
                         actual_outcomes=runtime['outcomes'] if runtime else None,
                         collected_count_matches=coverage, selected_tests_unchanged=stable_tests,
                         effective_runtime_passed=effective,
                         runtime_path=str(runtime_path) if runtime_path else None,
                         process_wall_seconds=receipt['process_wall_seconds']))
    omissions = [n for n, owners in membership.items() if not owners]
    overlaps = {n: owners for n, owners in membership.items() if len(owners) > 1}
    same_product = bool(fingerprints and all(all(v is not None for v in f)
                                           and f == fingerprints[0] for f in fingerprints))
    checks = dict(exact_id_union_without_overlap=not omissions and not overlaps,
                  all_invocations_terminal_and_counts_match=all(r['collected_count_matches'] for r in rows),
                  selected_test_identities_match_collection=all(r['selected_tests_unchanged'] for r in rows),
                  same_product_identity=same_product,
                  product_identity_matches_collection=bool(
                      all(v is not None for v in collection_product)
                      and all(f == collection_product for f in fingerprints)),
                  effective_runtime_verified=all(r['effective_runtime_passed'] for r in rows),
                  no_failing_or_error_outcomes=not any(total[k] for k in ('failed', 'error', 'xpassed')),
                  all_processes_successful=all(r['status'] == 'EXIT' for r in rows))
    return dict(kind='partitioned_development_regression', collection=collection,
                required_modules=[p for p in selection['all_required_targets'] if p not in excluded_modules],
                full_collection_id_count=full_collection_count,
                scope_excluded_modules=list(excluded_modules), collected_id_count=len(ids),
                actual_terminal_counts=total, checks=checks, passed=all(checks.values()),
                rows=rows, omitted_ids=omissions, overlapping_ids=overlaps,
                id_to_invocation={n: owners[0] for n, owners in membership.items() if len(owners) == 1},
                collection_stdout_sha256=hashlib.sha256(
                    (TASK/'evidence'/collection/'stdout.txt').read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--collection', required=True)
    parser.add_argument('--runs', nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--exclude-module', action='append', default=[])
    args = parser.parse_args()
    report = summarize(args.collection, args.runs, args.exclude_module)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps({k: report[k] for k in ('collected_id_count', 'actual_terminal_counts', 'checks', 'passed')}))


if __name__ == '__main__':
    main()

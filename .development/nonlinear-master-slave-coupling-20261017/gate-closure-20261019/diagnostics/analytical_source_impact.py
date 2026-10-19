"""Static AST/hash inventory only; imports no solver and executes no numerics."""
import ast
import hashlib
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parents[1]
TASK = PHASE.parent
REPO = TASK.parents[1]
OLD = TASK / 'candidate-identities/integrated-final-handoff-entry/snapshot'
CASE = TASK / 'evidence/integrated-final-arc-nonmatching-e0.002-a30-n32/result.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def symbols(path):
    found = {}
    def visit(nodes, prefix=''):
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + node.name
                found[name] = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
                visit(node.body, name + '.')
    tree = ast.parse(path.read_text(encoding='utf-8'))
    visit(tree.body)
    return found


def main():
    identity = json.loads(CASE.read_text())['identity']['sha256']
    rows = []
    for relative in ['src/anysolver/' + p for p in (
            'corotational.py', 'elements.py', 'mesh_gen.py',
            'nonlinear_static.py', 'nonlinear_performance.py', '_corotational_batch.py')]:
        old, current = OLD / relative, REPO / relative
        if digest(old) != identity[relative]:
            raise ValueError('Snapshot does not match historical case: ' + relative)
        before, after = symbols(old), symbols(current)
        changed = [n for n in before.keys() & after.keys() if before[n] != after[n]]
        leaves = [n for n in changed if not any(k.startswith(n + '.') for k in changed)]
        rows.append(dict(path=relative, historical_sha256=digest(old), current_sha256=digest(current),
                         changed_existing_leaf_symbols=sorted(leaves),
                         added_symbols=sorted(after.keys()-before.keys()),
                         removed_symbols=sorted(before.keys()-after.keys())))
    oracle = {}
    for name in ('arc_reference.py', 'assessment_support.py'):
        path = TASK/'diagnostics'/name
        key = path.relative_to(REPO).as_posix()
        oracle[name] = dict(historical_sha256=identity[key], current_sha256=digest(path),
                            unchanged=identity[key] == digest(path))
    out = dict(kind='static_source_delta_not_equivalence_proof', historical_case=str(CASE),
               historical_snapshot=str(OLD), source=rows, oracle=oracle)
    (PHASE/'analytical-source-impact-inventory.json').write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps(dict(source=[dict(path=r['path'], changed=r['changed_existing_leaf_symbols'])
                                  for r in rows], oracle=oracle)))


if __name__ == '__main__':
    main()

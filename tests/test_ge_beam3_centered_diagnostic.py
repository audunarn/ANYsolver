"""Fresh-process determinism and static bindings for centered reference work."""

import json
import os
from pathlib import Path
import subprocess
import sys

from docs.reference_cases import ge_beam3_centered_reference_diagnostic as diagnostic


def test_centered_diagnostic_two_fresh_processes_are_identical(tmp_path):
    env = dict(os.environ)
    env['PYTHONPATH'] = str(diagnostic.ROOT/'src')+os.pathsep+env.get('PYTHONPATH','')
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        env[name] = '1'
    outputs = []
    for index in (1,2):
        directory = tmp_path/str(index); directory.mkdir()
        result = subprocess.run([sys.executable,'-B',str(Path(diagnostic.__file__).resolve())],
            cwd=directory,env=env,check=True,capture_output=True,timeout=30)
        raw = result.stdout.replace(b'\r\n',b'\n'); value = json.loads(raw)
        assert diagnostic.canonical(value) == raw
        assert not value['native_package_adoption_complete'] and not value['production_qualified']
        outputs.append(raw)
    assert outputs[0] == outputs[1]


def test_preserved_centered_evidence_binds_sources_and_limits_claims():
    path = diagnostic.ROOT/'docs/reference_cases/ge_beam3_centered_reference_evidence.json'
    raw = path.read_text(encoding='utf-8').encode('ascii'); value = json.loads(raw)
    assert diagnostic.canonical(value) == raw
    assert value['source_bindings'] == diagnostic.bindings()
    assert value['base_commit'] == diagnostic.BASE
    assert value['independent_review_status'] == 'PENDING'
    assert not value['production_qualified'] and not value['native_package_adoption_complete']
    assert not value['historical_evidence_reclassified']
    assert len(value['geometry_records']) == 5 and len(value['operator_records']) == 2
    assert all(r['centered_geometry_byte_identical'] for r in value['geometry_records'])
    for record in value['operator_records']:
        assert len(record['translated_response_sha256']) == 5
        assert len(set(record['translated_response_sha256'])) == 1
        assert record['all_translations_byte_identical']

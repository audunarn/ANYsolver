"""Prescribed reference inputs retain their independently saved identities."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('core', (None, 'Haswell'))
def test_reference_construction_preserves_frozen_identity_across_blas_dispatch(core):
    root = Path(__file__).resolve().parents[1]
    environment = dict(os.environ)
    if core is None:
        environment.pop('OPENBLAS_CORETYPE', None)
    else:
        environment['OPENBLAS_CORETYPE'] = core
    # A fresh process is necessary: dispatch selection occurs at library load.
    source = r'''
import json
from pathlib import Path
from examples.general_contact_native_curved_material_s3 import analysis
from examples.general_contact_native_curved_material_plane import analysis as plane
data = Path('tests/data')
cases = (
 ('general_contact_native_fibre_s3_plastic_active_v1.checkpoint',
  lambda: analysis(physical_fibres=True, plastic_fibres=True)),
 ('general_contact_native_fibre_s3_plastic_k8e7_anchored_active_v1.checkpoint',
  lambda: analysis(physical_fibres=True, plastic_fibres=True,
                   normal_stiffness_Pa_per_m=8e7,
                   integration_budget_policy='certified_active',
                   root_tangent_enclosure_policy='anchored')),
 ('general_contact_native_curved_s3_v2_active.checkpoint', analysis),
 ('general_contact_native_curved_plane_v7.checkpoint', plane),
)
for filename, build in cases:
    saved = json.loads((data / filename).read_bytes())
    owner = build()
    assert owner.identity == saved['identity'], (filename, owner.identity, saved['identity'])
print(json.dumps({'matched': len(cases)}))
'''
    completed = subprocess.run([sys.executable, '-c', source], cwd=root,
        env=environment, capture_output=True, text=True, timeout=60)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout)['matched'] == 4

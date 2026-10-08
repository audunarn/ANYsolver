"""A zero reference retains useful finite comparison output."""
import json
from pathlib import Path
import runpy

import numpy as np


def test_precontact_saved_field_reports_nullable_relative_errors(tmp_path):
    compare=runpy.run_path(str(Path(__file__).parents[1]/
        'scripts/check_general_contact_oblique_temporal_dev.py'))['compare']
    times=np.array([0.,.0001,.0002])
    source=dict(times_s=times.tolist(),q=np.column_stack((np.zeros(3),-times)).tolist(),
        v=np.column_stack((np.zeros(3),-np.ones(3))).tolist(),plastic_xx=[0.]*3,alpha=[0.]*3)
    path=tmp_path/'precontact.json'
    path.write_text(json.dumps(source),encoding='utf-8')
    report=compare(path)
    assert [report['final_relative_error'][i] for i in (0,2,4,5)]==[None]*4
    assert max(report['maximum_scaled_trajectory_error'])<1.e-10
    # Export cannot contain a NaN in place of an undefined relative error.
    json.dumps(report,allow_nan=False)

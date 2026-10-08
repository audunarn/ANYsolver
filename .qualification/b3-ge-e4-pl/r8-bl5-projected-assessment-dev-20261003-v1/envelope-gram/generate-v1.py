"""Write an additive orchestration seam, preserving frozen common sources."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
old = (ROOT/'scripts/r8_bl5_sparse_envelope_kernel_dev.py').read_text()
body = old[old.index('def assess(case,owner,output'):old.index("        backend,order=factor_pattern(representative,budget=PROOF_BUDGET)")]
body = body.replace("def assess(case,owner,output,*,stationary_bound='sum',precision=50):",
    "def prepare(case,owner,output,*,wheel,site):\n    stationary_bound,precision='incidence',50")
body = body.replace("summary,report['input_binding']=bind(case,owner);save('BOUND_SAVED_INSTALLED_OWNER')",
    "summary,report['input_binding']=native.frozen_owner(case,owner)\n        native.installed_graph(site,wheel,summary);save('BOUND_SAVED_INSTALLED_OWNER')")
body = body.replace("'r8_bl5_projected_envelope_owner_dev.py')", "'r8_bl5_projected_envelope_owner_dev.py',\n            'r8_bl5_sparse_envelope_kernel_dev.py','r8_bl5_projected_native_beta_dev.py',\n            'r8_bl5_sparse_gram_margin_dev.py','r8_bl5_sparse_factor_residual_dev.py')")
body = body.replace("'exact saved", "'exact saved")
body = body.replace("store_sparse(arrays,'A_representative',representative);save('COMPLETE_MECHANICAL_ERROR_BOUND')",
    "store_sparse(arrays,'A_representative',representative)\n        report['status']='PREPARED_MECHANICAL_KERNEL'\n        save('COMPLETE_MECHANICAL_ERROR_BOUND')\n        return report")
body += """    except BaseException as error:
        report.update(status='FAILED_SPARSE_ENVELOPE_PREPARATION',failure=dict(type=type(error).__name__,message=str(error)))
        try:save('FAILED')
        except BaseException as recording_error:error.add_note('Recording also failed: '+repr(recording_error))
        raise
"""
header = '''"""Additive saved-envelope preparation and fixed-target Gram assessment.

Frozen common sources remain unchanged. No product solve or mechanical change.
"""
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_info

from scripts import r8_bl5_projected_native_beta_dev as native
from scripts import r8_bl5_sparse_kernel_saved_dev as bound
from scripts.r8_bl5_sparse_envelope_kernel_dev import (
    ROOT, RAW, INPUT_BUDGET, GRAPH_BUDGET, LOCAL_COLUMN_LIMIT, PROOF_BUDGET as OLD_PROOF_BUDGET,
    require, sha, partition, stationary, support_pivots, stationary_incidence_error, store_sparse,
)
from scripts._b3_e4_f03_sparse_certificate import check_arithmetic
from scripts.r8_bl5_sparse_kernel_interval_dev import down, up, sum_up
from scripts.r8_bl5_sparse_gram_margin_dev import certify_gram_margin
from scripts.r8_bl5_sparse_factor_residual_dev import _own, _ResourceRefusal

IDENTITY = 'BL5_SAVED_ENVELOPE_PREPARED_FIXED_SHIFT_GRAM_DEV_V1'
PROOF_BUDGET = replace(OLD_PROOF_BUDGET, max_workspace_bytes=2*1024**3)


'''
(ROOT/'scripts/r8_bl5_envelope_gram_dev.py').write_text(header+body, newline='\n')

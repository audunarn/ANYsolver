"""Balanced two-pair timing of the actual three-use candidate pattern only."""
from pathlib import Path
from hashlib import sha256
import json,os,sys,time,statistics
import numpy as np
ROOT=Path('C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001')
sys.path.insert(0,str(ROOT/'tests'))
from test_general_contact_native_curved_s3_static import _analysis
from anysolver._ge_beam3_p5_seeded.core import canonical

def test_balanced_saved_pose_candidate_pattern():
    owner=_analysis(physical_fibres=True,plastic_fibres=True)
    raw=(ROOT/'tests/data/general_contact_native_fibre_s3_plastic_active_v1.checkpoint').read_bytes()
    state,_=owner._restore(raw,sha256(raw).hexdigest());m=state.mechanical;u=state.shell_displacement
    values=[];reference=None
    with owner.context.operation(None):
        for enabled in (False,True,True,False):
            owner._begin_candidate_context(None)
            owner._contact_reuse_enabled=enabled
            pair_before=owner.pair_evaluations;hits_before=owner.contact_reuse_hits
            started=time.perf_counter()
            try:
                admission=owner._contact(m,u)
                first=owner._assemble(m,u,1.,owner.initial.native_histories)
                second=owner._assemble(m,u,1.,owner.initial.native_histories)
                elapsed=time.perf_counter()-started
                if reference is None:reference=first
                for actual in (first,second):
                    np.testing.assert_array_equal(actual[0],reference[0])
                    np.testing.assert_array_equal(actual[1],reference[1])
                    assert actual[2]==reference[2]
                    assert canonical(actual[-1].contact.to_dict())==canonical(reference[-1].contact.to_dict())
                values.append(dict(reuse=enabled,elapsed_s=elapsed,
                    pair_evaluations=owner.pair_evaluations-pair_before,
                    hits=owner.contact_reuse_hits-hits_before))
            finally:owner._end_candidate_context()
    medians={str(flag):statistics.median(r['elapsed_s'] for r in values if r['reuse']==flag) for flag in (False,True)}
    Path(os.environ['CONTACT_APP_RESULT_RECORD']+'-reuse-timing.json').write_text(json.dumps(dict(
        scope='three-use saved-pose admission/assembly pattern; no complete solve speedup claim',
        runs=values,median_s=medians,relative_time_reduction=1-medians['True']/medians['False']),indent=2))
    assert all(r['pair_evaluations']==(1 if r['reuse'] else 3) for r in values)
    assert all(r['hits']==(2 if r['reuse'] else 0) for r in values)

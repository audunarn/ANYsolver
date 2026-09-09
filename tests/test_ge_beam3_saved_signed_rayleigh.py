"""Read-only exact audit of all nineteen historical scalar discrepancies."""
import json
from pathlib import Path
from hashlib import sha256
from fractions import Fraction
import pytest
from docs.reference_cases.ge_beam3_saved_signed_rayleigh import action,compare,vector
from test_ge_beam3_schur_line_program import save

CURRENT=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-paired-consumers-a9430a2-20260908')
OLD=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-internal-secant-6b79200-20260908')
CASES={4:(0,13,15,21),8:(0,2,4,5,6,7,8,10,12,13,14,16,17,18,19)}


def test_exact_action_cancellation(tmp_path):
    a=action([[1e16,1.,-1e16]],[Fraction(1)]*3)
    assert a==[Fraction(1)]
    assert vector([[1.]],[[2.**-54]])==[Fraction(1)+Fraction(1,2**54)]
    save(tmp_path/'unit.json',dict(exact_cancellation=True,explicit_low_preserved=True))


def read_bound(path,root,manifest,nested=False):
    raw=path.read_bytes();bound=manifest[path.relative_to(root).as_posix()]
    expected=[bound['bytes'],bound['sha256'].upper()] if nested else bound
    assert [len(raw),sha256(raw).hexdigest().upper()]==expected
    return json.loads(raw)


@pytest.mark.parametrize('macros',(4,8))
def test_saved_discrepancy_decomposition(macros,tmp_path):
    current_raw=(CURRENT/'archive-manifest.json').read_bytes()
    old_raw=(OLD/'archive-manifest.json').read_bytes()
    assert len(current_raw)==21528 and sha256(current_raw).hexdigest().upper()=='043AD5A73674CFC17A7F05E0006925D56B239469687E2D67B1ADB94F3C0EA70A'
    assert len(old_raw)==113732 and sha256(old_raw).hexdigest().upper()=='BD870FBFCC67E1A4DF5ADEED02707381568E6C990D38A6ED714083D1C6DABC6A'
    current_manifest=json.loads(current_raw);old_manifest=json.loads(old_raw)['files']
    rows=[]
    for point in CASES[macros]:
        name='point-%02d.json'%point
        current_path=next((CURRENT/'runs'/str(macros)/'pytest').rglob(name))
        old_path=next((OLD/'runs'/('rehearsal-n%d'%macros)/'pytest').rglob(name))
        current=read_bound(current_path,CURRENT,current_manifest)
        old=read_bound(old_path,OLD,old_manifest,True)
        for key in ('state_sha256','compression','equilibrium_error'):
            assert current['row'][key]==old['row'][key]
        print(dict(stage='exact-saved-Rayleigh',macros=macros,point=point),flush=True)
        result=compare(current,old,macros)
        save(tmp_path/('decomposition-%02d.json'%point),result)
        assert abs(result['normalized_parts']['new_extraction'])<=1e-11
        # Independent original-factor energy on the two saved vectors must
        # agree; this does not assert old scalar eigenvalues are identical.
        assert abs(result['normalized_parts']['vector_quotient'])<=1e-11
        rows.append(dict(point=point,parts=result['normalized_parts']))
    save(tmp_path/'assessment.json',dict(macros=macros,rows=rows,production_qualified=False,
        historical_scalar_equivalence_reclassified=False,independent_review='PENDING'))

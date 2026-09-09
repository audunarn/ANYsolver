"""Diagnose supplied-factor versus solver covariance; never waive the failure."""
from decimal import Decimal as D, localcontext
import hashlib
import json
import os
from pathlib import Path
import numpy as np
import pytest
from docs.reference_cases.ge_beam3_decimal_mode_audit import factor_modes


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')


@pytest.mark.parametrize('variant',['per-node','batched'])
def test_separate_decimal_audit_of_captured_reference_factors(variant,tmp_path):
    supplied=os.environ.get('ANY_GE_BEAM3_RUNTIME_DIAGNOSTIC')
    if supplied is None: pytest.skip('explicit captured diagnostic input required')
    root=Path(supplied); values=[]; rows=[]
    for case in ('E','GENERAL'):
        path=root/(variant+'-'+case+'.npz'); raw=path.read_bytes()
        with np.load(path,allow_pickle=False) as data:
            arrays={k:data[k].copy() for k in data.files}
        assert np.count_nonzero(arrays['geometric'])==0
        results=[]
        for digits in (60,90):
            print(variant+' '+case+' Decimal '+str(digits)+' started',flush=True)
            result=factor_modes(arrays['factor'].tolist(),arrays['kinetic'].tolist(),
                arrays['free'].tolist(),arrays['algebraic'].tolist(),digits=digits)
            with (tmp_path/(case+'-'+str(digits)+'.json')).open('xb') as stream: stream.write(canonical(result))
            results.append(result)
        with localcontext() as context:
            context.prec=100
            assert max(abs(D(a)-D(b)) for a,b in zip(results[0]['eigenvalues'][:6],results[1]['eigenvalues'][:6]))<D('1e-30')
            for j in range(6):
                left=[D(row[j]) for row in results[0]['full_modes']]
                right=[D(row[j]) for row in results[1]['full_modes']]
                index=max(range(len(left)),key=lambda i:abs(left[i]))
                sign=D(1) if left[index]*right[index]>=0 else D(-1)
                assert max(abs(a-sign*b) for a,b in zip(left,right))<D('1e-30')
        audited=np.array(results[1]['full_modes'],dtype=float)[:,:6]
        roots=np.array(results[1]['eigenvalues'],dtype=float)[:6]
        correlation=arrays['modes'].T@arrays['mass']@audited
        row=dict(case=case,input_bytes=len(raw),input_sha256=hashlib.sha256(raw).hexdigest(),
            native_audit_correlation_error=(np.abs(correlation)-np.eye(6)).tolist(),
            maximum_native_audit_correlation_error=float(np.max(np.abs(np.abs(correlation)-np.eye(6)))),
            relative_eigenvalue_error=((arrays['eigenvalues']-roots)/roots).tolist())
        rows.append(row); values.append((audited,arrays['mass'],arrays['rotation']))
        # Save before adjudicating: a failing diagnostic never loses its inputs.
        with (tmp_path/(case+'-comparison.json')).open('xb') as stream: stream.write(canonical(row))
        np.testing.assert_allclose(roots,arrays['eigenvalues'],rtol=1e-11,atol=1e-11)
        np.testing.assert_allclose(np.abs(correlation),np.eye(6),rtol=1e-11,atol=1e-11)
    a,b=values; transform=np.kron(np.eye(14),b[2])
    cross=(transform@a[0]).T@b[1]@b[0]
    record=dict(variant=variant,cases=rows,audited_covariance_error=(np.abs(cross)-np.eye(6)).tolist(),
        maximum_audited_covariance_error=float(np.max(np.abs(np.abs(cross)-np.eye(6)))),
        qualification_passed=False,independent_review='PENDING',certified_intervals=False)
    with (tmp_path/'audit.json').open('xb') as stream:stream.write(canonical(record))
    print(canonical(record).decode(),flush=True)

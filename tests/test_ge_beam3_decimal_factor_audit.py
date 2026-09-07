"""Small numerical audit, not mechanics qualification or independent review."""
import importlib.util
from pathlib import Path
import json
from decimal import Decimal
import numpy as np
import pytest

PATH=Path(__file__).parents[1]/'docs/reference_cases/ge_beam3_decimal_factor_audit.py'
spec=importlib.util.spec_from_file_location('decimal_audit',PATH)
audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)


def test_extreme_diagonal_and_massless_trace():
    f=[[1e12,0.,0.],[0.,2.,1.],[0.,0.,1.]]; b=[[1.,0.,0.],[0.,1.,0.]]
    roots=audit.factor_roots(f,b,[0,1,2],[2],digits=60)
    assert abs(Decimal(roots[0])-2)<Decimal('1e-35')
    assert Decimal(roots[1])==Decimal(10)**24


def test_supplied_curved_factors_two_precisions(tmp_path):
    from test_ge_beam3_seeded_reduction_diagnostic import test_capture_reference_factor_reduction
    # Fresh small inputs. The original failed packet remains separately
    # archived; this portable unit does not claim to rerun that authority.
    root=tmp_path/'inputs'; root.mkdir()
    test_capture_reference_factor_reduction(root)
    outputs={}
    for case in ['E','R90']:
        with np.load(root/(case+'.npz')) as p:
            inputs=(p['factor'].tolist(),p['kinetic'].tolist(),p['free'].tolist(),p['algebraic'].tolist())
        values={str(d):audit.factor_roots(*inputs,digits=d)[:6] for d in (60,90)}
        assert max(abs(Decimal(a)-Decimal(b)) for a,b in zip(values['60'],values['90']))<Decimal('1e-30')
        outputs[case]=values
    with (tmp_path/'audit.json').open('x') as out: json.dump(outputs,out,sort_keys=True)

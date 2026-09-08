"""Exact-key, per-solve reference cache; never a mechanics approximation."""
import numpy as np
import pytest
from docs.reference_cases.ge_beam3_continuum_frequency_shooting import _cached_scalar
from test_ge_beam3_schur_line_program import save

@pytest.mark.parametrize('kind',('repeat','adjacent','failure','guard','isolated','nonfinite'))
def test_reference_determinant_cache(kind,tmp_path):
    calls=[];checks=[]
    def raw(x):
        calls.append(x)
        if kind=='failure' and len(calls)==1:raise ValueError('first evaluation failed')
        return x*x
    def check():
        checks.append(True)
        if kind=='guard' and len(checks)==2:raise RuntimeError('resource deadline')
    f=_cached_scalar(raw,check)
    if kind=='repeat':
        assert f(1.25)==f(np.float64(1.25))==1.5625
        assert calls==[1.25] and len(checks)==2
    elif kind=='adjacent':
        x=1.;y=float(np.nextafter(x,2.))
        assert f(x)==x*x and f(y)==y*y and calls==[x,y]
    elif kind=='failure':
        with pytest.raises(ValueError):f(2.)
        assert f(2.)==4. and calls==[2.,2.]
    elif kind=='guard':
        assert f(2.)==4.
        with pytest.raises(RuntimeError):f(2.)
        assert calls==[2.] and len(checks)==2
    elif kind=='isolated':
        other=_cached_scalar(raw,check)
        assert f(2.)==other(2.)==4. and calls==[2.,2.]
    else:
        with pytest.raises(ValueError):f(np.inf)
        with pytest.raises(ValueError):_cached_scalar(lambda x:np.nan,lambda:None)(1.)
        assert calls==[]
    save(tmp_path/'cache.json',dict(kind=kind,calls=calls,checks=len(checks),passed=True))

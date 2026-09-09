"""Separate continuum equation, sensitivity and fixed-family resolution checks."""
from dataclasses import asdict
import ast
from pathlib import Path
import numpy as np
import pytest
from docs.reference_cases import ge_beam3_uniform_arch_reference as ref
from test_ge_beam3_schur_line_program import save


def test_equation_derivatives_and_reference_balance(tmp_path):
    t=np.array([-.93,-.51,-.07]);y=np.array([t,.1*(1-t*t),[.12,.3,-.15],[.001,-.003,.002]])
    p=np.array([-.001,.0003]);a,b=ref.derivatives(t,y,p);errors=[]
    for i in range(4):
        changed=y.astype(complex);changed[i]+=1e-30j
        errors.append(float(np.max(np.abs(ref.equations(t,changed,p).imag/1e-30-a[:,i])/(1+np.abs(a[:,i])))))
    for i in range(2):
        changed=p.astype(complex);changed[i]+=1e-30j
        errors.append(float(np.max(np.abs(ref.equations(t,y,changed).imag/1e-30-b[:,i])/(1+np.abs(b[:,i])))))
    primitive=ref.primitive(t.astype(complex)+1e-30j).imag/1e-30
    errors.append(float(np.max(np.abs(primitive-np.sqrt(1+(2*ref.HEIGHT*t)**2)))))
    assert max(errors)<=1e-11
    virgin=np.array([t,ref.HEIGHT*(1-t*t),np.arctan(-2*ref.HEIGHT*t),np.zeros(3)])
    expected=np.array([np.ones(3),-2*ref.HEIGHT*t,-2*ref.HEIGHT/(1+(2*ref.HEIGHT*t)**2),np.zeros(3)])
    assert np.max(np.abs(ref.equations(t,virgin,np.zeros(2))-expected))<=1e-11
    save(tmp_path/'equations.json',dict(errors=errors,stress_free_reference=True,production_qualified=False))


def test_fixed_family_resolution(tmp_path):
    paths=[]
    for profile in ('BVP7','BVP9'):
        previous=None;rows=[]
        for drop in ref.DROPS:
            previous=ref.solve(drop,previous=previous,profile=profile);rows.append(asdict(previous))
        save(tmp_path/(profile+'.json'),dict(rows=rows));paths.append(rows)
    errors=[]
    for coarse,fine in zip(*paths):
        errors.append(max(abs(coarse[key]-fine[key])/max(1.,abs(fine[key])) for key in ('density','slope')))
    assert max(errors)<=1e-5
    save(tmp_path/'resolution.json',dict(errors=errors,rows=[dict(drop=r['drop'],density=r['density'],slope=r['slope']) for r in paths[1]],
        full_spatial_stability=False,production_qualified=False))


@pytest.mark.parametrize('drop',[True,-.1,.201,float('nan'),float('inf'),1])
def test_rejected_drop(drop):
    with pytest.raises(ValueError):ref.solve(drop)


def test_reference_import_boundary():
    tree=ast.parse(Path(ref.__file__).read_text());names=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):names.extend(n.name for n in node.names)
        if isinstance(node,ast.ImportFrom):names.append(node.module)
    assert set(names)=={'dataclasses','time','numpy','scipy.integrate'}

"""Nonclassifying saved-pencil inspection and fail-closed data tests."""
import ast
from copy import deepcopy
from pathlib import Path
import pytest
from docs.reference_cases import ge_beam3_saved_pencil_reproduction as diagnostic

def save(path,value):
    with path.open('xb') as stream:stream.write(diagnostic.canonical(value))

def toy():
    return (dict(stiffness=[[2.,0.,1.],[0.,4.,0.],[1.,0.,1.]],
        mass=[[1.,0.,0.],[0.,1.,0.],[0.,0.,0.]],free_dofs=[0,1,2],algebraic_dofs=[2]),
        dict(eigenvalues=[1.,4.],full_modes=[[1.,0.],[0.,1.],[-1.,0.]],
             dynamic_map=[[1.,0.],[0.,1.],[-1.,0.]]))

def test_exact_small_saved_pencil(tmp_path):
    packet,old=toy();before=deepcopy((packet,old))
    report,_=diagnostic.inspect(packet,old,count=2)
    assert (packet,old)==before and report['reconstructed_map_exactly_equal']
    for row in report['variants'].values():
        assert row['original_1e11_reproduction_criterion_passed']
        assert row['normalized_full_pencil_residual']<=1e-11
        assert row['mass_orthogonality_error']<=1e-11
    save(tmp_path/'toy.json',report)

@pytest.mark.parametrize('kind',('asymmetry','mass','slots','count','nonfinite','saved-map'))
def test_rejects_mutated_pencil(kind,tmp_path):
    packet,old=toy();count=2
    if kind=='asymmetry':packet['stiffness'][0][1]=1.
    if kind=='mass':packet['mass'][2][2]=.1
    if kind=='slots':packet['free_dofs']=[0,1,99]
    if kind=='count':count=0
    if kind=='nonfinite':packet['stiffness'][0][0]=float('nan')
    if kind=='saved-map':old['dynamic_map']=[[1.]]
    with pytest.raises(ValueError):diagnostic.inspect(packet,old,count=count)
    save(tmp_path/'rejection.json',dict(kind=kind,rejected=True))

def test_diagnostic_has_no_production_imports():
    tree=ast.parse(Path(diagnostic.__file__).read_text());imports=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):imports.extend(a.name for a in node.names)
        if isinstance(node,ast.ImportFrom):imports.append(node.module)
    assert set(imports)<={'hashlib','json','pathlib','time','numpy','scipy'}

def test_registered_saved_pencil_observations(tmp_path):
    result=diagnostic.registered_diagnostic()
    save(tmp_path/'observations.json',result)
    # These validate an eigenpair diagnostic, not the former forward-value
    # assertion or the old six-mode engineering comparison.
    assert result['reconstructed_map_exactly_equal']
    assert result['saved_normalized_residual']<=1e-11
    for variant in result['variants'].values():
        assert variant['normalized_full_pencil_residual']<=1e-11
        assert variant['mass_orthogonality_error']<=1e-11
    assert not result['old_gate_classification_changed']
    assert not result['production_qualified']

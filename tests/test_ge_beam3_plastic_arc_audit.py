"""Analytic station fixture and adversarial audit tests; no beam solve here."""
import ast
from copy import deepcopy
from pathlib import Path
import pytest
from docs.reference_cases import ge_beam3_plastic_arc_audit as audit
from docs.reference_cases.ge_beam3_plastic_arc_fixture import fixture

def parts(values):
    return [list(values), [0.]*len(values)]

def example():
    # Identity C/M, uniaxial e=.05, Y=.025, H=.6. Analytic radial return:
    # s=11/320, plastic increment=1/64; longitudinal tangent3/8,
    # transverse tangent11/16. These values are not produced by either backend.
    section = dict(elastic=[[float(i==j) for j in range(6)] for i in range(6)],
        metric=[[float(i==j) for j in range(6)] for i in range(6)], yield_force=.025, hardening=.6)
    s = 11./320.; dp = 1./64.; elastic = s*s/2.; stored = elastic+.6*dp*dp/2.
    origin = dict(section_identity='a'*64,plastic=[[0.,0.] for _ in range(6)],accumulated=[0.,0.])
    history = deepcopy(origin); history['plastic'][0][0] = dp; history['accumulated'][0] = dp
    material = dict(strain=parts([.05,0.,0.,0.,0.,0.]), resultants=parts([s,0.,0.,0.,0.,0.]),
        dual_potential=parts([.05*s-(stored+.025*dp)]), incremental_potential=parts([stored+.025*dp]),
        stored_energy=parts([stored]), dissipation=parts([.025*dp]), plastic_increment=parts([dp]),
        branch='PLASTIC', recovery_policy='RESULTANT_LEVEL_ONLY_NO_FIBRE_STRESSES_SUPPLIED')
    tangent = [[(3./8. if i==0 else 11./16.) if i==j else 0. for j in range(6)] for i in range(6)]
    data = dict(material=material, tangent=[tangent,[[0.]*6 for _ in range(6)]], tangent_origin=deepcopy(origin),
        tangent_strain=deepcopy(material['strain']), tangent_resultants=deepcopy(material['resultants']))
    return section, data, origin, history

def test_analytic_active_material():
    section, data, origin, history = example()
    before = audit.canonical([data,origin,history])
    result = audit.station(section,data,origin,history)
    assert result['active'] is True and result['branch']=='PLASTIC' and result['maximum_error']<1e-14
    assert audit.canonical([data,origin,history]) == before

@pytest.mark.parametrize('kind',('resultant','strain','history','accumulated','origin','branch','dissipation',
    'increment','tangent','tangent_origin','tangent_strain','dual','nonfinite','bool','extra','shape'))
def test_station_mutations(kind):
    section, data, origin, history = example(); m=data['material']
    if kind=='resultant': m['resultants'][0][0]+=.01
    elif kind=='strain': m['strain'][0][0]+=.01
    elif kind=='history': history['plastic'][0][0]+=.01
    elif kind=='accumulated': history['accumulated'][0]+=.01
    elif kind=='origin': origin['plastic'][0][0]+=.01; data['tangent_origin']=deepcopy(origin)
    elif kind=='branch': m['branch']='ELASTIC'
    elif kind=='dissipation': m['dissipation'][0][0]=-.01
    elif kind=='increment': m['plastic_increment'][0][0]=-.01
    elif kind=='tangent': data['tangent'][0][0][0]+=.1
    elif kind=='tangent_origin': data['tangent_origin']['accumulated'][0]+=.01
    elif kind=='tangent_strain': data['tangent_strain'][0][0]+=.01
    elif kind=='dual': m['dual_potential'][0][0]+=.01
    elif kind=='nonfinite': m['strain'][0][0]=float('nan')
    elif kind=='bool': m['strain'][0][1]=False
    elif kind=='extra': data['unexpected']=True
    else: m['resultants']=[[0.]]
    with pytest.raises(ValueError): audit.station(section,data,origin,history)

@pytest.mark.parametrize('n',(1,2))
def test_fixture_extent_and_copied_authority(n):
    f=fixture(n); raw=audit.canonical(f)
    assert len(f['points'])==2*n+1 and len(f['connectivity'])==n
    assert f['force'][0]==2*n+1 and f['steps']==[.05,.05,.05] and f['yield_force']==.025
    f['elastic'][0][0]=123.
    assert audit.canonical(fixture(n))==raw

@pytest.mark.parametrize('n',(True,0,3))
def test_unregistered_mesh(n):
    with pytest.raises(ValueError): fixture(n)

def test_checker_import_boundary():
    root=Path(__file__).resolve().parents[1]
    modules=('ge_beam3_plastic_arc_audit','ge_beam3_plastic_arc_fixture','ge_beam3_generalized_ellipsoid_oracle','ge_beam3_retained_prestress_protocol')
    allowed={'hashlib','math','decimal','time','pathlib','stat','json','copy',
        'docs.reference_cases.ge_beam3_generalized_ellipsoid_oracle',
        'docs.reference_cases.ge_beam3_retained_prestress_protocol','docs.reference_cases.ge_beam3_plastic_arc_fixture'}
    for module in modules:
        tree=ast.parse((root/'docs/reference_cases'/f'{module}.py').read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom): assert node.module in allowed
            elif isinstance(node,ast.Import): assert all(v.name in allowed for v in node.names)
            elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name): assert node.func.id not in ('eval','exec','__import__')

@pytest.mark.parametrize('raw',(b'{"x":1,"x":2}\n',b'{"x":NaN}\n',b'{ "x":1}\n'))
def test_strict_serialization(raw):
    with pytest.raises(ValueError): audit.strict_bytes(raw)

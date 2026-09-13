"""Six frozen exact affine recovery nodes; reviewed bounded runner only."""
import ast
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import pytest

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/'docs/reference_cases'
sys.path.insert(0,str(REFERENCE))
from ge_beam3_q4_exact_field import Field
import ge_beam3_q4_affine_recovery_producer as producer

SCIENTIFIC_RECORDS=[]
FIXTURES=('AFFINE_Q4_SQUARE','AFFINE_Q4_RECTANGLE','AFFINE_Q4_RHOMBUS')
SOURCE_BINDINGS={
 'src/anysolver/e4_pl_element.py':'7fc46a18046e043512a5fb2c3f61ed0b95b834e4dde764f63c500a885e87ea38',
 'src/anysolver/elements.py':'f8c59792947a3c9b84416c61a4d9db98e42926d1bf21e74e736afbf6a9a88b37',
 'src/anysolver/_ge_beam3_g3c_local_shell.py':'69d9f27a96ed7e9a5959a42a081eeafbbe72021de6e4da1f91355c5fb3850f10',
 'docs/GE_BEAM3_G3C_MATRIX_SHELL_CONTRACT.md':'59a09dc7db6256a145520ae7b4f2d325dee1abca5d5b5c381a7ada57a2ad92fd',
 'docs/GE_BEAM3_G3C_MO16_SOURCE_ASSESSMENT.md':'e6b702fba5c32ef22537a137fc150fa54b63028c6910df96c5c5f0c6a722026e',
 'docs/reference_cases/ge_beam3_g3c_fixtures_v1.json':'d5fecc80c3203ac7d191b4031d64bf35c56d2900066cb01fc1dfa4276d24c006',
 'src/anysolver/_ge_beam3_g3c_definition.py':'4b46b870fec010e3378df83c374d763f858d8f25820c14f9704dc6f0a656f0c2'}


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode('ascii')


def strict(raw):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('duplicate key')
            result[k]=v
        return result
    def bad(value):raise ValueError('nonfinite '+value)
    result=json.loads(raw.decode('ascii'),object_pairs_hook=pairs,parse_constant=bad)
    if canonical(result)!=raw:raise ValueError('noncanonical JSON')
    return result


def read(path):
    for item in (path,*path.parents):
        info=item.lstat()
        if getattr(info,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT:raise ValueError('reparse evidence')
    if not path.is_file():raise ValueError('regular evidence required')
    return path.read_bytes()


def write(path,value):
    raw=canonical(value)
    with path.open('xb') as stream:stream.write(raw)
    if read(path)!=raw:raise ValueError('exclusive bytes differ')
    return raw


def test_affine_exact_arithmetic_and_schema():
    roots=[Field.root(p) for p in (2,3,5)]
    for r,p in zip(roots,(2,3,5)):
        assert r*r==p and r*r.inverse()==r.inverse()*r==1
    a=1+roots[0]+roots[1]*roots[2];b=2-roots[2];c=Fraction(3,7)+roots[1]
    assert a*b==b*a and (a*b)*c==a*(b*c) and (a+b)*c==a*c+b*c
    assert a*a.inverse()==a.inverse()*a==1 and a-a==0
    assert strict(canonical({'coefficients':a.coefficients()}))=={'coefficients':a.coefficients()}
    for raw in (b'{"a":1,"a":2}\n',b'{"a":NaN}\n',b'{"a":Infinity}\n',b'{"a":1e999}\n',b'{ "a":1}\n'):
        with pytest.raises(ValueError):strict(raw)
    SCIENTIFIC_RECORDS.append(dict(test='affine_exact_arithmetic_and_schema',exact_arithmetic=True,negative_json_cases=5))


def test_affine_source_and_representation_boundaries():
    for path,digest in SOURCE_BINDINGS.items():
        raw=read(ROOT/path).replace(b'\r\n',b'\n')
        assert sha256(raw).hexdigest()==digest and sha256(raw+b'\n').hexdigest()!=digest
    permitted={'fractions','itertools','math','json','ge_beam3_q4_exact_field',
               'ge_beam3_q4_recovery_coefficient_producer','ge_beam3_q4_recovery_coefficient_checker'}
    for name in ('ge_beam3_q4_affine_recovery_producer.py','ge_beam3_q4_affine_recovery_checker.py'):
        tree=ast.parse(read(REFERENCE/name))
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):assert all(a.name in permitted for a in node.names)
            if isinstance(node,ast.ImportFrom):assert node.level==0 and node.module in permitted
            if isinstance(node,ast.Constant):assert not isinstance(node.value,float)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                assert node.func.id not in ('eval','exec','compile','__import__','float')
        imports={a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
        imports|={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        if 'checker' in name:assert 'ge_beam3_q4_recovery_coefficient_producer' not in imports
        else:assert 'ge_beam3_q4_recovery_coefficient_checker' not in imports
    SCIENTIFIC_RECORDS.append(dict(test='affine_source_and_representation_boundaries',source_bindings=7,
        producer_checker_independent_imports=True,representation_id='GE_BEAM3_Q4_AFFINE_STATION_RECOVERY_64_V1',
        physical_recovery_qualified=False,full_g3c_qualified=False))


def fixture_proof(fixture):
    value=os.environ.get('BEAM_QUALIFICATION_OUTPUT')
    if not value or not Path(value).is_absolute():raise ValueError('bounded output required')
    out=Path(value);lease=strict(read(out/'lease.json'))
    if lease['gate']!='q4-affine-exact' or lease['lane']!='core':raise ValueError('affine gate required')
    target=out/fixture;target.mkdir(exist_ok=False)
    proof=producer.audit(fixture,lambda x:print('AFFINE '+fixture+' '+x,flush=True))
    raw=write(target/'proof.json',proof);digest=sha256(raw).hexdigest()
    processes=[];streams=[]
    try:
        for replica in ('1','2'):
            stream=(target/('checker'+replica+'.log')).open('xb');streams.append(stream)
            processes.append(subprocess.Popen([sys.executable,'-I','-S','-B','-u',
                str(ROOT/'scripts/run_ge_beam3_qualification.py'),'--q4-affine-checker',str(out),fixture,replica,digest],
                cwd=ROOT,env=os.environ.copy(),stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT))
        deadline=time.monotonic()+600
        while any(p.poll() is None for p in processes):
            if any(p.poll() not in (None,0) for p in processes):raise ValueError('affine checker failed')
            if time.monotonic()>=deadline:raise TimeoutError('affine checker wait ceiling')
            time.sleep(1)
        if any(p.returncode!=0 for p in processes):raise ValueError('checker nonzero exit')
    finally:
        for p in processes:
            if p.poll() is None:p.terminate()
        for p in processes:p.wait(timeout=10)
        for stream in streams:stream.close()
    first=read(target/'checker1.json');second=read(target/'checker2.json')
    if first!=second:raise ValueError('checker replica disagreement')
    verification=dict(fixture_id=fixture,coefficient_count=7125,nonzero_count=proof['nonzero_count'],
        first_nonzero=proof['first_nonzero'],independently_verified=True,physical_recovery_qualified=False,full_g3c_qualified=False)
    expected=dict(schema='GE_BEAM3_Q4_AFFINE_CHECKER_RESULT_V1',candidate=lease['candidate'],
        inputs_sha256=sha256(canonical(lease['inputs'])).hexdigest(),proof_sha256=digest,verification=verification)
    if canonical(strict(first))!=canonical(expected) or read(target/'proof.json')!=raw:raise ValueError('checker/proof authority')
    SCIENTIFIC_RECORDS.append(dict(test=fixture,proof=proof,verification=verification,checker_replicas_byte_identical=True))


def test_affine_square_chart_polynomial():fixture_proof(FIXTURES[0])
def test_affine_rectangle_chart_polynomial():fixture_proof(FIXTURES[1])
def test_affine_rhombus_chart_polynomial():fixture_proof(FIXTURES[2])


def test_affine_stationary_schur_and_mutations(monkeypatch):
    from ge_beam3_q4_affine_recovery_checker import reconstruct,verify_against_reconstruction
    rows=[];out=Path(os.environ['BEAM_QUALIFICATION_OUTPUT'])
    for fixture in FIXTURES:
        expected=canonical(reconstruct(fixture,lambda s:print('AFFINE mutation '+fixture+' '+s,flush=True)))
        expected_sha=sha256(expected).hexdigest()
        original=read(out/fixture/'proof.json')
        verify_against_reconstruction(strict(original),strict(expected))
        results=[]
        def verify_bound(raw,digest):
            if sha256(raw).hexdigest()!=digest:raise ValueError('bound hash mismatch')
            return verify_against_reconstruction(strict(raw),strict(expected))
        def increment(value):value[0]=str(Fraction(value[0])+1)
        # Actual assembly alterations; baseline reconstruction is protected once perfixture.
        hooks={n:getattr(producer,n) for n in ('_frames','_geometry','_nonlinear_station_work','_nonlinear_coefficients',
                    '_constraints','_station_saddle','_combine_schur_terms')}
        def frames(nodes):
            mixed,centre=hooks['_frames'](nodes)
            return [[r[1],-r[0],r[2]] for r in mixed],centre
        def weight(*a):
            n,dx,dy,w,j=hooks['_geometry'](*a);return n,dx,dy,2*w,j
        def mixed_map(M,*a):
            M[0][0]+=1
            return hooks['_nonlinear_station_work'](M,*a)
        def nonlinear(*a):return [[2*x for x in r] for r in hooks['_nonlinear_coefficients'](*a)]
        def constraint(*a):
            C,R,p,Z=hooks['_constraints'](*a);C[0][0]+=1;return C,R,p,Z
        def nullspace(*a):
            C,R,p,Z=hooks['_constraints'](*a);Z[0][0]+=1;return C,R,p,Z
        def coupling(*a):
            B,I,C,X=hooks['_station_saddle'](*a);C=[[-v for v in r] for r in C];return B,I,C,X
        def inverse(*a):
            B,I,C,X=hooks['_station_saddle'](*a);I[0][0]+=1;return B,I,C,X
        cases=[('geometry',None,None),('frame','_frames',frames),('weight','_geometry',weight),
            ('M','_nonlinear_station_work',mixed_map),('n','_nonlinear_coefficients',nonlinear),
            ('constraint','_constraints',constraint),('Z','_constraints',nullspace),
            ('station_coupling_sign','_station_saddle',coupling),('inverse','_station_saddle',inverse),
            ('nonlinear_geometric_term','_combine_schur_terms',lambda material,geometric:material.copy())]
        for name,hook,changed in cases:
            called=[]
            with monkeypatch.context() as patch:
                if hook is None:
                    nodes=producer.FIXTURES[fixture]
                    patch.setitem(producer.FIXTURES,fixture,tuple((str(Fraction(x)+1),y) for x,y in nodes))
                else:
                    def observed(*a,_changed=changed,**kw):called.append(True);return _changed(*a,**kw)
                    patch.setattr(producer,hook,observed)
                try:altered=producer.audit(fixture,lambda s:print('AFFINE mutation '+name+' '+s,flush=True))
                except (ValueError,ArithmeticError) as error:
                    result=dict(id=name,rejection='ASSEMBLY_GUARD',exception_type=type(error).__name__)
                else:
                    with pytest.raises(ValueError,match='independent affine proof mismatch'):
                        verify_against_reconstruction(altered,strict(expected))
                    result=dict(id=name,rejection='INDEPENDENT_CHECKER')
            if hook is not None:assert called
            assert sha256(expected).hexdigest()==expected_sha
            results.append(result)
        for name in ('coefficient','identity','bound_hash'):
            altered=strict(original)
            if name=='coefficient':increment(altered['coefficient_records'][0]['coefficient'])
            elif name=='identity':altered['representation_id']='OLD_RETAINED_35_VARIABLE_SYSTEM'
            raw=canonical(altered);digest=sha256(raw).hexdigest()
            if name=='bound_hash':digest=('0' if digest[0]!='0' else '1')+digest[1:]
            with pytest.raises(ValueError):verify_bound(raw,digest)
            results.append(dict(id=name,rejection='BOUND_HASH' if name=='bound_hash' else 'INDEPENDENT_CHECKER'))
        # Every registered dimension above plus the additional actual geometric-term omission.
        assert len(results)==13 and len({r['id'] for r in results})==13
        assert read(out/fixture/'proof.json')==original and sha256(expected).hexdigest()==expected_sha
        rows.append(dict(fixture_id=fixture,independent_baseline_sha256=expected_sha,baseline_immutable=True,
                         registered_mutation_dimensions=12,additional_geometric_term_omission=True,mutations=results))
    SCIENTIFIC_RECORDS.append(dict(test='affine_stationary_schur_and_mutations',fixtures=rows,
        independent_reconstructions=3,physical_recovery_qualified=False,full_g3c_qualified=False))

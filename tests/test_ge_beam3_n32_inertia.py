import ast
from pathlib import Path
from decimal import Decimal as D,localcontext
import pytest
from docs.reference_cases import ge_beam3_n32_scaled_inertia as scaled
from docs.reference_cases import ge_beam3_n32_energy_inertia as energy
from docs.reference_cases import ge_beam3_n32_inertia_worker as worker
from docs.reference_cases import ge_beam3_scaled_energy_inertia as old
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical

@pytest.mark.parametrize('name,new_name,count',[
    ('ge_beam3_front_aware_inertia','ge_beam3_n32_front_inertia',1),
    ('ge_beam3_scaled_front_inertia','ge_beam3_n32_scaled_inertia',1),
    ('ge_beam3_scaled_energy_inertia','ge_beam3_n32_energy_inertia',4)])
def test_exact_capacity_only_kernel_extension(name,new_name,count):
    root=Path(energy.__file__).parent;a=ast.parse((root/(name+'.py')).read_text());b=ast.parse((root/(new_name+'.py')).read_text());changed=[]
    class Capacity(ast.NodeTransformer):
        def visit_Constant(self,node):
            if type(node.value) is int and node.value in (512,8192):changed.append(node.value);node.value={512:640,8192:12288}[node.value]
            return node
        def visit_ImportFrom(self,node):
            node.module={'docs.reference_cases.ge_beam3_front_aware_inertia':'docs.reference_cases.ge_beam3_n32_front_inertia',
                         'docs.reference_cases.ge_beam3_scaled_front_inertia':'docs.reference_cases.ge_beam3_n32_scaled_inertia'}.get(node.module,node.module)
            return node
    Capacity().visit(a)
    assert len(changed)==count and ast.dump(a)==ast.dump(b)

@pytest.mark.parametrize('digits',(80,100))
def test_full570_known_congruence_preserves_inertia(digits):
    with localcontext() as c:
        c.prec=digits;n=570;diagonal=[(-D(1) if i%7==0 else D(1))*D(10)**(10 if i%2 else -10) for i in range(n)]
        a=[[D(0)]*n for _ in range(n)]
        # Analytically A=L D L^T with unit lower bidiagonal L and L[i,i-1]=1/4.
        for i in range(n):
            a[i][i]=diagonal[i]+(diagonal[i-1]/16 if i else 0)
            if i:a[i][i-1]=a[i-1][i]=diagonal[i-1]/4
        before=[row[:] for row in a];r=scaled.inertia(a)
        assert a==before and r['negative']==sum(x<0 for x in diagonal) and r['positive']==n-r['negative']
        assert sorted(i for p in r['pivot_indices'] for i in p)==list(range(n))
        assert D(r['original_reconstruction_bound'])<=D('1e-60') and r['max_front']<=96

@pytest.mark.parametrize('digits',(80,100))
def test_original_small_energy_result_identical(digits):
    args=([[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],
        [[-2.,0.,1.],[0.,8.,2.],[1.,2.,4.]],[[1.,0.,0.],[0.,2.,0.]],(0,1,2),(2,),(0.,))
    assert canonical(energy.audit(*args,digits=digits))==canonical(old.audit(*args,digits=digits))

@pytest.mark.parametrize('kind',('zero','skew','nonfinite','cancel','fill','capacity'))
def test_unmodified_rejections(kind):
    with localcontext() as c:
        c.prec=80;a=[[D(2),D(1)],[D(1),D(2)]]
        if kind=='zero':a=[[D(0)]]
        elif kind=='skew':a[0][1]=D(0)
        elif kind=='nonfinite':a[0][0]=D('NaN')
        elif kind=='fill':a=[[D(2) if i==j else D(1) for j in range(100)] for i in range(100)]
        elif kind=='capacity':a=[[D(0)]]*641
        def check():
            if kind=='cancel':raise ValueError('cancelled')
        with pytest.raises(ValueError):scaled.inertia(a,check)

@pytest.mark.parametrize('sign',('plus','minus'))
def test_saved_same_state_spectrum_authority(sign,tmp_path):
    r=worker.source(sign);assert len(r['full_modes'][0])==582 and r['physical_dimension']==381
    (tmp_path/'manifest.json').write_bytes(b'{}\n')
    with pytest.raises(ValueError,match='manifest'):worker.source(sign,tmp_path)

@pytest.mark.parametrize('kind',('count','pivot','scale','reconstruction','front','mass','interval'))
def test_full_record_validation_mutations(kind):
    row=dict(shift=0.,negative=1,positive=569,pivot_indices=[[i] for i in range(570)],pivot_sizes=[1]*570,
        reconstruction_relative='0',original_reconstruction_bound='0',coordinate_roundtrip_relative='0',
        coordinate_scales=['1']*570,positive_diagonal_congruence=True,max_front=1,updates=569)
    r=dict(digits=100,physical_dimension=381,algebraic_dimension=189,rows=[row],trace_positive=True,
        mass_positive=True,quadratic_form_preserved=True,symmetric_energy_representation=True,
        certified_intervals=False,mechanics_reconstructed=False,raw_geometric_symmetric=True,raw_skew_normalized='0')
    worker.validate(r,100)
    if kind=='count':row['positive']=568
    elif kind=='pivot':row['pivot_indices'][-1]=[0]
    elif kind=='scale':row['coordinate_scales'][-1]='0'
    elif kind=='reconstruction':row['original_reconstruction_bound']='1e-59'
    elif kind=='front':row['max_front']=97
    elif kind=='mass':r['mass_positive']=False
    else:r['certified_intervals']=True
    with pytest.raises(ValueError):worker.validate(r,100)

def test_preserved120second_bound(monkeypatch):
    values=iter((0.,121.));monkeypatch.setattr(energy,'monotonic',lambda:next(values))
    with pytest.raises(ValueError,match='deadline'):
        energy.audit([[1.]],[[1.,0.]],[[1.,0.],[0.,2.]],[[1.,0.],[0.,1.]],(0,1),(),(0.,))

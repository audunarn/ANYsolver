"""Pure authority mutations; synthetic records are never executed as states."""
from copy import deepcopy
from itertools import product
import pytest
from docs.reference_cases import ge_beam3_fine_onset_protocol as p
from docs.reference_cases.ge_beam3_fine_onset_wave import prior_authority

@pytest.fixture(scope='module')
def auth():return p.authority()

def save(path,value):path.write_bytes(p.canonical(value));return p.bind(path)
def request(tmp_path):
    prior=save(tmp_path/'prior.json',dict(revision='a'*40,macros=24,rows=[],outputs=[]))
    return dict(schema=p.SCHEMA,revision='a'*40,macros=24,index=0,drop=float((.045+.0456)/2),prior=prior,stage=1,previous=None)
def point(auth,n=24,c=0):
    r=deepcopy(auth['points'][str(n)]['left']);r['drop']=float((.045+.0456)/2);r['lateral_negative']=c;return r
def fake_science(r):
    families={name:[dict(digits=d,mass_positive=True,trace_positive=True,rows=[dict(shift=0.,negative=r[name+'_negative'])]) for d in (80,100)] for name in ('planar','lateral')}
    g={k:0. for k in ('cell_rotation_reflection_error','nodal_frame_reflection_error','out_of_plane_position','physical_second_director_error','position_reflection_error')}
    return dict(schema='GE_BEAM3_FINE_ONSET_POINT_V1',revision='a'*40,macros=24,index=0,drop=r['drop'],load=r['load'],
        negative_counts=dict(planar=r['planar_negative'],lateral=r['lateral_negative']),families=families,geometry=[dict(g) for _ in range(4)],
        checkpoint_sha256=r['checkpoint_sha256'],packet_sha256=r['packet_sha256'],exact_factor_decoupling=True,
        critical_point_agreement_established=False,same_branch_uniqueness_proved=False,production_qualified=False,independent_review='PENDING')

def test_bound_history_and_start(auth,tmp_path):
    assert set(auth['points'])=={'20','24'} and p.request(request(tmp_path)) is None
    assert p.search([],auth['points']['24'])[0]==float((.045+.0456)/2)

@pytest.mark.parametrize('counts',list(product((0,1),repeat=3)))
def test_all_three_step_paths(auth,counts):
    rows=[]
    for count in counts:
        nxt,_,_=p.search(rows,auth['points']['24']);r=point(auth,c=count);r['drop']=nxt;rows.append(r)
    assert p.search(rows,auth['points']['24'])[0] is None
    result=p.finish(rows,24,auth)
    assert result['engineering_pass'] and result['production_qualified'] is False
    assert 0<result['bracket'][1]['drop']-result['bracket'][0]['drop']<=.000098
    assert result['first_root_proven'] is False and result['root_uniqueness_established'] is False
    assert p.canonical(result)==p.canonical(p.finish(deepcopy(rows),24,auth))

@pytest.mark.parametrize('key,value',[('schema','bad'),('revision','a'),('macros',True),('macros',16),('index',True),('index',3),('stage',True),('stage',0),('stage',7),('drop',.0456),('drop',float('nan')),('previous',{})])
def test_request_mutations(tmp_path,key,value):
    v=request(tmp_path);v[key]=value
    with pytest.raises(ValueError):p.request(v)

@pytest.mark.parametrize('key,value',[('drop',float('nan')),('load',float('inf')),('load',True),('lateral_negative',2),('lateral_negative',True),('planar_negative',-1),('checkpoint_sha256','x'),('packet_sha256','x')])
def test_point_mutations(auth,key,value):
    r=point(auth);r[key]=value
    with pytest.raises(ValueError):p.validate_row(r)

def test_wrong_midpoint_order_and_incomplete(auth):
    r=point(auth);r['drop']=.0454
    with pytest.raises(ValueError):p.search([r],auth['points']['24'])
    with pytest.raises(ValueError):p.finish([],24,auth)
    with pytest.raises(ValueError):p.search([point(auth)]*4,auth['points']['24'])

def test_conservative_load_failure_cannot_pass(auth):
    rows=[]
    for _ in range(3):
        d,_,_=p.search(rows,auth['points']['24']);r=point(auth,c=0);r['drop']=d;r['load']=.1;rows.append(r)
    out=p.finish(rows,24,auth)
    assert not out['engineering_pass'] and out['disposition']=='NO_GO_FINE_CONTROLLED_ONSET_COMPARISON'

@pytest.mark.parametrize('kind',('revision','schema','index','qualification','count','precision','mass','shift','geometry','extra'))
def test_science_mutations(auth,kind):
    v=fake_science(point(auth));assert p.science(v,'a'*40,24,0)==point(auth)
    if kind in ('revision','schema'):v[kind]='bad'
    elif kind=='index':v['index']=1
    elif kind=='qualification':v['production_qualified']=True
    elif kind=='count':v['families']['lateral'][1]['rows'][0]['negative']=1
    elif kind=='precision':v['families']['lateral'][1]['digits']=80
    elif kind=='mass':v['families']['lateral'][0]['mass_positive']=False
    elif kind=='shift':v['families']['planar'][0]['rows'][0]['shift']=1.
    elif kind=='geometry':v['geometry'][3]['out_of_plane_position']=1e-6
    else:v['extra']=1
    with pytest.raises(ValueError):p.science(v,'a'*40,24,0)

def test_prior_hash_mutation(tmp_path):
    v=request(tmp_path);v['prior']['sha256']='0'*64
    with pytest.raises(ValueError):p.request(v)

def test_other_programme_checkpoint_rejected(tmp_path):
    v=request(tmp_path);rq=save(tmp_path/'request.json',v)
    cap=save(tmp_path/'checkpoint.json',dict(schema='GE_BEAM3_RETAINED_GENERALIZED_TRANSLATION_ACCEPTED_CHAIN_V1',
        program=dict(control_node=25,direction=[0.,-1.,0.],max_backtracks=8,max_iterations=24,nodal_forces=dict(rows=[[25,0.,-1.,0.]]),targets=[.01,.02,.03,.0456]),
        completed_targets=1,records=[{}]))
    ready=save(tmp_path/'ready.json',dict(schema='GE_BEAM3_FINE_ONSET_READY_V1',revision=v['revision'],macros=24,index=0,drop=v['drop'],stage=1,
        request_sha256=rq['sha256'],checkpoint=cap,packet=None,science=None,production_qualified=False))
    receipt=save(tmp_path/'receipt.json',dict(reason='COMPLETED',success=True,exit_code=0,error=None,cleanup_error=None,elapsed=2.,before=[1,0,100],after=[1,0,100]))
    completion=save(tmp_path/'completion.json',dict(request=rq,ready=ready,receipt=receipt))
    with pytest.raises(ValueError,match='same complete native Programme'):p.completion(completion,v['revision'],24,0,v['drop'],v['prior'],1)

@pytest.mark.parametrize('raw',(b'{"x":1,"x":2}\n',b'{"x":NaN}\n',b'{"x":Infinity}\n',b'{ "x":1}\n'))
def test_noncanonical(raw):
    with pytest.raises(ValueError):p.strict_bytes(raw)

@pytest.mark.parametrize('phase',('formal-a','formal-b','bad'))
def test_no_missing_phase_authority(phase):
    with pytest.raises(ValueError):prior_authority(phase,None,'a'*40)

def test_rehearsal_has_no_predecessor(tmp_path):
    assert prior_authority('rehearsal',None,'a'*40) is None
    with pytest.raises(ValueError):prior_authority('rehearsal',tmp_path/'x','a'*40)

def test_source_and_archive_mutations(tmp_path,monkeypatch):
    f=tmp_path/'docs/reference_cases/ge_beam3_fine_upper_status.json';f.parent.mkdir(parents=True);f.write_bytes(b'{}\n')
    with monkeypatch.context() as m:
        m.setattr(p,'ROOT',tmp_path)
        with pytest.raises(ValueError,match='status authority'):p.authority()
    (tmp_path/'archive-manifest.json').write_bytes(b'{}\n');monkeypatch.setattr(p,'ARCHIVE',tmp_path)
    with pytest.raises(ValueError,match='archive authority'):p.authority()

def test_exclusive_output(tmp_path):
    from docs.reference_cases.ge_beam3_retained_prestress_wave import publish
    f=tmp_path/'science.json';publish(f,dict(value=1));raw=f.read_bytes()
    with pytest.raises(FileExistsError):publish(f,dict(value=2))
    assert f.read_bytes()==raw

def test_nested_wave_root_is_exclusive(tmp_path):
    from docs.reference_cases.ge_beam3_fine_onset_wave import output_root
    path=tmp_path/'new-parent'/'rehearsal'
    assert output_root(path)==path.resolve() and path.is_dir()
    marker=path/'keep';marker.write_bytes(b'preserve')
    with pytest.raises(ValueError):output_root(path)
    assert marker.read_bytes()==b'preserve'

def test_wave_root_rejects_repository_and_parent_file(tmp_path):
    from docs.reference_cases.ge_beam3_fine_onset_wave import output_root,ROOT
    with pytest.raises(ValueError):output_root(ROOT/'forbidden-wave')
    parent=tmp_path/'file';parent.write_bytes(b'preserve')
    with pytest.raises(OSError):output_root(parent/'rehearsal')
    assert parent.read_bytes()==b'preserve'

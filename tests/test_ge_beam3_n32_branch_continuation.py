from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import ast
import pytest
from docs.reference_cases import ge_beam3_n32_branch_continuation as branch
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical,strict_bytes

@pytest.mark.parametrize('operation,step',[(o,s) for o,s in [('enroll',0),('advance',1),('advance',2),('advance',3),('replay',3),('cancel-before',2),('cancel-after',2),('resume-before',2)]])
def test_exact_dispositions_and_mutations(operation,step):
    status,cursor,event=branch.recipe(operation,step);events=[] if event is None else [dict(stage=event,target=2,iteration=3)]
    branch.adjudicate(operation,step,status,cursor,events)
    for s,n,e in [('failed',cursor,events),(status,cursor+1,events),(status,bool(cursor),events),
        (status,cursor,[dict(stage='fabricated',target=2,iteration=3)])]:
        with pytest.raises(ValueError):branch.adjudicate(operation,step,s,n,e)

@pytest.mark.parametrize('op,step',[('enroll',1),('replay',2),('advance',0),('advance',4),('cancel-before',1),('cancel-after',3),('resume-before',3),('retry',1),('advance',True)])
def test_unregistered_operations_reject(op,step):
    with pytest.raises(ValueError):branch.recipe(op,step)

@pytest.mark.parametrize('sign',('plus','minus'))
def test_same_source_new_programme_not_old_checkpoint(sign):
    original,v=branch.sources(sign);desc=branch.descriptor(sign)
    assert desc['targets']==([.0075,.01,.015] if sign=='plus' else [-.0075,-.01,-.015])
    assert desc['control_node']==17 and desc['nodal_forces']==dict(rows=[[33,0.,-1.,0.]])
    assert desc['max_iterations']==24 and desc['max_backtracks']==8
    with pytest.raises(ValueError,match='programme'):branch.capsule(original['checkpoint.json'],sign,0)
    assert sha256(original['seed-input.json']).hexdigest()==branch.PREFIX[sign]['seed-input.json']

def skeleton():
    # Structural validator fixture only; not an issued owner record or evidence.
    original,_=branch.sources('plus');v=strict_bytes(original['checkpoint.json']);v['program']=branch.descriptor('plus')
    v['checkpoint_sha256']=sha256(canonical({k:x for k,x in v.items() if k!='checkpoint_sha256'})).hexdigest()
    return v

@pytest.mark.parametrize('kind',('program','hash','cursor','source','previous','history','bound','scope'))
def test_structural_capsule_mutations(kind):
    v=skeleton();branch.capsule(canonical(v),'plus',0)
    if kind=='program':v['program']['targets'][0]=.008
    elif kind=='hash':v['checkpoint_sha256']='0'*64
    elif kind=='cursor':v['completed_targets']=True
    elif kind=='source':v['seed_sha256']='0'*64
    elif kind=='previous':v['initial']['previous_sha256']='0'*64
    elif kind=='history':v['initial']['histories']=[]
    elif kind=='bound':v['initial']['correction']=2e-11
    else:v['physical_loading_path_from_rest']=True
    with pytest.raises(ValueError):branch.capsule(canonical(v),'plus',0)

def test_actual_owner_solver_called_without_mechanics_override():
    tree=ast.parse(Path(branch.__file__).read_text());calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
    solves=[n for n in calls if isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='owner' and n.func.attr=='solve']
    assert len(solves)==1 and {k.arg for k in solves[0].keywords}=={'expected_seed_sha256','checkpoint','expected_sha256','stop_after','cancellation_token','progress'}
    assert not any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr in ('started','max_iterations','max_backtracks','targets') for t in n.targets) for n in ast.walk(tree))

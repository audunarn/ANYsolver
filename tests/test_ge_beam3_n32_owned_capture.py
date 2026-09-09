import copy
import pytest
from docs.reference_cases.ge_beam3_n32_owned_capture import source,validate_equilibrium,layout

@pytest.mark.parametrize('sign',('plus','minus'))
def test_actual_equilibrium_source(sign):
    raw,v=source(sign);validate_equilibrium(v,sign)
    assert len(v['mechanical']['positions'])==65 and len(v['operators'])==32
@pytest.mark.parametrize('field,value',[
    ('accepted_history_issued',True),('old_chain_relabelled',True),('production_qualified',True),
    ('physical_loading_path_from_rest',True),('control_node',13),('load_node',25),('amplitude',.006),
    ('macros',24),('arithmetic_policy','other')])
def test_equilibrium_authority_mutations(field,value):
    _,v=source('plus');v[field]=value
    with pytest.raises(ValueError):validate_equilibrium(v,'plus')
def test_virgin_station_extent_and_convergence_mutations():
    _,v=source('plus')
    for change in (lambda x:x['recovery'].pop(),lambda x:x['recovery'][0]['stations'].pop(),
        lambda x:x['recovery'][0]['stations'][0]['history']['plastic'][0].__setitem__(0,1.),
        lambda x:x['convergence'].__setitem__('correction',1.)):
        bad=copy.deepcopy(v);change(bad)
        with pytest.raises(ValueError):validate_equilibrium(bad,'plus')
def test_complete_modal_partition_and_control_not_fixed():
    p=dict(free_dofs=list(range(6,384))+list(range(390,582)),
        algebraic_dofs=[6*i+j for i in range(1,64) for j in (3,4,5)],
        internal_layout=[[i+1,list(range(390+6*i,396+6*i))] for i in range(32)])
    free,algebraic=layout(p)
    assert len(free)==570 and len(algebraic)==189 and len(set(free)-set(algebraic))==381
    assert 6*16+2 in free and not {0,1,2,3,4,5,384,385,386,387,388,389}&set(free)
    for change in (lambda x:x['free_dofs'].remove(98),lambda x:x['algebraic_dofs'].append(390),
        lambda x:x['internal_layout'][-1][1].__setitem__(0,0)):
        bad=copy.deepcopy(p);change(bad)
        with pytest.raises(ValueError):layout(bad)
def test_wrong_archive_hash_rejected(tmp_path):
    (tmp_path/'manifest.json').write_text('{}\n')
    with pytest.raises(ValueError,match='manifest'):source('plus',tmp_path)
    with pytest.raises(ValueError):source('unknown',tmp_path)


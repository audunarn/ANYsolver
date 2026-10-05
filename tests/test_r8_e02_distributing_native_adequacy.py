import pytest
from scripts.r8_e02_distributing_native_adequacy import geometry
from scripts.r8_e02_native_rigid_tip import geometry as historical


def test_explicit_builder_matches_historical_allowed_fixture_exactly():
    assert geometry(40,16)==historical(40,16)
    with pytest.raises(ValueError):historical(80,32)
    with pytest.raises(ValueError):geometry(160,64)


def test_new_inventory_geometry_and_physical_pad():
    nodes,cells,_,_,root=geometry(80,32)
    assert len(nodes)==2673 and len(cells)==2560 and len(root)==33
    assert 6*len(nodes)+42==16080 and 6*len(nodes)+42+6<=100000
    assert nodes[1]==(0.,-.1,0.) and nodes[2673]==(1.,.1,0.)
    assert all(nodes[n][0]==0. for n in root)
    hosts=tuple(1+j*80+i for j in range(8,16) for i in range(64,80))
    pad_nodes={n for host in hosts for n in cells[host-1]}
    assert len(hosts)==128 and len(pad_nodes)==153
    assert min(nodes[n][0] for n in pad_nodes)==.8
    assert max(nodes[n][0] for n in pad_nodes)==1.
    assert min(nodes[n][1] for n in pad_nodes)==-.05
    assert max(nodes[n][1] for n in pad_nodes)==0.

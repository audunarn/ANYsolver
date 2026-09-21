"""Identity and dimension checks for the proposed, unregistered F03 set."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_independent_inventory as inventory


def test_refinement_axes_counts_and_unique_case_identities():
    meshes=inventory.meshes()
    assert len(meshes)==12 and len(set(meshes))==12
    anchor=inventory.Mesh(64,32,256,32)
    assert anchor in meshes
    for attribute,expected in (('n_s',(32,64,128)),
                               ('n_y',(16,32,64)),
                               ('n_beam',(128,256,512)),
                               ('n_mortar',(16,32,64))):
        assert {getattr(m,attribute) for m in meshes
                if all(getattr(m,name)==getattr(anchor,name)
                       for name in ('n_s','n_y','n_beam','n_mortar')
                       if name!=attribute)}==set(expected)
    cases=inventory.cases()
    assert len(cases)==96 and len({c.identity for c in cases})==96
    assert set(Counter((c.topology,c.loading,c.law) for c in cases).values())=={12}


def test_largest_assembly_dimensions_are_combinatorial_only():
    largest=inventory.Mesh(128,64,512,64)
    q=inventory.structural_counts(largest,'Q4','P1')
    t=inventory.structural_counts(largest,'CST','P0')
    assert q['shell_nodes']==16705
    assert q['shell_elements']==16384
    assert t['shell_elements']==32768
    assert q['beam_elements']==t['beam_elements']==512
    assert q['kkt_dimension']==q['shell_dofs']+q['beam_dofs']+q['multiplier_dofs']
    assert t['multiplier_dofs']==192 and q['multiplier_dofs']==195

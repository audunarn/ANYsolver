"""Manufactured exact membrane work checks, without scientific states."""
from fractions import Fraction as F

import pytest

from scripts import _b3_e4_f03_local_work_oracle as w
from scripts import _b3_e4_f03_spatial_contract as c


Z=F(0);O=F(1)
LOAD=w.Load((F(2),F(-3),F(5)),((F(7),F(11),F(13)),
                                  (F(-17),F(19),F(-23))))
NO_LOAD=w.Load((Z,Z,Z),((Z,Z,Z),(Z,Z,Z)))


def _displacement(x,y):
    # The displacement is C0, while normal stress jumps on both interfaces.
    return (abs(x-F(1,2))+x*y,abs(y)+x*y)


def _supported_test(x,y):
    tent=O-abs(x-F(1,2))
    return (tent*(O+y),tent*(O-y))


@pytest.mark.parametrize('p',(1,2,3))
def test_exact_supported_identity_with_nonzero_stress_jumps_and_full_pad_load(p):
    u=w.Patch.sample(p,_displacement)
    z=w.Patch.sample(p,_supported_test)
    result=w.work_identity(u,z,LOAD)
    assert result['jump_work']!=0
    assert result['supported_boundary_work']==0
    assert result['area_load_work']==result['direct_pad_work']
    assert result['integration_by_parts_defect']==0
    assert result['reaction_defect']==0
    assert (result['direct_pad_work']-result['strain_work']==
            result['volume_residual_work']+result['jump_work']-
            result['free_boundary_work'])


def test_both_oriented_jumps_balance_supported_tractions_for_constant_virtual_motion():
    u=w.Patch.sample(1,lambda x,y:(abs(x-F(1,2)),abs(y)))
    cells=list(u.cells())
    def at(poly,x,y):
        return sum((v*x**i*y**j for (i,j),v in poly.items()),Z)
    for y in (F(-1,4),F(1,4)):
        k=0 if y<0 else 2
        assert all(at(cells[k][1][axis],F(1,2),y)==
                   at(cells[k+1][1][axis],F(1,2),y)
                   for axis in range(2))
        tx_minus=w.stress(cells[k][1])[0]
        tx_plus=w.stress(cells[k+1][1])[0]
        assert at(tx_plus,F(1,2),y)-at(tx_minus,F(1,2),y)==(
            2*c.Q_THICKNESS*c.Q_PLANE[0][0])
    for x in (Z,O):
        k=0 if x<F(1,2) else 1
        assert all(at(cells[k][1][axis],x,Z)==
                   at(cells[k+2][1][axis],x,Z)
                   for axis in range(2))
        ty_minus=w.stress(cells[k][1])[1]
        ty_plus=w.stress(cells[k+2][1])[1]
        assert at(ty_plus,x,Z)-at(ty_minus,x,Z)==(
            2*c.Q_THICKNESS*c.Q_PLANE[1][1])
    z=w.Patch.sample(1,lambda x,y:(O,O))
    result=w.work_identity(u,z,NO_LOAD)
    support=2*c.Q_THICKNESS*c.Q_PLANE[0][0]   # x sides, length one each
    free=4*c.Q_THICKNESS*c.Q_PLANE[1][1]      # y sides, length two each
    assert result['jump_work']==support+free
    assert result['supported_boundary_work']==support
    assert result['free_boundary_work']==free
    assert result['volume_divergence_work']==0
    assert result['strain_work']==0
    assert result['integration_by_parts_defect']==0


def test_rigid_origin_rotation_measures_physical_moment_and_two_endpoint_atoms():
    u=w.Patch.sample(2,_displacement)
    rotation=w.Patch.sample(2,lambda x,y:(-y,x))
    result=w.work_identity(u,rotation,LOAD)
    expected=F(-3,2)+F(19)+(F(5)+F(13)-F(23))*c.Q_GAMMA
    assert result['direct_pad_work']==expected
    assert result['area_load_work']==expected
    assert result['strain_work']==0
    assert result['reaction_work']==-expected
    assert result['integration_by_parts_defect']==0
    assert result['reaction_defect']==0


def test_both_support_lifts_partition_force_and_origin_moment_without_slope_fixity():
    u=w.Patch.sample(2,_displacement)
    for rigid,expected in (
        (lambda x,y:(O,Z),LOAD.density[0]+LOAD.atoms[0][0]+LOAD.atoms[1][0]),
        (lambda x,y:(Z,O),LOAD.density[1]+LOAD.atoms[0][1]+LOAD.atoms[1][1]),
        (lambda x,y:(-y,x),F(-3,2)+F(19)-F(5)*c.Q_GAMMA),
    ):
        whole=w.work_identity(u,w.Patch.sample(2,rigid),LOAD)
        left=w.work_identity(u,w.Patch.sample(2,lambda x,y:(
            (F(3,2)-x)*rigid(x,y)[0]/2,
            (F(3,2)-x)*rigid(x,y)[1]/2)),LOAD)
        right=w.work_identity(u,w.Patch.sample(2,lambda x,y:(
            (x+F(1,2))*rigid(x,y)[0]/2,
            (x+F(1,2))*rigid(x,y)[1]/2)),LOAD)
        assert whole['direct_pad_work']==expected
        assert whole['reaction_work']==-expected
        assert left['reaction_work']+right['reaction_work']==whole['reaction_work']
        assert left['reaction_defect']==right['reaction_defect']==0


def test_shared_nodal_ownership_and_rejection():
    source=[[[F(i+j+k) for i in range(3)] for j in range(3)] for k in range(2)]
    patch=w.Patch(1,source)
    source[0][0][0]=F(99)
    assert patch.values[0][0][0]==0
    with pytest.raises(ValueError):w.Patch.sample(0,lambda x,y:(Z,Z))
    with pytest.raises(ValueError):w.Patch(1,source[:1])
    with pytest.raises(ValueError):w.Load((O,Z,0.),((Z,Z,Z),(Z,Z,Z)))

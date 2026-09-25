"""FRD expanded-tip matching rejects incomplete or ambiguous evidence."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from _b3_e4_ccx_3d_tip_work_parser import (parse_tip_corner_displacements,
                                          recover_tip_section_motion)


def _row(node,x,y,z):
    return f" -1{node:10d}{x:12.5E}{y:12.5E}{z:12.5E}"


def _frd():
    coords=[_row(226,1.,-.05,.05),_row(227,1.,.05,.05),
            _row(228,1.,-.05,.15),_row(229,1.,.05,.15)]
    disp=[_row(226,0.,-1e-5,0.),_row(227,0.,-2e-5,0.),
          _row(228,0.,-3e-5,0.),_row(229,0.,-4e-5,0.)]
    return "\n".join(["    2C",*coords," -3"," -4  DISP        4    1",
                      " -5  D1          1    2    1    0",*disp," -3"," 9999"])+"\n"


def test_four_geometric_corners_and_mean_are_extracted():
    result=parse_tip_corner_displacements(_frd())
    assert [item["node"] for item in result["corners"]]==[226,227,228,229]
    assert result["mean_tip_y_m"]==pytest.approx(-2.5e-5,rel=0,abs=1e-14)


def test_missing_ambiguous_or_duplicate_corner_fails():
    src=_frd()
    with pytest.raises(ValueError,match="missing expanded tip"):
        parse_tip_corner_displacements(src.replace(_row(229,0.,-4e-5,0.)+"\n",""))
    with pytest.raises(ValueError,match="ambiguous expanded"):
        parse_tip_corner_displacements(src.replace(_row(229,1.,.05,.15),
                                               _row(229,1.,.05,.05)))
    with pytest.raises(ValueError,match="duplicate FRD displacement"):
        parse_tip_corner_displacements(src.replace(_row(229,0.,-4e-5,0.),
                                               _row(228,0.,-4e-5,0.)))


def _motion_frd(translation, rotation, *, distortion=0.):
    points=[(1.,-.05,.05),(1.,.05,.05),(1.,-.05,.15),(1.,.05,.15)]
    center=np.array((1.,0.,.1))
    coords=[_row(node,*point) for node,point in enumerate(points,226)]
    disp=[]
    for node,point in enumerate(points,226):
        value=np.asarray(translation)+np.cross(rotation,np.asarray(point)-center)
        if node==226:
            value=value+np.array((distortion,0.,0.))
        disp.append(_row(node,*value))
    return "\n".join(["    2C",*coords," -3"," -4  DISP        4    1",
                      " -5  D1          1    2    1    0",*disp," -3"," 9999"])+"\n"


def test_section_fit_recovers_all_six_rigid_tip_work_coordinates():
    translation=(1.2e-5,-2.3e-5,3.4e-5)
    rotation=(2.0e-4,-3.0e-4,4.0e-4)
    recovered=recover_tip_section_motion(_motion_frd(translation,rotation))
    assert recovered["center_m"]==pytest.approx((1.,0.,.1),abs=1e-14)
    assert recovered["translation_m"]==pytest.approx(translation,abs=1e-11)
    assert recovered["rotation_rad"]==pytest.approx(rotation,abs=1e-10)
    assert recovered["max_corner_fit_residual_m"]<1e-11


def test_section_fit_reports_nonrigid_corner_motion():
    recovered=recover_tip_section_motion(_motion_frd(
        (0.,0.,0.),(0.,0.,0.),distortion=1e-5))
    assert recovered["max_corner_fit_residual_m"]>1e-6


def test_nonrigid_fit_rotations_equal_calculix_meanrotbs_work_coordinates():
    # Independent transcription of CalculiX 2.23 usermpc.f's linear
    # MEANROTBS: average the tangential displacement/radius for each axis.
    # gen3dforc.f sends the tip moment to this angle DOF. The four-corner
    # symmetric section makes these three means identical to the LS fit.
    frd=_motion_frd((1e-5,-2e-5,3e-5),(2e-4,-3e-4,4e-4),
                    distortion=1e-5)
    corners=parse_tip_corner_displacements(frd)["corners"]
    xyz=np.array([item["coordinate_m"] for item in corners])
    u=np.array([item["displacement_m"] for item in corners])
    relative=xyz-xyz.mean(axis=0)
    centered_u=u-u.mean(axis=0)
    source_mean=[]
    for axis in np.eye(3):
        projected=relative-(relative@axis)[:,None]*axis
        source_mean.append(float(np.mean([
            np.cross(axis,p)@v/(p@p)
            for p,v in zip(projected,centered_u)])))
    fitted=recover_tip_section_motion(frd)
    assert fitted["max_corner_fit_residual_m"]>1e-6
    assert fitted["rotation_rad"]==pytest.approx(source_mean,abs=1e-11)

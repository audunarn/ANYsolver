"""FRD expanded-tip matching rejects incomplete or ambiguous evidence."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from _b3_e4_ccx_3d_tip_work_parser import parse_tip_corner_displacements


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

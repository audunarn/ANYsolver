"""Physical resultant and virtual-work checks for the saved tip diagnostic."""

import numpy as np

from scripts.b3_e4_f03_c1_tip_face_work import split_tip_work


def test_rigid_tip_motion_has_no_nonrigid_load_work():
    origin = np.array((1., 0., .0675))
    coords = np.array([(1., y, z) for y in (-.05, 0., .05)
                       for z in (.0175, .0675, .1175)])
    force = np.array([(0., 2.*y, -3.*z) for _, y, z in coords])
    translation = np.array((.001, -.002, .003))
    rotation = np.array((.004, -.005, .006))
    displacement = translation+np.cross(rotation, coords-origin)
    result = split_tip_work(coords, force, displacement, origin)
    np.testing.assert_allclose(result["fitted_translation_m"], translation,
                               rtol=0., atol=1e-15)
    np.testing.assert_allclose(result["fitted_rotation_rad"], rotation,
                               rtol=0., atol=1e-15)
    assert abs(result["nonrigid_fit_load_work_J"]) < 1e-14


def test_nonrigid_tip_work_keeps_force_moment_identity():
    origin = np.array((1., 0., .0675))
    coords = np.array([(1., y, z) for y in (-.05, 0., .05)
                       for z in (.0175, .0675, .1175)])
    force = np.array([(1.+y*y, 2.*y*y, 3.*z*z) for _, y, z in coords])
    displacement = np.array([(y*z, y*y, z*z) for _, y, z in coords])
    result = split_tip_work(coords, force, displacement, origin)
    np.testing.assert_allclose(result["full_tip_load_work_J"],
                               np.sum(force*displacement), rtol=0., atol=1e-14)
    np.testing.assert_allclose(
        result["full_tip_load_work_J"],
        result["rigid_fit_load_work_J"]+result["nonrigid_fit_load_work_J"],
        rtol=0., atol=1e-14)
    assert abs(result["nonrigid_fit_load_work_J"]) > 1e-8

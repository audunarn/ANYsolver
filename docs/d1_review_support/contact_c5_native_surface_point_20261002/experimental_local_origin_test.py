
def test_nearby_plane_origin_preserves_affine_target_gap_and_motion():
    from anysolver.general_contact.native_surface_support import _nearby_target_origin,_base
    field=_field();pose=field.initial;cell=0;xis=(-.8,-.2)
    corners=np.array(((-5.,-5.,-.04),(5.,-5.,-.04),(-5.,5.,-.04)))
    weights=_nearby_target_origin(pose,corners,cell,xis)
    projected=weights@corners
    midpoint=(xis[0]+xis[1])/2
    base=_base(pose,cell,midpoint,np.zeros(3))
    np.testing.assert_allclose(projected[:2],base[:2],atol=2e-15,rtol=0.)
    increments=np.array(((.01,0.,.002),(-.01,.02,-.003),(.03,-.01,.005)))
    velocity=np.array((.02,-.01,-.004))
    for time in (0.,.13,.5,.91,1.):
        moved=corners+time*increments
        normal=np.cross(moved[1]-moved[0],moved[2]-moved[0]);normal/=np.linalg.norm(normal)
        point=base+time*velocity
        assert float(normal@(point-moved[0]))==pytest.approx(float(normal@(point-weights@moved)),abs=2e-15)
        np.testing.assert_allclose(weights@moved,projected+time*(weights@increments),atol=2e-15,rtol=0.)

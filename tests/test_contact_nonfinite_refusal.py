"""Nonfinite sphere/contact inputs are refused at construction, not deep in the solve."""
import pytest

import anysolver as fs

NAN, INF = float("nan"), float("inf")


@pytest.mark.parametrize("field,value", [
    ("radius", NAN), ("radius", INF), ("mass", NAN), ("mass", INF),
    ("speed", NAN), ("speed", INF), ("t_start", NAN), ("t_start", INF),
])
def test_sphere_refuses_nonfinite_scalars(field, value):
    kwargs = dict(name="b", radius=0.2, mass=1.0, start_point=(0.5, 0.5, 1.0),
                  travel_direction=(0.0, 0.0, -1.0), speed=1.0)
    kwargs[field] = value
    with pytest.raises(ValueError):
        fs.RigidSphereImpact(**kwargs)


@pytest.mark.parametrize("field", ["start_point", "travel_direction"])
def test_sphere_refuses_nonfinite_vectors(field):
    kwargs = dict(name="b", radius=0.2, mass=1.0, start_point=(0.5, 0.5, 1.0),
                  travel_direction=(0.0, 0.0, -1.0), speed=1.0)
    kwargs[field] = (0.0, NAN, 1.0)
    with pytest.raises(ValueError):
        fs.RigidSphereImpact(**kwargs)


@pytest.mark.parametrize("field,value", [
    ("penalty_stiffness", NAN), ("penalty_stiffness", INF),
    ("contact_damping", NAN), ("contact_damping", INF),
    ("search_margin", NAN), ("search_margin", INF),
])
def test_contact_config_refuses_nonfinite(field, value):
    with pytest.raises(ValueError):
        fs.SphereContactConfig(**{field: value})

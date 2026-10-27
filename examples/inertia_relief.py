"""A free bar accelerates under an end force while developing elastic strain."""
from anysolver import BeamElement, FEModel, LoadCase, solve_inertia_relief


def main():
    model = FEModel("free_bar_inertia_relief")
    model.add_material("steel", elastic_modulus=210.e9, poisson_ratio=.3, density=7850.)
    length, area, count = 2., .01, 4
    section = {"area": area, "Iy": 1.e-5, "Iz": 1.e-5, "J": 2.e-5,
               "consistent_mass": True}
    for i in range(count+1):
        model.add_node(i+1, length*i/count, 0., 0.)
    for i in range(count):
        model.add_element(i+1, BeamElement(i+1, [i+1,i+2], "steel", dict(section)))
    load = LoadCase("end_force")
    load.add_nodal_load(count+1, forces=[1000., 0., 0.])
    result = solve_inertia_relief(model, load)
    if not result.converged:
        raise RuntimeError(f"{result.status}: {result.error}")
    print(result.summary())
    print(f"Analytical axial acceleration: {1000./(7850.*area*length):.12g} m/s^2")
    print(f"Elastic backward error: {result.diagnostics['elastic_backward_error']:.3e}")
    return result


if __name__ == "__main__":
    main()

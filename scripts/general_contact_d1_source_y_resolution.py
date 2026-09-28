"""Source-only Q4/y-row pressure discriminator against scalar continuum.

The shell stiffness is the production elastic tangent. The clipped Q1
pressure work, scalar quadratic problem and continuum reference are assembled
outside the general-contact kernel. This is development evidence only.
"""

import argparse
import json

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from anysolver import BoundaryCondition, create_shell_element
from anysolver.assembly import build_constraint_transformation
from anysolver.fe_core import FEModel
from anysolver.matrix_assembly import assemble_stiffness_matrix
from scripts.general_contact_d1_continuum_obstacle_reference import solve
from scripts.general_contact_d1_linearized_front_reference import _nonnegative_quadratic


def _q1_mass(cells: int, right: float) -> sparse.csr_matrix:
    if cells < 1 or right <= 0.0 or right > 1.0:
        raise ValueError("invalid Q1 interval")
    matrix = sparse.lil_matrix((cells+1, cells+1))
    h = 1.0/cells
    points = (0.5*(1.0-1.0/np.sqrt(3.0)),
              0.5*(1.0+1.0/np.sqrt(3.0)))
    for cell in range(cells):
        left = cell*h
        end = min((cell+1)*h, right)
        if end <= left:
            continue
        interval = end-left
        for fraction in points:
            coordinate = left+fraction*interval
            local = (coordinate-left)/h
            shape = np.array((1.0-local, local))
            matrix[cell:cell+2, cell:cell+2] += (
                0.5*interval*np.outer(shape, shape)
            )
    return matrix.tocsr()


def _model(nx: int, ny: int) -> FEModel:
    model = FEModel(f"source_y_resolution_{nx}_{ny}")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    stride = nx+1
    for row in range(ny+1):
        for column in range(nx+1):
            node = 1+row*stride+column
            model.add_node(node, 0.1+column/nx, 0.1+row/ny, 0.04004)
    for row in range(ny):
        for column in range(nx):
            bottom = 1+row*stride+column
            element = 1+row*nx+column
            model.add_element(element, create_shell_element(
                element,
                (bottom, bottom+1, bottom+stride+1, bottom+stride),
                "elastic", thickness=0.05,
                reference_normal=(0.0, 0.0, 1.0),
            ))
    nodes = tuple(range(1, stride*(ny+1)+1))
    left = tuple(1+row*stride for row in range(ny+1))
    model.add_boundary_condition(BoundaryCondition(
        "guide", nodes, {name: 0.0 for name in
                         ("uy", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "left_support", left, {"uz": 0.0, "ux": 0.0},
    ))
    return model


def run(nx: int, ny: int) -> dict:
    model = _model(nx, ny)
    model.apply_boundary_conditions()
    stiffness, _ = assemble_stiffness_matrix(model)
    stride = nx+1
    node_z = np.asarray([
        model.mesh.dof_manager.get_node_dofs(node)[2]
        for node in range(1, stride*(ny+1)+1)
    ], dtype=int)
    load = np.zeros(stiffness.shape[0])
    for row in range(ny):
        for column in range(nx):
            nodes = (
                row*stride+column, row*stride+column+1,
                (row+1)*stride+column+1, (row+1)*stride+column,
            )
            load[node_z[list(nodes)]] -= 0.3/(4.0*nx*ny)
    if abs(np.sum(load)+0.3) > 1.0e-13:
        raise AssertionError("distributed source load is invalid")
    reduced_k, reduced_load, transform, offset, _, _ = (
        build_constraint_transformation(stiffness, load, model)
    )
    if np.linalg.norm(offset) > 0.0:
        raise ValueError("source y reference requires zero prescribed pose")

    mx = _q1_mass(nx, 1.0)
    my = _q1_mass(ny, 0.9)
    pressure_work_on_z = sparse.kron(my, mx, format="coo")
    work = sparse.coo_matrix((
        pressure_work_on_z.data,
        (pressure_work_on_z.row, node_z[pressure_work_on_z.col]),
    ), shape=(len(node_z), stiffness.shape[0])).tocsr()
    full_support = np.asarray(pressure_work_on_z.tocsr() @ np.ones(len(node_z)))
    if np.min(full_support) < -1.0e-14 or abs(np.sum(full_support)-0.9) > 1.0e-12:
        raise ValueError("clipped Q1 pressure support is invalid")
    supported = full_support > 1.0e-14
    support = full_support[supported]
    work = work[supported]
    reduced_work = (work @ transform).toarray()
    factor = splu(reduced_k.tocsc())
    free = factor.solve(reduced_load)
    response = factor.solve(reduced_work.T)
    compliance = reduced_work @ response
    compliance = 0.5*(compliance+compliance.T)
    initial_gap = 4.0e-5
    linear = support*initial_gap+reduced_work @ free
    pressure = _nonnegative_quadratic(compliance, linear, support)
    reduced_displacement = free+response @ pressure
    equilibrium = reduced_k @ reduced_displacement-reduced_load-reduced_work.T @ pressure
    weighted_gap = (linear+compliance @ pressure)/support
    if (np.linalg.norm(equilibrium) > 1.0e-7
            or np.min(weighted_gap) < -1.0e-11):
        raise RuntimeError("source y-resolution equilibrium or weak gap failed")
    full = np.asarray(transform @ reduced_displacement).reshape(-1)
    vertical = full[node_z].reshape(ny+1, nx+1)
    full_pressure = np.zeros(len(node_z))
    full_pressure[supported] = pressure
    pressure_grid = full_pressure.reshape(ny+1, nx+1)
    y_support = np.asarray(my @ np.ones(ny+1)).reshape(-1)
    x_line = y_support @ pressure_grid
    x_force = (x_line[:-1]+x_line[1:])/(2.0*nx)
    boundary = 0.9*ny
    lower = int(np.floor(boundary))
    if lower == ny:
        boundary_vertical = vertical[-1]
    elif abs(boundary-lower) < 1.0e-14:
        boundary_vertical = vertical[lower]
    else:
        boundary_vertical = ((1.0-(boundary-lower))*vertical[lower]
                             +(boundary-lower)*vertical[lower+1])
    represented_gap = min(
        float(np.min(initial_gap+vertical[:lower+1])),
        float(np.min(initial_gap+boundary_vertical)),
    )
    if represented_gap < -50.0e-6:
        raise RuntimeError("source y-resolution case exceeds its 50 µm represented-gap budget")
    return {
        "nx": nx, "ny": ny,
        "pressure_modes": len(pressure),
        "unsupported_pressure_modes": int(np.sum(~supported)),
        "active_modes": int(np.sum(pressure > 1.0e-8)),
        "integrated_reaction_n": float(np.sum(x_force)),
        "minimum_weak_gap_m": float(np.min(weighted_gap)),
        "minimum_represented_gap_m": represented_gap,
        "equilibrium_residual_n": float(np.linalg.norm(equilibrium)),
        "x_force_n": x_force.tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nx", type=int, nargs="+", default=(16, 32))
    parser.add_argument("--ny", type=int, nargs="+", default=(1, 2, 4, 8))
    args = parser.parse_args()
    if (not args.nx or not args.ny or max(args.nx) > 64
            or max(args.ny) > 16 or min(args.nx) < 8 or min(args.ny) < 1
            or any(256 % nx for nx in args.nx)):
        raise ValueError("development source grids require nx=8..64 dividing 256, ny=1..16")
    continuum = solve(256, 320, 0.9)
    continuum_x = np.sum(continuum.pressure_force, axis=0)
    cases = [run(nx, ny) for nx in args.nx for ny in args.ny]
    for case in cases:
        bins = case["nx"]
        reference = continuum_x.reshape(bins, 256//bins).sum(axis=1)
        source = np.asarray(case.pop("x_force_n"))
        difference = source-reference
        case["force_difference_n"] = float(np.sum(difference))
        case["x_force_l1_relative"] = float(
            np.sum(np.abs(difference))/np.sum(reference)
        )
        case["x_force_l2_relative"] = float(
            np.linalg.norm(difference)/np.linalg.norm(reference)
        )
        case["cumulative_force_max_relative"] = float(
            np.max(np.abs(np.cumsum(difference)))/np.sum(reference)
        )
    print(json.dumps({
        "method": "source_q4_y_resolution_against_independent_scalar_obstacle_dev",
        "continuum_grid": [256, 320],
        "continuum_contact_reaction_n": continuum.contact_reaction_n,
        "cases": cases,
    }, indent=2))


if __name__ == "__main__":
    main()

"""Bounded guided-scalar Q1 cut-row pressure detection family.

This is an independent scalar reference experiment, not a shell/contact
acceptance run. Both mesh directions refine while the physical y=.9 cut
keeps the same fraction of its intersected cell.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
import scipy
from scipy import linalg, sparse
from scipy.sparse.linalg import splu

from docs.d1_review_support.d1_guided_q1_fourier import (
    guided_q1_fourier_reference,
)


def _line_matrices(knots, upper):
    """Piecewise-linear mass on [0,upper] and full gradient energy."""
    count = len(knots)
    mass = np.zeros((count, count))
    gradient = np.zeros_like(mass)
    for element in range(count-1):
        left, right = float(knots[element]), float(knots[element+1])
        width = right-left
        ids = np.array((element, element+1))
        local_gradient = np.array(((1.0, -1.0), (-1.0, 1.0)))/width
        gradient[np.ix_(ids, ids)] += local_gradient
        clipped_right = min(right, upper)
        if clipped_right <= left:
            continue
        for root in (-1.0/np.sqrt(3.0), 1.0/np.sqrt(3.0)):
            point = (left+clipped_right+root*(clipped_right-left))/2.0
            shape = np.array(((right-point)/width, (point-left)/width))
            mass[np.ix_(ids, ids)] += (clipped_right-left)/2.0 * (
                np.outer(shape, shape))
    return sparse.csr_matrix(mass), sparse.csr_matrix(gradient)


def _independent_element_energy(x, y, values):
    """Separate 2×2 Gauss evaluation of Q1 gradient work."""
    nodal = values.reshape(len(y), len(x))
    roots = (-1.0/np.sqrt(3.0), 1.0/np.sqrt(3.0))
    total = 0.0
    for row in range(len(y)-1):
        height = y[row+1]-y[row]
        for column in range(len(x)-1):
            width = x[column+1]-x[column]
            local = nodal[row:row+2, column:column+2]
            for xi in roots:
                for eta in roots:
                    # local indexing is [y,x], with tensor-product Q1.
                    gx = ((1-eta)*(local[0, 1]-local[0, 0])
                          +(1+eta)*(local[1, 1]-local[1, 0]))/(2*width)
                    gy = ((1-xi)*(local[1, 0]-local[0, 0])
                          +(1+xi)*(local[1, 1]-local[0, 1]))/(2*height)
                    total += width*height*(gx*gx+gy*gy)/4.0
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cells", type=int, choices=(16, 32, 64), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists")
    started = time.perf_counter()
    cells = args.cells
    contact_y = 0.9
    cut_fraction = 0.1
    h = 1.0/cells
    x = np.linspace(0.0, 1.0, cells+1)
    y = np.linspace(0.0, 1.0, cells+1)
    cut_cell = int(np.floor(contact_y*cells))
    y[cut_cell] = contact_y-cut_fraction*h
    y[cut_cell+1] = contact_y+(1.0-cut_fraction)*h
    y_steps = np.diff(y)
    if (np.min(y_steps) < 0.25*h or np.max(y_steps) > 2.0*h
            or not np.isclose((contact_y-y[cut_cell])/
                              (y[cut_cell+1]-y[cut_cell]), cut_fraction,
                              rtol=0, atol=1e-14)):
        raise AssertionError("declared cut phase or shape bound failed")
    mx, kx = _line_matrices(x, 1.0)
    my, ky = _line_matrices(y, 1.0)
    my_contact, _ = _line_matrices(y, contact_y)
    stiffness = (sparse.kron(my, kx, format="csc")
                 + sparse.kron(ky, mx, format="csc"))
    contact_mass = sparse.kron(my_contact, mx, format="csc")
    dofs = (cells+1)**2
    free = np.flatnonzero(np.arange(dofs) % (cells+1) != 0)
    active_columns = np.flatnonzero(x >= 0.65-1e-14)
    active = cut_cell+1
    active_indices = active*(cells+1)+active_columns
    support = np.asarray(contact_mass.sum(axis=1)).reshape(-1)[active_indices]
    if np.any(support <= 0):
        raise AssertionError("cut-row Q1 pressure support is nonpositive")
    work = contact_mass[free, :][:, active_indices].toarray()
    factor = splu(stiffness[free, :][:, free].tocsc())
    response = factor.solve(work)
    raw_discrete = work.T @ response
    symmetry = float(np.linalg.norm(raw_discrete-raw_discrete.T)
                     / np.linalg.norm(raw_discrete))
    discrete = 0.5*(raw_discrete+raw_discrete.T)
    structural_residual = float(np.linalg.norm(
        stiffness[free, :][:, free] @ response-work)
        / np.linalg.norm(work))
    fourier_modes = 1024 if cells == 64 else 512
    finite, gram, tail_coefficient = guided_q1_fourier_reference(
        x, y, active_indices, contact_y_upper=contact_y,
        shear_stiffness_n_per_m=1.0,
        x_modes=fourier_modes, y_modes=fourier_modes,
    )
    independent_gram = contact_mass[active_indices, :][:, active_indices].toarray()
    gram_error = float(np.linalg.norm(gram-independent_gram)
                       /np.linalg.norm(independent_gram))
    upper = finite+tail_coefficient*gram
    tail_relative = float(linalg.eigvalsh(
        tail_coefficient*gram, finite)[-1])
    lower_eigen, lower_modes = linalg.eigh(discrete, upper)
    upper_eigen = linalg.eigvalsh(discrete, finite)
    alternating = (-1.0)**active_columns
    alternating /= np.linalg.norm(alternating)
    alternating_discrete = float(alternating @ discrete @ alternating)
    alternating_finite = float(alternating @ finite @ alternating)
    alternating_upper = float(alternating @ upper @ alternating)
    alternating_interval = [alternating_discrete/alternating_upper,
                            alternating_discrete/alternating_finite]
    test_values = (np.sin(1.3*np.arange(dofs))
                   +0.3*np.cos(0.7*np.arange(dofs)))
    assembled_energy = float(test_values @ stiffness @ test_values)
    independent_energy = _independent_element_energy(x, y, test_values)
    energy_error = abs(assembled_energy-independent_energy)/independent_energy
    if (structural_residual > 1e-10 or symmetry > 1e-12
            or gram_error > 1e-10 or energy_error > 1e-10
            or tail_relative > 0.1 or lower_eigen[0] <= 0
            or upper_eigen[0] < lower_eigen[0]):
        raise AssertionError("scalar work, energy or reference guard failed")
    weakest = lower_modes[:, 0]
    weakest /= np.max(np.abs(weakest))
    result = {
        "status": "development_balanced_cut_scalar",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "fourier_helper_sha256": hashlib.sha256(Path(
            guided_q1_fourier_reference.__code__.co_filename).read_bytes()).hexdigest(),
        "runtime_identity": {"python": platform.python_version(),
                             "numpy": np.__version__, "scipy": scipy.__version__},
        "cells_each_axis": cells,
        "contact_y_m": contact_y,
        "cut_cell_y_index": cut_cell,
        "cut_fraction": cut_fraction,
        "fourier_modes_each_axis": fourier_modes,
        "minimum_y_cell_to_x_cell_ratio": float(np.min(y_steps)/h),
        "maximum_y_cell_to_x_cell_ratio": float(np.max(y_steps)/h),
        "active_x_node_columns": active_columns.tolist(),
        "active_pressure_mode_count": len(active_indices),
        "minimum_positive_reference_support_m2": float(np.min(support)),
        "minimum_squared_detection_ratio_interval": [
            float(lower_eigen[0]), float(upper_eigen[0])],
        "alternating_mode_ratio_interval": alternating_interval,
        "minimum_mode_relative_coefficients": weakest.tolist(),
        "maximum_relative_fourier_tail_bound": tail_relative,
        "independent_gram_relative_error": gram_error,
        "independent_element_energy_relative_error": energy_error,
        "structural_response_relative_residual": structural_residual,
        "compliance_symmetry_relative_error": symmetry,
        "elapsed_seconds": time.perf_counter()-started,
    }
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "status", "cells_each_axis", "cut_fraction",
        "minimum_squared_detection_ratio_interval",
        "alternating_mode_ratio_interval", "maximum_relative_fourier_tail_bound",
        "elapsed_seconds",
    )}, indent=2))


if __name__ == "__main__":
    main()

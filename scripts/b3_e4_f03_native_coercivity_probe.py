"""Bounded straight native B3 energy/coercivity development discriminator.

This compares stationary-resultant physical energy with an independently
assembled half-cell strain energy on three existing fixtures. Finite-grid
eigenvalues cannot prove a mesh-uniform inequality or qualify F03.
"""

from __future__ import annotations

import json

import numpy as np
from scipy import linalg
from threadpoolctl import threadpool_info

from scripts._b3_e4_f03_native_fixture import SECTION_DIAGONAL, build
from scripts.b3_e4_f03_native_broken_l2 import _physical_beam


def _skew(vector):
    x, y, z = vector
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def canonical_energy(fixture, physical):
    """Return independent A/B half-cell energy, restricted to root-supported q."""
    count = fixture.context.count
    rows = np.zeros((9*fixture.n_half_cells, count))
    scales = np.zeros(9*fixture.n_half_cells)
    for half in range(fixture.n_half_cells):
        left, right = half, half+1
        length = fixture.abscissae[right]-fixture.abscissae[left]
        if length <= 0.:
            raise AssertionError("positive native material half-cell required")
        spin = fixture.context.nodal_count+24*(half//2)+3*(half%2)
        first = 9*half
        rows[first:first+3, 6*left:6*left+3] = -np.eye(3)
        rows[first:first+3, 6*right:6*right+3] = np.eye(3)
        rows[first:first+3, spin:spin+3] = _skew((length, 0., 0.))
        rows[first+3:first+6, 6*left+3:6*left+6] = -np.eye(3)
        rows[first+3:first+6, spin:spin+3] = np.eye(3)
        rows[first+6:first+9, 6*right+3:6*right+6] = np.eye(3)
        rows[first+6:first+9, spin:spin+3] = -np.eye(3)
        scales[first:first+3] = SECTION_DIAGONAL[:3]/length
        scales[first+3:first+6] = SECTION_DIAGONAL[3:]/length
        scales[first+6:first+9] = SECTION_DIAGONAL[3:]/length
    restricted = rows[:, physical]
    energy = restricted.T@(scales[:, None]*restricted)
    return energy, restricted, scales


def report(half_cells):
    fixture = build(half_cells, z_offset=.0675, assemble=True)
    physical, _, native = _physical_beam(fixture)
    canonical, strains, scales = canonical_energy(fixture, physical)
    linalg.cho_factor(canonical, lower=True, check_finite=True)
    spectrum, modes = linalg.eigh(native, canonical, check_finite=True)
    if not np.isfinite(spectrum).all() or spectrum[0] <= 0.:
        raise AssertionError("positive bounded physical/canonical energies required")
    soft = modes[:, 0]
    density = scales*(strains@soft)**2
    closed_form = np.zeros_like(native)
    for half in range(half_cells):
        length = fixture.abscissae[half+1]-fixture.abscissae[half]
        block = np.zeros((9, 9))
        block[:3, :3] = np.diag(SECTION_DIAGONAL[:3]/length)
        rotational = np.diag(SECTION_DIAGONAL[3:]/length)
        block[3:6, 3:6] = 4*rotational
        block[6:9, 6:9] = 4*rotational
        block[3:6, 6:9] = -2*rotational
        block[6:9, 3:6] = -2*rotational
        rows = strains[9*half:9*(half+1)]
        closed_form += rows.T@block@rows
    closed_form_relative_error = float(
        np.linalg.norm(native-closed_form, ord=np.inf)/
        np.linalg.norm(native, ord=np.inf))
    if closed_form_relative_error > 1e-10:
        raise AssertionError("straight diagonal-section local compliance formula failed")
    expected_spectrum = np.repeat((1., 2., 6.), 3*half_cells)
    return {
        "half_cells": half_cells,
        "physical_dofs": len(physical),
        "minimum_energy_ratio": float(spectrum[0]),
        "maximum_energy_ratio": float(spectrum[-1]),
        "closed_form_relative_error": closed_form_relative_error,
        "ratio_pattern_max_abs": float(np.max(np.abs(spectrum-expected_spectrum))),
        "soft_mode_translation_strain_fraction": float(
            density.reshape(-1, 9)[:, :3].sum()/density.sum()),
        "soft_mode_rotation_strain_fraction": float(
            density.reshape(-1, 9)[:, 3:].sum()/density.sum()),
        "sparse_dense_max_abs": fixture.dense_oracle_max_error,
    }


if __name__ == "__main__":
    print(json.dumps({
        "scope": "bounded finite-grid coercivity discriminator; not a uniform proof or F03 acceptance",
        "threadpools": [{"api": row["internal_api"], "threads": row["num_threads"]}
                        for row in threadpool_info()],
        "cases": [report(n) for n in (4, 8, 16)],
    }, indent=2))

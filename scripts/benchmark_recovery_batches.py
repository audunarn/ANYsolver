"""Benchmark the legacy isotropic S4 kernel against its scalar oracle."""

from __future__ import annotations

import argparse
import json
import statistics
import time
import warnings
from typing import Callable, Dict, Mapping

import numpy as np

from anysolver import RecoveryConfig, ResourceConfig, generate_simple_panel_mesh
from anysolver.elements import LegacyQ4DeprecationWarning, LegacyShellElement
from anysolver.recovery import (
    _compute_one_element_stress,
    recover_element_stresses_with_report,
)


_COMPILED_ISOTROPIC_S4_FIELDS = frozenset(
    {
        "bending_xx",
        "bending_xy",
        "bending_yy",
        "equivalent_stress",
        "equivalent_stress_measure",
        "hill_utilization",
        "membrane_xx",
        "membrane_xy",
        "membrane_yy",
        "shear_xz",
        "shear_yz",
        "von_mises",
    }
)


def _timings(call: Callable[[], object], repeats: int) -> list[float]:
    values = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        values.append(float(time.perf_counter() - start))
    return values


def _maximum_error(
    reference: Mapping[int, Mapping[str, object]],
    candidate: Mapping[int, Mapping[str, object]],
) -> float:
    maximum = 0.0
    for element_id, actual_fields in candidate.items():
        expected_fields = reference.get(element_id)
        if expected_fields is None or set(actual_fields) != _COMPILED_ISOTROPIC_S4_FIELDS:
            return float("inf")
        for field, actual in actual_fields.items():
            if field not in expected_fields:
                return float("inf")
            expected = expected_fields[field]
            if isinstance(expected, str):
                if actual != expected:
                    return float("inf")
                continue
            expected_array = np.asarray(expected, dtype=float)
            actual_array = np.asarray(actual, dtype=float)
            maximum = max(
                maximum,
                float(np.max(np.abs(actual_array - expected_array), initial=0.0)),
            )
    if set(reference) != set(candidate):
        return float("inf")
    return maximum


def _select_explicit_legacy_s4(model: object) -> None:
    """Replace generated Q4 defaults with the kernel's exact legacy target."""

    mesh = model.mesh
    with warnings.catch_warnings():
        # The benchmark intentionally exercises the still-supported legacy
        # kernel; its private construction should not corrupt JSON output.
        warnings.simplefilter("ignore", LegacyQ4DeprecationWarning)
        for element_id, element in tuple(mesh.elements.items()):
            model.add_element(
                element_id,
                LegacyShellElement(
                    element_id,
                    list(element.node_ids),
                    element.material_name,
                    thickness=element.thickness,
                ),
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nx", type=int, default=20)
    parser.add_argument("--ny", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--return-global", action="store_true")
    args = parser.parse_args()
    if min(args.nx, args.ny, args.repeats, args.threads) <= 0:
        parser.error("nx, ny, repeats, and threads must be positive")

    model = generate_simple_panel_mesh(
        float(args.nx),
        float(args.ny),
        0.01,
        num_divisions_x=args.nx,
        num_divisions_y=args.ny,
    )
    _select_explicit_legacy_s4(model)
    displacements = np.linspace(
        0.0,
        1.0e-5,
        model.mesh.dof_manager.total_dofs,
    )
    recovery = RecoveryConfig(components=None)
    resources = ResourceConfig(recovery_threads=args.threads)

    def scalar() -> Dict[int, Mapping[str, object]]:
        result: Dict[int, Mapping[str, object]] = {}
        for element_id in model.mesh.elements:
            item = _compute_one_element_stress(
                model,
                displacements,
                element_id,
                return_global=args.return_global,
            )
            if item is not None:
                result[item[0]] = item[1]
        return result

    def compiled():
        return recover_element_stresses_with_report(
            model,
            displacements,
            recovery,
            return_global=args.return_global,
            resource_config=resources,
        )

    # Warm JIT compilation and the bounded plan outside measured samples.
    compiled()
    scalar_reference = scalar()
    compiled_reference, report = compiled()
    if report.metadata["recovery_backend"] != "compiled_isotropic_s4":
        raise RuntimeError(
            "benchmark requires the compiled legacy isotropic S4 recovery path"
        )
    scalar_seconds = _timings(scalar, args.repeats)
    compiled_seconds = _timings(compiled, args.repeats)
    scalar_median = float(statistics.median(scalar_seconds))
    compiled_median = float(statistics.median(compiled_seconds))
    payload = {
        "status": "completed",
        "elements": len(model.mesh.elements),
        "formulation": "legacy-s4",
        "return_global": bool(args.return_global),
        "threads": int(args.threads),
        "repeats": int(args.repeats),
        "scalar_seconds": scalar_seconds,
        "compiled_seconds": compiled_seconds,
        "scalar_median_seconds": scalar_median,
        "compiled_median_seconds": compiled_median,
        "speedup": scalar_median / max(compiled_median, np.finfo(float).tiny),
        "maximum_absolute_error": _maximum_error(
            scalar_reference,
            compiled_reference,
        ),
        "diagnostics": report.to_dict()["metadata"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

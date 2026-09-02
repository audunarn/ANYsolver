"""Isolated V2D runtime adapter for the frozen Stage 4A scientific producer.

The historical proof schema retains its ``e4-pl-s3-v2`` selector and V2A slot
names.  A bounded re-authoring of the frozen producer's model builder changes
only the S3 factory selector to the accepted V2D selector.  No production
symbol is replaced, even temporarily.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Mapping


REFERENCE = Path(__file__).resolve().parent
BASE_PRODUCER_PATH = REFERENCE / "e4_pl_s3_v2_flat_funnel_producer.py"
BASE_PRODUCER_SHA256 = "A8FD7258303AA3D73968AAE775BCC0C4A31C88B6E7F2F1DF44F8A1D00180CB3F"
SCIENTIFIC_SELECTOR_SLOT = "e4-pl-s3-v2"
RUNTIME_SELECTOR = "e4-pl-s3-v2d"
V2D_FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1"
V2D_IMPLEMENTATION_ID = "E4_PL_S3_V2D_RECOVERY_CURRENT_EIGEN_GATE_V1"
ADAPTER_POLICY_ID = "S3_V6H_HISTORICAL_SCHEMA_SLOT_TO_EXACT_V2D_FACTORY_V1"


class V6HAdapterError(RuntimeError):
    """Raised when the frozen producer or runtime class differs."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_base() -> ModuleType:
    if _sha256(BASE_PRODUCER_PATH) != BASE_PRODUCER_SHA256:
        raise V6HAdapterError("frozen Stage 4A producer identity differs")
    reference_text = str(REFERENCE)
    inserted = reference_text not in sys.path
    if inserted:
        sys.path.insert(0, reference_text)
    try:
        spec = importlib.util.spec_from_file_location(
            "_s3_v6h_frozen_stage4a_producer", BASE_PRODUCER_PATH
        )
        if spec is None or spec.loader is None:
            raise V6HAdapterError("cannot load frozen Stage 4A producer")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if inserted:
            sys.path.remove(reference_text)


_BASE = _load_base()
_CONFIGURED = False


def _adapted_build_model(
    record: Mapping[str, Any],
    *,
    s3_selector: str,
) -> tuple[Any, dict[int, str], dict[str, int], dict[str, int]]:
    """Reconstruct the frozen topology with only the S3 selector changed."""

    candidate_root = (
        Path(_BASE._ACTIVE_CANDIDATE_ROOT).resolve()
        if _BASE._ACTIVE_CANDIDATE_ROOT is not None
        else REFERENCE.parents[1].resolve()
    )
    candidate_source = (candidate_root / "src").resolve()
    try:
        candidate_source.relative_to(candidate_root)
    except ValueError as exc:
        raise V6HAdapterError("candidate source escapes its frozen root") from exc
    loaded = sys.modules.get("anysolver")
    if loaded is None:
        source_text = str(candidate_source)
        if source_text in sys.path:
            sys.path.remove(source_text)
        sys.path.insert(0, source_text)
    else:
        loaded_path = Path(str(getattr(loaded, "__file__", ""))).resolve()
        try:
            loaded_path.relative_to(candidate_source)
        except ValueError as exc:
            raise V6HAdapterError(
                "loaded ANYsolver is outside the frozen candidate source"
            ) from exc

    import numpy as np
    from anysolver.boundary import LoadCase
    from anysolver.elements import create_shell_element
    from anysolver.fe_core import FEModel

    if s3_selector not in {SCIENTIFIC_SELECTOR_SLOT, "e4-pl-s3"}:
        raise V6HAdapterError("Stage 4A adapter selector is outside its scope")
    generator = _BASE._load_manifest_generator()
    level = int(record["level"])
    split_count = int(record["split_base_cell_count"])
    mask = str(record["mask"])
    diagonal = str(record["diagonal"])
    base_cells = (
        () if split_count == 0 else generator.selected_base_cells(mask, split_count)
    )
    split_cells = set(generator.expanded_split_cells(base_cells, level))
    if len(split_cells) != int(record["split_refined_cell_count"]):
        raise V6HAdapterError("refined split cells differ from the frozen manifest")

    model = FEModel(
        f"S3_V2_PHASE4A_{s3_selector}_{level}_{mask}_{diagonal}"
    )
    model.add_material(
        "phase4a_steel",
        _BASE.ELASTIC_MODULUS,
        _BASE.POISSON_RATIO,
        density=_BASE.DENSITY,
    )
    for j in range(level + 1):
        for i in range(level + 1):
            model.add_node(
                _BASE._node_id(i, j, level),
                _BASE.LENGTH * i / level,
                _BASE.WIDTH * j / level,
                0.0,
            )

    kinds: dict[int, str] = {}
    formulation_counts = {"qualified_q4": 0, "v2a_s3": 0, "v1_s3": 0}
    element_id = 0
    for j in range(level):
        for i in range(level):
            for kind, nodes in generator._cell_connectivity(
                i,
                j,
                level,
                split=(i, j) in split_cells,
                diagonal=diagonal,
            ):
                element_id += 1
                if kind == "Q4":
                    element = create_shell_element(
                        element_id,
                        list(nodes),
                        "phase4a_steel",
                        formulation="e4-pl",
                        thickness=_BASE.THICKNESS,
                        reference_normal=np.asarray((0.0, 0.0, 1.0)),
                        drilling_stabilization=0.001,
                        hourglass_stabilization=0.001,
                        pl_stabilization=1.0,
                        planar_tolerance=1.0e-10,
                        warped_formulation="varying_frame",
                    )
                    if getattr(element, "formulation_id", None) != _BASE.Q4_FORMULATION_ID:
                        raise V6HAdapterError(
                            "Q4 factory did not return the qualified Q4"
                        )
                    formulation_counts["qualified_q4"] += 1
                else:
                    runtime_selector = (
                        RUNTIME_SELECTOR
                        if s3_selector == SCIENTIFIC_SELECTOR_SLOT
                        else "e4-pl-s3"
                    )
                    kwargs: dict[str, Any] = {
                        "formulation": runtime_selector,
                        "thickness": _BASE.THICKNESS,
                        "reference_normal": np.asarray((0.0, 0.0, 1.0)),
                    }
                    if runtime_selector == "e4-pl-s3":
                        kwargs["director_polarity"] = 1
                    element = create_shell_element(
                        element_id,
                        list(nodes),
                        "phase4a_steel",
                        **kwargs,
                    )
                    if s3_selector == SCIENTIFIC_SELECTOR_SLOT:
                        if (
                            type(element).__name__
                            != "NativeParityE4PLS3V2DShellElement"
                            or getattr(element, "formulation_id", None)
                            != V2D_FORMULATION_ID
                            or getattr(element, "implementation_id", None)
                            != V2D_IMPLEMENTATION_ID
                        ):
                            raise V6HAdapterError(
                                "Stage 4A adapter did not construct exact V2D"
                            )
                        formulation_counts["v2a_s3"] += 1
                    else:
                        if (
                            getattr(element, "formulation_id", None)
                            != _BASE.V1_FORMULATION_ID
                        ):
                            raise V6HAdapterError(
                                "Stage 4A diagnostic factory did not construct V1"
                            )
                        formulation_counts["v1_s3"] += 1
                model.add_element(element_id, element)
                kinds[element_id] = kind

    topology_digest = generator.connectivity_sha256(
        level, frozenset(split_cells), diagonal
    )
    if topology_digest != record["connectivity_sha256"]:
        raise V6HAdapterError("constructed connectivity differs from the manifest")
    element_counts = {
        "Q4": sum(kind == "Q4" for kind in kinds.values()),
        "S3": sum(kind == "S3" for kind in kinds.values()),
    }
    if element_counts != {
        "Q4": int(record["q4_element_count"]),
        "S3": int(record["s3_element_count"]),
    }:
        raise V6HAdapterError("constructed element counts differ from the manifest")
    supports = _BASE._hard_navier_supports(model, level)
    load = LoadCase("phase4a_uniform_dead_pressure")
    for registered_id in model.mesh.elements:
        load.add_pressure_load(int(registered_id), _BASE.PRESSURE)
    model.add_load_case(load)
    return model, kinds, element_counts, formulation_counts | supports


def configure() -> ModuleType:
    """Bind the immutable V2D identity without changing proof schemas."""

    global _CONFIGURED
    if not _CONFIGURED:
        if _BASE.SELECTOR != SCIENTIFIC_SELECTOR_SLOT:
            raise V6HAdapterError("frozen Stage 4A selector slot differs")
        _BASE.V2A_FORMULATION_ID = V2D_FORMULATION_ID
        _BASE._build_model = _adapted_build_model
        _CONFIGURED = True
    if (
        _BASE.V2A_FORMULATION_ID != V2D_FORMULATION_ID
        or _BASE._build_model is not _adapted_build_model
    ):
        raise V6HAdapterError("configured Stage 4A adapter identity differs")
    return _BASE


def build_model_for_validation(
    record: Mapping[str, Any],
) -> tuple[Any, dict[int, str], dict[str, int], dict[str, int]]:
    """Build one topology without solving, for bounded disposable validation."""

    base = configure()
    return base._build_model(record, s3_selector=SCIENTIFIC_SELECTOR_SLOT)


def produce_case(member: Mapping[str, Any]) -> dict[str, Any]:
    """Run one unchanged scientific case using the exact V2D runtime class."""

    base = configure()
    return base.produce_case(member, s3_selector=SCIENTIFIC_SELECTOR_SLOT)


def disposable_validation_document() -> dict[str, Any]:
    """Run the frozen N20/1%/dispersed/slash pre-authority smoke case."""

    manifest = json.loads(_BASE.MANIFEST_PATH.read_bytes())
    for index, record in enumerate(manifest["records"]):
        if (
            record["level"] == 20
            and record["s3_area_fraction_percent"] == 1
            and record["mask"] == "dispersed"
            and record["diagonal"] == "slash"
        ):
            member = {
                "manifest_index": index,
                "record": record,
                "record_id": "V6H_DISPOSABLE_N20_1PCT_DISPERSED_SLASH",
            }
            return {
                "adapter_policy_id": ADAPTER_POLICY_ID,
                "candidate_formulation_id": V2D_FORMULATION_ID,
                "candidate_implementation_id": V2D_IMPLEMENTATION_ID,
                "record": produce_case(member),
                "schema": "anysolver.e4-pl-s3-v6h-disposable-validation-v1",
            }
    raise V6HAdapterError("frozen disposable validation record is absent")


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--emit-disposable-validation":
        output = Path(sys.argv[2]).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        raw = (
            json.dumps(
                disposable_validation_document(),
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        with output.open("xb") as handle:
            handle.write(raw)
        return 0
    return int(configure().main())


if __name__ == "__main__":
    raise SystemExit(main())

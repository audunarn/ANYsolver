from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "docs" / "reference_cases" / "e4_pl_s3_mixed_mesh_manifest.py"
MANIFEST = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"
)
MANIFEST_SHA256 = "3EA7ABD0B332831D62B30B3CD52E0DB85EC951B125340FFAF40A891DC37BD589"
QUALIFICATION_CONTRACT = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_mixed_mesh_qualification_contract.json"
)
QUALIFICATION_CONTRACT_SHA256 = (
    "091D6D63BF0950B8A5CBB298095E0787DEB78ECD4954E9F421741259F1E93FDD"
)
QUALIFIED_Q4_MECHANICS = ROOT / "src" / "anysolver" / "e4_pl_element.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("e4_pl_s3_mixed_mesh_manifest", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _strict_json(raw: bytes) -> object:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate key {key!r}")
            value[key] = item
        return value

    def reject_constant(value: str) -> object:
        raise ValueError(f"nonfinite JSON constant {value!r}")

    return json.loads(
        raw,
        object_pairs_hook=reject_duplicates,
        parse_constant=reject_constant,
    )


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _node_id(i: int, j: int, level: int) -> int:
    return j * (level + 1) + i + 1


def _independent_connectivity_sha256(
    level: int,
    split_cells: set[tuple[int, int]],
    diagonal: str,
) -> str:
    digest = hashlib.sha256(f"level:{level}\n".encode("ascii"))
    element_id = 0
    for j in range(level):
        for i in range(level):
            n00 = _node_id(i, j, level)
            n10 = _node_id(i + 1, j, level)
            n11 = _node_id(i + 1, j + 1, level)
            n01 = _node_id(i, j + 1, level)
            if (i, j) not in split_cells:
                elements = (("Q4", (n00, n10, n11, n01)),)
            else:
                made = diagonal
                if made == "alternating":
                    made = "backslash" if (i + j) % 2 == 0 else "slash"
                if made == "backslash":
                    elements = (
                        ("S3", (n00, n10, n11)),
                        ("S3", (n00, n11, n01)),
                    )
                elif made == "slash":
                    elements = (
                        ("S3", (n00, n10, n01)),
                        ("S3", (n10, n11, n01)),
                    )
                else:  # pragma: no cover - the manifest schema excludes this
                    raise AssertionError(made)
            for kind, node_ids in elements:
                element_id += 1
                nodes = ",".join(str(node_id) for node_id in node_ids)
                digest.update(f"{element_id}:{kind}:{nodes}\n".encode("ascii"))
    return digest.hexdigest().upper()


def _signed_area_twice(node_ids: tuple[int, ...], level: int) -> int:
    stride = level + 1
    points = tuple(((node_id - 1) % stride, (node_id - 1) // stride) for node_id in node_ids)
    return sum(
        x0 * y1 - x1 * y0
        for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1])
    )


def test_generator_is_standard_library_only_and_mechanics_free() -> None:
    tree = ast.parse(GENERATOR.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    assert roots == {
        "__future__",
        "argparse",
        "hashlib",
        "json",
        "pathlib",
        "typing",
    }


def test_manifest_is_strict_canonical_and_bound_to_generator() -> None:
    raw = MANIFEST.read_bytes()
    payload = _strict_json(raw)
    assert hashlib.sha256(raw).hexdigest().upper() == MANIFEST_SHA256
    assert raw == _canonical_bytes(payload)
    assert payload == GEN.build_manifest()
    assert payload["schema"] == GEN.SCHEMA
    assert payload["connectivity_hash_encoding"] == GEN.HASH_ENCODING


def test_qualification_contract_is_canonical_and_binds_connectivity() -> None:
    raw = QUALIFICATION_CONTRACT.read_bytes()
    contract = _strict_json(raw)
    assert hashlib.sha256(raw).hexdigest().upper() == QUALIFICATION_CONTRACT_SHA256

    canonical_pretty = (
        json.dumps(
            contract,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )
    assert raw == canonical_pretty
    authority = contract["connectivity_authority"]
    manifest_raw = MANIFEST.read_bytes()
    manifest = _strict_json(manifest_raw)
    assert authority == {
        "bytes": len(manifest_raw),
        "gated_record_count": len(manifest["records"]),
        "path": (
            "docs/reference_cases/e4_pl_s3_mixed_mesh_connectivity_manifest.json"
        ),
        "research_control_record_count": len(
            manifest["research_control"]["records"]
        ),
        "schema": manifest["schema"],
        "sha256": hashlib.sha256(manifest_raw).hexdigest().upper(),
    }


def test_qualification_contract_binds_the_unchanged_q4_mechanics_blob() -> None:
    contract = _strict_json(QUALIFICATION_CONTRACT.read_bytes())
    candidate = contract["candidate"]
    raw = QUALIFIED_Q4_MECHANICS.read_bytes()
    relative = QUALIFIED_Q4_MECHANICS.relative_to(ROOT).as_posix()
    indexed = subprocess.run(
        ["git", "ls-files", "-s", "--", relative],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip().split()
    unchanged = subprocess.run(
        ["git", "diff", "--quiet", "--", relative],
        cwd=ROOT,
        check=False,
    )

    assert unchanged.returncode == 0
    assert indexed[:2] == ["100644", candidate["qualified_q4_mechanics_blob"]]
    assert candidate["qualified_q4_mechanics_sha256"] == (
        hashlib.sha256(raw).hexdigest().upper()
    )


def test_qualification_contract_freezes_all_gate_families_without_activation() -> None:
    contract = _strict_json(QUALIFICATION_CONTRACT.read_bytes())
    gates = contract["acceptance_gates"]
    assert set(gates) == {
        "batch",
        "buckling",
        "convergence",
        "interface_resultants",
        "locking",
        "modal",
        "patch_and_equilibrium",
        "performance",
        "pl_participation",
        "symmetry_and_covariance_residual_maximum",
    }
    assert contract["execution_policy"] == {
        "automatic_retry": False,
        "canonical_cycles": 2,
        "deterministic_cycle_equality": "BYTE_IDENTICAL_CANONICAL_AGGREGATES",
        "external_diagnostics": True,
        "maximum_memory_gib_per_process": 24,
        "maximum_seconds_per_process": 600,
        "numerical_library_threads_per_process": 1,
        "partial_output_is_canonical": False,
        "worker_directories": "FRESH_AND_DISTINCT",
    }
    assert contract["result_policy"]["present_status"] == (
        "PREREGISTERED_NOT_EXECUTED"
    )
    assert contract["result_policy"]["research_control_can_classify"] is False
    assert contract["ecosystem"]["default_activation"].startswith("FORBIDDEN_")


def test_campaign_has_exact_order_counts_and_fractions() -> None:
    payload = _strict_json(MANIFEST.read_bytes())
    records = payload["records"]
    assert isinstance(records, list)
    assert len(records) == 252
    expected_keys: list[tuple[int, str, str, int]] = []
    for split_count in GEN.SPLIT_COUNTS:
        masks = ("none",) if split_count == 0 else GEN.MASKS
        for mask in masks:
            for diagonal in GEN.DIAGONALS:
                for level in GEN.LEVELS:
                    expected_keys.append((split_count, mask, diagonal, level))
    actual_keys = [
        (
            record["split_base_cell_count"],
            record["mask"],
            record["diagonal"],
            record["level"],
        )
        for record in records
    ]
    assert actual_keys == expected_keys
    assert len(actual_keys) == len(set(actual_keys))

    for record in records:
        level = record["level"]
        split_count = record["split_base_cell_count"]
        factor = level // GEN.BASE_GRID
        split_refined = split_count * factor * factor
        assert record["node_count"] == (level + 1) ** 2
        assert record["split_refined_cell_count"] == split_refined
        assert record["q4_element_count"] == level**2 - split_refined
        assert record["s3_element_count"] == 2 * split_refined
        assert record["element_count"] == level**2 + split_refined
        assert record["s3_area_fraction_percent"] == split_count // 4

    research = payload["research_control"]
    assert research["classification"] == "RESEARCH_CONTROL_NOT_A_PRODUCTION_GATE"
    assert research["split_base_cell_count"] == GEN.BASE_GRID**2
    assert research["s3_area_fraction_percent"] == 100
    control_records = research["records"]
    assert [
        (record["diagonal"], record["level"]) for record in control_records
    ] == [
        (diagonal, level)
        for diagonal in GEN.DIAGONALS
        for level in GEN.LEVELS
    ]
    assert len(control_records) == 12
    for record in control_records:
        level = record["level"]
        assert record["mask"] == "all_cells"
        assert record["node_count"] == (level + 1) ** 2
        assert record["split_refined_cell_count"] == level**2
        assert record["q4_element_count"] == 0
        assert record["s3_element_count"] == 2 * level**2
        assert record["element_count"] == 2 * level**2
        assert record["s3_area_fraction_percent"] == 100


def test_masks_are_exact_nested_permutations_and_refine_one_to_four() -> None:
    all_cells = {(i, j) for j in range(GEN.BASE_GRID) for i in range(GEN.BASE_GRID)}
    for mask in GEN.MASKS:
        ordered = GEN.ordered_mask_cells(mask)
        assert len(ordered) == GEN.BASE_GRID**2
        assert set(ordered) == all_cells
        previous: set[tuple[int, int]] = set()
        for split_count in GEN.SPLIT_COUNTS[1:]:
            selected = set(GEN.selected_base_cells(mask, split_count))
            assert len(selected) == split_count
            assert previous < selected
            previous = selected
            for level in GEN.LEVELS:
                factor = level // GEN.BASE_GRID
                expanded = GEN.expanded_split_cells(tuple(selected), level)
                assert len(expanded) == split_count * factor * factor
                for i, j in selected:
                    assert {
                        (factor * i + di, factor * j + dj)
                        for dj in range(factor)
                        for di in range(factor)
                    } <= expanded


def test_all_connectivity_hashes_are_independently_reproducible() -> None:
    payload = _strict_json(MANIFEST.read_bytes())
    all_records = [
        *payload["records"],
        *payload["research_control"]["records"],
    ]
    for record in all_records:
        mask = record["mask"]
        split_count = record["split_base_cell_count"]
        level = record["level"]
        if mask == "none":
            base_cells = ()
        elif mask == "all_cells":
            base_cells = GEN._all_cells()
        else:
            base_cells = GEN.selected_base_cells(mask, split_count)
        split_cells = set(GEN.expanded_split_cells(base_cells, level))
        assert record["selected_base_cells_sha256"] == hashlib.sha256(
            _canonical_bytes(base_cells)
        ).hexdigest().upper()
        assert record["connectivity_sha256"] == _independent_connectivity_sha256(
            level,
            split_cells,
            record["diagonal"],
        )


@pytest.mark.parametrize("diagonal", GEN.DIAGONALS)
def test_q4_and_s3_connectivities_are_counterclockwise(diagonal: str) -> None:
    level = GEN.BASE_GRID
    for split in (False, True):
        for i, j in ((0, 0), (7, 11), (19, 19)):
            elements = GEN._cell_connectivity(
                i,
                j,
                level,
                split=split,
                diagonal=diagonal,
            )
            assert len(elements) == (2 if split else 1)
            for kind, node_ids in elements:
                assert kind == ("S3" if split else "Q4")
                assert _signed_area_twice(node_ids, level) > 0


def test_cli_check_accepts_canonical_and_rejects_mutation(tmp_path: Path) -> None:
    accepted = subprocess.run(
        [sys.executable, str(GENERATOR), "--check", str(MANIFEST)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert accepted.returncode == 0, accepted.stderr

    stale = tmp_path / "stale.json"
    payload = _strict_json(MANIFEST.read_bytes())
    payload["base_grid"] = 21
    stale.write_bytes(_canonical_bytes(payload))
    rejected = subprocess.run(
        [sys.executable, str(GENERATOR), "--check", str(stale)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert rejected.returncode != 0
    assert "not canonical or is stale" in rejected.stderr

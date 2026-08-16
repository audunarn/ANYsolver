"""Independent Stage-M oracle for the compatible-H_D S4 candidate.

The module is proof infrastructure.  It content-addresses every inherited
input, reconstructs Candidate B without importing ANYsolver, and emits only
canonical JSON.  Production dispatch is intentionally absent.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from decimal import Decimal
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
import stat
import sys
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "anysolver.s4.stage-m-mechanics-output-v1"
SHARD_SCHEMA = "anysolver.s4.stage-m-mechanics-precision-shard-v1"
CONTRACT_SCHEMA = "anysolver.s4.stage-m-mechanics-contract-v1"
CANDIDATE_ID = "mitc4_plus_hd_compatible_surface_v1"
GOVERNING_SHA256 = "17CB914002E362A5DB2B475981A46020C1F39E8BA5398B4A7BEC64C39EEEC4A7"
PLAN_SHA256 = "4AE07F5954C9A2E6E6B002BEA24A9FC274B528D405EE6E5FCACE630893021E5B"
SOURCE_MANIFEST_SHA256 = "22B7B9D56DCC180CEE29F43AD4F31C69547A7C74CB212FD5B7D301909A8C0BE6"
CONSTRAINED_DERIVATION_SHA256 = "577BD98FC5609629BC078B27719ED72985E4BA81536A7C6D76CBA687322D5488"
ENERGETIC_DERIVATION_SHA256 = "ACD03B67474BF35A06B2183830E3195843D4254DB17F04A5540724F42EC9F3A5"
CASES_SHA256 = "912E07377C174E1FE031EEBA98DD5E8406C9A294AF2B3032D9AB5B38F67C7B94"
INTERVAL_SHA256 = "05C086DB11548AA4B77A5B31A5171792E08C053F93682D5FBED2D16425C16CC3"
BASE_ORACLE_SHA256 = "0112EF21FCF56672EB09DFB2FB5E179637C1BF1E026FE92D07CD919DFB91A12F"
MULTIPLIERS = ("0.25", "1", "4")
PRECISIONS = (80, 160, 320)

# Science dependencies are loaded only after the static, content-addressed
# contract checkpoint.  In particular, ``--emit-contract`` must neither import
# nor execute any frozen Python input.
mp: Any = None
BASE: Any = None
INTERVAL: Any = None


INHERITED_INPUTS: tuple[tuple[str, str], ...] = (
    ("tests/test_s4_eq21_eq25_reference.py", "E5112C7BF98A5C1F8F3FB28D2331B76B9B872F073372D0E7045AA59E70703B36"),
    ("docs/reference_cases/s4_nullspace_semantics_cases.json", "223C0E1A1F03D30AA5EFBB13E8ECD8F64E5F7F0865E6F11274577D15C6691ABF"),
    ("tests/test_s4_nullspace_semantics_proof.py", "B6E23E5C1D1F90702464487707345E14D0A2A65B87D18D0076EB546064B789F3"),
    ("docs/reference_cases/s4_drill_constraint_cases.json", "B4D663382302E971752F0757F6E869549A54234F485235E06DBEF74085860F38"),
    ("tests/test_s4_drill_constraint_derivation.py", "63B36AFEA4AC7C082F5BF46FB1E0A7EAA5D30ACD6E8F1D2172139E62741B7B80"),
    ("tests/test_s4_geometry_handoff.py", "942BCAF44FCA897A231F0685EF6466BCC1ED1716C017C644677606C58AEE3250"),
    ("tests/test_s4_restricted_integration.py", "15EE81C022CCAC1BF425308479F01978C355CA002A460C334C9921DFC8E94C30"),
    ("tests/test_s4_restricted_activity.py", "AAEDCA8FE1AB61552A4566BACF73855FCEF0F49CE20501901E2D3CDCCA8068B4"),
    ("docs/reference_cases/s4_restricted_release_contract.json", "08950098FD43473DCAEFA6C3ABFE35C95AA45441D1D677288FB4CEF6949227CD"),
    ("tests/test_s4_improved_qualification.py", "B77C7A854A3C8A5780600DE983F95831DD500B0271EEFF7260399E53FC313053"),
)


class MechanicsInputError(ValueError):
    """Fail-closed input, identity, or grammar violation."""


class MechanicsContractError(ValueError):
    """Fail-closed mismatch in the registered static mechanics contract."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def cases_path() -> Path:
    return Path(__file__).with_name("s4_stage_m_mechanics_cases.json")


def contract_path() -> Path:
    return Path(__file__).with_name("s4_stage_m_mechanics_contract.json")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _strict_text_bytes(data: bytes, label: str) -> str:
    if data.startswith(b"\xef\xbb\xbf"):
        raise MechanicsInputError(f"BOM is forbidden: {label}")
    if b"\r" in data:
        without_pairs = data.replace(b"\r\n", b"")
        if b"\r" in without_pairs:
            raise MechanicsInputError(f"lone CR is forbidden: {label}")
        if b"\n" in without_pairs:
            raise MechanicsInputError(f"mixed LF/CRLF transport is forbidden: {label}")
        data = data.replace(b"\r\n", b"\n")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise MechanicsInputError(f"input is not UTF-8: {label}") from error
    if not text.endswith("\n"):
        raise MechanicsInputError(f"terminal LF is required: {label}")
    return text


def _strict_text(path: Path) -> str:
    return _strict_text_bytes(path.read_bytes(), str(path))


def _reject_json_constant(value: str) -> None:
    raise MechanicsInputError(f"nonfinite JSON constant is forbidden: {value}")


def _pairs_no_duplicates(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MechanicsInputError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, Any]:
    return _load_json_bytes(path.read_bytes(), str(path))


def _load_json_bytes(data: bytes, label: str) -> dict[str, Any]:
    value = json.loads(
        _strict_text_bytes(data, label),
        object_pairs_hook=_pairs_no_duplicates,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(value, dict):
        raise MechanicsInputError(f"top-level JSON object required: {label}")
    return value


def _canonicalize(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, tuple):
        return [_canonicalize(item) for item in value]
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise MechanicsInputError("canonical JSON keys must be strings")
        return {key: _canonicalize(value[key]) for key in sorted(value)}
    raise MechanicsInputError(f"noncanonical JSON type: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            _canonicalize(value),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _verified_bytes(relative: str, sha256: str) -> tuple[Path, bytes]:
    path = (repository_root() / relative).resolve()
    root = repository_root().resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise MechanicsInputError(f"path escapes repository: {relative}") from error
    if not path.is_file():
        raise MechanicsInputError(f"required file is absent: {relative}")
    data = path.read_bytes()
    actual = _sha256_bytes(data)
    if actual != sha256.upper():
        raise MechanicsInputError(
            f"hash mismatch for {relative}: expected {sha256.upper()}, got {actual}"
        )
    return path, data


def _verified_path(relative: str, sha256: str) -> Path:
    return _verified_bytes(relative, sha256)[0]


def _literal_string(node: ast.AST, name: str) -> str:
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        raise MechanicsInputError(f"{name} must be a literal string")
    return node.value


def _ast_row_digest(node: ast.AST) -> str:
    return _sha256_bytes(ast.dump(node, annotate_fields=True, include_attributes=False).encode("utf-8"))


def _occurrence(
    inventory_ordinal: int,
    path: str,
    locator: str,
    kind: str,
    identifier: str,
) -> dict[str, Any]:
    result = {
        "inventory_ordinal": inventory_ordinal,
        "path": path,
        "locator": locator,
        "kind": kind,
        "id": identifier,
        "id_utf8_hex": identifier.encode("utf-8").hex(),
    }
    return result


def _module_functions(
    tree: ast.Module, inventory_ordinal: int, path: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    functions.sort(key=lambda node: (node.lineno, node.col_offset))
    for node in functions:
        result.append(
            _occurrence(
                inventory_ordinal,
                path,
                f"/{node.name}@{node.lineno}:{node.col_offset}",
                "python_test_function",
                node.name,
            )
        )
    return result


def _find_function(tree: ast.Module, name: str) -> ast.FunctionDef:
    matches = [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if len(matches) != 1:
        raise MechanicsInputError(f"expected one function {name}, got {len(matches)}")
    return matches[0]


def _extract_case_coordinate_keys(
    tree: ast.Module, inventory_ordinal: int, path: str
) -> list[dict[str, Any]]:
    function = _find_function(tree, "_case_coordinates")
    returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
    if len(returns) != 1 or not isinstance(returns[0].value, ast.Dict):
        raise MechanicsInputError("_case_coordinates must return one literal dict")
    result: list[dict[str, Any]] = []
    for ordinal, key in enumerate(returns[0].value.keys):
        identifier = _literal_string(key, "_case_coordinates key")
        result.append(
            _occurrence(
                inventory_ordinal,
                path,
                f"/_case_coordinates/return/{ordinal}",
                "python_literal_case_key",
                identifier,
            )
        )
    if len(result) != 6:
        raise MechanicsInputError("_case_coordinates must have six frozen keys")
    return result


def _extract_worker_checks(
    tree: ast.Module, inventory_ordinal: int, path: str
) -> list[dict[str, Any]]:
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_WORKER_CHECKS" for target in node.targets)
    ]
    if len(assignments) != 1 or not isinstance(assignments[0].value, ast.Tuple):
        raise MechanicsInputError("_WORKER_CHECKS must be one literal name tuple")
    result: list[dict[str, Any]] = []
    for ordinal, item in enumerate(assignments[0].value.elts):
        if not isinstance(item, ast.Name):
            raise MechanicsInputError("_WORKER_CHECKS entries must be names")
        result.append(
            _occurrence(
                inventory_ordinal,
                path,
                f"/_WORKER_CHECKS/{ordinal}",
                "python_worker_check",
                item.id,
            )
        )
    if len(result) != 13:
        raise MechanicsInputError("_WORKER_CHECKS must contain 13 names")
    return result


def _extract_benchmark_case_ids(
    tree: ast.Module, inventory_ordinal: int, path: str
) -> list[dict[str, Any]]:
    function = _find_function(tree, "test_benchmark_protocol_uses_all_frozen_kernel_hard_gates")
    candidates: list[ast.Set] = [node for node in ast.walk(function) if isinstance(node, ast.Set)]
    sets = [
        node
        for node in candidates
        if len(node.elts) == 8
        and all(isinstance(item, ast.Constant) and isinstance(item.value, str) for item in node.elts)
    ]
    if len(sets) != 1:
        raise MechanicsInputError("benchmark gate must contain one literal eight-ID set")
    return [
        _occurrence(
            inventory_ordinal,
            path,
            f"/test_benchmark_protocol_uses_all_frozen_kernel_hard_gates/set/{ordinal}",
            "python_benchmark_case_id",
            _literal_string(item, "benchmark case ID"),
        )
        for ordinal, item in enumerate(sets[0].elts)
    ]


def _parameter_decorator_rows(
    tree: ast.Module,
    inventory_ordinal: int,
    path: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for function in [node for node in tree.body if isinstance(node, ast.FunctionDef)]:
        for decorator in function.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            call_name = ast.unparse(decorator.func)
            if call_name != "pytest.mark.parametrize" or len(decorator.args) < 2:
                continue
            values = decorator.args[1]
            expanded: list[ast.AST]
            if isinstance(values, (ast.Tuple, ast.List)):
                expanded = list(values.elts)
            elif (
                isinstance(values, ast.Call)
                and isinstance(values.func, ast.Name)
                and values.func.id == "tuple"
                and len(values.args) == 1
                and isinstance(values.args[0], ast.Call)
                and isinstance(values.args[0].func, ast.Name)
                and values.args[0].func.id == "_case_coordinates"
            ):
                case_function = _find_function(tree, "_case_coordinates")
                return_node = next(node for node in ast.walk(case_function) if isinstance(node, ast.Return))
                if not isinstance(return_node.value, ast.Dict):
                    raise MechanicsInputError("computed case parameter source is not a literal dict")
                expanded = [key for key in return_node.value.keys if key is not None]
            else:
                raise MechanicsInputError(
                    f"unknown parameter grammar at {path}:{function.lineno}"
                )
            for ordinal, row in enumerate(expanded):
                rows.append(
                    {
                        "inventory_ordinal": inventory_ordinal,
                        "path": path,
                        "test_locator": function.name,
                        "row_ordinal": ordinal,
                        "canonical_ast_row_sha256": _ast_row_digest(row),
                    }
                )
    return rows


def _json_occurrence(
    inventory_ordinal: int,
    path: str,
    locator: str,
    kind: str,
    identifier: Any,
) -> dict[str, Any]:
    if not isinstance(identifier, str):
        raise MechanicsInputError(f"JSON ID must be a string: {path}{locator}")
    return _occurrence(inventory_ordinal, path, locator, kind, identifier)


def _nullspace_occurrences(
    data: Mapping[str, Any], inventory_ordinal: int, path: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for ordinal, key in enumerate(("quotient_counterexample", "inherited_scale_family")):
        record = data["algebraic_cases"][key]
        result.append(_json_occurrence(inventory_ordinal, path, f"/algebraic_cases/{key}/id", "json_case_id", record["id"]))
    for ordinal, record in enumerate(data["local_cases"]):
        result.append(_json_occurrence(inventory_ordinal, path, f"/local_cases/{ordinal}/id", "json_case_id", record["id"]))
        for variant_ordinal, variant in enumerate(record.get("numbering_variants", [])):
            result.append(
                _json_occurrence(
                    inventory_ordinal,
                    path,
                    f"/local_cases/{ordinal}/numbering_variants/{variant_ordinal}/id",
                    "json_qualified_variant_id",
                    f"{record['id']}::{variant['id']}",
                )
            )
    for ordinal, record in enumerate(data["topology_cases"]):
        result.append(_json_occurrence(inventory_ordinal, path, f"/topology_cases/{ordinal}/id", "json_case_id", record["id"]))
        for subordinal, constraint in enumerate(record.get("constraint_sets", [])):
            result.append(
                _json_occurrence(
                    inventory_ordinal,
                    path,
                    f"/topology_cases/{ordinal}/constraint_sets/{subordinal}/id",
                    "json_qualified_subcase_id",
                    f"{record['id']}::{constraint['id']}",
                )
            )
    return result


def _drill_occurrences(
    data: Mapping[str, Any], inventory_ordinal: int, path: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    result: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    for ordinal, record in enumerate(data["local_cases"]):
        result.append(_json_occurrence(inventory_ordinal, path, f"/local_cases/{ordinal}/id", "json_case_id", record["id"]))
    for ordinal, record in enumerate(data["topology_cases"]):
        result.append(_json_occurrence(inventory_ordinal, path, f"/topology_cases/{ordinal}/id", "json_case_id", record["id"]))
        for subordinal, constraint in enumerate(record.get("constraint_sets", [])):
            result.append(
                _json_occurrence(
                    inventory_ordinal,
                    path,
                    f"/topology_cases/{ordinal}/constraint_sets/{subordinal}/id",
                    "json_qualified_subcase_id",
                    f"{record['id']}::{constraint['id']}",
                )
            )
    def walk_probe(value: Any, locator: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                walk_probe(item, f"{locator}/{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk_probe(item, f"{locator}/{index}")
        elif isinstance(value, str):
            result.append(_json_occurrence(inventory_ordinal, path, locator, "json_probe_id", value))
        else:
            raise MechanicsInputError(f"probe ID leaf is not a string: {locator}")
    walk_probe(data["probe_ids"], "/probe_ids")
    covariance = data["derived_variants"]["warped_numbering_covariance"]
    for variant in ("cyclic", "anchored_reversal"):
        result.append(
            _json_occurrence(
                inventory_ordinal,
                path,
                f"/derived_variants/warped_numbering_covariance/{variant}",
                "json_qualified_variant_id",
                f"{covariance['topology_id']}::{variant}",
            )
        )
    for ordinal, row in enumerate(data["sample_points"]):
        sample_rows.append(
            {
                "inventory_ordinal": inventory_ordinal,
                "path": path,
                "row_ordinal": ordinal,
                "canonical_row_sha256": _sha256_bytes(canonical_json_bytes(row)),
            }
        )
    return result, sample_rows


def _release_tokens(data: Mapping[str, Any], inventory_ordinal: int, path: str) -> list[dict[str, Any]]:
    values: list[tuple[str, str]] = [
        ("/default_formulation/id", data["default_formulation"]["id"]),
        ("/improved_formulation/id", data["improved_formulation"]["id"]),
    ]
    values.extend((f"/deferred_scopes/{index}", value) for index, value in enumerate(data["deferred_scopes"]))
    reasons = data["improved_formulation"]["restricted_reason_codes"]
    values.extend((f"/improved_formulation/restricted_reason_codes/{index}", value) for index, value in enumerate(reasons))
    return [
        _json_occurrence(inventory_ordinal, path, locator, "immutable_release_token", value)
        for locator, value in values
    ]


def extract_contract(cases: Mapping[str, Any] | None = None) -> dict[str, Any]:
    cases = load_cases() if cases is None else dict(cases)
    authority_inputs = (
        ("docs/S4_FULL_PRODUCTION_QUALIFICATION_PROGRAM.md", GOVERNING_SHA256),
        ("docs/S4_STAGE_M_MECHANICS_SELECTION_PLAN.md", PLAN_SHA256),
        ("docs/reference_cases/s4_stage_m_source_manifest.json", SOURCE_MANIFEST_SHA256),
        ("docs/S4_STAGE_M_CONSTRAINED_DERIVATION.md", CONSTRAINED_DERIVATION_SHA256),
        ("docs/S4_STAGE_M_ENERGETIC_DERIVATION.md", ENERGETIC_DERIVATION_SHA256),
        ("docs/reference_cases/s4_stage_m_dyadic_interval.py", INTERVAL_SHA256),
    )
    authority_records: list[dict[str, Any]] = []
    for relative, expected_hash in authority_inputs:
        _, raw = _verified_bytes(relative, expected_hash)
        canonical = _strict_text_bytes(raw, relative).encode("utf-8")
        authority_records.append(
            {
                "path": relative,
                "raw_sha256": expected_hash,
                "bytes": len(raw),
                "text_transport": "crlf" if b"\r\n" in raw else "lf",
                "canonical_lf_sha256": _sha256_bytes(canonical),
                "canonical_lf_bytes": len(canonical),
            }
        )
    occurrences: list[dict[str, Any]] = []
    parameter_rows: list[dict[str, Any]] = []
    drill_sample_rows: list[dict[str, Any]] = []
    release_tokens: list[dict[str, Any]] = []
    inventory_records: list[dict[str, Any]] = []
    for inventory_ordinal, (relative, expected_hash) in enumerate(INHERITED_INPUTS):
        path, raw = _verified_bytes(relative, expected_hash)
        canonical_text = _strict_text_bytes(raw, relative)
        canonical = canonical_text.encode("utf-8")
        inventory_records.append(
            {
                "ordinal": inventory_ordinal,
                "path": relative,
                "raw_sha256": expected_hash,
                "bytes": len(raw),
                "text_transport": "crlf" if b"\r\n" in raw else "lf",
                "canonical_lf_sha256": _sha256_bytes(canonical),
                "canonical_lf_bytes": len(canonical),
            }
        )
        if path.suffix == ".py":
            try:
                tree = ast.parse(canonical_text, filename=relative)
            except SyntaxError as error:
                raise MechanicsInputError(f"Python syntax error in {relative}") from error
            occurrences.extend(_module_functions(tree, inventory_ordinal, relative))
            if relative.endswith("test_s4_eq21_eq25_reference.py"):
                occurrences.extend(_extract_case_coordinate_keys(tree, inventory_ordinal, relative))
                parameter_rows.extend(_parameter_decorator_rows(tree, inventory_ordinal, relative))
            elif relative.endswith("test_s4_nullspace_semantics_proof.py"):
                occurrences.extend(_extract_worker_checks(tree, inventory_ordinal, relative))
            elif relative.endswith("test_s4_geometry_handoff.py"):
                parameter_rows.extend(_parameter_decorator_rows(tree, inventory_ordinal, relative))
            elif relative.endswith("test_s4_improved_qualification.py"):
                occurrences.extend(_extract_benchmark_case_ids(tree, inventory_ordinal, relative))
        else:
            data = _load_json_bytes(raw, relative)
            if relative.endswith("s4_nullspace_semantics_cases.json"):
                occurrences.extend(_nullspace_occurrences(data, inventory_ordinal, relative))
            elif relative.endswith("s4_drill_constraint_cases.json"):
                additions, sample_rows = _drill_occurrences(data, inventory_ordinal, relative)
                occurrences.extend(additions)
                drill_sample_rows.extend(sample_rows)
            elif relative.endswith("s4_restricted_release_contract.json"):
                release_tokens.extend(_release_tokens(data, inventory_ordinal, relative))
    occurrences.sort(
        key=lambda item: (
            item["inventory_ordinal"],
            item["path"].encode("utf-8"),
            item["locator"].encode("utf-8"),
            item["kind"].encode("utf-8"),
        )
    )
    parameter_rows.sort(
        key=lambda item: (
            item["inventory_ordinal"],
            item["path"].encode("utf-8"),
            item["test_locator"].encode("utf-8"),
            item["row_ordinal"],
            item["canonical_ast_row_sha256"],
        )
    )
    drill_sample_rows.sort(
        key=lambda item: (
            item["inventory_ordinal"],
            item["path"].encode("utf-8"),
            item["row_ordinal"],
            item["canonical_row_sha256"],
        )
    )
    unique_ids = sorted({item["id"] for item in occurrences}, key=lambda value: value.encode("utf-8"))
    collision_map = {
        identifier: count
        for identifier, count in sorted(Counter(item["id"] for item in occurrences).items())
        if count > 1
    }
    candidate_ids = list(cases["candidate_case_ids"])
    if len(candidate_ids) != len(set(candidate_ids)):
        raise MechanicsInputError("candidate IDs must be unique")

    required_coverage: list[dict[str, Any]] = []
    coverage_map: list[dict[str, Any]] = []

    def append_coverage(
        class_name: str,
        class_prefix: str,
        class_ordinal: int,
        source: Mapping[str, Any],
    ) -> None:
        source_digest = _sha256_bytes(canonical_json_bytes(dict(source)))
        coverage_key = f"{class_prefix}{class_ordinal:03d}:{source_digest}"
        coverage_ordinal = len(required_coverage)
        required_coverage.append(
            {
                "coverage_ordinal": coverage_ordinal,
                "class": class_name,
                "coverage_key": coverage_key,
                "source_record_sha256": source_digest,
                "source": dict(source),
            }
        )
        executor_suffix = _sha256_bytes(
            canonical_json_bytes(
                {
                    "coverage_key": coverage_key,
                    "executor_kind": "unresolved_exact_executor",
                    "source_record_sha256": source_digest,
                }
            )
        )
        coverage_map.append(
            {
                "coverage_key": coverage_key,
                "source_record_sha256": source_digest,
                "executor_kind": "unresolved_exact_executor",
                "executor_id": f"stage_m.{class_prefix.lower()}{class_ordinal:03d}.{executor_suffix}",
                "result_pointer": f"/scientific_summary/coverage_evidence/{coverage_ordinal}",
            }
        )

    for ordinal, occurrence in enumerate(occurrences):
        append_coverage(
            "inherited_id_occurrence",
            "I",
            ordinal,
            occurrence,
        )
    for ordinal, row in enumerate(parameter_rows):
        append_coverage("parameter_execution_row", "P", ordinal, row)
    for ordinal, row in enumerate(drill_sample_rows):
        append_coverage("drill_sample_row", "S", ordinal, row)

    contract = {
        "schema": CONTRACT_SCHEMA,
        "extractor_schema": "s4-stage-m-static-id-extractor-v1",
        "authority": cases["authority"],
        "authority_inputs": authority_records,
        "candidate_id": CANDIDATE_ID,
        "implementation_inputs": {
            "oracle": {
                "path": "docs/reference_cases/s4_stage_m_mechanics_oracle.py",
                "raw_sha256": _sha256_file(Path(__file__).resolve()),
                "bytes": Path(__file__).resolve().stat().st_size,
            },
            "cases": {
                "path": "docs/reference_cases/s4_stage_m_mechanics_cases.json",
                "raw_sha256": CASES_SHA256,
                "bytes": cases_path().stat().st_size,
            },
            "dyadic_interval": {
                "path": "docs/reference_cases/s4_stage_m_dyadic_interval.py",
                "raw_sha256": INTERVAL_SHA256,
                "bytes": (Path(__file__).with_name("s4_stage_m_dyadic_interval.py")).stat().st_size,
            },
            "energetic_derivation": {
                "path": "docs/S4_STAGE_M_ENERGETIC_DERIVATION.md",
                "raw_sha256": ENERGETIC_DERIVATION_SHA256,
            },
            "constrained_status": {
                "path": "docs/S4_STAGE_M_CONSTRAINED_DERIVATION.md",
                "raw_sha256": CONSTRAINED_DERIVATION_SHA256,
            },
        },
        "inventories": inventory_records,
        "inherited_id_occurrences": occurrences,
        "inherited_unique_ids": unique_ids,
        "collision_map": collision_map,
        "immutable_release_tokens": release_tokens,
        "parameter_execution_rows": parameter_rows,
        "drill_sample_rows": drill_sample_rows,
        "candidate_case_ids": candidate_ids,
        "ordered_mechanics_ids": [
            item["id"] for item in occurrences
        ] + candidate_ids,
        "required_execution_coverage": required_coverage,
        "coverage_map": coverage_map,
        "execution_coverage_policy": cases["execution_coverage_policy"],
        "counts": {
            "inherited_id_occurrences": len(occurrences),
            "inherited_unique_ids": len(unique_ids),
            "immutable_release_tokens": len(release_tokens),
            "parameter_execution_rows": len(parameter_rows),
            "drill_sample_rows": len(drill_sample_rows),
            "candidate_case_ids": len(candidate_ids),
            "required_execution_coverage": len(required_coverage),
        },
        "terminal_precedence": cases["terminal_precedence"],
        "overall_stage_m_status_while_candidate_a_blocked": cases[
            "overall_stage_m_status_while_candidate_a_blocked"
        ],
    }
    contract["ledger_sha256"] = _sha256_bytes(
        canonical_json_bytes(
            {
                "occurrences": occurrences,
                "release_tokens": release_tokens,
                "parameter_rows": parameter_rows,
                "sample_rows": drill_sample_rows,
                "candidate_ids": candidate_ids,
                "required_execution_coverage": required_coverage,
                "coverage_map": coverage_map,
            }
        )
    )
    expected = {
        "inherited_id_occurrences": 146,
        "immutable_release_tokens": 20,
        "parameter_execution_rows": 20,
        "drill_sample_rows": 8,
        "required_execution_coverage": 174,
    }
    for name, expected_count in expected.items():
        if contract["counts"][name] != expected_count:
            raise MechanicsInputError(
                f"contract count mismatch for {name}: expected {expected_count}, got {contract['counts'][name]}"
            )
    return contract


def load_cases() -> dict[str, Any]:
    path, raw = _verified_bytes(
        "docs/reference_cases/s4_stage_m_mechanics_cases.json", CASES_SHA256
    )
    data = _load_json_bytes(raw, str(path))
    if data.get("schema") != "anysolver.s4.stage-m-mechanics-cases-v1":
        raise MechanicsInputError("unexpected Stage-M cases schema")
    if data.get("candidate_id") != CANDIDATE_ID:
        raise MechanicsInputError("unexpected Candidate-B identity")
    if data.get("authority") != {
        "governing_program_sha256": GOVERNING_SHA256,
        "stage_m_plan_sha256": PLAN_SHA256,
        "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "candidate_b_derivation_sha256": ENERGETIC_DERIVATION_SHA256,
        "candidate_a_status_sha256": CONSTRAINED_DERIVATION_SHA256,
    }:
        raise MechanicsInputError("Stage-M cases authority does not match frozen identities")
    return data


def _load_verified_module(name: str, relative: str, sha256: str) -> Any:
    path = _verified_path(relative, sha256)
    if name in sys.modules:
        raise MechanicsInputError(f"module name is already loaded: {name}")
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise MechanicsInputError(f"cannot create module specification for {relative}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        raise
    return module


def _load_science_dependencies() -> None:
    global mp, BASE, INTERVAL
    if BASE is not None or INTERVAL is not None or mp is not None:
        raise MechanicsInputError("science dependencies were already loaded")
    if os.environ.get("MPMATH_NOGMPY") != "1":
        raise MechanicsInputError("MPMATH_NOGMPY=1 is required before mechanics")
    import mpmath as imported_mpmath

    if imported_mpmath.__version__ != "1.3.0":
        raise MechanicsInputError(
            f"mpmath 1.3.0 is required, got {imported_mpmath.__version__}"
        )
    if getattr(imported_mpmath.libmp, "BACKEND", None) != "python":
        raise MechanicsInputError("mpmath must use the pure-Python backend")
    mp = imported_mpmath
    BASE = _load_verified_module(
        "s4_stage_m_frozen_drill_oracle",
        "docs/reference_cases/s4_drill_constraint_oracle.py",
        BASE_ORACLE_SHA256,
    )
    INTERVAL = _load_verified_module(
        "s4_stage_m_dyadic_interval",
        "docs/reference_cases/s4_stage_m_dyadic_interval.py",
        INTERVAL_SHA256,
    )


def _eval_scalar(value: Any, cases: Mapping[str, Any], active: tuple[str, ...] = ()) -> mp.mpf:
    if not isinstance(value, dict) or type(value.get("kind")) is not str:
        raise MechanicsInputError("exact scalar must be a tagged object")
    kind = value["kind"]
    allowed = set(cases["exact_scalar_grammar"]["allowed_kinds"])
    if kind not in allowed:
        raise MechanicsInputError(f"unknown exact scalar kind: {kind}")
    expected_keys = set(cases["exact_scalar_grammar"][kind]["keys"])
    if set(value) != expected_keys:
        raise MechanicsInputError(f"wrong keys for exact scalar {kind}: {sorted(value)}")
    if kind == "rational":
        numerator = int(value["numerator"])
        denominator = int(value["denominator"])
        if denominator <= 0 or str(numerator) != value["numerator"] or str(denominator) != value["denominator"]:
            raise MechanicsInputError("rational requires canonical integer strings and positive denominator")
        return mp.mpf(numerator) / denominator
    if kind == "pow2":
        significand = int(value["significand"])
        exponent = int(value["exponent"])
        if str(significand) != value["significand"] or str(exponent) != value["exponent"]:
            raise MechanicsInputError("pow2 requires canonical integer strings")
        return mp.mpf(significand) * mp.power(2, exponent)
    if kind == "sqrt":
        radicand = _eval_scalar(value["radicand"], cases, active)
        if radicand < 0:
            raise MechanicsInputError("sqrt radicand is negative")
        return mp.sqrt(radicand)
    if kind == "add":
        terms = value["terms"]
        if not isinstance(terms, list) or len(terms) < 2:
            raise MechanicsInputError("add requires at least two terms")
        return mp.fsum(_eval_scalar(term, cases, active) for term in terms)
    if kind == "mul":
        factors = value["factors"]
        if not isinstance(factors, list) or len(factors) < 2:
            raise MechanicsInputError("mul requires at least two factors")
        result = mp.mpf(1)
        for factor in factors:
            result *= _eval_scalar(factor, cases, active)
        return result
    if kind == "div":
        numerator = _eval_scalar(value["numerator"], cases, active)
        denominator = _eval_scalar(value["denominator"], cases, active)
        if denominator == 0:
            raise MechanicsInputError("exact scalar division by zero")
        return numerator / denominator
    if kind == "neg":
        return -_eval_scalar(value["value"], cases, active)
    if kind == "ref":
        identifier = value["id"]
        if not isinstance(identifier, str) or identifier in active:
            raise MechanicsInputError("invalid or cyclic exact scalar reference")
        constants = cases["exact_constants"]
        if identifier not in constants:
            raise MechanicsInputError(f"unknown exact scalar reference: {identifier}")
        return _eval_scalar(constants[identifier], cases, (*active, identifier))
    raise AssertionError(kind)


def _parse_exact_text(text: str) -> mp.mpf:
    if not isinstance(text, str) or not text or text.strip() != text:
        raise MechanicsInputError("exact text scalar must be a trimmed string")
    try:
        fraction = Fraction(text)
    except (ValueError, ZeroDivisionError) as error:
        raise MechanicsInputError(f"invalid exact rational text: {text}") from error
    return mp.mpf(fraction.numerator) / fraction.denominator


def _validate_cases(cases: Mapping[str, Any]) -> None:
    if cases["calculus"]["decimal_digits"] != list(PRECISIONS):
        raise MechanicsInputError("precision list differs from the frozen contract")
    multiplier_records = cases["calculus"]["sensitivity_multipliers"]
    if any(record.get("kind") != "rational" for record in multiplier_records):
        raise MechanicsInputError("sensitivity multipliers must be exact rationals")
    multipliers = [
        Fraction(int(record["numerator"]), int(record["denominator"]))
        for record in multiplier_records
    ]
    if multipliers != [Fraction(1, 4), Fraction(1), Fraction(4)]:
        raise MechanicsInputError("sensitivity multipliers differ from the frozen contract")
    if cases["execution"] != {
        "mode": "precision_shards_then_canonical_merge",
        "precision_shards": [80, 160, 320],
        "repeat_sets": 2,
        "shard_timeout_seconds": 7200,
        "merge_timeout_seconds": 300,
        "task_owned_directory": ".s4_stage_m_execution",
        "shard_filenames": [
            "set1_080.json",
            "set1_160.json",
            "set1_320.json",
            "set2_080.json",
            "set2_160.json",
            "set2_320.json",
        ],
        "merge_filenames": ["set1_merged.json", "set2_merged.json"],
        "completion_manifest": "COMPLETE.json",
        "pending_suffix": ".pending",
        "full_execution_environment_variable": "ANYSOLVER_RUN_S4_STAGE_M_FULL",
        "full_execution_environment_value": "PRECISION_SHARDS_THEN_CANONICAL_MERGE_V1",
        "shard_status": "partial",
        "shards_are_nonterminal": True,
        "quick_summary_decimal_digits": 80,
        "merge_precision_decimal_digits": 320,
        "completed_shards_are_preserved": True,
        "merge_recomputes_scientific_summary": True,
        "monolithic_timeout": {
            "timeout_seconds": 7200,
            "packet_produced": False,
            "scientific_result": False,
            "evidence_directory_created": False,
        },
    }:
        raise MechanicsInputError("execution shard contract differs from the frozen cases")
    if cases["quadrature"]["primary"]["id"] != "G3xG3xG2":
        raise MechanicsInputError("unexpected primary quadrature")
    if cases["quadrature"]["sensitivity"]["id"] != "G4xG4xG3":
        raise MechanicsInputError("unexpected sensitivity quadrature")
    certificate = cases["exact_certificates"]
    if certificate != {
        "flat_polynomial_evaluation_grid": ["-1", "0", "1"],
        "flat_surface_degree_bound": 2,
        "flat_thickness_degree_bound": 1,
        "rank_profile": "lexicographic_column_then_original_row_fraction_gauss_jordan",
        "minor_check": "exact_fraction_determinant_then_dyadic_point_interval_lu",
        "rounded_mpf_points_are_not_intervals": True,
        "topology_interval_bits": 768,
        "unclosed_interval_is": "BORDERLINE",
    }:
        raise MechanicsInputError("exact-certificate rules differ from the frozen contract")
    curved = cases["response_fixtures"]["curved_refinement"]
    if (
        curved["levels"] != [1, 2, 4, 8]
        or curved["response_quantity"] != "total_physical_strain_energy"
        or curved["error_definition"]
        != "abs(E_level-E_reference)/abs(E_reference)"
        or curved["reference_level"] != 8
        or curved["nominal_order"] != 2
        or curved["minimum_observed_slope_fraction"] != "0.85"
    ):
        raise MechanicsInputError("curved-refinement response rule is not frozen")
    beam = cases["response_fixtures"]["beam_shell_virtual_work"]
    if (
        beam["topology_id"] != "two_shared_edge_constraints"
        or beam["constraint_id"] != "rigid_beam_shell_work"
        or beam["coordinate_system"] != "physical_dofs"
    ):
        raise MechanicsInputError("beam-shell virtual-work fixture is not frozen")
    if cases["execution_coverage_policy"] != {
        "required_rows": 174,
        "exact_per_coverage_key_executor_required": True,
        "raw_identity_is_not_execution": True,
        "aggregate_gate_fanout_forbidden": True,
        "unresolved_exact_executor_status": "BORDERLINE",
        "go_requires_every_row_pass": True,
    }:
        raise MechanicsInputError("execution coverage policy differs from the frozen contract")
    if cases["terminal_precedence"] != [
        "BLOCKED_INPUT_IDENTITY",
        "BLOCKED_CONTRACT_VIOLATION",
        "NO_GO_CANDIDATE_B",
        "UNCLASSIFIED_CANDIDATE_B",
        "GO_CANDIDATE_B",
    ]:
        raise MechanicsInputError("terminal precedence differs from the frozen contract")
    for point in cases["pointwise_derivative_samples"]:
        _eval_scalar(point["r"], cases)
        _eval_scalar(point["s"], cases)
    for fixture in cases["constitutive_fixtures"]:
        if fixture["kind"] == "isotropic_plane_stress":
            _eval_scalar(fixture["youngs_modulus"], cases)
            _eval_scalar(fixture["poisson_ratio"], cases)
        elif fixture["kind"] == "spd_from_lower_cholesky":
            lower = fixture["lower"]
            if len(lower) != 5 or any(len(row) != 5 for row in lower):
                raise MechanicsInputError("orthotropic Cholesky fixture must be 5x5")
            matrix = mp.matrix([[_eval_scalar(entry, cases) for entry in row] for row in lower])
            if any(matrix[row, column] != 0 for row in range(5) for column in range(row + 1, 5)):
                raise MechanicsInputError("Cholesky fixture must be lower triangular")
            if any(matrix[index, index] <= 0 for index in range(5)):
                raise MechanicsInputError("Cholesky fixture must have positive diagonal")
        else:
            raise MechanicsInputError(f"unknown constitutive fixture: {fixture['kind']}")


def _full_midside_shapes(
    r_value: mp.mpf, s_value: mp.mpf
) -> tuple[list[mp.mpf], list[list[mp.mpf]]]:
    half = mp.mpf(1) / 2
    values = [
        half * (1 - r_value**2) * (1 - s_value),
        half * (1 - s_value**2) * (1 + r_value),
        half * (1 - r_value**2) * (1 + s_value),
        half * (1 - s_value**2) * (1 - r_value),
    ]
    derivatives = [
        [-r_value * (1 - s_value), -half * (1 - r_value**2)],
        [half * (1 - s_value**2), -s_value * (1 + r_value)],
        [-r_value * (1 + s_value), half * (1 - r_value**2)],
        [-half * (1 - s_value**2), -s_value * (1 - r_value)],
    ]
    return values, derivatives


def hd_operators(
    reference: Any, r_value: mp.mpf, s_value: mp.mpf
) -> tuple[mp.matrix, mp.matrix, mp.matrix]:
    values, derivatives = _full_midside_shapes(r_value, s_value)
    h_value = BASE._zeros(3, 24)
    h_r = BASE._zeros(3, 24)
    h_s = BASE._zeros(3, 24)
    dual_r = BASE._row(reference.center_dual, 0)
    dual_s = BASE._row(reference.center_dual, 1)
    drill = reference.drill_direction
    for edge in range(4):
        node_i, node_j = edge, (edge + 1) % 4
        coefficient_r = reference.edge_coefficients[edge, 0]
        coefficient_s = reference.edge_coefficients[edge, 1]
        direction = BASE._add_vectors(
            BASE._scale_vector(coefficient_r, dual_r),
            BASE._scale_vector(-coefficient_s, dual_s),
        )
        for row in range(3):
            for axis in range(3):
                factor = direction[row] * drill[axis]
                for matrix, scalar in (
                    (h_value, values[edge]),
                    (h_r, derivatives[edge][0]),
                    (h_s, derivatives[edge][1]),
                ):
                    matrix[row, 6 * node_i + 3 + axis] -= scalar * factor
                    matrix[row, 6 * node_j + 3 + axis] += scalar * factor
    return h_value, h_r, h_s


def compatible_surface_operator(
    reference: Any, r_value: mp.mpf, s_value: mp.mpf
) -> mp.matrix:
    _, h_r, h_s = hd_operators(reference, r_value, s_value)
    bases = BASE._geometry_bases(reference, r_value, s_value, mp.mpf(0))
    a_r = BASE._row(bases, 0)
    a_s = BASE._row(bases, 1)
    result = BASE._zeros(3, 24)
    for column in range(24):
        derivative_r = BASE._matrix_column(h_r, column)
        derivative_s = BASE._matrix_column(h_s, column)
        result[0, column] = BASE._dot(a_r, derivative_r)
        result[1, column] = BASE._dot(a_s, derivative_s)
        result[2, column] = (
            BASE._dot(a_r, derivative_s) + BASE._dot(a_s, derivative_r)
        ) / 2
    return result


def candidate_covariant_strain(
    reference: Any, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf
) -> mp.matrix:
    raw = BASE._raw_covariant(reference, r_value, s_value, zeta)
    membrane = (
        BASE.eq25_membrane(reference, r_value, s_value)
        + compatible_surface_operator(reference, r_value, s_value)
        - BASE._mid_membrane(reference, r_value, s_value)
    )
    for row in range(3):
        for column in range(24):
            raw[row, column] += membrane[row, column]
    shear = BASE._assumed_shear(reference, r_value, s_value, zeta)
    for row in range(2):
        for column in range(24):
            raw[3 + row, column] = shear[row, column]
    return raw


def base_without_eq21_covariant_strain(
    reference: Any, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf
) -> mp.matrix:
    raw = BASE._raw_covariant(reference, r_value, s_value, zeta)
    membrane = BASE.eq25_membrane(reference, r_value, s_value) - BASE._mid_membrane(
        reference, r_value, s_value
    )
    for row in range(3):
        for column in range(24):
            raw[row, column] += membrane[row, column]
    shear = BASE._assumed_shear(reference, r_value, s_value, zeta)
    for row in range(2):
        for column in range(24):
            raw[3 + row, column] = shear[row, column]
    return raw


def candidate_local_strain(
    reference: Any, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf
) -> tuple[mp.matrix, mp.mpf]:
    transform, determinant = BASE._local_transform(reference, r_value, s_value, zeta)
    if not determinant > 0 or not mp.isfinite(determinant):
        raise MechanicsInputError("Candidate-B quadrature Jacobian is not positive finite")
    return transform * candidate_covariant_strain(reference, r_value, s_value, zeta), determinant


def base_without_eq21_local_strain(
    reference: Any, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf
) -> tuple[mp.matrix, mp.mpf]:
    transform, determinant = BASE._local_transform(reference, r_value, s_value, zeta)
    if not determinant > 0 or not mp.isfinite(determinant):
        raise MechanicsInputError("base quadrature Jacobian is not positive finite")
    return (
        transform * base_without_eq21_covariant_strain(
            reference, r_value, s_value, zeta
        ),
        determinant,
    )


def candidate_displacement(
    reference: Any, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf
) -> mp.matrix:
    continuum, _, _, _ = BASE._continuum_parts(reference, r_value, s_value, zeta)
    h_value, _, _ = hd_operators(reference, r_value, s_value)
    return continuum + h_value


def _quadrature(cases: Mapping[str, Any], rule: str) -> tuple[list[tuple[mp.mpf, mp.mpf]], list[tuple[mp.mpf, mp.mpf]]]:
    if rule == "primary":
        surface = []
        for entry in cases["quadrature"]["primary"]["surface_1d"]:
            value = _eval_scalar(entry["node"], cases)
            sign = int(entry["node_sign"])
            surface.append((mp.mpf(sign) * value, _eval_scalar(entry["weight"], cases)))
        thickness = []
        for entry in cases["quadrature"]["primary"]["thickness_1d"]:
            value = _eval_scalar(entry["node"], cases)
            sign = int(entry["node_sign"])
            thickness.append((mp.mpf(sign) * value, _eval_scalar(entry["weight"], cases)))
        return surface, thickness
    if rule == "sensitivity":
        formula = cases["quadrature"]["sensitivity"]["surface_formula"]
        inner = _eval_scalar(formula["x_inner"], cases)
        outer = _eval_scalar(formula["x_outer"], cases)
        w_inner = _eval_scalar(formula["w_inner"], cases)
        w_outer = _eval_scalar(formula["w_outer"], cases)
        surface = [(-outer, w_outer), (-inner, w_inner), (inner, w_inner), (outer, w_outer)]
        root = mp.sqrt(mp.mpf(3) / 5)
        thickness = [(-root, mp.mpf(5) / 9), (mp.mpf(0), mp.mpf(8) / 9), (root, mp.mpf(5) / 9)]
        return surface, thickness
    raise MechanicsInputError(f"unknown quadrature rule: {rule}")


def _constitutive(cases: Mapping[str, Any], identifier: str) -> mp.matrix:
    fixture = next(
        (item for item in cases["constitutive_fixtures"] if item["id"] == identifier),
        None,
    )
    if fixture is None:
        raise MechanicsInputError(f"unknown constitutive fixture: {identifier}")
    if fixture["kind"] == "isotropic_plane_stress":
        young = _eval_scalar(fixture["youngs_modulus"], cases)
        poisson = _eval_scalar(fixture["poisson_ratio"], cases)
        factor = young / (1 - poisson**2)
        shear = young / (2 * (1 + poisson))
        result = BASE._zeros(5, 5)
        result[0, 0] = result[1, 1] = factor
        result[0, 1] = result[1, 0] = factor * poisson
        result[2, 2] = result[3, 3] = result[4, 4] = shear
        return result
    lower = mp.matrix(
        [[_eval_scalar(entry, cases) for entry in row] for row in fixture["lower"]]
    )
    return lower * lower.T


def _fraction_zeros(rows: int, columns: int) -> list[list[Fraction]]:
    return [[Fraction(0) for _ in range(columns)] for _ in range(rows)]


def _fraction_matmul(
    left: Sequence[Sequence[Fraction]], right: Sequence[Sequence[Fraction]]
) -> list[list[Fraction]]:
    if not left or not right:
        return []
    inner = len(left[0])
    if any(len(row) != inner for row in left) or len(right) != inner:
        raise MechanicsInputError("exact matrix product dimensions differ")
    columns = len(right[0])
    if any(len(row) != columns for row in right):
        raise MechanicsInputError("ragged exact matrix")
    return [
        [
            sum((left_row[k] * right[k][column] for k in range(inner)), Fraction(0))
            for column in range(columns)
        ]
        for left_row in left
    ]


def _fraction_determinant(matrix: Sequence[Sequence[Fraction]]) -> Fraction:
    size = len(matrix)
    if any(len(row) != size for row in matrix):
        raise MechanicsInputError("exact determinant requires a square matrix")
    work = [list(row) for row in matrix]
    sign = 1
    determinant = Fraction(1)
    for column in range(size):
        pivot = next(
            (row for row in range(column, size) if work[row][column] != 0), None
        )
        if pivot is None:
            return Fraction(0)
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
            sign = -sign
        value = work[column][column]
        determinant *= value
        for row in range(column + 1, size):
            factor = work[row][column] / value
            for inner in range(column + 1, size):
                work[row][inner] -= factor * work[column][inner]
    return determinant if sign > 0 else -determinant


def _fraction_rank_certificate(
    matrix: Sequence[Sequence[Fraction]], label: str
) -> dict[str, Any]:
    if not matrix:
        return {"label": label, "rank": 0, "minor_rows": [], "minor_columns": []}
    rows = len(matrix)
    columns = len(matrix[0])
    if any(len(row) != columns for row in matrix):
        raise MechanicsInputError(f"ragged exact matrix: {label}")
    work = [list(row) for row in matrix]
    origins = list(range(rows))
    pivot_rows: list[int] = []
    pivot_columns: list[int] = []
    cursor = 0
    for column in range(columns):
        pivot = next((row for row in range(cursor, rows) if work[row][column]), None)
        if pivot is None:
            continue
        work[cursor], work[pivot] = work[pivot], work[cursor]
        origins[cursor], origins[pivot] = origins[pivot], origins[cursor]
        value = work[cursor][column]
        work[cursor] = [entry / value for entry in work[cursor]]
        for row in range(rows):
            if row == cursor or work[row][column] == 0:
                continue
            factor = work[row][column]
            work[row] = [
                work[row][inner] - factor * work[cursor][inner]
                for inner in range(columns)
            ]
        pivot_rows.append(origins[cursor])
        pivot_columns.append(column)
        cursor += 1
        if cursor == rows:
            break
    minor = [
        [matrix[row][column] for column in pivot_columns] for row in pivot_rows
    ]
    determinant = _fraction_determinant(minor)
    if cursor and determinant == 0:
        raise RuntimeError(f"exact rank-profile minor is singular: {label}")
    interval_minor = [
        [INTERVAL.DyadicInterval.point(value) for value in row] for row in minor
    ]
    if cursor:
        sign, enclosure = INTERVAL.certify_nonzero_minor(interval_minor)
        interval_token = enclosure.token()
    else:
        sign = 0
        interval_token = INTERVAL.DyadicInterval.point(1).token()
    return {
        "label": label,
        "rank": cursor,
        "minor_rows": pivot_rows,
        "minor_columns": pivot_columns,
        "determinant": [str(determinant.numerator), str(determinant.denominator)],
        "interval_determinant": interval_token,
        "interval_sign": sign,
        "outward_bits": "exact-rational-point",
    }


def _flat_fraction_q4(
    r_value: Fraction, s_value: Fraction
) -> tuple[list[Fraction], list[tuple[Fraction, Fraction]]]:
    corners = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    values: list[Fraction] = []
    derivatives: list[tuple[Fraction, Fraction]] = []
    for corner_r, corner_s in corners:
        values.append(
            Fraction(1, 4)
            * (1 + corner_r * r_value)
            * (1 + corner_s * s_value)
        )
        derivatives.append(
            (
                Fraction(corner_r, 4) * (1 + corner_s * s_value),
                Fraction(corner_s, 4) * (1 + corner_r * r_value),
            )
        )
    return values, derivatives


def _flat_fraction_raw(
    r_value: Fraction, s_value: Fraction, zeta: Fraction
) -> list[list[Fraction]]:
    values, derivatives = _flat_fraction_q4(r_value, s_value)
    result = _fraction_zeros(5, 24)
    half_thickness = Fraction(1, 10)
    for node, (value, (d_r, d_s)) in enumerate(zip(values, derivatives, strict=True)):
        translation = 6 * node
        rotation = translation + 3
        result[0][translation] += d_r
        result[1][translation + 1] += d_s
        result[2][translation] += d_s / 2
        result[2][translation + 1] += d_r / 2
        result[3][translation + 2] += half_thickness * d_r / 2
        result[4][translation + 2] += half_thickness * d_s / 2
        result[0][rotation + 1] += zeta * half_thickness * d_r
        result[1][rotation] -= zeta * half_thickness * d_s
        result[2][rotation + 1] += zeta * half_thickness * d_s / 2
        result[2][rotation] -= zeta * half_thickness * d_r / 2
        result[3][rotation + 1] += half_thickness * value / 2
        result[4][rotation] -= half_thickness * value / 2
    return result


def _flat_fraction_hd(
    r_value: Fraction, s_value: Fraction
) -> tuple[list[list[Fraction]], list[list[Fraction]], list[list[Fraction]]]:
    half = Fraction(1, 2)
    values = [
        half * (1 - r_value**2) * (1 - s_value),
        half * (1 - s_value**2) * (1 + r_value),
        half * (1 - r_value**2) * (1 + s_value),
        half * (1 - s_value**2) * (1 - r_value),
    ]
    derivatives = [
        (-r_value * (1 - s_value), -half * (1 - r_value**2)),
        (half * (1 - s_value**2), -s_value * (1 + r_value)),
        (-r_value * (1 + s_value), half * (1 - r_value**2)),
        (-half * (1 - s_value**2), -s_value * (1 - r_value)),
    ]
    directions = (
        (Fraction(0), Fraction(1, 4), Fraction(0)),
        (Fraction(-1, 4), Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(-1, 4), Fraction(0)),
        (Fraction(1, 4), Fraction(0), Fraction(0)),
    )
    result = _fraction_zeros(3, 24)
    derivative_r = _fraction_zeros(3, 24)
    derivative_s = _fraction_zeros(3, 24)
    for edge, direction in enumerate(directions):
        node_i, node_j = edge, (edge + 1) % 4
        for axis in range(3):
            for target, scalar in (
                (result, values[edge]),
                (derivative_r, derivatives[edge][0]),
                (derivative_s, derivatives[edge][1]),
            ):
                target[axis][6 * node_i + 5] -= scalar * direction[axis]
                target[axis][6 * node_j + 5] += scalar * direction[axis]
    return result, derivative_r, derivative_s


def _flat_fraction_candidate(
    r_value: Fraction, s_value: Fraction, zeta: Fraction
) -> list[list[Fraction]]:
    raw = _flat_fraction_raw(r_value, s_value, zeta)
    mid = _flat_fraction_raw(r_value, s_value, Fraction(0))
    top = _flat_fraction_raw(Fraction(0), Fraction(1), Fraction(0))[0]
    bottom = _flat_fraction_raw(Fraction(0), Fraction(-1), Fraction(0))[0]
    right = _flat_fraction_raw(Fraction(1), Fraction(0), Fraction(0))[1]
    left = _flat_fraction_raw(Fraction(-1), Fraction(0), Fraction(0))[1]
    center_shear = _flat_fraction_raw(Fraction(0), Fraction(0), Fraction(0))[2]
    eq25 = [
        [(top[column] + bottom[column]) / 2 for column in range(24)],
        [(right[column] + left[column]) / 2 for column in range(24)],
        list(center_shear),
    ]
    _, h_r, h_s = _flat_fraction_hd(r_value, s_value)
    compatible = _fraction_zeros(3, 24)
    for column in range(24):
        compatible[0][column] = h_r[0][column]
        compatible[1][column] = h_s[1][column]
        compatible[2][column] = (h_s[0][column] + h_r[1][column]) / 2
    for row in range(3):
        for column in range(24):
            raw[row][column] += eq25[row][column] + compatible[row][column] - mid[row][column]
    shear_top = _flat_fraction_raw(Fraction(0), Fraction(1), zeta)[3]
    shear_bottom = _flat_fraction_raw(Fraction(0), Fraction(-1), zeta)[3]
    shear_right = _flat_fraction_raw(Fraction(1), Fraction(0), zeta)[4]
    shear_left = _flat_fraction_raw(Fraction(-1), Fraction(0), zeta)[4]
    raw[3] = [
        ((1 + s_value) * shear_top[column] + (1 - s_value) * shear_bottom[column]) / 2
        for column in range(24)
    ]
    raw[4] = [
        ((1 + r_value) * shear_right[column] + (1 - r_value) * shear_left[column]) / 2
        for column in range(24)
    ]
    local_factors = (Fraction(1), Fraction(1), Fraction(2), Fraction(20), Fraction(20))
    return [
        [local_factors[row] * value for value in raw[row]] for row in range(5)
    ]


def _flat_fraction_displacement(
    r_value: Fraction, s_value: Fraction, zeta: Fraction
) -> list[list[Fraction]]:
    values, _ = _flat_fraction_q4(r_value, s_value)
    h_value, _, _ = _flat_fraction_hd(r_value, s_value)
    result = _fraction_zeros(3, 24)
    half_thickness = Fraction(1, 10)
    for node, value in enumerate(values):
        translation = 6 * node
        rotation = translation + 3
        for axis in range(3):
            result[axis][translation + axis] += value
        result[0][rotation + 1] += zeta * half_thickness * value
        result[1][rotation] -= zeta * half_thickness * value
    for row in range(3):
        for column in range(24):
            result[row][column] += h_value[row][column]
    return result


def _flat_exact_certificate() -> dict[str, Any]:
    grid = (Fraction(-1), Fraction(0), Fraction(1))
    b_stack: list[list[Fraction]] = []
    h_stack: list[list[Fraction]] = []
    for r_value, s_value, zeta in itertools.product(grid, repeat=3):
        b_stack.extend(_flat_fraction_candidate(r_value, s_value, zeta))
        h_stack.extend(_flat_fraction_displacement(r_value, s_value, zeta))
    drill = _fraction_zeros(24, 4)
    common = _fraction_zeros(24, 1)
    checker = _fraction_zeros(24, 1)
    for node in range(4):
        drill[6 * node + 5][node] = Fraction(1)
        common[6 * node + 5][0] = Fraction(1)
        checker[6 * node + 5][0] = Fraction(1 if node % 2 == 0 else -1)
    pure = _fraction_matmul(b_stack, drill)
    combined = [*b_stack, *h_stack]
    b_common = _fraction_matmul(b_stack, common)
    h_common = _fraction_matmul(h_stack, common)
    b_checker = _fraction_matmul(b_stack, checker)
    h_checker = _fraction_matmul(h_stack, checker)
    coordinates = (
        (Fraction(-1), Fraction(-1), Fraction(0)),
        (Fraction(1), Fraction(-1), Fraction(0)),
        (Fraction(1), Fraction(1), Fraction(0)),
        (Fraction(-1), Fraction(1), Fraction(0)),
    )
    rigid = _fraction_zeros(24, 6)
    for node, position in enumerate(coordinates):
        for axis in range(3):
            rigid[6 * node + axis][axis] = Fraction(1)
        x_value, y_value, z_value = position
        cross_columns = (
            (Fraction(0), -z_value, y_value),
            (z_value, Fraction(0), -x_value),
            (-y_value, x_value, Fraction(0)),
        )
        for rotation_axis, displacement in enumerate(cross_columns):
            for axis in range(3):
                rigid[6 * node + axis][3 + rotation_axis] = displacement[axis]
            rigid[6 * node + 3 + rotation_axis][3 + rotation_axis] = Fraction(1)
    b_rigid = _fraction_matmul(b_stack, rigid)
    rigid_and_gauge = [
        [*rigid[row], common[row][0]] for row in range(len(rigid))
    ]

    def exact_zero(matrix: Sequence[Sequence[Fraction]]) -> bool:
        return all(value == 0 for row in matrix for value in row)

    first_b_checker = next(
        (index for index, row in enumerate(b_checker) if row[0] != 0), None
    )
    first_h_checker = next(
        (index for index, row in enumerate(h_checker) if row[0] != 0), None
    )
    if first_b_checker is None or first_h_checker is None:
        raise RuntimeError("flat checkerboard exact field unexpectedly vanishes")
    return {
        "evaluation_grid": ["-1", "0", "1"],
        "polynomial_unisolvence": {
            "surface_degree_bound": 2,
            "thickness_degree_bound": 1,
            "three_point_grid_is_injective": True,
        },
        "B": _fraction_rank_certificate(b_stack, "flat_candidate_B_polynomial"),
        "BH": _fraction_rank_certificate(combined, "flat_candidate_BH_polynomial"),
        "pure_drill": _fraction_rank_certificate(pure, "flat_pure_drill_polynomial"),
        "rigid": _fraction_rank_certificate(rigid, "flat_rigid_candidates"),
        "rigid_and_gauge": _fraction_rank_certificate(
            rigid_and_gauge, "flat_rigid_and_common_gauge"
        ),
        "B_rigid_exact_zero": exact_zero(b_rigid),
        "common_B_exact_zero": exact_zero(b_common),
        "common_H_exact_zero": exact_zero(h_common),
        "checker_B_nonzero": {
            "row": first_b_checker,
            "value": [
                str(b_checker[first_b_checker][0].numerator),
                str(b_checker[first_b_checker][0].denominator),
            ],
            "interval": INTERVAL.DyadicInterval.point(
                b_checker[first_b_checker][0]
            ).token(),
        },
        "checker_H_nonzero": {
            "row": first_h_checker,
            "value": [
                str(h_checker[first_h_checker][0].numerator),
                str(h_checker[first_h_checker][0].denominator),
            ],
            "interval": INTERVAL.DyadicInterval.point(
                h_checker[first_h_checker][0]
            ).token(),
        },
        "positive_energy_logic": "nonzero_B_field+positive_weights+pointwise_SPD",
        "positive_mass_logic": "nonzero_H_field+positive_weights+positive_density",
    }


def _fraction_matrix_to_mp(
    matrix: Sequence[Sequence[Fraction]],
) -> mp.matrix:
    return mp.matrix(
        [
            [mp.mpf(value.numerator) / value.denominator for value in row]
            for row in matrix
        ]
    )


def _flat_runtime_binding(
    cases: Mapping[str, Any], eps_p: mp.mpf
) -> dict[str, Any]:
    topology = next(
        record for record in _drill_cases()["topology_cases"] if record["id"] == "one_square"
    )
    element = topology["elements"][0]
    coordinates_input, directors_input, thickness_input = BASE._element_inputs(
        topology, element
    )
    reference = BASE.build_reference(
        coordinates_input,
        directors_input,
        thickness_input,
        element_id="candidate-b-exact-runtime-binding",
        connectivity=element["nodes"],
    )
    b_residuals: list[mp.mpf] = []
    h_residuals: list[mp.mpf] = []
    for r_fraction, s_fraction, zeta_fraction in itertools.product(
        (Fraction(-1), Fraction(0), Fraction(1)), repeat=3
    ):
        r_value = mp.mpf(r_fraction.numerator) / r_fraction.denominator
        s_value = mp.mpf(s_fraction.numerator) / s_fraction.denominator
        zeta = mp.mpf(zeta_fraction.numerator) / zeta_fraction.denominator
        runtime_b, _ = candidate_local_strain(reference, r_value, s_value, zeta)
        runtime_h = candidate_displacement(reference, r_value, s_value, zeta)
        exact_b = _fraction_matrix_to_mp(
            _flat_fraction_candidate(r_fraction, s_fraction, zeta_fraction)
        )
        exact_h = _fraction_matrix_to_mp(
            _flat_fraction_displacement(r_fraction, s_fraction, zeta_fraction)
        )
        b_residuals.append(BASE._equality_residual(runtime_b, exact_b))
        h_residuals.append(BASE._equality_residual(runtime_h, exact_h))
    dimension = 24
    tolerance = 4096 * dimension * eps_p
    maximum_b = max(b_residuals, default=mp.mpf(0))
    maximum_h = max(h_residuals, default=mp.mpf(0))
    return {
        "grid_point_count": len(b_residuals),
        "B_max_r_eq": BASE.mpf_token(maximum_b),
        "H_max_r_eq": BASE.mpf_token(maximum_h),
        "r_tol": BASE.mpf_token(tolerance),
        "pass": maximum_b <= tolerance and maximum_h <= tolerance,
    }


def _drill_cases() -> dict[str, Any]:
    path = _verified_path(
        "docs/reference_cases/s4_drill_constraint_cases.json",
        "B4D663382302E971752F0757F6E869549A54234F485235E06DBEF74085860F38",
    )
    return _load_json(path)


def _local_case_topology(record: Mapping[str, Any]) -> dict[str, Any]:
    if len(record["coordinates"]) != 4 or len(record["director_seeds"]) != 4:
        raise MechanicsInputError("local Candidate-B fixture must have four corners")
    return {
        "id": f"candidate_b_local::{record['id']}",
        "nodes": [
            {"id": f"n{index}", "x": list(coordinate)}
            for index, coordinate in enumerate(record["coordinates"])
        ],
        "elements": [
            {
                "id": "e0",
                "nodes": ["n0", "n1", "n2", "n3"],
                "state": "active",
                "director_seeds": [list(value) for value in record["director_seeds"]],
                "thickness": list(record["thickness"]),
            }
        ],
        "source_local_id": record["id"],
    }


def _scatter(local: mp.matrix, connectivity: Sequence[int], node_count: int) -> mp.matrix:
    return BASE._scatter_rows(local, connectivity, node_count)


def assemble_candidate_topology(
    topology: Mapping[str, Any],
    cases: Mapping[str, Any],
    rule: str,
    constitutive_id: str = "isotropic_plane_stress_rational",
    constitutive_scale: mp.mpf | None = None,
) -> dict[str, Any]:
    node_ids = [node["id"] for node in topology["nodes"]]
    if node_ids != sorted(node_ids, key=lambda value: value.encode("utf-8")):
        raise MechanicsInputError(f"topology nodes are not ordinal: {topology['id']}")
    node_index = {node_id: index for index, node_id in enumerate(node_ids)}
    coordinates = BASE._rows_to_matrix(
        [
            [BASE._mp(value, f"{topology['id']}.{node['id']}.x") for value in node["x"]]
            for node in topology["nodes"]
        ]
    )
    retained = [
        element
        for element in topology["elements"]
        if element.get("state", "active") != "deleted"
    ]
    if not retained:
        raise MechanicsInputError("Candidate-B topology has no retained shell")
    element_ids = [element["id"] for element in topology["elements"]]
    if element_ids != sorted(element_ids, key=lambda value: value.encode("utf-8")):
        raise MechanicsInputError(f"topology elements are not ordinal: {topology['id']}")
    deleted = [
        element["id"]
        for element in topology["elements"]
        if element.get("state", "active") == "deleted"
    ]
    components, orphans, edges = BASE._retained_components(node_ids, retained)
    retained_nodes = sorted(
        {node_index[node] for element in retained for node in element["nodes"]}
    )
    length = BASE._topology_length(coordinates, retained_nodes)
    scale = BASE._mixed_unit_scale(len(node_ids), length)
    surface, thickness = _quadrature(cases, rule)
    material_scale = mp.mpf(1) if constitutive_scale is None else constitutive_scale
    if not material_scale > 0 or not mp.isfinite(material_scale):
        raise MechanicsInputError("constitutive scale must be positive finite")
    material = material_scale * _constitutive(cases, constitutive_id)
    b_blocks: list[tuple[mp.mpf, mp.matrix]] = []
    base_b_blocks: list[tuple[mp.mpf, mp.matrix]] = []
    h_blocks: list[tuple[mp.mpf, mp.matrix]] = []
    recovery_blocks: list[mp.matrix] = []
    strain_recovery_blocks: list[mp.matrix] = []
    stress_recovery_blocks: list[mp.matrix] = []
    energy_terms: list[tuple[mp.mpf, mp.matrix, mp.matrix]] = []
    evaluation_records: list[dict[str, Any]] = []
    physical_k = BASE._zeros(6 * len(node_ids), 6 * len(node_ids))
    physical_m = BASE._zeros(6 * len(node_ids), 6 * len(node_ids))
    fingerprints: dict[str, str] = {}
    candidate_digests: dict[str, str] = {}
    for element in retained:
        coordinates_input, directors_input, thickness_input = BASE._element_inputs(
            topology, element
        )
        reference = BASE.build_reference(
            coordinates_input,
            directors_input,
            thickness_input,
            element_id=element["id"],
            connectivity=element["nodes"],
        )
        fingerprints[element["id"]] = reference.fingerprint
        connectivity = [node_index[node] for node in element["nodes"]]
        alpha = BASE._mp(
            element.get("alpha", "1"), f"{topology['id']}.{element['id']}.alpha"
        )
        beta = BASE._mp(
            element.get("beta", "1"), f"{topology['id']}.{element['id']}.beta"
        )
        density = BASE._mp(
            element.get("density", "1"), f"{topology['id']}.{element['id']}.density"
        )
        if min(alpha, beta, density) <= 0:
            raise MechanicsInputError("retained activity and density must be positive")
        local_digest_rows: list[mp.matrix] = []
        for r_value, r_weight in surface:
            for s_value, s_weight in surface:
                for zeta, zeta_weight in thickness:
                    local_b, determinant = candidate_local_strain(
                        reference, r_value, s_value, zeta
                    )
                    local_base, base_determinant = base_without_eq21_local_strain(
                        reference, r_value, s_value, zeta
                    )
                    if base_determinant != determinant:
                        raise RuntimeError("candidate/base Jacobian mismatch")
                    local_h = candidate_displacement(reference, r_value, s_value, zeta)
                    natural_weight = r_weight * s_weight * zeta_weight
                    weight = natural_weight * determinant
                    if not weight > 0 or not mp.isfinite(weight):
                        raise MechanicsInputError("Candidate-B volume weight is not positive finite")
                    b_hat = _scatter(local_b, connectivity, len(node_ids)) * scale
                    base_b_hat = (
                        _scatter(local_base, connectivity, len(node_ids)) * scale
                    )
                    h_hat = (
                        _scatter(local_h, connectivity, len(node_ids)) * scale
                    ) / length
                    b_blocks.append((alpha * weight, b_hat))
                    base_b_blocks.append((alpha * weight, base_b_hat))
                    h_blocks.append((density * beta * weight, h_hat))
                    global_b = _scatter(local_b, connectivity, len(node_ids))
                    global_h = _scatter(local_h, connectivity, len(node_ids))
                    recovery_blocks.append(global_h)
                    strain_recovery_blocks.append(global_b)
                    stress_recovery_blocks.append(material * global_b)
                    energy_terms.append((alpha * weight, global_b, material))
                    shape_values, _ = BASE.q4_shape(r_value, s_value)
                    thickness_value = mp.fsum(
                        shape_values[node] * reference.thickness[node]
                        for node in range(4)
                    )
                    evaluation_records.append(
                        {
                            "element_id": element["id"],
                            "r": r_value,
                            "s": s_value,
                            "zeta": zeta,
                            "thickness": thickness_value,
                            "weight": weight,
                            "B": global_b,
                            "H": global_h,
                        }
                    )
                    physical_k += alpha * weight * (global_b.T * material * global_b)
                    physical_m += density * beta * weight * (global_h.T * global_h)
                    local_digest_rows.append(local_b)
        candidate_digests[element["id"]] = BASE.matrix_digest(BASE._vstack(local_digest_rows))
    weight_b = mp.fsum(weight for weight, _ in b_blocks)
    weight_h = mp.fsum(weight for weight, _ in h_blocks)
    if not weight_b > 0 or not weight_h > 0:
        raise MechanicsInputError("Candidate-B normalized metric has nonpositive weight")
    b_weighted = BASE._vstack(
        [mp.sqrt(weight / weight_b) * block for weight, block in b_blocks]
    )
    base_b_weighted = BASE._vstack(
        [mp.sqrt(weight / weight_b) * block for weight, block in base_b_blocks]
    )
    h_weighted = BASE._vstack(
        [mp.sqrt(weight / weight_h) * block for weight, block in h_blocks]
    )
    rigid, rigid_labels = BASE._rigid_candidates(coordinates, components, length)
    bipartite, alternating = BASE._bipartite_patterns(
        components, edges, len(node_ids)
    )
    result = {
        "id": topology["id"],
        "rule": rule,
        "node_ids": node_ids,
        "node_index": node_index,
        "coordinates": coordinates,
        "retained_elements": retained,
        "deleted_element_ids": deleted,
        "components": components,
        "orphans": orphans,
        "edges": edges,
        "bipartite": bipartite,
        "alternating_patterns": alternating,
        "ell": length,
        "S_q": scale,
        "B_w": b_weighted,
        "B0_w": base_b_weighted,
        "H_w": h_weighted,
        "K_w": BASE._symmetrize(b_weighted.T * b_weighted),
        "M_w": BASE._symmetrize(h_weighted.T * h_weighted),
        "K_physical": BASE._symmetrize(physical_k),
        "M_physical": BASE._symmetrize(physical_m),
        "H_physical_stack": BASE._vstack(recovery_blocks),
        "B_physical_stack": BASE._vstack(strain_recovery_blocks),
        "stress_physical_stack": BASE._vstack(stress_recovery_blocks),
        "energy_terms": energy_terms,
        "evaluation_records": evaluation_records,
        "fingerprints": fingerprints,
        "candidate_element_digests": candidate_digests,
        "rigid_candidates": rigid,
        "rigid_labels": rigid_labels,
        "topology": topology,
        "constitutive_id": constitutive_id,
        "constitutive_scale": material_scale,
    }
    return result


def _partition_record(partition: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "dimensions": dict(partition["dimensions"]),
        "subspaces": dict(partition["subspaces"]),
        "B_parent_scale": BASE.mpf_token(partition["B_parent_scale"]),
        "H_parent_scale": BASE.mpf_token(partition["H_parent_scale"]),
    }


def _drill_coordinate_matrix(assembly: Mapping[str, Any]) -> mp.matrix:
    node_count = len(assembly["node_ids"])
    result = BASE._zeros(6 * node_count, node_count)
    for node in range(node_count):
        result[6 * node + 5, node] = 1
    return result


def _flat_probe_record(
    assembly: Mapping[str, Any],
    free: Mapping[str, Any],
    decimal_digits: int,
    eps_p: mp.mpf,
    multiplier: mp.mpf,
) -> dict[str, Any]:
    drill_coordinates = _drill_coordinate_matrix(assembly)
    restriction = assembly["B_w"] * drill_coordinates
    restriction_rank = BASE._spectral_rank(
        restriction,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
        inherited_scale=free["B_parent_scale"],
    )
    common = BASE._zeros(restriction.cols, 1)
    alternate = BASE._zeros(restriction.cols, 1)
    for node in range(restriction.cols):
        common[node, 0] = 1
        alternate[node, 0] = 1 if node % 2 == 0 else -1
    common_q = drill_coordinates * common
    alternate_q = drill_coordinates * alternate
    common_b = BASE._frob(assembly["B_w"] * common_q)
    common_h = BASE._frob(assembly["H_w"] * common_q)
    alternate_b = BASE._frob(assembly["B_w"] * alternate_q)
    alternate_h = BASE._frob(assembly["H_w"] * alternate_q)
    numerator = (alternate_q.T * assembly["K_physical"] * alternate_q)[0, 0]
    denominator = (alternate_q.T * assembly["M_physical"] * alternate_q)[0, 0]
    ratio = numerator / denominator if denominator > 0 else None
    return {
        "pure_drill_rank": int(restriction_rank["rank"]),
        "pure_drill_rank_pass": int(restriction_rank["rank"]) == 3,
        "pure_drill_sha256": BASE.matrix_digest(restriction),
        "constant_drill": {
            "B_action": BASE.mpf_token(common_b),
            "H_action": BASE.mpf_token(common_h),
            "pass": common_b == 0 and common_h == 0,
        },
        "checkerboard": {
            "B_action": BASE.mpf_token(alternate_b),
            "H_action": BASE.mpf_token(alternate_h),
            "energy_mass_ratio": BASE.mpf_token(ratio) if ratio is not None else None,
            "positive_mass": denominator > 0,
            "positive_energy": numerator > 0,
            "pass": denominator > 0 and numerator > 0,
        },
    }


def _flat_material_records(
    topology: Mapping[str, Any], cases: Mapping[str, Any], rule: str
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for fixture in cases["constitutive_fixtures"]:
        for scale_record in cases["positive_scales_pow2"]:
            scale = _eval_scalar(scale_record, cases)
            assembly = assemble_candidate_topology(
                topology,
                cases,
                rule,
                constitutive_id=fixture["id"],
                constitutive_scale=scale,
            )
            checker = BASE._zeros(assembly["K_physical"].rows, 1)
            for node in range(len(assembly["node_ids"])):
                checker[6 * node + 5, 0] = 1 if node % 2 == 0 else -1
            energy = (checker.T * assembly["K_physical"] * checker)[0, 0]
            mass = (checker.T * assembly["M_physical"] * checker)[0, 0]
            records.append(
                {
                    "constitutive_id": fixture["id"],
                    "scale": BASE.mpf_token(scale),
                    "energy": BASE.mpf_token(energy),
                    "mass": BASE.mpf_token(mass),
                    "positive_energy": energy > 0,
                    "positive_mass": mass > 0,
                    "pass": energy > 0 and mass > 0,
                    "certificate_logic": (
                        "exact_nonzero_flat_B/H+positive_quadrature+"
                        "exact_SPD_constitutive+positive_density"
                    ),
                }
            )
    return records


def _beam_shell_work_record(
    assembly: Mapping[str, Any],
    constraint: Mapping[str, Any],
    cases: Mapping[str, Any],
) -> dict[str, Any]:
    fixture = cases["response_fixtures"]["beam_shell_virtual_work"]
    if (
        assembly["topology"]["id"] != fixture["topology_id"]
        or constraint["id"] != fixture["constraint_id"]
    ):
        raise MechanicsInputError("beam-shell work fixture identity mismatch")
    row_inputs = constraint["rows"]
    if isinstance(row_inputs, dict):
        row_inputs = [row_inputs]
    if len(row_inputs) != 1:
        raise MechanicsInputError("beam-shell work fixture requires one physical row")
    dimension = assembly["B_w"].cols
    physical_row = BASE._zeros(1, dimension)
    for node_id, dof, coefficient in row_inputs[0]["terms"]:
        column = 6 * assembly["node_index"][node_id] + BASE.DOF_INDEX[dof]
        physical_row[0, column] += BASE._mp(
            coefficient, f"{constraint['id']}.work_coefficient"
        )
    increment = BASE._zeros(dimension, 1)
    for node_id, dof, value in fixture["admissible_increment"]:
        column = 6 * assembly["node_index"][node_id] + BASE.DOF_INDEX[dof]
        increment[column, 0] += BASE._mp(value, "beam_shell.increment")
    multiplier = BASE._mp(fixture["multiplier"], "beam_shell.multiplier")
    force = physical_row.T * multiplier
    constraint_action = (physical_row * increment)[0, 0]

    def group_work(terms: Sequence[Sequence[str]]) -> mp.mpf:
        return mp.fsum(
            increment[
                6 * assembly["node_index"][node_id] + BASE.DOF_INDEX[dof], 0
            ]
            * force[
                6 * assembly["node_index"][node_id] + BASE.DOF_INDEX[dof], 0
            ]
            for node_id, dof in terms
        )

    shell_work = group_work(fixture["shell_terms"])
    beam_work = group_work(fixture["beam_terms"])
    total_work = (increment.T * force)[0, 0]
    return {
        "coordinate_system": fixture["coordinate_system"],
        "constraint_action": BASE.mpf_token(constraint_action),
        "shell_work": BASE.mpf_token(shell_work),
        "beam_work": BASE.mpf_token(beam_work),
        "total_work": BASE.mpf_token(total_work),
        "constraint_exact_zero": constraint_action == 0,
        "total_work_exact_zero": total_work == 0,
        "equal_and_opposite_exact": shell_work == -beam_work,
        "pass": (
            constraint_action == 0
            and total_work == 0
            and shell_work == -beam_work
            and shell_work != 0
        ),
    }


def _physical_constraints(
    assembly: Mapping[str, Any],
    free: Mapping[str, Any],
    decimal_digits: int,
    eps_p: mp.mpf,
    multiplier: mp.mpf,
    cases: Mapping[str, Any],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    zero_candidate_rows = BASE._zeros(0, assembly["B_w"].cols)
    for constraint in assembly["topology"].get("constraint_sets", []):
        normalized = BASE._normalize_constraint_set(assembly, constraint, eps_p)
        feasibility = BASE._constraint_feasibility(
            normalized, zero_candidate_rows, decimal_digits, eps_p
        )
        record: dict[str, Any] = {
            "id": constraint["id"],
            "kind": constraint["kind"],
            "qualified": bool(constraint.get("qualified", True)),
            "expected_feasible": bool(constraint["expected_feasible"]),
            "feasible": bool(feasibility["feasible"]),
            "ranks": feasibility["ranks"],
        }
        if record["feasible"]:
            constrained = BASE.constrained_partition(
                assembly,
                free,
                normalized["rows"],
                decimal_digits,
                eps_p,
                multiplier,
            )
            record["dimensions"] = constrained["dimensions"]
            record["subspaces"] = constrained["subspaces"]
        if constraint["id"] == cases["response_fixtures"]["beam_shell_virtual_work"]["constraint_id"]:
            record["beam_shell_virtual_work"] = _beam_shell_work_record(
                assembly, constraint, cases
            )
        result.append(record)
    return result


def _exact_g_reduction(
    assembly: Mapping[str, Any],
    free: Mapping[str, Any],
    decimal_digits: int,
    eps_p: mp.mpf,
    multiplier: mp.mpf,
) -> dict[str, Any]:
    dimension = assembly["B_w"].cols
    if free["dimensions"]["G"] != 1:
        return {
            "applicable": False,
            "pass": False,
            "reason": "free_G_dimension_is_not_one",
            "observed_G": free["dimensions"]["G"],
        }
    admissible_projector = BASE._symmetrize(
        BASE._identity(dimension) - free["projectors"]["G"]
    )
    basis = BASE._canonical_basis(admissible_projector, dimension - 1, eps_p)
    gauge_basis = BASE._canonical_basis(free["projectors"]["G"], 1, eps_p)
    reduced_b = assembly["B_w"] * basis
    reduced_h = assembly["H_w"] * basis
    rank = BASE._spectral_rank(
        reduced_b,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
        inherited_scale=free["B_parent_scale"],
    )
    nullity = int(rank["kernel_dimension"])
    lifted_rigid = basis.T * assembly["rigid_candidates"]
    rigid_parent_scale = BASE._spectral_rank(
        assembly["rigid_candidates"],
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=mp.mpf(1),
    )["sigma_max"]
    rigid_rank = BASE._spectral_rank(
        lifted_rigid,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
        inherited_scale=rigid_parent_scale,
    )
    s_inverse = assembly["S_q"] ** -1
    t_physical = assembly["S_q"] * basis
    g_physical = assembly["S_q"] * gauge_basis
    c_physical = gauge_basis.T * s_inverse
    r_physical = basis.T * s_inverse
    k_hat_physical = BASE._symmetrize(
        assembly["S_q"].T * assembly["K_physical"] * assembly["S_q"]
    )
    m_hat_physical = BASE._symmetrize(
        assembly["S_q"].T * assembly["M_physical"] * assembly["S_q"]
    )
    k_reduced = BASE._symmetrize(basis.T * k_hat_physical * basis)
    m_reduced = BASE._symmetrize(basis.T * m_hat_physical * basis)
    y = BASE._zeros(basis.cols, 1)
    z = BASE._zeros(basis.cols, 1)
    for index in range(basis.cols):
        y[index, 0] = mp.mpf(index + 1) / basis.cols
        z[index, 0] = mp.mpf((-1) ** index) / (index + 1)
    full_y = basis * y
    full_z = basis * z
    energy_error = abs(
        (y.T * k_reduced * z)[0, 0]
        - (full_y.T * k_hat_physical * full_z)[0, 0]
    )
    mass_error = abs(
        (y.T * m_reduced * z)[0, 0]
        - (full_y.T * m_hat_physical * full_z)[0, 0]
    )
    load_physical = BASE._zeros(dimension, 1)
    for index in range(dimension):
        load_physical[index, 0] = mp.mpf((-1) ** index) * (index + 1) / dimension
    load_reduced = t_physical.T * load_physical
    load_error = abs(
        (y.T * load_reduced)[0, 0]
        - ((t_physical * y).T * load_physical)[0, 0]
    )
    state_physical = t_physical * y
    state_roundtrip = r_physical * state_physical
    state_error = BASE._frob(state_roundtrip - y)
    recovery_maps = {
        "displacement": assembly["H_physical_stack"],
        "strain": assembly["B_physical_stack"],
        "constitutive": assembly["stress_physical_stack"],
    }
    recovery_records: dict[str, Any] = {}
    for name, operator in recovery_maps.items():
        reduced_operator = operator * t_physical
        left = reduced_operator * y
        right = operator * state_physical
        participating_dimension = max(
            1, operator.rows, operator.cols, t_physical.cols
        )
        recovery_tolerance = 4096 * participating_dimension * eps_p
        recovery_records[name] = {
            "reduced_sha256": BASE.matrix_digest(reduced_operator),
            "r_eq": BASE.mpf_token(BASE._equality_residual(left, right)),
            "participating_dimension": participating_dimension,
            "r_tol": BASE.mpf_token(recovery_tolerance),
        }
    identity_residual = BASE._equality_residual(
        basis.T * basis, BASE._identity(basis.cols)
    )
    projector_residual = BASE._equality_residual(
        basis * basis.T, admissible_projector
    )
    gauge_residual = _r_zero_from_scale(
        basis.T * gauge_basis, mp.mpf(1), BASE._frob(gauge_basis)
    )
    c_t_residual = _r_zero_from_scale(
        c_physical * t_physical, mp.mpf(1), BASE._frob(t_physical)
    )
    c_g_residual = BASE._equality_residual(
        c_physical * g_physical, BASE._identity(1)
    )
    r_t_residual = BASE._equality_residual(
        r_physical * t_physical, BASE._identity(basis.cols)
    )
    lift_projector_residual = BASE._equality_residual(
        t_physical * r_physical,
        assembly["S_q"] * admissible_projector * s_inverse,
    )
    def tolerance_for(*dimensions: int) -> mp.mpf:
        return 4096 * max(1, *(int(value) for value in dimensions)) * eps_p

    tolerances = {
        "energy_work": tolerance_for(
            basis.rows, basis.cols, k_hat_physical.rows, k_hat_physical.cols
        ),
        "mass_work": tolerance_for(
            basis.rows, basis.cols, m_hat_physical.rows, m_hat_physical.cols
        ),
        "load_work": tolerance_for(
            y.rows,
            load_reduced.rows,
            t_physical.rows,
            t_physical.cols,
            load_physical.rows,
        ),
        "state_roundtrip": tolerance_for(
            r_physical.rows, r_physical.cols, state_physical.rows, y.rows
        ),
        "T_orthonormality": tolerance_for(basis.rows, basis.cols),
        "T_projector": tolerance_for(basis.rows, basis.cols),
        "T_gauge_orthogonality": tolerance_for(
            basis.T.rows, basis.T.cols, gauge_basis.rows, gauge_basis.cols
        ),
        "C_T_zero": tolerance_for(
            c_physical.rows, c_physical.cols, t_physical.rows, t_physical.cols
        ),
        "C_G_identity": tolerance_for(
            c_physical.rows, c_physical.cols, g_physical.rows, g_physical.cols
        ),
        "R_T_identity": tolerance_for(
            r_physical.rows, r_physical.cols, t_physical.rows, t_physical.cols
        ),
        "T_R_projector": tolerance_for(
            t_physical.rows, t_physical.cols, r_physical.rows, r_physical.cols
        ),
    }

    energy_residual = _scalar_r_eq(
        (y.T * k_reduced * z)[0, 0],
        (full_y.T * k_hat_physical * full_z)[0, 0],
    )
    mass_residual = _scalar_r_eq(
        (y.T * m_reduced * z)[0, 0],
        (full_y.T * m_hat_physical * full_z)[0, 0],
    )
    load_residual = _scalar_r_eq(
        (y.T * load_reduced)[0, 0],
        ((t_physical * y).T * load_physical)[0, 0],
    )
    state_residual = BASE._equality_residual(state_roundtrip, y)
    recovery_pass = all(
        _mpf_from_token(record["r_eq"]) <= _mpf_from_token(record["r_tol"])
        for record in recovery_records.values()
    )

    gauge_annihilation: dict[str, Any] = {}
    for name, operator in (
        ("B", assembly["B_physical_stack"]),
        ("H", assembly["H_physical_stack"]),
        ("K", assembly["K_physical"]),
        ("M", assembly["M_physical"]),
    ):
        operator_scale = BASE._spectral_rank(
            operator,
            decimal_digits=decimal_digits,
            eps_p=eps_p,
            multiplier=mp.mpf(1),
        )["sigma_max"]
        residual = _r_zero_from_scale(
            operator * g_physical, operator_scale, BASE._frob(g_physical)
        )
        annihilation_tolerance = tolerance_for(
            operator.rows, operator.cols, g_physical.rows, g_physical.cols
        )
        gauge_annihilation[name] = {
            "r_zero": BASE.mpf_token(residual),
            "participating_dimension": max(
                1, operator.rows, operator.cols, g_physical.rows, g_physical.cols
            ),
            "r_tol": BASE.mpf_token(annihilation_tolerance),
        }
    gauge_annihilation_pass = all(
        _mpf_from_token(record["r_zero"]) <= _mpf_from_token(record["r_tol"])
        for record in gauge_annihilation.values()
    )
    map_pass = (
        energy_residual <= tolerances["energy_work"]
        and mass_residual <= tolerances["mass_work"]
        and load_residual <= tolerances["load_work"]
        and state_residual <= tolerances["state_roundtrip"]
        and recovery_pass
        and identity_residual <= tolerances["T_orthonormality"]
        and projector_residual <= tolerances["T_projector"]
        and gauge_residual <= tolerances["T_gauge_orthogonality"]
        and c_t_residual <= tolerances["C_T_zero"]
        and c_g_residual <= tolerances["C_G_identity"]
        and r_t_residual <= tolerances["R_T_identity"]
        and lift_projector_residual <= tolerances["T_R_projector"]
        and gauge_annihilation_pass
    )
    return {
        "applicable": True,
        "retained_coordinates": basis.cols,
        "rank": int(rank["rank"]),
        "nullity": nullity,
        "rigid_rank": int(rigid_rank["rank"]),
        "T_sha256": BASE.matrix_digest(basis),
        "T_physical_sha256": BASE.matrix_digest(t_physical),
        "G_physical_sha256": BASE.matrix_digest(g_physical),
        "C_physical_sha256": BASE.matrix_digest(c_physical),
        "R_physical_sha256": BASE.matrix_digest(r_physical),
        "K_sha256": BASE.matrix_digest(k_reduced),
        "M_sha256": BASE.matrix_digest(m_reduced),
        "energy_work_error": BASE.mpf_token(energy_error),
        "mass_work_error": BASE.mpf_token(mass_error),
        "load_work_error": BASE.mpf_token(load_error),
        "state_roundtrip_error": BASE.mpf_token(state_error),
        "energy_work_residual": BASE.mpf_token(energy_residual),
        "mass_work_residual": BASE.mpf_token(mass_residual),
        "load_work_residual": BASE.mpf_token(load_residual),
        "state_roundtrip_residual": BASE.mpf_token(state_residual),
        "recovery_maps": recovery_records,
        "T_orthonormality_error": BASE.mpf_token(identity_residual),
        "T_projector_error": BASE.mpf_token(projector_residual),
        "T_gauge_orthogonality_error": BASE.mpf_token(gauge_residual),
        "C_T_zero_residual": BASE.mpf_token(c_t_residual),
        "C_G_identity_residual": BASE.mpf_token(c_g_residual),
        "R_T_identity_residual": BASE.mpf_token(r_t_residual),
        "T_R_projector_residual": BASE.mpf_token(lift_projector_residual),
        "gauge_physical_annihilation": gauge_annihilation,
        "r_tols": {
            key: BASE.mpf_token(value) for key, value in tolerances.items()
        },
        "map_pass": map_pass,
        "constraint_kind": "explicit_reported_exact_zero_mass_G_only",
        "pass": (
            int(rank["rank"]) == 17
            and nullity == 6
            and int(rigid_rank["rank"]) == 6
            and map_pass
        ),
    }


def _scalar_r_eq(left: mp.mpf, right: mp.mpf) -> mp.mpf:
    numerator = abs(left - right)
    denominator = max(abs(left), abs(right))
    if denominator == 0:
        return mp.mpf(0) if numerator == 0 else mp.inf
    return numerator / denominator


def _r_zero_from_scale(
    action: mp.matrix, operator_scale: mp.mpf, vector_norm: mp.mpf
) -> mp.mpf:
    numerator = BASE._frob(action)
    denominator = operator_scale * vector_norm
    if denominator == 0:
        return mp.mpf(0) if numerator == 0 else mp.inf
    return numerator / denominator


def _energy_record(
    assembly: Mapping[str, Any], decimal_digits: int, eps_p: mp.mpf
) -> dict[str, Any]:
    k_value = assembly["K_physical"]
    m_value = assembly["M_physical"]
    try:
        k_psd = BASE._psd_record(k_value, decimal_digits, eps_p)
        k_psd_pass = True
    except RuntimeError as error:
        k_psd = {"error": str(error)}
        k_psd_pass = False
    try:
        m_psd = BASE._psd_record(m_value, decimal_digits, eps_p)
        m_psd_pass = True
    except RuntimeError as error:
        m_psd = {"error": str(error)}
        m_psd_pass = False
    dimension = k_value.rows
    q_value = BASE._zeros(dimension, 1)
    delta = BASE._zeros(dimension, 1)
    for index in range(dimension):
        q_value[index, 0] = mp.mpf(index + 1) / dimension
        delta[index, 0] = mp.mpf((-1) ** index) / (index + 2)
    residual = k_value * q_value
    residual_terms = BASE._zeros(dimension, 1)
    delta_terms = BASE._zeros(dimension, 1)
    virtual_work_terms = mp.mpf(0)
    for weight, b_value, material in assembly["energy_terms"]:
        b_q = b_value * q_value
        b_delta = b_value * delta
        residual_terms += weight * (b_value.T * (material * b_q))
        delta_terms += weight * (b_value.T * (material * b_delta))
        virtual_work_terms += weight * (b_delta.T * material * b_q)[0, 0]
    directional = (delta.T * residual)[0, 0]
    potential_plus = ((q_value + delta).T * k_value * (q_value + delta))[0, 0] / 2
    potential_minus = ((q_value - delta).T * k_value * (q_value - delta))[0, 0] / 2
    central_work = (potential_plus - potential_minus) / 2
    central_error = abs(directional - central_work)
    rigid_action = BASE._frob(k_value * assembly["rigid_candidates"])
    k_scale = BASE._spectral_rank(
        k_value,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=mp.mpf(1),
    )["sigma_max"]
    participating_dimension = max(1, k_value.rows, k_value.cols)
    tolerances = {
        "rigid": 4096 * max(
            participating_dimension,
            assembly["rigid_candidates"].rows,
            assembly["rigid_candidates"].cols,
        ) * eps_p,
        "gradient": 4096 * participating_dimension * eps_p,
        "hessian": 4096 * participating_dimension * eps_p,
        "virtual_work": 4096 * participating_dimension * eps_p,
        "central_difference": 4096 * participating_dimension * eps_p,
    }
    rigid_denominator = k_scale * BASE._frob(assembly["rigid_candidates"])
    normalized_rigid = (
        (mp.mpf(0) if rigid_action == 0 else mp.inf)
        if rigid_denominator == 0
        else rigid_action / rigid_denominator
    )
    gradient_residual = BASE._equality_residual(residual, residual_terms)
    hessian_residual = BASE._equality_residual(k_value * delta, delta_terms)
    virtual_error = abs(directional - virtual_work_terms)
    virtual_residual = _scalar_r_eq(directional, virtual_work_terms)
    central_residual = _scalar_r_eq(directional, central_work)
    return {
        "K_sha256": BASE.matrix_digest(k_value),
        "M_sha256": BASE.matrix_digest(m_value),
        "K_psd": k_psd,
        "M_psd": m_psd,
        "gradient_sha256": BASE.matrix_digest(residual),
        "hessian_sha256": BASE.matrix_digest(k_value),
        "gradient_residual": BASE.mpf_token(gradient_residual),
        "hessian_residual": BASE.mpf_token(hessian_residual),
        "virtual_work_residual": BASE.mpf_token(virtual_residual),
        "central_difference_residual": BASE.mpf_token(central_residual),
        "rigid_normalized_residual": BASE.mpf_token(normalized_rigid),
        "rigid_pass": normalized_rigid <= tolerances["rigid"],
        "gradient_pass": gradient_residual <= tolerances["gradient"],
        "hessian_pass": hessian_residual <= tolerances["hessian"],
        "virtual_work_pass": (
            virtual_residual <= tolerances["virtual_work"]
            and central_residual <= tolerances["central_difference"]
        ),
        "K_psd_pass": k_psd_pass,
        "M_psd_pass": m_psd_pass,
        "r_tols": {
            key: BASE.mpf_token(value) for key, value in tolerances.items()
        },
        "total_energy_cross_terms_included": True,
    }


def _physical_field_vector(
    assembly: Mapping[str, Any], field: str
) -> mp.matrix:
    result = BASE._zeros(6 * len(assembly["node_ids"]), 1)
    for node in range(len(assembly["node_ids"])):
        x_value = assembly["coordinates"][node, 0]
        if field == "membrane_extension_x":
            result[6 * node, 0] = x_value
        elif field == "transverse_shear_xz":
            result[6 * node + 2, 0] = x_value
        elif field == "constant_bending_x":
            result[6 * node + 2, 0] = x_value**2 / 2
            result[6 * node + 4, 0] = -x_value
        else:
            raise MechanicsInputError(f"unknown physical patch field: {field}")
    return result


def _patch_response_record(
    topology: Mapping[str, Any],
    cases: Mapping[str, Any],
    rule: str,
    eps_p: mp.mpf,
) -> dict[str, Any]:
    assembly = assemble_candidate_topology(topology, cases, rule)
    fields: dict[str, Any] = {}
    for field in (
        "membrane_extension_x",
        "constant_bending_x",
        "transverse_shear_xz",
    ):
        vector = _physical_field_vector(assembly, field)
        numerator = mp.mpf(0)
        observed_norm_squared = mp.mpf(0)
        expected_norm_squared = mp.mpf(0)
        max_shear = mp.mpf(0)
        for record in assembly["evaluation_records"]:
            observed = record["B"] * vector
            expected = BASE._zeros(5, 1)
            if field == "membrane_extension_x":
                expected[0, 0] = 1
            elif field == "transverse_shear_xz":
                expected[3, 0] = 1
            else:
                expected[0, 0] = -record["zeta"] * record["thickness"] / 2
            difference = observed - expected
            numerator += record["weight"] * BASE._frob(difference) ** 2
            observed_norm_squared += record["weight"] * BASE._frob(observed) ** 2
            expected_norm_squared += record["weight"] * BASE._frob(expected) ** 2
            max_shear = max(max_shear, abs(observed[3, 0]), abs(observed[4, 0]))
        denominator = max(
            mp.sqrt(observed_norm_squared), mp.sqrt(expected_norm_squared)
        )
        residual = (
            (mp.mpf(0) if numerator == 0 else mp.inf)
            if denominator == 0
            else mp.sqrt(numerator) / denominator
        )
        tolerance = 4096 * max(1, assembly["B_w"].rows, assembly["B_w"].cols) * eps_p
        fields[field] = {
            "residual": BASE.mpf_token(residual),
            "max_transverse_shear": BASE.mpf_token(max_shear),
            "tolerance": BASE.mpf_token(tolerance),
            "pass": residual <= tolerance,
        }
    return {"topology": topology["id"], "rule": rule, "fields": fields}


def _thickness_locking_record(
    topology: Mapping[str, Any],
    cases: Mapping[str, Any],
    rule: str,
    eps_p: mp.mpf,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    stack_dimensions: list[int] = []
    for exponent in (0, -1, -2):
        scaled = json.loads(json.dumps(topology))
        factor = Decimal(2) ** exponent
        for element in scaled["elements"]:
            original = element["thickness"]
            if not isinstance(original, str):
                raise MechanicsInputError("thickness sequence requires scalar strings")
            value = Decimal(original) * factor
            element["thickness"] = format(value, "f").rstrip("0").rstrip(".")
        assembly = assemble_candidate_topology(scaled, cases, rule)
        membrane = _physical_field_vector(assembly, "membrane_extension_x")
        bending = _physical_field_vector(assembly, "constant_bending_x")
        membrane_energy = (
            membrane.T * assembly["K_physical"] * membrane
        )[0, 0] / 2
        bending_energy = (
            bending.T * assembly["K_physical"] * bending
        )[0, 0] / 2
        stack_dimensions.append(assembly["B_w"].rows)
        shear_action = mp.mpf(0)
        strain_action = mp.mpf(0)
        for evaluation in assembly["evaluation_records"]:
            strain = evaluation["B"] * bending
            shear_action += evaluation["weight"] * (
                strain[3, 0] ** 2 + strain[4, 0] ** 2
            )
            strain_action += evaluation["weight"] * BASE._frob(strain) ** 2
        shear_ratio = (
            (mp.mpf(0) if shear_action == 0 else mp.inf)
            if strain_action == 0
            else mp.sqrt(shear_action / strain_action)
        )
        records.append(
            {
                "thickness_exponent": exponent,
                "membrane_energy": BASE.mpf_token(membrane_energy),
                "bending_energy": BASE.mpf_token(bending_energy),
                "bending_shear_ratio": BASE.mpf_token(shear_ratio),
            }
        )
    membrane_base = _mpf_from_token(records[0]["membrane_energy"])
    bending_base = _mpf_from_token(records[0]["bending_energy"])
    participating_dimension = max(
        1, len(topology["nodes"]) * 6, *stack_dimensions
    )
    tolerance = 4096 * participating_dimension * eps_p
    membrane_pass = membrane_base > 0
    bending_pass = bending_base > 0
    locking_pass = True
    for record in records:
        exponent = record["thickness_exponent"]
        membrane_value = _mpf_from_token(record["membrane_energy"])
        bending_value = _mpf_from_token(record["bending_energy"])
        expected_membrane = membrane_base * mp.power(2, exponent)
        expected_bending = bending_base * mp.power(2, 3 * exponent)
        membrane_scale = abs(expected_membrane)
        bending_scale = abs(expected_bending)
        membrane_residual = _scalar_r_eq(membrane_value, expected_membrane)
        bending_residual = _scalar_r_eq(bending_value, expected_bending)
        shear_ratio = _mpf_from_token(record["bending_shear_ratio"])
        record["membrane_scaling_residual"] = BASE.mpf_token(membrane_residual)
        record["bending_scaling_residual"] = BASE.mpf_token(bending_residual)
        membrane_pass = membrane_pass and membrane_residual <= tolerance
        bending_pass = bending_pass and bending_residual <= tolerance
        locking_pass = locking_pass and shear_ratio <= tolerance
    return {
        "topology": topology["id"],
        "rule": rule,
        "records": records,
        "participating_dimension": participating_dimension,
        "tolerance": BASE.mpf_token(tolerance),
        "membrane_t_pass": membrane_pass,
        "bending_t3_pass": bending_pass,
        "thin_locking_pass": locking_pass,
    }


def _fraction_decimal(value: Fraction) -> str:
    denominator = value.denominator
    twos = 0
    fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise MechanicsInputError("fixture fraction has a non-terminating decimal")
    places = max(twos, fives)
    scaled = value.numerator * (2 ** (places - twos)) * (5 ** (places - fives))
    sign = "-" if scaled < 0 else ""
    digits = str(abs(scaled)).rjust(places + 1, "0")
    if places == 0:
        return sign + digits
    result = sign + digits[:-places] + "." + digits[-places:]
    result = result.rstrip("0").rstrip(".")
    return "0" if result in ("", "-0") else result


def _curved_refinement_topology(
    level: int, cases: Mapping[str, Any]
) -> dict[str, Any]:
    fixture = cases["response_fixtures"]["curved_refinement"]
    if level not in fixture["levels"] or level <= 0:
        raise MechanicsInputError("unregistered curved-refinement level")
    nodes: list[dict[str, Any]] = []
    for prefix, y_value in (("b", Fraction(0)), ("t", Fraction(1))):
        for index in range(level + 1):
            x_value = Fraction(index, level)
            nodes.append(
                {
                    "id": f"{prefix}{index:03d}",
                    "x": [
                        _fraction_decimal(x_value),
                        _fraction_decimal(y_value),
                        _fraction_decimal(x_value * x_value / 10),
                    ],
                }
            )
    elements: list[dict[str, Any]] = []
    for index in range(level):
        local_x = (
            Fraction(index, level),
            Fraction(index + 1, level),
            Fraction(index + 1, level),
            Fraction(index, level),
        )
        elements.append(
            {
                "id": f"e{index:03d}",
                "nodes": [
                    f"b{index:03d}",
                    f"b{index + 1:03d}",
                    f"t{index + 1:03d}",
                    f"t{index:03d}",
                ],
                "state": "active",
                "director_seeds": [
                    [_fraction_decimal(-x_value / 5), "0", "1"]
                    for x_value in local_x
                ],
                "thickness": fixture["thickness"],
            }
        )
    topology = {
        "id": f"candidate_b_curved_refinement_{level:03d}",
        "nodes": nodes,
        "elements": elements,
    }
    if [node["id"] for node in nodes] != sorted(
        (node["id"] for node in nodes), key=lambda value: value.encode("utf-8")
    ):
        raise MechanicsInputError("generated curved nodes are not ordinal")
    return topology


def _curved_refinement_record(
    cases: Mapping[str, Any],
    rule: str,
    decimal_digits: int,
    eps_p: mp.mpf,
) -> dict[str, Any]:
    fixture = cases["response_fixtures"]["curved_refinement"]
    levels = list(fixture["levels"])
    records: list[dict[str, Any]] = []
    for level in levels:
        topology = _curved_refinement_topology(int(level), cases)
        assembly = assemble_candidate_topology(topology, cases, rule)
        field = _physical_field_vector(assembly, fixture["field"])
        energy = (field.T * assembly["K_physical"] * field)[0, 0] / 2
        dimensions: dict[str, Any] = {}
        for multiplier_text in MULTIPLIERS:
            partition = BASE.free_partition(
                assembly,
                decimal_digits,
                eps_p,
                mp.mpf(multiplier_text),
            )
            dimensions[multiplier_text] = dict(partition["dimensions"])
        records.append(
            {
                "level": int(level),
                "node_count": len(topology["nodes"]),
                "element_count": len(topology["elements"]),
                "energy": BASE.mpf_token(energy),
                "positive_energy": energy > 0,
                "dimensions": dimensions,
                "stable_dimensions": all(
                    value == next(iter(dimensions.values()))
                    for value in dimensions.values()
                ),
                "no_positive_mass_quotient_mechanism": all(
                    value["Z"] == 0 for value in dimensions.values()
                ),
            }
        )
    reference = _mpf_from_token(records[-1]["energy"])
    if not reference > 0:
        raise MechanicsInputError("curved reference energy is not positive")
    for record in records:
        value = _mpf_from_token(record["energy"])
        record["relative_error_to_reference"] = BASE.mpf_token(
            abs(value - reference) / abs(reference)
        )
    slopes: list[dict[str, Any]] = []
    required = mp.mpf(fixture["minimum_observed_slope_fraction"]) * int(
        fixture["nominal_order"]
    )
    for left, right in zip(records[:-2], records[1:-1], strict=True):
        left_error = _mpf_from_token(left["relative_error_to_reference"])
        right_error = _mpf_from_token(right["relative_error_to_reference"])
        if left_error == 0 and right_error == 0:
            slope = mp.inf
            status = "exact_equal"
        elif left_error > 0 and right_error == 0:
            slope = mp.inf
            status = "next_exact_reference"
        elif left_error > 0 and right_error > 0:
            slope = mp.log(left_error / right_error, 2)
            status = "finite"
        else:
            slope = -mp.inf
            status = "nonmonotone_or_undefined"
        slopes.append(
            {
                "from_level": left["level"],
                "to_level": right["level"],
                "status": status,
                "slope": None if not mp.isfinite(slope) else BASE.mpf_token(slope),
                "passes_required_order": slope >= required,
            }
        )
    return {
        "rule": rule,
        "response_quantity": fixture["response_quantity"],
        "error_definition": fixture["error_definition"],
        "nominal_order": int(fixture["nominal_order"]),
        "minimum_required_slope": BASE.mpf_token(required),
        "records": records,
        "slopes": slopes,
        "pass": (
            all(record["positive_energy"] for record in records)
            and all(record["stable_dimensions"] for record in records)
            and all(
                record["no_positive_mass_quotient_mechanism"]
                for record in records
            )
            and all(record["passes_required_order"] for record in slopes)
        ),
    }


def analyze_topology(
    topology: Mapping[str, Any],
    cases: Mapping[str, Any],
    decimal_digits: int,
    eps_p: mp.mpf,
    rule: str,
) -> dict[str, Any]:
    assembly = assemble_candidate_topology(topology, cases, rule)
    base_assembly = dict(assembly)
    base_assembly["B_w"] = assembly["B0_w"]
    base_assembly["K_w"] = BASE._symmetrize(
        assembly["B0_w"].T * assembly["B0_w"]
    )
    sensitivities: dict[str, Any] = {}
    for multiplier_text in MULTIPLIERS:
        multiplier = mp.mpf(multiplier_text)
        free = BASE.free_partition(assembly, decimal_digits, eps_p, multiplier)
        base_free = BASE.free_partition(
            base_assembly, decimal_digits, eps_p, multiplier
        )
        record: dict[str, Any] = {
            "free": _partition_record(free),
            "base_without_eq21_free": _partition_record(base_free),
            "physical_constraint_sets": _physical_constraints(
                assembly, free, decimal_digits, eps_p, multiplier, cases
            ),
        }
        if topology["id"] == "one_square":
            record["flat_probes"] = _flat_probe_record(
                assembly, free, decimal_digits, eps_p, multiplier
            )
            record["exact_g_reduction"] = _exact_g_reduction(
                assembly, free, decimal_digits, eps_p, multiplier
            )
        sensitivities[multiplier_text] = record
    result = {
        "id": topology["id"],
        "rule": rule,
        "node_ids": assembly["node_ids"],
        "retained_element_ids": [element["id"] for element in assembly["retained_elements"]],
        "deleted_element_ids": assembly["deleted_element_ids"],
        "components": [
            [assembly["node_ids"][node] for node in component]
            for component in assembly["components"]
        ],
        "orphan_node_ids": [assembly["node_ids"][node] for node in assembly["orphans"]],
        "bipartite": assembly["bipartite"],
        "ell": BASE.mpf_token(assembly["ell"]),
        "director_fingerprints": assembly["fingerprints"],
        "candidate_element_digests": assembly["candidate_element_digests"],
        "energy": _energy_record(assembly, decimal_digits, eps_p),
        "sensitivities": sensitivities,
    }
    if topology["id"] == "one_square":
        result["material_scaling"] = _flat_material_records(topology, cases, rule)
    return result


def _pointwise_derivative_record(cases: Mapping[str, Any]) -> dict[str, Any]:
    drill_cases = _drill_cases()
    local = next(record for record in drill_cases["local_cases"] if record["id"] == "square_uniform")
    reference = BASE.build_reference(
        local["coordinates"],
        local["director_seeds"],
        local["thickness"],
        element_id="candidate-b-derivative-square",
        connectivity=("n0", "n1", "n2", "n3"),
    )
    samples: list[dict[str, Any]] = []
    for point in cases["pointwise_derivative_samples"]:
        r_value = _eval_scalar(point["r"], cases)
        s_value = _eval_scalar(point["s"], cases)
        h_value, h_r, h_s = hd_operators(reference, r_value, s_value)
        incremental = compatible_surface_operator(reference, r_value, s_value)
        candidate = candidate_covariant_strain(reference, r_value, s_value, mp.mpf(0))
        base_without_eq21 = base_without_eq21_covariant_strain(
            reference, r_value, s_value, mp.mpf(0)
        )
        delta = candidate - base_without_eq21
        membrane_delta = mp.matrix(
            [[delta[row, column] for column in range(24)] for row in range(3)]
        )
        shear_delta = mp.matrix(
            [[delta[3 + row, column] for column in range(24)] for row in range(2)]
        )
        accepted_hd = BASE.displacement_operator(
            reference, r_value, s_value, mp.mpf(0), include_drill=True
        ) - BASE.displacement_operator(
            reference, r_value, s_value, mp.mpf(0), include_drill=False
        )
        published = BASE.covariant_strain(reference, r_value, s_value, mp.mpf(0))
        literal_base = BASE._raw_covariant(reference, r_value, s_value, mp.mpf(0))
        literal_membrane = BASE.eq25_membrane(reference, r_value, s_value) - BASE._mid_membrane(
            reference, r_value, s_value
        )
        for row in range(3):
            for column in range(24):
                literal_base[row, column] += literal_membrane[row, column]
        literal_shear = BASE._assumed_shear(reference, r_value, s_value, mp.mpf(0))
        for row in range(2):
            for column in range(24):
                literal_base[3 + row, column] = literal_shear[row, column]
        samples.append(
            {
                "id": point["id"],
                "H_D_sha256": BASE.matrix_digest(h_value),
                "H_D_r_sha256": BASE.matrix_digest(h_r),
                "H_D_s_sha256": BASE.matrix_digest(h_s),
                "B_D_sha256": BASE.matrix_digest(incremental),
                "candidate_sha256": BASE.matrix_digest(candidate),
                "literal_published_sha256": BASE.matrix_digest(published),
                "eq21_superseded": BASE.matrix_digest(candidate) != BASE.matrix_digest(published),
                "accepted_H_D_equal": BASE._exact_zero(h_value - accepted_hd),
                "compatible_membrane_equal": BASE._exact_zero(
                    membrane_delta - incremental
                ),
                "incremental_shear_exact_zero": BASE._exact_zero(shear_delta),
                "literal_eq24_25_base_equal": BASE._exact_zero(
                    base_without_eq21 - literal_base
                ),
            }
        )
    return {
        "samples": samples,
        "full_eq10_derivatives": True,
        "eq11_used": False,
        "eq21_activation_count": 0,
        "eq25_tying_includes_H_D": False,
        "eq27_activation_count": 0,
    }


def _rule_categories(topologies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        topology["id"]: {
            multiplier: {
                "free": topology["sensitivities"][multiplier]["free"]["dimensions"],
                "base_without_eq21": topology["sensitivities"][multiplier][
                    "base_without_eq21_free"
                ]["dimensions"],
                "constraints": [
                    {
                        "id": item["id"],
                        "feasible": item["feasible"],
                        "dimensions": item.get("dimensions"),
                    }
                    for item in topology["sensitivities"][multiplier]["physical_constraint_sets"]
                ],
            }
            for multiplier in MULTIPLIERS
        }
        for topology in topologies
    }


def evaluate_precision(decimal_digits: int, cases: Mapping[str, Any], *, quick: bool) -> dict[str, Any]:
    if decimal_digits not in PRECISIONS:
        raise MechanicsInputError(f"unsupported precision: {decimal_digits}")
    mp.mp.dps = decimal_digits
    arithmetic_eps = +mp.mp.eps
    eps_p = _eval_scalar(cases["calculus"]["eps64"], cases)
    drill_cases = _drill_cases()
    topologies = drill_cases["topology_cases"]
    if quick:
        topologies = [record for record in topologies if record["id"] == "one_square"]
    rules: dict[str, list[dict[str, Any]]] = {}
    for rule in ("primary", "sensitivity"):
        rules[rule] = [
            analyze_topology(topology, cases, decimal_digits, eps_p, rule)
            for topology in topologies
        ]
    primary_categories = _rule_categories(rules["primary"])
    sensitivity_categories = _rule_categories(rules["sensitivity"])
    quadrature_agreement = primary_categories == sensitivity_categories
    if not quadrature_agreement:
        # Preserve both complete rule records; the final terminal becomes
        # UNCLASSIFIED rather than choosing a preferred quadrature.
        pass
    result = {
        "decimal_digits": decimal_digits,
        "mp_prec": mp.mp.prec,
        "mp_eps": BASE.mpf_token(arithmetic_eps),
        "classification_eps64": BASE.mpf_token(eps_p),
        "exact_flat_certificate": _flat_exact_certificate(),
        "exact_flat_runtime_binding": _flat_runtime_binding(cases, eps_p),
        "pointwise_derivation": _pointwise_derivative_record(cases),
        "rules": rules,
        "quadrature_categories_equal": quadrature_agreement,
        "quick": quick,
    }
    if not quick:
        result["local_rules"] = {
            rule: [
                analyze_topology(
                    _local_case_topology(local),
                    cases,
                    decimal_digits,
                    eps_p,
                    rule,
                )
                for local in drill_cases["local_cases"]
            ]
            for rule in ("primary", "sensitivity")
        }
        regular = next(
            item for item in topologies if item["id"] == "regular_2x2"
        )
        result["response"] = {
            rule: {
                "patch": _patch_response_record(regular, cases, rule, eps_p),
                "thickness_locking": _thickness_locking_record(
                    regular, cases, rule, eps_p
                ),
                "curved_refinement": _curved_refinement_record(
                    cases, rule, decimal_digits, eps_p
                ),
            }
            for rule in ("primary", "sensitivity")
        }
        result["covariance"] = {
            rule: _covariance_record(cases, drill_cases, decimal_digits, eps_p, rule)
            for rule in ("primary", "sensitivity")
        }
        result["activity_deletion"] = {
            rule: _activity_deletion_record(cases, drill_cases, decimal_digits, eps_p, rule)
            for rule in ("primary", "sensitivity")
        }
    return result


def _free_for_covariance(
    topology: Mapping[str, Any],
    cases: Mapping[str, Any],
    decimal_digits: int,
    eps_p: mp.mpf,
    rule: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    assembly = assemble_candidate_topology(topology, cases, rule)
    free = BASE.free_partition(assembly, decimal_digits, eps_p, mp.mpf(1))
    return assembly, free


def _projector_residuals(
    base: Mapping[str, Any], candidate: Mapping[str, Any], transform: mp.matrix | None = None
) -> dict[str, list[Any]]:
    result: dict[str, list[Any]] = {}
    for name in ("N", "G", "P", "R_N", "R_G", "RQ", "Z"):
        target = candidate["projectors"][name]
        if transform is not None:
            target = transform.T * target * transform
        result[name] = BASE.mpf_token(
            BASE._equality_residual(base["projectors"][name], target)
        )
    return result


def _scale_topology(topology: Mapping[str, Any], exponent: int) -> dict[str, Any]:
    result = json.loads(json.dumps(topology))
    factor = Decimal(2) ** exponent

    def scaled(value: Any) -> str:
        if not isinstance(value, str):
            raise MechanicsInputError("scale covariance requires decimal-string input")
        result_value = Decimal(value) * factor
        text = format(result_value, "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return "0" if text in ("-0", "") else text

    for node in result["nodes"]:
        node["x"] = [scaled(value) for value in node["x"]]
    for element in result["elements"]:
        if isinstance(element["thickness"], list):
            element["thickness"] = [scaled(value) for value in element["thickness"]]
        else:
            element["thickness"] = scaled(element["thickness"])
    return result


def _numbering_variant(
    topology: Mapping[str, Any], metadata: Mapping[str, Any], name: str
) -> dict[str, Any]:
    result = json.loads(json.dumps(topology))
    if len(result["elements"]) != 1:
        raise MechanicsInputError("numbering covariance requires one retained element")
    source = topology["elements"][0]
    target = result["elements"][0]
    order = metadata[name]["local_corner_order"]
    sign = BASE._mp(metadata[name]["director_sign"], f"{name}.director_sign")
    target["nodes"] = [source["nodes"][index] for index in order]
    target["thickness"] = [source["thickness"][index] for index in order]
    target["director_seeds"] = [
        [mp.nstr(sign * BASE._mp(value, f"{name}.director"), mp.mp.dps) for value in source["director_seeds"][index]]
        for index in order
    ]
    return result


def _covariance_record(
    cases: Mapping[str, Any],
    drill_cases: Mapping[str, Any],
    decimal_digits: int,
    eps_p: mp.mpf,
    rule: str,
) -> dict[str, Any]:
    square = next(item for item in drill_cases["topology_cases"] if item["id"] == "one_square")
    base_assembly, base = _free_for_covariance(
        square, cases, decimal_digits, eps_p, rule
    )
    variants = drill_cases["derived_variants"]
    rotation = mp.matrix(
        [[BASE._mp(value, "covariance.rotation") for value in row] for row in variants["proper_rotation"]]
    )
    rotated_topology = BASE._topology_variant(square, rotation=variants["proper_rotation"])
    _, rotated = _free_for_covariance(rotated_topology, cases, decimal_digits, eps_p, rule)
    q_rotation = BASE._spatial_dof_transform(rotation, len(square["nodes"]))
    shifted_topology = BASE._topology_variant(square, shift=variants["origin_shift"])
    _, shifted = _free_for_covariance(shifted_topology, cases, decimal_digits, eps_p, rule)
    scales: dict[str, Any] = {}
    for exponent in variants["coordinate_scales_pow2"]:
        _, scaled = _free_for_covariance(
            _scale_topology(square, int(exponent)),
            cases,
            decimal_digits,
            eps_p,
            rule,
        )
        scales[str(exponent)] = {
            "dimensions": scaled["dimensions"],
            "residuals": _projector_residuals(base, scaled),
        }
    metadata = variants["warped_numbering_covariance"]
    warped = next(
        item for item in drill_cases["topology_cases"] if item["id"] == metadata["topology_id"]
    )
    _, warped_base = _free_for_covariance(warped, cases, decimal_digits, eps_p, rule)
    numbering: dict[str, Any] = {}
    for name in ("cyclic", "anchored_reversal"):
        _, transformed = _free_for_covariance(
            _numbering_variant(warped, metadata, name),
            cases,
            decimal_digits,
            eps_p,
            rule,
        )
        numbering[name] = {
            "dimensions": transformed["dimensions"],
            "residuals": _projector_residuals(warped_base, transformed),
        }
    tolerance = 4096 * max(1, base_assembly["B_w"].cols) * eps_p
    records = {
        "base_dimensions": base["dimensions"],
        "frame": {
            "dimensions": rotated["dimensions"],
            "residuals": _projector_residuals(base, rotated, q_rotation),
        },
        "origin": {
            "dimensions": shifted["dimensions"],
            "residuals": _projector_residuals(base, shifted),
        },
        "scales": scales,
        "warped_numbering": numbering,
        "tolerance": BASE.mpf_token(tolerance),
    }
    # Residual tokens are retained verbatim; the summary compares them to the
    # frozen tolerance without converting through binary floats.
    return records


def _activity_deletion_record(
    cases: Mapping[str, Any],
    drill_cases: Mapping[str, Any],
    decimal_digits: int,
    eps_p: mp.mpf,
    rule: str,
) -> dict[str, Any]:
    softened = next(
        item for item in drill_cases["topology_cases"] if item["id"] == "softened_invariance"
    )
    neutral = json.loads(json.dumps(softened))
    for element in neutral["elements"]:
        if element.get("state") == "softened":
            element["state"] = "active"
        element["alpha"] = "1"
        element["beta"] = "1"
        element["density"] = "1"
    soft_assembly, soft_free = _free_for_covariance(
        softened, cases, decimal_digits, eps_p, rule
    )
    _, neutral_free = _free_for_covariance(neutral, cases, decimal_digits, eps_p, rule)
    deletion = next(
        item for item in drill_cases["topology_cases"] if item["id"] == "deletion_split"
    )
    restored = json.loads(json.dumps(deletion))
    for element in restored["elements"]:
        if element.get("state") == "deleted":
            element["state"] = "active"
    deletion_assembly, deletion_free = _free_for_covariance(
        deletion, cases, decimal_digits, eps_p, rule
    )
    deletion_pruned = json.loads(json.dumps(deletion))
    deletion_pruned["elements"] = [
        element
        for element in deletion_pruned["elements"]
        if element.get("state", "active") != "deleted"
    ]
    deletion_pruned["id"] = "deletion_split_physically_pruned"
    deletion_pruned_assembly, deletion_pruned_free = _free_for_covariance(
        deletion_pruned, cases, decimal_digits, eps_p, rule
    )
    restored_assembly, restored_free = _free_for_covariance(
        restored, cases, decimal_digits, eps_p, rule
    )
    orphan_topology = next(
        item
        for item in drill_cases["topology_cases"]
        if item["id"] == "deletion_orphans"
    )
    orphan_assembly, orphan_free = _free_for_covariance(
        orphan_topology, cases, decimal_digits, eps_p, rule
    )
    orphan_pruned = json.loads(json.dumps(orphan_topology))
    orphan_pruned["elements"] = [
        element
        for element in orphan_pruned["elements"]
        if element.get("state", "active") != "deleted"
    ]
    orphan_pruned["id"] = "deletion_orphans_physically_pruned"
    orphan_pruned_assembly, orphan_pruned_free = _free_for_covariance(
        orphan_pruned, cases, decimal_digits, eps_p, rule
    )
    orphan_restored = json.loads(json.dumps(orphan_topology))
    for element in orphan_restored["elements"]:
        if element.get("state") == "deleted":
            element["state"] = "active"
    orphan_restored_assembly, orphan_restored_free = _free_for_covariance(
        orphan_restored, cases, decimal_digits, eps_p, rule
    )
    orphan_ids = [
        orphan_assembly["node_ids"][node] for node in orphan_assembly["orphans"]
    ]
    orphan_zero_columns = True
    for node in orphan_assembly["orphans"]:
        for column in range(6 * node, 6 * node + 6):
            orphan_zero_columns = orphan_zero_columns and all(
                orphan_assembly["B_w"][row, column] == 0
                for row in range(orphan_assembly["B_w"].rows)
            )
            orphan_zero_columns = orphan_zero_columns and all(
                orphan_assembly["H_w"][row, column] == 0
                for row in range(orphan_assembly["H_w"].rows)
            )
    tolerance = 4096 * max(1, soft_assembly["B_w"].cols) * eps_p
    return {
        "positive_activity": {
            "softened_dimensions": soft_free["dimensions"],
            "neutral_dimensions": neutral_free["dimensions"],
            "projector_residuals": _projector_residuals(soft_free, neutral_free),
            "tolerance": BASE.mpf_token(tolerance),
            "candidate_elements": soft_assembly["candidate_element_digests"],
        },
        "hard_deletion": {
            "deleted_dimensions": deletion_free["dimensions"],
            "restored_dimensions": restored_free["dimensions"],
            "deleted_element_absent": "e1" not in deletion_assembly["candidate_element_digests"],
            "restored_element_present": "e1" in restored_assembly["candidate_element_digests"],
            "deleted_orphans": [deletion_assembly["node_ids"][node] for node in deletion_assembly["orphans"]],
            "restored_orphans": [restored_assembly["node_ids"][node] for node in restored_assembly["orphans"]],
            "pruned_dimensions": deletion_pruned_free["dimensions"],
            "pruned_inventory_equal": (
                deletion_assembly["candidate_element_digests"]
                == deletion_pruned_assembly["candidate_element_digests"]
            ),
            "pruned_B_equal": BASE.matrix_digest(deletion_assembly["B_w"])
            == BASE.matrix_digest(deletion_pruned_assembly["B_w"]),
            "pruned_H_equal": BASE.matrix_digest(deletion_assembly["H_w"])
            == BASE.matrix_digest(deletion_pruned_assembly["H_w"]),
            "pruned_K_equal": BASE.matrix_digest(deletion_assembly["K_physical"])
            == BASE.matrix_digest(deletion_pruned_assembly["K_physical"]),
            "pruned_M_equal": BASE.matrix_digest(deletion_assembly["M_physical"])
            == BASE.matrix_digest(deletion_pruned_assembly["M_physical"]),
        },
        "orphan_dofs": {
            "orphan_node_ids": orphan_ids,
            "expected_orphan_node_ids": ["z0", "z1", "z2", "z3"],
            "operator_columns_exact_zero": orphan_zero_columns,
            "original_coordinate_count": orphan_assembly["B_w"].cols,
            "restored_coordinate_count": orphan_restored_assembly["B_w"].cols,
            "deleted_dimensions": orphan_free["dimensions"],
            "restored_dimensions": orphan_restored_free["dimensions"],
            "restored_orphan_node_ids": [
                orphan_restored_assembly["node_ids"][node]
                for node in orphan_restored_assembly["orphans"]
            ],
            "deleted_element_absent": all(
                element_id not in orphan_assembly["candidate_element_digests"]
                for element_id in orphan_assembly["deleted_element_ids"]
            ),
            "restored_deleted_elements_present": all(
                element_id in orphan_restored_assembly["candidate_element_digests"]
                for element_id in orphan_assembly["deleted_element_ids"]
            ),
            "pruned_dimensions": orphan_pruned_free["dimensions"],
            "pruned_inventory_equal": (
                orphan_assembly["candidate_element_digests"]
                == orphan_pruned_assembly["candidate_element_digests"]
            ),
            "pruned_B_equal": BASE.matrix_digest(orphan_assembly["B_w"])
            == BASE.matrix_digest(orphan_pruned_assembly["B_w"]),
            "pruned_H_equal": BASE.matrix_digest(orphan_assembly["H_w"])
            == BASE.matrix_digest(orphan_pruned_assembly["H_w"]),
            "pruned_K_equal": BASE.matrix_digest(orphan_assembly["K_physical"])
            == BASE.matrix_digest(orphan_pruned_assembly["K_physical"]),
            "pruned_M_equal": BASE.matrix_digest(orphan_assembly["M_physical"])
            == BASE.matrix_digest(orphan_pruned_assembly["M_physical"]),
        },
    }


def _mpf_from_token(token: Any) -> mp.mpf:
    if (
        not isinstance(token, list)
        or len(token) != 4
        or type(token[0]) is not int
        or type(token[1]) is not str
        or type(token[2]) is not int
        or type(token[3]) is not int
    ):
        raise MechanicsInputError("invalid canonical mpf token")
    sign, mantissa_text, exponent, bitcount = token
    mantissa = int(mantissa_text)
    if sign not in (0, 1) or mantissa < 0 or bitcount < 0:
        raise MechanicsInputError("nonfinite or malformed mpf token")
    value = mp.mpf(mantissa) * mp.power(2, exponent)
    return -value if sign else value


def _gate(status: str, evidence: Any) -> dict[str, Any]:
    if status not in ("PASS", "PROVEN_FAIL", "BORDERLINE", "EXECUTION_ERROR"):
        raise MechanicsInputError(f"unknown gate status: {status}")
    return {"status": status, "evidence": evidence}


def _max_residual_tokens(value: Any) -> mp.mpf:
    tokens: list[mp.mpf] = []
    def visit(item: Any) -> None:
        if isinstance(item, list) and len(item) == 4 and isinstance(item[1], str):
            tokens.append(abs(_mpf_from_token(item)))
        elif isinstance(item, dict):
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
    visit(value)
    return max(tokens, default=mp.mpf(0))


def _aggregate_status(statuses: Sequence[str]) -> str:
    if any(status == "PROVEN_FAIL" for status in statuses):
        return "PROVEN_FAIL"
    if any(status in ("BORDERLINE", "EXECUTION_ERROR") for status in statuses):
        return "BORDERLINE"
    if statuses and all(status == "PASS" for status in statuses):
        return "PASS"
    return "BORDERLINE"


def _rule_signature(record: Mapping[str, Any], rule: str) -> dict[str, Any]:
    def topology_signature(topology: Mapping[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": topology["id"],
            "energy": {
                key: topology["energy"][key]
                for key in (
                    "rigid_pass",
                    "gradient_pass",
                    "hessian_pass",
                    "virtual_work_pass",
                    "K_psd_pass",
                    "M_psd_pass",
                )
            },
            "sensitivities": {},
        }
        for multiplier in MULTIPLIERS:
            sensitivity = topology["sensitivities"][multiplier]
            item: dict[str, Any] = {
                "free": sensitivity["free"]["dimensions"],
                "base_without_eq21": sensitivity["base_without_eq21_free"][
                    "dimensions"
                ],
                "constraints": [
                    {
                        "id": constraint["id"],
                        "kind": constraint["kind"],
                        "qualified": constraint["qualified"],
                        "expected_feasible": constraint["expected_feasible"],
                        "feasible": constraint["feasible"],
                        "dimensions": constraint.get("dimensions"),
                        "beam_shell_work_pass": constraint.get(
                            "beam_shell_virtual_work", {}
                        ).get("pass"),
                    }
                    for constraint in sensitivity["physical_constraint_sets"]
                ],
            }
            if "flat_probes" in sensitivity:
                item["flat"] = {
                    "pure_drill_rank": sensitivity["flat_probes"]["pure_drill_rank"],
                    "common_pass": sensitivity["flat_probes"]["constant_drill"]["pass"],
                    "checker_pass": sensitivity["flat_probes"]["checkerboard"]["pass"],
                    "reduction_pass": sensitivity["exact_g_reduction"]["pass"],
                }
            result["sensitivities"][multiplier] = item
        if "material_scaling" in topology:
            result["material_scaling"] = [
                {
                    "constitutive_id": item["constitutive_id"],
                    "scale": item["scale"],
                    "pass": item["pass"],
                }
                for item in topology["material_scaling"]
            ]
        return result

    signature: dict[str, Any] = {
        "topologies": [topology_signature(item) for item in record["rules"][rule]],
    }
    if not record["quick"]:
        signature["local_cases"] = [
            topology_signature(item) for item in record["local_rules"][rule]
        ]
        response = record["response"][rule]
        signature["response"] = {
            "patch": {
                key: value["pass"] for key, value in response["patch"]["fields"].items()
            },
            "thickness": {
                key: response["thickness_locking"][key]
                for key in ("membrane_t_pass", "bending_t3_pass", "thin_locking_pass")
            },
            "curved": {
                "pass": response["curved_refinement"]["pass"],
                "dimensions": [item["dimensions"] for item in response["curved_refinement"]["records"]],
                "slope_pass": [item["passes_required_order"] for item in response["curved_refinement"]["slopes"]],
            },
        }
        covariance = record["covariance"][rule]
        signature["covariance"] = {
            "base_dimensions": covariance["base_dimensions"],
            "frame_dimensions": covariance["frame"]["dimensions"],
            "origin_dimensions": covariance["origin"]["dimensions"],
            "scale_dimensions": {
                key: value["dimensions"] for key, value in covariance["scales"].items()
            },
            "numbering_dimensions": {
                key: value["dimensions"]
                for key, value in covariance["warped_numbering"].items()
            },
            "residuals_pass": _max_residual_tokens(covariance)
            <= _mpf_from_token(covariance["tolerance"]),
        }
        activity = record["activity_deletion"][rule]
        signature["activity_deletion"] = {
            "positive_dimensions": {
                "softened": activity["positive_activity"]["softened_dimensions"],
                "neutral": activity["positive_activity"]["neutral_dimensions"],
            },
            "positive_dimensions_equal": activity["positive_activity"][
                "softened_dimensions"
            ]
            == activity["positive_activity"]["neutral_dimensions"],
            "positive_residuals_pass": _max_residual_tokens(
                activity["positive_activity"]["projector_residuals"]
            )
            <= _mpf_from_token(activity["positive_activity"]["tolerance"]),
            "hard_deletion": {
                "dimensions": {
                    "deleted": activity["hard_deletion"]["deleted_dimensions"],
                    "restored": activity["hard_deletion"]["restored_dimensions"],
                    "pruned": activity["hard_deletion"]["pruned_dimensions"],
                },
                **{
                    key: activity["hard_deletion"][key]
                    for key in (
                        "deleted_element_absent",
                        "restored_element_present",
                        "pruned_inventory_equal",
                        "pruned_B_equal",
                        "pruned_H_equal",
                        "pruned_K_equal",
                        "pruned_M_equal",
                    )
                },
            },
            "orphan": {
                "dimensions": {
                    "deleted": activity["orphan_dofs"]["deleted_dimensions"],
                    "restored": activity["orphan_dofs"]["restored_dimensions"],
                    "pruned": activity["orphan_dofs"]["pruned_dimensions"],
                },
                **{
                    key: activity["orphan_dofs"][key]
                    for key in (
                        "orphan_node_ids",
                        "expected_orphan_node_ids",
                        "operator_columns_exact_zero",
                        "restored_orphan_node_ids",
                        "deleted_element_absent",
                        "restored_deleted_elements_present",
                        "pruned_inventory_equal",
                        "pruned_B_equal",
                        "pruned_H_equal",
                        "pruned_K_equal",
                        "pruned_M_equal",
                    )
                },
            },
        }
    return signature


def _coverage_records(
    contract: Mapping[str, Any], gates: Mapping[str, Mapping[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    del gates
    required = contract["required_execution_coverage"]
    mapping = contract["coverage_map"]
    if len(required) != 174 or len(mapping) != 174:
        raise MechanicsContractError("execution coverage must contain exactly 174 rows")
    required_keys = [item["coverage_key"] for item in required]
    mapped_keys = [item["coverage_key"] for item in mapping]
    if required_keys != mapped_keys or len(set(required_keys)) != 174:
        raise MechanicsContractError("execution coverage keys are missing, duplicated, or reordered")
    evidence_rows: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    for ordinal, (source, executor) in enumerate(zip(required, mapping, strict=True)):
        source_digest = _sha256_bytes(canonical_json_bytes(source["source"]))
        if source_digest != source["source_record_sha256"]:
            raise MechanicsContractError("execution coverage source digest mismatch")
        if source["coverage_ordinal"] != ordinal:
            raise MechanicsContractError("execution coverage ordinal is not canonical")
        if executor.get("source_record_sha256") != source_digest:
            raise MechanicsContractError("executor does not bind its exact source record")
        if executor["result_pointer"] != f"/scientific_summary/coverage_evidence/{ordinal}":
            raise MechanicsContractError("execution result pointer is not canonical")
        if executor["executor_kind"] != "unresolved_exact_executor":
            raise MechanicsContractError("coverage executor is not exact and fail-closed")
        status = "BORDERLINE"
        evidence = {
            "coverage_key": source["coverage_key"],
            "executor_kind": "unresolved_exact_executor",
            "executor_id": executor["executor_id"],
            "source_record_sha256": source_digest,
            "source_class": source["class"],
            "status": status,
            "reason": "exact per-item Candidate-B executor is not implemented",
            "raw_identity_is_not_execution": True,
        }
        evidence_rows.append(evidence)
        ledger.append(
            {
                "coverage_key": source["coverage_key"],
                "executor_id": executor["executor_id"],
                "status": status,
                "evidence_sha256": _sha256_bytes(canonical_json_bytes(evidence)),
                "result_pointer": executor["result_pointer"],
            }
        )
    return evidence_rows, ledger


def scientific_summary(
    records: Sequence[Mapping[str, Any]],
    cases: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_ids = list(cases["candidate_case_ids"])
    gates = {
        identifier: _gate("BORDERLINE", "required evidence not yet closed")
        for identifier in candidate_ids
    }
    if not records:
        raise MechanicsInputError("scientific summary requires precision records")

    def assign(
        identifier: str,
        passed: bool,
        evidence: Any,
        *,
        certified_failure: bool = False,
    ) -> None:
        if passed:
            status = "PASS"
        elif certified_failure:
            status = "PROVEN_FAIL"
        else:
            status = "BORDERLINE"
        gates[identifier] = _gate(status, evidence)

    pointwise_pass = all(
        all(
            sample["incremental_shear_exact_zero"]
            and sample["accepted_H_D_equal"]
            and sample["compatible_membrane_equal"]
            and sample["literal_eq24_25_base_equal"]
            for sample in record["pointwise_derivation"]["samples"]
        )
        and any(
            sample["eq21_superseded"]
            for sample in record["pointwise_derivation"]["samples"]
        )
        and record["pointwise_derivation"]["full_eq10_derivatives"]
        and not record["pointwise_derivation"]["eq11_used"]
        and record["pointwise_derivation"]["eq21_activation_count"] == 0
        and record["pointwise_derivation"]["eq27_activation_count"] == 0
        and not record["pointwise_derivation"]["eq25_tying_includes_H_D"]
        for record in records
    )
    pointwise_evidence = {
        "all_precision_records": [
            record["pointwise_derivation"] for record in records
        ],
        "formula_mismatch_is_exact_implementation_failure": True,
    }
    for identifier in (
        "candidate_b.derivation.full_hd_eq15_16",
        "candidate_b.identity.eq24_25_literal",
        "candidate_b.identity.eq21_supersession_scope",
        "candidate_b.identity.eq27_unused",
    ):
        assign(
            identifier,
            pointwise_pass,
            pointwise_evidence,
            certified_failure=not pointwise_pass,
        )

    exact_records = [record["exact_flat_certificate"] for record in records]
    exact_expected = all(
        certificate["B"]["rank"] == 17
        and certificate["BH"]["rank"] == 23
        and certificate["pure_drill"]["rank"] == 3
        and certificate["rigid"]["rank"] == 6
        and certificate["rigid_and_gauge"]["rank"] == 7
        and certificate["B_rigid_exact_zero"]
        and certificate["common_B_exact_zero"]
        and certificate["common_H_exact_zero"]
        and certificate["checker_B_nonzero"]["interval"]["lower"]
        != ["0", "1"]
        and certificate["checker_H_nonzero"]["interval"]["lower"]
        != ["0", "1"]
        for certificate in exact_records
    )
    runtime_binding_pass = all(
        record["exact_flat_runtime_binding"]["pass"] for record in records
    )

    material_records = [
        material
        for record in records
        for rule in ("primary", "sensitivity")
        for topology in record["rules"][rule]
        if topology["id"] == "one_square"
        for material in topology["material_scaling"]
    ]
    material_pass = (
        len(material_records) == len(records) * 2 * 6
        and all(item["pass"] for item in material_records)
    )
    assign(
        "candidate_b.constitutive.coefficient_free",
        exact_expected and material_pass,
        {
            "exact_flat_certificate": exact_records,
            "physical_material_records": material_records,
            "expected_records_per_precision_and_rule": 6,
            "added_coefficient_count": 0,
        },
        certified_failure=not exact_expected,
    )

    expected_square = {
        key: cases["flat_square_expected"][key]
        for key in ("rank_B", "N", "G", "P", "R", "R_N", "R_G", "RQ", "Z")
    }
    square_observations: list[dict[str, Any]] = []
    square_numeric = True
    common_numeric = True
    checker_numeric = material_pass
    reduction_numeric = True
    for record in records:
        for rule in ("primary", "sensitivity"):
            square = next(
                item for item in record["rules"][rule] if item["id"] == "one_square"
            )
            for multiplier in MULTIPLIERS:
                sensitivity = square["sensitivities"][multiplier]
                dimensions = sensitivity["free"]["dimensions"]
                probes = sensitivity["flat_probes"]
                reduction = sensitivity["exact_g_reduction"]
                square_observations.append(
                    {
                        "decimal_digits": record["decimal_digits"],
                        "rule": rule,
                        "multiplier": multiplier,
                        "dimensions": dimensions,
                        "pure_drill_rank": probes["pure_drill_rank"],
                        "reduction": {
                            "rank": reduction.get("rank"),
                            "nullity": reduction.get("nullity"),
                            "rigid_rank": reduction.get("rigid_rank"),
                            "map_pass": reduction.get("map_pass"),
                        },
                    }
                )
                square_numeric = (
                    square_numeric
                    and dimensions == expected_square
                    and probes["pure_drill_rank"] == 3
                )
                common_numeric = common_numeric and probes["constant_drill"]["pass"]
                checker_numeric = checker_numeric and probes["checkerboard"]["pass"]
                reduction_numeric = reduction_numeric and bool(reduction.get("pass"))
    assign(
        "candidate_b.square.rank_and_quotient",
        exact_expected and runtime_binding_pass and square_numeric,
        {
            "exact_certificates": exact_records,
            "runtime_bindings": [
                record["exact_flat_runtime_binding"] for record in records
            ],
            "observations": square_observations,
        },
        certified_failure=not exact_expected,
    )
    assign(
        "candidate_b.square.checkerboard_coercivity",
        exact_expected and checker_numeric,
        {
            "exact_certificates": exact_records,
            "physical_material_records": material_records,
        },
        certified_failure=not exact_expected,
    )
    assign(
        "candidate_b.square.common_drill_exact_g",
        exact_expected and common_numeric,
        {"exact_certificates": exact_records, "observations": square_observations},
        certified_failure=not exact_expected,
    )
    assign(
        "candidate_b.square.reported_exact_g_reduction",
        exact_expected and reduction_numeric,
        {"exact_certificates": exact_records, "observations": square_observations},
        certified_failure=not exact_expected,
    )

    energy_records = [
        topology["energy"]
        for record in records
        for rule in ("primary", "sensitivity")
        for group in (
            record["rules"][rule],
            [] if record["quick"] else record["local_rules"][rule],
        )
        for topology in group
    ]
    energy_checks = {
        "candidate_b.rigid.six_modes": all(
            item["rigid_pass"] for item in energy_records
        ),
        "candidate_b.energy.gradient": all(
            item["gradient_pass"] for item in energy_records
        ),
        "candidate_b.energy.hessian": all(
            item["hessian_pass"]
            and item["K_psd_pass"]
            and item["M_psd_pass"]
            for item in energy_records
        ),
        "candidate_b.energy.virtual_work": all(
            item["virtual_work_pass"] for item in energy_records
        ),
    }
    for identifier, passed in energy_checks.items():
        assign(
            identifier,
            bool(energy_records) and passed,
            {"records": energy_records},
        )

    if all(not record["quick"] for record in records):
        patch_fields = {
            "candidate_b.patch.membrane": "membrane_extension_x",
            "candidate_b.patch.bending": "constant_bending_x",
            "candidate_b.patch.transverse_shear": "transverse_shear_xz",
        }
        for identifier, field in patch_fields.items():
            evidence = [
                record["response"][rule]["patch"]["fields"][field]
                for record in records
                for rule in ("primary", "sensitivity")
            ]
            assign(identifier, all(item["pass"] for item in evidence), evidence)
        thickness = [
            record["response"][rule]["thickness_locking"]
            for record in records
            for rule in ("primary", "sensitivity")
        ]
        assign(
            "candidate_b.thickness.membrane_t_bending_t3",
            all(
                item["membrane_t_pass"] and item["bending_t3_pass"]
                for item in thickness
            ),
            thickness,
        )
        assign(
            "candidate_b.locking.thin_sequence",
            all(item["thin_locking_pass"] for item in thickness),
            thickness,
        )
        curved = [
            record["response"][rule]["curved_refinement"]
            for record in records
            for rule in ("primary", "sensitivity")
        ]
        assign(
            "candidate_b.geometry.curved_refinement",
            all(item["pass"] for item in curved),
            curved,
        )

    def topology_observation(
        topology_id: str, *, include_local: bool = False
    ) -> dict[str, Any]:
        dimensions: list[dict[str, int]] = []
        for record in records:
            for rule in ("primary", "sensitivity"):
                groups = [record["rules"][rule]]
                if include_local and not record["quick"]:
                    groups.append(record["local_rules"][rule])
                for group in groups:
                    for topology in group:
                        if topology["id"] != topology_id:
                            continue
                        for multiplier in MULTIPLIERS:
                            dimensions.append(
                                topology["sensitivities"][multiplier]["free"][
                                    "dimensions"
                                ]
                            )
        return {
            "topology_id": topology_id,
            "observations": dimensions,
            "stable": bool(dimensions)
            and all(value == dimensions[0] for value in dimensions),
            "no_positive_mass_quotient_mechanism": bool(dimensions)
            and all(value["Z"] == 0 for value in dimensions),
        }

    topology_gate_map = {
        "candidate_b.geometry.distorted": (
            "distorted_varied_directors",
            "candidate_b_local::distorted_varied_directors",
        ),
        "candidate_b.geometry.noncoplanar_fan": ("noncoplanar_rigid_fan",),
        "candidate_b.topology.connected": ("regular_2x2",),
        "candidate_b.topology.disconnected": ("disconnected",),
        "candidate_b.topology.odd_cycle": ("odd_cycle_prism",),
    }
    for identifier, topology_ids in topology_gate_map.items():
        observations = [
            topology_observation(
                topology_id, include_local=topology_id.startswith("candidate_b_local::")
            )
            for topology_id in topology_ids
        ]
        passed = all(
            item["stable"] and item["no_positive_mass_quotient_mechanism"]
            for item in observations
        )
        assign(identifier, passed, observations)

    warped_observations = [
        topology_observation("warped_varied_directors"),
        topology_observation(
            "candidate_b_local::warped_varied_directors", include_local=True
        ),
    ]
    gates["candidate_b.geometry.warped_interval"] = _gate(
        "BORDERLINE",
        {
            "numerical_observations": warped_observations,
            "outward_interval_closed": False,
            "reason": "generic warped algebraic interval enclosure is not closed",
        },
    )

    constraint_records: list[dict[str, Any]] = []
    for record in records:
        for rule in ("primary", "sensitivity"):
            for topology in record["rules"][rule]:
                for multiplier in MULTIPLIERS:
                    for constraint in topology["sensitivities"][multiplier][
                        "physical_constraint_sets"
                    ]:
                        constraint_records.append(
                            {
                                "decimal_digits": record["decimal_digits"],
                                "rule": rule,
                                "topology_id": topology["id"],
                                "multiplier": multiplier,
                                **constraint,
                            }
                        )

    def constraint_numeric_pass(item: Mapping[str, Any]) -> bool:
        passed = item["feasible"] == item["expected_feasible"]
        if (
            passed
            and item["qualified"]
            and item["feasible"]
            and item.get("dimensions") is not None
        ):
            passed = item["dimensions"]["Z_C"] == 0
        return passed

    for identifier, kinds in (
        ("candidate_b.constraint.support", {"support"}),
        ("candidate_b.constraint.mpc", {"mpc"}),
        ("candidate_b.constraint.affine_feasibility", {"affine_mpc"}),
    ):
        evidence = [item for item in constraint_records if item["kind"] in kinds]
        assign(
            identifier,
            bool(evidence) and all(constraint_numeric_pass(item) for item in evidence),
            evidence,
        )

    beam_records = [
        item for item in constraint_records if item["kind"] == "beam_shell"
    ]
    beam_work_exact = (
        bool(beam_records)
        and all(
            item.get("beam_shell_virtual_work", {}).get("pass", False)
            for item in beam_records
        )
    )
    assign(
        "candidate_b.coupling.beam_shell_work",
        beam_work_exact
        and all(constraint_numeric_pass(item) for item in beam_records),
        beam_records,
        certified_failure=bool(beam_records) and not beam_work_exact,
    )
    shell_records = [
        item for item in constraint_records if item["kind"] == "abstract_shell_shell"
    ]
    shell_unqualified = bool(shell_records) and all(
        not item["qualified"] for item in shell_records
    )
    assign(
        "candidate_b.coupling.shell_shell_unqualified",
        shell_unqualified,
        {"qualified": False, "records": shell_records},
        certified_failure=bool(shell_records) and not shell_unqualified,
    )

    if all(not record["quick"] for record in records):
        covariance_records = [
            record["covariance"][rule]
            for record in records
            for rule in ("primary", "sensitivity")
        ]
        covariance_pass = True
        for covariance in covariance_records:
            base_dimensions = covariance["base_dimensions"]
            dimensions_equal = (
                covariance["frame"]["dimensions"] == base_dimensions
                and covariance["origin"]["dimensions"] == base_dimensions
                and all(
                    item["dimensions"] == base_dimensions
                    for item in covariance["scales"].values()
                )
                and all(
                    item["dimensions"] == base_dimensions
                    for item in covariance["warped_numbering"].values()
                )
            )
            covariance_pass = (
                covariance_pass
                and dimensions_equal
                and _max_residual_tokens(covariance)
                <= _mpf_from_token(covariance["tolerance"])
            )
        for identifier in (
            "candidate_b.covariance.cyclic",
            "candidate_b.covariance.reversal",
            "candidate_b.covariance.frame",
            "candidate_b.covariance.origin",
            "candidate_b.covariance.scale",
        ):
            assign(identifier, covariance_pass, covariance_records)

        activity_records = [
            record["activity_deletion"][rule]
            for record in records
            for rule in ("primary", "sensitivity")
        ]
        positive_pass = all(
            item["positive_activity"]["softened_dimensions"]
            == item["positive_activity"]["neutral_dimensions"]
            and _max_residual_tokens(
                item["positive_activity"]["projector_residuals"]
            )
            <= _mpf_from_token(item["positive_activity"]["tolerance"])
            for item in activity_records
        )
        assign(
            "candidate_b.activity.positive_invariance",
            positive_pass,
            [item["positive_activity"] for item in activity_records],
        )
        hard_keys = (
            "deleted_element_absent",
            "restored_element_present",
            "pruned_inventory_equal",
            "pruned_B_equal",
            "pruned_H_equal",
            "pruned_K_equal",
            "pruned_M_equal",
        )
        hard_pass = all(
            all(item["hard_deletion"][key] for key in hard_keys)
            for item in activity_records
        )
        assign(
            "candidate_b.activity.hard_deletion",
            hard_pass,
            [item["hard_deletion"] for item in activity_records],
            certified_failure=not hard_pass,
        )
        orphan_keys = (
            "operator_columns_exact_zero",
            "deleted_element_absent",
            "restored_deleted_elements_present",
            "pruned_inventory_equal",
            "pruned_B_equal",
            "pruned_H_equal",
            "pruned_K_equal",
            "pruned_M_equal",
        )
        orphan_pass = all(
            item["orphan_dofs"]["orphan_node_ids"]
            == item["orphan_dofs"]["expected_orphan_node_ids"]
            and item["orphan_dofs"]["restored_orphan_node_ids"] == []
            and item["orphan_dofs"]["original_coordinate_count"]
            == item["orphan_dofs"]["restored_coordinate_count"]
            and all(item["orphan_dofs"][key] for key in orphan_keys)
            for item in activity_records
        )
        assign(
            "candidate_b.activity.orphan_dofs",
            orphan_pass,
            [item["orphan_dofs"] for item in activity_records],
            certified_failure=not orphan_pass,
        )

    rule_signature_records = [
        {
            "decimal_digits": record["decimal_digits"],
            "primary": _rule_signature(record, "primary"),
            "sensitivity": _rule_signature(record, "sensitivity"),
        }
        for record in records
    ]
    within_precision_pass = all(
        item["primary"] == item["sensitivity"] for item in rule_signature_records
    )
    reference_primary = rule_signature_records[0]["primary"]
    cross_precision_pass = all(
        item["primary"] == reference_primary for item in rule_signature_records
    )
    quadrature_pass = within_precision_pass and cross_precision_pass
    assign(
        "candidate_b.quadrature.primary_and_sensitivity",
        quadrature_pass,
        {
            "records": rule_signature_records,
            "within_precision_pass": within_precision_pass,
            "cross_precision_pass": cross_precision_pass,
        },
    )

    coverage_evidence, inherited_ledger = _coverage_records(contract, gates)
    gate_statuses = [record["status"] for record in gates.values()]
    coverage_statuses = [record["status"] for record in inherited_ledger]
    proven_failures = [
        identifier
        for identifier, record in gates.items()
        if record["status"] == "PROVEN_FAIL"
    ] + [
        record["coverage_key"]
        for record in inherited_ledger
        if record["status"] == "PROVEN_FAIL"
    ]
    unresolved = [
        identifier
        for identifier, record in gates.items()
        if record["status"] in ("BORDERLINE", "EXECUTION_ERROR")
    ] + [
        record["coverage_key"]
        for record in inherited_ledger
        if record["status"] in ("BORDERLINE", "EXECUTION_ERROR")
    ]
    if proven_failures:
        terminal = "NO_GO_CANDIDATE_B"
    elif unresolved or any(record["quick"] for record in records):
        terminal = "UNCLASSIFIED_CANDIDATE_B"
    elif (
        all(status == "PASS" for status in gate_statuses)
        and all(status == "PASS" for status in coverage_statuses)
    ):
        terminal = "GO_CANDIDATE_B"
    else:
        terminal = "UNCLASSIFIED_CANDIDATE_B"
    return {
        "candidate_terminal": terminal,
        "overall_stage_m_status": "BLOCKED_PRIMARY_SOURCE_UNAVAILABLE",
        "gates": gates,
        "coverage_evidence": coverage_evidence,
        "inherited_execution_ledger": inherited_ledger,
        "blockers": proven_failures,
        "borderline": unresolved,
        "candidate_b_may_resolve_overall_selection": False,
    }
def load_contract(
    cases: Mapping[str, Any], expected_raw_sha256: str
) -> tuple[dict[str, Any], str]:
    path = contract_path()
    if not path.is_file():
        raise MechanicsContractError("registered mechanics contract is absent")
    raw = path.read_bytes()
    actual_raw_sha256 = _sha256_bytes(raw)
    if actual_raw_sha256 != expected_raw_sha256.upper():
        raise MechanicsContractError(
            "registered mechanics contract raw SHA-256 differs from the caller-bound identity"
        )
    actual = _load_json_bytes(raw, str(path))
    expected = extract_contract(cases)
    if canonical_json_bytes(actual) != canonical_json_bytes(expected):
        raise MechanicsContractError(
            "registered mechanics contract differs from static extraction"
        )
    return actual, actual_raw_sha256


def environment_record() -> dict[str, Any]:
    manifest, unsupported_reason = BASE.environment_manifest()
    if manifest is None:
        raise MechanicsInputError(
            f"unsupported runtime for same-manifest proof: {unsupported_reason}"
        )
    digest = _sha256_bytes(BASE.canonical_json_bytes(manifest))
    return {
        "frozen_base_manifest": manifest,
        "frozen_base_manifest_sha256": digest,
        "python_implementation": sys.implementation.name,
        "python_version": list(sys.version_info[:3]),
        "mpmath_version": mp.__version__,
        "mpmath_file": str(Path(mp.__file__).resolve()),
    }


def _identity_record(
    contract: Mapping[str, Any], contract_raw_sha256: str
) -> dict[str, Any]:
    return {
        "candidate_id": CANDIDATE_ID,
        "governing_sha256": GOVERNING_SHA256,
        "plan_sha256": PLAN_SHA256,
        "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "energetic_derivation_sha256": ENERGETIC_DERIVATION_SHA256,
        "constrained_status_sha256": CONSTRAINED_DERIVATION_SHA256,
        "cases_sha256": CASES_SHA256,
        "interval_sha256": INTERVAL_SHA256,
        "oracle_sha256": _sha256_file(Path(__file__).resolve()),
        "contract_sha256": contract_raw_sha256,
        "contract_ledger_sha256": contract["ledger_sha256"],
    }


def _exclusion_record() -> dict[str, bool]:
    return {
        "production_source_edit": False,
        "selector_or_activation": False,
        "penalty_or_stabilization": False,
        "invented_material_coefficient": False,
        "gauge_relabel": False,
        "rank18_claim": False,
        "candidate_a_equation_implementation": False,
    }


def _compose_full_result(
    cases: Mapping[str, Any],
    contract: Mapping[str, Any],
    contract_raw_sha256: str,
    environment: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    *,
    mode: str,
    execution_shards: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if not records:
        raise MechanicsContractError("full-result composition requires precision records")
    digits = [record.get("decimal_digits") for record in records]
    quick_flags = [record.get("quick") for record in records]
    if mode == "quick":
        if digits != [80] or quick_flags != [True] or execution_shards is not None:
            raise MechanicsContractError("quick composition is not the frozen 80-digit record")
        summary_precision = cases["execution"]["quick_summary_decimal_digits"]
    elif mode == "full":
        if (
            digits != list(PRECISIONS)
            or quick_flags != [False, False, False]
            or execution_shards is None
            or len(execution_shards) != 3
        ):
            raise MechanicsContractError("full composition is not the frozen shard merge")
        summary_precision = cases["execution"]["merge_precision_decimal_digits"]
    else:
        raise MechanicsContractError("unknown full-result composition mode")
    if summary_precision != int(records[-1]["decimal_digits"]):
        raise MechanicsContractError("summary precision differs from the final ordered record")
    mp.mp.dps = summary_precision
    summary = scientific_summary(records, cases, contract)
    result = {
        "schema": SCHEMA,
        "status": "complete",
        "mode": mode,
        "identities": _identity_record(contract, contract_raw_sha256),
        "environment": dict(environment),
        "summary_decimal_digits": summary_precision,
        "precision_records": [dict(record) for record in records],
        "scientific_summary": summary,
        "candidate_terminal": summary["candidate_terminal"],
        "overall_stage_m_status": summary["overall_stage_m_status"],
        "exclusions": _exclusion_record(),
    }
    if execution_shards is not None:
        result["execution_shards"] = [dict(record) for record in execution_shards]
    return result


def run_proof(
    cases: Mapping[str, Any],
    contract: Mapping[str, Any],
    contract_raw_sha256: str,
    *,
    quick: bool = False,
) -> dict[str, Any]:
    _validate_cases(cases)
    if not quick:
        raise MechanicsContractError(
            "monolithic full proof is superseded by precision-shard execution"
        )
    environment = environment_record()
    precisions = (80,)
    records = [evaluate_precision(value, cases, quick=quick) for value in precisions]
    return _compose_full_result(
        cases,
        contract,
        contract_raw_sha256,
        environment,
        records,
        mode="quick" if quick else "full",
    )


def run_precision_shard(
    cases: Mapping[str, Any],
    contract: Mapping[str, Any],
    contract_raw_sha256: str,
    decimal_digits: int,
) -> dict[str, Any]:
    _validate_cases(cases)
    if decimal_digits not in cases["execution"]["precision_shards"]:
        raise MechanicsContractError("precision shard is outside the frozen execution set")
    environment = environment_record()
    record = evaluate_precision(decimal_digits, cases, quick=False)
    _validate_precision_record_structure(record, cases, decimal_digits)
    return {
        "schema": SHARD_SCHEMA,
        "status": "partial",
        "mode": "precision_shard",
        "identities": _identity_record(contract, contract_raw_sha256),
        "environment": environment,
        "decimal_digits": decimal_digits,
        "precision_record": record,
        "execution": {
            "full_catalog": True,
            "quadrature_rules": ["primary", "sensitivity"],
            "sensitivity_multipliers": list(MULTIPLIERS),
        },
        "exclusions": _exclusion_record(),
    }


def _is_reparse_point(path: Path) -> bool:
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(attributes & flag)


def _validate_precision_record_structure(
    record: Mapping[str, Any], cases: Mapping[str, Any], decimal_digits: int
) -> None:
    expected_keys = {
        "decimal_digits",
        "mp_prec",
        "mp_eps",
        "classification_eps64",
        "exact_flat_certificate",
        "exact_flat_runtime_binding",
        "pointwise_derivation",
        "rules",
        "quadrature_categories_equal",
        "quick",
        "local_rules",
        "response",
        "covariance",
        "activity_deletion",
    }
    if set(record) != expected_keys:
        raise MechanicsContractError("precision record keyset is incomplete or unexpected")
    if (
        not isinstance(record["decimal_digits"], int)
        or isinstance(record["decimal_digits"], bool)
        or record["decimal_digits"] != decimal_digits
        or record["quick"] is not False
    ):
        raise MechanicsContractError("precision record is mislabeled or abbreviated")
    if (
        not isinstance(record["mp_prec"], int)
        or isinstance(record["mp_prec"], bool)
        or record["mp_prec"] <= 0
        or not isinstance(record["quadrature_categories_equal"], bool)
    ):
        raise MechanicsContractError("precision arithmetic metadata is malformed")
    for token_name in ("mp_eps", "classification_eps64"):
        token = record[token_name]
        if not isinstance(token, list) or len(token) != 4:
            raise MechanicsContractError("precision scalar token is malformed")
    if set(record["exact_flat_certificate"]) != {
        "evaluation_grid",
        "polynomial_unisolvence",
        "B",
        "BH",
        "pure_drill",
        "rigid",
        "rigid_and_gauge",
        "B_rigid_exact_zero",
        "common_B_exact_zero",
        "common_H_exact_zero",
        "checker_B_nonzero",
        "checker_H_nonzero",
        "positive_energy_logic",
        "positive_mass_logic",
    }:
        raise MechanicsContractError("flat exact certificate keyset is incomplete")
    if set(record["exact_flat_runtime_binding"]) != {
        "grid_point_count",
        "B_max_r_eq",
        "H_max_r_eq",
        "r_tol",
        "pass",
    }:
        raise MechanicsContractError("flat runtime-binding keyset is incomplete")
    if set(record["pointwise_derivation"]) != {
        "samples",
        "full_eq10_derivatives",
        "eq11_used",
        "eq21_activation_count",
        "eq25_tying_includes_H_D",
        "eq27_activation_count",
    }:
        raise MechanicsContractError("pointwise derivation keyset is incomplete")
    drill_cases = _drill_cases()
    topology_ids = [item["id"] for item in drill_cases["topology_cases"]]
    local_ids = [
        f"candidate_b_local::{item['id']}" for item in drill_cases["local_cases"]
    ]
    for container_name, expected_ids in (
        ("rules", topology_ids),
        ("local_rules", local_ids),
    ):
        container = record[container_name]
        if set(container) != {"primary", "sensitivity"}:
            raise MechanicsContractError("precision record quadrature rule set is incomplete")
        for rule in ("primary", "sensitivity"):
            values = container[rule]
            if not isinstance(values, list):
                raise MechanicsContractError("precision topology catalog must be a list")
            if [item.get("id") for item in values] != expected_ids:
                raise MechanicsContractError("precision record topology order is incomplete")
            for topology in values:
                if set(topology.get("sensitivities", {})) != set(MULTIPLIERS):
                    raise MechanicsContractError("precision topology multiplier set is incomplete")
    for section in ("response", "covariance", "activity_deletion"):
        if set(record[section]) != {"primary", "sensitivity"}:
            raise MechanicsContractError(f"precision record {section} section is incomplete")
    response_keys = {"patch", "thickness_locking", "curved_refinement"}
    if any(set(record["response"][rule]) != response_keys for rule in ("primary", "sensitivity")):
        raise MechanicsContractError("precision response section is incomplete")
    covariance_keys = {
        "base_dimensions",
        "frame",
        "origin",
        "scales",
        "warped_numbering",
        "tolerance",
    }
    activity_keys = {"positive_activity", "hard_deletion", "orphan_dofs"}
    for rule in ("primary", "sensitivity"):
        if set(record["covariance"][rule]) != covariance_keys:
            raise MechanicsContractError("precision covariance keyset is incomplete")
        if set(record["activity_deletion"][rule]) != activity_keys:
            raise MechanicsContractError("precision activity/deletion keyset is incomplete")


def _load_precision_shards(
    paths: Sequence[str],
    expected_raw_sha256: Sequence[str],
    cases: Mapping[str, Any],
    contract: Mapping[str, Any],
    contract_raw_sha256: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if len(paths) != 3 or len(expected_raw_sha256) != 3:
        raise MechanicsContractError("merge requires exactly three precision shards")
    root = Path(__file__).resolve().parents[2] / cases["execution"][
        "task_owned_directory"
    ]
    if not root.is_dir() or root.is_symlink() or _is_reparse_point(root):
        raise MechanicsContractError("task-owned shard directory is absent or unsafe")
    resolved_root = root.resolve(strict=True)
    allowed_names = set(cases["execution"]["shard_filenames"])
    expected_identities = _identity_record(contract, contract_raw_sha256)
    current_environment = environment_record()
    shards: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    set_names: set[str] = set()
    seen_paths: set[str] = set()
    expected_precisions = list(cases["execution"]["precision_shards"])
    for raw_path, expected_hash, expected_precision in zip(
        paths, expected_raw_sha256, expected_precisions, strict=True
    ):
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            raise MechanicsContractError("shard paths must be absolute")
        if not candidate.exists():
            raise MechanicsContractError("precision shard path is absent")
        if candidate.is_symlink() or _is_reparse_point(candidate):
            raise MechanicsContractError("shard path is a link or reparse point")
        resolved = candidate.resolve(strict=True)
        casefold_path = str(resolved).casefold()
        if casefold_path in seen_paths:
            raise MechanicsContractError("precision shard path is duplicated")
        seen_paths.add(casefold_path)
        if resolved.parent != resolved_root or resolved.name not in allowed_names:
            raise MechanicsContractError("shard path is outside the exact allowlist")
        if not stat.S_ISREG(resolved.lstat().st_mode):
            raise MechanicsContractError("shard path is not a regular file")
        set_names.add(resolved.stem.split("_", 1)[0])
        raw = resolved.read_bytes()
        if (
            not isinstance(expected_hash, str)
            or len(expected_hash) != 64
            or any(character not in "0123456789ABCDEF" for character in expected_hash)
            or _sha256_bytes(raw) != expected_hash
        ):
            raise MechanicsContractError("caller-bound precision shard hash mismatch")
        shard = _load_json_bytes(raw, str(resolved))
        if canonical_json_bytes(shard) != raw:
            raise MechanicsContractError("precision shard bytes are not canonical")
        expected_shard_keys = {
            "schema",
            "status",
            "mode",
            "identities",
            "environment",
            "decimal_digits",
            "precision_record",
            "execution",
            "exclusions",
        }
        if (
            set(shard) != expected_shard_keys
            or shard.get("schema") != SHARD_SCHEMA
            or shard.get("status") != cases["execution"]["shard_status"]
            or shard.get("mode") != "precision_shard"
            or shard.get("identities") != expected_identities
            or shard.get("environment") != current_environment
            or shard.get("exclusions") != _exclusion_record()
            or shard.get("execution")
            != {
                "full_catalog": True,
                "quadrature_rules": ["primary", "sensitivity"],
                "sensitivity_multipliers": list(MULTIPLIERS),
            }
        ):
            raise MechanicsContractError("precision shard identity or environment mismatch")
        precision = shard.get("decimal_digits")
        if type(precision) is not int or precision != expected_precision:
            raise MechanicsContractError("precision shard order is not 80/160/320")
        _validate_precision_record_structure(shard["precision_record"], cases, precision)
        shards.append(shard)
        provenance.append(
            {
                "decimal_digits": precision,
                "raw_sha256": _sha256_bytes(raw),
                "bytes": len(raw),
            }
        )
    if len(set_names) != 1:
        raise MechanicsContractError("merge inputs must belong to one repeat set")
    set_name = next(iter(set_names))
    expected_names = [f"{set_name}_{precision:03d}.json" for precision in PRECISIONS]
    if [Path(path).name for path in paths] != expected_names:
        raise MechanicsContractError("precision shard filenames are not the exact ordered set")
    if [shard["decimal_digits"] for shard in shards] != list(PRECISIONS):
        raise MechanicsContractError("precision shards are missing, duplicated, or reordered")
    return shards, provenance, current_environment


def merge_precision_shards(
    paths: Sequence[str],
    expected_raw_sha256: Sequence[str],
    cases: Mapping[str, Any],
    contract: Mapping[str, Any],
    contract_raw_sha256: str,
) -> dict[str, Any]:
    _validate_cases(cases)
    shards, provenance, environment = _load_precision_shards(
        paths, expected_raw_sha256, cases, contract, contract_raw_sha256
    )
    records = [shard["precision_record"] for shard in shards]
    return _compose_full_result(
        cases,
        contract,
        contract_raw_sha256,
        environment,
        records,
        mode="full",
        execution_shards=provenance,
    )


def proof_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": result["schema"],
        "status": result["status"],
        "mode": result["mode"],
        "identities": result["identities"],
        "candidate_terminal": result["candidate_terminal"],
        "overall_stage_m_status": result["overall_stage_m_status"],
        "scientific_summary": result["scientific_summary"],
        "exclusions": result["exclusions"],
    }


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--emit-contract", action="store_true")
    modes.add_argument("--quick", action="store_true")
    modes.add_argument("--full", action="store_true")
    modes.add_argument("--precision-shard", type=int, choices=PRECISIONS)
    modes.add_argument("--merge-shards", nargs=3, metavar=("SHARD80", "SHARD160", "SHARD320"))
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--contract-sha256")
    parser.add_argument("--shard-sha256", nargs=3, metavar=("SHA80", "SHA160", "SHA320"))
    arguments = parser.parse_args(argv)
    try:
        if arguments.emit_contract:
            if (
                arguments.contract_sha256 is not None
                or arguments.shard_sha256 is not None
                or arguments.summary
            ):
                raise MechanicsContractError(
                    "science and summary arguments are forbidden with --emit-contract"
                )
            value = extract_contract(load_cases())
        else:
            if arguments.contract_sha256 is None:
                raise MechanicsContractError(
                    "--contract-sha256 is required for every science mode"
                )
            if arguments.full:
                raise MechanicsContractError(
                    "monolithic --full is superseded by the frozen precision-shard execution"
                )
            if arguments.summary and not arguments.quick:
                raise MechanicsContractError("--summary is available only with --quick")
            if arguments.merge_shards is None and arguments.shard_sha256 is not None:
                raise MechanicsContractError(
                    "--shard-sha256 is available only with --merge-shards"
                )
            if arguments.merge_shards is not None and arguments.shard_sha256 is None:
                raise MechanicsContractError(
                    "--merge-shards requires three caller-bound --shard-sha256 values"
                )
            cases = load_cases()
            contract, contract_raw_sha256 = load_contract(
                cases, arguments.contract_sha256
            )
            _load_science_dependencies()
            if arguments.quick:
                value = run_proof(
                    cases,
                    contract,
                    contract_raw_sha256,
                    quick=True,
                )
                if arguments.summary:
                    value = proof_summary(value)
            elif arguments.precision_shard is not None:
                value = run_precision_shard(
                    cases,
                    contract,
                    contract_raw_sha256,
                    arguments.precision_shard,
                )
            else:
                value = merge_precision_shards(
                    arguments.merge_shards,
                    arguments.shard_sha256,
                    cases,
                    contract,
                    contract_raw_sha256,
                )
        sys.stdout.buffer.write(canonical_json_bytes(value))
        return 0
    except MechanicsContractError as error:
        failure = {
            "schema": SCHEMA,
            "status": "blocked",
            "terminal": "BLOCKED_CONTRACT_VIOLATION",
            "error_type": type(error).__name__,
            "message": str(error),
        }
        sys.stdout.buffer.write(canonical_json_bytes(failure))
        return 2
    except MechanicsInputError as error:
        failure = {
            "schema": SCHEMA,
            "status": "blocked",
            "terminal": "BLOCKED_INPUT_IDENTITY",
            "error_type": type(error).__name__,
            "message": str(error),
        }
        sys.stdout.buffer.write(canonical_json_bytes(failure))
        return 2
    except Exception as error:
        failure = {
            "schema": SCHEMA,
            "status": "blocked",
            "terminal": "UNCLASSIFIED_CANDIDATE_B",
            "candidate_terminal": "UNCLASSIFIED_CANDIDATE_B",
            "overall_stage_m_status": "BLOCKED_PRIMARY_SOURCE_UNAVAILABLE",
            "error_type": type(error).__name__,
            "message": str(error),
        }
        sys.stdout.buffer.write(canonical_json_bytes(failure))
        return 3


if __name__ == "__main__":
    raise SystemExit(_main())

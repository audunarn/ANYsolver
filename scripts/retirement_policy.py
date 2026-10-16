"""Administrative retirement policy for the experimental stiffened-shell programme.

On 16 October 2026 the whole experimental stiffened-shell / GE beam-shell
programme (including BL5 and F03) was administratively retired from default
pytest collection and portable CI selection.  The programme source and tests
are preserved in place; this module is the single selection policy shared by
``tests/conftest.py`` (default pytest) and ``scripts/run_portable_ci.py``
(portable CI), so the two cannot drift.

This file is deliberately stdlib-only and never imports programme or product
source.  Setting the opt-in environment variable restores ordinary selection
of the retired paths for future explicit use only; it does not renew any
frozen execution authority, scientific acceptance or qualification claim.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts" / "retired_programme_manifest.json"
SCHEMA = "anysolver.retired-programme-tests.v1"
OPT_IN_ENV = "ANYSOLVER_RUN_RETIRED_PROGRAMME_TESTS"

_MANIFEST: dict | None = None


def load_manifest() -> dict:
    """Return the validated retirement manifest (cached per process)."""

    global _MANIFEST
    if _MANIFEST is None:
        record = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if record.get("schema") != SCHEMA:
            raise RuntimeError("invalid retired-programme manifest schema")
        paths = [path for group in record["groups"] for path in group["paths"]]
        if len(paths) != len(set(paths)):
            raise RuntimeError("retired-programme manifest has duplicate paths")
        nodes = [node["id"] for node in record["nodes"]]
        if len(nodes) != len(set(nodes)):
            raise RuntimeError("retired-programme manifest has duplicate nodes")
        for node in nodes:
            if node.partition("::")[0] in set(paths):
                raise RuntimeError(
                    "retired node belongs to a fully retired module"
                )
        _MANIFEST = record
    return _MANIFEST


def retired_module_paths() -> frozenset[str]:
    """Return the exact repo-relative posix paths of retired test modules."""

    return frozenset(
        path for group in load_manifest()["groups"] for path in group["paths"]
    )


def retired_node_ids() -> frozenset[str]:
    """Return exact retired node IDs inside otherwise active modules."""

    return frozenset(node["id"] for node in load_manifest()["nodes"])


def opt_in_enabled() -> bool:
    """Return whether explicit future-use opt-in is requested."""

    return os.environ.get(OPT_IN_ENV) == "1"


def relative_path(path) -> str | None:
    """Normalize a filesystem path to a repo-relative posix path, or None."""

    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except (ValueError, OSError):
        return None


def is_retired_module(relative: str) -> bool:
    return relative in retired_module_paths()


def is_retired_node(node_id: str) -> bool:
    """Return whether a collected node belongs to the retired programme.

    Exact retired nodes, their parametrized instances and class-scoped
    descendants are retired; a longer node id that merely shares a prefix
    (``test_x`` versus ``test_x2``) is not.  A bare module path is retired
    when the module itself is retired.
    """

    for retired in retired_node_ids():
        if node_id == retired or node_id.startswith(
            (retired + "[", retired + "::")
        ):
            return True
    module = node_id.partition("::")[0]
    return module in retired_module_paths()


def is_retired_collected_node(path, node_id: str) -> bool:
    """Use physical file identity even when pytest changes its root directory."""

    relative = relative_path(path)
    if relative is None:
        return False
    _, separator, suffix = node_id.partition("::")
    return is_retired_node(relative + (separator + suffix if separator else ""))


def retired_explicit_selectors(args, invocation_dir) -> tuple[str, ...]:
    """Return explicit invocation selectors that name retired modules or nodes.

    *args* are pytest positional selectors (files, directories, node IDs)
    and *invocation_dir* the ORIGINAL process invocation directory, because
    conftest normalization may have changed the working directory before
    hooks run. Refuse explicitly selected retired nodes before import too;
    directory discovery of mixed modules keeps their shared sibling coverage.
    """

    refused = []
    for arg in args:
        if not isinstance(arg, str) or not arg:
            continue
        file_part, separator, suffix = arg.partition("::")
        candidate = Path(file_part)
        if not candidate.is_absolute():
            candidate = Path(invocation_dir) / candidate
        relative = relative_path(candidate)
        if relative is not None and is_retired_node(
            relative + (separator + suffix if separator else "")
        ):
            refused.append(arg)
    return tuple(refused)


def split_selection(modules) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Split an ordered selection into (active, retired) module paths."""

    retired = retired_module_paths()
    active = tuple(module for module in modules if module not in retired)
    dropped = tuple(module for module in modules if module in retired)
    return active, dropped


def retired_nodes_in_modules(modules) -> tuple[str, ...]:
    """Return retired node IDs whose modules are inside *modules*."""

    owned = set(modules)
    return tuple(
        sorted(
            node for node in retired_node_ids() if node.partition("::")[0] in owned
        )
    )


def retirement_report() -> dict:
    """Return a compact status summary for logging and admin tests."""

    record = load_manifest()
    return {
        "policy": record["policy"],
        "opt_in_env": record["opt_in_env"],
        "retired_module_count": sum(
            len(group["paths"]) for group in record["groups"]
        ),
        "retired_node_count": len(record["nodes"]),
        "groups": {
            group["id"]: len(group["paths"]) for group in record["groups"]
        },
    }

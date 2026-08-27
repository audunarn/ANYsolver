"""Public-boundary checks for qualified S3 default activation."""

from __future__ import annotations

import pytest

import anysolver
from scripts import run_portable_ci
from anysolver import (
    DEFAULT_S3_FORMULATION,
    LegacyS3MigrationWarning,
    QUALIFIED_S3_FORMULATION_ID,
    QualifiedE4PLS3ShellElement,
    ShellElement,
    create_element,
    create_shell_element,
    shell_element_from_dict,
    shell_formulation_diagnostics,
)


_NORMAL = (0.0, 0.0, 1.0)


def _qualified(factory_name: str = "shell") -> ShellElement:
    return create_element(
        factory_name,
        1,
        [1, 2, 3],
        "steel",
        thickness=0.01,
        reference_normal=_NORMAL,
    )


def test_current_candidate_declares_the_coordinated_release_and_s3_default() -> None:
    assert anysolver.__version__ == "0.4.0"
    assert DEFAULT_S3_FORMULATION == "e4-pl-s3"


@pytest.mark.parametrize("alias", ("shell", "s3", "tri3", "tria3", "t3", "shell3"))
def test_three_node_public_factory_aliases_select_the_exact_qualified_class(alias: str) -> None:
    element = _qualified(alias)

    assert type(element) is QualifiedE4PLS3ShellElement
    assert element.formulation_id == QUALIFIED_S3_FORMULATION_ID
    assert tuple(element.reference_normal) == _NORMAL


def test_direct_shell_element_and_explicit_legacy_s3_remain_legacy() -> None:
    direct = ShellElement(1, [1, 2, 3], "steel", thickness=0.01)
    rollback = create_shell_element(
        2,
        [1, 2, 3],
        "steel",
        formulation="legacy-s3",
        thickness=0.01,
    )

    assert type(direct) is ShellElement
    assert type(rollback) is ShellElement
    assert not hasattr(direct, "formulation_id")
    assert not hasattr(rollback, "formulation_id")


def test_qualified_s3_requires_physical_owner_normal_and_e4_pl_remains_q4_only() -> None:
    with pytest.raises(ValueError, match="authoritative reference_normal"):
        create_shell_element(1, [1, 2, 3], "steel", thickness=0.01)
    with pytest.raises(ValueError, match="only for four-node"):
        create_shell_element(
            1,
            [1, 2, 3],
            "steel",
            formulation="e4-pl",
            thickness=0.01,
        )


def test_missing_identity_historical_tri3_still_migrates_to_explicit_legacy() -> None:
    payload = {
        "element_id": 7,
        "node_ids": [1, 2, 3],
        "material_name": "steel",
        "thickness": 0.01,
    }

    with pytest.warns(LegacyS3MigrationWarning, match="legacy-s3"):
        restored = shell_element_from_dict(payload)

    assert type(restored) is ShellElement
    assert not hasattr(restored, "formulation_id")


def test_diagnostics_identify_both_qualified_production_defaults() -> None:
    s3 = shell_formulation_diagnostics(node_count=3)
    q4 = shell_formulation_diagnostics(node_count=4)

    assert s3["production_default"] is True
    assert s3["selected_formulation"] == "e4-pl-s3"
    assert s3["topology_policy"] == "QUALIFIED_E4_PL_S3_DEFAULT"
    assert q4["production_default"] is True
    assert q4["selected_formulation"] == "e4-pl"


def test_opt_in_smoke_protocol_remains_immutable_historical_evidence() -> None:
    historical = "tests/test_e4_pl_s3_mixed_mesh_qualification_runner.py"

    assert historical in run_portable_ci.POST_CLOSEOUT_HISTORICAL_MODULES
    assert historical not in run_portable_ci.merge_test_modules()

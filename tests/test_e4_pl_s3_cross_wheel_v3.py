"""Exact-wheel S3 default and provenance gate for formal qualification v3."""

from __future__ import annotations

from importlib import metadata
import os
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    os.environ.get("ANYSOLVER_S3_V3_CROSS_WHEEL") != "1",
    reason="runs only in the hash-bound isolated-wheel qualification target",
)


EXPECTED_DISTRIBUTIONS = {
    "ANYsolver": "0.4.0",
    "ANYfem": "0.4.0",
    "ANYmesher": "0.3.2",
    "ANYstructure": "6.3.1",
    "ANYfileio": "0.2.1",
    "ANYmaterial": "0.1.1",
    "ANYgeometry": "0.4.1",
}


def test_exact_wheels_import_and_route_qualified_s3_with_provenance() -> None:
    import anysolver
    from anysolver.e4_pl_s3_element import (
        FORMULATION_ID,
        QualifiedE4PLS3ShellElement,
    )
    from anysolver.elements import (
        DEFAULT_S3_FORMULATION,
        create_shell_element,
        shell_formulation_diagnostics,
    )

    target = Path(os.environ["ANYSOLVER_S3_V3_TARGET"]).resolve(strict=True)
    assert Path(str(anysolver.__file__)).resolve().is_relative_to(target)
    assert anysolver.__version__ == EXPECTED_DISTRIBUTIONS["ANYsolver"]
    for distribution_name, version in EXPECTED_DISTRIBUTIONS.items():
        distribution = metadata.distribution(distribution_name)
        assert distribution.version == version
        assert Path(distribution.locate_file("")).resolve().is_relative_to(target)
    assert DEFAULT_S3_FORMULATION == "e4-pl-s3"
    element = create_shell_element(1, [1, 2, 3], "qualified")
    assert type(element) is QualifiedE4PLS3ShellElement
    assert element.formulation_id == FORMULATION_ID
    diagnostic = shell_formulation_diagnostics(node_count=3)
    assert diagnostic["selected_formulation"] == "e4-pl-s3"
    assert diagnostic["topology_policy"] == "QUALIFIED_E4_PL_S3_DEFAULT"
    assert diagnostic["production_default"] is True

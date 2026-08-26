from __future__ import annotations

import copy
import pickle
from typing import Any

import pytest

import anysolver.matrix_assembly as matrix_assembly_module
from anysolver.e4_pl_element import QualifiedE4PLShellElement
from anysolver.fe_core import FEModel, FEMesh
from anysolver.matrix_assembly import AssemblyError


def _qualified_q4_model() -> tuple[FEModel, QualifiedE4PLShellElement]:
    model = FEModel("trusted-loop-authority")
    model.add_material("steel", 210.0e9, 0.3)
    for node_id, coordinate in enumerate(
        (
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
        ),
        start=1,
    ):
        model.add_node(node_id, *coordinate)
    element = QualifiedE4PLShellElement(
        1,
        (1, 2, 3, 4),
        "steel",
        thickness=0.05,
    )
    model.add_element(1, element)
    return model, element


def test_qualified_direct_state_epoch_is_monotonic_fixed_and_copyable() -> None:
    mesh = FEMesh()
    token = mesh._qualified_direct_state_token
    assert isinstance(token, list)
    assert token == [0]

    mesh.add_node(1, 0.0, 0.0, 0.0)
    current = token[0]
    assert current > 0

    with pytest.raises(ValueError, match="only advance by one"):
        token[0] = current - 1
    with pytest.raises(ValueError, match="only advance by one"):
        token[0] = current + 2
    with pytest.raises(TypeError, match="fixed length"):
        token.append(current + 1)
    assert token == [current]

    token[0] = current + 1
    assert token == [current + 1]

    copied = copy.deepcopy(token)
    restored = pickle.loads(pickle.dumps(token))
    assert copied == token and copied is not token
    assert restored == token and restored is not token
    copied[0] = copied[0] + 1
    restored[0] = restored[0] + 1


def test_all_qualified_lease_exposes_constant_time_aba_safe_check() -> None:
    model, element = _qualified_q4_model()
    lease = matrix_assembly_module._CAPTURE_QUALIFIED_ASSEMBLY_RUNTIME_LEASE(
        model,
        context="trusted-loop test",
    )
    trusted = vars(lease).get("_qualified_trusted_require")
    assert callable(trusted)

    for _ in range(1_000):
        trusted(model, context="trusted-loop repeat")

    original = element.thickness
    element.thickness = original * 2.0
    element.thickness = original
    with pytest.raises(AssemblyError, match="qualified shell authority"):
        trusted(model, context="trusted-loop element ABA")


def test_trusted_check_rejects_module_aba_and_mixed_model_has_no_fast_path() -> None:
    model, _element = _qualified_q4_model()
    lease = matrix_assembly_module._CAPTURE_QUALIFIED_ASSEMBLY_RUNTIME_LEASE(
        model,
        context="trusted-loop module test",
    )
    trusted = vars(lease).get("_qualified_trusted_require")
    assert callable(trusted)
    original = matrix_assembly_module._assemble_element_matrix_under_lease

    def replacement(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("replacement must never run")

    setattr(
        matrix_assembly_module,
        "_assemble_element_matrix_under_lease",
        replacement,
    )
    setattr(
        matrix_assembly_module,
        "_assemble_element_matrix_under_lease",
        original,
    )
    with pytest.raises(AssemblyError, match="qualified shell authority"):
        trusted(model, context="trusted-loop module ABA")

    class GenericElement:
        pass

    mixed, _mixed_q4 = _qualified_q4_model()
    mixed.add_element(2, GenericElement())
    mixed_lease = (
        matrix_assembly_module._CAPTURE_QUALIFIED_ASSEMBLY_RUNTIME_LEASE(
            mixed,
            context="mixed-model test",
        )
    )
    assert vars(mixed_lease).get("_qualified_trusted_require") is None

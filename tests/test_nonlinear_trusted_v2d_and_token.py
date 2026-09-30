"""Constant-time Newton-loop guards for owned S3 V2D elements and tokens.

The trusted path must be result-neutral and must keep failing closed for
every supported mutation surface that the complete lifecycle scan observes.
"""

from __future__ import annotations

import numpy as np
import pytest

import anysolver.current_state_tangent as current_state_tangent
import anysolver.e4_pl_s3_v2d_element as v2d_module
import anysolver.nonlinear_static as nonlinear_static_module
from anysolver import elements as elements_module
from anysolver import plasticity, vectorized_nonlinear
from anysolver.boundary import BoundaryCondition, LoadCase
from anysolver.control import CancellationToken
from anysolver.e4_pl_element import QualifiedE4PLShellElement
from anysolver.e4_pl_s3_v2d_element import NativeParityE4PLS3V2DShellElement
from anysolver.element_capabilities import ElementCapabilityError
from anysolver.elements import create_shell_element
from anysolver.fe_core import FEModel
from anysolver.jit_compiler import JIT_ENABLED
from anysolver.matrix_assembly import AssemblyError
from anysolver.nonlinear_static import solve_static_nonlinear


NEWTON_LOOP_CONTEXTS = (
    "nonlinear static force tangent assembly",
    "nonlinear static force external load",
    "nonlinear static force iteration cancellation",
    "nonlinear static step external load",
)


def _mixed_model() -> tuple[FEModel, LoadCase]:
    """One qualified Q4 beside one exact S3 V2D triangle."""

    model = FEModel("mixed-q4-v2d")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    for node_id, coordinate in enumerate(
        (
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (2.0, 0.5, 0.0),
        ),
        start=1,
    ):
        model.add_node(node_id, *coordinate)
    quad = create_shell_element(
        1, (1, 2, 3, 4), "steel", formulation="e4-pl", thickness=0.01
    )
    triangle = create_shell_element(
        2,
        (2, 5, 3),
        "steel",
        formulation="e4-pl-s3-v2d",
        thickness=0.01,
        reference_normal=(0.0, 0.0, 1.0),
    )
    assert type(quad) is QualifiedE4PLShellElement
    assert type(triangle) is NativeParityE4PLS3V2DShellElement
    model.add_element(1, quad)
    model.add_element(2, triangle)
    fixed = {"ux": 0.0, "uy": 0.0, "uz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}
    model.add_boundary_condition(BoundaryCondition("fixed", [1, 4], fixed))
    load = LoadCase("tip")
    load.add_nodal_load(5, [0.0, 0.0, 2.0e3, 0.0, 0.0, 0.0])
    return model, load


def _two_v2d_model() -> tuple[FEModel, LoadCase]:
    """One qualified Q4 beside two exact S3 V2D triangles."""

    model = FEModel("mixed-q4-two-v2d")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    for node_id, coordinate in enumerate(
        (
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (2.0, 0.5, 0.0),
            (2.0, 1.5, 0.0),
        ),
        start=1,
    ):
        model.add_node(node_id, *coordinate)
    model.add_element(
        1,
        create_shell_element(
            1, (1, 2, 3, 4), "steel", formulation="e4-pl", thickness=0.01
        ),
    )
    for element_id, nodes in ((2, (2, 5, 3)), (3, (3, 5, 6))):
        model.add_element(
            element_id,
            create_shell_element(
                element_id,
                nodes,
                "steel",
                formulation="e4-pl-s3-v2d",
                thickness=0.01,
                reference_normal=(0.0, 0.0, 1.0),
            ),
        )
    fixed = {"ux": 0.0, "uy": 0.0, "uz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}
    model.add_boundary_condition(BoundaryCondition("fixed", [1, 4], fixed))
    load = LoadCase("tip")
    load.add_nodal_load(6, [0.0, 0.0, 2.0e2, 0.0, 0.0, 0.0])
    return model, load


def _solve(model: FEModel, load: LoadCase, **options: object):
    return solve_static_nonlinear(
        model, load, max_load_factor=1.0, num_steps=2, num_layers=5, **options
    )


def _count_complete_scans(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    original = nonlinear_static_module._EXACT_QUALIFIED_LIFECYCLE_GUARD
    contexts: list[str] = []

    def counted_guard(observed_model: object, *, context: str) -> object:
        contexts.append(context)
        return original(observed_model, context=context)

    monkeypatch.setattr(
        nonlinear_static_module,
        "_EXACT_QUALIFIED_LIFECYCLE_GUARD",
        counted_guard,
    )
    return contexts


def _v2d_element(model: FEModel) -> NativeParityE4PLS3V2DShellElement:
    return next(
        element
        for element in model.mesh.elements.values()
        if type(element) is NativeParityE4PLS3V2DShellElement
    )


def test_mixed_q4_v2d_newton_loop_uses_trusted_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contexts = _count_complete_scans(monkeypatch)
    result = _solve(*_mixed_model())

    assert result.status == "completed"
    assert "solve_static_nonlinear preflight" in contexts
    assert "nonlinear static constraint postcheck" in contexts
    for context in NEWTON_LOOP_CONTEXTS:
        assert context not in contexts


def test_trusted_v2d_path_is_bitwise_result_neutral(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trusted = _solve(*_mixed_model())
    monkeypatch.setattr(
        nonlinear_static_module,
        "_CAPTURE_QUALIFIED_V2D_TRUSTED_AUTHORITY",
        lambda *_args, **_kwargs: None,
    )
    contexts = _count_complete_scans(monkeypatch)
    complete = _solve(*_mixed_model())

    assert "nonlinear static force tangent assembly" in contexts
    assert trusted.status == complete.status == "completed"
    assert np.asarray(trusted.displacements).tobytes() == np.asarray(
        complete.displacements
    ).tobytes()
    assert trusted.load_factor == complete.load_factor
    assert len(trusted.steps) == len(complete.steps)


def test_solver_cancellation_token_keeps_the_trusted_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contexts = _count_complete_scans(monkeypatch)
    result = _solve(*_mixed_model(), cancellation_token=CancellationToken())

    assert result.status == "completed"
    assert "nonlinear static force iteration cancellation" not in contexts
    assert "nonlinear static force increment cancellation" not in contexts


class _ForeignToken:
    def raise_if_cancelled(self, stage: str = "") -> None:
        del stage


class _SubclassedToken(CancellationToken):
    pass


def _token_with_instance_override() -> CancellationToken:
    token = CancellationToken()
    token.raise_if_cancelled = lambda stage="": None  # type: ignore[method-assign]
    return token


def _token_with_event_override() -> CancellationToken:
    token = CancellationToken()
    token._event.is_set = lambda: False  # type: ignore[method-assign]
    return token


class _HostileFlag:
    def __bool__(self) -> bool:
        return False


def _token_with_hostile_flag() -> CancellationToken:
    token = CancellationToken()
    token._event._flag = _HostileFlag()  # type: ignore[assignment]
    return token


@pytest.mark.parametrize(
    "make_token",
    (
        _ForeignToken,
        _SubclassedToken,
        _token_with_instance_override,
        _token_with_event_override,
        _token_with_hostile_flag,
    ),
    ids=(
        "foreign",
        "subclass",
        "instance-override",
        "event-override",
        "hostile-flag",
    ),
)
def test_untrusted_tokens_keep_the_complete_scan(
    monkeypatch: pytest.MonkeyPatch,
    make_token: object,
) -> None:
    token = make_token()  # type: ignore[operator]
    assert not nonlinear_static_module._is_known_cancellation_checkpoint(token)
    contexts = _count_complete_scans(monkeypatch)
    _solve(*_mixed_model(), cancellation_token=token)

    assert "nonlinear static force iteration cancellation" in contexts


def test_modified_token_class_keeps_the_complete_scan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = CancellationToken()
    monkeypatch.setattr(
        CancellationToken, "raise_if_cancelled", lambda self, stage="": None
    )
    assert not nonlinear_static_module._is_known_cancellation_checkpoint(token)
    # Without a token the checkpoint runs no token code at all.
    assert nonlinear_static_module._is_known_cancellation_checkpoint(None)


def test_replaced_checkpoint_keeps_the_complete_scan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = nonlinear_static_module.cancellation_safe_point
    monkeypatch.setattr(
        nonlinear_static_module,
        "cancellation_safe_point",
        lambda token, stage="": original(token, stage),
    )
    assert not nonlinear_static_module._is_known_cancellation_checkpoint(None)
    contexts = _count_complete_scans(monkeypatch)
    _solve(*_mixed_model())

    assert "nonlinear static force iteration cancellation" in contexts


def test_v2d_instance_writes_advance_the_owning_mesh_epoch() -> None:
    model, _load = _mixed_model()
    element = _v2d_element(model)
    token = model.mesh._qualified_direct_state_token
    start = int(token[0])

    element.thickness = element.thickness
    assert int(token[0]) == start + 1
    element.material_name = element.material_name
    assert int(token[0]) == start + 2
    element.extra_marker = 1
    assert int(token[0]) == start + 3
    del element.extra_marker
    assert int(token[0]) == start + 4

    # Data-only resets of generic derived caches are not validated facts.
    element._stiffness_matrix = None
    element._mass_matrix = np.zeros((18, 18))
    assert int(token[0]) == start + 4
    # A callable written under a cache name is not data-only.
    element._nl_cache = lambda: None
    assert int(token[0]) == start + 5


def test_v2d_capture_rejects_formulation_and_class_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model, _load = _mixed_model()
    items = tuple(model.mesh.elements.items())
    require = current_state_tangent._capture_qualified_v2d_trusted_authority(
        items, context="test"
    )
    assert require is not None
    require(context="clean")

    # A replaced module helper is formulation-level authority.
    original_helper = v2d_module._advance_bound_state_tokens
    monkeypatch.setattr(
        v2d_module,
        "_advance_bound_state_tokens",
        lambda *_args, **_kwargs: None,
    )
    with pytest.raises(ElementCapabilityError):
        require(context="replaced helper")
    monkeypatch.setattr(v2d_module, "_advance_bound_state_tokens", original_helper)

    # Swapping a protected hook installs a raising stub; restoring it still
    # leaves the class epoch changed for this capture.
    fresh = current_state_tangent._capture_qualified_v2d_trusted_authority(
        items, context="test"
    )
    assert fresh is not None
    original_hook = NativeParityE4PLS3V2DShellElement.__dict__["__setattr__"]
    NativeParityE4PLS3V2DShellElement.__setattr__ = object.__setattr__
    try:
        with pytest.raises(ValueError, match="class authority was replaced"):
            _v2d_element(model).extra_marker = 1
    finally:
        NativeParityE4PLS3V2DShellElement.__setattr__ = original_hook
    assert NativeParityE4PLS3V2DShellElement.__dict__["__setattr__"] is original_hook
    with pytest.raises(ElementCapabilityError, match="class authority changed"):
        fresh(context="restored hook")
    assert current_state_tangent._capture_qualified_v2d_trusted_authority(
        items, context="test"
    ) is not None


def test_v2d_capture_requires_immutable_instance_values() -> None:
    model, _load = _mixed_model()
    element = _v2d_element(model)
    object.__setattr__(element, "writable_marker", np.zeros(3))

    assert current_state_tangent._capture_qualified_v2d_trusted_authority(
        tuple(model.mesh.elements.items()), context="test"
    ) is None


def test_v2d_capture_declines_an_inadmissible_element() -> None:
    model, _load = _mixed_model()
    element = _v2d_element(model)
    # A shadow of class authority fails the exact per-instance validation.
    object.__setattr__(element, "formulation_id", element.formulation_id)

    assert current_state_tangent._capture_qualified_v2d_trusted_authority(
        tuple(model.mesh.elements.items()), context="test"
    ) is None


def test_v2d_write_during_solve_fails_closed() -> None:
    model, load = _mixed_model()
    element = _v2d_element(model)
    calls: list[int] = []

    def mutate(_message: str) -> None:
        calls.append(1)
        if len(calls) == 1:
            element.thickness = element.thickness

    with pytest.raises(AssemblyError, match="qualified shell authority"):
        _solve(model, load, status_callback=mutate)
    assert calls == [1]


@pytest.mark.skipif(not JIT_ENABLED, reason="Numba is not active")
@pytest.mark.parametrize(
    ("module", "name"),
    (
        (plasticity, "_jit_plane_stress_return_map"),
        (plasticity, "_jit_flow_stress"),
        (elements_module, "_jit_integrate_nonlinear_response"),
        (elements_module, "_jit_compute_4node_shape_functions"),
        (vectorized_nonlinear, "_jit_batch_integrate_nonlinear_response"),
    ),
)
def test_hot_nonlinear_kernels_use_the_numba_disk_cache(
    module: object, name: str
) -> None:
    dispatcher = getattr(module, name)
    assert type(dispatcher._cache).__name__ != "NullCache"


class _V2DSubclass(NativeParityE4PLS3V2DShellElement):
    pass


def _override_callable(element: NativeParityE4PLS3V2DShellElement, _model: FEModel) -> None:
    element.compute_stiffness_matrix = lambda *_a, **_k: np.zeros((18, 18))  # type: ignore[method-assign]


def _write_thickness(element: NativeParityE4PLS3V2DShellElement, _model: FEModel) -> None:
    element.thickness = 0.02


def _swap_class(element: NativeParityE4PLS3V2DShellElement, _model: FEModel) -> None:
    element.__class__ = _V2DSubclass


def _replace_in_mapping(element: NativeParityE4PLS3V2DShellElement, model: FEModel) -> None:
    model.mesh.elements[3] = element


@pytest.mark.parametrize(
    "mutate",
    (_override_callable, _write_thickness, _swap_class, _replace_in_mapping),
    ids=("callable-override", "thickness-write", "class-swap", "mapping-replace"),
)
def test_non_representative_v2d_mutation_fails_closed(mutate: object) -> None:
    """Only the first V2D element is re-scanned; the others rely on the mesh
    token and the ``__setattr__`` hook, so mutate the second one."""

    model, load = _two_v2d_model()
    v2d = [
        element
        for element in model.mesh.elements.values()
        if type(element) is NativeParityE4PLS3V2DShellElement
    ]
    assert len(v2d) == 2
    target = v2d[1]
    calls: list[int] = []

    def trigger(_message: str) -> None:
        calls.append(1)
        if len(calls) == 1:
            mutate(target, model)  # type: ignore[operator]

    with pytest.raises((AssemblyError, ElementCapabilityError)):
        _solve(model, load, status_callback=trigger)
    assert calls == [1]


def test_two_v2d_newton_loop_uses_trusted_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contexts = _count_complete_scans(monkeypatch)
    result = _solve(*_two_v2d_model())

    assert result.status == "completed"
    for context in NEWTON_LOOP_CONTEXTS:
        assert context not in contexts

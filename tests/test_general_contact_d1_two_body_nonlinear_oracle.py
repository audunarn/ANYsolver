"""Bounded nonlinear Q4/S3 two-body response with independent contact work."""

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np


def test_clipping_signature_distinguishes_equal_vertex_counts_with_different_edges():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "docs" / "d1_review_support"))
    from d1_two_body_current_skin_quadrature import overlap_incidence
    from d1_two_body_reference_oracle import _clip

    source = np.array(((0., 0.), (1., 0.), (1., 1.), (0., 1.)))
    lower_left = np.array(((0., 0.), (0.2, 0.), (0., 0.2)))
    upper_right = np.array(((1., 1.), (0.8, 1.), (1., 0.8)))
    first = _clip(source, lower_left)
    second = _clip(source, upper_right)
    assert len(first) == len(second) == 3
    assert (overlap_incidence(source, lower_left, first)
            == overlap_incidence(source, lower_left, np.roll(first, 1, axis=0)))
    assert (overlap_incidence(source, lower_left, first)
            != overlap_incidence(source, upper_right, second))


def test_saved_slide_matches_independent_current_contact_kkt():
    root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((
        str(root / "src"), str(root), str(root / "docs" / "d1_review_support"),
    ))
    completed = subprocess.run(
        [sys.executable, str(root / "docs" / "d1_review_support"
                                   / "d1_two_body_nonlinear_kkt_compare.py")],
        cwd=root, env=environment, capture_output=True, text=True,
        check=True, timeout=120,
    )
    result = json.loads(completed.stdout)
    assert result["status"] == "development_independent_contact_nonlinear_kkt"
    assert result["active_pressure_modes"] == [3, 8]
    assert result["clipping_incidence_signature"]
    assert result["final_scaled_merit"] <= 1e-9
    assert result["minimum_inactive_gap_m"] >= -1e-9
    assert min(row["minimum_active_force_n"] for row in result["trace"]) > 0
    assert result["maximum_displacement_difference_m_or_rad"] <= 1e-9
    derivative = result["gradient_step_sensitivity"]
    assert derivative["directions"] == 30
    assert derivative["resolved_columns_at_norm_1e_minus_4"] >= 10
    assert derivative["maximum_half_vs_nominal_resolved_relative_difference"] <= 1e-5
    assert derivative["maximum_double_vs_nominal_resolved_relative_difference"] <= 1e-5
    assert derivative["maximum_half_vs_nominal_absolute_difference"] <= 1e-8
    assert derivative["maximum_double_vs_nominal_absolute_difference"] <= 1e-8
    for name in (
        "relative_pressure_l2_difference",
        "relative_nodal_force_l2_difference",
        "relative_integrated_force_difference",
        "control_reaction_relative_l2_difference",
    ):
        assert result[name] <= 1e-6, (name, result[name])


def test_oracle_source_identity_does_not_attribute_an_enclosing_checkout(monkeypatch,tmp_path):
    # Extract this metadata-only helper without running the nonlinear fixture.
    # Its negative cases protect exported/installed-source provenance.
    import ast
    source=Path(__file__).resolve().parents[1]/'docs/d1_review_support/d1_two_body_nonlinear_kkt_compare.py'
    tree=ast.parse(source.read_text(encoding='utf-8'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_checkout_commit')
    namespace=dict(Path=Path,subprocess=subprocess)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace)
    project=tmp_path/'source-export';project.mkdir()
    calls=[]
    def git_output(args,**kwargs):
        calls.append(args)
        assert kwargs['cwd']==project
        return str(tmp_path) if '--show-toplevel' in args else 'must-not-be-used'
    monkeypatch.setattr(subprocess,'check_output',git_output)
    assert namespace['_checkout_commit'](project) is None
    assert len(calls)==1
    monkeypatch.setattr(subprocess,'check_output',lambda args,**kw:
        str(project) if '--show-toplevel' in args else 'own-checkout-sha')
    assert namespace['_checkout_commit'](project)=='own-checkout-sha'
    def unavailable(*args,**kw):raise subprocess.CalledProcessError(128,args[0])
    monkeypatch.setattr(subprocess,'check_output',unavailable)
    assert namespace['_checkout_commit'](project) is None

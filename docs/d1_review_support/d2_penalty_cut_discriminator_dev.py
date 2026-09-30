"""Independent finite projected weak-gap penalty strip discriminator; no shell claim.

S_i=integral N_i, G_i=integral N_i*g, g_i=G_i/S_i on S_i>0.
p_i=epsilon*max(-g_i,0), B_i=dG_i-g_i*dS_i=S_i*dg_i.
R=-sum p_i*B_i. On a smooth pressure branch,
J=sum epsilon*chi_i*outer(B_i,B_i)/S_i
  -sum p_i*(H_Gi-g_i*H_Si-outer(dS_i,dg_i)).
This generally nonsymmetric work Jacobian is NOT the Hessian of storage
E=epsilon/2*sum S_i*min(g_i,0)^2: dE=R+epsilon/2*sum g_i^-^2*dS_i.

The scalar oracle uses explicit polynomial moments, not production contact code.
Jet2 differentiates independent exact Gauss integrals. Full normal and cut-coordinate
work is retained; prescribed normal DOFs remain in reactions and work comparisons.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
JET_PATH = ROOT / "src/anysolver/_ge_beam3_mixed_ad.py"
spec = importlib.util.spec_from_file_location("d2_independent_jet2", JET_PATH)
jet_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jet_module)
Jet2 = jet_module.Jet2

INPUTS = dict(theta=[.1, .05, .025, .001, .00001, .0000001],
              epsilon_pa_per_m=[1e3, 1e4, 1e5], source_diffusivity_n=1.,
              target_diffusivity_n=5., width_m=1., source_prescribed_m=-1e-6,
              target_prescribed_m=0., source_end_load_n=-1e-3,
              vanishing_overlap_length_m=[.1, .01, .001, .0001, .00001],
              constant_gap_m=-1e-6, derivative_step_normal_m=1e-8,
              derivative_step_cut_m=1e-5, maximum_newton_iterations=20)
CRITERIA = dict(smooth_jacobian_relative=1e-5, full_virtual_work_relative=1e-10,
                equilibrium_and_normal_balance_relative=1e-6,
                normal_constant_gap_cut_work_absolute_n=1e-14,
                fixed_epsilon_cut_response_bound_factor=10.,
                last_two_epsilon_response_relative=.02)


def identity(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def moments(length):
    """Closed scalar polynomial moments and their exact length derivatives."""
    if not 0 < length < 2:
        raise ValueError("positive overlap below two source cells required")
    if length <= 1:
        l = length
        s = np.array([l-l*l/2, l*l/2, 0.])
        ds = np.array([1-l, l, 0.])
        m = np.array([[l-l*l+l**3/3, l*l/2-l**3/3, 0.],
                      [l*l/2-l**3/3, l**3/3, 0.], [0., 0., 0.]])
        dm = np.array([[(1-l)**2, l-l*l, 0.],
                       [l-l*l, l*l, 0.], [0., 0., 0.]])
        y = np.array([l*l/2-l**3/3, l**3/3, 0.])
        dy = np.array([l-l*l, l*l, 0.])
    else:
        t = length-1
        s = np.array([.5, .5+t-t*t/2, t*t/2])
        ds = np.array([0., 1-t, t])
        m = np.array([[1/3, 1/6, 0.],
                      [1/6, 1/3+t-t*t+t**3/3, t*t/2-t**3/3],
                      [0., t*t/2-t**3/3, t**3/3]])
        dm = np.array([[0., 0., 0.],
                       [0., (1-t)**2, t-t*t], [0., t-t*t, t*t]])
        y = np.array([1/6, 1/3+t-t**3/3, t*t/2+t**3/3])
        dy = np.array([0., 1-t*t, t+t*t])
    return s, ds, m, dm, y, dy


def scalar_oracle(x, epsilon):
    l = x[5]
    s, ds, m, dm, y, dy = moments(l)
    a = np.column_stack((m, -(s-y/l), -y/l))
    g_integral = a @ x[:5]
    g = np.divide(g_integral, s, out=np.zeros(3), where=s > 0)
    p = epsilon*np.maximum(-g, 0.)
    d_g_integral_l = dm @ x[:3]-ds*x[3]-(dy/l-y/l**2)*(x[4]-x[3])
    b = np.column_stack((a, d_g_integral_l-g*ds))
    residual = -p @ b
    return residual, s, g, p, b


def differentiated_work(x, epsilon):
    jets = [Jet2.variable(value, i, 6) for i, value in enumerate(x)]
    l = jets[5]
    zero = Jet2.constant(0., 6)
    support = [zero, zero, zero]
    weighted = [zero, zero, zero]
    # Degree-two integrands: exact three-point rule on each fixed source cell.
    gauss = ((-np.sqrt(3/5), 5/9), (0., 8/9), (np.sqrt(3/5), 5/9))
    intervals = [(zero, l, 0)] if x[5] <= 1 else [
        (zero, Jet2.constant(1., 6), 0), (Jet2.constant(1., 6), l, 1)]
    for left, right, cell in intervals:
        for point, weight in gauss:
            y = (left+right)/2+(right-left)*(point/2)
            n = [1-y, y, zero] if cell == 0 else [zero, 2-y, y-1]
            gap = sum((n[i]*jets[i] for i in range(3)), zero)
            gap -= (1-y/l)*jets[3]+(y/l)*jets[4]
            for i in range(3):
                factor = n[i]*(right-left)*(weight/2)
                support[i] = support[i]+factor
                weighted[i] = weighted[i]+factor*gap
    residual, jacobian = np.zeros(6), np.zeros((6, 6))
    for s, w in zip(support, weighted, strict=True):
        if s.value == 0:
            continue  # exactly unsupported mode, retained in all three arrays
        g = w/s
        p = epsilon*max(-g.value, 0.)
        b = w.gradient-g.value*s.gradient
        residual -= p*b
        if p > 0:
            jacobian += epsilon*np.outer(b, b)/s.value
        jacobian -= p*(w.hessian-g.value*s.hessian
                       - np.outer(s.gradient, g.gradient))
    return residual, jacobian


def structural_stiffness(length):
    k = np.zeros((5, 5))
    for left in (0, 1):
        k[np.ix_([left, left+1], [left, left+1])] += np.array([[1., -1.], [-1., 1.]])
    k[3:, 3:] = 5/length*np.array([[1., -1.], [-1., 1.]])
    return k


def case(theta, epsilon):
    length = 1+theta
    k = structural_stiffness(length)
    f = np.array([0., 0., INPUTS["source_end_load_n"], 0., 0.])
    free = np.array([1, 2, 4])
    x = np.array([INPUTS["source_prescribed_m"], -1e-6, -1e-6, 0., 0., length])
    for iteration in range(INPUTS["maximum_newton_iterations"]):
        r, j = differentiated_work(x, epsilon)
        full = k@x[:5]+r[:5]-f
        if np.linalg.norm(full[free])/1e-3 <= 1e-10:
            break
        tangent = k+j[:5, :5]
        x[free] -= np.linalg.solve(tangent[np.ix_(free, free)], full[free])
    else:
        raise ValueError("strip equilibrium did not converge within declared bound")
    oracle, s, g, p, b = scalar_oracle(x, epsilon)
    # Different value/derivative route; central finite differences of explicit moments.
    fd = np.zeros((6, 6))
    perturbations = []
    for i in range(6):
        h = INPUTS["derivative_step_normal_m"] if i < 5 else min(
            INPUTS["derivative_step_cut_m"], theta/4)
        direction = np.eye(6)[i]*h
        plus = scalar_oracle(x+direction, epsilon)
        minus = scalar_oracle(x-direction, epsilon)
        fd[:, i] = (plus[0]-minus[0])/(2*h)
        perturbations.append(dict(coordinate=i, half_interval=float(h),
            active_branch_unchanged=bool(np.array_equal(plus[3] > 0, p > 0)
                                        and np.array_equal(minus[3] > 0, p > 0)),
            minimum_positive_support_m2=float(min(np.min(plus[1]), np.min(minus[1])))))
    reaction = full[[0, 3]]
    direction = np.array([.2, -.3, .1, -.4, .4, .2])
    work = float(-p @ (b@direction))
    work_error = abs(float(r@direction)-work)/max(abs(work), 1e-12)
    reference = float(np.linalg.norm(fd))
    return dict(theta=theta, epsilon_pa_per_m=epsilon, coordinates=x.tolist(),
        support_m2=s.tolist(), normalized_gap_m=g.tolist(), pressure_pa=p.tolist(),
        all_three_pressure_modes_retained=True, supported_count=int(np.count_nonzero(s)),
        residual_full_normal_and_cut=r.tolist(), jacobian_full_normal_and_cut=j.tolist(),
        jacobian_oracle_relative=float(np.linalg.norm(j-fd)/max(reference, 1e-12)),
        residual_oracle_relative=float(np.linalg.norm(r-oracle)/max(np.linalg.norm(oracle), 1e-12)),
        full_virtual_work_relative=work_error,
        equilibrium_relative=float(np.linalg.norm(full[free])/1e-3),
        fixed_source_normal_reaction_n=float(reaction[0]),
        fixed_target_normal_reaction_n=float(reaction[1]),
        normal_global_balance_relative=float(abs(np.sum(reaction)+np.sum(f))/1e-3),
        both_body_contact_balance_relative=float(abs(np.sum(r[:5]))/1e-3),
        normal_contact_force_n=float(s@p),
        minimum_full_supported_space_tangent_eigenvalue=float(np.linalg.eigvalsh(
            (k+j[:5, :5])[np.ix_(free, free)])[0]),
        full_jacobian_nonsymmetry_l2=float(np.linalg.norm(j-j.T)),
        free_response_l2_m=float(np.linalg.norm(x[free])), iterations=iteration+1,
        oracle_perturbation_intervals=perturbations,
        free_tangent_condition_number=float(np.linalg.cond(
            (k+j[:5, :5])[np.ix_(free, free)])),
        represented_overlap_endpoint_gaps_m=[float(x[0]-x[3]),
            float(x[1]-(x[3]+(x[4]-x[3])/length)),
            float(x[1]*(2-length)+x[2]*(length-1)-x[4])],
        uncovered_source_tip_gap_excluded=True)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    started = time.perf_counter()
    rows = [case(theta, epsilon) for theta in INPUTS["theta"]
            for epsilon in INPUTS["epsilon_pa_per_m"]]
    cut_controls = []
    for length in INPUTS["vanishing_overlap_length_m"]:
        x = np.array([-1e-6, -1e-6, -1e-6, 0., 0., length])
        r, s, g, p, _ = scalar_oracle(x, 1e4)
        flux = .5*1e4*1e-12  # derivative of epsilon*delta^2*length/2
        cut_controls.append(dict(overlap_length_m=length, support_m2=s.tolist(),
            pressure_pa=p.tolist(), normal_force_n=float(s@p),
            projected_cut_work_n=float(r[5]), storage_derivative_n=flux,
            pressure_modes_retained=3))
    sensitivities = []
    for theta in INPUTS["theta"]:
        pair = [row for row in rows if row["theta"] == theta][-2:]
        response = [np.array(row["coordinates"])[[1, 2, 4]] for row in pair]
        sensitivities.append(dict(theta=theta,
            epsilon_pair_pa_per_m=[row["epsilon_pa_per_m"] for row in pair],
            free_response_relative=float(np.linalg.norm(response[0]-response[1])/
                np.linalg.norm(response[1])),
            force_relative=abs(pair[0]["normal_contact_force_n"]-pair[1]["normal_contact_force_n"])/
                pair[1]["normal_contact_force_n"]))
    checks = dict(jacobian=max(r["jacobian_oracle_relative"] for r in rows) <= 1e-5,
        residual=max(r["residual_oracle_relative"] for r in rows) <= 1e-10,
        full_work=max(r["full_virtual_work_relative"] for r in rows) <= 1e-10,
        equilibrium=max(r["equilibrium_relative"] for r in rows) <= 1e-6,
        reactions=max(r["normal_global_balance_relative"] for r in rows) <= 1e-6,
        both_body_balance=max(r["both_body_contact_balance_relative"] for r in rows) <= 1e-6,
        positive_pressure=all(min(r["pressure_pa"]) >= 0 for r in rows),
        coercive_supported_response=all(r["minimum_full_supported_space_tangent_eigenvalue"] > 0
                                        for r in rows),
        zero_constant_gap_cut_work=max(abs(r["projected_cut_work_n"]) for r in cut_controls) <= 1e-14,
        last_two_epsilon_response=all(s["free_response_relative"] <= .02 for s in sensitivities))
    for epsilon in INPUTS["epsilon_pa_per_m"]:
        selected = [r for r in rows if r["epsilon_pa_per_m"] == epsilon]
        checks[f"bounded_cut_response_epsilon_{epsilon:g}"] = max(
            r["free_response_l2_m"] for r in selected) <= 10*selected[0]["free_response_l2_m"]
    result = dict(status="development_finite_projected_penalty_strip_discriminator",
        accepted=False, released=False, inputs=INPUTS, criteria=CRITERIA,
        cap=dict(time_limit_seconds=180, memory_limit_bytes=1073741824, maximum_executions=1),
        source={"adapter": identity(__file__), "jet2": identity(JET_PATH),
                "read_only_production_work": identity(ROOT/"src/anysolver/general_contact/s3_patch_augmented.py"),
                "historical_counterexample": identity(ROOT/"docs/d1_review_support/d1_cut_front_two_hat_counterexample_20260929.md")},
        python_executable=sys.executable, numpy_version=np.__version__,
        effective_thread_environment={name: os.environ.get(name) for name in
            ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
        rows=rows, vanishing_overlap_constant_gap_controls=cut_controls,
        finite_regularization_sensitivity=sensitivities, criterion_results=checks,
        elapsed_seconds=time.perf_counter()-started,
        limits=["Independent scalar strip, not the retained 2D shell counterexample or a shell solve.",
                "No cut-uniform exact-pressure inf-sup or method acceptance claim.",
                "Projection/offset shell work, physical gap accuracy and moving active rims remain untested."])
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(criterion_results=checks, elapsed_seconds=result["elapsed_seconds"],
                          output=str(args.output))), flush=True)


if __name__ == "__main__":
    main()

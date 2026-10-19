"""Finite complementary-basis oracle for ONE saved modified cone.

No ANYsolver/material imports, force evaluations or production predictors.
Run only through the task harness under the separately granted 120s bound.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import pickle
import time

import numpy as np


EPS = np.finfo(float).eps
ROUND = 64.0 * EPS
STATUS = {0: "singular", 1: "numerically_excluded", 2: "weak",
          3: "uncertain", 4: "finite_feasible"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operators", type=Path)
    parser.add_argument("terms", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    paths = [args.operators.resolve(), args.terms.resolve(), Path(__file__).resolve()]
    identity = {str(p): digest(p) for p in paths}
    save_json(out / "identity.json", identity)
    # Trusted local numerical arrays only. No model or material reconstruction.
    data = pickle.loads(args.operators.read_bytes())
    terms = pickle.loads(args.terms.read_bytes())
    A, P, wy, wg, rhs = (np.array(data[k], dtype=float, copy=True)
                         for k in ("A", "P", "wy", "wg", "rhs"))
    assert A.shape == (25, 25) and P.shape == (24, 16)
    assert wy.shape == (16, 24) and wg.shape == (16,) and rhs.shape == (25,)
    assert len(terms) == 16 and all(np.all(np.isfinite(x)) for x in (A, P, wy, wg, rhs))
    E = np.array([t["elastic_modulus"] for t in terms])
    Y = np.array([t["yield_stress"] for t in terms])
    h = np.array([t["h"] for t in terms])
    rows = np.array([t["row"] for t in terms])
    assert np.all(E > 0.) and np.all(Y > 0.) and np.all(h > 0.)
    yield_strain = Y/E
    # Independent units/order check. No cone data or thresholds are changed.
    wy_from_terms = -rows/(E*Y)[:, None]
    wg_from_terms = h/(E*Y*Y)
    assert np.all(np.abs(wy-wy_from_terms) <= ROUND*np.maximum(1., np.abs(wy_from_terms)))
    assert np.all(np.abs(wg-wg_from_terms) <= ROUND*np.maximum(1., np.abs(wg_from_terms)))
    B = np.vstack((P, np.zeros((1, 16))))

    def original_checks(z, gamma):
        w = wy @ z[:-1] + wg*gamma
        residual = A @ z-rhs-B @ gamma
        # Componentwise operation scales, exactly the given 64eps convention.
        scale = np.abs(A) @ np.abs(z)+np.abs(rhs)+np.abs(B) @ np.abs(gamma)
        global_bound = ROUND*np.maximum(1., scale)
        cone_bound = ROUND*(np.abs(gamma)+np.abs(w)+yield_strain)
        product = gamma*w
        product_bound = cone_bound*(np.abs(gamma)+np.abs(w)+yield_strain)
        minimum = np.minimum(gamma, w)  # Independent unsmoothed NCP residual.
        equations = bool(np.all(np.abs(residual) <= global_bound))
        cone = bool(np.all(gamma >= -cone_bound) and np.all(w >= -cone_bound)
                    and np.all(np.abs(minimum) <= cone_bound)
                    and np.all(np.abs(product) <= product_bound))
        denominator = np.linalg.norm(A, np.inf)*np.linalg.norm(z, np.inf)
        denominator += np.linalg.norm(B, np.inf)*np.linalg.norm(gamma, np.inf)+np.linalg.norm(rhs, np.inf)
        backward = float(np.linalg.norm(residual, np.inf)/max(denominator, np.finfo(float).tiny))
        return dict(w=w, residual=residual, global_bound=global_bound,
                    cone_bound=cone_bound, product=product, product_bound=product_bound,
                    minimum=minimum, equations=equations, cone=cone, backward=backward)

    total = 1 << 16
    masks = np.arange(total, dtype=np.uint32)
    classifications = np.full(total, -1, dtype=np.int8)
    # All visited solutions retained, including failed/weak/uncertain bases.
    zs = np.full((total, 25), np.nan)
    gammas = np.full((total, 16), np.nan)
    ws = np.full((total, 16), np.nan)
    conditions = np.full(total, np.nan)
    backward_errors = np.full(total, np.nan)
    basis_backward = np.full(total, np.nan)
    forward_estimates = np.full(total, np.nan)
    equation_pass = np.zeros(total, dtype=bool)
    cone_pass = np.zeros(total, dtype=bool)
    counts = dict(bases_visited=0, basis_solve_calls=0, svd_calls=0,
                  singular=0, numerically_excluded=0, weak=0, uncertain=0,
                  finite_feasible=0)
    found = None
    stop = "exhaustive"
    for mask in range(total):
        if time.perf_counter()-start >= 90.0:
            stop = "internal_90_second_bound"
            break
        active = np.array([i for i in range(16) if mask & (1 << i)], dtype=int)
        na = len(active)
        matrix = np.zeros((25+na, 25+na))
        matrix[:25, :25] = A
        matrix[:25, 25:] = -B[:, active]
        matrix[25:, :24] = wy[active]
        matrix[25:, 25:] = np.diag(wg[active])
        vector = np.r_[rhs, np.zeros(na)]
        # Solve-only physical column scaling and row equilibration. Admission
        # always uses the ORIGINAL equations above, never these scaled rows.
        col = np.r_[np.ones(25), yield_strain[active]]
        row = np.maximum(np.max(np.abs(matrix)*col, axis=1), np.abs(vector))
        row[row == 0.] = 1.
        scaled = matrix*col[None, :]/row[:, None]
        scaled_rhs = vector/row
        counts["bases_visited"] += 1
        counts["basis_solve_calls"] += 1
        try:
            solution_scaled = np.linalg.solve(scaled, scaled_rhs)
        except np.linalg.LinAlgError:
            classifications[mask] = 0; counts["singular"] += 1
            continue
        counts["svd_calls"] += 1
        try:
            singular_values = np.linalg.svd(scaled, compute_uv=False)
        except np.linalg.LinAlgError:
            singular_values = np.array([np.nan, np.nan])
        largest, smallest = float(singular_values[0]), float(singular_values[-1])
        condition = largest/smallest if smallest > 0. else float("inf")
        conditions[mask] = condition
        x = col*solution_scaled
        z, gamma = x[:25], np.zeros(16)
        gamma[active] = x[25:]
        zs[mask], gammas[mask] = z, gamma
        if not np.all(np.isfinite(x)):
            classifications[mask] = 3; counts["uncertain"] += 1
            continue
        check = original_checks(z, gamma); w = check["w"]
        ws[mask] = w; backward_errors[mask] = check["backward"]
        equation_pass[mask], cone_pass[mask] = check["equations"], check["cone"]
        scaled_residual = scaled @ solution_scaled-scaled_rhs
        bden = np.linalg.norm(scaled, np.inf)*np.linalg.norm(solution_scaled, np.inf)+np.linalg.norm(scaled_rhs, np.inf)
        basis_backward[mask] = np.linalg.norm(scaled_residual, np.inf)/max(bden, np.finfo(float).tiny)
        # Conservative sensitivity estimate, not a certified interval bound.
        rounding = ROUND*(np.abs(scaled) @ np.abs(solution_scaled)+np.abs(scaled_rhs))
        sv_margin = ROUND*len(x)*largest
        forward = ((np.linalg.norm(scaled_residual)+np.linalg.norm(rounding))/(smallest-sv_margin)
                   if np.isfinite(smallest) and smallest > sv_margin else float("inf"))
        forward_estimates[mask] = forward
        z_error = forward*col[:25]
        gamma_error = np.zeros(16); gamma_error[active] = forward*col[25:]
        w_error = (np.abs(wy) @ z_error[:-1] + np.abs(wg)*gamma_error
                   + ROUND*(np.abs(wy) @ np.abs(z[:-1])+np.abs(wg*gamma)+yield_strain))
        inactive = np.array([i for i in range(16) if not mask & (1 << i)], dtype=int)
        free_factors = np.r_[gamma[active], w[inactive]]
        free_bounds = np.r_[check["cone_bound"][active], check["cone_bound"][inactive]]
        strict = bool(np.all(free_factors > free_bounds))
        if check["equations"] and check["cone"] and strict:
            code = 4
            found = dict(mask=mask, active_indices=active.tolist(), z=z,
                         gamma=gamma, check=check, scaled_condition=condition,
                         scaled_basis_backward_error=float(basis_backward[mask]),
                         forward_sensitivity_estimate=forward)
            stop = "finite_feasible_assignment_found"
        elif check["equations"] and check["cone"]:
            code = 2
        elif np.any(gamma < -np.maximum(gamma_error, check["cone_bound"])) or np.any(w < -np.maximum(w_error, check["cone_bound"])):
            code = 1
        else:
            code = 3
        classifications[mask] = code; counts[STATUS[code]] += 1
        if found is not None:
            break
        if mask % 4096 == 4095:
            print(json.dumps({"progress": counts, "elapsed_seconds": time.perf_counter()-start}), flush=True)

    visited = counts["bases_visited"]
    np.savez(out / "bases.npz", mask=masks[:visited], status=classifications[:visited],
             z=zs[:visited], gamma=gammas[:visited], w=ws[:visited],
             scaled_condition=conditions[:visited], original_backward_error=backward_errors[:visited],
             scaled_basis_backward_error=basis_backward[:visited],
             forward_sensitivity_estimate=forward_estimates[:visited],
             original_equations_pass=equation_pass[:visited], cone_pass=cone_pass[:visited],
             yield_strain=yield_strain)
    if found is not None:
        with (out / "feasible.pkl").open("xb") as stream:
            pickle.dump(found, stream, protocol=5)
    unchanged = {str(p): digest(p) for p in paths} == identity
    unresolved = counts["singular"]+counts["weak"]+counts["uncertain"]+total-visited
    result = dict(saved_modified_cone_only=True, no_force_material_or_target_evaluations=True,
                  production_predictor_seed_authorized=False, stop_reason=stop,
                  finite_roundoff_feasible=found is not None, exact_real_feasibility_certified=False,
                  infeasibility_claim=False, counts=counts, total_bases=total,
                  unvisited_bases=total-visited, unresolved_or_weak_bases=unresolved,
                  status_codes=STATUS, original_input_files_unchanged=unchanged,
                  roundoff_multiplier=64, elapsed_seconds=time.perf_counter()-start,
                  finite_feasible_mask=None if found is None else found["mask"],
                  finite_feasible_active_indices=None if found is None else found["active_indices"])
    if found is not None:
        ck = found["check"]
        result["witness"] = dict(scaled_condition=found["scaled_condition"],
            original_equation_backward_error=ck["backward"],
            max_original_equation_error=float(np.max(np.abs(ck["residual"]))),
            max_original_equation_error_over_bound=float(np.max(np.abs(ck["residual"])/ck["global_bound"])),
            minimum_gamma=float(np.min(found["gamma"])), minimum_w=float(np.min(ck["w"])),
            maximum_product=float(np.max(np.abs(ck["product"]))),
            maximum_natural_complementarity_error_over_bound=float(np.max(np.abs(ck["minimum"])/ck["cone_bound"])))
    save_json(out / "result.json", result)
    print(json.dumps(result, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()

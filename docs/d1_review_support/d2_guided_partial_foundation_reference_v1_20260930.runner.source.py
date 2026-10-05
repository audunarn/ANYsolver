"""Independent continuum scalar reference for the guided partial foundation.

SI: D [N/m], q [N/m²] downward, gap [m], kappa [N/m³], width [m].
Normal displacement is positive upward, pressure positive upward on the source.
No production contact, structural assembly, or numerical ODE solver is used.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time
import traceback

import numpy as np

DEFAULT_D = (5./6.)*(1e5/(2*(1+.3)))*.05
DEFAULT_INPUTS = dict(D=DEFAULT_D, q=.5, gap=1e-4, kappa=1e6,
                      length=1., supported_length=.9, width=1.)


def _sech(x):
    return 2*math.exp(-x)/(1+math.exp(-2*x))


def _ratio(x, denominator, *, sinh=False):
    # 0 <= x <= denominator: no large positive exponent or overflow.
    numerator = -np.expm1(-2*x) if sinh else 1+np.exp(-2*x)
    return np.exp(x-denominator)*numerator/(1+math.exp(-2*denominator))


def _required_gap(a, D, q, beta, supported, tail):
    z = beta*(supported-a)
    return q/D*(a*a/2+a*math.tanh(z)/beta+a*tail*_sech(z))


def _decimal_ratio(x, denominator, sinh=False):
    numerator = 1-(-2*x).exp() if sinh else 1+(-2*x).exp()
    return (x-denominator).exp()*numerator/(1+(-2*denominator).exp())


@dataclass(frozen=True)
class PartialFoundationReference:
    D: float
    q: float
    initial_gap_m: float
    kappa: float
    length: float
    supported_length: float
    width: float
    front_m: float
    front_bracket_m: tuple
    regime: str

    @property
    def beta(self):
        return math.sqrt(self.kappa)/math.sqrt(self.D)

    @property
    def tail(self):
        return self.length-self.supported_length

    def _coordinates(self, s):
        s = np.asarray(s, dtype=float)
        if np.any(~np.isfinite(s)) or np.any(s < 0) or np.any(s > self.length):
            raise ValueError("finite reference coordinate in [0,length] required")
        return s

    @staticmethod
    def _returned(value, coordinates):
        return float(value) if coordinates.ndim == 0 else value

    def _covered_active_gap(self, s):
        tau = self.beta*(s-self.front_m)
        lam = self.beta*(self.supported_length-self.front_m)
        # cosh(lam-tau)/cosh(lam)-1, without cancellation at the front.
        difference = np.expm1(-tau)*(-np.expm1(-2*lam+tau))/(1+math.exp(-2*lam))
        return self.q/self.kappa*difference-self.q*self.tail/(self.D*self.beta)*_ratio(tau, lam, sinh=True)

    def gap(self, s):
        """Geometric g0+w, also reported on the uncovered tail (pressure=0)."""
        s = self._coordinates(s)
        if self.regime == "no_contact":
            result = self.initial_gap_m+self.q/(2*self.D)*s*s-self.q*self.length/self.D*s
            return self._returned(result, s)
        a, cut = self.front_m, self.supported_length
        result = np.empty_like(s)
        open_mask, active_mask = s < a, (s >= a) & (s <= cut)
        if a > 0:
            result[open_mask] = (a-s[open_mask])*(self.initial_gap_m/a-self.q*s[open_mask]/(2*self.D))
        result[active_mask] = self._covered_active_gap(s[active_mask])
        tail_mask = s > cut
        xi = s[tail_mask]-cut
        result[tail_mask] = self._covered_active_gap(np.asarray(cut))-self.q*self.tail*xi/self.D+self.q*xi*xi/(2*self.D)
        return self._returned(result, s)

    def displacement(self, s):
        coordinates = self._coordinates(s)
        return self._returned(np.asarray(self.gap(coordinates))-self.initial_gap_m, coordinates)

    def pressure(self, s):
        s = self._coordinates(s)
        result = np.zeros_like(s)
        if self.regime != "no_contact":
            mask = (s >= self.front_m) & (s <= self.supported_length)
            result[mask] = -self.kappa*self._covered_active_gap(s[mask])
        return self._returned(result, s)

    def derivative(self, s, order=1):
        """Analytically differentiated w; second derivative chooses covered side at cut."""
        if type(order) is not int or order not in (1, 2):
            raise ValueError("derivative order must be 1 or 2")
        s = self._coordinates(s)
        if self.regime == "no_contact":
            result = self.q/self.D*(s-self.length) if order == 1 else np.full_like(s, self.q/self.D)
            return self._returned(result, s)
        a, cut, beta = self.front_m, self.supported_length, self.beta
        result = np.empty_like(s)
        open_mask, active_mask, tail_mask = s < a, (s >= a) & (s <= cut), s > cut
        if a > 0:
            result[open_mask] = (self.q*s[open_mask]/self.D-self.initial_gap_m/a-self.q*a/(2*self.D)
                                 if order == 1 else self.q/self.D)
        x = beta*(cut-s[active_mask])
        tau = beta*(s[active_mask]-a)
        lam = beta*(cut-a)
        if order == 1:
            result[active_mask] = -self.q/(self.D*beta)*_ratio(x, lam, sinh=True)-self.q*self.tail/self.D*_ratio(tau, lam)
            result[tail_mask] = self.q/self.D*(s[tail_mask]-self.length)
        else:
            result[active_mask] = self.q/self.D*_ratio(x, lam)-self.q*self.tail*beta/self.D*_ratio(tau, lam, sinh=True)
            result[tail_mask] = self.q/self.D
        return self._returned(result, s)

    def force_between(self, a, b):
        """Analytical pressure integral [N], with inactive/uncovered portions zero.

        Decimal antiderivative differences avoid cancellation in narrow bins.
        This is a closed integral, not pressure quadrature or a finite mesh.
        """
        a, b = float(a), float(b)
        if not (math.isfinite(a) and math.isfinite(b) and 0 <= a <= b <= self.length):
            raise ValueError("ordered finite bin in [0,length] required")
        if self.regime == "no_contact":
            return 0.
        lo, hi = max(a, self.front_m), min(b, self.supported_length)
        if hi <= lo:
            return 0.
        with localcontext() as context:
            context.prec = 80
            D, q, kappa, cut, front, tail, width, lo, hi = map(Decimal.from_float,
                (self.D, self.q, self.kappa, self.supported_length, self.front_m,
                 self.tail, self.width, lo, hi))
            beta = (kappa/D).sqrt()
            lam = beta*(cut-front)
            # Integral q*(1-cosh(beta*(cut-s))/cosh(lam))
            #       +q*tail*beta*sinh(beta*(s-front))/cosh(lam).
            first = _decimal_ratio(beta*(cut-lo), lam, True)-_decimal_ratio(beta*(cut-hi), lam, True)
            second = _decimal_ratio(beta*(hi-front), lam)-_decimal_ratio(beta*(lo-front), lam)
            value = width*q*((hi-lo)-first/beta+tail*second)
            if value < 0:
                raise ArithmeticError("unresolved negative analytic pressure integral")
            return float(value)

    def summary(self):
        a, beta = self.front_m, self.beta
        if self.regime == "no_contact":
            clamp = self.q*self.length*self.width
            reaction = 0.
            root_residual = None
        else:
            lam = beta*(self.supported_length-a)
            clamp = self.width*self.q*(a+math.tanh(lam)/beta+self.tail*_sech(lam))
            reaction = self.force_between(0., self.length)
            root_residual = _required_gap(a, self.D, self.q, beta, self.supported_length, self.tail)-self.initial_gap_m
        return dict(regime=self.regime, D_n_per_m=self.D, q_pa=self.q, initial_gap_m=self.initial_gap_m,
                    kappa_pa_per_m=self.kappa, length_m=self.length, supported_length_m=self.supported_length,
                    width_m=self.width, beta_per_m=beta, front_m=a, front_bracket_m=list(self.front_bracket_m),
                    front_equation_gap_residual_m=root_residual,
                    contact_reaction_n=reaction, clamp_reaction_n=clamp, total_downward_load_n=self.width*self.q*self.length,
                    balance_residual_n=clamp+reaction-self.width*self.q*self.length,
                    minimum_covered_gap_m=self.gap(self.supported_length), uncovered_tip_gap_m=self.gap(self.length),
                    free_tip_displacement_m=self.displacement(self.length),
                    pressure_at_cut_covered_side_pa=self.pressure(self.supported_length),
                    contact_force_sign="positive upward on source, opposite on fixed target",
                    scope="guided scalar continuum, linear transverse shear, fixed partial foundation; no general nonlinear qualification")


def make_reference(D=DEFAULT_D, q=.5, gap=1e-4, kappa=1e6, length=1., supported_length=.9, width=1.):
    parameters = [float(v) for v in (D, q, gap, kappa, length, supported_length, width)]
    D, q, gap, kappa, length, supported_length, width = parameters
    if (not all(math.isfinite(v) for v in parameters) or min(D, q, kappa, length, supported_length, width) <= 0
            or gap < 0 or supported_length > length):
        raise ValueError("finite positive D/q/kappa/length/support/width, nonnegative gap, support<=length required")
    beta = math.sqrt(kappa)/math.sqrt(D)
    if not math.isfinite(beta) or not math.isfinite(beta*supported_length):
        raise ValueError("finite inverse foundation length required")
    critical_gap = q/D*supported_length*(length-supported_length/2)
    if gap >= critical_gap:
        return PartialFoundationReference(D, q, gap, kappa, length, supported_length, width,
                                          supported_length, (supported_length, supported_length), "no_contact")
    if gap == 0:
        return PartialFoundationReference(D, q, gap, kappa, length, supported_length, width, 0., (0., 0.), "active_from_clamp")
    lo, hi = 0., supported_length
    for _ in range(128):
        mid = lo+(hi-lo)/2
        if mid == lo or mid == hi:
            break
        if _required_gap(mid, D, q, beta, supported_length, length-supported_length) < gap:
            lo = mid
        else:
            hi = mid
    front = min((lo, hi), key=lambda a: abs(_required_gap(a, D, q, beta, supported_length, length-supported_length)-gap))
    return PartialFoundationReference(D, q, gap, kappa, length, supported_length, width, front, (lo, hi), "partial_contact")


def selfcheck(reference):
    r = reference
    a, cut, end = r.front_m, r.supported_length, r.length
    # Independent high-precision monotone front solve, same physical inputs.
    with localcontext() as context:
        context.prec = 80
        D, q, gap, kappa, cutd, endd = map(Decimal.from_float,
            (r.D, r.q, r.initial_gap_m, r.kappa, cut, end))
        beta = (kappa/D).sqrt()
        lo, hi = Decimal(0), cutd
        for _ in range(220):
            mid = (lo+hi)/2
            lam = beta*(cutd-mid)
            sech = 2*(-lam).exp()/(1+(-2*lam).exp())
            tanh = (1-(-2*lam).exp())/(1+(-2*lam).exp())
            required = q/D*(mid*mid/2+mid*tanh/beta+mid*(endd-cutd)*sech)
            if required < gap:
                lo = mid
            else:
                hi = mid
        root_error = float(max(abs(Decimal.from_float(a)-lo), abs(Decimal.from_float(a)-hi)))
        exact_front = str((lo+hi)/2)
    sites = np.array((a*.25, a*.75, a+(cut-a)*.2, a+(cut-a)*.5,
                      a+(cut-a)*.8, cut+(end-cut)*.25, cut+(end-cut)*.75))
    ode = -r.D*r.derivative(sites, 2)-r.pressure(sites)+r.q
    differences = []
    for s in sites:
        boundary_distance = min(abs(s), abs(s-a), abs(s-cut), abs(s-end))
        h = min(1e-4*end, boundary_distance/16)
        values = r.displacement(s+np.array((-2., -1., 0., 1., 2.))*h)
        first = (values[0]-8*values[1]+8*values[3]-values[4])/(12*h)
        second = (-values[0]+16*values[1]-30*values[2]+16*values[3]-values[4])/(12*h*h)
        differences.append(dict(s_m=float(s), perturbation_m=h,
            derivative_absolute_error=float(abs(first-r.derivative(s))),
            independently_differenced_ode_relative_load_error=float(abs(-r.D*second-r.pressure(s)+r.q)/r.q)))
    lam = r.beta*(cut-a)
    open_front_slope = r.q*a/(2*r.D)-r.initial_gap_m/a
    active_front_slope = -r.q/(r.D*r.beta)*math.tanh(lam)-r.q*r.tail/r.D*_sech(lam)
    bins = [(0., .5), (.5, .75), (.75, .8), (.8, .85), (.85, .9), (.9, 1.)]
    bin_values = [dict(interval_m=[lo, hi], force_n=r.force_between(lo, hi)) for lo, hi in bins]
    # Independent numerical integration checks the closed bin primitives only.
    roots, weights = np.polynomial.legendre.leggauss(32)
    numerical = []
    for lo, hi in bins:
        lo, hi = max(lo, a), min(hi, cut)
        value = 0. if hi <= lo else r.width*(hi-lo)/2*float(weights @ r.pressure((lo+hi)/2+(hi-lo)/2*roots))
        numerical.append(value)
    summary = r.summary()
    force_closed = r.width*r.q*((cut-a)-math.tanh(lam)/r.beta+r.tail*(1-_sech(lam)))
    clamp_closed = r.width*(r.D*r.initial_gap_m/a+r.q*a/2)
    checks = dict(maximum_analytic_ode_residual_pa=float(np.max(abs(ode))),
        maximum_fd_ode_relative_load_error=max(item["independently_differenced_ode_relative_load_error"] for item in differences),
        clamp_displacement_m=r.displacement(0.), free_tip_slope=r.derivative(end),
        front_gap_m=r.gap(a), front_slope_mismatch=open_front_slope-active_front_slope,
        cut_slope_mismatch=r.derivative(cut)+r.q*r.tail/r.D,
        bin_additivity_error_n=abs(sum(item["force_n"] for item in bin_values)-summary["contact_reaction_n"]),
        maximum_bin_integral_quadrature_error_n=max(abs(x["force_n"]-y) for x, y in zip(bin_values, numerical)),
        contact_closed_formula_error_n=abs(force_closed-summary["contact_reaction_n"]),
        clamp_closed_formula_error_n=abs(clamp_closed-summary["clamp_reaction_n"]),
        force_balance_error_n=abs(summary["balance_residual_n"]),
        open_covered_minimum_gap_m=float(np.min(r.gap(np.linspace(0., a, 65)))),
        active_maximum_gap_m=float(np.max(r.gap(np.linspace(a, cut, 65)))),
        active_minimum_pressure_pa=float(np.min(r.pressure(np.linspace(a, cut, 65)))),
        uncovered_maximum_pressure_pa=float(np.max(r.pressure(np.linspace(np.nextafter(cut, end), end, 65)))))
    passed = (checks["maximum_analytic_ode_residual_pa"] <= 1e-12 and
              checks["maximum_fd_ode_relative_load_error"] <= 1e-5 and
              max(checks[name] for name in ("bin_additivity_error_n", "maximum_bin_integral_quadrature_error_n",
                  "contact_closed_formula_error_n", "clamp_closed_formula_error_n", "force_balance_error_n")) <= 1e-12 and
              max(abs(checks[name]) for name in ("clamp_displacement_m", "free_tip_slope", "front_gap_m",
                  "front_slope_mismatch", "cut_slope_mismatch")) <= 1e-12 and
              checks["open_covered_minimum_gap_m"] >= -1e-15 and checks["active_maximum_gap_m"] <= 1e-15 and
              checks["active_minimum_pressure_pa"] >= -1e-15 and checks["uncovered_maximum_pressure_pa"] == 0.)
    return dict(status="development_scalar_selfcheck_consistent" if passed else "development_scalar_selfcheck_failure",
                accepted=False, released=False, summary=summary, checks=checks, finite_difference_checks=differences,
                bin_integrals=bin_values, decimal80_front_m=exact_front, binary64_front_absolute_error_m=root_error,
                sites_m=sites.tolist(), displacements_m=r.displacement(sites).tolist(), pressures_pa=r.pressure(sites).tolist(),
                numerical_check_tolerances=dict(analytic_residual_pa=1e-12, force_n=1e-12, fd_relative_load=1e-5),
                scope="one fixed-candidate continuum scalar selfcheck; not a finite-element or nonlinear qualification")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inputs-output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.inputs_output.exists():
        parser.error("exclusive evidence output already exists")
    started = time.perf_counter()
    source = Path(__file__).resolve()
    inputs = dict(parameters=DEFAULT_INPUTS, source=str(source), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  resource_caps=dict(seconds=180, process_tree_bytes=1073741824), argv=sys.argv,
                  environment=dict(python=sys.version, executable=sys.executable, numpy=np.__version__, platform=platform.platform()),
                  production_contact_calls=0, accepted=False, released=False)
    with args.inputs_output.open("x", encoding="utf-8") as stream:
        json.dump(inputs, stream, indent=2)
    print(json.dumps(dict(stage="frozen_inputs_saved", elapsed_seconds=time.perf_counter()-started)), flush=True)
    try:
        result = selfcheck(make_reference(**DEFAULT_INPUTS))
    except Exception as error:
        result = dict(status="development_scalar_selfcheck_failure", accepted=False, released=False,
                      error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
    result.update(inputs=inputs, elapsed_seconds=time.perf_counter()-started)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({key: result[key] for key in ("status", "elapsed_seconds", "summary") if key in result}), flush=True)
    if result["status"] != "development_scalar_selfcheck_consistent":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

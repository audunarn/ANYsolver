"""B2 original-target scalar work prediction, not a solve or acceptance gate.

Exact rational interval arithmetic only. Missing directional/error observables
remain unresolved; historical scalar metadata never supplies their values.
No operator payload loading, matrix assembly, factor, precision/backend change.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import argparse
import hashlib
import json
from pathlib import Path

ABS_WORK = F.from_float(1e-12)
REL_WORK = F.from_float(1e-8)
UNIT_ROUNDOFF = F(1, 2**53)
HALF_SUBNORMAL = F(1, 2**1075)
ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Interval:
    lo: F
    hi: F

    def __post_init__(self):
        if not isinstance(self.lo, F) or not isinstance(self.hi, F) or self.lo > self.hi:
            raise ValueError("ordered exact rational interval required")

    @classmethod
    def point(cls, value):
        value = F(value)
        return cls(value, value)

    @classmethod
    def centered(cls, value, radius):
        value, radius = F(value), F(radius)
        if radius < 0:
            raise ValueError("nonnegative independent error radius required")
        return cls(value-radius, value+radius)

    def __add__(self, other):
        return Interval(self.lo+other.lo, self.hi+other.hi)

    def abs_min(self):
        return F(0) if self.lo <= 0 <= self.hi else min(abs(self.lo), abs(self.hi))

    def abs_max(self):
        return max(abs(self.lo), abs(self.hi))


def rounded_dot_radius(term_count, exact_abs_products_upper, *, finite_round_to_nearest):
    """Conservative 2n-operation binary64 dot bound incl gradual underflow.

    The caller must independently bound exact sum |a_i*b_i| and establish
    finite intermediates/RN arithmetic. This is an upper error bound, never
    an observed error floor, contraction or global solver norm.
    """
    if not finite_round_to_nearest or type(term_count) is not int or term_count < 0:
        raise ValueError("finite RN intermediates and nonnegative term count required")
    magnitude = F(exact_abs_products_upper)
    operations = 2*term_count
    if magnitude < 0 or operations*UNIT_ROUNDOFF >= 1:
        raise ValueError("valid absolute-action upper bound/operation count required")
    denominator = 1-operations*UNIT_ROUNDOFF
    return operations*(UNIT_ROUNDOFF*magnitude+HALF_SUBNORMAL)/denominator


def kinematic_work_radius(linear_abs_action_upper, quadratic_cross_upper,
                          quadratic_error_upper):
    """Bound work change from e between nominal and actual physical increment.

    Inputs separately enclose |e|^T|((K+K.T)u-f)|,
    |e|^T(|K|+|K.T|)|v|, and |e|^T|K||e|.
    All inputs use joules; no mixed force/moment scalar norm is introduced.
    """
    values = tuple(map(F, (linear_abs_action_upper, quadratic_cross_upper, quadratic_error_upper)))
    if any(value < 0 for value in values):
        raise ValueError("independent nonnegative work-action upper bounds required")
    return sum(values, F(0))


def required_signed_change(base_defect, candidate_external_work, error_radius=F(0)):
    """Sufficient change window for every enclosed D0/external/error value.

    Empty window means these enclosures cannot certify, not formulation failure.
    External interval encloses the candidate's actual product external work.
    """
    radius = F(error_radius)
    if radius < 0:
        raise ValueError("nonnegative work error radius required")
    tolerance_lower = work_tolerance_enclosure(candidate_external_work).lo
    lo = -tolerance_lower-base_defect.lo+radius
    hi = tolerance_lower-base_defect.hi-radius
    return None if lo > hi else Interval(lo, hi)


def work_tolerance_enclosure(candidate_external_work):
    """Unchanged product 1e-12+1e-8*abs(external), including two RN ops."""
    lower = ABS_WORK+REL_WORK*candidate_external_work.abs_min()
    upper = ABS_WORK+REL_WORK*candidate_external_work.abs_max()
    radius = rounded_dot_radius(1, upper, finite_round_to_nearest=True)
    return Interval(max(F(0), lower-radius), upper+radius)


def original_target_prediction(*, base_defect, linear_raw_work, quadratic_raw_work,
                               kinematic_error_radius, final_evaluation_radius,
                               candidate_external_work, original_equilibrium_rows=None,
                               homogeneous_physical_family=True):
    """Conditional development prediction from independently supplied witnesses.

    linear_raw_work = v.T((K+K.T)u-f), quadratic_raw_work=v.T K v.
    Kinematic radius covers actual reconstruction/update/final-restoration
    versus nominal v; final radius covers current work evaluation. Base D0
    already encloses its evaluation error. No physical/fullspace acceptance.
    Equilibrium rows are (original residual enclosure, unchanged caller
    tolerance enclosure), each compared in its own existing covector unit.
    """
    if not homogeneous_physical_family:
        raise ValueError("affine identity allowed, but existing homogeneous-work gate is not an affine gate")
    missing = [name for name, value in (("base_defect", base_defect),
               ("linear_raw_work", linear_raw_work), ("quadratic_raw_work", quadratic_raw_work),
               ("kinematic_error_radius", kinematic_error_radius),
               ("final_evaluation_radius", final_evaluation_radius),
               ("candidate_external_work", candidate_external_work)) if value is None]
    if missing:
        return {"status": "unresolved_missing_original_action_observables", "missing": missing,
                "qualification": False}
    error = F(kinematic_error_radius)+F(final_evaluation_radius)
    if min(F(kinematic_error_radius), F(final_evaluation_radius)) < 0:
        raise ValueError("nonnegative independent error radii required")
    defect = base_defect+linear_raw_work+quadratic_raw_work+Interval.centered(0, error)
    tolerance = work_tolerance_enclosure(candidate_external_work)
    tmin, tmax = tolerance.lo, tolerance.hi
    work = ("sufficient_enclosure" if defect.abs_max() <= tmin else
            "enclosed_failure" if defect.abs_min() > tmax else "unresolved_enclosure")
    equilibrium = "unresolved_missing_original_rows"
    if original_equilibrium_rows is not None:
        rows = tuple(original_equilibrium_rows)
        if not rows or any(t.lo < 0 for _, t in rows):
            raise ValueError("nonempty original rows/unchanged nonnegative tolerances required")
        equilibrium = ("sufficient_enclosure" if all(r.abs_max() <= t.lo for r, t in rows) else
                       "enclosed_failure" if any(r.abs_min() > t.hi for r, t in rows) else "unresolved_enclosure")
    return {"status": "conditional_original_target_prediction", "work": work,
            "equilibrium": equilibrium, "defect": defect, "tolerance": tolerance,
            "qualification": False, "condition": "independent raw-action/error/row witnesses; no stored-residual contraction assumed"}


def historical_requirements():
    """Only recorded case1 scalar metadata; no saved array decoding/evaluation."""
    path = ROOT / "docs/agent_plans/development/r8-b2-large-work-allocation-20261009/attempt-v1/summary.json"
    record = json.loads(path.read_text())
    d0 = F.from_float(record["signed_work_defect"])
    external = F.from_float(record["external_work"])
    conditional = required_signed_change(Interval.point(d0), Interval.point(external))
    return {"status": "historical_scalar_requirements_only_not_candidate_prediction",
            "metadata_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "old_product_defect_J": str(d0), "old_external_J": str(external),
            "required_signed_change_zero_uncertainty_unchanged_external_J":
                {"lo": str(conditional.lo), "hi": str(conditional.hi)},
            "missing": ["current original-target factor response and raw signed linear/quadratic contractions",
                        "candidate external-work change/evaluation bound",
                        "base/current action and reconstruction/update/restoration bounds",
                        "original per-row response and unchanged candidate tolerance enclosures"],
            "qualification": False, "operator_payloads_read": 0, "solves": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-requirements", action="store_true")
    args = parser.parse_args()
    if not args.historical_requirements:
        parser.error("explicit scalar-metadata mode required; no default model/check execution")
    print(json.dumps(historical_requirements(), indent=2, sort_keys=True))

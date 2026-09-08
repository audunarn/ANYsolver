"""Explicit symmetric-energy audit of supplied virgin compliance, research only."""
from fractions import Fraction
import numpy as np
from docs.reference_cases.ge_beam3_generalized_virgin_chain import virgin_chain

def energy_chain(high,low,residual):
    high=np.array(high,dtype=float,copy=True);low=np.array(low,dtype=float,copy=True)
    residual=np.array(residual,dtype=float,copy=True)
    if high.shape!=(42,42) or low.shape!=(42,42) or residual.shape!=(42,):
        raise ValueError('complete generalized virgin blocks')
    if not all(np.isfinite(a).all() for a in (high,low,residual)):
        raise ValueError('finite generalized virgin blocks')
    h=high+low
    if not np.array_equal(h[:24,24:].T,h[24:,:24]):
        raise ValueError('exact work-conjugate kinematic blocks required')
    s=-h[24:,24:];symmetric=np.empty_like(s);rounding=Fraction(0)
    for i in range(18):
        for j in range(i,18):
            exact=(Fraction(float(s[i,j]))+Fraction(float(s[j,i])))/2
            value=float(exact);symmetric[i,j]=symmetric[j,i]=value
            rounding=max(rounding,abs(Fraction(value)-exact))
    report=dict(maximum_compliance_skew=float(np.max(abs(s-s.T))),
        normalized_compliance_skew=float(np.linalg.norm(s-s.T)/max(1.,np.linalg.norm(s))),
        maximum_mean_rounding_error_numerator=str(rounding.numerator),
        maximum_mean_rounding_error_denominator=str(rounding.denominator),
        supplied_force_operator_modified=False,energy_symmetric_part_only=True)
    h[24:,24:]=-symmetric
    left,right,compliance=virgin_chain(h,np.zeros_like(h),residual)
    return left,right,compliance,report

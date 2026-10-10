"""Exact sufficiency counterexample, not an emulation of native SuperLU."""
from fractions import Fraction as Q
import json
import sys
from pathlib import Path
import numpy as np
from prepared_static_response_m10_bounds import ZERO,ONE,UNIT,TINY,rational,upward

def admitted(T,x,b):
    """Check the frozen M12 residual relation on the candidate itself."""
    n=len(x);count=2*n+2;g=count*UNIT/(ONE-count*UNIT)
    rows=[]
    for i,row in enumerate(T):
        residual=abs(sum((a*v for a,v in zip(row,x)),ZERO)-b[i])
        allowance=g*(sum((abs(a)*abs(v) for a,v in zip(row,x)),ZERO)+abs(b[i]))+count*TINY*(ONE+abs(row[i]))/(ONE-count*UNIT)
        rows.append((residual,allowance))
    return all(r<=a for r,a in rows),rows

def exact_dot(w,x):return sum((a*v for a,v in zip(w,x)),ZERO)

def counterexample(sign=1):
    M=Q(2)**20;epsilon=Q(2)**-31
    T=[[ONE,M],[ZERO,ONE]];b=[ZERO,Q(sign)]
    center=[-Q(sign)*M,Q(sign)]
    candidate=[center[0]+Q(sign)*epsilon,center[1]]
    assert all(rational(float(x))==x for x in candidate+b)
    okay,rows=admitted(T,candidate,b)
    assert okay
    output_row=[ONE,M]
    exact_output=exact_dot(output_row,center)
    adversarial_output=exact_dot(output_row,candidate)
    assert exact_output==ZERO and abs(adversarial_output)==epsilon
    assert epsilon>rational(1e-12)+rational(1e-12)*abs(exact_output)
    # All values, products and final cancellation in this scalar expression
    # are exactly representable. Native triangular solve is not executed.
    actual_expression=float(candidate[0])+float(M)*float(candidate[1])
    assert rational(actual_expression)==adversarial_output
    return {'signed_load':sign,'operation_count':6,'triangular_condition':'unit diagonal; exactly represented power-of-two offdiagonal',
        'candidate_is_binary64':True,'frozen_relation_admitted':okay,
        'row_residuals':[upward(r) for r,a in rows],
        'row_allowances':[upward(a) for r,a in rows],
        'exact_output':float(exact_output),'adversarial_output':float(adversarial_output),
        'output_error':upward(epsilon),'output_target':1e-12,
        'actual_native_result_not_claimed':True}

def controls():
    T=[[ONE,ZERO],[ZERO,ONE]];b=[ONE,ONE]
    assert admitted(T,b,b)[0]
    assert not admitted(T,[ONE+Q(1,1000),ONE],b)[0]
    large=rational(1e308);small=rational(1e-20)
    assert admitted([[large]],[ZERO],[small])[0]
    assert small>4*TINY
    return {'exact_solution_admitted':True,'excessive_identity_error_refused':True,'diagonal_scaled_underflow_required':True}

if __name__=='__main__':
    result={'status':'NO_GO_FOR_SUFFICIENCY_OF_DECLARED_RELATION','claim':'Frozen generic componentwise native residual relation permits output errors above target; actual gstrs/vendor behavior remains undetermined',
        'counterexamples':[counterexample(1),counterexample(-1)],'controls':controls(),
        'no_native_solve_or_intermediate_observed':True,'no_gamma_reduction':True}
    Path(sys.argv[1]).write_text(json.dumps(result,indent=2));print(json.dumps(result))

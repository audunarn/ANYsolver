"""Saved-only attribution of exact and floating classical pose representations."""
from __future__ import annotations

from fractions import Fraction
import json
import math
import re

import numpy as np
from numpy.polynomial import legendre

import _b3_e4_f03_primal_exact_pose as exact
import _b3_e4_f03_primal_ritz as constants


SCHEMA='primal_exact_saved_pose_attribution_v1'
MAX_JSON_BYTES=16*1024**2
MAX_RATIONAL_PAIRS=2048
TERM_NAMES=('total','floating_polynomial','coefficient_reconstruction','direct_action')
ROOT_KEYS={'schema','n','term_names','diagnostic_status','checks',
           'original_full_saved_action','derivative_binding','pose',
           'oracle_stations','terms','rounding_remainders','endpoint_weights',
           'endpoint_bounds','floating','attribution_on_original_scale'}


def _pair(value: Fraction) -> list[str]:
    return [str(value.numerator),str(value.denominator)]


def _parse_pair(pair) -> Fraction:
    if (type(pair) is not list or len(pair)!=2 or
            any(type(part) is not str or len(part)>4096 or
                re.fullmatch(r'(?:0|-?[1-9][0-9]*)',part) is None for part in pair)):
        raise ValueError('noncanonical bounded rational pair')
    numerator,denominator=map(int,pair)
    if denominator<=0:
        raise ValueError('nonpositive rational denominator')
    value=Fraction(numerator,denominator)
    if _pair(value)!=pair:
        raise ValueError('nonreduced rational pair')
    return value


def _rational_array(value,shape) -> int:
    if not shape:
        _parse_pair(value)
        return 1
    if type(value) is not list or len(value)!=shape[0]:
        raise ValueError('wrong exact attribution dimensions')
    return sum(_rational_array(item,shape[1:]) for item in value)


def _float_array(value,shape) -> None:
    if not shape:
        if type(value) is not float or not math.isfinite(value):
            raise ValueError('invalid exact attribution display')
        return
    if type(value) is not list or len(value)!=shape[0]:
        raise ValueError('wrong floating attribution dimensions')
    for item in value:
        _float_array(item,shape[1:])


def validate_payload(record: dict,n: int) -> None:
    """Validate exact dimensions and rational syntax before numerical reuse."""
    if (type(n) is not int or not 2<=n<=24 or type(record) is not dict or
            set(record)!=ROOT_KEYS or record['schema']!=SCHEMA or
            type(record['n']) is not int or record['n']!=n or
            record['term_names']!=list(TERM_NAMES) or
            record['diagnostic_status'] not in
            ('PASSED_REPRESENTATION_DIAGNOSTIC','FAILED_DIAGNOSTIC_IDENTITY')):
        raise ValueError('invalid exact attribution inventory')
    pose=record['pose']
    if (type(pose) is not dict or
            set(pose)!={'schema','n','geometry','q','tau_power','legendre'} or
            pose['schema']!=exact.SCHEMA or type(pose['n']) is not int or
            pose['n']!=n or type(pose['geometry']) is not dict or
            set(pose['geometry'])!={'dx','dy','a','held_J','J_geom','gamma'}):
        raise ValueError('invalid exact pose metadata')
    count=sum(_rational_array(pair,()) for pair in pose['geometry'].values())
    count+=_rational_array(pose['q'],(2*(n*n-1),))
    count+=_rational_array(pose['tau_power'],(3,n+1))
    count+=_rational_array(pose['legendre'],(3,n+1))
    for key,shape in (('oracle_stations',(3,9,3)),('terms',(3,9,3,4)),
            ('rounding_remainders',(3,9,3)),
            ('endpoint_weights',(2,2,n+1)),('endpoint_bounds',(2,2,3,2))):
        count+=_rational_array(record[key],shape)
    if count>MAX_RATIONAL_PAIRS:
        raise ValueError('exact attribution exceeds rational count bound')
    floating=record['floating']
    if (type(floating) is not dict or set(floating)!=
            {'polynomial','direct','subtraction','normalized_difference','normalizers'}):
        raise ValueError('invalid floating replay inventory')
    for key in ('polynomial','direct','subtraction','normalized_difference'):
        _float_array(floating[key],(3,9,3))
    _float_array(floating['normalizers'],(3,))
    _float_array(record['attribution_on_original_scale'],(3,9,3,4))
    checks=record['checks']
    if (type(checks) is not dict or set(checks)!=
            {'exact_representation_agreement','exact_three_term_closure',
             'exact_endpoint_identity','valid_endpoint_triangle_bounds',
             'held_source_geometry'} or any(type(v) is not bool for v in checks.values())):
        raise ValueError('invalid exact identity checks')
    expected=('PASSED_REPRESENTATION_DIAGNOSTIC' if all(checks.values()) else
              'FAILED_DIAGNOSTIC_IDENTITY')
    if record['diagnostic_status']!=expected:
        raise ValueError('contradictory exact identity status')
    original=record['original_full_saved_action']
    if (type(original) is not dict or set(original)!=
            {'source','value','limit','case_status'} or
            original['source']!='immutable_saved_audit' or
            type(original['value']) is not float or
            not math.isfinite(original['value']) or original['value']<0 or
            type(original['limit']) is not float or original['limit']!=1e-11 or
            original['case_status'] not in
            ('PASSED_NUMERICAL_SCREEN','FAILED_NUMERICAL_SCREEN')):
        raise ValueError('invalid retained original metric')
    derivative=record['derivative_binding']
    if (type(derivative) is not dict or set(derivative)!=
            {'per_order_max','value','limit','passes_original_limit'}):
        raise ValueError('invalid derivative submetric inventory')
    _float_array(derivative['per_order_max'],(3,))
    if (type(derivative['value']) is not float or
            derivative['value']!=max(derivative['per_order_max']) or
            type(derivative['limit']) is not float or derivative['limit']!=1e-11 or
            type(derivative['passes_original_limit']) is not bool or
            derivative['passes_original_limit']!=(derivative['value']<=1e-11)):
        raise ValueError('contradictory derivative submetric')
    # Fixed dimensions, scalar types and digit lengths above bound this
    # allocation. File readers apply the byte bound before JSON parsing.
    if len(json.dumps(record,allow_nan=False).encode('utf-8'))>MAX_JSON_BYTES:
        raise ValueError('exact attribution exceeds JSON byte bound')


def evaluate_saved(n: int,arrays: dict,original_decision: dict) -> dict:
    """Reconstruct polynomials only; never project, assemble or solve."""
    if type(n) is not int or not 2<=n<=24:
        raise ValueError('invalid exact attribution degree')
    d=2*(n*n-1)
    for key,shape in (('q',(d,)),('b_coefficients',(n+1,3)),
                      ('station_A',(9,3,d)),('station_A1',(9,3,d)),
                      ('station_A2',(9,3,d))):
        value=arrays[key]
        if (not isinstance(value,np.ndarray) or value.dtype!=np.float64 or
                value.shape!=shape or not np.isfinite(value).all()):
            raise ValueError(f'invalid saved exact attribution input: {key}')
    q=arrays['q'];saved=arrays['b_coefficients']
    pose=exact.reconstruct(n,q)
    oracle=exact.station_derivatives(pose)
    independent=exact.station_derivatives_legendre(pose)
    stations=np.array([float(s) for s in exact.STATIONS])
    # This is the original derivative-binding arithmetic, including its
    # global per-order denominator and the characteristic length once.
    scale=np.diag((1/constants.U0,1/constants.U0,
                   constants.YAW_LENGTH/constants.U0))
    floating={key:[] for key in ('polynomial','direct','subtraction',
                                 'normalized_difference','normalizers')}
    terms=[];remainders=[];attribution=[];derivative_max=[]
    closure=True
    for order,key in enumerate(('station_A','station_A1','station_A2')):
        polynomial=np.stack([legendre.legval(2*stations-1,
            legendre.legder(saved[:,channel],m=order))*2**order
            for channel in range(3)],axis=-1)
        direct=arrays[key]@q
        scaled_reference=(constants.L0**order)*(polynomial@scale.T)
        scaled_observed=(constants.L0**order)*(direct@scale.T)
        denominator=max(1.,float(np.max(np.abs(scaled_observed))),
                        float(np.max(np.abs(scaled_reference))))
        normalized=(scaled_reference-scaled_observed)/denominator
        # Preserve the original max-before-division order, rather than
        # substituting max(normalized) in the retained floating submetric.
        derivative_max.append(float(np.max(np.abs(
            scaled_observed-scaled_reference))/denominator))
        for values in (polynomial,direct,normalized):
            if not np.isfinite(values).all():
                raise ValueError('nonfinite saved floating pose replay')
        floating['polynomial'].append(polynomial.tolist())
        floating['direct'].append(direct.tolist())
        floating['subtraction'].append((polynomial-direct).tolist())
        floating['normalized_difference'].append(normalized.tolist())
        floating['normalizers'].append(denominator)
        order_terms=[];order_remainders=[];order_attribution=[]
        for station in range(9):
            station_terms=[];station_remainders=[];station_attribution=[]
            for channel in range(3):
                split=exact.decompose_discrepancy(saved,pose,channel,order,station,
                    float(polynomial[station,channel]),float(direct[station,channel]))
                values=[getattr(split,name) for name in TERM_NAMES]
                closure &= sum(values[1:],Fraction(0))==values[0]
                station_terms.append([_pair(value) for value in values])
                subtraction=float(polynomial[station,channel]-direct[station,channel])
                station_remainders.append(_pair(Fraction.from_float(subtraction)-values[0]))
                factor=(constants.L0**order)*scale[channel,channel]/denominator
                station_attribution.append([float(float(value)*factor) for value in values])
            order_terms.append(station_terms)
            order_remainders.append(station_remainders)
            order_attribution.append(station_attribution)
        terms.append(order_terms);remainders.append(order_remainders)
        attribution.append(order_attribution)
    endpoint_weights=[];endpoint_bounds=[];endpoint_identity=True;triangle=True
    for order in (1,2):
        order_weights=[];order_bounds=[]
        for endpoint in (0,1):
            bounds=[exact.endpoint_coefficient_bound(saved,pose,channel,order,endpoint)
                    for channel in range(3)]
            order_weights.append([_pair(w) for w in bounds[0].weights])
            order_bounds.append([[_pair(b.signed),_pair(b.triangle)] for b in bounds])
            for channel,bound in enumerate(bounds):
                coefficient_term=_parse_pair(terms[order][endpoint*8][channel][2])
                endpoint_identity &= bound.signed==coefficient_term
                triangle &= abs(bound.signed)<=bound.triangle
        endpoint_weights.append(order_weights);endpoint_bounds.append(order_bounds)
    checks={'exact_representation_agreement':oracle==independent,
            'exact_three_term_closure':bool(closure),
            'exact_endpoint_identity':bool(endpoint_identity),
            'valid_endpoint_triangle_bounds':bool(triangle),
            'held_source_geometry':pose.held_J==Fraction.from_float(constants.J) and
                pose.dx==Fraction.from_float(.2) and
                pose.dy==Fraction.from_float(.23) and
                pose.a==Fraction.from_float(constants.HALFWIDTH) and
                pose.J_geom==pose.dx**2+pose.dy**2+2*pose.a**2/3 and
                pose.gamma==pose.J_geom/pose.held_J}
    full=original_decision['reproduced_decision']['metrics']['checks'][
        'saved_action_parity_scaled']
    record={'schema':SCHEMA,'n':n,'term_names':list(TERM_NAMES),
        'diagnostic_status':('PASSED_REPRESENTATION_DIAGNOSTIC' if all(checks.values())
                             else 'FAILED_DIAGNOSTIC_IDENTITY'),
        'checks':checks,'original_full_saved_action':{
            'source':'immutable_saved_audit','value':float(full),'limit':1e-11,
            'case_status':original_decision['status']},
        'derivative_binding':{'per_order_max':derivative_max,
            'value':max(derivative_max),'limit':1e-11,
            'passes_original_limit':max(derivative_max)<=1e-11},
        'pose':exact.to_record(pose),
        'oracle_stations':[[[_pair(v) for v in station] for station in order]
                           for order in oracle],
        'terms':terms,'rounding_remainders':remainders,
        'endpoint_weights':endpoint_weights,'endpoint_bounds':endpoint_bounds,
        'floating':floating,'attribution_on_original_scale':attribution}
    validate_payload(record,n)
    return record


def _identical(observed,expected,path='root') -> None:
    if type(observed) is not type(expected):
        raise ValueError(f'exact diagnostic type changed: {path}')
    if isinstance(expected,dict):
        if set(observed)!=set(expected):
            raise ValueError(f'exact diagnostic inventory changed: {path}')
        for key,value in expected.items():
            _identical(observed[key],value,path+'/'+str(key))
    elif isinstance(expected,list):
        if len(observed)!=len(expected):
            raise ValueError(f'exact diagnostic length changed: {path}')
        for index,value in enumerate(expected):
            _identical(observed[index],value,path+'/'+str(index))
    elif isinstance(expected,float):
        if not math.isfinite(observed) or observed.hex()!=expected.hex():
            raise ValueError(f'exact diagnostic floating value changed: {path}')
    elif observed!=expected:
        raise ValueError(f'exact diagnostic value changed: {path}')


def verify_saved_record(record: dict,n: int,arrays: dict,
                        original_decision: dict) -> dict:
    validate_payload(record,n)
    recomputed=evaluate_saved(n,arrays,original_decision)
    _identical(record,recomputed)
    return recomputed

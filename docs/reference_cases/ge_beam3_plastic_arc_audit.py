"""Independent station KKT audit; standard library and independent oracle only."""
from hashlib import sha256
from math import fsum, isfinite, sqrt
from docs.reference_cases.ge_beam3_generalized_ellipsoid_oracle import response
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical, strict_bytes
from docs.reference_cases.ge_beam3_plastic_arc_fixture import fixture

TOLERANCE = 1e-11

def vector(value, n):
    if type(value) is not list or len(value) != n or any(type(x) is not float or not isfinite(x) for x in value):
        raise ValueError('finite binary64 vector')
    return value

def paired(value, n):
    if type(value) is not list or len(value) != 2:
        raise ValueError('two high/low vectors')
    a, b = (vector(v, n) for v in value)
    return [fsum((x, y)) for x, y in zip(a, b)]

def error(actual, expected):
    if len(actual) != len(expected):
        raise ValueError('comparison extent')
    e = sqrt(fsum((a-b)**2 for a, b in zip(actual, expected)))/max(1., sqrt(fsum(b*b for b in expected)))
    if not isfinite(e) or e > TOLERANCE:
        raise ValueError('independent material disagreement: '+str(e))
    return e

def station(section, data, origin, history):
    if set(data) != {'material', 'tangent', 'tangent_strain', 'tangent_resultants', 'tangent_origin'}:
        raise ValueError('exact station packet')
    if canonical(data['tangent_origin']) != canonical(origin):
        raise ValueError('original increment origin required')
    m = data['material']
    if set(m) != {'strain','resultants','dual_potential','incremental_potential','stored_energy','dissipation','plastic_increment','branch','recovery_policy'}:
        raise ValueError('exact material station')
    if m['branch'] not in ('ELASTIC', 'PLASTIC'):
        raise ValueError('smooth material branch required')
    if m['recovery_policy'] != 'RESULTANT_LEVEL_ONLY_NO_FIBRE_STRESSES_SUPPLIED':
        raise ValueError('resultant-only recovery authority')
    for h in (origin, history):
        if set(h) != {'section_identity', 'plastic', 'accumulated'} or len(h['plastic']) != 6:
            raise ValueError('complete generalized station history')
        for v in h['plastic']:
            vector(v, 2)
        vector(h['accumulated'], 2)
    if origin['section_identity'] != history['section_identity']:
        raise ValueError('same station section identity')
    strain = paired(m['strain'], 6); force = paired(m['resultants'], 6)
    expected = response(dict(elastic=section['elastic'], metric=section['metric'],
        strain=strain, plastic=origin['plastic'], accumulated=origin['accumulated'],
        yield_force=section['yield_force'], hardening=section['hardening']))
    if expected['branch'] != m['branch']:
        raise ValueError('independent active-branch disagreement')
    errors = [error(force, expected['stress']),
              error([fsum(v) for v in history['plastic']], expected['plastic']),
              error([fsum(history['accumulated'])], [expected['accumulated']])]
    for key, other in (('plastic_increment','increment'), ('incremental_potential','potential'),
                       ('stored_energy','stored_energy'), ('dissipation','dissipation')):
        errors.append(error(paired(m[key], 1), [expected[other]]))
    increment = paired(m['plastic_increment'], 1)[0]
    dissipation = paired(m['dissipation'], 1)[0]
    if increment < 0. or dissipation < 0. or fsum(history['accumulated']) < fsum(origin['accumulated']):
        raise ValueError('irreversible history decreased')
    errors.append(error([fsum(history['accumulated'])-fsum(origin['accumulated'])], [increment]))
    errors.append(error(paired(data['tangent_strain'], 6), strain))
    errors.append(error(paired(data['tangent_resultants'], 6), force))
    # The tangent sample is evaluated at the rounded binary64 station resultant,
    # not silently presented as an exact high/low constitutive derivative.
    if type(data['tangent']) is not list or len(data['tangent']) != 2:
        raise ValueError('paired tangent')
    for part in data['tangent']:
        if type(part) is not list or len(part) != 6:
            raise ValueError('six tangent rows')
        for row in part:
            vector(row, 6)
    actual_tangent = [fsum((data['tangent'][0][i][j],data['tangent'][1][i][j])) for i in range(6) for j in range(6)]
    errors.append(error(actual_tangent, [x for row in expected['tangent'] for x in row]))
    # Fenchel identity independently checks the stored dual station energy.
    errors.append(error(paired(m['dual_potential'], 1), [fsum(a*b for a,b in zip(strain,force))-expected['potential']]))
    return dict(active=increment > 0., branch=m['branch'], maximum_error=max(errors))

def audit(packet, checkpoint_raw, revision, macros):
    if set(packet) != {'schema','revision','fixture','checkpoint_sha256','steps','production_qualified'}:
        raise ValueError('exact active-plastic capture schema')
    f = fixture(macros)
    if (packet['schema'] != 'GE_BEAM3_PLASTIC_ARC_CAPTURE_V1' or packet['revision'] != revision
            or canonical(packet['fixture']) != canonical(f) or packet['production_qualified'] is not False
            or packet['checkpoint_sha256'] != sha256(checkpoint_raw).hexdigest()):
        raise ValueError('fixture/checkpoint/candidate authority')
    cp = strict_bytes(checkpoint_raw)
    if type(cp['completed_steps']) is not int or cp['completed_steps'] != 3 or len(cp['records']) != 3 or len(packet['steps']) != 3:
        raise ValueError('all three accepted steps required')
    if canonical(cp['program']) != canonical(dict(steps=f['steps'], length_scale=f['length_scale'], parameter_scale=f['parameter_scale'],
            initial_sign=f['initial_sign'], max_iterations=24, max_backtracks=8, nodal_forces=dict(rows=[f['force']]))):
        raise ValueError('same complete programme')
    if cp['schema'] != 'GE_BEAM3_RETAINED_FRAME_CHORD_ACCEPTED_CHAIN_V1':
        raise ValueError('arc-owned checkpoint required')
    if sha256(canonical({k:v for k,v in cp.items() if k != 'checkpoint_sha256'})).hexdigest() != cp['checkpoint_sha256']:
        raise ValueError('checkpoint body hash')
    for record in [cp['initial'], *cp['records']]:
        if sha256(canonical({k:v for k,v in record.items() if k != 'record_sha256'})).hexdigest() != record['record_sha256']:
            raise ValueError('record body hash')
    summary = []; predecessor = cp['initial']
    for index, (record, captured) in enumerate(zip(cp['records'], packet['steps']), 1):
        if (set(captured) != {'step','record_sha256','elements'} or type(captured['step']) is not int
                or captured['step'] != index or captured['record_sha256'] != record['record_sha256']
                or type(record['step']) is not int or record['step'] != index or record['step_size'] != f['steps'][index-1]):
            raise ValueError('actual accepted record binding')
        if canonical(record['origins']) != canonical(predecessor['histories']):
            raise ValueError('original history continuity')
        if record['previous_sha256'] != predecessor['record_sha256']:
            raise ValueError('record chain')
        metrics = vector(record['metrics'], 2)
        vector([record['arc_gap'],record['correction']], 2)
        if min(*metrics,record['correction']) < 0. or max(*metrics, abs(record['arc_gap']), record['correction']) > TOLERANCE:
            raise ValueError('actual full equilibrium required')
        if len(captured['elements']) != macros or len(record['origins']) != macros or len(record['histories']) != macros:
            raise ValueError('all elements required')
        rows = []
        for i, element in enumerate(captured['elements']):
            if set(element) != {'element_id','stations'} or element['element_id'] != i+1 or len(element['stations']) != 8:
                raise ValueError('all eight stations per macro')
            origins = record['origins'][i]['stations']; histories = record['histories'][i]['stations']
            if len(origins) != 8 or len(histories) != 8:
                raise ValueError('complete station histories')
            rows.extend(station(f, data, origin, history) for data, origin, history in zip(element['stations'], origins, histories, strict=True))
        active = sum(v['active'] for v in rows)
        if not active:
            raise ValueError('every smoke increment must actually be plastic')
        summary.append(dict(step=index, stations=len(rows), active_stations=active, maximum_error=max(v['maximum_error'] for v in rows)))
        predecessor = record
    return dict(schema='GE_BEAM3_PLASTIC_ARC_SMOKE_RESULT_V1', revision=revision, macros=macros,
        fixture_sha256=sha256(canonical(f)).hexdigest(), checkpoint_sha256=sha256(checkpoint_raw).hexdigest(),
        steps=summary, terminal='PRIVATE_ACTIVE_PLASTIC_ARC_MATERIAL_SMOKE_PASS',
        independent_review='PENDING', production_qualified=False, restart_cancellation_qualified=False)

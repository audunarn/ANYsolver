"""Bounded development diagnostic; no native integration/qualification authority."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = '0fd9d3a27ad3c385d8d616f25ce5058841d89c5c'
SOURCES = ('src/anysolver/ge_beam3_curved_reference.py',
    'src/anysolver/_ge_beam3_mixed_ad.py',
    'src/anysolver/_ge_beam3_centered_reference.py',
    'src/anysolver/_ge_beam3_centered_mixed.py',
    'docs/reference_cases/ge_beam3_curved_p5_package_source_map.json',
    'docs/reference_cases/ge_beam3_curved_p5_coordinate_source_map.json')


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False)+'\n').encode('ascii')


def bindings():
    result = {}
    for path in SOURCES:
        raw = (ROOT/path).read_text(encoding='utf-8').encode('utf-8')
        result[path] = dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    # Verify preserved package modules before importing any mechanics.
    for manifest in SOURCES[-2:]:
        for path, expected in json.loads((ROOT/manifest).read_text())['outputs'].items():
            raw = (ROOT/path).read_text(encoding='utf-8').encode('utf-8')
            if dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) != expected:
                raise ValueError('preserved candidate source mismatch: '+path)
    return result


def run():
    bound = bindings()
    import numpy as np
    from anysolver.ge_beam3_curved_reference import CurvedBeam3ReferenceGeometry as Old
    from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as New
    from anysolver._ge_beam3_centered_mixed import CenteredStationaryBeam
    from anysolver._ge_beam3_p5.section import DirectedHardeningSection
    from anysolver._ge_beam3_p5.mixed import LocalForceAccuracy
    from anysolver._ge_beam3_p5.core import sha
    from anysolver._ge_beam3_p5_coordinates.positions import from_total
    nodes = np.array([[-1.,0.,0.],[0.,.5,0.],[1.,0.,0.]])
    frames = []
    for xi in (-1.,0.,1.):
        axis = np.array([1.,-xi,0.]); axis /= np.linalg.norm(axis)
        second = np.array([0.,0.,1.])
        frames.append(np.column_stack((axis,second,np.cross(axis,second))))
    frames = np.array(frames); old = Old(nodes,frames); new = New(nodes,frames)
    shifts = (0.,2.**20,2.**30,2.**40,-2.**40)
    gauss = np.polynomial.legendre.leggauss(8)[0]
    records = []
    for shift in shifts:
        old_shift = Old(nodes+shift,frames); new_shift = New(nodes+shift,frames)
        derivative_error = max(np.linalg.norm(old_shift.derivative(x)-old.derivative(x)) for x in gauss)
        old_lift_error = 0.; stable_exact = True
        for cell in (0,1):
            for point in gauss:
                t = float((point+1)/2); xi = cell-1+t
                baseline = old.position(xi)-((1-t)*nodes[cell]+t*nodes[cell+1])
                moved = old_shift.position(xi)-((1-t)*(nodes+shift)[cell]+t*(nodes+shift)[cell+1])
                old_lift_error = max(old_lift_error,float(np.linalg.norm(moved-baseline)))
                stable_exact &= np.array_equal(new_shift.half_cell_lift(cell,t),new.half_cell_lift(cell,t))
                for method in ('derivative','frame','frame_derivative'):
                    stable_exact &= np.array_equal(getattr(new_shift,method)(xi),getattr(new,method)(xi))
        if not stable_exact: raise ValueError('centered geometry lost exact-translation invariance')
        records.append(dict(shift_hex=shift.hex(),old_derivative_error_hex=float(derivative_error).hex(),
            old_lift_error_hex=old_lift_error.hex(),centered_geometry_byte_identical=True))
    operator_records = []
    total = np.array([[.01,-.02,.03,0.,0.,0.],[.04,.03,-.02,0.,0.,0.],[-.01,.04,.02,0.,0.,0.]]).ravel()
    for plastic in (False,True):
        section = DirectedHardeningSection(np.diag([4.,9.,16.,1.,2.,4.]),
            np.array([1.,.2,-.1,.3,-.4,.5]),.02 if plastic else 1000.,.4)
        hashes = []
        for shift in shifts:
            ref = New(nodes+shift,frames)
            high, low = from_total(ref.coordinates,total,ref.coordinates+total.reshape(3,6)[:,:3])
            beam = CenteredStationaryBeam(ref,section,order=8,position_low=low,line_force=np.array([.001,-.002,.001]))
            response = beam.solve(high,frames,force_accuracy=LocalForceAccuracy(1e-12,2.))
            if any(s.response.plastic_active for s in response.stations) != plastic:
                raise ValueError('registered material branch was not exercised')
            hashes.append(sha(response))
        if len(set(hashes)) != 1: raise ValueError('translated stationary responses disagree')
        operator_records.append(dict(material='plastic' if plastic else 'elastic',
            translated_response_sha256=hashes,all_translations_byte_identical=True))
    if bindings() != bound: raise ValueError('source inputs changed during diagnostic')
    return dict(schema='GE_BEAM3_CENTERED_REFERENCE_OPERATOR_DIAGNOSTIC_V1',base_commit=BASE,
        disposition='DEVELOPMENT_CENTERED_REFERENCE_AND_LOCAL_OPERATOR_CHECKED',source_bindings=bound,
        geometry_records=records,operator_records=operator_records,
        native_package_adoption_complete=False,production_qualified=False,
        independent_review_status='PENDING',historical_evidence_reclassified=False)


if __name__ == '__main__':
    print(canonical(run()).decode('ascii'),end='')

"""Small deterministic development check; stdout only, no execution authority."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = '326ad849ba29f8fc9f0a40ca7da6483f97f55d40'
MAP = 'docs/reference_cases/ge_beam3_centered_native_source_map.json'
MAP_SHA = '5f6a8cbfce0b6a05eb7839b1db8541d89b0284e66516c2d1748c39f66dbd0493'
SOURCES = ('docs/reference_cases/ge_beam3_centered_line_load_oracle.py',
           'docs/reference_cases/ge_beam3_centered_line_load_probe.py',
           'docs/reference_cases/ge_beam3_centered_line_load_diagnostic.py')


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')


def binding(path):
    raw = (ROOT/path).read_text(encoding='utf-8').encode('utf-8')
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def bindings():
    if binding(MAP)['sha256'] != MAP_SHA: raise ValueError('preserved centered source map changed')
    for path, expected in json.loads((ROOT/MAP).read_text())['outputs'].items():
        if binding(path) != expected: raise ValueError('preserved source changed: '+path)
    return {path:binding(path) for path in (*SOURCES,MAP)}


def run():
    bound = bindings()
    import numpy as np
    from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as Centered
    from anysolver._ge_beam3_p5.section import DirectedHardeningSection, SectionHistory
    from anysolver._ge_beam3_p5.algebra import rotation
    from anysolver._ge_beam3_p5.core import sha
    from anysolver._ge_beam3_p5_coordinates.positions import from_total
    from docs.reference_cases import ge_beam3_centered_line_load_probe as probe
    from docs.reference_cases import ge_beam3_centered_line_load_oracle as oracle
    factor = np.array([[2.,.1,0.,.2,-.1,0.],[0.,3.,.2,0.,.3,.1],[0.,0.,4.,.1,0.,.2],
                       [0.,0.,0.,1.,.1,.2],[0.,0.,0.,0.,1.5,.1],[0.,0.,0.,0.,0.,2.]])
    total = np.array([[.01,-.02,.03,.04,-.02,.06],[.04,.03,-.02,-.03,.05,.02],[-.01,.04,.02,.02,.03,-.04]])
    force = np.array([.03,-.02,.01]); records = []
    origins = tuple(SectionHistory(.0001*i,.0002*i) for i in range(16))
    for curved in (False,True):
        nodes = np.array([[-1.,0.,0.],[0.,.5 if curved else 0.,.25 if curved else 0.],[1.,0.,0.]])
        frames = []
        for xi in (-1.,0.,1.):
            a = np.array([1.,-xi if curved else 0.,-.5*xi if curved else 0.]); a /= np.linalg.norm(a)
            b = np.array([0.,0.,1.]); b -= a*float(a@b); b /= np.linalg.norm(b)
            frames.append(np.column_stack((a,b,np.cross(a,b))))
        frames = np.array(frames); vertex = np.array([rotation(v)@q for v,q in zip(total[:,3:],frames)])
        for plastic in (False,True):
            section = DirectedHardeningSection(factor.T@factor,np.array([1.,.2,-.1,.3,-.4,.5]),.02 if plastic else 1000.,.4)
            def solve(parameter,shift=0.):
                ref = Centered(nodes+shift,frames)
                high,low = from_total(ref.coordinates,total.ravel(),ref.coordinates+total[:,:3])
                return probe.evaluate(ref,section,high,low,vertex,force,parameter,order=8,origins=origins)
            base = solve(.7); plus = solve(.70001); minus = solve(.69999)
            if any(base.branch) != plastic or not base.branch == plus.branch == minus.branch:
                raise ValueError('smooth registered branch not exercised')
            expected = oracle.evaluate(nodes,total[:,:3],base.response.local_rotations,force)
            errors = dict(work=abs(base.unit_work-expected.work),
                augmented_force=float(np.linalg.norm(base.augmented_unit_force-expected.force)),
                work_hessian=float(np.linalg.norm(base.augmented_unit_work_hessian-expected.hessian)),
                parameter_force=float(np.linalg.norm((plus.response.residual-minus.response.residual)/.00002-base.residual_parameter_derivative)),
                parameter_work=abs((plus.response.potential-minus.response.potential)/.00002-base.potential_parameter_derivative),
                parameter_second=abs((plus.potential_parameter_derivative-minus.potential_parameter_derivative)/.00002-base.potential_parameter_second_derivative))
            for name,error in errors.items():
                if error > (1e-7 if name.startswith('parameter') else 1e-11):
                    raise ValueError('load reconstruction/parameter derivative failed: '+name)
            correction = float(np.linalg.norm(base.residual_parameter_derivative+base.augmented_unit_force[:18]))
            if (curved and correction <= 1e-5) or (not curved and correction > 1e-11):
                raise ValueError('internal load-work distinction failed')
            hashes = [sha(base),sha(solve(.7,2.**30)),sha(solve(.7,2.**40))]
            if len(set(hashes)) != 1: raise ValueError('exact translations disagree')
            records.append(dict(geometry='curved' if curved else 'straight',material='plastic' if plastic else 'elastic',
                response_sha256=hashes[0],errors_hex={k:float(v).hex() for k,v in errors.items()},
                internal_load_correction_norm_hex=correction.hex(),all_translations_byte_identical=True,
                station_count=len(base.branch),plastic_station_count=sum(base.branch)))
    if bindings() != bound: raise ValueError('inputs changed during development diagnostic')
    return dict(schema='GE_BEAM3_CENTERED_DEAD_LINE_DEVELOPMENT_V1',base_commit=BASE,
        disposition='DEVELOPMENT_LOAD_WORK_AND_PARAMETER_SCHUR_CHECKED',source_bindings=bound,records=records,
        policy=probe.POLICY,production_qualified=False,native_load_integration_complete=False,
        independent_review_status='PENDING',historical_evidence_reclassified=False)


if __name__ == '__main__':
    print(canonical(run()).decode('ascii'),end='')

"""Compare saved manufactured shell states with a continuous independent oracle.

No production solve is performed. This is a development discriminator, not an
acceptance runner or a general shell/material reference.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tests'))
from reference_oblique_q4_plateau import continuous_reference, H, YIELD, MASS, STATE_SCALES


def compare(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    times = np.asarray(data['times_s'])
    reference = continuous_reference(times)
    q, v = np.asarray(data['q']), np.asarray(data['v'])
    p, alpha = np.asarray(data['plastic_xx']), np.asarray(data['alpha'])
    if not (q.shape == v.shape == reference.q.shape and p.shape == alpha.shape == times.shape
            and np.all(np.isfinite(np.r_[q.ravel(),v.ravel(),p,alpha]))):
        raise ValueError('invalid saved manufactured state arrays')
    if np.max(alpha) >= .005:
        raise ValueError('saved field exceeds independent plateau domain')
    actual = np.column_stack((q,v,p,alpha))
    expected = np.column_stack((reference.q,reference.v,reference.p,reference.alpha))
    final_absolute = np.abs(actual[-1]-expected[-1])
    final_relative = [float(error/abs(value)) if value != 0. else None
                      for error,value in zip(final_absolute,expected[-1])]
    plastic_work = H*YIELD*alpha
    membrane_kinetic = .5*MASS[0]*v[:,0]**2
    return dict(input=str(path.resolve()), input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        states=len(times), final_time_s=float(times[-1]),
        quantities=['epsilon','normal_displacement_m','epsilon_rate_per_s','normal_velocity_m_s','plastic_xx','alpha'],
        response_scales=STATE_SCALES.tolist(),
        maximum_scaled_trajectory_error=np.max(np.abs(actual-expected)/STATE_SCALES,axis=0).tolist(),
        final_actual=actual[-1].tolist(), final_reference=expected[-1].tolist(),
        final_absolute_error=final_absolute.tolist(),
        final_relative_error=final_relative,
        final_plastic_dissipation_j=float(plastic_work[-1]),
        reference_final_plastic_dissipation_j=float(reference.plastic_dissipation[-1]),
        final_membrane_kinetic_j=float(membrane_kinetic[-1]),
        reference_final_membrane_kinetic_j=float(.5*MASS[0]*reference.v[-1,0]**2),
        continuous_events=[asdict(event) for event in reference.events],
        reference_diagnostics=dict(reference.diagnostics))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fields',nargs='+',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    report=dict(scope='manufactured development temporal comparison; not engineering acceptance',
        reference_sha256=hashlib.sha256((Path(__file__).resolve().parents[1]/'tests/reference_oblique_q4_plateau.py').read_bytes()).hexdigest(),
        records=[compare(path) for path in args.fields])
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    for record in report['records']:
        print(Path(record['input']).name, 'final relative errors',record['final_relative_error'])


if __name__=='__main__':
    main()

"""Saved/source-only comparison; no solver, imports, eigensolve or time advance."""
from hashlib import sha256
import json
from pathlib import Path
import math

base=Path(__file__).parent
old_path=base/'d6_native_free_temporal_v1_20260930.json'
new_path=base/'native_dynamic_interface_v3_20261001.raw.json'
old=json.loads(old_path.read_text()); new=json.loads(new_path.read_text())
assert old['status']=='PASS' and new['status']=='NONPASS' and new['accepted_steps']==0
initial=new['initial_mechanical']; velocity=new['physical_velocity15']
spin=velocity[9:12]; translation=(.1,-.04,.03)
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
expected=[]
for point in initial['positions']:
    expected.extend(t+c for t,c in zip(translation,cross(spin,point)))
expected.extend(spin);expected.extend(spin)
mapping_error=max(abs(a-b) for a,b in zip(expected,velocity))
assert mapping_error==0.
spin_case=old['cases']['anisotropic_spin']['resolutions']['coarse']
result=dict(scope='read-only saved arrays and source semantics, no production evaluation',
    old_raw_sha256=sha256(old_path.read_bytes()).hexdigest(),
    v3_raw_sha256=sha256(new_path.read_bytes()).hexdigest(),
    old_source_test_sha256=sha256((base/'d6_native_free_temporal_v1_20260930.test.source.py').read_bytes()).hexdigest(),
    same=dict(physical_model='same source literals: centered curved x=(-1,0,1),y=.2(1-x^2), coupled ellipsoid, mass2.7/cross-center(.035,-.025,.012)',
        physical_slots='node1/2/3 translation and cell1/2 spatial spin; algebraic nodal rotation placeholders zero',
        owner='dynamic_elastic free15/algebraic27, inertia_order24, max_iterations12,max_backtracks8, no loads, virgin elastic',
        dt_seconds=.001,momentum_origin_high_m=[0.,0.,0.]),
    differences=dict(old_spin_velocity_rad_s=old['prospective']['initial_spin_rad_per_s'],
        v3_spin_velocity_rad_s=spin,v3_translation_velocity_m_s=list(translation),
        old_pose='reference/I cell frames/zero low positions',
        v3_pose='common rotation vector(.0002,-.0001,.0003), translation(.002,-.001,.003), low x1/x3=1e-18',
        old_stage_residual_tolerance=1e-11,v3_stage_residual_tolerance=1e-15),
    saved_v3_velocity_mapping_max_error= mapping_error,
    old_initial_rank_mass=spin_case['initial_rank_mass'],v3_initial_rank_mass=new['initial_checks'],
    disposition='V3 vs old free is not tolerance-only: kinematic seed differs. V3-to-V4 will be tolerance-only, keeping its exact pose/velocity/scales/gates and owner physics; old pass is contextual evidence only.')
path=base/'native_dynamic_interface_v4_20261001.saved_compare.json'
with path.open('x') as stream: stream.write(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(saved_compare_sha256=sha256(path.read_bytes()).hexdigest(),
                     old_raw_sha256=result['old_raw_sha256'],v3_velocity_mapping_max_error=mapping_error,
                     disposition=result['disposition'])))

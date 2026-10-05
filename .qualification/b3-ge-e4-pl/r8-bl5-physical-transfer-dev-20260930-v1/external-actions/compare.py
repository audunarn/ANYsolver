from pathlib import Path
import json, math
import numpy as np

root=Path(__file__).parent
native=Path(r'C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-bl5-matched-native-transfer-v1')
def cross(a,b): return np.cross(np.asarray(a),np.asarray(b))
def wrench(field,positions,origin):
    values=[np.r_[v[:3],np.asarray(v[3:])+cross(np.asarray(positions[n])-origin,v[:3])]
            for n,v in field.items()]
    return np.sum(values,axis=0).tolist()
def norms(a,b):
    a,b=np.asarray(a),np.asarray(b)
    return {'translation_l2_relative':float(np.linalg.norm(a[:,:3]-b[:,:3])/max(np.linalg.norm(b[:,:3]),1e-15)),
            'rotation_l2_relative':float(np.linalg.norm(a[:,3:]-b[:,3:])/max(np.linalg.norm(b[:,3:]),1e-15)),
            'pose_l2_length_1m_relative':float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-15)),
            'max_translation_error_m':float(np.max(np.abs(a[:,:3]-b[:,:3]))),
            'max_rotation_error_rad':float(np.max(np.abs(a[:,3:]-b[:,3:])))}
output={'classification':'fixed-mesh development comparison only',
 'contracts':{'geometry':'L1m,W.2m,h.035m; square .1m beam axisz.0675m; common interfacez.0175m',
 'sections':'E210GPa,nu.3,A.01,As.008,Iy=Iz8.333333333333333e-6,J1.6666666666666667e-5',
 'supports':'shell root6; native beamroot0..4 direct ground versus external five root equations into fixed shell; normal spin free',
 'discretization':'native8 B3 members/16 retained halfcells/80 P0 rows versus external16 Timoshenko beams/85 strong nodal rows',
 'origin_m':[0,0,.0675],
 'limits':'Not equal discrete constraints or an exact oracle. No refinement/convergence, 1% qualification, drilling-response independence or F03 acceptance.'},'cases':{}}
for case in ('fy','mx'):
    n=json.loads((native/(case+'.json')).read_text())
    raw=json.loads((root/case/'raw-inventory.json').read_text())
    d=json.loads((root/case/'recovered-actions.json').read_text())
    beam_ids=sorted(map(int,n['nodal_beam_poses']))
    shell_ids=sorted(map(int,n['nodal_shell_poses']))
    beam_n=[n['nodal_beam_poses'][str(i)] for i in beam_ids]
    beam_e=[raw['poses'][str(i+900)] for i in beam_ids]
    shell_n=[n['nodal_shell_poses'][str(i)] for i in shell_ids]
    shell_e=[raw['poses'][str(i)] for i in shell_ids]
    positions=raw['nodes']; origin=np.array(output['contracts']['origin_m'])
    external_beam={i:v for i,v in d['connection_exerted_loads'].items() if int(i)>=1001}
    external_root={'1001':external_beam['1001']}
    external_line={i:v for i,v in external_beam.items() if i!='1001'}
    output['cases'][case]={
      'work_j':{'native':n['applied_work_j'],'external':d['work_j']['applied'],
                'relative_difference':(n['applied_work_j']/d['work_j']['applied']-1)},
      'beam_pose':norms(beam_n,beam_e),'shell_pose':norms(shell_n,shell_e),
      'tip_pose_native':beam_n[-1],'tip_pose_external':beam_e[-1],
      'native_beam_ground_wrench_about_beamroot':n['beam_ground_force_n']+n['beam_ground_moment_about_root_nm'],
      'external_beam_root_connection_wrench_about_beamroot':wrench(external_root,positions,origin),
      'native_beam_line_moment_about_beamroot':n['beam_line_moment_about_root_nm'],
      'external_beam_nonroot_line_wrench_about_beamroot':wrench(external_line,positions,origin),
      'recovery_checks_external':d['checks'],
      'support_role_limit':'External root transfer corresponds to native direct ground role. Finite weak line still spans first interval; a root/line split is resolution-dependent.'}
(root/'comparison.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
for case,data in output['cases'].items():
    print(case,{k:data[k] for k in ('work_j','beam_pose','shell_pose',
        'native_beam_ground_wrench_about_beamroot','external_beam_root_connection_wrench_about_beamroot',
        'native_beam_line_moment_about_beamroot','external_beam_nonroot_line_wrench_about_beamroot')})

from pathlib import Path
import json,math
root=Path.cwd();native=json.loads((root/'native/native.json').read_text());rows=[]
scale=[2.,2.,2.,1.,1.,1.]
for panel in native['panels']:
 sign=panel['sign']
 for case in panel['cases']:
  name=case['name'];n=case['result'];e=json.loads((root/f'panel-{sign}-{name}'/f'panel-{sign}-{name}.json').read_text())
  un=n['displacements'];ue=[v for key in ('1','2','3','4','5','6','101','102','103') for v in e['nodal_states'][key]]
  norm=lambda u:max(abs(v)/scale[i%6] for i,v in enumerate(u))
  dis=norm([a-b for a,b in zip(un,ue)])/norm(ue)
  tip=norm([a-b for a,b in zip(un[48:54],ue[48:54])])/norm(ue[48:54])
  lamn=[v for _,l in n['point_multipliers'] for v in l];lame=e['physical_point_multipliers'];lm=lambda x:max(abs(v)/(1 if i%6<3 else 2) for i,v in enumerate(x))
  lam=lm([a-b for a,b in zip(lamn,lame)])/lm(lame)
  energy=abs(n['internal_strain_energy']-e['internal_strain_energy'])/abs(e['internal_strain_energy'])
  ground=lm([a-b for a,b in zip(n['affine_reactions'],e['actual_ground_covector'])])/lm(e['actual_ground_covector'])
  checks=max(v['value'] for v in e['checks'].values())
  rows.append({'sign':sign,'channel':name,'native_connection_row_error':panel['constraint_row_max_error'],'pose_relative':dis,'tip_pose_relative':tip,'energy_relative':energy,'physical_multiplier_relative':lam,'ground_relative':ground,'reference_max_normalized_check':checks})
report={'status':'FIXED_COMPARISON_ONLY_NOT_QUALIFIED','metric':'infinity norm of translation/2m and rotation; wrench force/moment/2m; no raw mixed-unit norm','one_percent_final_gate':'not assessed; mesh-converged matched quantities required','rows':rows,'stop':'No automatic refinement. Interpret channel/work differences with unchanged physical connection extent.'}
(root/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
for row in rows:print(f"{row['sign']:+} {row['channel']} tip={100*row['tip_pose_relative']:.4f}% energy={100*row['energy_relative']:.4f}% lambda={100*row['physical_multiplier_relative']:.4f}% ground={100*row['ground_relative']:.4f}%")

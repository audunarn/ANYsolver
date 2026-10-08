from pathlib import Path
import json
import numpy as np
from test_case import _fixture,_actions,_snapshot,_plain,_coverage,PREFIX_FACTORS
from anysolver import stiffened_shell
from contextlib import ExitStack

root=Path.cwd()
with ExitStack() as cleanup:
 def owner():
  made=stiffened_shell.create_analysis(definition=_fixture(True));cleanup.callback(made.close);return made
 def capture(made,label):
  snapshot=_snapshot(made)
  material=_plain((made._finite_driver._shell_origins,made._finite_driver._beam_origins))
  (root/(label+'-material.json')).write_text(json.dumps(material,indent=2))
  return snapshot,material
 control=owner();history=[]
 for factor in PREFIX_FACTORS:
  control.solve(_actions(),(factor,),max_iterations=20,max_backtracks=12)
  snap,_=capture(control,'prefix-'+str(factor));history.append(snap)
 rebased=owner();rebased.restore(control.checkpoint());capture(rebased,'restored-prefix')
 rebased.rebase_rotations(rebased.recover().generation);capture(rebased,'reset-prefix')
 resumed=owner();resumed.restore(rebased.checkpoint());capture(resumed,'anchored-prefix')
 final=[]
 for label,made in (('control',control),('reset',rebased),('resumed',resumed)):
  result=made.solve(_actions(),(1.,),max_iterations=20,max_backtracks=12)
  snap,material=capture(made,label+'-final');final.append((label,snap,material))
 differences=[]
 def walk(a,b,path):
  if isinstance(a,dict):
   assert a.keys()==b.keys()
   for key in a:walk(a[key],b[key],path+'/'+key)
  elif isinstance(a,list):
   assert len(a)==len(b)
   for i,(x,y) in enumerate(zip(a,b)):walk(x,y,path+'/'+str(i))
  elif a!=b:
   if isinstance(a,(int,float)) and not isinstance(a,bool):
    differences.append(dict(path=path,left=a,right=b,absolute_difference=abs(a-b)))
   else:differences.append(dict(path=path,left=a,right=b))
 for label,snapshot,material in final[1:]:walk(final[0][2],material,label)
 coverage={label:{domain:_coverage(history+[snap],domain) for domain in ('shell_frames','beam_frames')} for label,snap,_ in final}
 physics={label:{field:float(np.max(np.abs(snap[field]-final[0][1][field]))) for field in ('shell_positions','shell_frames','beam_positions','beam_frames','cell_frames','resultants','multipliers','support','point_actions','gaps')} for label,snap,_ in final[1:]}
 result=dict(status='COMPLETED_DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',differences=differences,coverage=coverage,physical_absolute_differences=physics)
 (root/'result.json').write_text(json.dumps(result,indent=2))
 print(json.dumps(dict(status=result['status'],different_leaves=len(differences),coverage=coverage)))

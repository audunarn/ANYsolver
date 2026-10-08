from pathlib import Path
import json,traceback
import b2_e01_opensees_finite_point as ref
import openseespy.opensees as ops
root=Path.cwd();target=root/'fresh-fy.json';assert not target.exists()
record={'case':'fresh-panel--1-Fy','source':'unchanged V2','status':'FAILED','runtime':ops.version(),'question':'same Fy operator in fresh process versus after six controls and Fx'}
try:
 ref.panel_case(ops,record,ref.panel_input(-1),1,1000.)
 assert record['passed']
 record['status']='PASSED_PHYSICAL_CHECKS'
except BaseException:
 record['traceback']=traceback.format_exc();raise
finally:
 ref.atomic_json(target,record)
print(json.dumps({'status':record['status'],'maximum_metric':max(v['value'] for v in record['checks'].values())}))

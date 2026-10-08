from pathlib import Path
import importlib.util,json,shutil,numpy as np
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('physical_under_test',root/'physical-v3.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
fixture=root.parent/'r8-bl5-affine-flexible-v1'
wheel=root.parent/'r8-bl5-projected-integration-v1/dist/anysolver-0.4.7-py3-none-any.whl'
original=m.compile_saved_projection
cases=[]
mutations=(('scalar_binding',lambda c:c.update(scalar_registration_sha256='0'*64)),
('representation_binding',lambda c:c.update(representation_sha256='0'*64)),
('derived_floor',lambda c:c.update(safe_case_floor=0.)),
('criteria',lambda c:c['criteria'].update(condition_budget=1e8)),
('density_scale',lambda c:c['physical_L2_basis_scale'].__setitem__(1,1.)))
for name,change in mutations:
 folder=root/'mutation-checks'/name;folder.mkdir(parents=True,exist_ok=False)
 for n in ('scalar.json','representation.json'):shutil.copyfile(root/n,folder/n)
 c=json.loads((root/'physical-registration.json').read_text());change(c)
 reg=folder/'registration.json';reg.write_text(json.dumps(c))
 try:m.assess(fixture,reg,folder/'unexpected.json',wheel)
 except (ValueError,AssertionError) as error:cases.append(dict(case=name,status='rejected',exception=type(error).__name__,detail=str(error)))
 else:raise AssertionError('mutation accepted: '+name)
for name in ('geometry','supports'):
 folder=root/'mutation-checks'/name;folder.mkdir(exist_ok=False)
 def altered(source):
  data=list(original(source))
  if name=='geometry':data[0]['xyz_m'][17][1]*=2.
  else:data[8]=data[8][data[8]!=0]
  return data
 m.compile_saved_projection=altered
 try:m.assess(fixture,root/'physical-registration.json',folder/'unexpected.json',wheel)
 except ValueError as error:cases.append(dict(case=name,status='rejected',exception=type(error).__name__,detail=str(error)))
 else:raise AssertionError('mutation accepted: '+name)
 m.compile_saved_projection=original
(root/'mutation-results.json').write_text(json.dumps(dict(status='ALL_REJECTED',cases=cases),indent=2)+'\n')
print(json.dumps(dict(status='ALL_REJECTED',count=len(cases))))

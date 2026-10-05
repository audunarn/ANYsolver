from pathlib import Path
import ast,hashlib,json,xml.etree.ElementTree as ET,zipfile
raw=Path(__file__).resolve().parent; repo=raw.parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
site=raw.parent/'r8-native-fibre-bl5-dev-20261005-v1/installed-s3-v1'; ci=raw.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
passes=set(); inventory=set(); versions={}
for v in (2,3,4):
 cases=list(ET.parse(raw/f'junit-v{v}.xml').getroot().iter('testcase'))
 keys={(c.attrib.get('classname',''),c.attrib['name']) for c in cases}
 good={(c.attrib.get('classname',''),c.attrib['name']) for c in cases if c.find('failure') is None and c.find('error') is None and c.find('skipped') is None}
 if v==2: inventory=keys
 else: assert not any('calibration' in name for _,name in keys)
 passes.update(good); versions[str(v)]={'tested':len(keys),'passed':len(good)}
 r=json.loads((raw/f'runtime-v{v}.json').read_text())
 assert all(Path(p).resolve().is_relative_to(site.resolve()) for p in r['imports'].values())
 assert all(Path(r['dependencies'][n]['path']).resolve().is_relative_to(ci.resolve()) for n in ('numpy','scipy','numba','llvmlite'))
 assert r['affinity']==[0] and r['jit_off'] and r['numba_threads']==1 and not r['errors']
 assert all(p['num_threads']==1 for p in r['pools'])
assert passes==inventory and len(passes)==13
b=json.loads((raw/'binding-v4.json').read_text())
for name,digest in b['source'].items():
 if not name.startswith('docs/'): assert sha(repo/name)==digest, name
for rel,digest in b['installed_modules'].items():
 assert sha(site/rel)==digest and sha(repo/'src'/rel)==digest, rel
wheel=site.parent/'wheel-s3-v1/anysolver-0.4.7-py3-none-any.whl'
assert sha(wheel)==b['wheel_sha256']
with zipfile.ZipFile(wheel) as z:
 assert all(hashlib.sha256(z.read(rel.replace(chr(92),'/'))).hexdigest()==digest for rel,digest in b['installed_modules'].items())
functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
a=functions(ast.parse((raw/'executed-script-v2.py').read_text())); c=functions(ast.parse((repo/'scripts/r8_bl5_matched_native_reference.py').read_text()))
assert all(c[k]==v for k,v in a.items()) and set(c)-set(a)=={'common_origin_wrench'}
a_tests=functions(ast.parse((raw/'executed-tests-v2.py').read_text())); c_tests=functions(ast.parse((repo/'tests/test_r8_bl5_matched_native_reference.py').read_text()))
changed={k for k in a_tests if a_tests[k]!=c_tests[k]}
assert changed=={'test_actual_global_continuum_common_field_and_integrated_dual','test_free_normal_spin_and_independent_supported_transverse_shear'}
original=raw.parent/'r8-bl5-released-reference-dev-20261005-v1/original-supervisor.py'
assert sha(original)==b['base_supervisor_sha256']
result={'scope':'root independent source/runtime/coverage/artifact inspection; DEV only; no numerical rerun','distinct_controls':len(passes),'versions':versions,'loaded_solver_modules':len(r['imports']),'source_site_wheel_modules':len(b['installed_modules']),'wheel_sha256':sha(wheel),'source_sha256':{n:sha(repo/n) for n in b['source']},'unchanged_v2_functions_reused':sorted(a),'changed_tests':sorted(changed),'calibration_runs':1,'calibration_sha256':sha(raw/'calibration-v2.json'),'original_supervisor_repo_path':str(original),'original_supervisor_sha256':sha(original),'runtime_roots_settings_verified':True,'scientific_acceptance':False,'verifier_sha256':sha(__file__),'prior_verifier_failure':'zip entry used Windows separators; fixed normalization; no numerical job involved'}
(raw/'integration-binding.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
print(json.dumps({k:result[k] for k in ('distinct_controls','versions','loaded_solver_modules','source_site_wheel_modules','wheel_sha256','calibration_runs','runtime_roots_settings_verified')}))